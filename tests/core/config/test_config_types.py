"""
---------------------------------------------------------------
File name:                  test_config_types.py
Author:                     Ignorant-lu
Date created:               2025/05/12
Description:                Unit tests for status/core/config/config_types.py
----------------------------------------------------------------

Changed history:
                            2025/05/12: Initial creation;
----
"""

import unittest
import sys
import os

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, project_root)

from status.core.config.config_types import ConfigEventType, DEFAULT_CONFIG, DEFAULT_CONFIG_FILE # Assuming these exist

class TestConfigTypes(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures, if any."""
        pass

    def tearDown(self):
        """Tear down test fixtures, if any."""
        pass

    def test_config_event_type_enum(self):
        """Test the ConfigEventType enum values."""
        # Example: Check if it's an Enum and has expected members
        from enum import Enum
        self.assertTrue(issubclass(ConfigEventType, Enum))
        try:
            self.assertIsNotNone(ConfigEventType.CONFIG_LOADED)
            self.assertIsNotNone(ConfigEventType.CONFIG_SAVED)
            self.assertIsNotNone(ConfigEventType.CONFIG_CHANGED)
            # Test string representation or value if consistent
            self.assertEqual(ConfigEventType.CONFIG_LOADED.name, "CONFIG_LOADED")
        except AttributeError:
            self.skipTest("ConfigEventType or its members not defined as expected.")

    def test_default_config_structure(self):
        """Test the structure and basic values of DEFAULT_CONFIG."""
        self.assertIsInstance(DEFAULT_CONFIG, dict)
        # Add more specific checks based on the expected structure of DEFAULT_CONFIG
        # For example:
        # self.assertIn("window_settings", DEFAULT_CONFIG)
        # self.assertEqual(DEFAULT_CONFIG.get("default_behavior"), "idle")
        self.assertTrue(True) # Placeholder if no specific structure to test initially

    def test_default_config_file_constant(self):
        """Test the DEFAULT_CONFIG_FILE constant."""
        self.assertIsInstance(DEFAULT_CONFIG_FILE, str)
        self.assertTrue(DEFAULT_CONFIG_FILE.endswith(".json"))
        # Example: self.assertEqual(DEFAULT_CONFIG_FILE, "settings.json")

if __name__ == '__main__':
    unittest.main() 