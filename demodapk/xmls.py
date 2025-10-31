import os
import xml.etree.ElementTree as ET

from demodapk.utils import msg

ANDROID_NS = "http://schemas.android.com/apk/res/android"


def update_manifest_group(manifest_xml: str, apk_config: dict) -> None:
    """
    Apply all manifest updates defined in apk_config.
    Supports:
      - app_debuggable
      - export_all_activities
      - app_label
      - remove_metadata
    """
    if "manifest" not in apk_config:
        return

    config = apk_config["manifest"]

    if config.get("activity_exportall", False):
        update_manifest_activity_export_all(manifest_xml)

    if config.get("app_debuggable", False):
        update_manifest_app_debuggable(manifest_xml)

    if "app_label" in config:
        update_manifest_app_label(manifest_xml, config["app_label"])

    if "remove_metadata" in config:
        remove_metadata_from_manifest(manifest_xml, config["remove_metadata"])


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
            name = meta.get(f"{{{ANDROID_NS}}}name")
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
        ET.register_namespace("android", ANDROID_NS)
        tree = ET.parse(manifest_xml)
        root = tree.getroot()

        app = root.find("application")
        if app is None:
            msg.error("No <application> tag found in AndroidManifest.xml.")
            return

        app.set(f"{{{ANDROID_NS}}}debuggable", "true")
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
        ET.register_namespace("android", ANDROID_NS)
        tree = ET.parse(manifest_xml)
        root = tree.getroot()

        changed_activities = 0
        for activity in root.findall(".//activity"):
            updated = False
            if activity.get(f"{{{ANDROID_NS}}}exported") != "true":
                activity.set(f"{{{ANDROID_NS}}}exported", "true")
                updated = True
            if activity.get(f"{{{ANDROID_NS}}}enabled") != "true":
                activity.set(f"{{{ANDROID_NS}}}enabled", "true")
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
        ET.register_namespace("android", ANDROID_NS)
        tree = ET.parse(manifest_xml)
        root = tree.getroot()

        app = root.find("application")
        if app is None:
            msg.error("No <application> tag found in AndroidManifest.xml.")
            return

        app.set(f"{{{ANDROID_NS}}}label", app_name)
        xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")

        with open(manifest_xml, "w", encoding="utf-8") as f:
            f.write(xml_str)

        msg.success(f"Application label: [reset]{app_name}")

    except ET.ParseError as e:
        msg.error(f"Failed to parse manifest: {e}")
