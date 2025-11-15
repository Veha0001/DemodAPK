"""Module for applying hex patches to binary files."""

import re
from pathlib import Path

from demodapk.utils import msg


def _hex_to_regex(hex_string: str) -> re.Pattern | None:
    """Converts a hex string with '??' wildcards to a compiled regex pattern."""
    hex_string = re.sub(r"\s+", "", hex_string)
    if len(hex_string) % 2 != 0:
        msg.error(f"Odd-length hex string: {hex_string}")
        return None

    pattern = b""
    try:
        i = 0
        while i < len(hex_string):
            two_chars = hex_string[i : i + 2]
            if two_chars == "??":
                pattern += b"."
            else:
                # For literal hex, escape it to handle potential regex special characters
                pattern += re.escape(bytes.fromhex(two_chars))
            i += 2
    except ValueError:
        msg.error(f"Invalid hex characters in search pattern: {hex_string}")
        return None

    return re.compile(pattern, re.DOTALL)


def _parse_replace_pattern(
    hex_replace_str: str, original_bytes: bytearray, offset: int
) -> bytes | None:
    """
    Parses a hex replace string, handling '??' wildcards to keep original bytes.

    Args:
        hex_replace_str: The hex string for replacement, can contain '??'.
        original_bytes: The bytearray of the file content.
        offset: The offset in original_bytes where the replacement would start.

    Returns:
        The actual bytes to write, or None if invalid.
    """
    clean_hex = re.sub(r"\s+", "", hex_replace_str)
    if len(clean_hex) % 2 != 0:
        msg.error(f"Odd-length hex replace string: {hex_replace_str}")
        return None

    result_bytes = bytearray()
    try:
        for i in range(0, len(clean_hex), 2):
            two_chars = clean_hex[i : i + 2]
            if two_chars == "??":
                # Keep original byte at this position
                current_replace_pos = offset + len(result_bytes)
                if current_replace_pos >= len(original_bytes):
                    msg.error(
                        "Replace pattern '??' goes out of bounds at offset "
                        f"{hex(current_replace_pos)}."
                    )
                    return None
                result_bytes.append(original_bytes[current_replace_pos])
            else:
                result_bytes.append(int(two_chars, 16))
    except ValueError:
        msg.error(f"Invalid hex characters in replace pattern: {hex_replace_str}")
        return None

    return bytes(result_bytes)


def _apply_offset_patch(
    hex_search_or_offset: str,
    hex_replace_str: str,
    patched_data: bytearray,
    verbose: bool,
) -> tuple[bool, bytearray]:
    """Applies an offset-based hex patch."""
    try:
        target_offset = int(hex_search_or_offset, 16)
    except ValueError:
        msg.error(f"Invalid hex offset: {hex_search_or_offset}")
        return False, patched_data

    replace_bytes = _parse_replace_pattern(hex_replace_str, patched_data, target_offset)
    if not replace_bytes:
        return False, patched_data

    if target_offset + len(replace_bytes) > len(patched_data):
        msg.error(
            "Offset patch out of bounds: "
            f"{hex(target_offset)} with replace length {len(replace_bytes)}."
        )
        return False, patched_data

    # Apply the patch directly
    patched_data[target_offset : target_offset + len(replace_bytes)] = replace_bytes

    if verbose:
        msg.done(f"Replace: [b magenta]{hex_replace_str}")
    msg.info(f"  -> Offset: {hex(target_offset)}")
    return True, patched_data


def _apply_search_replace_patch(
    hex_search_or_offset: str,
    hex_replace_str: str,
    patched_data: bytearray,
    verbose: bool,
) -> tuple[int, bytearray]:
    """Applies a search-and-replace hex patch."""
    regex = _hex_to_regex(hex_search_or_offset)
    if not regex:
        return 0, patched_data

    # For search-and-replace, replace_bytes must be literal (no wildcards)
    try:
        replace_bytes = bytes.fromhex(re.sub(r"\s+", "", hex_replace_str))
    except ValueError:
        msg.error(f"Invalid hex characters in replace pattern: {hex_replace_str}")
        return 0, patched_data

    current_offset = 0
    patches_in_this_code = 0
    while current_offset < len(patched_data):
        match = regex.search(patched_data, current_offset)

        if match:
            found_offset = match.start()
            if verbose:
                msg.done(f"Found: [b blue]{hex_search_or_offset}")
                msg.done(f"Replace: [b magenta]{hex_replace_str}")

            msg.info(f"  -> Offset: [u green]{hex(found_offset)}[/u green]", prefix="?")

            end_of_replace = found_offset + len(replace_bytes)
            if end_of_replace > len(patched_data):
                msg.error(f"Patch is out of bounds for pattern {hex_search_or_offset}.")
                break

            patched_data[found_offset:end_of_replace] = replace_bytes
            patches_in_this_code += 1
            current_offset = end_of_replace
        else:
            break  # No more matches found

    if patches_in_this_code == 0:
        msg.warning(f"Not found: [b blue]{hex_search_or_offset}")
    return patches_in_this_code, patched_data


def update_bin_with_patch(attr: dict, decoded_dir: str):
    """
    Update binary file with hex patch.

    Args:
        attr (dict): The application-specific configuration containing the 'hex' key.
        decoded_dir (str): The root directory of the decoded APK.
    """
    hex_patches = attr.get("hex", [])
    for hex_patch in hex_patches:
        rel_path = hex_patch.get("path")
        patches = hex_patch.get("patch", [])
        verbose = hex_patch.get("verbose", False)

        if not rel_path or not patches:
            msg.error("Invalid hex patch format: requires 'path' and 'patch'.")
            continue

        full_path = Path(decoded_dir) / rel_path
        patch_codes(full_path, patches, verbose)


def patch_codes(src: Path, codes: list[str], verbose: bool = False) -> None:
    """
    Patch binary file with given hex codes.
    Each code in codes should be in the format:
    "search | replace" or "offset | replace"
    :param src: Path to the binary file to be patched.
    :param codes: List of hex code strings to search and replace.
    :param verbose: If True, print detailed information about the patches.

    :return: None
    """
    if not src.exists():
        msg.error(f"File not found: {src.name}")
        return

    try:
        with open(src, "rb") as f:
            binary_data = f.read()
    except IOError as e:
        msg.error(f"Failed to read file {src.name}: {e}")
        return

    patched_data = bytearray(binary_data)
    total_patches_applied = 0

    msg.info(f"Analyze [b cyan]{src.name}[/] for hex patches.")

    for code in codes:
        try:
            hex_search_or_offset, hex_replace_str = map(str.strip, code.split("|"))
        except ValueError:
            msg.error(f"Invalid patch format: {code}")
            continue

        # Check if hex_search_or_offset is an offset
        if hex_search_or_offset.lower().startswith("0x"):
            applied, patched_data = _apply_offset_patch(
                hex_search_or_offset, hex_replace_str, patched_data, verbose
            )
            if applied:
                total_patches_applied += 1
        else:  # Existing search-and-replace logic
            applied_count, patched_data = _apply_search_replace_patch(
                hex_search_or_offset, hex_replace_str, patched_data, verbose
            )
            total_patches_applied += applied_count

    if total_patches_applied > 0:
        try:
            with open(src, "wb") as f:
                f.write(patched_data)
            msg.done(f"Updated {total_patches_applied} hex patch(es) in [b cyan]{src.name}[/].")
        except IOError as e:
            msg.error(f"Failed to write to file {src}: {e}")
    else:
        msg.info(f"No patches applied to [b cyan]{src.name}[/].")
