"""不需要摄像头、串口或 OpenCV 的回归测试。"""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config
import protocol as proto
from recognition_state import RecognitionState
from uart_link import VisionLink


class StateTests(unittest.TestCase):
    def setUp(self):
        self.state = RecognitionState()

    def confirm_sign(self, sign=proto.SIGN_LEFT, quality=60):
        for _ in range(config.SIGN_CONFIRM_FRAMES):
            self.state.update_sign(sign, quality)

    def confirm_colors(self):
        for _ in range(config.COLOR_CONFIRM_FRAMES):
            self.state.update_colors(list(proto.COLOR_CODE), True, 95)

    def test_sign_requires_consecutive_frames(self):
        self.state.update_sign(proto.SIGN_LEFT, 80)
        self.state.update_sign(proto.SIGN_NONE, 0)
        for _ in range(config.SIGN_CONFIRM_FRAMES - 1):
            self.state.update_sign(proto.SIGN_LEFT, 80)
        self.assertEqual(self.state.sign, proto.SIGN_NONE)
        self.state.update_sign(proto.SIGN_LEFT, 80)
        self.assertEqual(self.state.sign, proto.SIGN_LEFT)

    def test_lost_sign_expires(self):
        self.confirm_sign()
        for _ in range(config.SIGN_LOST_FRAMES):
            self.state.update_sign(proto.SIGN_NONE, 0)
        self.assertEqual(self.state.sign, proto.SIGN_NONE)
        self.assertEqual(self.state.sign_quality, 0)

    def test_reverse_candidate_clears_previous_direction(self):
        self.confirm_sign()
        self.state.update_sign(proto.SIGN_RIGHT, 80)
        self.assertEqual(self.state.sign, proto.SIGN_NONE)

    def test_low_quality_expires_sign(self):
        self.confirm_sign()
        for _ in range(config.SIGN_LOST_FRAMES):
            self.state.update_sign(proto.SIGN_LEFT, 0)
        self.assertEqual(self.state.sign, proto.SIGN_NONE)

    def test_colors_latch_after_confirmation(self):
        colors = list(proto.COLOR_CODE)
        self.state.update_colors(colors, True, 95)
        self.assertEqual(self.state.colors, [])
        self.confirm_colors()
        self.state.update_colors([], False, 0)
        self.assertEqual(self.state.colors, colors)
        self.state.update_colors(colors[::-1], True, 99)
        self.assertEqual(self.state.colors, colors)

    def test_duplicate_colors_rejected(self):
        for _ in range(config.COLOR_CONFIRM_FRAMES):
            self.state.update_colors(["red"] * 4, True, 100)
        self.assertEqual(self.state.colors, [])

    def test_color_quality_does_not_override_sign(self):
        self.confirm_colors()
        self.confirm_sign(quality=50)
        parsed = proto.parse_frame(self.state.pack())
        self.assertEqual(parsed["quality"], 50)
        self.assertEqual(parsed["color_seq"], 0x1B)
        self.assertTrue(parsed["checksum_ok"])

    def test_empty_frame_is_valid_heartbeat(self):
        self.assertEqual(self.state.pack(), bytes.fromhex("aa 55 00 00 00 00 00"))


class LinkTests(unittest.TestCase):
    def test_short_write_closes_link(self):
        link = VisionLink()
        port = Mock()
        port.write.return_value = 2
        link._ser = port
        self.assertFalse(link.send(b"1234567"))
        port.close.assert_called_once()
        self.assertIsNone(link._ser)
        self.assertEqual(link.failed, 1)

    def test_reconnect_is_rate_limited(self):
        link = VisionLink()
        with patch.object(link, "_open", side_effect=OSError("offline")) as opening:
            with patch("uart_link.time.monotonic", side_effect=[0.0, 0.1, 1.1]):
                for _ in range(3):
                    self.assertFalse(link.send(b"1234567"))
        self.assertEqual(opening.call_count, 2)


if __name__ == "__main__":
    unittest.main()
