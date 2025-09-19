import json
import os
import sys

import inquirer

import demodapk
from demodapk.utils import console

SCHEMA_PATH = os.path.join(os.path.dirname(demodapk.__file__), "schema.json")
SCHEMA_URL = (
    "https://raw.githubusercontent.com/Veha0001/DemodAPK/refs/heads/main/demodapk"
    "/schema.json"
)
SCHEMA_NETLIFY = "https://demodapk.netlify.app/schema.json"
CONFIG_FILE = "config.json"


def ensure_config(schema_value):
    """Open or create config.json and set $schema at the top."""
    config = {}

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                console.log("config.json exists but is invalid JSON. Rewriting it.")

    # Insert $schema at the top by creating a new dict
    new_config = {"$schema": schema_value}
    for k, v in config.items():
        if k != "$schema":  # Avoid duplicates
            new_config[k] = v

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(new_config, f, indent=4)
        console.print(schema_value)
    console.log("Add selected $schema to ./config.json")


def get_schema():
    questions = [
        inquirer.List(
            "schema_index",
            message="Select a way of JSON Schema",
            choices=["pack", "netlify", "githubusercontent"],
            default="netlify",
        )
    ]

    ans = inquirer.prompt(questions)
    choice = ans.get("schema_index") if ans else None

    if choice:
        console.log(f"[bold green]You selected Schema {choice}:[/bold green]")
    else:
        console.print("[red]No selection made[/red]")
        sys.exit(1)

    if choice == "pack":
        ensure_config(SCHEMA_PATH)
    elif choice == "githubusercontent":
        ensure_config(SCHEMA_URL)
    else:
        ensure_config(SCHEMA_NETLIFY)

    sys.exit(0)
