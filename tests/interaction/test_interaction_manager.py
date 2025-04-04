"""
---------------------------------------------------------------
File name:                  test_interaction_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                桌宠交互管理器测试
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import unittest
from unittest.mock import Mock, patch
import sys

# 首先导入tests模块中的conftest以确保正确设置mocks
import tests.conftest

# 从自定义mocks模块导入QApplication
try:
    from tests.mocks import QApplication
except ImportError:
    # 如果不能导入，尝试从PyQt6导入
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        print("无法导入QApplication，测试将失败")
        # 定义一个替代品，以便代码能继续执行
        class QApplication:
            @staticmethod
            def instance():
                return None
            def __init__(self, argv):
                pass

from status.interaction.interaction_manager import InteractionManager
from status.core.events import EventManager


class TestInteractionManager(unittest.TestCase):
    """测试交互管理器类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        # 创建QApplication实例，用于测试
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)
    
    def setUp(self):
        """每个测试前的初始化"""
        # 清理单例实例
        InteractionManager._instance = None
        # Mock事件管理器
        self.mock_event_manager = Mock(spec=EventManager)
        with patch('status.interaction.interaction_manager.EventManager.get_instance', 
                  return_value=self.mock_event_manager):
            # 获取交互管理器实例
            self.manager = InteractionManager.get_instance()
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        # 再次获取实例，应该是同一个实例
        with patch('status.interaction.interaction_manager.EventManager.get_instance', 
                  return_value=self.mock_event_manager):
            another_manager = InteractionManager.get_instance()
        
        # 判断是否是同一个实例
        self.assertIs(self.manager, another_manager)
    
    def test_direct_instantiation_raises_exception(self):
        """测试直接实例化会引发异常"""
        # 尝试直接实例化
        with self.assertRaises(RuntimeError):
            # 不使用get_instance方法，而是直接实例化
            InteractionManager()
    
    def test_initialize_subsystems(self):
        """测试初始化子系统"""
        # 创建模拟对象
        mock_app = Mock()
        mock_window = Mock()
        
        # 模拟子系统类
        mock_mouse_interaction = Mock()
        mock_tray_icon = Mock()
        mock_context_menu = Mock()
        mock_hotkey_manager = Mock()
        mock_behavior_trigger = Mock()
        mock_drag_manager = Mock()
        
        # 使用patch装饰器模拟导入的子系统类
        with patch('status.interaction.mouse_interaction.MouseInteraction', return_value=mock_mouse_interaction), \
             patch('status.interaction.tray_icon.TrayIcon', return_value=mock_tray_icon), \
             patch('status.interaction.context_menu.ContextMenu', return_value=mock_context_menu), \
             patch('status.interaction.hotkey.HotkeyManager', return_value=mock_hotkey_manager), \
             patch('status.interaction.behavior_trigger.BehaviorTrigger', return_value=mock_behavior_trigger), \
             patch('status.interaction.drag_manager.DragManager', return_value=mock_drag_manager):
            
            # 初始化交互管理器
            result = self.manager.initialize(mock_app, mock_window)
        
        # 验证初始化是否成功
        self.assertTrue(result)
        self.assertTrue(self.manager.initialized)
        
        # 验证子系统是否正确初始化
        self.assertEqual(self.manager.mouse_interaction, mock_mouse_interaction)
        self.assertEqual(self.manager.tray_icon, mock_tray_icon)
        self.assertEqual(self.manager.context_menu, mock_context_menu)
        self.assertEqual(self.manager.hotkey_manager, mock_hotkey_manager)
        self.assertEqual(self.manager.behavior_trigger, mock_behavior_trigger)
        self.assertEqual(self.manager.drag_manager, mock_drag_manager)
    
    def test_handle_interaction_event(self):
        """测试处理交互事件"""
        # 创建模拟子系统
        mock_mouse_interaction = Mock()
        mock_tray_icon = Mock()
        mock_context_menu = Mock()
        mock_hotkey_manager = Mock()
        mock_behavior_trigger = Mock()
        mock_drag_manager = Mock()
        
        # 设置子系统
        self.manager.mouse_interaction = mock_mouse_interaction
        self.manager.tray_icon = mock_tray_icon
        self.manager.context_menu = mock_context_menu
        self.manager.hotkey_manager = mock_hotkey_manager
        self.manager.behavior_trigger = mock_behavior_trigger
        self.manager.drag_manager = mock_drag_manager
        
        # 创建模拟事件
        mock_event = Mock()
        mock_event.event_type = "test_event"
        
        # 调用处理方法
        self.manager._handle_interaction_event(mock_event)
        
        # 验证每个子系统的handle_event方法是否被调用
        mock_mouse_interaction.handle_event.assert_called_once_with(mock_event)
        mock_tray_icon.handle_event.assert_called_once_with(mock_event)
        mock_context_menu.handle_event.assert_called_once_with(mock_event)
        mock_hotkey_manager.handle_event.assert_called_once_with(mock_event)
        mock_behavior_trigger.handle_event.assert_called_once_with(mock_event)
        mock_drag_manager.handle_event.assert_called_once_with(mock_event)
    
    def test_shutdown(self):
        """测试关闭交互管理器"""
        # 创建模拟子系统
        mock_mouse_interaction = Mock()
        mock_tray_icon = Mock()
        mock_context_menu = Mock()
        mock_hotkey_manager = Mock()
        mock_behavior_trigger = Mock()
        mock_drag_manager = Mock()
        
        # 设置子系统和初始化标志
        self.manager.mouse_interaction = mock_mouse_interaction
        self.manager.tray_icon = mock_tray_icon
        self.manager.context_menu = mock_context_menu
        self.manager.hotkey_manager = mock_hotkey_manager
        self.manager.behavior_trigger = mock_behavior_trigger
        self.manager.drag_manager = mock_drag_manager
        self.manager.initialized = True
        
        # 调用关闭方法
        result = self.manager.shutdown()
        
        # 验证关闭是否成功
        self.assertTrue(result)
        self.assertFalse(self.manager.initialized)
        
        # 验证每个子系统的shutdown方法是否被调用
        mock_mouse_interaction.shutdown.assert_called_once()
        mock_tray_icon.shutdown.assert_called_once()
        mock_context_menu.shutdown.assert_called_once()
        mock_hotkey_manager.shutdown.assert_called_once()
        mock_behavior_trigger.shutdown.assert_called_once()
        mock_drag_manager.shutdown.assert_called_once()
        
        # 验证事件管理器的unregister_handler方法是否被调用
        self.mock_event_manager.unregister_handler.assert_called_once()


if __name__ == '__main__':
    unittest.main() 