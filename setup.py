from setuptools import setup

with open("requirements.txt", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="DemodAPK",
    author="Veha Veha",
    version="1.1.3",
    packages=["demodapk"],
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "demodapk = demodapk.cli:main",
        ],
    },
)
