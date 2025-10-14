"""
Utility functions for DemodAPK.

This module provides utility functions and classes for:
- Logging configuration with rich formatting
- Command execution with progress tracking
- Message printing with colored output
- Logo display with gradient effects
"""

import os
import subprocess
import sys
from typing import Any, Optional

from art import text2art
from platformdirs import user_config_path
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.traceback import install
from rich_gradient import Gradient

install(show_locals=True)
console = Console(log_path=False)

CONFIG_DIR = user_config_path(
    appname="demodapk", appauthor="VehaLV", ensure_exists=True, roaming=True
)


def show_logo(
    text: Any,
    font: str = "small",
    style: tuple[str, bool] | bool = ("bold", True),
    fits: tuple[bool, int] | bool = (True, 1),
    panel: bool = True,
) -> None:
    """
    Display ASCII art logo with gradient coloring.

    Args:
        text (str): Text to convert to ASCII art
        font (str, optional): ASCII art font name. Defaults to "small".
        style (str, bool): Text style. Defaults to "bold". Gradient colors.
        like (bool, int): Panel fit, Number of blank lines after logo. Defaults to 1.
        panel (bool): Print inside a rich panel.
    Returns:
        None
    """
    if isinstance(style, bool):
        style = ("bold", style)
    if isinstance(fits, bool):
        fits = (fits, 1)
    logo_art = text2art(text, font=font)
    if isinstance(logo_art, str):
        lines = str(logo_art).splitlines()
        if panel:
            if fits[0]:
                lines = Panel.fit("\n".join(lines))
            else:
                lines = Panel("\n".join(lines))

        lolcat = Gradient(lines) if style[1] else lines
        console.print(lolcat, style=style[0], soft_wrap=True)
        console.line(fits[1])


class CLIprinter:
    """RICH Style, Text Printer"""

    def __call__(self) -> None:
        """Caller pass nothing"""

    def print(
        self,
        value: str | Any = "",
        style: Optional[str] = "bold",
        prefix: Optional[str] = "?",
    ):
        """Print using rich console"""
        fix = f"\\[[{style}]{prefix}[reset]] "
        console.print(
            f"{fix}[{style}]{value}",
            markup=True,
            highlight=True,
            soft_wrap=True,
        )

    def info(self, value: Any, style: str = "bold cyan", prefix: str = "!"):
        """Level Info"""
        self.print(value=value, style=style, prefix=prefix)

    def error(self, value: Any, style: str = "bold red", prefix: str = "x"):
        """Level Error"""
        self.print(value=value, style=style, prefix=prefix)

    def warning(self, value: Any, style: str = "bold yellow", prefix: str = "~"):
        """Level Warning"""
        self.print(value=value, style=style, prefix=prefix)

    def progress(self, value: Any, style: str = "bold magenta", prefix: str = "$"):
        """Level Progress"""
        self.print(value=value, style=style, prefix=prefix)

    def success(self, value: Any, style: str = "bold green", prefix: str = "*"):
        """Level Success"""
        self.print(value=value, style=style, prefix=prefix)


msg = CLIprinter()


def run_commands(commands: list, quietly: bool, tasker: bool = False) -> None:
    """
    Run shell commands with support for conditional execution and progress tracking.

    Can handle both simple command strings and command dictionaries with
    additional options like titles and quiet mode overrides.

    Args:
        commands (list): List of command strings or command dictionaries
        quietly (bool): Run all commands quietly unless overridden per command
        tasker (bool, optional): Disable progress messages if True. Defaults to False.

    Returns:
        None

    Raises:
        SystemExit: If command execution fails or is interrupted
    """

    def run(cmd, quiet_mode, title: str = ""):
        try:
            if quiet_mode:
                if not tasker and title:
                    msg.progress(title)
                subprocess.run(
                    cmd,
                    shell=True,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    env=os.environ,
                )
            else:
                subprocess.run(cmd, shell=True, check=True, env=os.environ)
        except subprocess.CalledProcessError as e:
            if e.returncode == 130:
                msg.warning("Execution cancelled by user (Ctrl+C).")
                sys.exit(2)
            else:
                msg.error(e)
                sys.exit(1)
        except KeyboardInterrupt:
            msg.warning("Execution cancelled by user.")
            sys.exit(2)  # Custom exit code for cancellation

    if isinstance(commands, list):
        for command in commands:
            if isinstance(command, str):
                run(command, quietly)
            elif isinstance(command, dict):
                cmd = command.get("run")
                title = command.get("title", "")
                quiet = command.get("quiet", quietly)
                if cmd:
                    run(cmd, quiet, title)


def showbox_packages(available_packages, selected_idx=None):
    """Print table of Packages in rich styling"""
    table = Table(title="Available Packages", box=box.ROUNDED, show_lines=True)
    table.add_column("Index", style="cyan", justify="right")
    table.add_column("Package Name", style="magenta")

    for i, name in enumerate(available_packages):
        if i == selected_idx:
            table.add_row(str(i), f"[bold green]{name}[/bold green]")
        else:
            table.add_row(str(i), name)

    console.print(table)


if __name__ == "__main__":
    show_logo("Diego")
    try:
        msg.progress("The World!")
        subprocess.run("exit 2", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        msg.error(e)
    msg.info("Hello World")
    msg.error("Something wrong")
    msg.warning("He is here!")
    msg.success("Everything gonna be alright.")
    msg.print("I am Grok", style="b u", prefix="∅")
