# DemodAPk

DemoAPk is a Python-based APK modification tool designed to allow users to easily modify Android APK files with a user-friendly interface. The tool includes features such as renaming package names, modifying resources, and adjusting application metadata.

## Features

- **User-friendly Interface**: Intuitive UI for seamless operation.
- **Package Renaming**: Easily rename package names in APK files.
- **Resource Modification**: Modify resources in APK files as needed.
- **Metadata Adjustment**: Update application metadata in the AndroidManifest.xml file.
- **Configurable Settings**: Store and manage settings in a JSON configuration file.

## Requirements

- Python 3.x
- Necessary libraries specified in `requirements.txt`

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Veha0001/DemodAPk.git
   cd DemodAPk
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
- Configuration of Patcher
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
                "method_name": "0x111111",
                "hex_code": "20 25 B1"
            }
        ]
    }
}
```
> [!NOTE]
> Edit by method_name may work on some dump.cs file.
> The dump.cs file is get from [Il2CppDumper](https://github.com/Perfare/Il2CppDumper).

## Arguments
* --config: Path to the JSON configuration file (default: config.json).

* <apk_directory>: Path to the APK directory that contains the files to be modified.

## Example
```bash
python autogen.py --config config.json /path/to/apk/directory
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
