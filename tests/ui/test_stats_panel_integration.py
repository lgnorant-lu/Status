"""
---------------------------------------------------------------
File name:                  test_stats_panel_integration.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                测试状态面板与主窗口的集成，数据传递和位置绑定
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

import unittest
import sys
import os
import time
from unittest.mock import MagicMock, patch

# 添加项目根目录到系统路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt, QPoint, QSize, QTimer, QCoreApplication
from PySide6.QtTest import QTest
import logging

# 导入被测试的模块
from status.ui.stats_panel import StatsPanel
from status.ui.main_pet_window import MainPetWindow
from status.core.events import WindowPositionChangedEvent, SystemStatsUpdatedEvent
from status.core.event_system import EventSystem, EventType
from status.monitoring.system_monitor import publish_stats

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(funcName)s - %(message)s')
logger = logging.getLogger("TestStatsPanelIntegration")

# QApplication instance management
_app: QCoreApplication | None = None

def get_qapp():
    global _app
    _app = QApplication.instance()
    if _app is None:
        _app = QApplication([])
    return _app

class TestStatsPanel(unittest.TestCase):
    """测试StatsPanel的集成功能"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        cls.app = get_qapp()
    
    def setUp(self):
        """每个测试前的设置"""
        # 创建主窗口
        self.main_window = MainPetWindow()
        self.main_window.resize(200, 200)
        self.main_window.move(100, 100)
        
        # 创建状态面板
        self.stats_panel = StatsPanel(parent=self.main_window)
        
        # 获取事件系统
        self.event_system = EventSystem.get_instance()
        
        # 显示状态面板
        self.stats_panel.show()
        self.stats_panel.toggle_expand_collapse()
        self.app.processEvents()
    
    def tearDown(self):
        """每个测试后的清理"""
        # 清理窗口
        if hasattr(self, 'main_window') and self.main_window:
            self.main_window.close()
        
        if hasattr(self, 'stats_panel') and self.stats_panel:
            self.stats_panel.close()
        
        # 清理事件监听器 - 简化处理
        # 我们不尝试清除所有处理器，因为这可能依赖于EventSystem的具体实现
        # 测试环境的清理会通过Python的垃圾回收来处理
        self.app.processEvents()
        pass
    
    @patch('status.ui.stats_panel.QTimer.singleShot')
    def test_stats_panel_receives_data(self, mock_single_shot: MagicMock):
        """测试状态面板是否能正确接收系统数据"""
        # 确保状态面板存在
        if not self.stats_panel:
            self.skipTest("状态面板未正确初始化")
        
        # 确保面板已展开以显示详细信息
        if not self.stats_panel.is_expanded:
            logger.debug("Panel was not expanded, expanding now.")
            self.stats_panel.toggle_expand_collapse()
            self.app.processEvents()
            self.assertTrue(self.stats_panel.is_expanded, "Panel did not expand for test")
        
        # 模拟系统数据
        test_data = {
            'cpu': 25.5, # Changed key to match what update_data expects based on StatsPanel unit tests
            'memory': 60.2, # Changed key
            # 'disk_usage': 45.0, # disk key is different in StatsPanel
            'network_speed': {
                'upload_kbps': 128.5,
                'download_kbps': 1024.3
            },
            'period': 'MORNING'
        }
        
        # 发布模拟数据事件 using OldEvent for the old EventSystem
        # Event is imported as 'from status.core.event_system import Event'
        # REMOVED: old_event = Event(EventType.SYSTEM_STATS_UPDATED, data=test_data) # Use OldEvent
        
        # This test was intended to check if panel receives data when an event is sent via the old EventSystem
        # because the test's setUp used to register panel's handler to it.
        # However, StatsPanel now self-registers to the adapter. 
        # To properly test the adapter path for this kind of direct data, we should use the adapter.
        # For now, let's see if sending to the adapter works as it would be the primary path.
        # self.stats_panel.event_manager.dispatch_event(EventType.SYSTEM_STATS_UPDATED, data=test_data)
        # The above uses adapter.dispatch_event -> adapter.dispatch -> adv_event_data[_data_] should be test_data

        # Let's use the adapter's emit, similar to how SystemMonitor would, but with raw data for simplicity if adapter handles it.
        # The adapter's emit expects event_data to either be raw data or an OldEvent instance.
        # If we pass raw test_data: emit will wrap it in OldEvent(type, sender, data=test_data)
        # then actual_event_to_send.data is test_data.
        # Then payload_for_new_em[_data_] will be test_data.
        # Then _create_adapted_handler gets actual_data as test_data.
        # Then legacy_event.data is test_data. This looks correct.
        self.stats_panel.event_manager.emit(EventType.SYSTEM_STATS_UPDATED, event_data=test_data)

        # if self.event_system: # This was for the old system, which might not be relevant if panel only uses adapter
        #     self.event_system.dispatch(old_event)
        
        # 给事件处理一点时间
        QApplication.processEvents()
        
        # 验证数据是否正确显示在UI上
        if hasattr(self.stats_panel, 'cpu_label') and self.stats_panel.cpu_label:
            cpu_text = self.stats_panel.cpu_label.text()
            self.assertIn("25.5", cpu_text, f"CPU标签应显示25.5%, 实际为: {cpu_text}")
        
        if hasattr(self.stats_panel, 'memory_label') and self.stats_panel.memory_label:
            memory_text = self.stats_panel.memory_label.text()
            self.assertIn("60.2", memory_text, f"内存标签应显示60.2%, 实际为: {memory_text}")
        
        # Expand panel to check time_period_label if it's relevant to this test_data
        if not self.stats_panel.is_expanded:
            self.stats_panel.toggle_expand_collapse()
        QApplication.processEvents() # ensure toggle is processed

        if (self.stats_panel.is_expanded and 
            hasattr(self.stats_panel, 'time_period_label') and self.stats_panel.time_period_label):
            time_text = self.stats_panel.time_period_label.text()
            self.assertIn("MORNING", time_text, f"时间段标签应显示MORNING, 实际为: {time_text}")
    
    def test_stats_panel_position_follows_main_window(self):
        """测试状态面板位置是否跟随主窗口移动"""
        # 确保窗口存在
        if not self.main_window or not self.stats_panel:
            self.skipTest("主窗口或状态面板未正确初始化")
        
        # 显示窗口
        self.main_window.show()
        self.stats_panel.show()
        
        # 初始定位状态面板
        initial_pos = QPoint(100, 100)
        initial_size = QSize(200, 200)
        self.stats_panel.update_position(initial_pos, initial_size)
        
        # 记录初始位置
        initial_panel_pos = self.stats_panel.pos()
        
        # 移动主窗口
        new_pos = QPoint(300, 300)
        self.main_window.move(new_pos)
        
        # 发送位置变化事件
        event = WindowPositionChangedEvent(
            position=new_pos,
            size=self.main_window.size(),
            sender=self.main_window
        )
        # if self.event_system: # Old direct dispatch
        #     self.event_system.dispatch(event)
        self.stats_panel.event_manager.emit(EventType.WINDOW_POSITION_CHANGED, event) # Use adapter
        
        # 给事件处理一点时间
        QApplication.processEvents()
        
        # 检查状态面板是否也移动
        new_panel_pos = self.stats_panel.pos()
        
        # 验证状态面板位置已经改变，并且位移量与主窗口相同
        self.assertNotEqual(initial_panel_pos, new_panel_pos, "状态面板位置应该改变")
        
        # 计算相对位移
        main_window_offset = new_pos.x() - initial_pos.x()
        panel_offset = new_panel_pos.x() - initial_panel_pos.x()
        
        self.assertEqual(main_window_offset, panel_offset, 
                        f"状态面板X轴位移({panel_offset})应该与主窗口位移({main_window_offset})相同")
    
    @patch('status.ui.stats_panel.QTimer.singleShot')
    def test_publish_stats_updates_panel(self, mock_single_shot: MagicMock):
        """测试publish_stats函数是否能更新状态面板"""
        # 确保状态面板存在
        if not self.stats_panel:
            self.skipTest("状态面板未正确初始化")
        
        # 显示状态面板
        self.stats_panel.show()
        
        # 替换真实的系统指标采集函数，使用固定值
        with patch('status.monitoring.system_monitor.get_cpu_usage', return_value=33.3), \
             patch('status.monitoring.system_monitor.get_memory_usage', return_value=66.6):
            
            # 发布状态更新
            publish_stats(include_details=True)
            
            # 给事件处理一点时间
            QApplication.processEvents()
            
            # 验证面板是否更新
            if hasattr(self.stats_panel, 'cpu_label') and self.stats_panel.cpu_label:
                cpu_text = self.stats_panel.cpu_label.text()
                self.assertIn("33.3", cpu_text, f"CPU标签应显示33.3%, 实际为: {cpu_text}")
            
            if hasattr(self.stats_panel, 'memory_label') and self.stats_panel.memory_label:
                memory_text = self.stats_panel.memory_label.text()
                self.assertIn("66.6", memory_text, f"内存标签应显示66.6%, 实际为: {memory_text}")


if __name__ == '__main__':
    unittest.main() 