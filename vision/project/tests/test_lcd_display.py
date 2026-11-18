"""Display-path tests that do not require a Raspberry Pi or an LCD."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from PIL import Image
except ImportError:  # pragma: no cover - handled by the skip below
    Image = None

from lcd_display import _rgb565_bytes


@unittest.skipUnless(Image is not None, "Pillow is required for LCD conversion tests")
class PixelFormatTests(unittest.TestCase):
    def test_rgb565_is_big_endian(self):
        image = Image.new("RGB", (3, 1))
        image.putdata([(255, 0, 0), (0, 255, 0), (0, 0, 255)])
        self.assertEqual(_rgb565_bytes(image), bytes.fromhex("f800 07e0 001f"))

    def test_rgb565_preserves_frame_size(self):
        image = Image.new("RGB", (240, 320), (255, 255, 255))
        self.assertEqual(len(_rgb565_bytes(image)), 240 * 320 * 2)


if __name__ == "__main__":
    unittest.main()
