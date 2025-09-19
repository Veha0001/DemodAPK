import os
import re
import shutil
import sys
from pathlib import Path

from platformdirs import user_config_path

from demodapk.baseconf import Apkeditor
from demodapk.tool import download_apkeditor, get_latest_version
from demodapk.utils import msg, run_commands


def update_apkeditor():
    """
    Ensure the latest APKEditor jar is present in the user config folder.
    Deletes older versions and downloads the latest.
    Returns the path to the latest jar.
    """
    config_dir = user_config_path("demodapk")
    os.makedirs(config_dir, exist_ok=True)

    latest_version = get_latest_version()
    if not latest_version:
        msg.error("Could not fetch the latest APKEditor version.")
        return None

    # Remove all existing APKEditor jars
    for fname in os.listdir(config_dir):
        if re.match(r"APKEditor-(\d+\.\d+\.\d+)\.jar$", fname):
            path = os.path.join(config_dir, fname)
            try:
                os.remove(path)
                msg.info(f"Deleted: {fname}")
            except (PermissionError, shutil.Error):
                pass

    download_apkeditor(config_dir)
    latest_jar = os.path.join(config_dir, f"APKEditor-{latest_version}.jar")

    if os.path.exists(latest_jar):
        return latest_jar

    msg.error("Failed to download APKEditor.")
    return None


def get_apkeditor_cmd(cfg: Apkeditor):
    """
    Return the command to run APKEditor.
    - Use the provided jar or pick the latest jar from config.
    - If missing, download the latest jar and prompt to rerun.
    """
    editor_jar = cfg.editor_jar
    javaopts = cfg.javaopts
    # Use system apkeditor if available
    # apkeditor_cmd = shutil.which("apkeditor")
    # if apkeditor_cmd:
    # opts = " ".join(f"-J{opt.lstrip('-')}" for opt in javaopts.split())
    # return f"apkeditor {opts}".strip()
    config_dir = user_config_path("demodapk")
    os.makedirs(config_dir, exist_ok=True)

    # Look for existing jars
    if editor_jar:
        if not os.path.exists(editor_jar):
            msg.error(f"Specified editor jar does not exist: {editor_jar}")
            sys.exit(1)
    else:
        jars = []
        for fname in os.listdir(config_dir):
            match = re.match(r"APKEditor-(\d+\.\d+\.\d+)\.jar$", fname)
            if match:
                version = tuple(int(x) for x in match.group(1).split("."))
                jars.append((version, os.path.join(config_dir, fname)))
        if jars:
            jars.sort(reverse=True)
            editor_jar = jars[0][1]

    # If jar  doesn't exist, update/download latest
    if not editor_jar or not os.path.exists(editor_jar):
        update_apkeditor()
        sys.exit(0)
    return f"java {javaopts} -jar {editor_jar}".strip()


def apkeditor_merge(
    cfg: Apkeditor,
    apk_file: Path,
    merge_base_apk: Path,
    quietly: bool,
    force: bool = False,
):
    # New base name of apk_file end with .apk
    command = f'{get_apkeditor_cmd(cfg)} m -i "{apk_file}" -o "{merge_base_apk}"'
    if force:
        command += " -f"
    msg.info(f"Merging: {apk_file}", bold=True, prefix="[-]")
    run_commands([command], quietly, tasker=True)
    msg.info(
        f"Merged into: {os.path.relpath(merge_base_apk)}",
        color="green",
        bold=True,
        prefix="[+]",
    )


def apkeditor_decode(
    cfg: Apkeditor,
    apk_file: Path,
    output_dir: str | Path,
    quietly: bool,
    force: bool,
):
    merge_base_apk = apk_file.with_suffix(".apk")
    # If apk_file is not end with .apk then merge
    if apk_file.suffix.lower() != ".apk":
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
    msg.info(f"Decoding: [blue underline]{apk_file.name}", bold=True, prefix="[-]")
    run_commands([command], quietly, tasker=True)
    msg.info(
        f"Decoded into: {cfg.to_output}",
        color="green",
        bold=True,
        prefix="[+]",
    )


def apkeditor_build(
    cfg: Apkeditor,
    input_dir: Path,
    output_apk: Path,
    quietly: bool,
    force: bool,
):
    command = f'{get_apkeditor_cmd(cfg)} b -i "{input_dir}" -o "{output_apk}"'
    if force:
        command += " -f"
    msg.info(f"Building: {input_dir}", bold=True, prefix="[-]")
    run_commands([command], quietly, tasker=True)
    if cfg.clean:
        output_apk = cleanup_apk_build(input_dir, output_apk)
    msg.info(
        f"Built into: {output_apk}",
        color="green",
        bold=True,
        prefix="[+]",
    )
    return output_apk


def cleanup_apk_build(input_dir, output_apk):
    dest_file = input_dir + ".apk"
    shutil.move(output_apk, dest_file)
    msg.info(f"Clean: {input_dir}")
    shutil.rmtree(input_dir, ignore_errors=True)
    return dest_file
