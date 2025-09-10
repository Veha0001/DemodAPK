import dataclasses
import json
import os
import subprocess
import sys
from typing import Optional

from platformdirs import user_config_dir

from demodapk.utils import msg


@dataclasses.dataclass
class ApkBasic:
    apk_config: dict
    package_orig_name: Optional[str] = None
    package_orig_path: Optional[str] = None
    dex_folder_exists: bool = False
    decoded_dir: str = ""
    android_manifest: str = ""


@dataclasses.dataclass
class Apkeditor:
    editor_jar: str
    javaopts: str
    dex_option: bool
    to_output: str
    clean: bool

    def __bool__(self):
        return bool(
            self.editor_jar
            or self.javaopts
            or self.dex_option
            or self.to_output
            or self.clean
        )


@dataclasses.dataclass
class Facebook:
    appid: str
    client_token: str
    login_protocol_scheme: str

    def __bool__(self):
        return bool(self.appid or self.client_token)


@dataclasses.dataclass
class Package:
    name: str
    path: str

    def __boo__(self):
        return bool(self.name)


class ConfigHandler:
    def __init__(self, apk_config):
        self.log_level = apk_config.get("log", False)
        self.manifest_edit_level = apk_config.get("level", 2)
        self.app_name = apk_config.get("app_name", None)
        self.apk_config = apk_config
        self.command_quietly = apk_config.get("commands", {}).get("quietly", False)

    def apkeditor(self, args) -> Apkeditor:
        apkeditor_conf = self.apk_config.get("apkeditor", {})
        return Apkeditor(
            editor_jar=apkeditor_conf.get("jarpath", ""),
            javaopts=apkeditor_conf.get("javaopts", ""),
            dex_option=getattr(args, "dex", None) or apkeditor_conf.get("dex", False),
            to_output=getattr(args, "output", None) or apkeditor_conf.get("output"),
            clean=getattr(args, "clean", None) or apkeditor_conf.get("clean"),
        )

    def facebook(self) -> Facebook:
        fb = self.apk_config.get("facebook", {})
        appid = fb.get("app_id", "")
        return Facebook(
            appid=appid,
            client_token=fb.get("client_token", ""),
            login_protocol_scheme=fb.get("login_protocol_scheme", f"fb{appid}"),
        )

    def package(self) -> Package:
        name = self.apk_config.get("package", "")
        return Package(
            name=name,
            path="L" + name.replace(".", "/"),
        )


def get_config_path(config: str):
    return os.path.join(user_config_dir("demodapk"), config)


def load_config(config: str = "config.json"):
    config_path = os.path.abspath(os.path.expanduser(config))
    if os.path.isdir(config_path):
        config_path = os.path.join(config_path, config)
    if not os.path.exists(config_path):
        config_path = get_config_path(config)
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_for_dex_folder(apk_dir):
    dex_folder_path = os.path.join(apk_dir, "dex")  # Adjust the path if necessary
    return os.path.isdir(dex_folder_path)


def verify_apk_directory(apk_dir):
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
            subprocess.run(cmd, shell=True, check=True, env=os.environ)

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
