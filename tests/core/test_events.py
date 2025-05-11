"""
---------------------------------------------------------------
File name:                  test_events.py
Author:                     Ignorant-lu
Date created:               2025/05/12
Description:                Unit tests for status/core/event_system.py (primarily Event and EventType)
----------------------------------------------------------------

Changed history:
                            2025/05/12: Initial creation with skeleton, adapted to event_system.py definitions;
----
"""

import unittest
import sys
import os

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

# Directly import from event_system where Event and EventType are defined
from status.core.event_system import Event, EventType 

class TestCoreEventSystemEvents(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures, if any."""
        pass

    def tearDown(self):
        """Tear down test fixtures, if any."""
        pass

    def test_event_creation(self):
        """Test basic event creation and properties."""
        test_event_type = EventType.SYSTEM_ALERT # Use an actual EventType member
        event_sender = "test_sender"
        event_data = {"key": "value"}
        
        event = Event(event_type=test_event_type, sender=event_sender, data=event_data)
        
        self.assertEqual(event.type, test_event_type)
        self.assertEqual(event.sender, event_sender)
        self.assertEqual(event.data, event_data)
        self.assertFalse(event.handled) # Default handled state

    def test_event_type_enum_values(self):
        """Test the EventType enum members and their names."""
        self.assertEqual(EventType.SYSTEM_STATUS_UPDATE.name, "SYSTEM_STATUS_UPDATE")
        self.assertEqual(EventType.USER_INTERACTION.name, "USER_INTERACTION")
        # Add more checks if other specific event types are defined in EventType
        # Check if it's an Enum
        from enum import Enum
        self.assertTrue(issubclass(EventType, Enum))

    def test_event_representation(self):
        """Test the string representation of an Event."""
        event = Event(event_type=EventType.CONFIG_CHANGE, sender="config_module", data={"new_setting": True})
        event_repr = str(event) # Using str() as per __str__ method
        self.assertIn("Event(type=CONFIG_CHANGE", event_repr)
        self.assertIn("sender=config_module", event_repr)
        self.assertIn("data={'new_setting': True}", event_repr)

    def test_event_handled_property(self):
        """Test the handled property of an Event."""
        event = Event(EventType.ERROR, sender="test_component")
        self.assertFalse(event.handled)
        event.handled = True
        self.assertTrue(event.handled)

if __name__ == '__main__':
    unittest.main() 