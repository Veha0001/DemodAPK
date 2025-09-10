from typing import Optional

from art import text2art
from termcolor import colored, cprint


def show_logo(text, font="small", color_pattern=None):
    logo_art = text2art(text, font=font)
    if color_pattern is None:
        color_blocks = [
            ("green", 6),
            ("red", 5),
            ("cyan", 7),
            ("yellow", 5),
            ("blue", 6),
            ("magenta", 7),
            ("light_green", 5),
            ("light_cyan", 6),
        ]
    else:
        color_blocks = color_pattern

    if isinstance(logo_art, str):
        lines = logo_art.splitlines()
        for line in lines:
            colored_line = ""
            color_index = 0
            count_in_block = 0
            current_color, limit = color_blocks[color_index]

            for char in line:
                colored_line += colored(char, current_color, attrs=["bold"])
                count_in_block += 1
                if count_in_block >= limit:
                    count_in_block = 0
                    color_index = (color_index + 1) % len(color_blocks)
                    current_color, limit = color_blocks[color_index]
            print(colored_line)


class MessagePrinter:
    def print(
        self,
        message: str,
        color: Optional[str] = None,
        inline: bool = False,
        bold: bool = False,
        prefix: Optional[str] = None,
        flush: bool = False,
        inlast: bool = False,
    ):
        formatted_message = f"{prefix or ''} {message}".strip()
        attrs = ["bold"] if bold else []

        if inline:
            # Didnt mix it in...
            cprint(f"\r{formatted_message}", color, attrs=attrs, end=" ", flush=flush)
            if inlast:
                print(" " * 5)
        else:
            cprint(formatted_message, color, attrs=attrs, flush=flush)

    def success(self, message, bold: bool = False, inline=False, prefix="[*]"):
        self.print(message, color="green", bold=bold, inline=inline, prefix=prefix)

    def warning(
        self,
        message,
        color: Optional[str] = "yellow",
        bold: bool = False,
        inline=False,
    ):
        self.print(
            message,
            color=color,
            bold=bold,
            inline=inline,
            prefix="[~]",
        )

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


# Example usage
msg = MessagePrinter()
