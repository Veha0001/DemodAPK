from demodapk.utils import show_logo
from demodapk.mods import runsteps

try:
    from colorama import init

    init(autoreset=True)
except ImportError:
    pass


def main():
    show_logo("DemodAPK")
    runsteps()


if __name__ == "__main__":
    main()
