import argparse
from pathlib import Path

from rich_argparse import RawTextRichHelpFormatter

from demodapk import __version__


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog="demodapk",
        usage="%(prog)s <apk_dir> [options]",
        description="DemodAPK: APK Modification Script.",
        formatter_class=RawTextRichHelpFormatter,
    )
    parser.add_argument("apk_dir", nargs="?", help="Path to the APK directory/file")
    parser.add_argument(
        "-c",
        "--config",
        default=Path("config.json"),
        metavar="<file>",
        help="Path to the JSON configuration file.\n(default: %(default)s)",
    )
    parser.add_argument(
        "-sc",
        "--schema",
        action="store_true",
        help="Apply schema to the config.",
    )
    parser.add_argument(
        "-S",
        "--single-apk",
        action="store_true",
        default=False,
        help="Keep only the rebuilt APK.",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        help="Force to overwrite.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        metavar="<file/path>",
        help="Path to decode and build",
    )
    parser.add_argument(
        "-ua",
        "--update-apkeditor",
        action="store_true",
        help="Update APKEditor latest version.",
    )
    parser.add_argument(
        "-dex",
        action="store_true",
        default=False,
        help="Decode with raw dex.",
    )
    parser.add_argument(
        "-n",
        "--no-rename-package",
        action="store_true",
        help="Skip rename package.",
    )
    parser.add_argument(
        "-nfb",
        "--no-facebook",
        action="store_true",
        help="Skip Facebook API update.",
    )
    parser.add_argument(
        "-nsd",
        "--rename-smali",
        action="store_true",
        help="Rename package in smali files and directories.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=("%(prog)s version: " + __version__),
        help="Show version of the program.",
    )
    return parser
