#!/bin/python

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


class Colors:
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
    OLD_PACKAGE_NAME = None
    OLD_PACKAGE_PATH = None

    if os.path.isfile(manifest_file):
        with open(manifest_file, "r", encoding="utf-8") as file:
            content = file.read()

        # Extract the package name using regex
        package_name_match = re.search(r'package="([\w\.]+)"', content)
        if package_name_match:
            OLD_PACKAGE_NAME = package_name_match.group(1)
            OLD_PACKAGE_PATH = "L" + OLD_PACKAGE_NAME.replace(".", "/")
        else:
            print(
                f"{Colors.RED}Package name not found in {manifest_file}.{Colors.RESET}"
            )
    else:
        print(
            f"{
                Colors.RED}AndroidManifest.xml not found. Skipping package name extraction.{
                Colors.RESET}")

    return OLD_PACKAGE_NAME, OLD_PACKAGE_PATH


# Function to replace specific values in strings.xml
def replace_values_in_strings_file(
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
        print(f"{Colors.GREEN}Updated string values in {strings_file}.{Colors.RESET}")
    else:
        print(
            f"{
                Colors.YELLOW}File '{strings_file}' does not exist. Skipping string value replacements.{
                Colors.RESET}")


# Function to replace lib.so with libpatch.so
def replace_lib_so(lib_file, lib_patch_file):
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
            # content = re.sub(f'android:taskAffinity="{old_package_name}"', f'android:taskAffinity="{new_package_name}"', content)
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
            # content = re.sub(f'android:host="{old_package_name}"', f'android:host="{new_package_name}"', content)
            # content = re.sub(f'android:host="cct\.{old_package_name}"', f'android:host="cct.{new_package_name}"', content)

            with open(manifest_file, "w", encoding="utf-8") as file:
                file.write(content)
            print(
                f"{Colors.GREEN}Updated package name in {manifest_file}.{Colors.RESET}"
            )
        except Exception as e:
            print(f"{Colors.RED}Error processing {manifest_file}: {e}{Colors.RESET}")
    else:
        print(
            f"{
                Colors.RED}AndroidManifest.xml not found. Skipping package renaming in manifest.{
                Colors.RESET}")


# Function to rename package in smali files while excluding specific files
def update_smali_path_package(
    smali_dir, old_package_path, new_package_path, excluded_files
):
    for root, dirs, files in os.walk(smali_dir):
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
    for root, dirs, files in os.walk(resources_dir):
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
                f"{Colors.YELLOW}Directory {old_dir} does not exist. Skipping renaming.{Colors.RESET}"
            )

    if not renamed:
        print(
            f"{
                Colors.YELLOW}No directories matching {old_package_path} were found. Skipping renaming.{
                Colors.RESET}")


def update_application_id_in_smali(
        smali_dir,
        old_package_name,
        new_package_name):
    for root, dirs, files in os.walk(smali_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith("BuildConfig.smali"):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Replace APPLICATION_ID
                new_content = content.replace(
                    f'.field public static final APPLICATION_ID:Ljava/lang/String; = "{old_package_name}"',
                    f'.field public static final APPLICATION_ID:Ljava/lang/String; = "{new_package_name}"',
                )

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)

    print(f"{Colors.GREEN}Updated APPLICATION_ID in smali files.{Colors.RESET}")


def remove_metadata_from_manifest(manifest_file):
    if os.path.isfile(manifest_file):
        with open(manifest_file, "r", encoding="utf-8") as file:
            lines = file.readlines()

        # Define the metadata to search for and remove
        metadata_to_remove = [
            "com.google.android.gms.games.APP_ID",
            # 'com.google.android.gms.games.unityVersion'
        ]

        # Filter out lines that match the metadata
        filtered_lines = []
        skip = False
        for line in lines:
            # Check if the line contains one of the metadata names
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
            f"{Colors.GREEN}Removed specified metadata from {manifest_file}.{Colors.RESET}"
        )
    else:
        print(
            f"{
                Colors.RED}File '{manifest_file}' does not exist. Skipping metadata removal.{
                Colors.RESET}")


def check_for_dex_folder(apk_dir):
    """Check if a 'dex' folder exists in the specified APK directory."""
    dex_folder_path = os.path.join(
        apk_dir, "dex")  # Adjust the path if necessary
    return os.path.isdir(dex_folder_path)


def main():
    print_rainbow_figlet("DemodAPk")

    # Default configuration structure
    default_config = {
        "facebook": {
            "app_id": "",
            "client_token": "",
            "login_protocol_scheme": ""},
        "package": {
            "new_name": "",
            "new_path": ""},
        "paths": {
            "strings_file": "",
            "lib_file": "",
            "lib_patch_file": "",
            "android_manifest": "",
            "excluded_smali_files": [],
        },
    }

    # Set up argument parsing
    parser = argparse.ArgumentParser(
        description="DemodAPk: An APK Modification Script")

    # Argument parsing
    parser.add_argument(
        "apk_dir", nargs="?", help="Path to the APK directory"
    )  # Optional positional argument
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
        default="config.json",  # Default config file
        help="Path to the JSON configuration file.",
    )
    parser.add_argument(
        "-yd",
        "--move-rename-smali",
        action="store_true",
        help="Rename package in smali files and the smali directory.",
    )
    args = parser.parse_args()

    # Check if config file exists, if not, create it with default values
    if not os.path.isfile(args.config):
        with open(args.config, "w") as file:
            json.dump(default_config, file, indent=4)
        print(
            f"Configuration file '{
                args.config}' not found. Created default config file.")
        # Exit after creating the file to allow editing before next run
        sys.exit(0)

    # Load configuration from the specified JSON file
    try:
        with open(args.config, "r") as file:
            config = json.load(file)
    except json.JSONDecodeError:
        print(
            f"Error: Configuration file '{
                args.config}' is not a valid JSON file.")
        sys.exit(1)

    # Accessing values from the configuration with empty default values
    FB_APPID = config.get("facebook", {}).get("app_id", "")
    FB_CLIENT_TOKEN = config.get("facebook", {}).get("client_token", "")
    FB_LOGIN_PROTOCOL_SCHEME = config.get("facebook", {}).get(
        "login_protocol_scheme", ""
    )

    NEW_PACKAGE_NAME = config.get("package", {}).get("new_name", "")
    NEW_PACKAGE_PATH = config.get("package", {}).get("new_path", "")

    STRINGS_FILE_RELATIVE_PATH = config.get(
        "paths", {}).get("strings_file", "")
    LIB_FILE_RELATIVE_PATH = config.get("paths", {}).get("lib_file", "")
    LIB_PATCH_FILE_RELATIVE_PATH = config.get(
        "paths", {}).get("lib_patch_file", "")
    ANDROID_MANIFEST_FILE = config.get("paths", {}).get("android_manifest", "")
    EXCLUDED_SMALI_FILES = config.get(
        "paths", {}).get(
        "excluded_smali_files", [])

    # Get APK directory input from the command line or ask for input if not
    # provided
    if args.apk_dir:
        apk_dir = args.apk_dir
    else:
        apk_dir = input("Please enter the path to the APK directory: ")

    # Verify the APK directory path
    if not os.path.exists(apk_dir):
        print(f"Error: The directory {apk_dir} does not exist.")
        return

    skip_package_rename = args.no_rename_package

    # Check if the dex folder exists
    dex_folder_exists = check_for_dex_folder(apk_dir)
    if dex_folder_exists:
        print(
            f"{
                Colors.BOLD}{
                Colors.UNDERLINE}{
                Colors.YELLOW}Dex folder found. Certain functions will be disabled.{
                    Colors.RESET}")

    # Define the full paths to the required files based on the APK directory
    strings_file = os.path.join(apk_dir, STRINGS_FILE_RELATIVE_PATH)
    lib_file = os.path.join(apk_dir, LIB_FILE_RELATIVE_PATH)
    lib_patch_file = LIB_PATCH_FILE_RELATIVE_PATH
    manifest_file = os.path.join(apk_dir, ANDROID_MANIFEST_FILE)
    smali_dir = os.path.join(apk_dir, "smali")
    resources_dir = os.path.join(
        apk_dir, "resources"
    )  # Adjust based on actual structure
    OLD_PACKAGE_NAME, OLD_PACKAGE_PATH = extract_package_info(manifest_file)

    # Feature 1: Replace values in strings.xml and lib.so
    replace_values_in_strings_file(
        strings_file, FB_APPID, FB_CLIENT_TOKEN, FB_LOGIN_PROTOCOL_SCHEME
    )
    replace_lib_so(lib_file, lib_patch_file)

    # Feature 2: Conditionally rename package name in manifest and resources
    if not skip_package_rename:
        rename_package_in_manifest(
            manifest_file,
            OLD_PACKAGE_NAME,
            NEW_PACKAGE_NAME)
        rename_package_in_resources(
            resources_dir,
            OLD_PACKAGE_NAME,
            NEW_PACKAGE_NAME)

        # Disable certain functions if dex folder exists
        if not dex_folder_exists:
            if args.move_rename_smali:
                update_smali_path_package(
                    smali_dir,
                    OLD_PACKAGE_PATH,
                    NEW_PACKAGE_PATH,
                    EXCLUDED_SMALI_FILES)
                update_smali_directory(
                    smali_dir, OLD_PACKAGE_PATH, NEW_PACKAGE_PATH)
            else:
                update_application_id_in_smali(
                    smali_dir, OLD_PACKAGE_NAME, NEW_PACKAGE_NAME
                )
    else:
        print(
            f"{Colors.YELLOW}Skipping package renaming as requested (using -n flag).{Colors.RESET}"
        )

    # Optionally, you can call the remove_metadata_from_manifest function if
    # needed
    remove_metadata_from_manifest(manifest_file)

    print(f"{Colors.GREEN}APK modification completed.{Colors.RESET}")


if __name__ == "__main__":
    main()
