# DemodAPk
APK 📦, Use [APKEditor](https://github.com/REAndroid/APKEditor)
+ Setup
```bash
pip install -r ./requirement.txt
```
## autogen.py
- [x] Rename Package
- [x] Replace Libs
- [ ] [...]
## Add Config
- In config.py file:
```python
# Predefined values
## developers.facebook.com/apps
FB_APPID = ""
FB_CLIENT_TOKEN = ""
FB_LOGIN_PROTOCOL_SCHEME = ""
## Package
OLD_PACKAGE_NAME = "com.notmod.game"  # Replace with the current package name
NEW_PACKAGE_NAME = "com.mod.game"  # Replace with the desired new package name
OLD_PACKAGE_PATH = "Lcom/notmod/game"
NEW_PACKAGE_PATH = "Lcom/mod/game"
# Paths relative to the APK directory
STRINGS_FILE_RELATIVE_PATH = "resources/package_1/res/values/strings.xml"
LIB_FILE_RELATIVE_PATH = "root/lib/arm64-v8a/libil2cpp.so"
LIB_PATCH_FILE_RELATIVE_PATH = "libil2cpp_patched.so"
ANDROID_MANIFEST_FILE = "AndroidManifest.xml"
EXCLUDED_SMALI_FILES = []
```
