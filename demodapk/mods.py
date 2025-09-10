import os
import shutil
import sys

from demodapk.argments import parse_arguments
from demodapk.baseconf import (
    ApkBasic,
    ConfigHandler,
    check_for_dex_folder,
    load_config,
    verify_apk_directory,
)
from demodapk.mark import (
    apkeditor_build,
    apkeditor_decode,
    run_commands,
    update_apkeditor,
)
from demodapk.patch import (
    extract_package_info,
    remove_metadata_from_manifest,
    rename_package_in_manifest,
    rename_package_in_resources,
    update_app_name_values,
    update_application_id_in_smali,
    update_facebook_app_values,
    update_smali_directory,
    update_smali_path_package,
)
from demodapk.utils import msg

try:
    import inquirer
except ImportError:
    inquirer = None

parsers = parse_arguments()
args = parsers.parse_args()
packer = load_config(args.config).get("DemodAPK", {})


def setup_env(ref: dict):
    for key, path in ref.items():
        os.environ[key] = path
    return ref


def get_the_input(config):
    apk_dir = args.apk_dir
    if args.update_apkeditor:
        update_apkeditor()
        sys.exit(0)
    if apk_dir is None:
        parsers.print_help()
        sys.exit(0)

    android_manifest = os.path.join(apk_dir, "AndroidManifest.xml")
    apk_solo = apk_dir.lower().endswith((".zip", ".apk", ".apks", ".xapk"))

    if os.path.isfile(apk_dir):
        available_packages = list(config.keys())

        if not apk_solo:
            msg.error(f"This: {apk_dir}, isn’t an apk type.")
            sys.exit(1)

        if not available_packages:
            msg.error("No preconfigured packages found in config.json.")
            sys.exit(1)

        if inquirer is None:
            msg.error(
                "Inquirer package is not installed. Please install it to proceed."
            )
            sys.exit(1)

        questions = [
            inquirer.List(
                "package",
                message="Select a package configuration for this APK",
                choices=available_packages,
            )
        ]

        try:
            answers = inquirer.prompt(questions)
            if answers and "package" in answers:
                package_orig_name = answers["package"]
                package_orig_path = "L" + package_orig_name.replace(".", "/")
            else:
                msg.error("No package was selected.")
                sys.exit(1)
        except Exception as e:
            msg.error(f"Error during package selection: {e}")
            sys.exit(1)

        apk_config = config.get(package_orig_name)
        if not apk_config:
            msg.error(f"No configuration found for package: {package_orig_name}")
            sys.exit(1)

        dex_folder_exists = False
        decoded_dir = apk_dir.rsplit(".", 1)[0]

    else:
        apk_dir = verify_apk_directory(apk_dir)
        dex_folder_exists = check_for_dex_folder(apk_dir)
        decoded_dir = apk_dir

        current_package_name, _ = extract_package_info(android_manifest)

        # Match the current package name to a config key or a config["package"]
        matched_key = None
        for key, value in config.items():
            if key == current_package_name:
                matched_key = key
                break
            if isinstance(value, dict) and value.get("package") == current_package_name:
                matched_key = key
                break

        if not matched_key:
            msg.error(
                f"No matching configuration found for package: {current_package_name}"
            )
            sys.exit(1)

        package_orig_name = matched_key
        package_orig_path = "L" + package_orig_name.replace(".", "/")
        apk_config = config[matched_key]

    return ApkBasic(
        apk_config=apk_config,
        package_orig_name=package_orig_name,
        package_orig_path=package_orig_path,
        dex_folder_exists=dex_folder_exists,
        decoded_dir=decoded_dir,
        android_manifest=android_manifest,
    )


def get_demo(conf, apk_dir, apk_config, isdex: bool, decoded_dir):
    editor = conf.apkeditor(args)

    if conf.log_level and isdex:
        msg.warning("Dex folder found. Some functions will be disabled.", bold=True)

    if editor.to_output:
        decoded_dir = editor.to_output.removesuffix(".apk")

    if not shutil.which("java"):
        msg.error("Java is not installed. Please install Java to proceed.")
        sys.exit(1)

    if os.path.isfile(apk_dir):
        apkeditor_decode(
            editor.editor_jar,
            apk_dir,
            editor.javaopts,
            decoded_dir,
            editor.dex_option,
            conf.command_quietly,
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


def get_updates(
    conf,
    android_manifest,
    apk_config,
    value_strings,
    smali_folder,
    resources_folder,
    package_orig_name,
    package_orig_path,
    dex_folder_exists,
):
    editor = conf.apkeditor(args)
    package = conf.package()
    facebook = conf.facebook()

    if not os.path.isfile(android_manifest):
        msg.error("AndroidManifest.xml not found in the directory.")
        sys.exit(1)

    if conf.app_name:
        update_app_name_values(conf.app_name, value_strings)

    if facebook and not args.no_facebook:
        update_facebook_app_values(
            value_strings,
            fb_app_id=facebook.appid,
            fb_client_token=facebook.client_token,
            fb_login_protocol_scheme=facebook.login_protocol_scheme,
        )

    if not args.no_rename_package and "package" in apk_config:
        rename_package_in_manifest(
            android_manifest,
            package_orig_name,
            new_package_name=package.name,
            level=conf.manifest_edit_level,
        )
        rename_package_in_resources(
            resources_folder,
            package_orig_name,
            new_package_name=package.name,
        )

        if not dex_folder_exists and not editor.dex_option:
            if args.move_rename_smali:
                update_smali_path_package(
                    smali_folder,
                    package_orig_path,
                    new_package_path=package.path,
                )
                update_smali_directory(
                    smali_folder,
                    package_orig_path,
                    new_package_path=package.path,
                )
            update_application_id_in_smali(
                smali_folder,
                package_orig_name,
                new_package_name=package.name,
            )

    if "manifest" in apk_config and "remove_metadata" in apk_config["manifest"]:
        remove_metadata_from_manifest(
            android_manifest, apk_config["manifest"]["remove_metadata"]
        )


def get_finish(conf, decoded_dir, apk_config):
    editor = conf.apkeditor(args)
    output_apk = os.path.basename(decoded_dir.rstrip("/"))
    output_apk_path = os.path.join(decoded_dir, output_apk + ".apk")

    if (
        not os.path.exists(output_apk_path)
        or shutil.which("apkeditor")
        or "jarpath" in apk_config["apkeditor"]
    ):
        output_apk_path = apkeditor_build(
            editor_jar=editor.editor_jar,
            input_dir=decoded_dir,
            output_apk=output_apk_path,
            javaopts=editor.javaopts,
            quietly=conf.command_quietly,
            force=args.force,
            clean=editor.clean,
        )

    setup_env({"BUILD": output_apk_path})
    if "commands" in apk_config and "end" in apk_config["commands"]:
        run_commands(apk_config["commands"]["end"], conf.command_quietly)

    msg.info("APK modification finished!", bold=True)


def runsteps():
    basic = get_the_input(packer)

    conf = ConfigHandler(basic.apk_config)
    android_manifest, smali_folder, resources_folder, value_strings, decoded_dir = (
        get_demo(
            conf,
            apk_dir=args.apk_dir,
            apk_config=basic.apk_config,
            isdex=basic.dex_folder_exists,
            decoded_dir=basic.decoded_dir,
        )
    )

    get_updates(
        conf,
        android_manifest=android_manifest,
        apk_config=basic.apk_config,
        value_strings=value_strings,
        smali_folder=smali_folder,
        resources_folder=resources_folder,
        package_orig_name=basic.package_orig_name,
        package_orig_path=basic.package_orig_path,
        dex_folder_exists=basic.dex_folder_exists,
    )

    get_finish(
        conf,
        decoded_dir=decoded_dir,
        apk_config=basic.apk_config,
    )
