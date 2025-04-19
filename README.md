# DemodAPK

**DemodAPK** is a tool for modifying and editing an **apk** that has been decoded by [APKEditor](https://github.com/REAndroid/APKEditor).

## Overview

DemodAPK is a Python-based tool designed to modify decompiled APK files. It enables developers to:

- Update Facebook App credentials (App ID, Client Token, Login Protocol Scheme).
- Rename package names in the APK manifest and associated files.
- Apply binary patches with programs like [Hexsaly](https://github.com/Veha0001/Hexsaly).

## Features

- **Commands**: Automatically decodes and builds APKs, with the ability to run commands after decoding and building.
- **Package Renaming**: Easily rename package names in APK files.
- **Resource Modification**: Modify resources in APK files as needed.
- **Facebook API Updates**: Automatically replaces Facebook App details in the appropriate XML files.
- **Metadata Adjustment**: Update application metadata in the AndroidManifest.xml file.
- **Configurable Settings**: Store and manage settings in a JSON configuration file.
- **For educational purposes**: You're learning how APK files work or exploring reverse engineering ethically.

## Requirements

- Python v3.x or higher.
- Java v8 or higher.
- Necessary libraries specified in `requirements.txt`.

## Install

```sh
pip install git+https://github.com/Veha0001/DemodAPK
```

## Usage

Run the script with the following command:

```bash
demodapk [Options] <apk_directory/apk_file> 
```

For more about options run the command with `-h`.

## Example

This is a `config.json` example file:

```json
{
  "DemodAPK": {
    "com.overpower.game": {
      "log": true,
      "dex": true,
      "command": {
        "editor_jar": "./APKEditor.jar",
        "begin": [
          { 
            "command": "hexsaly -i 0 -b=\"$DECODE/root/lib/arm64-v8a/libil2cpp.so;$DECODE/root/lib/arm64-v8a/libil2cpp.so\"",
            "present": true
          }
        ],
        "end": [
          "apksigner sign --key ./assets/keys/android.pk8 --cert ./assets/keys/android.x509.pem $BASE"
        ]
      },
      "level": 0,
      "package": "com.yes.game",
      "facebook": {
        "app_id": "0000000000000",
        "client_token": "dj2025id828018ahzl11",
        "login_protocol_scheme": "fb0000000000000"
      },
      "files": {
        "replace": {
            "patches/beta/libil2cpp_patched.so": "root/lib/arm64-v8a/libil2cpp.so"
        },
        "copy": {
            "assets/background.png": "res/drawable/background.png"
        },
        "base_move": {
            "root/lib/arm64-v8a/libreal.so": "root/lib/arm64-v8a/libfake.so"
        }
      },
      "manifest": {
        "remove_metadata": [
          "com.google.android.gms.games.APP_ID"
        ]
      }
    }
  }
```

Follow the prompts to select the APK file and modify its contents according to your preferences.
> [!NOTE]  
> `$DECODE` refers to the APK directory, and `$BASE` is the output `build.apk`.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or features.

<!--
## Acknowledgements

- Thanks to all contributors and open-source projects that made this tool possible.
-->
