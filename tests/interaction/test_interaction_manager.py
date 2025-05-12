"""
---------------------------------------------------------------
File name:                  test_interaction_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                桌宠交互管理器测试
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
                            2025/05/12: 修正QApplication导入和InteractionManager获取逻辑;
----
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os
import logging # Import logging
import pytest # Add pytest import for pytestmark

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

# Simplified import, assuming PySide6 is the standard
from PySide6.QtWidgets import QApplication

from status.interaction.interaction_manager import InteractionManager
from status.core.events import EventManager
from status.interaction.hotkey import HotkeyManager

@pytest.mark.usefixtures("qapp") # Indicate pytest-qt should handle QApplication
class TestInteractionManager(unittest.TestCase):
    """测试交互管理器类"""
    
    def setUp(self):
        """每个测试前的初始化"""
        InteractionManager._instance = None # Reset singleton before each test
        self.mock_event_manager = Mock(spec=EventManager)
        self.mock_app_context = Mock()
        self.mock_app_context.event_bus = self.mock_event_manager # Ensure event_bus is on app_context
        self.mock_settings = Mock()
        
        # Get/create instance using get_instance, passing necessary args for __init__
        # Patch EventManager.get_instance as it might be called within InteractionManager's __init__ or get_instance
        with patch('status.core.config.config_manager.ConfigManager.get_instance') as mock_config_mgr, \
             patch('status.core.events.EventManager.get_instance', return_value=self.mock_event_manager): 
            # Assuming EventManager is correctly patched if used by InteractionManager directly
            # If app_context is supposed to provide EventManager, ensure mock_app_context.event_bus is set
            self.manager = InteractionManager.get_instance(app_context=self.mock_app_context, settings=self.mock_settings)

    def tearDown(self):
        """每个测试执行后的清理"""
        if hasattr(self, 'manager') and self.manager and hasattr(self.manager, '_initialized') and self.manager._initialized:
            try:
                # Attempt to shutdown, but catch errors if it fails (e.g., due to Qt state)
                self.manager.shutdown()
            except Exception as e:
                logging.warning(f"Error during InteractionManager shutdown in tearDown: {e}")
        InteractionManager._instance = None # Reset singleton
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        # self.manager is already created in setUp
        with patch('status.core.events.EventManager.get_instance', return_value=self.mock_event_manager):
            another_manager = InteractionManager.get_instance(app_context=self.mock_app_context, settings=self.mock_settings)
        self.assertIs(self.manager, another_manager)
    
    def test_direct_instantiation_after_get_instance_raises_exception(self):
        """测试在get_instance之后直接实例化会引发异常"""
        # Instance is created in setUp via get_instance
        with self.assertRaises(RuntimeError):
            InteractionManager(app_context=self.mock_app_context, settings=self.mock_settings)
    
    def test_initialize_subsystems(self):
        """测试初始化子系统 - 重点测试 HotkeyManager 部分"""
        # mock_window = Mock()
        # self.mock_app_context.get_main_window = Mock(return_value=mock_window)
        
        # mock_mouse_interaction = Mock()
        mock_hotkey_manager = Mock()
        mock_hotkey_manager.start = Mock() 
        
        # 只 Patch HotkeyManager
        with patch('status.interaction.interaction_manager.HotkeyManager', return_value=mock_hotkey_manager) as MockHotkeyMgrProvider:
            
            # 我们期望 InteractionManager.initialize() 内部会执行：
            # self.keyboard_event_handler = HotkeyManager()  (即 mock_hotkey_manager)
            # if hasattr(self.keyboard_event_handler, 'start'): self.keyboard_event_handler.start()
            
            self.manager.initialize()
        
        # 断言 HotkeyManager() 被调用以获取实例
        MockHotkeyMgrProvider.assert_called_once_with()
        
        # 断言 keyboard_event_handler 被正确赋值
        self.assertIs(self.manager.keyboard_event_handler, mock_hotkey_manager, "keyboard_event_handler should be the mocked instance")
        
        # 最关键的断言：mock_hotkey_manager 的 start 方法是否被调用
        mock_hotkey_manager.start.assert_called_once()
        
        # 也可以检查 _initialized 状态，但这取决于其他子系统是否被 mock 或真实执行
        # self.assertTrue(self.manager._initialized)

    def test_handle_interaction_event(self):
        """测试处理交互事件"""
        self.manager.mouse_event_handler = Mock()
        self.manager.keyboard_event_handler = Mock()
        
        mock_event_type = "test_event_type"
        mock_event_data = {"key": "value"}
        
        self.manager._handle_interaction_event(mock_event_type, mock_event_data)
        
        if hasattr(self.manager.mouse_event_handler, 'handle_event'):
            self.manager.mouse_event_handler.handle_event.assert_called_once_with(mock_event_type, mock_event_data)
        if hasattr(self.manager.keyboard_event_handler, 'handle_event'):
            self.manager.keyboard_event_handler.handle_event.assert_called_once_with(mock_event_type, mock_event_data)
    
    def test_shutdown(self):
        """测试关闭交互管理器"""
        self.manager._initialized = True # Assume initialized
        
        # Mock a HotkeyManager instance for keyboard_event_handler
        mock_kb_handler = Mock(spec=HotkeyManager) # Use spec for isinstance checks
        self.manager.keyboard_event_handler = mock_kb_handler
        
        self.manager.mouse_event_handler = Mock()
        self.manager.event_bus = self.mock_event_manager # Ensure correct event_bus for unregister
        
        result = self.manager.shutdown()
        
        self.assertTrue(result, "shutdown() should return True")
        self.assertFalse(self.manager._initialized, "Manager should be marked as not initialized after shutdown")
        
        if hasattr(self.manager.mouse_event_handler, 'shutdown'):
            self.manager.mouse_event_handler.shutdown.assert_called_once()
        
        # HotkeyManager has a 'stop' method that should be called by shutdown
        mock_kb_handler.stop.assert_called_once()
        
        # Ensure unregister_handler is called with the correct arguments
        self.mock_event_manager.unregister_handler.assert_called_with("interaction", self.manager._handle_interaction_event)

if __name__ == '__main__':
    unittest.main() 