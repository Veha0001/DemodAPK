"""
APK modification utilities using APKEditor.

This module provides functions for managing and executing APKEditor operations
including updating, decoding, building and merging APK files.
"""

import os
import re
import shutil
import sys
from contextlib import nullcontext
from os.path import abspath, basename

from rich.panel import Panel

from demodapk.baseconf import Apkeditor
from demodapk.tool import (
    download_apkeditor,
    get_file_sha256,
    get_latest_apkeditor_info,
)
from demodapk.utils import CONFIG_DIR, console, msg, run_commands


def update_apkeditor():
    """
    Ensure the latest APKEditor jar is present in the user config folder.
    Deletes older versions and downloads the latest if needed.
    Returns the path to the latest jar.
    """
    apkeditor_info = get_latest_apkeditor_info()
    if not apkeditor_info or not apkeditor_info.get("version"):
        msg.error("Could not get latest APKEditor version info.")
        return None

    latest_version = apkeditor_info["version"]
    latest_jar_name = f"APKEditor-{latest_version}.jar"
    latest_jar_path = os.path.join(CONFIG_DIR, latest_jar_name)
    remote_sha = apkeditor_info.get("sha256")

    # Clean up old versions
    for fname in os.listdir(CONFIG_DIR):
        if re.match(r"APKEditor-(.+?)\.jar$", fname) and fname != latest_jar_name:
            path = os.path.join(CONFIG_DIR, fname)
            try:
                os.remove(path)
                console.print(
                    Panel(f"{fname}", title="Deleted old version"),
                    justify="left",
                    style="bold yellow",
                )
            except (PermissionError, shutil.Error):
                pass

    # Check if latest version already exists and is valid
    if os.path.exists(latest_jar_path):
        if remote_sha:
            local_sha = get_file_sha256(latest_jar_path)
            if local_sha == remote_sha:
                console.print(
                    Panel.fit(
                        f"APKEditor [bold blue]v{latest_version}[/bold blue] is up to date.",
                        border_style="bold green",
                    )
                )
                return latest_jar_path

            console.print("Local APKEditor JAR has incorrect hash. Redownloading.", style="yellow")
        else:
            # No remote hash, just assume it's fine if it exists and is not empty
            if os.path.getsize(latest_jar_path) > 0:
                console.print(
                    f"APKEditor v{latest_version} is up to date (no hash to verify).",
                    style="green",
                )
                return latest_jar_path

            console.print("Local APKEditor JAR is empty. Redownloading.", style="yellow")

    # If we are here, we need to download
    download_apkeditor(CONFIG_DIR)

    if os.path.exists(latest_jar_path):
        if remote_sha:
            local_sha = get_file_sha256(latest_jar_path)
            if local_sha != remote_sha:
                msg.error("Downloaded APKEditor JAR has incorrect hash. Download may be corrupt.")
                return None
        return latest_jar_path

    msg.error("Failed to download APKEditor.")
    return None


def get_apkeditor_cmd(cfg: Apkeditor):
    """
    Return the command to run APKEditor.
    - Use the provided jar or pick the latest jar from config.
    - If missing, download the latest jar and prompt to rerun.
    """
    javaopts = cfg.javaopts

    env_editor_jar = os.environ.get("APKEDITOR_JAR")
    if env_editor_jar and os.path.exists(env_editor_jar):
        editor_jar = env_editor_jar
    else:
        editor_jar = cfg.editor_jar
        if editor_jar:
            if not os.path.exists(editor_jar):
                msg.error(f"Specified editor jar does not exist: {editor_jar}")
                sys.exit(1)
        else:
            jars = []
            for fname in os.listdir(CONFIG_DIR):
                match = re.match(r"APKEditor-(.+?)\.jar$", fname)
                if match:
                    version_str = match.group(1)
                    version_parts = tuple(map(int, re.findall(r"\d+", version_str)))
                    if version_parts:
                        jars.append((version_parts, os.path.join(CONFIG_DIR, fname)))
            if jars:
                jars.sort(reverse=True)
                editor_jar = jars[0][1]

    # If jar  doesn't exist, update/download latest
    if not editor_jar or not os.path.exists(editor_jar):
        update_apkeditor()
        sys.exit(0)

    if os.path.getsize(editor_jar) == 0:
        msg.error("The APKEditor JAR is faulty.")
        update_apkeditor()
        sys.exit(0)

    return f"java {javaopts} -jar {editor_jar}".strip()


def apkeditor_merge(
    cfg: Apkeditor,
    apk_file: str,
    merge_base_apk: str,
    quietly: bool,
    force: bool = False,
):
    """
    Merge an APK file with a base APK using APKEditor.

    Args:
        cfg (Apkeditor): APKEditor configuration object
        apk_file (str): Path to the APK file to merge
        merge_base_apk (str): Path to output the merged APK
        quietly (bool): Run in quiet mode if True
        force (bool, optional): Force overwrite existing files. Defaults to False.

    Returns:
        None
    """
    # New base name of apk_file end with .apk
    command = (
        f'{get_apkeditor_cmd(cfg)} m -i "{os.path.abspath(apk_file)}"'
        f' -o "{os.path.abspath(merge_base_apk)}"'
    )
    if force:
        command += " -f"
    msg.info(f"Merging: {os.path.basename(apk_file)}", prefix="-")
    with (
        console.status("[bold blue]Processing...", spinner="point", spinner_style="blue")
        if quietly
        else nullcontext()
    ):
        run_commands([command], quietly, tasker=True)
    msg.success(
        f"Merged into: {os.path.basename(merge_base_apk)}",
        prefix="+",
    )


def apkeditor_decode(
    cfg: Apkeditor,
    apk_file: str,
    output_dir: str,
    quietly: bool,
    force: bool,
):
    """
    Decode an APK file using APKEditor.

    Args:
        cfg (Apkeditor): APKEditor configuration object
        apk_file (str): Path to the APK file to decode
        output_dir (str): Directory to output decoded files
        quietly (bool): Run in quiet mode if True
        force (bool): Force overwrite existing files

    Returns:
        None
    """
    output_dir = abspath(output_dir)
    merge_base_apk = abspath(os.path.splitext(apk_file)[0] + ".apk")
    # If apk_file is not end with .apk then merge
    if apk_file.lower() != ".apk":
        if not os.path.exists(merge_base_apk):
            apkeditor_merge(cfg, apk_file, merge_base_apk, quietly)
        command = f'{get_apkeditor_cmd(cfg)} d -i "{merge_base_apk}" -o "{output_dir}"'
        apk_file = merge_base_apk
    else:
        command = f'{get_apkeditor_cmd(cfg)} d -i "{apk_file}" -o "{output_dir}"'

    if cfg.dex_option:
        command += " -dex"
    if force:
        command += " -f"
    msg.info(
        f"Decoding: [magenta underline]{basename(apk_file)}",
        prefix="-",
    )
    with console.status("[bold green]Processing...", spinner="point") if quietly else nullcontext():
        run_commands([command], quietly, tasker=True)
    msg.success(
        f"Decoded into: {cfg.to_output}",
        prefix="+",
    )


def apkeditor_build(
    cfg: Apkeditor,
    input_dir: str,
    output_apk: str,
    quietly: bool,
    force: bool,
):
    """
    Build an APK from decoded files using APKEditor.

    Args:
        cfg (Apkeditor): APKEditor configuration object
        input_dir (str): Directory containing decoded APK files
        output_apk (str): Path to output the built APK
        quietly (bool): Run in quiet mode if True
        force (bool): Force overwrite existing files

    Returns:
        str: Path to the built APK file
    """
    input_dir = abspath(input_dir)
    output_apk = abspath(output_apk)
    command = f'{get_apkeditor_cmd(cfg)} b -i "{input_dir}" -o "{output_apk}"'
    if force:
        command += " -f"
    msg.info(f"Building: {basename(input_dir)}", prefix="-")
    with (
        console.status("[bold green]Finishing Build...", spinner="point")
        if quietly
        else nullcontext()
    ):
        run_commands([command], quietly, tasker=True)
    if cfg.clean:
        output_apk = cleanup_apk_build(input_dir, output_apk)
    msg.success(
        f"Built into: {basename(output_apk)}",
        prefix="+",
    )
    return output_apk


def cleanup_apk_build(input_dir: str, output_apk: str):
    """
    Clean up temporary files after APK build.

    Args:
        input_dir (str): Directory containing decoded APK files
        output_apk (str): Path to the built APK file

    Returns:
        str: Path to the final APK file after cleanup
    """
    dest_file = input_dir + ".apk"
    shutil.move(output_apk, dest_file)
    msg.info(f"Clean: {basename(input_dir)}")
    shutil.rmtree(input_dir, ignore_errors=True)
    return dest_file
