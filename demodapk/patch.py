"""
APK patching utilities module.

This module provides functions for modifying APK components including:
- Package name updates in manifest and resources
- App name modifications
- Facebook integration settings
- Smali code modifications
- Build configuration updates
- Metadata management
"""

import glob
import os
import re

from demodapk.utils import msg


def extract_package_info(manifest_file):
    """
    Extract package name and path from AndroidManifest.xml.

    Args:
        manifest_file (str): Path to AndroidManifest.xml file

    Returns:
        tuple: (package_name, package_path) where:
            - package_name (str): Android package name
            - package_path (str): Package path in smali format

    Raises:
        FileNotFoundError: If manifest file doesn't exist
    """
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
    """
    Update application name in strings.xml resource file.

    Args:
        app_name (str): New application name
        value_strings (str): Path to strings.xml resource file

    Returns:
        None
    """
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

    msg.success(f"Updated app name to: [reset]{app_name}")


def update_facebook_app_values(strings_file, fb_app_id, fb_client_token, fb_login_protocol_scheme):
    """
    Update Facebook integration settings in strings.xml.

    Args:
        strings_file (str): Path to strings.xml file
        fb_app_id (str): Facebook application ID
        fb_client_token (str): Facebook client token
        fb_login_protocol_scheme (str): Facebook login protocol scheme

    Returns:
        None
    """
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
        msg.success("Updated facebook app values.")
    else:
        msg.error(f"File: {strings_file}, does not exists.")


def rename_package_in_manifest(manifest_file, old_package_name, new_package_name, level=0):
    """
    Update package name references in AndroidManifest.xml.

    Args:
        manifest_file (str): Path to AndroidManifest.xml
        old_package_name (str): Original package name
        new_package_name (str): New package name to use
        level (int): Modification level (0-4) controlling which elements to update

    Returns:
        None

    Raises:
        FileNotFoundError: If manifest file doesn't exist
        IOError: If file read/write fails
    """
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

        msg.success(f"Updated package name to: [reset]{new_package_name}")

    except FileNotFoundError:
        msg.error(f"The manifest file '{manifest_file}' was not found.")
    except IOError as e:
        msg.error(f"Error reading or writing the manifest file: {e}")
    except re.error as e:
        msg.error(f"Regular expression error: {e}")


def update_smali_path_package(smali_dir, old_package_path, new_package_path):
    """
    Update package paths in smali files.

    Args:
        smali_dir (str): Directory containing smali files
        old_package_path (str): Original package path
        new_package_path (str): New package path to use

    Returns:
        None
    """
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
    """
    Update package name references in resource files.

    Args:
        resources_dir (str): Directory containing resource files
        old_package_name (str): Original package name
        new_package_name (str): New package name to use

    Returns:
        None

    Raises:
        FileNotFoundError: If resources directory doesn't exist
    """
    try:
        # Check if resources directory exists
        if not os.path.isdir(resources_dir):
            raise FileNotFoundError(f"The resources directory '{resources_dir}' does not exist.")

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
                    msg.warning(f"File {file_path} is not UTF-8 encoded.")
                except (OSError, IOError) as e:
                    msg.error(f"Failed to process file: {file_path}. Error: {e}")

        if updated_any:
            msg.success("Updated package name in resource files.")
        else:
            msg.info("No matching package found in resource.")

    except FileNotFoundError as fnf_error:
        msg.error(str(fnf_error))


def update_smali_directory(smali_base_dir, old_package_path, new_package_path):
    """
    Rename smali directories to match new package path.

    Args:
        smali_base_dir (str): Base directory containing smali folders
        old_package_path (str): Original package path
        new_package_path (str): New package path to use

    Returns:
        None
    """
    # Normalize paths (remove leading L)
    old_package_path = old_package_path.strip("L")
    new_package_path = new_package_path.strip("L")

    renamed = False

    # Loop through smali, smali_classes2, smali_classes3, ...
    for root, _, _ in os.walk(smali_base_dir):
        if os.path.basename(root).startswith("smali"):
            # Search recursively in this smali folder
            old_package_pattern = os.path.join(root, "**", old_package_path)
            old_dirs = glob.glob(old_package_pattern, recursive=True)

            for old_dir in old_dirs:
                if os.path.isdir(old_dir):
                    new_dir = old_dir.replace(old_package_path, new_package_path)
                    os.makedirs(os.path.dirname(new_dir), exist_ok=True)  # Ensure parent dir exists
                    os.rename(old_dir, new_dir)
                    msg.success(f"Updated smali with: [reset]{new_package_path}")
                    renamed = True

    if not renamed:
        msg.info(f"No match for [reset]{old_package_path}.")


def update_buildconfig_file(file_path, old_package_name, new_package_name):
    """Update APPLICATION_ID in a single BuildConfig.smali file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        target = f' APPLICATION_ID:Ljava/lang/String; = "{old_package_name}"'
        if target in content:
            new_content = content.replace(
                target,
                f' APPLICATION_ID:Ljava/lang/String; = "{new_package_name}"',
            )
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True
    except (OSError, IOError) as e:
        msg.error(f"Failed to update {file_path}: {e}")
    return False


def update_application_id_in_smali(smali_dir, old_package_name, new_package_name, strict=False):
    """
    Update APPLICATION_ID in BuildConfig.smali files.

    Args:
        smali_dir (str): Directory containing smali files
        old_package_name (str): Original package name
        new_package_name (str): New package name
        strict (bool): Enable strict validation of updates

    Returns:
        None

    Raises:
        FileNotFoundError: If smali directory doesn't exist
    """
    if not os.path.isdir(smali_dir):
        msg.error(f"The smali directory '{smali_dir}' does not exist.")
        return

    buildconfig_found = False
    updated_any = False

    for root, _, files in os.walk(smali_dir):
        for file in files:
            if file.endswith("BuildConfig.smali"):
                buildconfig_found = True
                file_path = os.path.join(root, file)
                if update_buildconfig_file(file_path, old_package_name, new_package_name):
                    updated_any = True

    if strict:
        if not buildconfig_found:
            msg.error("No BuildConfig.smali files found in the provided smali directory.")
            return
        if not updated_any:
            msg.error("No BuildConfig.smali file contained the specified old APPLICATION_ID.")
            return

    if updated_any:
        msg.success("Updated APPLICATION_ID in smali files.")
