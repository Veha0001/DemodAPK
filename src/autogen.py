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
from platformdirs import user_config_dir

try:
    from colorama import init

    init(autoreset=True)
except ImportError:
    pass

try:
    from art import text2art
except ImportError:
    text2art = None

try:
    import inquirer
except ImportError:
    inquirer = None

# Define base ANSI color codes for the rainbow
base_rainbow_colors = [31, 33, 32, 36, 34, 35]


def print_rainbow_art(text, font="smslant", bold=False):
    if text2art is None:
        return  # Exit quietly if the art package is not available

    # Generate ANSI color codes with or without bold
    rainbow_colors = [
        f"\033[1;{color}m" if bold else f"\033[{color}m"
        for color in base_rainbow_colors
    ]

    # Generate ASCII art using the specified font
    ascii_art = text2art(text, font=font)
    # Split the ASCII art into lines
    if isinstance(ascii_art, str):
        lines = ascii_art.splitlines()
        # Apply rainbow colors line by line
        for i, line in enumerate(lines):
            color = rainbow_colors[i % len(rainbow_colors)]
            print(color + line + "\033[0m")  # Reset color after each line


class MessagePrinter:
    def __init__(self):
        self.colors = {
            "green": "\033[92m",
            "yellow": "\033[93m",
            "red": "\033[91m",
            "purple": "\033[95m",
            "blue": "\033[94m",
            "cyan": "\033[96m",
            "bold": "\033[1m",
            "underline": "\033[4m",
            "reset": "\033[0m",
        }

    def print(
        self,
        message: str,
        color: Optional[str] = None,
        bold: bool = False,
        underline: bool = False,
        inline: bool = False,
        prefix: Optional[str] = None,
    ):
        color_code = self.colors.get(color or "", "")
        bold_code = self.colors["bold"] if bold else ""
        underline_code = self.colors["underline"] if underline else ""
        reset_code = self.colors["reset"]

        formatted_message = f"{bold_code}{color_code}{prefix or ''}{reset_code} {color_code}{bold_code}{underline_code}{message}{reset_code}".strip()

        if inline:
            print(f"\r{formatted_message}", end="", flush=True)
        else:
            print(formatted_message)

    def success(self, message, bold: bool = False, inline=False):
        self.print(message, color="green", bold=bold, inline=inline, prefix="[✔]")

    def warning(
        self,
        message,
        color: Optional[str] = "yellow",
        bold: bool = False,
        underline: bool = False,
        inline=False,
    ):
        # Use the passed color, bold, and underline values
        self.print(
            message,
            color=color,
            bold=bold,
            underline=underline,
            inline=inline,
            prefix="[⚠]",
        )

    def error(self, message, inline=False):
        self.print(message, color="red", inline=inline, prefix="[✖]")

    def info(self, message, bold: bool = False, inline=False):
        self.print(message, color="cyan", bold=bold, inline=inline, prefix="[ℹ]")

    def progress(self, message, inline=False, bold: bool = False):
        self.print(message, color="blue", bold=bold, inline=inline, prefix="[➜]")

    def input(
        self,
        prompt: str,
        color: Optional[str] = None,
        bold: bool = False,
        nextline: bool = False,
    ):
        """Displays a styled input prompt and returns the user input."""
        color_code = self.colors.get(color or "", "")
        bold_code = self.colors["bold"] if bold else ""
        reset_code = self.colors["reset"]
        if not nextline:
            formatted_prompt = f"{bold_code}{color_code}[?] {prompt}{reset_code}"
        else:
            formatted_prompt = f"{bold_code}{color_code}[?] {prompt}{reset_code}\n> "
        # Use input() to get user input
        return input(formatted_prompt)


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


def run_commands(commands):
    """
    Run commands with support for conditional execution based on directory existence.

    Args:
        commands: List of commands or list of command dictionaries
        target_dir: Target directory to check for existence (default: None)
    """
    if isinstance(commands, list):
        for command in commands:
            if isinstance(command, str):
                # Simple string command - run directly
                try:
                    subprocess.run(command, shell=True, check=True)
                except subprocess.CalledProcessError as e:
                    msg.error(f"Command failed: {command}\nError: {e}")
                    sys.exit(1)
            elif isinstance(command, dict):
                # Dictionary command with potential "present" flag
                cmd = command.get("command")
                quiet = command.get("quiet", False)

                if cmd:
                    try:
                        if quiet:
                            msg.progress(f"$ {cmd}")
                            subprocess.run(
                                cmd, shell=True, check=True, stdout=subprocess.PIPE
                            )
                        else:
                            subprocess.run(cmd, shell=True, check=True)
                    except subprocess.CalledProcessError as e:
                        msg.error(f"Command failed: {cmd}\nError: {e}")
                        sys.exit(1)


def get_apkeditor_cmd(editor_jar):
    apkeditor_cmd = shutil.which("apkeditor")
    if apkeditor_cmd:
        return "apkeditor"
    elif editor_jar:
        return f"java -jar {editor_jar}"
    else:       
        msg.error("The selected package does not have command settings.")
        msg.info("Config: Required \"editor_jar\" in \"commands\". ")
        msg.info("Cannot decode APK without commands settings.")
        sys.exit(1)


def apkeditor_merge(editor_jar, apk_file, merge_base_apk):
    # New base name of apk_file end with .apk
    command = (
        f'${get_apkeditor_cmd(editor_jar)} m -i "{apk_file}" -o "{merge_base_apk}"'
    )
    run_commands([command])


def apkeditor_decode(editor_jar, apk_file, output_dir, dex=False):
    if not shutil.which("java"):
        msg.error("Java is not installed. Please install Java to proceed.")
        sys.exit(1)
    merge_base_apk = apk_file.rsplit(".", 1)[0] + ".apk"
    # If apk_file is not end with .apk then merge
    if not apk_file.endswith(".apk") and not os.path.exists(merge_base_apk):
        apkeditor_merge(editor_jar, apk_file, merge_base_apk)
        output_dir = merge_base_apk.rsplit(".", 1)[0]
        command = f'{get_apkeditor_cmd(editor_jar)} d -i "{merge_base_apk}" -o "{output_dir}"'
    else:
        command = (
            f'{get_apkeditor_cmd(editor_jar)} d -i "{apk_file}" -o "{output_dir}"'
        )
    if dex:
        command += " -dex"
    run_commands([command])


def apkeditor_build(editor_jar, input_dir, output_apk):
    if not shutil.which("java"):
        msg.error("Java is not installed. Please install Java to proceed.")
        sys.exit(1)
    command = f'{get_apkeditor_cmd(editor_jar)} b -i "{input_dir}" -o "{output_apk}"'
    run_commands([command])


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
    print_rainbow_art("DemodAPK", bold=True, font="small")
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

    if os.path.isfile(apk_dir):
        # Extract preconfigured package names
        available_packages = list(config.get("DemodAPK", {}).keys())

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
    dex_option = apk_config.get("dex", False)
    manifest_edit_level = apk_config.get("level", 0)
    facebook_config = apk_config.get("facebook", {})
    facebook_appid = facebook_config.get("app_id", "")
    fb_client_token = facebook_config.get("client_token", "")
    fb_login_protocol_scheme = facebook_config.get("login_protocol_scheme", "")
    new_package_name = apk_config.get("package", "")
    new_package_path = "L" + new_package_name.replace(".", "/")
    editor_jar = apk_config.get("commands", {}).get("editor_jar", "")
    files_entry = apk_config.get("files", {})
    # Log a warning if dex folder is found
    if log_level and dex_folder_exists:
        msg.warning(
            "Dex folder found. Some functions will be disabled.",
            bold=True,
            underline=True,
        )

    # Decode APK if input is an APK file
    if os.path.isfile(apk_dir):
        if args.force:
            shutil.rmtree(decoded_dir, ignore_errors=True)
        if not os.path.exists(decoded_dir):
            apkeditor_decode(editor_jar, apk_dir, decoded_dir, dex=dex_option)
        apk_dir = decoded_dir

    # Run pre-modification commands
    os.environ["BASE"] = apk_dir
    if "commands" in apk_config and "begin" in apk_config["commands"]:
        run_commands(apk_config.get("commands", {}).get("begin", []))

    # Paths
    resources_folder = os.path.join(apk_dir, "resources")
    smali_folder = os.path.join(apk_dir, "smali") if not dex_option else None
    value_strings = os.path.join(resources_folder, "package_1/res/values/strings.xml")
    if not android_manifest:
        android_manifest = os.path.join(apk_dir, "AndroidManifest.xml")

    # Modify APK contents
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
    output_apk = os.path.basename(apk_dir.rstrip("/"))
    output_apk_path = os.path.join(apk_dir, output_apk + ".apk")

    if not os.path.exists(output_apk_path) or shutil.which("apkeditor") or "editor_jar" in apk_config["command"]:
        apkeditor_build(editor_jar, apk_dir, output_apk_path)

    # Run post-modification commands
    os.environ["BUILD"] = output_apk_path
    if "commands" in apk_config and "end" in apk_config["commands"]:
        run_commands(apk_config.get("commands", {}).get("end", []))

    msg.info("APK modification finished!", bold=True)


if __name__ == "__main__":
    main()
