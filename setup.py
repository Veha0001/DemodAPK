from setuptools import setup

with open("requirements.txt", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="DemodAPK",
    author="Veha Veha",
    version="1.0",
    py_modules=["demodapk.autogen"],
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "demodapk = demodapk.autogen:main",
        ],
    },
)
