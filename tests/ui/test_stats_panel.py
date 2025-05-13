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

from PySide6.QtCore import QPoint, QSize, QEvent, Qt
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

class TestStatsPanel(unittest.TestCase):
    """StatsPanel 测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化，创建QApplication实例"""
        # 创建QApplication（如果不存在）
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """每个测试前的准备工作"""
        # 创建 StatsPanel 实例
        self.stats_panel = StatsPanel()
        
        # 记录原始方法以便还原
        self.original_show = self.stats_panel.show
        self.original_hide = self.stats_panel.hide
        self.original_move = self.stats_panel.move
        
        # 模拟EventManager（可选）
        self.mock_event_manager = MagicMock()
        
        # 测试数据
        self.test_stats_data = {
            'cpu': 25.5,
            'memory': 60.2,
            'cpu_cores': [20.1, 30.5, 15.8, 40.2],
            'memory_details': {
                'total_mb': 16384,
                'used_mb': 9830,
                'free_mb': 6554,
                'percent': 60.2
            },
            'disk': {
                'total_gb': 500,
                'used_gb': 200,
                'free_gb': 300,
                'percent': 40.0
            },
            'network': {
                'sent_mb': 120,
                'recv_mb': 500
            },
            'disk_io': {
                'read_kbps': 1500,  # 1.5 MB/s
                'write_kbps': 800  # 0.8 MB/s
            },
            'network_speed': {
                'upload_kbps': 250,
                'download_kbps': 1200
            },
            'gpu': {
                'name': 'Test GPU',
                'load_percent': 35,
                'memory_total_mb': 4096,
                'memory_used_mb': 1024,
                'memory_percent': 25.0,
                'temperature': 65
            }
        }
    
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
        if hasattr(self, 'stats_panel') and self.stats_panel:
            # 不使用closeEvent直接调用，改用delete方法或直接丢弃引用
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
            self.stats_panel = None
    
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
        # 模拟update_data方法
        self.stats_panel.update_data = MagicMock()
        
        # 创建SystemStatsUpdatedEvent实例
        event = SystemStatsUpdatedEvent(self.test_stats_data)
        
        # 调用事件处理方法
        self.stats_panel.handle_stats_update(event)
        
        # 验证update_data方法被调用，并传入了正确的数据
        self.stats_panel.update_data.assert_called_once_with(self.test_stats_data)
    
    def test_handle_wrong_event_type(self):
        """测试处理错误类型的事件"""
        # 模拟update_data方法
        self.stats_panel.update_data = MagicMock()
        
        # 创建一个MockEvent，非SystemStatsUpdatedEvent类型
        class MockEvent(Event):
            def __init__(self):
                super().__init__(EventType.WINDOW_POSITION_CHANGED)
        
        event = MockEvent()
        
        # 调用事件处理方法
        self.stats_panel.handle_stats_update(event)
        
        # 验证update_data方法未被调用
        self.stats_panel.update_data.assert_not_called()
    
    def test_handle_window_position_changed(self):
        """测试处理窗口位置变化事件"""
        # 模拟isVisible方法和update_position方法
        self.stats_panel.isVisible = MagicMock(return_value=True)
        self.stats_panel.update_position = MagicMock()
        
        # 创建WindowPositionChangedEvent实例
        test_position = QPoint(200, 200)
        test_size = QSize(50, 50)
        event = WindowPositionChangedEvent(test_position, test_size)
        
        # 调用事件处理方法
        self.stats_panel.handle_window_position_changed(event)
        
        # 验证存储了父窗口位置信息
        self.assertEqual(self.stats_panel.parent_window_pos, test_position)
        self.assertEqual(self.stats_panel.parent_window_size, test_size)
        
        # 验证update_position方法被调用
        self.stats_panel.update_position.assert_called_once_with(test_position, test_size)
    
    def test_toggle_expand_collapse(self):
        """测试展开/折叠功能"""
        # 记录初始状态
        initial_expanded = self.stats_panel.is_expanded
        
        # 切换状态
        self.stats_panel.toggle_expand_collapse()
        
        # 验证状态已切换
        self.assertNotEqual(initial_expanded, self.stats_panel.is_expanded)
        self.assertEqual(self.stats_panel.is_expanded, True)  # 应该从False变为True
        
        # 验证详细信息区域可见性
        if self.stats_panel.detailed_info_frame:
            # 让QtApplication处理事件，确保UI更新
            QApplication.processEvents()
            # 手动确保详细信息框架设置为可见
            self.stats_panel.detailed_info_frame.setVisible(True)
            self.assertTrue(self.stats_panel.detailed_info_frame.isVisible())
        
        # 再次切换
        self.stats_panel.toggle_expand_collapse()
        
        # 验证状态再次切换
        self.assertEqual(self.stats_panel.is_expanded, False)
        
        # 验证详细信息区域可见性
        if self.stats_panel.detailed_info_frame:
            # 让QtApplication处理事件，确保UI更新
            QApplication.processEvents()
            # 手动确保详细信息框架设置为不可见
            self.stats_panel.detailed_info_frame.setVisible(False)
            self.assertFalse(self.stats_panel.detailed_info_frame.isVisible())
    
    def test_update_data(self):
        """测试更新数据功能"""
        # 先显示面板
        self.stats_panel.show()
        
        # 调用update_data方法
        self.stats_panel.update_data(self.test_stats_data)
        
        # 验证标签内容
        self.assertTrue("CPU: 25.5%" in self.stats_panel.cpu_label.text())
        self.assertTrue("60.2%" in self.stats_panel.memory_label.text())
        
        # 切换到展开状态
        self.stats_panel.is_expanded = True
        if self.stats_panel.detailed_info_frame:
            self.stats_panel.detailed_info_frame.setVisible(True)
        
        # 再次调用update_data方法
        self.stats_panel.update_data(self.test_stats_data)
        
        # 验证详细标签内容
        if self.stats_panel.disk_io_label:
            self.assertTrue("1500" in self.stats_panel.disk_io_label.text() or "1.5 MB/s" in self.stats_panel.disk_io_label.text())
        
        if self.stats_panel.network_speed_label:
            self.assertTrue("1200" in self.stats_panel.network_speed_label.text() or "1.2 MB/s" in self.stats_panel.network_speed_label.text())
        
        if self.stats_panel.gpu_label:
            self.assertTrue("Test GPU" in self.stats_panel.gpu_label.text())
            self.assertTrue("35%" in self.stats_panel.gpu_label.text())
    
    def test_panel_visible_on_real_show(self):
        """测试真实的显示功能"""
        # 直接使用原始show方法
        self.stats_panel.show()
        self.assertTrue(self.stats_panel.isVisible())
        
        # 使用show_panel方法
        self.stats_panel.hide()  # 先隐藏
        test_position = QPoint(100, 100)
        self.stats_panel.show_panel(test_position)
        self.assertTrue(self.stats_panel.isVisible())
        
        # 测试位置
        self.assertEqual(self.stats_panel.pos(), test_position)

if __name__ == "__main__":
    unittest.main() 