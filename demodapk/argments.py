import argparse

from demodapk import __version__


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog="demodapk",
        usage="%(prog)s <apk_dir> [options]",
        description="DemodAPK: APK Modification Script.",
    )
    parser.add_argument("apk_dir", nargs="?", help="Path to the APK directory/file")
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
        default="config.json",
        help="Path to the JSON configuration file.",
    )
    parser.add_argument(
        "-dex",
        action="store_true",
        default=False,
        help="For decode with raw dex.",
    )
    parser.add_argument(
        "-cl",
        "--clean",
        action="store_true",
        default=False,
        help="Cleanup the decoded folder.",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        help="Force overwrite the decoded APK directory.",
    )
    parser.add_argument(
        "-ua",
        "--update-apkeditor",
        action="store_true",
        help="Update APKEditor latest version",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="output path of decoded_dir and name.",
    )
    parser.add_argument(
        "-nfb",
        "--no-facebook",
        action="store_true",
        help="No update for Facebook app API.",
    )
    parser.add_argument(
        "-mv",
        "--move-rename-smali",
        action="store_true",
        help="Rename package in smali files and the smali directory.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=("%(prog)s version: " + __version__),
        help="Show version of the program.",
    )
    return parser
