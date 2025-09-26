"""
Utility functions for DemodAPK.

This module provides utility functions and classes for:
- Logging configuration with rich formatting
- Command execution with progress tracking
- Message printing with colored output
- Logo display with gradient effects
"""

import logging
import os
import subprocess
import sys
from art import text2art
from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text
from rich.traceback import install
from rich_gradient import Gradient

install(show_locals=True)
console = Console()

logging.basicConfig(
    level="NOTSET",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[
        RichHandler(rich_tracebacks=True, markup=True, show_path=False, show_time=False)
    ],
)


def show_logo(
    text: str, font: str = "small", style: str = "bold", ptb: int = 1
) -> None:
    """
    Display ASCII art logo with gradient coloring.

    Args:
        text (str): Text to convert to ASCII art
        font (str, optional): ASCII art font name. Defaults to "small".
        style (str, optional): Text style. Defaults to "bold".
        ptb (int, optional): Number of blank lines after logo. Defaults to 1.

    Returns:
        None
    """
    logo_art = text2art(text, font=font)
    if isinstance(logo_art, str):
        lines = str(logo_art).splitlines()
        artlol = Gradient(lines)
        console.print(artlol, style=style)
        console.line(ptb)


class MessagePrinter:
    """
    Formatted message printer with colored output and prefix icons.

    Provides methods for printing:
    - Success messages (green with [*] prefix)
    - Warning messages (yellow with [~] prefix)
    - Error messages (red with [x] prefix)
    - Info messages (cyan with [!] prefix)
    - Progress messages (magenta with [$] prefix)
    """

    def print(self, message: str, **kwargs) -> None:
        """
        Print formatted message with optional styling.

        Args:
            message (str): Message text to print
            **kwargs: Optional styling parameters:
                color (str): Text color name
                bold (bool): Make text bold
                inline (bool): Print inline without newline
                prefix (str): Message prefix icon/text
                inlast (bool): Add extra spacing after inline message

        Returns:
            None
        """
        color = kwargs.pop("color", None)
        bold = kwargs.pop("bold", True)
        inline = kwargs.pop("inline", False)
        prefix = kwargs.pop("prefix", None)
        inlast = kwargs.pop("inlast", False)
        styled_message = Text()
        if prefix:
            styled_message.append(f"{prefix} ", style="bold")

        style_str = f"bold {color}" if bold and color else color or ""
        styled_message.append(Text.from_markup(message, style=style_str))

        if inline:
            console.print(
                styled_message, end=" ", soft_wrap=True, highlight=True, markup=True
            )
            if inlast:
                console.print(" " * 5)
        else:
            console.print(
                styled_message,
                soft_wrap=True,
                markup=True,
                justify="left",
                highlight=True,
            )

    def success(self, message, **kwargs) -> None:
        """
        Print success message in green with [*] prefix.

        Args:
            message (str): Message text to print
            **kwargs: Optional styling parameters:
                color (str): Text color name
                bold (bool): Make text bold
                inline (bool): Print inline without newline
                prefix (str): Message prefix icon/text
                inlast (bool): Add extra spacing after inline message

        Returns:
            None
        """
        kwargs.setdefault("color", "green")
        kwargs.setdefault("prefix", "[*]")
        self.print(message, **kwargs)

    def warning(self, message, **kwargs) -> None:
        """
        Print warning message in yellow with [~] prefix.

        Args:
            message (str): Message text to print
            **kwargs: Optional styling parameters:
                color (str): Text color name
                bold (bool): Make text bold
                inline (bool): Print inline without newline
                prefix (str): Message prefix icon/text
                inlast (bool): Add extra spacing after inline message

        Returns:
            None
        """
        kwargs.setdefault("color", "yellow")
        kwargs.setdefault("prefix", "[~]")
        self.print(message, **kwargs)

    def error(self, message, **kwargs) -> None:
        """
        Print error message in red with [x] prefix.

        Args:
            message (str): Message text to print
            **kwargs: Optional styling parameters:
                color (str): Text color name
                bold (bool): Make text bold
                inline (bool): Print inline without newline
                prefix (str): Message prefix icon/text
                inlast (bool): Add extra spacing after inline message

        Returns:
            None
        """
        kwargs.setdefault("color", "red")
        kwargs.setdefault("prefix", "[x]")
        self.print(message, **kwargs)

    def info(self, message, **kwargs) -> None:
        """
        Print info message in cyan with [!] prefix.

        Args:
            message (str): Message text to print
            **kwargs: Optional styling parameters:
                color (str): Text color name
                bold (bool): Make text bold
                inline (bool): Print inline without newline
                prefix (str): Message prefix icon/text
                inlast (bool): Add extra spacing after inline message

        Returns:
            None
        """
        kwargs.setdefault("color", "cyan")
        kwargs.setdefault("prefix", "[!]")
        self.print(message, **kwargs)

    def progress(self, message, **kwargs) -> None:
        """
        Print progress message in magenta with [$] prefix.

        Args:
            message (str): Message text to print
            **kwargs: Optional styling parameters:
                color (str): Text color name
                bold (bool): Make text bold
                inline (bool): Print inline without newline
                prefix (str): Message prefix icon/text
                inlast (bool): Add extra spacing after inline message

        Returns:
            None
        """
        kwargs.setdefault("color", "magenta")
        kwargs.setdefault("prefix", "[$]")
        self.print(message, **kwargs)


msg = MessagePrinter()
log = logging.getLogger("demodapk")


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
                msg.warning(f"Command failed: {cmd}")
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


if __name__ == "__main__":
    show_logo("Hello World", font="small", style="bold cyan", ptb=1)
    # Test msg and log
    log.info("Starting printing messages")
    msg.info("This is an info message.")
    msg.success("This is a success message.")
    msg.warning("This is a warning message.")
    msg.error("This is an error message.")
    log.info("Print every msg kwargs")
    msg.info("Inline message", inline=True, inlast=True)
    msg.info("Bold inline message", inline=True, bold=True, inlast=True)
    msg.info("Not-Bold colored inline message", inline=True, bold=False, color="pink1")
    msg.info("FINE", color="blue")
    log.info("Everything Done.")
    log.info("start run_commands test")
    run_commands(
        [
            "echo 'Hello World'",
            {
                "run": "python -c 'import datetime; print(datetime.datetime.now())'",
                "title": "Today",
                "quiet": False,
            },
            {
                "run": "python -c 'import time; time.sleep(2)'",
                "title": "Sleeping",
                "quiet": True,
            },
        ],
        quietly=False,
    )
