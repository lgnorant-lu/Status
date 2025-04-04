"""
---------------------------------------------------------------
File name:                  test_data_process.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                数据处理模块测试
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import unittest
import time
import collections
from unittest.mock import Mock, patch, MagicMock

from status.core.event_system import Event, EventType
from status.monitoring.data_process import DataProcessor


class TestDataProcessor(unittest.TestCase):
    """测试数据处理类"""
    
    def setUp(self):
        """测试前准备"""
        # 重置单例
        DataProcessor._instance = None
        
        # 模拟事件系统
        self.mock_event_system = MagicMock()
        
        # 使用patch创建测试实例，确保创建的EventSystem返回我们的mock
        with patch('status.monitoring.data_process.EventSystem', return_value=self.mock_event_system):
            self.processor = DataProcessor()
        
        # 模拟事件数据
        self.test_timestamp = time.time()
        self.test_metrics = {
            "cpu": {
                "percent_overall": 30.0,
                "percent_per_cpu": [25.0, 35.0, 28.0, 32.0],
            },
            "memory": {
                "percent": 45.0,
                "total_gb": 16.0,
                "used_gb": 7.2,
            },
            "disk": {
                "partitions": [
                    {
                        "mountpoint": "C:\\",
                        "usage": {
                            "percent": 70.0,
                        },
                        "usage_gb": {
                            "total": 500.0,
                            "used": 350.0,
                            "free": 150.0,
                        }
                    }
                ]
            },
            "network": {
                "io_counters": {
                    "bytes_sent": 1024 * 1024 * 10,  # 10MB
                    "bytes_recv": 1024 * 1024 * 20,  # 20MB
                    "packets_sent": 1000,
                    "packets_recv": 2000,
                }
            },
            "battery": {
                "percent": 75.0,
                "power_plugged": True,
                "time_left": "3:45:00",
            }
        }
        
        # 模拟事件
        self.test_event = Event(
            event_type=EventType.SYSTEM_STATUS_UPDATE,
            sender="TestSender",
            data={
                "timestamp": self.test_timestamp,
                "metrics": self.test_metrics
            }
        )
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        # 创建两个实例
        instance1 = DataProcessor()
        instance2 = DataProcessor()
        
        # 验证它们是相同的实例
        self.assertIs(instance1, instance2)
    
    def test_init(self):
        """测试初始化"""
        # 验证历史数据容器
        for key in ["cpu", "memory", "disk", "network", "battery", "processes", "timestamps"]:
            self.assertIn(key, self.processor.history)
            self.assertIsInstance(self.processor.history[key], collections.deque)
        
        # 验证统计数据
        for key in ["cpu", "memory", "disk", "network", "battery"]:
            self.assertIn(key, self.processor.stats)
            
        # 验证阈值配置
        for key in ["cpu_high", "memory_high", "disk_space_low", "battery_low", "network_high"]:
            self.assertIn(key, self.processor.thresholds)
        
        # 验证事件处理器注册
        self.mock_event_system.register_handler.assert_called_once_with(
            EventType.SYSTEM_STATUS_UPDATE,
            self.processor._handle_system_status_update
        )
    
    def test_handle_system_status_update(self):
        """测试处理系统状态更新事件"""
        # 打补丁内部方法
        self.processor._update_history = Mock()
        self.processor._calculate_stats = Mock()
        self.processor._check_thresholds = Mock()
        self.processor._apply_custom_processors = Mock()
        
        # 处理事件
        self.processor._handle_system_status_update(self.test_event)
        
        # 验证方法调用
        self.processor._update_history.assert_called_once_with(
            self.test_timestamp, self.test_metrics
        )
        self.processor._calculate_stats.assert_called_once()
        self.processor._check_thresholds.assert_called_once_with(self.test_metrics)
        self.processor._apply_custom_processors.assert_called_once_with(
            self.test_timestamp, self.test_metrics
        )
    
    def test_update_history(self):
        """测试更新历史数据"""
        # 调用方法
        self.processor._update_history(self.test_timestamp, self.test_metrics)
        
        # 验证时间戳
        self.assertEqual(len(self.processor.history["timestamps"]), 1)
        self.assertEqual(self.processor.history["timestamps"][0], self.test_timestamp)
        
        # 验证CPU历史数据
        self.assertEqual(len(self.processor.history["cpu"]), 1)
        self.assertEqual(self.processor.history["cpu"][0]["percent"], 30.0)
        self.assertEqual(self.processor.history["cpu"][0]["per_cpu"], [25.0, 35.0, 28.0, 32.0])
        
        # 验证内存历史数据
        self.assertEqual(len(self.processor.history["memory"]), 1)
        self.assertEqual(self.processor.history["memory"][0]["percent"], 45.0)
        self.assertEqual(self.processor.history["memory"][0]["used_gb"], 7.2)
        self.assertEqual(self.processor.history["memory"][0]["total_gb"], 16.0)
        
        # 验证磁盘历史数据
        self.assertEqual(len(self.processor.history["disk"]), 1)
        self.assertEqual(self.processor.history["disk"][0]["C:\\"]["percent"], 70.0)
        
        # 验证网络历史数据
        self.assertEqual(len(self.processor.history["network"]), 1)
        self.assertEqual(self.processor.history["network"][0]["bytes_sent"], 1024 * 1024 * 10)
        self.assertEqual(self.processor.history["network"][0]["bytes_recv"], 1024 * 1024 * 20)
        
        # 验证电池历史数据
        self.assertEqual(len(self.processor.history["battery"]), 1)
        self.assertEqual(self.processor.history["battery"][0]["percent"], 75.0)
        self.assertEqual(self.processor.history["battery"][0]["plugged"], True)
    
    def test_calculate_stats(self):
        """测试计算统计数据"""
        # 准备历史数据
        self.processor.history["cpu"].append({"percent": 20.0})
        self.processor.history["cpu"].append({"percent": 30.0})
        self.processor.history["cpu"].append({"percent": 40.0})
        
        self.processor.history["memory"].append({"percent": 40.0})
        self.processor.history["memory"].append({"percent": 45.0})
        self.processor.history["memory"].append({"percent": 50.0})
        
        self.processor.history["disk"].append({
            "C:\\": {"percent": 65.0},
            "D:\\": {"percent": 55.0}
        })
        self.processor.history["disk"].append({
            "C:\\": {"percent": 70.0},
            "D:\\": {"percent": 60.0}
        })
        
        # 计算统计数据
        self.processor._calculate_stats()
        
        # 验证CPU统计数据
        self.assertEqual(self.processor.stats["cpu"]["current"], 40.0)
        self.assertEqual(self.processor.stats["cpu"]["min"], 20.0)
        self.assertEqual(self.processor.stats["cpu"]["max"], 40.0)
        self.assertEqual(self.processor.stats["cpu"]["avg"], 30.0)
        
        # 验证内存统计数据
        self.assertEqual(self.processor.stats["memory"]["current"], 50.0)
        self.assertEqual(self.processor.stats["memory"]["min"], 40.0)
        self.assertEqual(self.processor.stats["memory"]["max"], 50.0)
        self.assertEqual(self.processor.stats["memory"]["avg"], 45.0)
        
        # 验证磁盘统计数据（优先选择C:\\）
        self.assertEqual(self.processor.stats["disk"]["current"], 70.0)
        self.assertEqual(self.processor.stats["disk"]["min"], 65.0)
        self.assertEqual(self.processor.stats["disk"]["max"], 70.0)
        self.assertEqual(self.processor.stats["disk"]["avg"], 67.5)
    
    def test_check_thresholds(self):
        """测试检查阈值并发送告警"""
        # 打补丁发送告警方法
        self.processor._send_alert = Mock()
        
        # 设置阈值
        self.processor.thresholds = {
            "cpu_high": 80.0,
            "memory_high": 80.0,
            "disk_space_low": 20.0,
            "battery_low": 20.0,
        }
        
        # 重置告警状态
        self.processor.alert_status = {
            "cpu_high": False,
            "memory_high": False,
            "disk_space_low": False,
            "battery_low": False,
        }
        
        # 测试CPU告警（未超过阈值）
        metrics = {"cpu": {"percent_overall": 70.0}}
        self.processor._check_thresholds(metrics)
        self.processor._send_alert.assert_not_called()
        self.assertFalse(self.processor.alert_status["cpu_high"])
        
        # 测试CPU告警（超过阈值）
        metrics = {"cpu": {"percent_overall": 85.0}}
        self.processor._check_thresholds(metrics)
        self.processor._send_alert.assert_called_once()
        self.assertTrue(self.processor.alert_status["cpu_high"])
        
        # 重置
        self.processor._send_alert.reset_mock()
        
        # 测试内存告警
        metrics = {"memory": {"percent": 85.0}}
        self.processor._check_thresholds(metrics)
        self.processor._send_alert.assert_called_once()
        self.assertTrue(self.processor.alert_status["memory_high"])
        
        # 重置
        self.processor._send_alert.reset_mock()
        
        # 测试磁盘告警
        metrics = {"disk": {"partitions": [{"mountpoint": "C:\\", "usage": {"percent": 85.0}}]}}
        self.processor._check_thresholds(metrics)
        self.processor._send_alert.assert_called_once()
        self.assertTrue(self.processor.alert_status["disk_space_low"])
        
        # 重置
        self.processor._send_alert.reset_mock()
        
        # 测试电池告警（已接通电源，不应告警）
        metrics = {"battery": {"percent": 15.0, "power_plugged": True}}
        self.processor._check_thresholds(metrics)
        self.processor._send_alert.assert_not_called()
        self.assertFalse(self.processor.alert_status["battery_low"])
        
        # 测试电池告警（未接通电源，应告警）
        metrics = {"battery": {"percent": 15.0, "power_plugged": False}}
        self.processor._check_thresholds(metrics)
        self.processor._send_alert.assert_called_once()
        self.assertTrue(self.processor.alert_status["battery_low"])
    
    def test_send_alert(self):
        """测试发送告警事件"""
        # 调用方法
        self.processor._send_alert("test_alert", "测试告警", {"test": "data"})
        
        # 验证事件分发
        self.mock_event_system.dispatch_event.assert_called_once()
        
        # 获取分发的事件
        event = self.mock_event_system.dispatch_event.call_args[0][0]
        self.assertEqual(event.type, EventType.SYSTEM_STATUS_UPDATE)
        self.assertEqual(event.sender, "DataProcessor")
        self.assertEqual(event.data["alert"], True)
        self.assertEqual(event.data["alert_type"], "test_alert")
        self.assertEqual(event.data["message"], "测试告警")
        self.assertEqual(event.data["data"]["test"], "data")
    
    def test_register_unregister_custom_processor(self):
        """测试注册和注销自定义数据处理器"""
        # 创建测试处理器
        def test_processor(timestamp, metrics, history, stats):
            pass
        
        # 注册处理器
        result = self.processor.register_custom_processor("test", test_processor)
        self.assertTrue(result)
        self.assertIn("test", self.processor.custom_processors)
        self.assertEqual(self.processor.custom_processors["test"], test_processor)
        
        # 再次注册同名处理器
        result = self.processor.register_custom_processor("test", test_processor)
        self.assertTrue(result)  # 应该返回True，但会发出警告
        
        # 注销不存在的处理器
        result = self.processor.unregister_custom_processor("nonexistent")
        self.assertFalse(result)
        
        # 注销存在的处理器
        result = self.processor.unregister_custom_processor("test")
        self.assertTrue(result)
        self.assertNotIn("test", self.processor.custom_processors)
    
    def test_apply_custom_processors(self):
        """测试应用自定义处理器"""
        # 创建测试处理器
        mock_processor = Mock()
        
        # 注册处理器
        self.processor.register_custom_processor("test", mock_processor)
        
        # 应用处理器
        self.processor._apply_custom_processors(self.test_timestamp, self.test_metrics)
        
        # 验证处理器被调用
        mock_processor.assert_called_once_with(
            self.test_timestamp, 
            self.test_metrics, 
            self.processor.history, 
            self.processor.stats
        )
        
        # 测试处理器异常
        mock_processor.side_effect = Exception("测试异常")
        # 不应该抛出异常，而是记录错误
        self.processor._apply_custom_processors(self.test_timestamp, self.test_metrics)
    
    def test_set_get_threshold(self):
        """测试设置和获取告警阈值"""
        # 初始阈值
        initial_cpu_high = self.processor.thresholds["cpu_high"]
        
        # 设置阈值
        result = self.processor.set_threshold("cpu_high", 90.0)
        self.assertTrue(result)
        self.assertEqual(self.processor.thresholds["cpu_high"], 90.0)
        
        # 设置不存在的阈值
        result = self.processor.set_threshold("nonexistent", 50.0)
        self.assertFalse(result)
        
        # 获取阈值
        value = self.processor.get_threshold("cpu_high")
        self.assertEqual(value, 90.0)
        
        # 获取不存在的阈值
        value = self.processor.get_threshold("nonexistent")
        self.assertIsNone(value)
        
        # 获取所有阈值
        thresholds = self.processor.get_all_thresholds()
        self.assertEqual(thresholds["cpu_high"], 90.0)
    
    def test_get_stats(self):
        """测试获取统计数据"""
        # 设置测试数据
        self.processor.stats = {
            "cpu": {"current": 30.0, "min": 20.0, "max": 40.0, "avg": 30.0},
            "memory": {"current": 50.0, "min": 40.0, "max": 60.0, "avg": 50.0},
        }
        
        # 获取统计数据
        stats = self.processor.get_stats()
        
        # 验证数据
        self.assertEqual(stats, self.processor.stats)
        self.assertIsNot(stats, self.processor.stats)  # 应该是一个副本
    
    def test_get_history(self):
        """测试获取历史数据"""
        # 设置测试数据
        self.processor.history["cpu"].append({"percent": 20.0})
        self.processor.history["cpu"].append({"percent": 30.0})
        self.processor.history["cpu"].append({"percent": 40.0})
        
        # 获取全部历史数据
        history = self.processor.get_history("cpu")
        self.assertEqual(len(history), 3)
        
        # 获取部分历史数据
        history = self.processor.get_history("cpu", 2)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["percent"], 30.0)
        self.assertEqual(history[1]["percent"], 40.0)
        
        # 获取不存在的类型
        history = self.processor.get_history("nonexistent")
        self.assertEqual(history, [])
    
    def test_get_history_with_timestamps(self):
        """测试获取带时间戳的历史数据"""
        # 设置测试数据
        self.processor.history["cpu"].append({"percent": 20.0})
        self.processor.history["cpu"].append({"percent": 30.0})
        self.processor.history["cpu"].append({"percent": 40.0})
        
        self.processor.history["timestamps"].append(100)
        self.processor.history["timestamps"].append(200)
        self.processor.history["timestamps"].append(300)
        
        # 获取全部历史数据
        history = self.processor.get_history_with_timestamps("cpu")
        self.assertEqual(len(history), 3)
        
        # 验证数据格式
        self.assertEqual(history[0][0], 100)
        self.assertEqual(history[0][1]["percent"], 20.0)
        
        # 获取部分历史数据
        history = self.processor.get_history_with_timestamps("cpu", 2)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0][0], 200)
        self.assertEqual(history[1][0], 300)
        
        # 获取不存在的类型
        history = self.processor.get_history_with_timestamps("nonexistent")
        self.assertEqual(history, [])
    
    def test_clear_history(self):
        """测试清空历史数据"""
        # 设置测试数据
        self.processor.history["cpu"].append({"percent": 20.0})
        self.processor.history["memory"].append({"percent": 40.0})
        
        # 清空历史数据
        self.processor.clear_history()
        
        # 验证数据已清空
        self.assertEqual(len(self.processor.history["cpu"]), 0)
        self.assertEqual(len(self.processor.history["memory"]), 0)


if __name__ == '__main__':
    unittest.main() 