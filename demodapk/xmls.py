import os
import xml.etree.ElementTree as ET

from demodapk.utils import msg

ANDROID_NS_URL = "http://schemas.android.com/apk/res/android"
ANDROID_NS = f"{{{ANDROID_NS_URL}}}"
ET.register_namespace("android", ANDROID_NS_URL)


def android_attr(name: str) -> str:
    """Return fully-qualified Android namespace attribute."""
    return f"{ANDROID_NS}{name}"


def update_manifest_group(manifest_xml: str, apk_config: dict) -> None:
    """
    Apply all manifest updates defined in apk_config.
    Supports:
      - app_debuggable
      - export_all_activities
      - app_label
      - remove_metadata
      - version_targetsdk
      - version_code
      - hide_app_icon
    """
    if "manifest" not in apk_config:
        return

    config: dict = apk_config["manifest"]

    if config.get("hide_app_icon", False):
        hide_app_icon(manifest_xml)

    if config.get("activity_exportall", False):
        update_manifest_activity_export_all(manifest_xml)

    if config.get("app_debuggable", False):
        update_manifest_app_debuggable(manifest_xml)

    if "app_label" in config:
        update_manifest_app_label(manifest_xml, config["app_label"])

    if "remove_metadata" in config:
        remove_metadata_from_manifest(manifest_xml, config["remove_metadata"])

    if config.get("version_targetsdk") is not None:
        set_target_sdk_version(manifest_xml, config["version_targetsdk"])

    if config.get("version_code") is not None:
        set_version_code(manifest_xml, config["version_code"])


def hide_app_icon(manifest_xml: str) -> None:
    """
    Hides the app icon from the launcher by changing the category of launcher activities.
    It finds activities with MAIN action and LAUNCHER category and changes
    the category to DEFAULT.
    """
    if not os.path.isfile(manifest_xml):
        msg.error(f"File {manifest_xml} not found.")
        return

    try:
        tree = ET.parse(manifest_xml)
        root = tree.getroot()

        changed_count = 0
        # Find all intent-filter tags
        for intent_filter in root.findall(".//intent-filter"):
            has_main_action = False
            launcher_category = None

            # Check for MAIN action
            for action in intent_filter.findall("action"):
                if action.get(android_attr("name")) == "android.intent.action.MAIN":
                    has_main_action = True
                    break

            if not has_main_action:
                continue

            # Find LAUNCHER category
            for category in intent_filter.findall("category"):
                if category.get(android_attr("name")) == "android.intent.category.LAUNCHER":
                    launcher_category = category
                    break

            if launcher_category is not None:
                launcher_category.set(android_attr("name"), "android.intent.category.DEFAULT")
                changed_count += 1

        if changed_count > 0:
            tree.write(manifest_xml, encoding="utf-8", xml_declaration=True)
            msg.success("App icon hidden from launcher.")
        else:
            msg.info("App icon is already hidden.")

    except ET.ParseError as e:
        msg.error(f"Failed to parse manifest: {e}")


def remove_metadata_from_manifest(manifest_xml, metadata_to_remove):
    """
    Remove specified <meta-data> entries from AndroidManifest.xml.

    Args:
        manifest_xml (str): Path to AndroidManifest.xml
        metadata_to_remove (list): List of metadata names to remove
    """
    # Filter out empty or invalid entries
    metadata_to_remove = [m.strip() for m in metadata_to_remove if isinstance(m, str) and m.strip()]
    if not metadata_to_remove:
        return

    if not os.path.isfile(manifest_xml):
        msg.warning(f"File {manifest_xml} does not exist.")
        return

    try:
        tree = ET.parse(manifest_xml)
        root = tree.getroot()

        app = root.find("application")
        if app is None:
            msg.warning("No <application> tag found in manifest.")
            return

        removed_count = 0
        for meta in list(app.findall("meta-data")):  # list() so we can remove
            name = meta.get(android_attr("name"))
            if name in metadata_to_remove:
                app.remove(meta)
                removed_count += 1

        if removed_count > 0:
            tree.write(manifest_xml, encoding="utf-8", xml_declaration=True)
            msg.success(f"Removed {removed_count} metadata entries from manifest.")
        else:
            msg.info("No matching metadata entries found to remove.")

    except ET.ParseError as e:
        msg.error(f"Failed to parse manifest: {e}")


def update_manifest_app_debuggable(manifest_xml: str) -> None:
    """
    Adds android:debuggable="true" to the <application> tag.
    """
    if not os.path.isfile(manifest_xml):
        msg.error("AndroidManifest.xml was not found.")
        return

    try:
        tree = ET.parse(manifest_xml)
        root = tree.getroot()

        app = root.find("application")
        if app is None:
            msg.error("No <application> tag found in AndroidManifest.xml.")
            return

        app.set(android_attr("debuggable"), "true")
        xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")

        with open(manifest_xml, "w", encoding="utf-8") as f:
            f.write(xml_str)

        msg.success("Application marked as debuggable.")

    except ET.ParseError as e:
        msg.error(f"Failed to parse manifest: {e}")


def update_manifest_activity_export_all(manifest_xml: str) -> None:
    """
    Sets android:exported="true" and android:enabled="true"
    for all <activity> tags.
    """
    if not os.path.isfile(manifest_xml):
        msg.error("AndroidManifest.xml was not found.")
        return

    try:
        tree = ET.parse(manifest_xml)
        root = tree.getroot()

        changed_activities = 0
        for activity in root.findall(".//activity"):
            updated = False
            if activity.get(android_attr("exported")) != "true":
                activity.set(android_attr("exported"), "true")
                updated = True
            if activity.get(android_attr("enabled")) != "true":
                activity.set(android_attr("enabled"), "true")
                updated = True
            if updated:
                changed_activities += 1

        if changed_activities == 0:
            msg.info("All activities already exported and enabled.")
            return

        xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")
        with open(manifest_xml, "w", encoding="utf-8") as f:
            f.write(xml_str)

        msg.success(f"Updated {changed_activities} activities.")

    except ET.ParseError as e:
        msg.error(f"Failed to parse manifest: {e}")


def update_manifest_app_label(manifest_xml: str, app_name: str) -> None:
    """
    Updates the android:label attribute of the <application> tag.
    """
    if not os.path.isfile(manifest_xml):
        msg.error("AndroidManifest.xml was not found.")
        return

    try:
        tree = ET.parse(manifest_xml)
        root = tree.getroot()

        app = root.find("application")
        if app is None:
            msg.error("No <application> tag found in AndroidManifest.xml.")
            return

        app.set(android_attr("label"), app_name)
        xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")

        with open(manifest_xml, "w", encoding="utf-8") as f:
            f.write(xml_str)

        msg.success(f"Application label: [reset]{app_name}")

    except ET.ParseError as e:
        msg.error(f"Failed to parse manifest: {e}")


def set_target_sdk_version(manifest_xml: str, version: int) -> None:
    """
    Sets the android:targetSdkVersion in AndroidManifest.xml.

    Args:
        manifest_xml (str): Path to AndroidManifest.xml
        version (int): Target SDK version to set
    """
    if not os.path.isfile(manifest_xml):
        msg.error(f"File {manifest_xml} not found.")
        return
    if version < 23:
        msg.error("targetSdkVersion must be >= 23.")
        return

    try:
        tree = ET.parse(manifest_xml)
        root = tree.getroot()

        # Find existing <uses-sdk> or create one if missing
        uses_sdk = root.find("uses-sdk")
        if uses_sdk is None:
            uses_sdk = ET.Element("uses-sdk")
            root.append(uses_sdk)

        # Set targetSdkVersion attribute
        uses_sdk.set(android_attr("targetSdkVersion"), str(version))
        tree.write(manifest_xml, encoding="utf-8", xml_declaration=True)
        msg.success(f"Set targetSdkVersion to {version}.")

    except ET.ParseError as e:
        msg.error(f"Failed to parse manifest: {e}")


def set_version_code(manifest_xml: str, version_code: int) -> None:
    """
    Sets the android:versionCode attribute in AndroidManifest.xml.

    Args:
        manifest_xml (str): Path to AndroidManifest.xml
        version_code (int): Version code to set (must be >= 1)
    """
    if version_code < 1:
        msg.warning("Version code must be >= 1.")
        return

    if not os.path.isfile(manifest_xml):
        msg.error(f"File {manifest_xml} not found.")
        return

    try:
        tree = ET.parse(manifest_xml)
        root = tree.getroot()

        # Set android:versionCode on <manifest> tag
        root.set(android_attr("versionCode"), str(version_code))

        tree.write(manifest_xml, encoding="utf-8", xml_declaration=True)
        msg.success(f"Set versionCode to {version_code}.")

    except ET.ParseError as e:
        msg.error(f"Failed to parse manifest: {e}")
