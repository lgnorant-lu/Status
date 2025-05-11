"""
---------------------------------------------------------------
File name:                  test_data_collector.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                系统数据采集器测试
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import unittest
from unittest.mock import patch, MagicMock
import psutil
import logging

from status.monitor.data_collector import SystemDataCollector


class TestSystemDataCollector(unittest.TestCase):
    """测试系统数据采集器"""

    def setUp(self):
        """测试前的准备工作"""
        # 配置日志
        logging.basicConfig(level=logging.CRITICAL)
        
        # 创建数据采集器实例
        self.collector = SystemDataCollector()
        
    def test_init(self):
        """测试初始化"""
        # 默认配置初始化
        collector = SystemDataCollector()
        self.assertIsNotNone(collector)
        self.assertIsInstance(collector.config, dict)
        
        # 自定义配置初始化
        config = {
            "enable_advanced_metrics": True,
            "enable_io_stats": False,
            "enable_network_stats": True
        }
        collector = SystemDataCollector(config)
        self.assertEqual(collector.config["enable_advanced_metrics"], True)
        self.assertEqual(collector.config["enable_io_stats"], False)
        self.assertEqual(collector.config["enable_network_stats"], True)
        
    def test_update_config(self):
        """测试更新配置"""
        # 初始配置
        self.collector.config = {
            "enable_advanced_metrics": False,
            "enable_io_stats": True,
            "collection_interval": 1.0
        }
        
        # 更新部分配置
        self.collector.update_config({
            "enable_advanced_metrics": True,
            "new_option": "value"
        })
        
        # 检查配置是否正确更新
        self.assertEqual(self.collector.config["enable_advanced_metrics"], True)
        self.assertEqual(self.collector.config["enable_io_stats"], True)  # 保持不变
        self.assertEqual(self.collector.config["collection_interval"], 1.0)  # 保持不变
        self.assertEqual(self.collector.config["new_option"], "value")  # 新增配置
        
    @patch('psutil.cpu_percent')
    def test_collect_cpu_data(self, mock_cpu_percent):
        """测试CPU数据采集"""
        # 模拟CPU数据
        mock_cpu_percent.return_value = 25.5
        
        # 采集CPU数据
        data = self.collector._collect_cpu_data()
        
        # 验证结果
        self.assertIn('usage', data)
        self.assertEqual(data['usage'], 25.5)
        
    @patch('psutil.virtual_memory')
    def test_collect_memory_data(self, mock_virtual_memory):
        """测试内存数据采集"""
        # 模拟内存数据
        mock_memory = MagicMock()
        mock_memory.percent = 60.2
        mock_memory.total = 16 * 1024 * 1024 * 1024  # 16GB
        mock_memory.used = 10 * 1024 * 1024 * 1024   # 10GB
        mock_virtual_memory.return_value = mock_memory
        
        # 采集内存数据
        data = self.collector._collect_memory_data()
        
        # 验证结果
        self.assertIn('percent', data)
        self.assertEqual(data['percent'], 60.2)
        self.assertIn('total', data)
        self.assertEqual(data['total'], 16 * 1024 * 1024 * 1024)
        self.assertIn('used', data)
        self.assertEqual(data['used'], 10 * 1024 * 1024 * 1024)
        
    @patch('psutil.disk_usage')
    def test_collect_disk_data(self, mock_disk_usage):
        """测试磁盘数据采集"""
        # 模拟磁盘数据
        mock_disk = MagicMock()
        mock_disk.percent = 75.0
        mock_disk.total = 500 * 1024 * 1024 * 1024  # 500GB
        mock_disk.used = 375 * 1024 * 1024 * 1024   # 375GB
        mock_disk_usage.return_value = mock_disk
        
        # 采集磁盘数据
        data = self.collector._collect_disk_data()
        
        # 验证结果
        self.assertIn('percent', data)
        self.assertEqual(data['percent'], 75.0)
        self.assertIn('total', data)
        self.assertEqual(data['total'], 500 * 1024 * 1024 * 1024)
        self.assertIn('used', data)
        self.assertEqual(data['used'], 375 * 1024 * 1024 * 1024)
        
    @patch('psutil.net_io_counters')
    def test_collect_network_data(self, mock_net_io):
        """测试网络数据采集"""
        # 模拟网络数据
        mock_net = MagicMock()
        mock_net.bytes_sent = 1024 * 1024 * 10  # 10MB
        mock_net.bytes_recv = 1024 * 1024 * 50  # 50MB
        mock_net_io.return_value = mock_net
        
        # 采集网络数据
        data = self.collector._collect_network_data()
        
        # 验证结果
        self.assertIn('bytes_sent', data)
        self.assertEqual(data['bytes_sent'], 1024 * 1024 * 10)
        self.assertIn('bytes_recv', data)
        self.assertEqual(data['bytes_recv'], 1024 * 1024 * 50)
        
    def test_collect_data_all(self):
        """测试采集所有数据"""
        # 模拟各个采集方法
        self.collector._collect_cpu_data = MagicMock(return_value={'usage': 30.0})
        self.collector._collect_memory_data = MagicMock(return_value={'percent': 65.0})
        self.collector._collect_disk_data = MagicMock(return_value={'percent': 70.0})
        self.collector._collect_network_data = MagicMock(return_value={'bytes_sent': 1000})
        
        # 采集所有数据
        data = self.collector.collect_data()
        
        # 验证结果
        self.assertIn('cpu', data)
        self.assertEqual(data['cpu']['usage'], 30.0)
        self.assertIn('memory', data)
        self.assertEqual(data['memory']['percent'], 65.0)
        self.assertIn('disk', data)
        self.assertEqual(data['disk']['percent'], 70.0)
        self.assertIn('network', data)
        self.assertEqual(data['network']['bytes_sent'], 1000)
        
    def test_collect_data_specified(self):
        """测试采集指定数据"""
        # 模拟各个采集方法
        self.collector._collect_cpu_data = MagicMock(return_value={'usage': 30.0})
        self.collector._collect_memory_data = MagicMock(return_value={'percent': 65.0})
        self.collector._collect_disk_data = MagicMock(return_value={'percent': 70.0})
        self.collector._collect_network_data = MagicMock(return_value={'bytes_sent': 1000})
        
        # 只采集CPU和内存数据
        data = self.collector.collect_data(['cpu', 'memory'])
        
        # 验证结果
        self.assertIn('cpu', data)
        self.assertEqual(data['cpu']['usage'], 30.0)
        self.assertIn('memory', data)
        self.assertEqual(data['memory']['percent'], 65.0)
        self.assertNotIn('disk', data)
        self.assertNotIn('network', data)
        
        # 验证调用情况
        self.collector._collect_cpu_data.assert_called_once()
        self.collector._collect_memory_data.assert_called_once()
        self.collector._collect_disk_data.assert_not_called()
        self.collector._collect_network_data.assert_not_called()
        
    def test_collect_data_invalid(self):
        """测试采集无效数据类型"""
        # 模拟各个采集方法
        self.collector._collect_cpu_data = MagicMock(return_value={'usage': 30.0})
        
        # 采集无效的数据类型
        data = self.collector.collect_data(['invalid_type'])
        
        # 验证结果
        self.assertEqual(data, {})
        
        # 验证调用情况
        self.collector._collect_cpu_data.assert_not_called()
        
    def test_get_available_metrics(self):
        """测试获取可用指标"""
        metrics = self.collector.get_available_metrics()
        
        # 验证结果
        self.assertIsInstance(metrics, list)
        self.assertIn('cpu', metrics)
        self.assertIn('memory', metrics)
        self.assertIn('disk', metrics)
        self.assertIn('network', metrics)
        
    def test_check_system_alerts(self):
        """测试系统告警检测"""
        # 创建采集器并设置告警阈值
        collector = SystemDataCollector({
            "alert_thresholds": {
                "cpu_usage": 80.0,
                "memory_usage": 90.0,
                "disk_usage": 95.0
            }
        })
        
        # 模拟各项指标
        collector._collect_cpu_data = MagicMock(return_value={'usage': 85.0})  # 超过阈值
        collector._collect_memory_data = MagicMock(return_value={'percent': 80.0})  # 未超过阈值
        collector._collect_disk_data = MagicMock(return_value={'percent': 96.0})  # 超过阈值
        
        # 检测告警
        alerts = collector.check_system_alerts()
        
        # 验证结果
        self.assertEqual(len(alerts), 2)  # 两个告警
        self.assertIn('cpu', [alert['type'] for alert in alerts])
        self.assertIn('disk', [alert['type'] for alert in alerts])
        self.assertNotIn('memory', [alert['type'] for alert in alerts])
        
    def tearDown(self):
        """测试结束后的清理工作"""
        pass


if __name__ == '__main__':
    unittest.main() 