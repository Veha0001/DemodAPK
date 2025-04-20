from setuptools import setup

with open("requirements.txt", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="DemodAPK",
    author="Veha Veha",
    version="1.1.2",
    py_modules=["src.autogen"],
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "demodapk = src.autogen:main",
        ],
    },
)
