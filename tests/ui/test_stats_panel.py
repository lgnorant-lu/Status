"""
---------------------------------------------------------------
File name:                  test_stats_panel.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                StatsPanel 单元测试
----------------------------------------------------------------

Changed history:            
                            2025/05/13: 初始创建;
----
"""

import sys
import os
import unittest
import logging
from unittest.mock import MagicMock, patch
from typing import Optional, Callable

from PySide6.QtCore import QPoint, QSize, QEvent, Qt, QCoreApplication
from PySide6.QtWidgets import QApplication

# 将项目根目录添加到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# 导入被测组件
from status.ui.stats_panel import StatsPanel
from status.core.event_system import EventType, Event
from status.core.events import SystemStatsUpdatedEvent, WindowPositionChangedEvent, EventManager

# 配置日志
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("TestStatsPanel")

# QApplication instance management
_app: Optional[QCoreApplication] = None

def get_qapp_for_tests():
    global _app
    if _app is None:
        _app = QApplication.instance()
        if _app is None:
            _app = QApplication(sys.argv)
    return _app

class TestStatsPanel(unittest.TestCase):
    """StatsPanel 测试类"""
    stats_panel: StatsPanel
    app: Optional[QApplication] = None
    test_stats_data_dict: dict
    test_stats_data_dict_for_mocking: dict
    original_update_data: Optional[Callable] = None
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化，创建QApplication实例"""
        get_qapp_for_tests()
    
    def setUp(self):
        """每个测试前的准备工作"""
        self.stats_panel = StatsPanel()
        
        # 记录原始方法以便还原
        self.original_show = self.stats_panel.show
        self.original_hide = self.stats_panel.hide
        self.original_move = self.stats_panel.move
        
        # 模拟EventManager（可选）
        self.mock_event_manager = MagicMock()
        
        # 修改: self.test_stats_data_dict_for_mocking is now a general dict for other tests
        # that might rely on update_data being mocked (e.g. handle_stats_update)
        self.test_stats_data_dict_for_mocking = {'cpu': 50.0, 'memory': 60.0, 'period': 'DAY'}
        
        # Store the original update_data method
        self.original_update_data = self.stats_panel.update_data
        # Mock update_data for tests that specifically test event handlers, not the update_data logic itself
        self.stats_panel.update_data = MagicMock()
    
    def tearDown(self):
        """每个测试后的清理工作"""
        # 恢复原始方法
        if hasattr(self, 'original_show'):
            self.stats_panel.show = self.original_show
        if hasattr(self, 'original_hide'):
            self.stats_panel.hide = self.original_hide
        if hasattr(self, 'original_move'):
            self.stats_panel.move = self.original_move
        
        # 销毁StatsPanel实例
        if self.stats_panel:
            if hasattr(self, 'original_update_data') and self.original_update_data is not None:
                self.stats_panel.update_data = self.original_update_data
            if hasattr(self.stats_panel, 'event_manager') and self.stats_panel.event_manager:
                try:
                    # 直接调用注销方法
                    self.stats_panel.event_manager.unregister_handler(EventType.SYSTEM_STATS_UPDATED, self.stats_panel.handle_stats_update)
                    self.stats_panel.event_manager.unregister_handler(EventType.WINDOW_POSITION_CHANGED, self.stats_panel.handle_window_position_changed)
                except Exception as e:
                    logger.error(f"注销 StatsPanel 事件处理器时出错: {e}")
            
            # 使用deleteLater而不是直接调用closeEvent
            self.stats_panel.hide()
            self.stats_panel.deleteLater()
            self.stats_panel = None # type: ignore[assignment]
        QApplication.processEvents()
    
    def test_init(self):
        """测试StatsPanel初始化"""
        # 验证StatsPanel正确初始化
        self.assertIsNotNone(self.stats_panel)
        self.assertFalse(self.stats_panel.isVisible())  # 默认隐藏
        self.assertFalse(self.stats_panel.is_expanded)  # 默认折叠状态
    
    def test_show_panel(self):
        """测试显示面板功能"""
        # 模拟show和move方法
        self.stats_panel.show = MagicMock()
        self.stats_panel.move = MagicMock()
        
        # 调用show_panel方法
        test_position = QPoint(100, 100)
        self.stats_panel.show_panel(test_position)
        
        # 验证show和move方法被调用
        self.stats_panel.move.assert_called_once_with(test_position)
        self.stats_panel.show.assert_called_once()
    
    def test_hide_panel(self):
        """测试隐藏面板功能"""
        # 模拟hide方法
        self.stats_panel.hide = MagicMock()
        
        # 调用hide_panel方法
        self.stats_panel.hide_panel()
        
        # 验证hide方法被调用
        self.stats_panel.hide.assert_called_once()
    
    def test_handle_stats_update(self):
        """测试处理系统统计更新事件"""
        # Use the renamed dictionary meant for when update_data is mocked
        old_event_with_dict_data = Event(EventType.SYSTEM_STATS_UPDATED, data=self.test_stats_data_dict_for_mocking)
        
        # For debugging:
        print(f"[TestHandleStatsUpdate] Event type: {old_event_with_dict_data.type}, Event data: {old_event_with_dict_data.data}, Event data type: {type(old_event_with_dict_data.data)}")
        
        self.stats_panel.handle_stats_update(old_event_with_dict_data)
        # Assert that the mocked update_data was called with the correct data
        self.stats_panel.update_data.assert_called_once_with(self.test_stats_data_dict_for_mocking)
    
    def test_handle_wrong_event_type(self):
        """测试处理错误类型的事件"""
        # Create an event of a different type
        wrong_event = Event(EventType.WINDOW_POSITION_CHANGED, data={}) 
        self.stats_panel.handle_stats_update(wrong_event)
        self.stats_panel.update_data.assert_not_called()
    
    def test_handle_window_position_changed(self):
        """测试处理窗口位置变化事件"""
        test_position = QPoint(200, 200)
        test_size = QSize(50, 50)
        
        new_event_as_data = WindowPositionChangedEvent(position=test_position, size=test_size, sender=self.stats_panel)
        old_event_wrapping_new = Event(EventType.WINDOW_POSITION_CHANGED, data=new_event_as_data)

        print(f"[TestHandleWindowPosChanged] Event type: {old_event_wrapping_new.type}, Event data: {old_event_wrapping_new.data}, Event data type: {type(old_event_wrapping_new.data)}")
        
        self.stats_panel.handle_window_position_changed(old_event_wrapping_new)
        
        self.assertEqual(self.stats_panel.parent_window_pos, test_position)
        self.assertEqual(self.stats_panel.parent_window_size, test_size)
    
    def test_toggle_expand_collapse(self):
        """测试展开/折叠功能"""
        # 确保面板可见以正确测试子控件的可见性
        self.stats_panel.show()
        QApplication.processEvents() # Allow show event to be processed

        # 记录初始状态
        initial_expanded = self.stats_panel.is_expanded
        self.assertFalse(initial_expanded, "Initial state should be collapsed")
        
        if self.stats_panel.detailed_info_frame:
            self.assertFalse(self.stats_panel.detailed_info_frame.isVisible(), 
                             "Detailed info frame should be initially invisible")

        # 切换状态 (第一次切换：折叠 -> 展开)
        self.stats_panel.toggle_expand_collapse()
        QApplication.processEvents()
        
        # 验证状态已切换
        self.assertNotEqual(initial_expanded, self.stats_panel.is_expanded)
        self.assertTrue(self.stats_panel.is_expanded, "State should be expanded after first toggle")
        
        # 验证详细信息区域可见性
        if self.stats_panel.detailed_info_frame:
            self.assertTrue(self.stats_panel.detailed_info_frame.isVisible(),
                            "Detailed info frame should be visible after expanding")
        
        # 再次切换 (第二次切换：展开 -> 折叠)
        self.stats_panel.toggle_expand_collapse()
        QApplication.processEvents()
        
        # 验证状态再次切换
        self.assertFalse(self.stats_panel.is_expanded, "State should be collapsed after second toggle")
        
        # 验证详细信息区域可见性
        if self.stats_panel.detailed_info_frame:
            self.assertFalse(self.stats_panel.detailed_info_frame.isVisible(),
                             "Detailed info frame should be invisible after collapsing")
    
    @patch('status.ui.stats_panel.QTimer.singleShot') 
    def test_update_data(self, mock_single_shot: MagicMock):
        """测试更新数据功能"""
        # Restore the original update_data method for this specific test
        if self.original_update_data is not None:
            self.stats_panel.update_data = self.original_update_data
        else:
            # Fallback or error if original_update_data was not captured
            # This case should ideally not happen if setUp ran correctly
            pass

        self.stats_panel.show()
        QApplication.processEvents()

        # Define comprehensive test data for this test
        detailed_test_data = {
            'cpu': 25.5,  # For "CPU: 25.5%"
            'memory': 60.2, # For "内存: 60.2%"
            'cpu_cores': [20.1, 30.5, 15.0], # For "CPU 核心: 20.1%, 30.5%, 15.0%"
            'memory_details': {'total_mb': 8192, 'available_mb': 4096, 'used_mb': 3072},
            'disk': [{'mountpoint': 'C:', 'used_gb': 100, 'total_gb': 200, 'percent': 50.0}],
            'network': {'sent_mb': 1024, 'recv_mb': 2048},
            'disk_io': {'read_kbps': 1536.0, 'write_kbps': 800.0}, # read: 1.5 MB/s, write: 800.0 KB/s
            'network_speed': {'upload_kbps': 512, 'download_kbps': 2048},
            'gpu': [{'name': 'GPU 0', 'load': 45.5, 'memory_used_mb': 1024, 'memory_total_mb': 2048}],
            'period': 'DAY',
            'special_date': 'None',
            'upcoming_dates': 'None'
        }

        self.stats_panel.update_data(detailed_test_data)
        QApplication.processEvents()

        actual_cpu_text = self.stats_panel.cpu_label.text()
        self.assertEqual("CPU: 25.5%", actual_cpu_text, f"CPU text expected 'CPU: 25.5%', got '{actual_cpu_text}'")
        actual_memory_text = self.stats_panel.memory_label.text()
        self.assertEqual("内存: 60.2%", actual_memory_text, f"Memory text expected '内存: 60.2%', got '{actual_memory_text}'")
        
        # Expand panel to test detailed info update
        if not self.stats_panel.is_expanded:
            self.stats_panel.toggle_expand_collapse() # Use the method to expand
        self.assertTrue(self.stats_panel.is_expanded, "Panel should be expanded before updating detailed info")
        QApplication.processEvents()
        
        print(f"DEBUG_TEST_EXPAND: About to call update_data for details. self.stats_panel.is_expanded = {self.stats_panel.is_expanded}")
        self.stats_panel.update_data(detailed_test_data) # Call again to ensure detailed info is updated if panel was just expanded
        QApplication.processEvents()

        # Check CPU Cores
        if self.stats_panel.cpu_cores_label:
            expected_cpu_cores_text = "CPU 核心: 20.1%, 30.5%, 15.0%"
            actual_cpu_cores_text = self.stats_panel.cpu_cores_label.text()
            self.assertEqual(expected_cpu_cores_text, actual_cpu_cores_text,
                             f"CPU Cores text expected '{expected_cpu_cores_text}', got '{actual_cpu_cores_text}'")
        else:
            self.fail("cpu_cores_label was not initialized in StatsPanel UI or test setup did not make panel visible for it to be created")

        # Check Disk IO
        if self.stats_panel.disk_io_label:
            # From data: read_kbps: 1536.0 (1.5 MB/s), write_kbps: 800.0 (800.0 KB/s)
            # Expected format: f"磁盘读写: 读 {read_speed_str}, 写 {write_speed_str}"
            expected_disk_io_text = "磁盘读写: 读 1.5 MB/s, 写 800.0 KB/s"
            actual_disk_io_text = self.stats_panel.disk_io_label.text()
            self.assertEqual(expected_disk_io_text, actual_disk_io_text,
                             f"磁盘IO文本应为 '{expected_disk_io_text}', 实际为 '{actual_disk_io_text}'")
        else:
            self.fail("disk_io_label was not initialized in StatsPanel UI or test setup did not make panel visible for it to be created")

if __name__ == "__main__":
    unittest.main() 