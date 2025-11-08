"""
DemodAPK: baseconf.py
"""

import dataclasses
import json
import os
import sys
from typing import Optional

from demodapk.utils import CONFIG_DIR, msg


@dataclasses.dataclass
class ApkBasic:
    """Basic information about the APK."""

    apk_config: dict
    package_orig_name: Optional[str] = None
    package_orig_path: Optional[str] = None
    dex_folder_exists: bool = False
    decoded_dir: str = ""
    android_manifest: str = ""


@dataclasses.dataclass
class Apkeditor:
    """Configuration for the APK editor."""

    editor_jar: str
    javaopts: str
    dex_option: bool
    to_output: Optional[str]
    clean: bool

    def __bool__(self):
        return bool(
            self.editor_jar or self.javaopts or self.dex_option or self.to_output or self.clean
        )


@dataclasses.dataclass
class UpdateContext:
    """Context for updating the APK."""

    value_strings: str
    smali_folder: str
    resources_folder: str
    package_orig_name: Optional[str]
    package_orig_path: Optional[str]
    dex_folder_exists: bool


@dataclasses.dataclass
class Facebook:
    """Configuration for Facebook integration."""

    appid: str
    client_token: str
    login_protocol_scheme: str

    def __bool__(self):
        return bool(self.appid or self.client_token)


@dataclasses.dataclass
class Package:
    """Package information."""

    name: str
    path: str

    def __boo__(self):
        return bool(self.name)


class ConfigHandler:
    """Handles configuration for the APK."""

    def __init__(self, apk_config):
        """Initialize with the given APK configuration."""
        self.log_level = apk_config.get("log", False)
        self.manifest_edit_level = apk_config.get("level", 2)
        self.app_name = apk_config.get("app_name", None)
        self.apk_config = apk_config
        self.command_quietly = apk_config.get("commands", {}).get("quietly", False)

    def apkeditor(self, args) -> Apkeditor:
        """Get the APK editor configuration."""
        apkeditor_conf = self.apk_config.get("apkeditor", {})
        return Apkeditor(
            editor_jar=apkeditor_conf.get("jarpath", ""),
            javaopts=apkeditor_conf.get("javaopts", ""),
            dex_option=getattr(args, "raw_dex", None) or apkeditor_conf.get("dex", False),
            to_output=getattr(args, "output", None) or apkeditor_conf.get("output"),
            clean=getattr(args, "single_apk", False) or apkeditor_conf.get("clean"),
        )

    def facebook(self) -> Facebook:
        """Get the Facebook configuration."""
        fb = self.apk_config.get("facebook", {})
        appid = fb.get("app_id", "")
        return Facebook(
            appid=appid,
            client_token=fb.get("client_token", ""),
            login_protocol_scheme=fb.get("login_protocol_scheme", f"fb{appid}"),
        )

    def package(self) -> Package:
        """Get the package information."""
        name = self.apk_config.get("package", "")
        return Package(
            name=name,
            path="L" + name.replace(".", "/"),
        )


def load_config(config: str = "config.json"):
    """
    Load the configuration from the specified JSON file.
    """
    config_path = os.path.abspath(os.path.expanduser(config))
    if os.path.isdir(config_path):
        config_path = os.path.join(config_path, "config.json")
    if not os.path.exists(config_path):
        config_path = CONFIG_DIR / config
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_for_dex_folder(apk_dir):
    """
    Check if the dex folder exists in the given APK directory.
    """
    dex_folder_path = os.path.join(apk_dir, "dex")  # Adjust the path if necessary
    return os.path.isdir(dex_folder_path)


def verify_apk_directory(apk_dir):
    """
    Verify the structure of the APK directory.
    """
    if not os.path.exists(apk_dir):
        msg.error(f"The directory {apk_dir} does not exist.")
        sys.exit(1)
    apk_dir = os.path.abspath(apk_dir)
    dir_name = os.path.basename(apk_dir)
    # Check for required files and folders
    required_files = ["AndroidManifest.xml"]
    required_folders = ["resources", "root"]
    optional_folders = ["dex", "smali"]

    # Check for required files
    for req_file in required_files:
        if not os.path.isfile(os.path.join(apk_dir, req_file)):
            msg.error(f"Missing required file '{req_file}' in {dir_name}.")
            sys.exit(1)

    # Check for required folders
    for req_folder in required_folders:
        if not os.path.isdir(os.path.join(apk_dir, req_folder)):
            msg.error(f"Missing required folder '{req_folder}' in {dir_name}.")
            sys.exit(1)

    # Check for at least one optional folder
    if not any(os.path.isdir(os.path.join(apk_dir, folder)) for folder in optional_folders):
        msg.error(
            "At least one of the following folders is required in"
            f" {dir_name}: {', '.join(optional_folders)}."
        )
        sys.exit(1)

    msg.info(f"APK directory verified: {os.path.basename(dir_name)}")
    return apk_dir
