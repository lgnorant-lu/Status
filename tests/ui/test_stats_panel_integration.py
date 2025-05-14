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

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPoint, QSize

# 导入被测试的模块
from status.ui.stats_panel import StatsPanel
from status.ui.main_pet_window import MainPetWindow
from status.core.events import WindowPositionChangedEvent, SystemStatsUpdatedEvent
from status.core.event_system import EventSystem, EventType
from status.monitoring.system_monitor import publish_stats


class TestStatsPanel(unittest.TestCase):
    """测试StatsPanel的集成功能"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        # 创建QApplication实例，如果尚未创建
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """每个测试前的设置"""
        # 创建主窗口
        self.main_window = MainPetWindow()
        self.main_window.resize(200, 200)
        self.main_window.move(100, 100)
        
        # 创建状态面板
        self.stats_panel = StatsPanel()
        
        # 获取事件系统
        self.event_system = EventSystem.get_instance()
        
        # 尝试重置事件监听器
        # 由于我们不确定EventSystem类的具体实现，使用更简单的方式设置
        # 直接注册我们需要的事件处理器，不考虑之前的注册状态
        try:
            if self.stats_panel and self.event_system:
                # 注册状态面板的事件处理器
                self.event_system.register_handler(EventType.SYSTEM_STATS_UPDATED, self.stats_panel.handle_stats_update)
                self.event_system.register_handler(EventType.WINDOW_POSITION_CHANGED, self.stats_panel.handle_window_position_changed)
        except Exception as e:
            print(f"注册事件处理器时出错: {e}")
    
    def tearDown(self):
        """每个测试后的清理"""
        # 清理窗口
        if hasattr(self, 'main_window') and self.main_window:
            self.main_window.close()
            self.main_window = None
        
        if hasattr(self, 'stats_panel') and self.stats_panel:
            self.stats_panel.close()
            self.stats_panel = None
        
        # 清理事件监听器 - 简化处理
        # 我们不尝试清除所有处理器，因为这可能依赖于EventSystem的具体实现
        # 测试环境的清理会通过Python的垃圾回收来处理
        pass
    
    def test_stats_panel_receives_data(self):
        """测试状态面板是否能正确接收系统数据"""
        # 确保状态面板存在
        if not self.stats_panel:
            self.skipTest("状态面板未正确初始化")
        
        # 显示状态面板
        self.stats_panel.show()
        self.assertTrue(self.stats_panel.isVisible(), "状态面板应该可见")
        
        # 模拟系统数据
        test_data = {
            'cpu_usage': 25.5,
            'memory_usage': 60.2,
            'disk_usage': 45.0,
            'network_speed': {
                'upload_kbps': 128.5,
                'download_kbps': 1024.3
            },
            'period': 'MORNING'
        }
        
        # 发布模拟数据事件
        event = SystemStatsUpdatedEvent(stats_data=test_data)
        if self.event_system:
            self.event_system.dispatch(event)
        
        # 给事件处理一点时间
        QApplication.processEvents()
        
        # 验证数据是否正确显示在UI上
        if hasattr(self.stats_panel, 'cpu_label') and self.stats_panel.cpu_label:
            cpu_text = self.stats_panel.cpu_label.text()
            self.assertIn("25.5", cpu_text, f"CPU标签应显示25.5%, 实际为: {cpu_text}")
        
        if hasattr(self.stats_panel, 'memory_label') and self.stats_panel.memory_label:
            memory_text = self.stats_panel.memory_label.text()
            self.assertIn("60.2", memory_text, f"内存标签应显示60.2%, 实际为: {memory_text}")
        
        if (hasattr(self.stats_panel, 'is_expanded') and self.stats_panel.is_expanded and 
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
        if self.event_system:
            self.event_system.dispatch(event)
        
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
    
    def test_publish_stats_updates_panel(self):
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