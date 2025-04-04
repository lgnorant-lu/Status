"""
---------------------------------------------------------------
File name:                  test_monitor.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                系统监控器主类测试
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import unittest
import time
from unittest.mock import Mock, patch, MagicMock

from status.monitoring.monitor import SystemMonitor
from status.monitoring.system_info import SystemInfo
from status.monitoring.data_process import DataProcessor
from status.monitoring.ui_controller import MonitorUIController
from status.core.event_system import EventType


class TestSystemMonitor(unittest.TestCase):
    """测试系统监控器主类"""
    
    def setUp(self):
        """测试前准备"""
        # 重置单例
        SystemMonitor._instance = None
        
        # 打补丁各个模块
        self.mock_system_info = Mock(spec=SystemInfo)
        self.mock_data_processor = Mock(spec=DataProcessor)
        self.mock_ui_controller = Mock(spec=MonitorUIController)
        
        # 创建测试实例
        with patch('status.monitoring.monitor.SystemInfo', return_value=self.mock_system_info), \
             patch('status.monitoring.monitor.DataProcessor', return_value=self.mock_data_processor), \
             patch('status.monitoring.monitor.MonitorUIController', return_value=self.mock_ui_controller):
            self.monitor = SystemMonitor(update_interval=2.0)
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        # 创建两个实例
        instance1 = SystemMonitor()
        instance2 = SystemMonitor()
        
        # 验证它们是相同的实例
        self.assertIs(instance1, instance2)
    
    def test_init(self):
        """测试初始化"""
        # 验证属性
        self.assertEqual(self.monitor.update_interval, 2.0)
        self.assertFalse(self.monitor.is_running)
        
        # 验证依赖模块
        self.assertIs(self.monitor.system_info, self.mock_system_info)
        self.assertIs(self.monitor.data_processor, self.mock_data_processor)
        self.assertIs(self.monitor.ui_controller, self.mock_ui_controller)
    
    def test_start_stop(self):
        """测试启动和停止监控"""
        # 设置mock返回值
        self.mock_system_info.start_auto_update.return_value = True
        self.mock_system_info.stop_auto_update.return_value = True
        
        # 打补丁事件发送方法
        self.monitor._send_monitor_event = Mock()
        
        # 启动监控
        result = self.monitor.start()
        self.assertTrue(result)
        self.assertTrue(self.monitor.is_running)
        self.mock_system_info.start_auto_update.assert_called_once()
        self.monitor._send_monitor_event.assert_called_once_with("start")
        
        # 再次启动应该返回False
        result = self.monitor.start()
        self.assertFalse(result)
        
        # 停止监控
        result = self.monitor.stop()
        self.assertTrue(result)
        self.assertFalse(self.monitor.is_running)
        self.mock_system_info.stop_auto_update.assert_called_once()
        self.monitor._send_monitor_event.assert_called_with("stop")
        
        # 再次停止应该返回False
        result = self.monitor.stop()
        self.assertFalse(result)
        
        # 测试启动失败
        self.mock_system_info.start_auto_update.return_value = False
        result = self.monitor.start()
        self.assertFalse(result)
        self.assertFalse(self.monitor.is_running)
        
        # 测试停止失败
        self.monitor.is_running = True  # 手动设置为运行状态
        self.mock_system_info.stop_auto_update.return_value = False
        result = self.monitor.stop()
        self.assertFalse(result)
        self.assertTrue(self.monitor.is_running)  # 应该保持运行状态
    
    def test_set_update_interval(self):
        """测试设置更新间隔"""
        # 调用方法
        self.monitor.set_update_interval(5.0)
        
        # 验证结果
        self.assertEqual(self.monitor.update_interval, 5.0)
        self.mock_system_info.set_update_interval.assert_called_once_with(5.0)
        
        # 测试无效值
        self.monitor.set_update_interval(0)
        self.assertEqual(self.monitor.update_interval, 5.0)  # 应该保持不变
    
    def test_get_status(self):
        """测试获取当前系统状态"""
        # 设置mock返回值
        expected_status = {"timestamp": 1000, "metrics": {"cpu": {"percent_overall": 30.0}}}
        self.mock_ui_controller.get_latest_status.return_value = expected_status
        
        # 获取状态
        status = self.monitor.get_status()
        
        # 验证结果
        self.assertEqual(status, expected_status)
        self.mock_ui_controller.get_latest_status.assert_called_once()
        
        # 测试无缓存状态的情况
        self.mock_ui_controller.get_latest_status.return_value = None
        self.mock_system_info.update_metrics.return_value = {"cpu": {"percent_overall": 30.0}}
        
        # 获取状态
        status = self.monitor.get_status()
        
        # 验证结果
        self.assertEqual(status["metrics"], {"cpu": {"percent_overall": 30.0}})
        self.assertIn("timestamp", status)
        self.mock_system_info.update_metrics.assert_called_once()
    
    def test_get_alerts(self):
        """测试获取告警历史"""
        # 设置mock返回值
        expected_alerts = [{"alert_type": "cpu_high", "message": "CPU告警"}]
        self.mock_ui_controller.get_alerts.return_value = expected_alerts
        
        # 获取告警
        alerts = self.monitor.get_alerts()
        
        # 验证结果
        self.assertEqual(alerts, expected_alerts)
        self.mock_ui_controller.get_alerts.assert_called_once_with(None)
        
        # 获取指定数量的告警
        alerts = self.monitor.get_alerts(5)
        self.mock_ui_controller.get_alerts.assert_called_with(5)
    
    def test_clear_alerts(self):
        """测试清空告警历史"""
        # 调用方法
        self.monitor.clear_alerts()
        
        # 验证结果
        self.mock_ui_controller.clear_alerts.assert_called_once()
    
    def test_threshold_management(self):
        """测试阈值管理"""
        # 设置mock返回值
        self.mock_data_processor.set_threshold.return_value = True
        self.mock_data_processor.get_threshold.return_value = 80.0
        self.mock_data_processor.get_all_thresholds.return_value = {"cpu_high": 80.0}
        
        # 设置阈值
        result = self.monitor.set_threshold("cpu_high", 80.0)
        self.assertTrue(result)
        self.mock_data_processor.set_threshold.assert_called_once_with("cpu_high", 80.0)
        
        # 获取阈值
        value = self.monitor.get_threshold("cpu_high")
        self.assertEqual(value, 80.0)
        self.mock_data_processor.get_threshold.assert_called_once_with("cpu_high")
        
        # 获取所有阈值
        thresholds = self.monitor.get_all_thresholds()
        self.assertEqual(thresholds, {"cpu_high": 80.0})
        self.mock_data_processor.get_all_thresholds.assert_called_once()
    
    def test_get_stats(self):
        """测试获取统计数据"""
        # 设置mock返回值
        expected_stats = {"cpu": {"current": 30.0}}
        self.mock_data_processor.get_stats.return_value = expected_stats
        
        # 获取统计数据
        stats = self.monitor.get_stats()
        
        # 验证结果
        self.assertEqual(stats, expected_stats)
        self.mock_data_processor.get_stats.assert_called_once()
    
    def test_get_history(self):
        """测试获取历史数据"""
        # 设置mock返回值
        expected_history = [{"percent": 20.0}, {"percent": 30.0}]
        self.mock_data_processor.get_history.return_value = expected_history
        
        # 获取历史数据
        history = self.monitor.get_history("cpu")
        
        # 验证结果
        self.assertEqual(history, expected_history)
        self.mock_data_processor.get_history.assert_called_once_with("cpu", None)
        
        # 获取指定数量的历史数据
        history = self.monitor.get_history("cpu", 5)
        self.mock_data_processor.get_history.assert_called_with("cpu", 5)
    
    def test_get_history_with_timestamps(self):
        """测试获取带时间戳的历史数据"""
        # 设置mock返回值
        expected_history = [(1000, {"percent": 20.0}), (2000, {"percent": 30.0})]
        self.mock_data_processor.get_history_with_timestamps.return_value = expected_history
        
        # 获取历史数据
        history = self.monitor.get_history_with_timestamps("cpu")
        
        # 验证结果
        self.assertEqual(history, expected_history)
        self.mock_data_processor.get_history_with_timestamps.assert_called_once_with("cpu", None)
        
        # 获取指定数量的历史数据
        history = self.monitor.get_history_with_timestamps("cpu", 5)
        self.mock_data_processor.get_history_with_timestamps.assert_called_with("cpu", 5)
    
    def test_ui_component_management(self):
        """测试UI组件管理"""
        # 设置mock返回值
        self.mock_ui_controller.register_component.return_value = True
        self.mock_ui_controller.unregister_component.return_value = True
        
        # 创建测试组件
        test_component = Mock()
        
        # 注册组件
        result = self.monitor.register_ui_component("test", test_component)
        self.assertTrue(result)
        self.mock_ui_controller.register_component.assert_called_once_with("test", test_component)
        
        # 注销组件
        result = self.monitor.unregister_ui_component("test")
        self.assertTrue(result)
        self.mock_ui_controller.unregister_component.assert_called_once_with("test")
    
    def test_custom_processor_management(self):
        """测试自定义处理器管理"""
        # 设置mock返回值
        self.mock_data_processor.register_custom_processor.return_value = True
        self.mock_data_processor.unregister_custom_processor.return_value = True
        
        # 创建测试处理器
        test_processor = Mock()
        
        # 注册处理器
        result = self.monitor.register_custom_processor("test", test_processor)
        self.assertTrue(result)
        self.mock_data_processor.register_custom_processor.assert_called_once_with("test", test_processor)
        
        # 注销处理器
        result = self.monitor.unregister_custom_processor("test")
        self.assertTrue(result)
        self.mock_data_processor.unregister_custom_processor.assert_called_once_with("test")
    
    def test_send_monitor_event(self):
        """测试发送监控事件"""
        # 打补丁事件系统
        self.monitor.event_system = Mock()
        
        # 发送事件
        self.monitor._send_monitor_event("test_action")
        
        # 验证事件分发
        self.monitor.event_system.dispatch_event.assert_called_once()
        
        # 获取分发的事件
        event = self.monitor.event_system.dispatch_event.call_args[0][0]
        self.assertEqual(event.type, EventType.SYSTEM_MONITOR_STATE)
        self.assertEqual(event.sender, "SystemMonitor")
        self.assertEqual(event.data["action"], "test_action")
        self.assertEqual(event.data["is_running"], False)
        self.assertEqual(event.data["update_interval"], 2.0)


if __name__ == '__main__':
    unittest.main() 