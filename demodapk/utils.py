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


def show_logo(text, font="small", style="bold", ptb=1):
    logo_art = text2art(text, font=font)
    if isinstance(logo_art, str):
        lines = str(logo_art).splitlines()
        artlol = Gradient(lines)
        console.print(artlol, style=style)
        console.line(ptb)


def run_commands(commands, quietly, tasker: bool = False):
    """
    Run commands with support for conditional execution based on directory existence.

    Args:
        commands: List of commands or list of command dictionaries
        quietly: Run all commands quietly unless overridden per command
        tasker: If True, disables progress messages
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
            sys.exit(2)  # Custom exit code for cancel
        except Exception as e:
            msg.error(f"Unexpected error running command: {cmd}")
            msg.error(e)
            sys.exit(1)

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


class MessagePrinter:
    def print(self, message, **kwargs):
        color = kwargs.pop("color", None)
        bold = kwargs.pop("bold", False)
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

    def success(self, message, **kwargs):
        kwargs.setdefault("color", "green")
        kwargs.setdefault("prefix", "[*]")
        self.print(message, **kwargs)

    def warning(self, message, **kwargs):
        kwargs.setdefault("color", "yellow")
        kwargs.setdefault("prefix", "[~]")
        self.print(message, **kwargs)

    def error(self, message, **kwargs):
        kwargs.setdefault("color", "red")
        kwargs.setdefault("prefix", "[x]")
        self.print(message, **kwargs)

    def info(self, message, **kwargs):
        kwargs.setdefault("color", "cyan")
        kwargs.setdefault("prefix", "[!]")
        self.print(message, **kwargs)

    def progress(self, message, **kwargs):
        kwargs.setdefault("color", "magenta")
        kwargs.setdefault("prefix", "[$]")
        self.print(message, **kwargs)


msg = MessagePrinter()
log = logging.getLogger("demodapk")
