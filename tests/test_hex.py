import shutil
import tempfile
from pathlib import Path

from demodapk.hex import update_bin_with_patch


def test_hex_patching():
    """
    Tests both search-and-replace and offset-based hex patching,
    including wildcard support in the replace pattern for offset patches.
    """
    # Create a dummy decoded APK structure for testing
    test_dir = tempfile.mkdtemp()
    try:
        # Setup for 'path' test
        test_file_path = Path(test_dir) / "test.bin"
        # Content: 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F
        test_file_path.write_bytes(bytes(range(16)))

        test_config = {
            "hex": [
                {
                    "path": "test.bin",
                    "verbose": True,
                    "patch": [
                        # Search and replace
                        "01 02 ?? 04 | FF EE DD CC",
                        # Offset patch with wildcard in replace
                        "0x0A | AA ?? BB",
                    ],
                },
            ]
        }
        update_bin_with_patch(test_config, test_dir)

        # Verify patches
        content = test_file_path.read_bytes()
        print(f"Patched content: {content.hex().upper()}")

        # Expected:
        # Original: 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F
        # Patch 1 (01 02 ?? 04 | FF EE DD CC):
        # Search: 01 02 03 04 (at offset 1)
        # Result: 00 FF EE DD CC 05 06 07 08 09 0A 0B 0C 0D 0E 0F
        # Patch 2 (0x0A | AA ?? BB):
        # Original byte at 0x0B is 0B
        # Result: 00 FF EE DD CC 05 06 07 08 09 AA 0B BB 0D 0E 0F
        expected_content = bytes.fromhex("00FFEEDDCC0506070809AA0BBB0D0E0F")
        assert content == expected_content, (
            f"Expected {expected_content.hex().upper()}, got {content.hex().upper()}"
        )

    finally:
        # Clean up the dummy directory
        shutil.rmtree(test_dir)
        print("Test finished and cleaned up.")
