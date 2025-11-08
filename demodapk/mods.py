"""
APK modification workflow module.

This module implements the core workflow for modifying APK files, including:
- APK decoding and building
- Package name modifications
- Resource updates
- Command execution
- Configuration handling
"""

import os
import shutil
import sys

from demodapk.baseconf import (
    ApkBasic,
    ConfigHandler,
    UpdateContext,
    check_for_dex_folder,
    verify_apk_directory,
)
from demodapk.mark import apkeditor_build, apkeditor_decode, update_apkeditor
from demodapk.patch import (
    extract_package_info,
    rename_package_in_manifest,
    rename_package_in_resources,
    update_app_name_values,
    update_application_id_in_smali,
    update_facebook_app_values,
    update_smali_directory,
    update_smali_path_package,
)
from demodapk.schema import get_schema
from demodapk.utils import console, msg, run_commands, showbox_packages
from demodapk.xmls import update_manifest_group

try:
    import inquirer
except ImportError:
    inquirer = None


def dowhat(args, click):
    """
    Process initial command line arguments and perform preliminary actions.

    Args:
        args: Namespace object containing command line arguments
        click: Click context object for CLI handling

    Returns:
        None
    """
    if args.update_apkeditor:
        update_apkeditor()
        sys.exit(0)
    if args.schema:
        get_schema()
    apk_dir = getattr(args, "apk_dir", None)
    if apk_dir is None:
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        sys.exit(0)


def setup_env(ref: dict):
    """
    Set up environment variables for the modification process.

    Args:
        ref (dict): Dictionary mapping environment variable names to paths

    Returns:
        dict: The reference dictionary that was used to set up the environment
    """
    for key, path in ref.items():
        os.environ[key] = path
    return ref


def select_config_for_apk(config, args):
    """
    Handle APK file case by prompting user to select a package configuration.

    Args:
        config (dict): Configuration dictionary containing package options

    Returns:
        tuple: Selected package name and its configuration

    Raises:
        SystemExit: If no configuration is selected or inquirer is not installed
    """
    for pkg_name, pkg_config in config.items():
        if not isinstance(pkg_config, dict):
            msg.error(f"Invalid configuration for package '{pkg_name}'")
            sys.exit(1)

    available_packages = list(config.keys())
    if not available_packages:
        msg.error("No preconfigured packages found.")
        sys.exit(1)

    if getattr(args, "index", None) is not None:
        idx = args.index
        if idx < 0 or idx >= len(available_packages):
            showbox_packages(available_packages, idx)
            msg.error(f"Invalid index {idx}, must be between 0 and {len(available_packages) - 1}.")
            sys.exit(1)
        name = available_packages[idx]
        return name, config[name]

    if inquirer is None:
        msg.error("Inquirer package is not installed. Please install it to proceed.")
        sys.exit(1)

    questions = [
        inquirer.List(
            "package",
            message="Select a package configuration for this APK",
            choices=available_packages,
        )
    ]
    answers = inquirer.prompt(questions)
    if answers and "package" in answers:
        name = answers["package"]
        return name, config.get(name)

    msg.warning("No package was selected.")
    sys.exit(0)


def match_config_by_manifest(config, android_manifest):
    """
    Match package configuration using the package name from AndroidManifest.xml.

    Args:
        config (dict): Configuration dictionary containing package options
        android_manifest (str): Path to AndroidManifest.xml file

    Returns:
        tuple: Matched package name and its configuration

    Raises:
        SystemExit: If no matching configuration is found
    """
    current_package_name, _ = extract_package_info(android_manifest)

    for key, value in config.items():
        if key == current_package_name:
            return key, config[key]
        if isinstance(value, dict) and value.get("package") == current_package_name:
            return key, config[key]

    msg.error(f"No matching configuration found for package: {current_package_name}")
    sys.exit(1)


def get_the_inputs(config, args):
    """
    Process input APK/directory and get configuration details.

    Args:
        config (dict): Configuration dictionary

    Returns:
        ApkBasic: Object containing basic APK configuration details

    Raises:
        SystemExit: If input validation fails
    """
    apk_input = args.apk_dir
    apk_dir = os.path.abspath(apk_input)
    android_manifest = os.path.join(apk_dir, "AndroidManifest.xml")
    if os.path.isfile(apk_dir):  # APK file case
        if not apk_dir.lower().endswith((".zip", ".apk", ".apks", ".xapk")):
            msg.error(f"This: {apk_dir}, isn’t an apk type.")
            sys.exit(1)

        package_name, apk_config = select_config_for_apk(config, args)
        decoded_dir, dex_folder_exists = apk_dir.rsplit(".", 1)[0], False

    else:  # Decoded directory case
        apk_dir = verify_apk_directory(apk_dir)
        dex_folder_exists = check_for_dex_folder(apk_dir)
        decoded_dir = apk_dir

        package_name, apk_config = match_config_by_manifest(config, android_manifest)

    package_path = "L" + package_name.replace(".", "/")

    return ApkBasic(
        apk_config=apk_config,
        package_orig_name=package_name,
        package_orig_path=package_path,
        dex_folder_exists=dex_folder_exists,
        decoded_dir=decoded_dir,
        android_manifest=android_manifest,
    )


def get_demo(conf: ConfigHandler, basic: ApkBasic, args):
    """
    Set up demo environment and decode APK if needed.

    Args:
        conf (ConfigHandler): Configuration handler object
        basic (ApkBasic): Basic APK configuration
        args: Command line arguments

    Returns:
        tuple: Paths to manifest, smali, resources, values and decoded directory

    Raises:
        SystemExit: If Java is not installed
    """
    apk_dir = args.apk_dir
    apk_config = basic.apk_config
    isdex = basic.dex_folder_exists
    decoded_dir = basic.decoded_dir

    editor = conf.apkeditor(args)
    if conf.log_level and isdex:
        msg.warning("Dex folder found. Some functions will be disabled.")

    decoded_dir = (
        os.path.expanduser(os.path.splitext(editor.to_output)[0])
        if editor.to_output
        else decoded_dir
    )

    if not shutil.which("java"):
        msg.error("Java is not installed. Please install Java to proceed.")
        sys.exit(1)

    if os.path.isfile(apk_dir):
        apkeditor_decode(
            editor,
            apk_dir,
            output_dir=decoded_dir,
            quietly=conf.command_quietly,
            force=args.force,
        )
        apk_dir = decoded_dir

    apk_root_folder = os.path.join(apk_dir, "root")
    android_manifest = os.path.join(apk_dir, "AndroidManifest.xml")
    resources_folder = os.path.join(apk_dir, "resources")
    smali_folder = os.path.join(apk_dir, "smali") if not editor.dex_option else ""
    value_strings = os.path.join(resources_folder, "package_1/res/values/strings.xml")

    begin_paths = {
        "BASE": apk_dir,
        "BASE_ROOT": apk_root_folder,
        "BASE_MANIFEST": android_manifest,
        "BASE_RESOURCES": resources_folder,
        "BASE_VALUE": value_strings,
        "BASE_SMALI": smali_folder,
        "BASE_RESDIR": os.path.join(resources_folder, "package_1/res"),
        "BASE_LIB": os.path.join(apk_root_folder, "lib"),
    }
    setup_env(begin_paths)

    if "commands" in apk_config and "begin" in apk_config["commands"]:
        run_commands(apk_config["commands"]["begin"], conf.command_quietly)

    return android_manifest, smali_folder, resources_folder, value_strings, apk_dir


def get_updates(conf, android_manifest, apk_config, ctx: UpdateContext, args):
    """
    Apply updates to the APK based on configuration.

    Args:
        conf (ConfigHandler): Configuration handler
        android_manifest (str): Path to AndroidManifest.xml
        apk_config (dict): APK configuration dictionary
        ctx (UpdateContext): Update context object
        args: Command line arguments

    Returns:
        None

    Raises:
        SystemExit: If AndroidManifest.xml is not found
    """
    editor = conf.apkeditor(args)
    package = conf.package()
    facebook = conf.facebook()

    if not os.path.isfile(android_manifest):
        msg.error("AndroidManifest.xml not found in the directory.")
        sys.exit(1)

    if conf.app_name and not args.no_rename:
        update_app_name_values(conf.app_name, ctx.value_strings)

    if facebook and not args.no_facebook:
        update_facebook_app_values(
            ctx.value_strings,
            fb_app_id=facebook.appid,
            fb_client_token=facebook.client_token,
            fb_login_protocol_scheme=facebook.login_protocol_scheme,
        )

    if not args.no_rename and "package" in apk_config:
        rename_package_in_manifest(
            android_manifest,
            ctx.package_orig_name,
            new_package_name=package.name,
            level=conf.manifest_edit_level,
        )
        rename_package_in_resources(
            ctx.resources_folder,
            ctx.package_orig_name,
            new_package_name=package.name,
        )

        if not ctx.dex_folder_exists and not editor.dex_option:
            if args.rename_smali:
                update_smali_path_package(
                    ctx.smali_folder,
                    ctx.package_orig_path,
                    new_package_path=package.path,
                )
                update_smali_directory(
                    ctx.smali_folder,
                    ctx.package_orig_path,
                    new_package_path=package.path,
                )
            update_application_id_in_smali(
                ctx.smali_folder,
                ctx.package_orig_name,
                new_package_name=package.name,
            )
    update_manifest_group(manifest_xml=android_manifest, apk_config=apk_config)


def get_finish(conf, decoded_dir, apk_config, args):
    """
    Complete APK modification process and build final APK.

    Args:
        conf (ConfigHandler): Configuration handler
        decoded_dir (str): Path to decoded APK directory
        apk_config (dict): APK configuration dictionary
        args: Command line arguments

    Returns:
        None
    """
    editor = conf.apkeditor(args)
    decoded_dir = os.path.abspath(decoded_dir)
    output_apk_name = os.path.basename(decoded_dir.rstrip("/"))
    output_apk_path = os.path.join(decoded_dir, output_apk_name + ".apk")

    if (
        not os.path.exists(output_apk_path)
        or shutil.which("apkeditor")
        or "jarpath" in apk_config["apkeditor"]
    ):
        output_apk_path = apkeditor_build(
            editor,
            input_dir=decoded_dir,
            output_apk=output_apk_path,
            quietly=conf.command_quietly,
            force=args.force,
        )

    setup_env({"BUILD": output_apk_path})
    if "commands" in apk_config and "end" in apk_config["commands"]:
        run_commands(apk_config["commands"]["end"], conf.command_quietly)
    msg.info("APK modification finished!")


def runsteps(args, packer):
    """
    Execute the complete APK modification workflow.

    Args:
        args: Command line arguments
        packer (dict): Package configuration dictionary

    Returns:
        None
    """
    basic = get_the_inputs(packer, args)
    conf = ConfigHandler(basic.apk_config)

    android_manifest, smali_folder, resources_folder, value_strings, decoded_dir = get_demo(
        conf,
        basic,
        args=args,
    )
    with console.status(
        "[bold orange_red1]Modifying...", spinner_style="orange_red1", spinner="point"
    ):
        ctx = UpdateContext(
            value_strings=value_strings,
            smali_folder=smali_folder,
            resources_folder=resources_folder,
            package_orig_name=basic.package_orig_name,
            package_orig_path=basic.package_orig_path,
            dex_folder_exists=basic.dex_folder_exists,
        )
        get_updates(conf, android_manifest, basic.apk_config, ctx, args=args)
    get_finish(conf, decoded_dir=decoded_dir, apk_config=basic.apk_config, args=args)
