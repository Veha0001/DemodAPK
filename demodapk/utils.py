from typing import Optional

from art import text2art
from rich.console import Console
from rich.text import Text
from rich.traceback import install

install(show_locals=True)
console = Console()


def show_logo(text, font="small", color_pattern=None):
    logo_art = text2art(text, font=font)
    if color_pattern is None:
        color_blocks = [
            ("green1", 6),
            ("red1", 5),
            ("cyan2", 7),
            ("yellow2", 5),
            ("dodger_blue1", 6),
            ("medium_orchid1", 7),
            ("light_green", 5),
            ("orange_red1", 6),
        ]
    else:
        color_blocks = color_pattern

    if isinstance(logo_art, str):
        lines = logo_art.splitlines()
        for line in lines:
            colored_line = Text()
            color_index = 0
            count_in_block = 0
            current_color, limit = color_blocks[color_index]

            for char in line:
                colored_line.append(char, style=f"bold {current_color}")
                count_in_block += 1
                if count_in_block >= limit:
                    count_in_block = 0
                    color_index = (color_index + 1) % len(color_blocks)
                    current_color, limit = color_blocks[color_index]
            console.print(colored_line)


class MessagePrinter:
    def print(
        self,
        message: str,
        color: Optional[str] = None,
        inline: bool = False,
        bold: bool = False,
        prefix: Optional[str] = None,
        inlast: bool = False,
    ):
        styled_message = Text()
        if prefix:
            styled_message.append(f"{prefix} ", style="bold")
        style_str = f"bold {color}" if bold and color else color or "default"
        styled_message.append(message, style=style_str)

        if inline:
            console.print(styled_message, end=" ", soft_wrap=True)
            if inlast:
                console.print(" " * 5)
        else:
            console.print(styled_message, soft_wrap=True, justify="left")

    def success(self, message, bold: bool = False, inline=False, prefix="[*]"):
        self.print(message, color="green", bold=bold, inline=inline, prefix=prefix)

    def warning(
        self,
        message,
        color: Optional[str] = "yellow",
        bold: bool = False,
        inline=False,
    ):
        self.print(message, color=color, bold=bold, inline=inline, prefix="[~]")

    def error(self, message, inline=False):
        self.print(message, color="red", inline=inline, prefix="[x]")

    def info(
        self,
        message,
        color: str = "cyan",
        bold: bool = False,
        inline=False,
        prefix: str = "[!]",
    ):
        self.print(message, color=color, bold=bold, inline=inline, prefix=prefix)

    def progress(self, message, inline=False, bold: bool = False):
        self.print(message, color="magenta", bold=bold, inline=inline, prefix="[$]")


msg = MessagePrinter()
