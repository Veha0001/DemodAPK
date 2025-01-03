# DemoAPK

DemoAPk is a tool for modifying and editing the APK package name that has been decoded by [APKEditor](https://github.com/REAndroid/APKEditor) and includes a patcher for editing binary files.

## Overview

DemodAPK is a Python-based tool designed to modify decompiled APK files. It enables developers to:

- Update Facebook App credentials (App ID, Client Token, Login Protocol Scheme).
- Rename package names in the APK manifest and associated files.
- Apply binary patches and remove metadata.

## Features

- **Package Renaming**: Easily rename package names in APK files.
- **Resource Modification**: Modify resources in APK files as needed.
- **Facebook API Updates**: Automatically replaces Facebook App details in the appropriate XML files.
- **Metadata Adjustment**: Update application metadata in the AndroidManifest.xml file.
- **Configurable Settings**: Store and manage settings in a JSON configuration file.
- **For educational purposes**: You're learning how APK files work or exploring reverse engineering ethically.

## Requirements

- Python 3.x
- Necessary libraries specified in `requirements.txt`

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Veha0001/DemodAPK.git
   cd DemodAPK
   ```
2. Install the required libraries:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script with the following command:

```bash
python autogen.py --config <path_to_config.json> <apk_directory>
```

### Patcher

```bash
python patcher.py <config_file>
# default is config.json
```

Configuration of Patcher

```json
{
  "Patcher": {
    "input_file": "apkdir/root/lib/arm64-v8a/libil2cpp.so",
    "dump_file": "dump.cs",
    "output_file": "libil2cpp_patched.so",
    "patches": [
      {
        "method_name": "UnlockAll",
        "hex_code": "20 00 80 D2 C0 03 5F D6"
      },
      {
        "offset": "0x111111",
        "hex_code": "1F 20 03 D5"
      },
      {
        "wildcard": "AA DD F5 ?? ?? ?? 00 01",
        "hex_code": "00 E0 AF D2 C0 03 5F D6"
      }
    ]
  }
}
```

#### Performance Notice

The `patcher.py` file may work slowly when performing wildcard scans. If you want to run it faster, consider using the C++ version.

#### Building the C++ Version

To build the C++ version, you will need to have `g++` or `gcc` installed, along with the `nlohmann-json` library. You can build it using the following command:

```bash
g++ -o patcher patcher.cpp -O2
```

For **Windows** using [MSYS2](https://www.msys2.org/) First Install some package:

```bash
pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-nlohmann-json gcc
```

Then run the gcc command: `g++ patcher.cpp -o patcher.exe -O2`

> [!NOTE]
> Edit by method_name may work on some dump.cs file.
> The dump.cs file is get from [Il2CppDumper](https://github.com/Perfare/Il2CppDumper).

## Arguments

- --config: Path to the JSON configuration file (default: config.json).

- <apk_directory>: Path to the APK directory that contains the files to be modified.

## Example

Run with a custom config file.

```bash
python autogen.py --config config.json /path/to/apk/directory
```

All available example options in config.json

```json
{
  "log": 0,
  "level": 0,
  "facebook": {
    "app_id": "1234567890",
    "client_token": "aaabbbcccddd0001",
    "login_protocol_scheme": "fb1234567890"
  },
  "package": {
    "new_name": "com.app.master",
    "new_path": "Lcom/app/master"
  },
  "files": [
    {
      "replace": {
        "target": "root/lib/arm64-v8a/libil2cpp.so",
        "source": "/path/to/external/bin.so",
        "backup": true
      }
    },
    {
      "replace": {
        "target": "resources/package_1/res/values/strings.xml",
        "source": "./path/to/external/strings_new.xml"
      }
    }
  ],
  "metadata_to_remove": [
    "com.google.android.gms.games.APP_ID"
  ],
  "Patcher": {
    "input_file": "apkdir/root/lib/arm64-v8a/libil2cpp.so",
    "dump_file": "dump.cs",
    "output_file": "libil2cpp_patched.so",
    "patches": [
      {
        "method_name": "UnlockAll",
        "hex_code": "20 00 80 D2 C0 03 5F D6"
      },
      {
        "offset": "0x111111",
        "hex_code": "1F 20 03 D5"
      },
      {
        "wildcard": "AA DD F5 ?? ?? ?? 00 01",
        "hex_code": "00 E0 AF D2 C0 03 5F D6"
      }
    ]
  }
}
```

Follow the prompts to select the APK file and modify its contents according to your preferences.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or features.

<!--
## Acknowledgements

- Thanks to all contributors and open-source projects that made this tool possible.
-->
