#!/usr/bin/env python
"""
A script for patching binary files based on configurations provided in JSON format.
Supports direct offset patching, method name-based patching, and wildcard pattern patching.
"""

import json
import os
import re
import sys

# ANSI escape codes for colors
RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"

DEFAULT_CONFIG_PATH = "config.json"  # Default configuration file name


def load_config(config_path):
    """Load the JSON configuration file."""
    if not os.path.exists(config_path):
        print(f"{RED}Error: Configuration file '{config_path}' not found.{RESET}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)


def replace_hex_at_offset(data, offset, repl):
    """Replace hex bytes at a specified offset in the binary data."""
    repl_bytes = bytes.fromhex(repl.replace(" ", ""))
    data[offset: offset + len(repl_bytes)] = repl_bytes


def wildcard_pattern_scan(data, pattern):
    """Search for a byte pattern with wildcards in the given data."""
    pattern_bytes = pattern.split(" ")
    pattern_length = len(pattern_bytes)

    # Convert pattern into a list of bytes (integers) or None for wildcards
    pattern_bytes = [int(b, 16) if b != "??" else None for b in pattern_bytes]

    for i, _ in enumerate(data[: -pattern_length + 1]):
        if all(p_b is None or p_b == data[i + j]
                for j, p_b in enumerate(pattern_bytes)):
            return i
    return -1


def patch_code(input_filename, output_filename, patch_list, dump_path):
    """Patch the input binary file based on the configuration."""
    if not os.path.exists(input_filename):
        print(f"{RED}Error: Input file '{input_filename}' not found.{RESET}")
        return

    try:
        with open(input_filename, "rb") as file:
            data = bytearray(file.read())
    except OSError as e:
        print(f"{RED}Error reading input file: {e}{RESET}")
        return

    # Check if any patch uses a wildcard, and print a single note if so
    if any("wildcard" in patch for patch in patch_list):
        print(
            f"{CYAN}Note: Scanning with wildcards; this may take longer on larger files...{RESET}"
        )

    for patch in patch_list:
        # Determine whether to use method_name, offset, or wildcard
        if "method_name" in patch:
            offset = find_offset_by_method_name(
                patch["method_name"], dump_path)
            if offset is None:
                print(
                    f"{YELLOW}Warning: Method '{
                        patch['method_name']}' not found. Skipping patch.{RESET}")
                continue
        elif "offset" in patch:
            offset = int(patch["offset"], 16)  # Convert hex string to integer
        elif "wildcard" in patch:
            offset = wildcard_pattern_scan(data, patch["wildcard"])
            if offset == -1:
                print(
                    f"{YELLOW}Warning: No match found for wildcard pattern '{
                        patch['wildcard']}'. Skipping patch.{RESET}")
                continue
        else:
            print(
                f"{YELLOW}Warning: No valid patch definition found. Skipping.{RESET}")
            continue

        if offset >= len(data):
            print(
                f"{RED}Error: Offset 0x{
                    offset:X} is out of range for the input file.{RESET}")
            continue

        print(f"{GREEN}Patching at Offset: 0x{offset:X}{RESET}")
        replace_hex_at_offset(data, offset, patch["hex_code"])

    try:
        with open(output_filename, "wb") as file:
            file.write(data)
    except OSError as e:
        print(f"{RED}Error writing output file: {e}{RESET}")
        return

    print(f"{CYAN}Patching completed. Output written to '{output_filename}'.{RESET}")


def find_offset_by_method_name(method_name, dump_path):
    """Find the offset of a method name in the dump file."""
    if not os.path.exists(dump_path):
        print(f"{RED}Error: '{dump_path}' file not found.{RESET}")
        return None

    try:
        with open(dump_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
    except OSError as e:
        print(f"{RED}Error reading dump file: {e}{RESET}")
        return None

    for i, line in enumerate(lines):
        if method_name in line:
            # Look at the previous line for the offset
            if i > 0:
                match = re.search(r"Offset: 0x([0-9A-Fa-f]+)", lines[i - 1])
                if match:
                    offset = int(match.group(1), 16)
                    print(
                        f"{GREEN}Found {method_name} at Offset: 0x{
                            offset:X}{RESET}")
                    return offset
                print(
                    f"{YELLOW}Warning: No offset found for {method_name}.{RESET}")
    return None


# Argument parsing
config_path = DEFAULT_CONFIG_PATH if len(sys.argv) < 2 else sys.argv[1]
config = load_config(config_path)

# Extract necessary details
input_filename = config["Patcher"]["input_file"]
dump_path = config["Patcher"]["dump_file"]
output_filename = config["Patcher"]["output_file"]
patch_list = config["Patcher"]["patches"]

# Apply patches to binary
patch_code(input_filename, output_filename, patch_list, dump_path)
