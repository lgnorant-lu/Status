"""
---------------------------------------------------------------
File name:                  test_app_features.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                测试 StatusPet 应用层面的特性集成
----------------------------------------------------------------
"""

import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock PySide6 在测试环境中不可用或不需要GUI的部分
# 注意：如果测试需要真实的Qt事件循环，则不能完全Mock QApplication
# 但对于这里的逻辑测试，我们可以模拟它
mock_qapplication = MagicMock()
sys.modules['PySide6.QtWidgets'] = MagicMock()
sys.modules['PySide6.QtWidgets'].QApplication = mock_qapplication
sys.modules['PySide6.QtGui'] = MagicMock()
# 不再完全模拟 QtCore，以便使用真实的 Qt 枚举和可能的 QObject
# sys.modules['PySide6.QtCore'] = MagicMock()
# sys.modules['PySide6.QtCore'].Qt = MagicMock() 
# sys.modules['PySide6.QtCore'].QTimer = MagicMock()
# sys.modules['PySide6.QtCore'].QPoint = MagicMock()

# 导入真实的 QtCore
from PySide6.QtCore import Qt # 导入真实的 Qt

# 在Mock之后导入被测试的类
from status.main import StatusPet
from status.ui.main_pet_window import MainPetWindow # 尽管mock了QtWidgets，但可能仍需导入类本身用于isinstance等
from status.ui.system_tray import SystemTrayManager

class TestAppFeatures(unittest.TestCase):
    """测试 StatusPet 应用特性"""

    @patch('status.main.QApplication') # Patch QApplication to avoid real instance
    @patch('status.ui.main_pet_window.MainPetWindow') # Mock MainPetWindow
    @patch('status.ui.system_tray.SystemTrayManager') # Mock SystemTrayManager
    def setUp(self, mock_tray_cls, mock_window_cls, mock_app_init):
        """设置测试环境，模拟核心依赖"""
        self.app = StatusPet()
        # 设置模拟实例
        self.app.main_window = mock_window_cls()
        self.app.system_tray = mock_tray_cls()
        # 确保模拟窗口有 flags 属性和方法
        self.app.main_window.windowFlags = MagicMock(return_value=Qt.WindowFlags()) # Start with default flags
        self.app.main_window.setWindowFlags = MagicMock()
        self.app.main_window.show = MagicMock()
        # 确保模拟托盘有 show_message
        self.app.system_tray.show_message = MagicMock()

    def test_toggle_interaction_enables_click_through(self):
        """测试切换交互以启用鼠标穿透"""
        # 初始状态：没有 WindowTransparentForInput 标志
        initial_flags = Qt.WindowFlags() | Qt.FramelessWindowHint # 模拟一些基础标志
        self.app.main_window.windowFlags.return_value = initial_flags
        
        self.app.toggle_pet_interaction()
        
        # 断言 setWindowFlags 被调用，添加了穿透标志
        expected_flags = initial_flags | Qt.WindowTransparentForInput
        self.app.main_window.setWindowFlags.assert_called_once_with(expected_flags)
        # 断言 show 被调用
        self.app.main_window.show.assert_called_once()
        # 断言托盘消息显示"禁用"或"穿透"
        self.app.system_tray.show_message.assert_called_once()
        self.assertIn("禁用", self.app.system_tray.show_message.call_args[0][1])

    def test_toggle_interaction_disables_click_through(self):
        """测试切换交互以禁用鼠标穿透（恢复可交互）"""
        # 初始状态：包含 WindowTransparentForInput 标志
        initial_flags = Qt.WindowFlags() | Qt.FramelessWindowHint | Qt.WindowTransparentForInput
        self.app.main_window.windowFlags.return_value = initial_flags
        
        self.app.toggle_pet_interaction()
        
        # 断言 setWindowFlags 被调用，移除了穿透标志
        expected_flags = initial_flags & ~Qt.WindowTransparentForInput
        self.app.main_window.setWindowFlags.assert_called_once_with(expected_flags)
        # 断言 show 被调用
        self.app.main_window.show.assert_called_once()
        # 断言托盘消息显示"启用"或"可交互"
        self.app.system_tray.show_message.assert_called_once()
        self.assertIn("启用", self.app.system_tray.show_message.call_args[0][1])

    def test_toggle_interaction_handles_no_window(self):
        """测试在没有主窗口时切换交互不应失败"""
        self.app.main_window = None
        try:
            self.app.toggle_pet_interaction()
        except Exception as e:
            self.fail(f"toggle_pet_interaction raised an exception with no window: {e}")

    def test_toggle_interaction_handles_no_tray(self):
        """测试在没有系统托盘时切换交互不应失败（特别是消息显示）"""
        # 确保有窗口以测试窗口逻辑
        initial_flags = Qt.WindowFlags() | Qt.FramelessWindowHint
        self.app.main_window.windowFlags.return_value = initial_flags
        # 设置托盘为 None
        self.app.system_tray = None 
        try:
            self.app.toggle_pet_interaction()
            # 验证窗口逻辑仍然执行了
            expected_flags = initial_flags | Qt.WindowTransparentForInput
            self.app.main_window.setWindowFlags.assert_called_once_with(expected_flags)
            self.app.main_window.show.assert_called_once()
        except Exception as e:
            self.fail(f"toggle_pet_interaction raised an exception with no tray: {e}")


if __name__ == '__main__':
    unittest.main() 