from setuptools import setup

setup(
    name="DemoAPK",
    version="1.0",
    py_modules=["autogen"],
    install_requires=[
        "art",
        "colorama",
        "platformdirs"
    ],
    entry_points={
        "console_scripts": [
            "demodapk = autogen:main",
        ],
    },
)
