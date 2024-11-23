#!/bin/python

import os
import re
import sys
import glob
import json
import shutil
import argparse
try:
    from art import text2art
except ImportError:
    text2art = None


# Define base ANSI color codes for the rainbow
base_rainbow_colors = [
    "31",  # Red
    "33",  # Yellow
    "32",  # Green
    "36",  # Cyan
    "34",  # Blue
    "35",  # Magenta
]


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
    lines = ascii_art.splitlines()
    # Apply rainbow colors line by line
    for i, line in enumerate(lines):
        color = rainbow_colors[i % len(rainbow_colors)]
        print(color + line + "\033[0m")  # Reset color after each line


class Colors:  # pylint: disable=too-few-public-methods
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    PURPLE = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"


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
            print(
                f"{Colors.RED}Package name not found in {
                    manifest_file}.{Colors.RESET}"
            )
    else:
        print(
            f"{Colors.RED}AndroidManifest.xml not found. Skipping package name extraction.{
                Colors.RESET}"
        )

    return package_name, package_path


def replace_values_in_strings_file(strings_file, fb_app_id, fb_client_token, fb_login_protocol_scheme):
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
            f'<string name="fb_login_protocol_scheme">{
                fb_login_protocol_scheme}</string>',
            content,
        )

        with open(strings_file, "w", encoding="utf-8") as file:
            file.write(content)
        print(f"{Colors.GREEN}Updated string values in {
              strings_file}.{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}File '{strings_file}' does not exist. Skipping string value replacements.{
              Colors.RESET}")


def replace_files_from_loaded(config, apk_dir):
    # Process each file replacement
    for item in config.get("files", []):
        # Ensure the item is a dictionary with the "replace" key
        if not isinstance(item, dict) or "replace" not in item:
            print(f"{Colors.RED}Invalid entry in config: {
                  item}. Skipping...{Colors.RESET}")
            continue
        replace_info = item.get("replace", {})
        target_file = replace_info.get("target")
        source_file = replace_info.get("source")
        # Default to False if not present
        backup = replace_info.get("backup", False)

        if not target_file or not source_file:
            print(f"{Colors.RED}Invalid entry in config: {item}{Colors.RESET}")
            continue

        # Ensure that the target file is inside the apk_dir
        target_path = os.path.join(apk_dir, target_file)

        # Check if the source file exists (anywhere on the filesystem)
        if not os.path.isfile(source_file):
            print(f"{Colors.RED}Source file not found: {
                  source_file}. Skipping replacement.{Colors.RESET}")
            continue

        # Perform backup if required
        if backup:
            backup_file = f"{target_path}.bak"
            try:
                shutil.copyfile(target_path, backup_file)
                print(f"{Colors.YELLOW}Backup created: {
                      backup_file}{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.RED}Error creating backup for {
                      target_path}: {e}{Colors.RESET}")

        # Perform the file replacement (source file to target location)
        try:
            # Copy the source to the target location
            shutil.copyfile(source_file, target_path)
            print(f"{Colors.GREEN}Replaced {target_path} with {
                  source_file}.{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}Error replacing {
                  target_path}: {e}{Colors.RESET}")


# Function to rename package in AndroidManifest.xml
def rename_package_in_manifest(manifest_file, old_package_name, new_package_name):
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

            print(f"{Colors.GREEN}Updated package name in {
                  manifest_file}.{Colors.RESET}")

        except FileNotFoundError:
            print(f"{Colors.RED}Error: The manifest file '{manifest_file}' was not found.{
                  Colors.RESET}")
        except IOError as e:
            print(f"{Colors.RED}Error reading or writing '{
                  manifest_file}': {e}{Colors.RESET}")
        except re.error as e:
            print(f"{Colors.RED}Error with regular expression: {e}{Colors.RESET}")
        # Removed the general exception catch
    else:
        print(
            f"{Colors.RED}AndroidManifest.xml not found. Skipping package renaming in manifest.{
                Colors.RESET}"
        )


def update_smali_path_package(smali_dir, old_package_path, new_package_path):
    for root, _, files in os.walk(smali_dir):
        for file in files:
            file_path = os.path.join(root, file)
            # Skip excluded files
            # if any(excluded_file in file_path for excluded_file in excluded_files):
            #    print(
            #        f"{Colors.YELLOW}Skipping {file_path} as it's excluded.{Colors.RESET}"
            #    )
            #    continue

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
def rename_package_in_resources(resources_dir, old_package_name, new_package_name):
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
    old_package_pattern = os.path.join(
        smali_dir, "**", old_package_path.strip("L")
    )  # Use '**' to search in subdirectories
    # Recursively find all matching directories
    old_dirs = glob.glob(old_package_pattern, recursive=True)

    renamed = False  # Track if any directory was renamed

    for old_dir in old_dirs:
        # Create the new directory path based on the found old directory
        new_dir = old_dir.replace(old_package_path.strip(
            "L"), new_package_path.strip("L"))

        if os.path.isdir(old_dir):
            # Rename the old directory to the new directory
            os.rename(old_dir, new_dir)
            print(f"{Colors.GREEN}Renamed directory {
                  old_dir} to {new_dir}.{Colors.RESET}")
            renamed = True
        else:
            print(f"{Colors.YELLOW}Directory {old_dir} does not exist. Skipping renaming.{
                  Colors.RESET}")

    if not renamed:
        print(f"{Colors.YELLOW}No directories matching {old_package_path} were found. Skipping renaming.{
              Colors.RESET}")


def update_application_id_in_smali(smali_dir, old_package_name, new_package_name):
    for root, _, files in os.walk(smali_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith("BuildConfig.smali"):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Replace APPLICATION_ID
                new_content = content.replace(
                    f' APPLICATION_ID:Ljava/lang/String; = "{
                        old_package_name}"',
                    f' APPLICATION_ID:Ljava/lang/String; = "{
                        new_package_name}"',
                )

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)

    print(f"{Colors.GREEN}Updated APPLICATION_ID in smali files.{Colors.RESET}")


def remove_metadata_from_manifest(manifest_file, config_file):
    # Filter out any empty strings in metadata_to_remove
    metadata_to_remove = [
        meta for meta in config_file.get("metadata_to_remove", []) if meta.strip()
    ]

    # If metadata_to_remove is empty or only contained empty strings, skip removal
    if not metadata_to_remove:
        print(
            f"{Colors.YELLOW}No valid metadata entries specified for removal in configuration file.{
                Colors.RESET}"
        )
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
        print(
            f"{Colors.GREEN}Removed specified metadata from {
                manifest_file}.{Colors.RESET}"
        )
    else:
        print(
            f"{Colors.RED}File '{manifest_file}' does not exist. Skipping metadata removal.{
                Colors.RESET}"
        )


def check_for_dex_folder(apk_dir):
    dex_folder_path = os.path.join(
        apk_dir, "dex")  # Adjust the path if necessary
    return os.path.isdir(dex_folder_path)


def create_default_config(config_path, default_config):
    with open(config_path, "w", encoding="utf-8") as file:
        json.dump(default_config, file, indent=4)
    print(f"Configuration file '{
          config_path}' not found. Created default config file.")
    sys.exit(0)


def load_config(config_path):
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        print(f"Error: Configuration file '{
              config_path}' is not a valid JSON file.")
        sys.exit(1)


def parse_arguments():
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
    if not os.path.exists(apk_dir):
        print(f"Error: The directory {apk_dir} does not exist.")
        sys.exit(1)
    return apk_dir


def main():
    print_rainbow_art("DemodAPK", bold=True)
    default_config = {
        "facebook": {
            "app_id": "",
            "client_token": "",
            "login_protocol_scheme": ""
        },
        "package": {
            "new_name": "",
            "new_path": ""
        },
        "files": [
            {
                "replace": {
                    "target": "",
                    "source": "",
                    "backup": False
                }
            }
        ],
        "metadata_to_remove": [],
        "Patcher": {
            "input_file": "",
            "dump_file": "",
            "output_file": "",
            "patches": [
                {
                    "method_name": "",
                    "hex_code": ""
                },
                {
                    "offset": "",
                    "hex_code": ""
                },
                {
                    "wildcard": "",
                    "hex_code": ""
                }
            ]
        }
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

    android_manifest = os.path.join(apk_dir, "AndroidManifest.xml")
    resources_folder = os.path.join(apk_dir, "resources")
    smali_folder = os.path.join(apk_dir, "smali")
    value_strings = os.path.join(
        resources_folder, "package_1/res/values/strings.xml")

    dex_folder_exists = check_for_dex_folder(apk_dir)
    if dex_folder_exists:
        print(
            f"{Colors.BOLD}{Colors.UNDERLINE}{Colors.YELLOW}Dex folder found. Certain functions will be disabled.{
                Colors.RESET}"
        )

    package_orig_name, package_orig_path = extract_package_info(
        android_manifest)
    replace_values_in_strings_file(
        value_strings, facebook_appid, fb_client_token, fb_login_protocol_scheme
    )

    replace_files_from_loaded(config, apk_dir)
    if not args.no_rename_package:
        rename_package_in_manifest(
            android_manifest, package_orig_name, new_package_name
        )
        rename_package_in_resources(
            resources_folder, package_orig_name, new_package_name
        )

        if not dex_folder_exists and args.move_rename_smali:
            update_smali_path_package(
                smali_folder, package_orig_path, new_package_path)
            update_smali_directory(
                smali_folder, package_orig_path, new_package_path)
        if not dex_folder_exists:
            update_application_id_in_smali(
                smali_folder, package_orig_name, new_package_name
            )
    else:
        print("Skipping package renaming as requested (using -n flag).")

    remove_metadata_from_manifest(android_manifest, config)
    print(f"{Colors.GREEN}APK modification completed.{Colors.RESET}")


if __name__ == "__main__":
    main()
