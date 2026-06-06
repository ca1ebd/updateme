"""Tests for config defaults and time_format option."""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import Config


class TestConfigDefaults(unittest.TestCase):
    def test_time_format_default_is_24h(self):
        cfg = Config()
        self.assertEqual(cfg.time_format, "24h")

    def test_time_format_12h(self):
        cfg = Config(time_format="12h")
        self.assertEqual(cfg.time_format, "12h")

    def test_time_format_24h_explicit(self):
        cfg = Config(time_format="24h")
        self.assertEqual(cfg.time_format, "24h")


if __name__ == "__main__":
    unittest.main()
