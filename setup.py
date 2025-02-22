from setuptools import setup

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="DemodAPK",
    author="Veha Veha",
    version="1.0",
    py_modules=["autogen"],
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "demodapk = autogen:main",
        ],
    },
)
