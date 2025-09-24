"""DemodAPK CLI"""

from types import SimpleNamespace

import rich_click as click

from demodapk import __version__
from demodapk.baseconf import load_config
from demodapk.mods import dowhat, runsteps
from demodapk.utils import show_logo


@click.command()
@click.help_option("-h", "--help")
@click.argument(
    "apk_dir",
    required=False,
    type=click.Path(exists=True, file_okay=True, dir_okay=True, path_type=str),
    metavar="<apk>",
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
    "--update-apkeditor",
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
    "-n",
    "--no-rename-package",
    is_flag=True,
    help="Skip rename package.",
)
@click.option(
    "-nfb",
    "--no-facebook",
    is_flag=True,
    help="Skip Facebook API update.",
)
@click.option(
    "-nas",
    "--rename-smali",
    is_flag=True,
    help="Rename package in smali files and directories.",
)
@click.version_option(
    __version__,
    "-v",
    "--version",
)
def main(**kwargs):
    """DemodAPK: APK Modification Script"""
    # kwargs will contain all arguments/options
    args = SimpleNamespace(**kwargs)
    packer = load_config(args.config).get("DemodAPK", {})
    show_logo("DemodAPK")
    dowhat(args, click)
    runsteps(args, packer)


if __name__ == "__main__":
    main()
