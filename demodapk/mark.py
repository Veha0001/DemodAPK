import os
import shutil
import sys

from demodapk.baseconf import run_commands
from demodapk.utils import msg


def get_apkeditor_cmd(editor_jar: str, javaopts: str):
    apkeditor_cmd = shutil.which("apkeditor")
    if apkeditor_cmd:
        opts = " ".join(f"-J{opt.lstrip('-')}" for opt in javaopts.split())
        return f"apkeditor {opts}".strip()
    if editor_jar:
        return f"java {javaopts} -jar {editor_jar}".strip()
    msg.error("Cannot decode the apk without APKEditor.")
    sys.exit(1)


def apkeditor_merge(
    editor_jar, apk_file, javaopts, merge_base_apk, quietly: bool, force: bool = False
):
    # New base name of apk_file end with .apk
    command = f'{get_apkeditor_cmd(editor_jar, javaopts)} m -i "{apk_file}" -o "{merge_base_apk}"'
    if force:
        command += " -f"
    msg.info(f"Merging: {apk_file}", bold=True, prefix="[-]")
    run_commands([command], quietly, tasker=True)
    msg.info(
        f"Merged into: {merge_base_apk}",
        color="green",
        bold=True,
        prefix="[+]",
    )


def apkeditor_decode(
    editor_jar,
    apk_file,
    javaopts,
    output_dir,
    dex: bool,
    quietly: bool,
    force: bool,
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
    if force:
        command += " -f"
    msg.info(f"Decoding: {os.path.basename(apk_file)}", bold=True, prefix="[-]")
    run_commands([command], quietly, tasker=True)
    msg.info(
        f"Decoded into: {output_dir}",
        color="green",
        bold=True,
        prefix="[+]",
    )


def apkeditor_build(
    editor_jar,
    input_dir,
    output_apk,
    javaopts,
    quietly: bool,
    force: bool,
    clean: bool,
):
    command = f'{get_apkeditor_cmd(editor_jar, javaopts)} b -i "{input_dir}" -o "{output_apk}"'
    if force:
        command += " -f"
    msg.info(f"Building: {input_dir}", bold=True, prefix="[-]")
    run_commands([command], quietly, tasker=True)
    if clean:
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
    msg.info(f"Cleanup: {input_dir}")
    shutil.rmtree(input_dir, ignore_errors=True)
    return dest_file
