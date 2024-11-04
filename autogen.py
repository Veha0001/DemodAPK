#!/bin/python
"an APK Modification tool"

import os
import re
import sys
import glob
import json
import shutil
import argparse
import itertools

try:
    import pyfiglet

    PYFIGLET_INSTALLED = True
except ImportError:
    PYFIGLET_INSTALLED = False


class Colors:  # pylint: disable=too-few-public-methods
    "highlight colors"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    PURPLE = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"


# Define the rainbow colors using the Colors class
rainbow_colors = [
    Colors.RED,
    Colors.YELLOW,
    Colors.GREEN,
    Colors.CYAN,
    Colors.BLUE,
    Colors.PURPLE,
]


def print_rainbow_figlet(text):
    "Print logo with rainbow_colors"
    if PYFIGLET_INSTALLED:
        # Create the figlet text
        figlet_text = pyfiglet.figlet_format(text)

        # Generate colored text
        color_iter = itertools.cycle(rainbow_colors)
        colored_output = ""

        for char in figlet_text:
            if char in ["\n", "\r"]:
                colored_output += char
            else:
                colored_output += next(color_iter) + char

        # Reset color at the end
        colored_output += Colors.RESET

        print(colored_output)

def extract_package_info(manifest_file):
    "Find App Package"
    package_orig_name = None
    package_orig_path = None

    if os.path.isfile(manifest_file):
        with open(manifest_file, "r", encoding="utf-8") as file:
            content = file.read()

        # Extract the package name using regex
        package_name_match = re.search(r'package="([\w\.]+)"', content)
        if package_name_match:
            package_orig_name = package_name_match.group(1)
            package_orig_path = "L" + package_orig_name.replace(".", "/")
        else:
            print(
                f"{Colors.RED}Package name not found in {manifest_file}.{Colors.RESET}"
            )
    else:
        print(
            f"{
                Colors.RED}AndroidManifest.xml not found. Skipping package name extraction.{
                Colors.RESET}")

    return package_orig_name, package_orig_path


def replace_values_in_strings_file(
    strings_file, fb_app_id, fb_client_token, fb_login_protocol_scheme
):
    "Function to replace specific values in strings.xml"
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
            r'<string name="fb_client_token">.*?</string>',
            f'<string name="fb_client_token">{fb_client_token}</string>',
            content,
        )
        content = re.sub(
            r'<string name="fb_login_protocol_scheme">.*?</string>',
            f'<string name="fb_login_protocol_scheme">{fb_login_protocol_scheme}</string>',
            content,
        )

        with open(strings_file, "w", encoding="utf-8") as file:
            file.write(content)
        print(f"{Colors.GREEN}Updated string values in {strings_file}.{Colors.RESET}")
    else:
        print(
            f"{Colors.YELLOW}File '{strings_file}' does not exist. Skipping string value replacements.{Colors.RESET}"  # pylint: disable=line-too-long
        )


# Function to replace lib.so with libpatch.so
def replace_lib_so(lib_file, lib_patch_file):
    "replace a file in libs folder"
    if os.path.isfile(lib_file) and os.path.isfile(lib_patch_file):
        shutil.copyfile(lib_patch_file, lib_file)
        print(f"{Colors.GREEN}Replaced {lib_file} with {lib_patch_file}.{Colors.RESET}")
    else:
        print(
            f"{Colors.RED}lib.so or libpatch.so not found. Skipping replacement.{Colors.RESET}"
        )


# Function to rename package in AndroidManifest.xml
def rename_package_in_manifest(
        manifest_file,
        old_package_name,
        new_package_name):
    "Rename Package in AndroidManifest.xml"
    if os.path.isfile(manifest_file):
        try:
            with open(manifest_file, "r", encoding="utf-8") as file:
                content = file.read()

            # Normalize line endings (for Windows compatibility)
            content = content.replace("\r\n", "\n")

            # Replace package name and authorities
            content = re.sub(
                f'package="{old_package_name}"',
                f'package="{new_package_name}"',
                content,
            )
            # pyright: ignore[

            # content = re.sub(
            # f'android:taskAffinity="{old_package_name}"',
            # f'android:taskAffinity="{new_package_name}"',
            # content,
            # )]

            content = re.sub(
                f'android:name="{old_package_name}\\.',
                f'android:name="{new_package_name}.',
                content,
            )
            content = re.sub(
                f'android:authorities="{old_package_name}\\.',
                f'android:authorities="{new_package_name}.',
                content,
            )
            # content = re.sub(
            #    f'android:host="{old_package_name}"',
            #    f'android:host="{new_package_name}"',
            #    content,
            # )
            # content = re.sub(
            #    f'android:host="cct\.{old_package_name}"',
            #    f'android:host="cct.{new_package_name}"',
            #    content,
            # )

            with open(manifest_file, "w", encoding="utf-8") as file:
                file.write(content)

            print(
                f"{Colors.GREEN}Updated package name in {manifest_file}.{Colors.RESET}"
            )

        except FileNotFoundError:
            print(
                f"{Colors.RED}Error: The manifest file '{manifest_file}' was not found.{Colors.RESET}"  # pylint: disable=line-too-long
            )
        except IOError as e:
            print(
                f"{Colors.RED}Error reading or writing '{manifest_file}': {e}{Colors.RESET}"
            )
        except re.error as e:
            print(f"{Colors.RED}Error with regular expression: {e}{Colors.RESET}")
        # Removed the general exception catch
    else:
        print(
            f"{Colors.RED}AndroidManifest.xml not found. Skipping package renaming in manifest.{Colors.RESET}"  # pylint: disable=line-too-long
        )


def update_smali_path_package(smali_dir, old_package_path, new_package_path, excluded_files):  # pylint: disable=line-too-long
    "Update smali package paths"
    for root, _, files in os.walk(smali_dir):
        for file in files:
            file_path = os.path.join(root, file)
            # Skip excluded files
            if any(excluded_file in file_path for excluded_file in excluded_files):
                print(
                    f"{Colors.YELLOW}Skipping {file_path} as it's excluded.{Colors.RESET}"
                )
                continue

            if file.endswith(".smali"):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Replace old package name with new one
                new_content = content.replace(
                    old_package_path, new_package_path)

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)

    print(f"{Colors.GREEN}Updated package name in smali files.{Colors.RESET}")


# Function to rename package in resources files
def rename_package_in_resources(
        resources_dir,
        old_package_name,
        new_package_name):
    "Update Package Name in resources"
    for root, _, files in os.walk(resources_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith(".xml") or file.endswith(
                ".json"
            ):  # Adjust based on file types
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Replace old package name with new one
                new_content = content.replace(
                    f'"{old_package_name}"', f'"{new_package_name}"'
                )

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)

    print(f"{Colors.GREEN}Updated package name in resources files.{Colors.RESET}")


def update_smali_directory(smali_dir, old_package_path, new_package_path):
    # Use glob to find all directories in the smali_dir that match the old
    # package path
    "Move dirs with the new package"
    old_package_pattern = os.path.join(
        smali_dir, "**", old_package_path.strip("L")
    )  # Use '**' to search in subdirectories
    old_dirs = glob.glob(
        old_package_pattern, recursive=True
    )  # Recursively find all matching directories

    renamed = False  # Track if any directory was renamed

    for old_dir in old_dirs:
        # Create the new directory path based on the found old directory
        new_dir = old_dir.replace(
            old_package_path.strip("L"), new_package_path.strip("L")
        )

        if os.path.isdir(old_dir):
            # Rename the old directory to the new directory
            os.rename(old_dir, new_dir)
            print(
                f"{Colors.GREEN}Renamed directory {old_dir} to {new_dir}.{Colors.RESET}"
            )
            renamed = True
        else:
            print(
                f"{Colors.YELLOW}Directory {old_dir} does not exist. Skipping renaming.{Colors.RESET}"  # pylint: disable=line-too-long
            )

    if not renamed:
        print(
            f"{Colors.YELLOW}No directories matching {old_package_path} were found. Skipping renaming.{Colors.RESET}"  # pylint: disable=line-too-long
        )


def update_application_id_in_smali(
        smali_dir,
        old_package_name,
        new_package_name):
    "Update APPLICATION_ID in BuildConfig.smali for some APPLICATION & GAME"
    for root, _, files in os.walk(smali_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith("BuildConfig.smali"):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Replace APPLICATION_ID
                new_content = content.replace(
                    f' APPLICATION_ID:Ljava/lang/String; = "{old_package_name}"',
                    f' APPLICATION_ID:Ljava/lang/String; = "{new_package_name}"',
                )

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)

    print(f"{Colors.GREEN}Updated APPLICATION_ID in smali files.{Colors.RESET}")

def remove_metadata_from_manifest(manifest_file, config_file):
    """Removes specified metadata in the AndroidManifest"""

    # Filter out any empty strings in metadata_to_remove
    metadata_to_remove = [meta for meta in config_file.get("metadata_to_remove", []) if meta.strip()] # pylint: disable=line-too-long

    # If metadata_to_remove is empty or only contained empty strings, skip removal
    if not metadata_to_remove:
        print(f"{Colors.YELLOW}No valid metadata entries specified for removal in configuration file.{Colors.RESET}") # pylint: disable=line-too-long
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
        print(f"{Colors.GREEN}Removed specified metadata from {manifest_file}.{Colors.RESET}")
    else:
        print(f"{Colors.RED}File '{manifest_file}' does not exist. Skipping metadata removal.{Colors.RESET}") # pylint: disable=line-too-long

def check_for_dex_folder(apk_dir):
    """Check if a 'dex' folder exists in the specified APK directory."""
    dex_folder_path = os.path.join(
        apk_dir, "dex")  # Adjust the path if necessary
    return os.path.isdir(dex_folder_path)


def create_default_config(config_path, default_config):
    "Create config file before run the code."
    with open(config_path, "w", encoding="utf-8") as file:
        json.dump(default_config, file, indent=4)
    print(
        f"Configuration file '{config_path}' not found. Created default config file.")
    sys.exit(0)


def load_config(config_path):
    "Load config file."
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        print(
            f"Error: Configuration file '{config_path}' is not a valid JSON file.")
        sys.exit(1)


def parse_arguments():
    "Argument"
    parser = argparse.ArgumentParser(
        description="DemodAPk: An APK Modification Script")
    parser.add_argument("apk_dir", nargs="?", help="Path to the APK directory")
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
        "-yd",
        "--move-rename-smali",
        action="store_true",
        help="Rename package in smali files and the smali directory.",
    )
    return parser.parse_args()


def verify_apk_directory(apk_dir):
    "$1"
    if not os.path.exists(apk_dir):
        print(f"Error: The directory {apk_dir} does not exist.")
        sys.exit(1)
    return apk_dir


def setup_paths(apk_dir, config):
    "Join config"
    paths = config.get("paths", {})
    return {
        "strings_file": os.path.join(
            apk_dir, paths.get(
                "strings_file", "")), "lib_file": os.path.join(
            apk_dir, paths.get(
                "lib_file", "")), "lib_patch_file": paths.get(
            "lib_patch_file", ""), "android_manifest": os.path.join(
            apk_dir, paths.get(
                "android_manifest", "")), "smali_dir": os.path.join(
            apk_dir, "smali"), "resources_dir": os.path.join(
            apk_dir, "resources"), }


def main():
    "The Main functions."
    print_rainbow_figlet("DemodAPk")
    default_config = {
        "facebook": {
            "app_id": "",
            "client_token": "",
            "login_protocol_scheme": ""},
        "package": {
            "new_name": "",
            "new_path": ""},
        "paths": {
            "strings_file": "resources/package_1/res/values/strings.xml",
            "lib_file": "",
            "lib_patch_file": "",
            "android_manifest": "AndroidManifest.xml",
            "excluded_smali_files": [],
        },
        "metadata_to_remove": [],
        "Patcher": {}
    }

    args = parse_arguments()
    if not os.path.isfile(args.config):
        create_default_config(args.config, default_config)

    config = load_config(args.config)
    facebook_appid = config.get("facebook", {}).get("app_id", "")
    fb_client_token = config.get("facebook", {}).get("client_token", "")
    fb_login_protocol_scheme = config.get("facebook", {}).get(
        "login_protocol_scheme", ""
    )
    new_package_name = config.get("package", {}).get("new_name", "")
    new_package_path = config.get("package", {}).get("new_path", "")
    apk_dir = args.apk_dir or input(
        "Please enter the path to the APK directory: ")
    apk_dir = verify_apk_directory(apk_dir)
    paths = setup_paths(apk_dir, config)

    dex_folder_exists = check_for_dex_folder(apk_dir)
    if dex_folder_exists:
        print(f"{Colors.BOLD}{Colors.UNDERLINE}{Colors.YELLOW}Dex folder found. Certain functions will be disabled.{Colors.RESET}")  # pylint: disable=line-too-long


    package_orig_name, package_orig_path = extract_package_info(
        paths["android_manifest"]
    )
    replace_values_in_strings_file(
        paths["strings_file"],
        facebook_appid,
        fb_client_token,
        fb_login_protocol_scheme)
    replace_lib_so(paths["lib_file"], paths["lib_patch_file"])

    if not args.no_rename_package:
        rename_package_in_manifest(
            paths["android_manifest"], package_orig_name, new_package_name
        )
        rename_package_in_resources(
            paths["resources_dir"], package_orig_name, new_package_name
        )

        if not dex_folder_exists and args.move_rename_smali:
            update_smali_path_package(
                paths["smali_dir"],
                package_orig_path,
                new_package_path,
                config["paths"]["excluded_smali_files"],
            )
            update_smali_directory(
                paths["smali_dir"], package_orig_path, new_package_path
            )
        if not dex_folder_exists:
            update_application_id_in_smali(
                paths["smali_dir"], package_orig_name, new_package_name
            )
    else:
        print("Skipping package renaming as requested (using -n flag).")

    remove_metadata_from_manifest(paths["android_manifest"], config)
    print(f"{Colors.GREEN}APK modification completed.{Colors.RESET}")

if __name__ == "__main__":
    main()
