# DemodAPK

**DemodAPK** is a tool for modifying and editing an **apk** that has been decoded by [APKEditor](https://github.com/REAndroid/APKEditor).

## Features

- **Commands**: Automatically decodes and builds APKs, with the ability to run commands after decoding and building.
- **Package Renaming**: Easily rename package names in APK files.
- **Resource Modification**: Modify resources in APK files as needed.
- **Facebook API Updates**: Automatically replaces Facebook App details in the appropriate XML files.
- **Metadata Adjustment**: Update application metadata in the AndroidManifest.xml file.
- **Configurable Settings**: Store and manage settings in a JSON configuration file.
- **For educational purposes**: You're learning how APK files work or exploring reverse engineering ethically.

### Requirements

- Python v3.x or higher.
- Java v8 or higher.
- Necessary libraries specified in `requirements.txt`.

### Install

```sh
pip install git+https://github.com/Veha0001/DemodAPK
```

#### Build from Source

Clone the repository and install manually:

```sh
git clone https://github.com/Veha0001/DemodAPK.git
cd DemodAPK
# Run git fetch and git pull for latest change.
pip install .
```

### Usage

Run the script with the following command:

```bash
demodapk [Options] <apkdir_decoded/apk_file>
```

For more about options run the command with `-h`.

### Example

<details> <summary>This is a `config.json` example file: </summary>

```json
{
  "DemodAPK": {
    "com.overpower.game": {
      "app_name": "OMYRPG"
      "apkeditor": {
          "jarpath": "~/.apkeditor/apkeditor.jar",
          "javaopts": "-Xmx8G",
          "output": "omyrpg"
          "dex": true
      },
      "log": true,
      "commands": {
        "quietly": true,
        "begin": [
          {
            "run": "hexsaly -c beta.json open $BASE/root/lib/arm64-v8a/libil2cpp.so -i 0",
            "quiet": false
          },
          "rm -r $BASE/root/lib/armeabi-v7a"
        ],
        "end": [
          {
              "run": "apksigner sign --key ./assets/keys/android.pk8 --cert ./assets/keys/android.x509.pem $BUILD",
              "title": "Signing Build"
          }
        ]
      },
      "level": 0,
        "package": "com.super.gamerpg",
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

<!-- "files" feature is useless now when you use to run commands -->

Follow the prompts to select the APK file and modify its contents according to your preferences.

</details>

> [!TIP]  
> `$BASE`: decode apk_dir
>
> `$BUILD`: output apk_file

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or features.
