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
    def print(self, message, **kwargs):
        color = kwargs.pop("color", None)
        bold = kwargs.pop("bold", False)
        inline = kwargs.pop("inline", False)
        prefix = kwargs.pop("prefix", None)
        inlast = kwargs.pop("inlast", False)

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
