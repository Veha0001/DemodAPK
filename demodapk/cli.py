"""
DemodAPK CLI module.

This module provides the command-line interface for the DemodAPK tool,
which handles APK modification tasks including decoding, rebuilding,
and various customization options.
"""

from types import SimpleNamespace

import rich_click as click
from auto_click_auto import enable_click_shell_completion_option

from demodapk import __version__
from demodapk.baseconf import load_config
from demodapk.mods import dowhat, runsteps
from demodapk.utils import show_logo


# INFO: https://click.palletsprojects.com/en/stable/api/
@click.command()
@click.help_option("-h", "--help")
@click.argument(
    "apk_dir",
    required=False,
    type=click.Path(exists=True, file_okay=True, dir_okay=True, path_type=str),
    metavar="<apk>",
)
@click.option(
    "-i",
    "--id",
    "index",
    type=int,
    default=None,
    metavar="<int>",
    help="Index of package configured.",
)
@click.option(
    "-c",
    "--config",
    default="config.json",
    type=click.Path(exists=False, file_okay=True, dir_okay=True, path_type=str),
    metavar="<json>",
    show_default=True,
    help="Path to the configuration file.",
)
@click.option(
    "-sc",
    "--schema",
    is_flag=True,
    help="Apply schema to the config.",
)
@click.option(
    "-S",
    "--single-apk",
    is_flag=True,
    default=False,
    help="Keep only the rebuilt APK.",
)
@click.option(
    "-s",
    "--skip",
    "skip_list",
    metavar="<key>",
    type=click.Choice(["fb", "rename"]),
    multiple=True,
    help="Skip specific JSON config keys.",
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    default=False,
    help="Force to overwrite.",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(exists=False, file_okay=True, dir_okay=True, path_type=str),
    metavar="<path>",
    help="Path to writes decode and build.",
)
@click.option(
    "-ua",
    "--getup",  # Wake Up!
    "update_apkeditor",
    is_flag=True,
    help="Update APKEditor latest version.",
)
@click.option(
    "-dex",
    "--raw-dex",
    is_flag=True,
    default=False,
    help="Decode with raw dex.",
)
@click.option(
    "-sm",
    "--xsmali",
    is_flag=True,
    help="Rename package in smali files and directories.",
)
@enable_click_shell_completion_option("--completion", "-ac", program_name="demodapk")
@click.version_option(
    __version__,
    "-v",
    "--version",
)
def main(**kwargs):
    """DemodAPK: APK Modification Script"""
    args = SimpleNamespace(**kwargs)
    packer = load_config(args.config).get("DemodAPK", {})
    show_logo("DemodAPK")
    dowhat(args, click)
    runsteps(args, packer)


if __name__ == "__main__":
    main()
