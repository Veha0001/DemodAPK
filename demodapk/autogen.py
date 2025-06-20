#!/bin/python

import os
import re
import sys
import glob
import json
import shutil
import argparse
import subprocess
from typing import Optional
from art import text2art
from termcolor import cprint, colored
from platformdirs import user_config_dir

try:
    from colorama import init

    init(autoreset=True)
except ImportError:
    pass

try:
    import inquirer
except ImportError:
    inquirer = None

__version__ = "1.1.3"


def show_logo(text, font="small", color_pattern=None):
    logo_art = text2art(text, font=font)
    if color_pattern is None:
        color_blocks = [
            ("green", 6),
            ("red", 5),
            ("cyan", 7),
            ("yellow", 5),
            ("blue", 6),
            ("magenta", 7),
            ("light_green", 5),
            ("light_cyan", 6),
        ]
    else:
        color_blocks = color_pattern

    if isinstance(logo_art, str):
        lines = logo_art.splitlines()
        for line in lines:
            colored_line = ""
            color_index = 0
            count_in_block = 0
            current_color, limit = color_blocks[color_index]

            for char in line:
                colored_line += colored(char, current_color, attrs=["bold"])
                count_in_block += 1
                if count_in_block >= limit:
                    count_in_block = 0
                    color_index = (color_index + 1) % len(color_blocks)
                    current_color, limit = color_blocks[color_index]
            print(colored_line)


class MessagePrinter:
    def print(
        self,
        message: str,
        color: Optional[str] = None,
        inline: bool = False,
        bold: bool = False,
        prefix: Optional[str] = None,
        flush: bool = False,
        inlast: bool = False,
    ):
        formatted_message = f"{prefix or ''} {message}".strip()
        attrs = ["bold"] if bold else []

        if inline:
            # Didnt mix it in...
            cprint(f"\r{formatted_message}", color, attrs=attrs, end=" ", flush=flush)
            print(" " * 5) if inlast else None
        else:
            cprint(formatted_message, color, attrs=attrs, flush=flush)

    def success(self, message, bold: bool = False, inline=False, prefix="[*]"):
        self.print(message, color="green", bold=bold, inline=inline, prefix=prefix)

    def warning(
        self,
        message,
        color: Optional[str] = "yellow",
        bold: bool = False,
        inline=False,
    ):
        self.print(
            message,
            color=color,
            bold=bold,
            inline=inline,
            prefix="[W]",
        )

    def error(self, message, inline=False):
        self.print(message, color="red", inline=inline, prefix="[X]")

    def info(
        self,
        message,
        color: str = "cyan",
        bold: bool = False,
        inline=False,
        prefix: str = "[!]",
    ):
        self.print(message, color=color, bold=bold, inline=inline, prefix=prefix)

    def progress(self, message, inline=False, bold: bool = False):
        self.print(message, color="magenta", bold=bold, inline=inline, prefix="[$]")


# Example usage
msg = MessagePrinter()


def extract_package_info(manifest_file):
    package_name = None
    package_path = None

    if os.path.isfile(manifest_file):
        with open(manifest_file, "r", encoding="utf-8") as file:
            content = file.read()

        # Extract the package name using regex
        package_match = re.search(r'package="([\w\.]+)"', content)
        if package_match:
            package_name = package_match.group(1)
            package_path = "L" + package_name.replace(".", "/")
        else:
            msg.error(f"Package name not found in {manifest_file}.")
    else:
        msg.error("AndroidManifest.xml not found.")
    return package_name, package_path


def update_app_name_values(app_name, value_strings):
    if not os.path.isfile(value_strings):
        msg.error(f"File not found: {value_strings}")
        return

    with open(value_strings, "r", encoding="utf-8") as f:
        content = f.read()

    if '<string name="app_name">' not in content:
        msg.error("app_name string not found.")
        return

    new_content = re.sub(
        r'<string name="app_name">.*?</string>',
        f'<string name="app_name">{app_name}</string>',
        content,
    )

    with open(value_strings, "w", encoding="utf-8") as f:
        f.write(new_content)

    msg.success(f"Updated AppName to: {app_name}")


def update_facebook_app_values(
    strings_file, fb_app_id, fb_client_token, fb_login_protocol_scheme
):
    if os.path.isfile(strings_file):
        with open(strings_file, "r", encoding="utf-8") as file:
            content = file.read()

        # Replace values in strings.xml
        content = re.sub(
            r'<string name="facebook_app_id">.*?</string>',
            f'<string name="facebook_app_id">{fb_app_id}</string>',
            content,
        )
        content = re.sub(
            r'<string name="facebook_client_token">.*?</string>',
            f'<string name="facebook_client_token">{fb_client_token}</string>',
            content,
        )
        content = re.sub(
            r'<string name="fb_login_protocol_scheme">.*?</string>',
            f'<string name="fb_login_protocol_scheme">{fb_login_protocol_scheme}</string>',
            content,
        )

        with open(strings_file, "w", encoding="utf-8") as file:
            file.write(content)
        msg.success("Updated Facebook App values")
    else:
        msg.error(f"File: {strings_file}, does not exists.")


def update_files_from_loaded(files_info, apk_dir):
    """Modify files based on the configuration entry (replace, copy, move within APK)."""

    for operation, files in files_info.items():
        if operation == "replace":
            for src, dest in files.items():
                if isinstance(dest, list):
                    msg.error(f"Replace does not support multiple destinations: {src}")
                    continue  # Skip invalid entry

                dest_path = os.path.join(apk_dir, dest)

                if not os.path.exists(src):
                    msg.error(f"Source file '{src}' not found.")
                    continue

                os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                try:
                    shutil.move(src, dest_path)
                    msg.success(f"Replaced: {src} → {dest_path}")
                except Exception as e:
                    msg.error(f"Failed to replace '{src}' → '{dest_path}': {e}")

        elif operation == "copy":
            for src, dests in files.items():
                if not isinstance(dests, list):
                    dests = [dests]  # Ensure it's a list

                if not os.path.exists(src):
                    msg.error(f"Source file '{src}' not found.")
                    continue

                for dest in dests:
                    dest_path = os.path.join(apk_dir, dest)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                    try:
                        shutil.copy2(src, dest_path)
                        msg.success(f"Copied: {src} → {dest_path}")
                    except Exception as e:
                        msg.error(f"Failed to copy '{src}' → '{dest_path}': {e}")

        elif operation == "base_move":
            for src, dest in files.items():
                if isinstance(dest, list):
                    msg.error(f"Move does not support multiple destinations: {src}")
                    continue  # Skip invalid entry

                src = os.path.join(apk_dir, src)
                dest_path = os.path.join(apk_dir, dest)

                if not os.path.exists(src):
                    msg.error(f"Source file '{src}' not found.")
                    continue

                os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                try:
                    shutil.move(src, dest_path)
                    msg.success(f"Moved: {src} → {dest_path}")
                except Exception as e:
                    msg.error(f"Failed to move '{src}' → '{dest_path}': {e}")


def rename_package_in_manifest(
    manifest_file, old_package_name, new_package_name, level=0
):
    if not os.path.isfile(manifest_file):
        msg.error("AndroidManifest.xml was not found.")
        return

    try:
        with open(manifest_file, "r", encoding="utf-8") as file:
            content = file.read()

        # Normalize line endings (for Windows compatibility)
        content = content.replace("\r\n", "\n")

        # Base replacements
        replacements = [
            (f'package="{old_package_name}"', f'package="{new_package_name}"'),
            (
                f'android:name="{old_package_name}\\.',
                f'android:name="{new_package_name}.',
            ),
            (
                f'android:authorities="{old_package_name}\\.',
                f'android:authorities="{new_package_name}.',
            ),
        ]

        # Add additional replacements for level == 1
        if level == 1:
            replacements.extend(
                [
                    (
                        f'android:taskAffinity="{old_package_name}"',
                        'android:taskAffinity=""',
                    ),
                ]
            )

        if level == 2:
            replacements.extend(
                [
                    (
                        f'android:taskAffinity="{old_package_name}"',
                        f'android:taskAffinity="{new_package_name}"',
                    ),
                ]
            )

        if level == 3:
            replacements.extend(
                [
                    (
                        f'android:taskAffinity="{old_package_name}"',
                        f'android:taskAffinity="{new_package_name}"',
                    ),
                    (
                        f'android:host="{old_package_name}"',
                        f'android:host="{new_package_name}"',
                    ),
                    (
                        f'android:host="cct\\.{old_package_name}"',
                        f'android:host="cct.{new_package_name}"',
                    ),
                ]
            )

        if level == 4:
            replacements.extend(
                [
                    (
                        f'android:taskAffinity="{old_package_name}"',
                        'android:taskAffinity=""',
                    ),
                    (
                        f'android:host="{old_package_name}"',
                        f'android:host="{new_package_name}"',
                    ),
                    (
                        f'android:host="cct\\.{old_package_name}"',
                        f'android:host="cct.{new_package_name}"',
                    ),
                ]
            )

        # Perform replacements
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)

        with open(manifest_file, "w", encoding="utf-8") as file:
            file.write(content)

        msg.success("Updated package name in AndroidManifest.xml")

    except FileNotFoundError:
        msg.error(f"The manifest file '{manifest_file}' was not found.")
    except IOError as e:
        msg.error(f"Error reading or writing the manifest file: {e}")
    except re.error as e:
        msg.error(f"Regular expression error: {e}")


def update_smali_path_package(smali_dir, old_package_path, new_package_path):
    for root, _, files in os.walk(smali_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith(".smali"):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Replace old package name with new one
                new_content = content.replace(old_package_path, new_package_path)

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)

    msg.success("Updated package name in smali files.")


def rename_package_in_resources(resources_dir, old_package_name, new_package_name):
    try:
        # Check if resources directory exists
        if not os.path.isdir(resources_dir):
            raise FileNotFoundError(
                f"The resources directory '{resources_dir}' does not exist."
            )

        updated_any = False  # Track if any file was updated
        valid_file_extensions = (
            ".xml",
            ".json",
            ".txt",
        )  # Define file types to process

        for root, _, files in os.walk(resources_dir):
            for file in files:
                if not file.endswith(valid_file_extensions):
                    continue  # Skip irrelevant file types

                file_path = os.path.join(root, file)

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Check if the old package name exists in the file
                    if f'"{old_package_name}"' in content:
                        new_content = content.replace(
                            f'"{old_package_name}"', f'"{new_package_name}"'
                        )
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        updated_any = True

                except UnicodeDecodeError:
                    msg.warning(f"File {file_path} is not UTF-8 encoded, skipping.")
                except (OSError, IOError) as e:
                    msg.error(f"Failed to process file: {file_path}. Error: {e}")

        if updated_any:
            msg.success("Updated package name in resource files.")
        else:
            msg.info("No files with the specified package name were found to update.")

    except FileNotFoundError as fnf_error:
        msg.error(str(fnf_error))
    except Exception as e:
        msg.error(f"An unexpected error occurred: {e}")


def update_smali_directory(smali_dir, old_package_path, new_package_path):
    # Use glob to find all directories in the smali_dir that match the old
    old_package_pattern = os.path.join(
        smali_dir, "**", old_package_path.strip("L")
    )  # Use '**' to search in subdirectories
    # Recursively find all matching directories
    old_dirs = glob.glob(old_package_pattern, recursive=True)

    renamed = False  # Track if any directory was renamed

    for old_dir in old_dirs:
        # Create the new directory path based on the found old directory
        new_dir = old_dir.replace(
            old_package_path.strip("L"), new_package_path.strip("L")
        )

        if os.path.isdir(old_dir):
            # Rename the old directory to the new directory
            os.rename(old_dir, new_dir)
            msg.success(f"Renamed directory {old_dir} to {new_dir}.")
            renamed = True
        else:
            msg.info(f"Directory {old_dir} does not exist. Skipping renaming.")

    if not renamed:
        msg.info(
            f"No directories matching {old_package_path} were found. Skipping renaming."
        )


def update_application_id_in_smali(smali_dir, old_package_name, new_package_name):
    try:
        # Check if smali directory exists
        if not os.path.isdir(smali_dir):
            raise FileNotFoundError(
                f"The smali directory '{smali_dir}' does not exist."
            )

        buildconfig_found = False
        updated_any = False

        for root, _, files in os.walk(smali_dir):
            for file in files:
                if file.endswith("BuildConfig.smali"):
                    buildconfig_found = True
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        # Check if old APPLICATION_ID exists in the file
                        if (
                            f' APPLICATION_ID:Ljava/lang/String; = "{old_package_name}"'
                            in content
                        ):
                            # Replace APPLICATION_ID
                            new_content = content.replace(
                                f' APPLICATION_ID:Ljava/lang/String; = "{old_package_name}"',
                                f' APPLICATION_ID:Ljava/lang/String; = "{new_package_name}"',
                            )
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(new_content)
                            updated_any = True

                    except (OSError, IOError) as e:
                        msg.error(f"Failed to update {file_path}: {e}")

        if not buildconfig_found:
            raise FileNotFoundError(
                "No BuildConfig.smali files found in the provided smali directory."
            )
        if not updated_any:
            raise ValueError(
                "No BuildConfig.smali file contained the specified old APPLICATION_ID."
            )
    except FileNotFoundError as fnf_error:
        msg.error(str(fnf_error))
    except ValueError as val_error:
        msg.error(str(val_error))
    except Exception as e:
        msg.error(f"An unexpected error occurred: {e}")
    else:
        msg.success("Updated APPLICATION_ID in smali files.")


def remove_metadata_from_manifest(manifest_file, config_file):
    # Filter out any empty strings in metadata_to_remove
    metadata_to_remove = [
        meta for meta in config_file if isinstance(meta, str) and meta.strip()
    ]

    # If metadata_to_remove is empty or only contained empty strings, skip removal
    if not metadata_to_remove:
        # msg.info("No valid metadata entries specified for removal in configuration file.")
        return

    if os.path.isfile(manifest_file):
        with open(manifest_file, "r", encoding="utf-8") as file:
            lines = file.readlines()

        # Filter out lines that match the metadata
        filtered_lines = []
        skip = False
        for line in lines:
            if any(meta in line for meta in metadata_to_remove):
                skip = True  # Skip this line and the next
            elif skip and "/>" in line:  # End of the meta-data entry
                skip = False  # Stop skipping after closing tag
            else:
                filtered_lines.append(line)

        # Write the filtered lines back to the manifest file
        with open(manifest_file, "w", encoding="utf-8") as file:
            file.writelines(filtered_lines)
        msg.success("Specific metadata removed from manifest.")
    else:
        msg.warning(f"File '{manifest_file}' does not exist.")


def check_for_dex_folder(apk_dir):
    dex_folder_path = os.path.join(apk_dir, "dex")  # Adjust the path if necessary
    return os.path.isdir(dex_folder_path)


def create_default_config(config_path, default_config):
    with open(config_path, "w", encoding="utf-8") as file:
        json.dump(default_config, file, indent=4)
    msg.info(
        f"Configuration file '{config_path}' not found. Created default config file."
    )
    sys.exit(0)


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog="demodapk",
        usage="%(prog)s <apk_dir> [options]",
        description="DemodAPK: APK Modification Script, Made by @Veha0001.",
    )
    parser.add_argument("apk_dir", nargs="?", help="Path to the APK directory/file")
    parser.add_argument(
        "-n",
        "--no-rename-package",
        action="store_true",
        help="Run the script without renaming the package",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default="config.json",
        help="Path to the JSON configuration file.",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force overwrite the decoded APK directory.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="output path of decoded_dir and name.",
    )
    parser.add_argument(
        "-nfb",
        "--no-facebook",
        action="store_true",
        help="No update for Facebook app API.",
    )
    parser.add_argument(
        "-mv",
        "--move-rename-smali",
        action="store_true",
        help="Rename package in smali files and the smali directory.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=("%(prog)s " + __version__),
        help="Show version of the program.",
    )
    return parser


def verify_apk_directory(apk_dir):
    """
    Verifies if the given directory is a valid decoded APK directory.

    Args:
        apk_dir (str): Path to the APK directory.

    Returns:
        str: Verified APK directory path.
    """
    if not os.path.exists(apk_dir):
        msg.error(f"The directory {apk_dir} does not exist.")
        sys.exit(1)

    # Check for required files and folders
    required_files = ["AndroidManifest.xml"]
    required_folders = ["resources", "root"]
    optional_folders = ["dex", "smali"]

    # Check for required files
    for req_file in required_files:
        if not os.path.isfile(os.path.join(apk_dir, req_file)):
            msg.error(f"Missing required file '{req_file}' in {apk_dir}.")
            sys.exit(1)

    # Check for required folders
    for req_folder in required_folders:
        if not os.path.isdir(os.path.join(apk_dir, req_folder)):
            msg.error(f"Missing required folder '{req_folder}' in {apk_dir}.")
            sys.exit(1)

    # Check for at least one optional folder
    if not any(
        os.path.isdir(os.path.join(apk_dir, folder)) for folder in optional_folders
    ):
        msg.error(
            f"At least one of the following folders is required in {apk_dir}: {', '.join(optional_folders)}."
        )
        sys.exit(1)

    msg.info(f"APK directory verified: {apk_dir}")
    return apk_dir


def run_commands(commands, quietly, tasker: bool = False):
    """
    Run commands with support for conditional execution based on directory existence.

    Args:
        commands: List of commands or list of command dictionaries
        quietly: Run all commands quietly unless overridden per command
    """

    def run(cmd, quiet_mode, title: str = ""):
        if quiet_mode:
            if not tasker:
                msg.progress(title or cmd)

            subprocess.run(
                cmd,
                shell=True,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            subprocess.run(cmd, shell=True, check=True)

    if isinstance(commands, list):
        for command in commands:
            try:
                if isinstance(command, str):
                    run(command, quietly)
                elif isinstance(command, dict):
                    cmd = command.get("run")
                    title = command.get("title", "")
                    quiet = command.get("quiet", True)
                    if cmd:
                        run(cmd, quiet, title)
            except subprocess.CalledProcessError as e:
                failed_cmd = command if isinstance(command, str) else command.get("run")
                msg.error(f"Command failed: {failed_cmd}\nError: {e}")
                sys.exit(1)


def get_apkeditor_cmd(editor_jar: str, javaopts: str):
    apkeditor_cmd = shutil.which("apkeditor")
    if apkeditor_cmd:
        opts = " ".join(f"-J{opt.lstrip('-')}" for opt in javaopts.split())
        return f"apkeditor {opts}".strip()
    if editor_jar:
        return f"java {javaopts} -jar {editor_jar}".strip()
    msg.error("Cannot decode the apk without APKEditor.")
    sys.exit(1)


def apkeditor_merge(editor_jar, apk_file, javaopts, merge_base_apk, quietly: bool):
    # New base name of apk_file end with .apk
    command = f'{get_apkeditor_cmd(editor_jar, javaopts)} m -i "{apk_file}" -o "{merge_base_apk}"'
    msg.info(f"Merging: {apk_file}", bold=True, prefix="[-]")
    run_commands([command], quietly, tasker=True)
    msg.info(
        f"Merged into: {merge_base_apk}",
        color="green",
        bold=True,
        prefix="[+]",
    )


def apkeditor_decode(
    editor_jar, apk_file, javaopts, output_dir, dex: bool, quietly: bool
):
    merge_base_apk = apk_file.rsplit(".", 1)[0] + ".apk"
    # If apk_file is not end with .apk then merge
    if not apk_file.endswith(".apk"):
        if not os.path.exists(merge_base_apk):
            apkeditor_merge(editor_jar, apk_file, javaopts, merge_base_apk, quietly)
        command = f'{get_apkeditor_cmd(editor_jar, javaopts)} d -i "{merge_base_apk}" -o "{output_dir}"'
        apk_file = merge_base_apk
    else:
        command = f'{get_apkeditor_cmd(editor_jar, javaopts)} d -i "{apk_file}" -o "{output_dir}"'

    if dex:
        command += " -dex"
    msg.info(f"Decoding: {os.path.basename(apk_file)}", bold=True, prefix="[-]")
    run_commands([command], quietly, tasker=True)
    msg.info(
        f"Decoded into: {output_dir}",
        color="green",
        bold=True,
        prefix="[+]",
    )


def apkeditor_build(editor_jar, input_dir, output_apk, javaopts, quietly: bool):
    command = f'{get_apkeditor_cmd(editor_jar, javaopts)} b -i "{input_dir}" -o "{output_apk}"'
    msg.info(f"Building: {input_dir}", bold=True, prefix="[-]")
    run_commands([command], quietly, tasker=True)
    msg.info(
        f"Built into: {output_apk}",
        color="green",
        bold=True,
        prefix="[+]",
    )


def get_config_path():
    local_config = "config.json"
    if os.path.exists(local_config):
        return local_config
    # Cross-platform config directory
    global_config = os.path.join(user_config_dir("demodapk"), "config.json")
    return global_config


def load_config():
    config_path = get_config_path()

    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    show_logo("DemodAPK")
    parsers = parse_arguments()
    args = parsers.parse_args()
    config = load_config()
    apk_dir = args.apk_dir
    if apk_dir is None:
        parsers.print_help()
        sys.exit(1)

    # Initialize android_manifest variable
    android_manifest = None
    package_orig_name, package_orig_path = None, None
    apk_solo = apk_dir.lower().endswith((".zip", ".apk", ".apks", ".xapk"))

    if os.path.isfile(apk_dir):
        # Extract preconfigured package names
        available_packages = list(config.get("DemodAPK", {}).keys())

        if not apk_solo:
            msg.error(f"This: {apk_dir}, is’t an apk type.")
            sys.exit(1)

        if not available_packages:
            msg.error("No preconfigured packages found in config.json.")
            sys.exit(1)

        if inquirer is None:
            msg.error(
                "Inquirer package is not installed. Please install it to proceed."
            )
            sys.exit(1)

        # Create the inquirer question
        questions = [
            inquirer.List(
                "package",
                message="Select a package configuration for this APK",
                choices=available_packages,
            )
        ]

        try:
            # Show the interactive selection menu
            answers = inquirer.prompt(questions)
            if answers and "package" in answers:
                package_orig_name = answers["package"]
                package_orig_path = "L" + package_orig_name.replace(".", "/")
            else:
                msg.error("No package was selected.")
                sys.exit(1)
        except Exception as e:
            msg.error(f"Error during package selection: {e}")
            sys.exit(1)

        # Retrieve the selected package configuration
        apk_config = config["DemodAPK"].get(package_orig_name)

        if not apk_config:
            msg.error(f"No configuration found for package: {package_orig_name}")
            sys.exit(1)

        dex_folder_exists = False
        decoded_dir = apk_dir.rsplit(".", 1)[0]
    else:
        apk_dir = verify_apk_directory(apk_dir)
        dex_folder_exists = check_for_dex_folder(apk_dir)
        decoded_dir = apk_dir

        # Extract package info from AndroidManifest.xml
        android_manifest = os.path.join(apk_dir, "AndroidManifest.xml")
        if not os.path.isfile(android_manifest):
            msg.error("AndroidManifest.xml not found in the directory.")
            sys.exit(1)

        package_orig_name, package_orig_path = extract_package_info(android_manifest)
        apk_config = config.get("DemodAPK", {}).get(package_orig_name)

        if not apk_config:
            msg.error(f"No configuration found for package: {package_orig_name}")
            sys.exit(1)

    # Extract config values
    log_level = apk_config.get("log", False)
    manifest_edit_level = apk_config.get("level", 0)
    app_name = apk_config.get("app_name", None)
    facebook_config = apk_config.get("facebook", {})
    facebook_appid = facebook_config.get("app_id", "")
    fb_client_token = facebook_config.get("client_token", "")
    fb_login_protocol_scheme = facebook_config.get("login_protocol_scheme", "")
    new_package_name = apk_config.get("package", "")
    new_package_path = "L" + new_package_name.replace(".", "/")
    apkeditor = apk_config.get("apkeditor", {})
    editor_jar = apkeditor.get("jarpath", "")
    javaopts = apkeditor.get("javaopts", "")
    dex_option = apkeditor.get("dex", False)
    to_output = args.output or apkeditor.get("output")
    files_entry = apk_config.get("files", {})
    command_quietly = apk_config.get("commands", {}).get("quietly", False)
    # Log a warning if dex folder is found
    if log_level and dex_folder_exists:
        msg.warning(
            "Dex folder found. Some functions will be disabled.",
            bold=True,
        )
    if to_output:
        decoded_dir = to_output.removesuffix(".apk")

    if apkeditor and not shutil.which("java"):
        msg.error("Java is not installed. Please install Java to proceed.")
        sys.exit(1)

    # Decode APK if input is an APK file
    if os.path.isfile(apk_dir):
        if args.force:
            shutil.rmtree(decoded_dir, ignore_errors=True)
        if not os.path.exists(decoded_dir):
            apkeditor_decode(
                editor_jar, apk_dir, javaopts, decoded_dir, dex_option, command_quietly
            )
        apk_dir = decoded_dir

    # Run pre-modification commands
    os.environ["BASE"] = apk_dir
    if "commands" in apk_config and "begin" in apk_config["commands"]:
        run_commands(apk_config.get("commands", {}).get("begin", []), command_quietly)

    # Paths
    resources_folder = os.path.join(apk_dir, "resources")
    smali_folder = os.path.join(apk_dir, "smali") if not dex_option else None
    value_strings = os.path.join(resources_folder, "package_1/res/values/strings.xml")
    if not android_manifest:
        android_manifest = os.path.join(apk_dir, "AndroidManifest.xml")

    # Modify APK contents
    if app_name is not None:
        update_app_name_values(app_name, value_strings)

    if facebook_config and not args.no_facebook:
        update_facebook_app_values(
            value_strings, facebook_appid, fb_client_token, fb_login_protocol_scheme
        )

    if "files" in apk_config:
        update_files_from_loaded(files_entry, apk_dir)

    if not args.no_rename_package and "package" in apk_config:
        rename_package_in_manifest(
            android_manifest, package_orig_name, new_package_name, manifest_edit_level
        )
        rename_package_in_resources(
            resources_folder, package_orig_name, new_package_name
        )

        if not dex_folder_exists and not dex_option:
            if args.move_rename_smali:
                update_smali_path_package(
                    smali_folder, package_orig_path, new_package_path
                )
                update_smali_directory(
                    smali_folder, package_orig_path, new_package_path
                )
            update_application_id_in_smali(
                smali_folder, package_orig_name, new_package_name
            )

    if "manifest" in apk_config and "remove_metadata" in apk_config["manifest"]:
        remove_metadata_from_manifest(
            android_manifest, apk_config["manifest"]["remove_metadata"]
        )

    # Build APK if decoded
    output_apk = os.path.basename(decoded_dir.rstrip("/"))
    output_apk_path = os.path.join(decoded_dir, output_apk + ".apk")

    if (
        not os.path.exists(output_apk_path)
        or shutil.which("apkeditor")
        or "jarpath" in apk_config["apkeditor"]
    ):
        apkeditor_build(
            editor_jar, decoded_dir, output_apk_path, javaopts, command_quietly
        )

    # Run post-modification commands
    os.environ["BUILD"] = output_apk_path
    if "commands" in apk_config and "end" in apk_config["commands"]:
        run_commands(apk_config.get("commands", {}).get("end", []), command_quietly)

    msg.info("APK modification finished!", bold=True)


if __name__ == "__main__":
    main()
