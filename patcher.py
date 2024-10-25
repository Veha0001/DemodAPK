#!/usr/bin/env python
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

DEFAULT_CONFIG_FILE = "config.json"  # Default configuration file name

def load_config(config_file):
    """Load the JSON configuration file."""
    if not os.path.exists(config_file):
        print(f"{RED}Error: Configuration file '{config_file}' not found.{RESET}")
        sys.exit(1)

    with open(config_file, 'r') as f:
        return json.load(f)

def replace_hex_at_offset(data, offset, repl):
    """Replace hex bytes at a specified offset in the binary data."""
    repl_bytes = bytes.fromhex(repl.replace(' ', ''))
    data[offset:offset + len(repl_bytes)] = repl_bytes

def patch_code(in_file, out_file, patches, dump_file):
    """Patch the input binary file based on the configuration."""
    if not os.path.exists(in_file):
        print(f"{RED}Error: Input file '{in_file}' not found.{RESET}")
        return

    try:
        with open(in_file, "rb") as f:
            data = bytearray(f.read())
    except Exception as e:
        print(f"{RED}Error reading input file: {e}{RESET}")
        return

    for patch in patches:
        # Determine whether to use method_name or offset
        if "method_name" in patch:
            offset = find_offset_by_method_name(patch["method_name"], dump_file)
            if offset is None:
                print(f"{YELLOW}Warning: Method '{patch['method_name']}' not found. Skipping patch.{RESET}")
                continue
        elif "offset" in patch:
            offset = int(patch["offset"], 16)  # Convert hex string to integer
        else:
            print(f"{YELLOW}Warning: No valid patch definition found. Skipping.{RESET}")
            continue
        
        if offset >= len(data):
            print(f"{RED}Error: Offset 0x{offset:X} is out of range for the input file.{RESET}")
            continue

        print(f"{GREEN}Patching at offset 0x{offset:X}{RESET}")
        replace_hex_at_offset(data, offset, patch["hex_code"])

    try:
        with open(out_file, "wb") as f:
            f.write(data)
    except Exception as e:
        print(f"{RED}Error writing output file: {e}{RESET}")
        return

    print(f"{CYAN}Patching completed. Output written to '{out_file}'.{RESET}")

def find_offset_by_method_name(method_name, dump_file):
    """Find the offset of a method name in the dump file."""
    if not os.path.exists(dump_file):
        print(f"{RED}Error: '{dump_file}' file not found.{RESET}")
        return None

    try:
        with open(dump_file, "r", encoding="utf-8") as file:
            lines = file.readlines()
    except Exception as e:
        print(f"{RED}Error reading dump file: {e}{RESET}")
        return None

    for i in range(len(lines)):
        if method_name in lines[i]:
            # Look at the previous line for the offset
            if i > 0:
                match = re.search(r"Offset: 0x([0-9A-Fa-f]+)", lines[i-1])
                if match:
                    offset = int(match.group(1), 16)
                    print(f"{GREEN}Found {method_name} at offset 0x{offset:X}{RESET}")
                    return offset
                else:
                    print(f"{YELLOW}Warning: No offset found for {method_name}.{RESET}")
    return None

# Argument parsing
config_file = DEFAULT_CONFIG_FILE if len(sys.argv) < 2 else sys.argv[1]
config = load_config(config_file)

# Extract necessary details
input_file = config["Patcher"]["input_file"]
dump_file = config["Patcher"]["dump_file"]
output_file = config["Patcher"]["output_file"]
patches = config["Patcher"]["patches"]

# Apply patches to binary
patch_code(input_file, output_file, patches, dump_file)
