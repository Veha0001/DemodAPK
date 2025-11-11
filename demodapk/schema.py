"""
JSON Schema configuration module.

This module provides functionality for managing JSON schema configuration:
- Schema selection and application
- Config file creation and updates
- Remote schema fetching
"""

import json
import os
import sys

import inquirer

import demodapk
from demodapk.utils import msg

# Schema configuration constants
SCHEMA_PATH = os.path.join(os.path.dirname(demodapk.__file__), "schema.json")
SCHEMA_URL = (
    "https://raw.githubusercontent.com/Veha0001/DemodAPK/refs/heads/main/demodapk/schema.json"
)
SCHEMA_NETLIFY = "https://demodapk.netlify.app/schema.json"
CONFIG_FILE = "config.json"


def ensure_config(schema_value: str) -> None:
    """
    Open or create config.json and set $schema at the top.

    Reads existing config file if present, otherwise creates new one.
    Places schema reference at the start of the JSON configuration.

    Args:
        schema_value (str): URL or path to JSON schema

    Returns:
        None

    Raises:
        IOError: If unable to write config file
        JSONDecodeError: If existing config contains invalid JSON
    """
    config = {}

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                msg.error("config.json exists but is invalid JSON. Rewriting it.")

    # Insert $schema at the top by creating a new dict
    new_config = {"$schema": schema_value}
    for k, v in config.items():
        if k != "$schema":  # Avoid duplicates
            new_config[k] = v
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(new_config, f, indent=4)
    except (PermissionError, json.JSONDecodeError, TypeError, OSError) as e:
        msg.error(f"Error: {type(e).__name__}: {e}", style="bold red")
    msg.success("Add selected [blue]$schema[/blue] to: [u]config.json[/u]")
    sys.exit(0)


def get_schema() -> None:
    """
    Interactive schema selection and configuration.

    Prompts user to select schema source and updates config file.
    Options include:
    - Local package schema
    - Netlify hosted schema
    - GitHub hosted schema

    Returns:
        None

    Raises:
        SystemExit: After schema selection and config update
    """
    questions = [
        inquirer.List(
            "schema_index",
            message="Select a way of JSON Schema",
            choices=["project", "netlify", "githubusercontent"],
            default="netlify",
        )
    ]

    ans = inquirer.prompt(questions)
    choice = ans.get("schema_index") if ans else None
    if choice == "project":
        schema_link = SCHEMA_PATH
    elif choice == "githubusercontent":
        schema_link = SCHEMA_URL
    else:
        schema_link = SCHEMA_NETLIFY
    if choice:
        msg.info(
            f"Selected [blue]$schema[/blue]: [u][link={schema_link}]{choice}[/link][/u]",
        )
    else:
        msg.error("No selection made")
        sys.exit(1)

    return ensure_config(schema_link)
