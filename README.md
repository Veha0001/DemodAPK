# DemodAPK

**DemodAPK** is a tool for modifying and editing an **apk** that has been decoded by [APKEditor](https://github.com/REAndroid/APKEditor).

## Features

- Decode and build APKs with custom commands.
- Rename packages and modify resources.
- Update AndroidManifest metadata.
- Manage settings via JSON config.
- Configure Facebook App integration.
- For educational and ethical learning purposes.

### Requirements

- Python v3.x or higher.
- Java v8 or higher.
- Necessary libraries specified in `requirements.txt`.

### Install

```sh
pip install demodapk
```

#### Build from Source

Clone the repository and install manually:

```bash
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

<details> <summary>config.json</summary>

```json
{
  "DemodAPK": {
    "com.demodapk.lite": {
      "app_name": "DemodAPK"
      "apkeditor": {
          "jarpath": "~/.apkeditor/apkeditor.jar",
          "javaopts": "-Xmx8G",
          "output": "./build/DemodAPK"
          "clean": false,
          "dex": true
      },
      "commands": {
        "quietly": true,
        "begin": [
          {
            "run": "hexsaly -c beta.json open $BASE/root/lib/arm64-v8a/libil2cpp.so -i 0",
            "quiet": false
          },
          "rm -r $BASE/root/lib/armeabi-v7a",
          "./scripts/fixbluebutton.sh"
        ],
        "end": [
          {
              "run": "apksigner sign --key ./assets/keys/android.pk8 --cert ./assets/keys/android.x509.pem $BUILD",
              "title": "Signing Build"
          }
        ]
      },
      "level": 2,
      "package": "com.demodapk.hyper",
      "facebook": {
        "app_id": "2000000000001",
        "client_token": "example_client_token",
        "login_protocol_scheme": "fb2000000000001"
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

</details>

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or features.
