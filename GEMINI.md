# DemodAPK Project Documentation (for Gemini)

This document provides an overview of the DemodAPK project, its purpose, and how to interact with it, particularly from the perspective of an automated agent like Gemini.

## Project Overview

DemodAPK is a Python-based tool designed for modifying Android Application Packages (APKs). It allows for various patching operations, including:
- Updating package names in the manifest and resources.
- Modifying application names.
- Configuring Facebook integration settings.
- Performing Smali code modifications.
- Updating build configurations.
- Managing metadata within the `AndroidManifest.xml`.

The tool aims to provide a flexible and configurable way to automate common APK modification tasks.

## Key Files and Directories

-   `demodapk/`: Contains the core Python source code for the tool.
    -   `demodapk/cli.py`: The command-line interface entry point.
    -   `demodapk/patch.py`: Contains functions for various APK patching operations.
    -   `demodapk/xmls.py`: Handles modifications to XML files, primarily `AndroidManifest.xml`.
    -   `demodapk/schema.json`: The JSON schema defining the structure and valid options for the configuration file.
-   `pyproject.toml`: Project metadata and build system configuration.
-   `requirements.txt`: Python dependencies for the project.
-   `mkdocs.yml`: Configuration for the project's documentation website.

## How to Use DemodAPK

The `demodapk` tool is executed from the command line. It requires an APK file and a configuration file (typically `config.json`) to specify the desired modifications.

**Basic Usage:**

```bash
demodapk <path_to_apk_file> --config <path_to_config.json>
```

**Example Configuration (`config.json`):**

The configuration file follows the schema defined in `demodapk/schema.json`. Here's a simplified example:

```json
{
  "DemodAPK": {
    "com.example.oldpackage": {
      "package": "com.example.newpackage",
      "app_name": "My New App",
      "manifest": {
        "hide_app_icon": true,
        "app_debuggable": true
      },
      "level": 2
    }
  }
}
```

## Implemented Features

### Hide App Icon

**Functionality:** This feature hides the application's icon from the Android launcher (app drawer and home screen). The app remains installed but is not directly launchable from the standard UI.

**Technical Implementation:** It modifies the `AndroidManifest.xml` by changing the `android:name` attribute of the `<category>` tag from `android.intent.category.LAUNCHER` to `android.intent.category.DEFAULT` within any `<intent-filter>` that also contains `android.intent.action.MAIN`. This prevents the Android system from recognizing the activity as a launcher entry point.

**Configuration:** To enable this feature, set `"hide_app_icon": true` within the `"manifest"` section of your app's configuration in the JSON file.

## Development Guidelines for Gemini

-   **Adhere to `demodapk/schema.json`:** When generating or modifying configuration files, always ensure they conform to the defined schema.
-   **XML Modifications:** Use `xml.etree.ElementTree` for `AndroidManifest.xml` modifications, following existing patterns in `demodapk/xmls.py`.
-   **Messaging:** Maintain consistency with the `demodapk.utils.msg` module for all output messages.
-   **Code Quality (Pylint):** Run `pylint .` to ensure code quality and aim to maintain a high score (e.g., 9.0 or above).
-   **Testing:** When adding new features, consider adding corresponding tests to ensure functionality and prevent regressions.

## Building Executables with PyInstaller

To create a standalone executable for DemodAPK using PyInstaller, you can use a `.spec` file to define the build process. This file gives you more control over the build process and ensures that all necessary dependencies and data files are included.

### 1. Install PyInstaller

If you don't have PyInstaller installed, you can install it using pip:

```bash
pip install pyinstaller
```

### 2. Create a `.spec` file

You can generate a basic `.spec` file using `pyi-makespec` or create one manually. For this project, create a file named `demodapk.spec` in the project root.

Here is a well-commented `demodapk.spec` file that you can use as a template:

```python
# -*- mode: python ; coding: utf-8 -*-

# This is a PyInstaller spec file. For more information, see:
# https://pyinstaller.readthedocs.io/en/stable/spec-files.html

from PyInstaller.building.api import EXE, PYZ
from PyInstaller.building.build_main import Analysis
from PyInstaller.utils.hooks import collect_data_files

# Collect data files from the 'demodapk' package.
# This ensures that non-python files like 'schema.json' are included.
datas = collect_data_files('demodapk', include_py_files=False)


a = Analysis(
    ['demodapk/__main__.py'],  # The main entry point of the application.
    pathex=[],  # A list of paths to search for modules.
    binaries=[],  # A list of non-python modules to include.
    datas=datas,  # Data files to be included in the application.
    hiddenimports=[
        # A list of modules to include that are not automatically detected.
        # e.g., 'pkg_resources.py2_warn'
    ],
    hookspath=[],  # A list of paths to search for hooks.
    hooksconfig={},
    runtime_hooks=[],  # A list of hooks to execute at runtime.
    excludes=[],  # A list of modules to exclude from the build.
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='demodapk',  # The name of the executable.
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Use UPX to compress the executable if available.
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # This is a console application.
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

### 3. Build the Executable

Once you have the `demodapk.spec` file, navigate to the project's root directory in your terminal and run PyInstaller:

```bash
pyinstaller demodapk.spec
```

This command will process the `.spec` file and generate a `dist/` directory containing the standalone `demodapk` executable.

### Customizing the Build

-   **Hidden Imports**: If you encounter `ModuleNotFound` errors when running the executable, you may need to add the missing modules to the `hiddenimports` list in the `Analysis` section of the `.spec` file.
-   **Data Files**: If your application needs to access data files (like `.json`, `.txt`, images, etc.), make sure they are included in the `datas` section. The `collect_data_files` function is a convenient way to include all non-python files from a package.
-   **One-File vs. One-Dir**: The default output is a one-directory bundle. If you want to create a single executable file, you can use the `--onefile` option with `pyinstaller`. You can also change this in the `.spec` file.
