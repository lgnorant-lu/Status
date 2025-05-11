"""
---------------------------------------------------------------
File name:                  test_data_processor.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                数据处理器测试
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import unittest
from unittest.mock import patch, MagicMock
import logging

from status.monitor.data_processor import DataProcessor


class TestDataProcessor(unittest.TestCase):
    """测试数据处理器"""

    def setUp(self):
        """测试前的准备工作"""
        # 配置日志
        logging.basicConfig(level=logging.CRITICAL)
        
        # 创建数据处理器实例
        self.processor = DataProcessor()
        
    def test_init(self):
        """测试初始化"""
        # 默认配置初始化
        processor = DataProcessor()
        self.assertIsNotNone(processor)
        self.assertIsInstance(processor.config, dict)
        
        # 自定义配置初始化
        config = {
            "enable_trends": True,
            "smoothing_window": 5,
            "enable_predictions": False
        }
        processor = DataProcessor(config)
        self.assertEqual(processor.config["enable_trends"], True)
        self.assertEqual(processor.config["smoothing_window"], 5)
        self.assertEqual(processor.config["enable_predictions"], False)
        
    def test_update_config(self):
        """测试更新配置"""
        # 初始配置
        self.processor.config = {
            "enable_trends": False,
            "smoothing_window": 3,
            "threshold_values": {
                "cpu_high": 80.0
            }
        }
        
        # 更新部分配置
        self.processor.update_config({
            "enable_trends": True,
            "threshold_values": {
                "memory_high": 90.0
            }
        })
        
        # 检查配置是否正确更新
        self.assertEqual(self.processor.config["enable_trends"], True)
        self.assertEqual(self.processor.config["smoothing_window"], 3)  # 保持不变
        self.assertEqual(self.processor.config["threshold_values"]["cpu_high"], 80.0)  # 保持不变
        self.assertEqual(self.processor.config["threshold_values"]["memory_high"], 90.0)  # 新增配置
        
    def test_process_cpu_data(self):
        """测试处理CPU数据"""
        # 初始CPU数据
        cpu_data = {
            'usage': 75.5,
            'core_count': 8,
            'per_core': [70.0, 80.0, 75.0, 85.0, 72.0, 68.0, 78.0, 76.0]
        }
        
        # 处理CPU数据
        processed = self.processor._process_cpu_data(cpu_data)
        
        # 验证结果
        self.assertIn('usage', processed)
        self.assertEqual(processed['usage'], 75.5)
        self.assertIn('status', processed)
        self.assertIn('load_level', processed)
        self.assertTrue(0 <= processed['load_level'] <= 1.0)
        
    def test_process_memory_data(self):
        """测试处理内存数据"""
        # 初始内存数据
        memory_data = {
            'percent': 65.8,
            'total': 16 * 1024 * 1024 * 1024,  # 16GB
            'used': 10.5 * 1024 * 1024 * 1024  # 10.5GB
        }
        
        # 处理内存数据
        processed = self.processor._process_memory_data(memory_data)
        
        # 验证结果
        self.assertIn('percent', processed)
        self.assertEqual(processed['percent'], 65.8)
        self.assertIn('status', processed)
        self.assertIn('usage_level', processed)
        self.assertTrue(0 <= processed['usage_level'] <= 1.0)
        self.assertIn('total_gb', processed)
        self.assertIn('used_gb', processed)
        # 检查GB转换是否正确
        self.assertAlmostEqual(processed['total_gb'], 16.0, places=1)
        self.assertAlmostEqual(processed['used_gb'], 10.5, places=1)
        
    def test_process_disk_data(self):
        """测试处理磁盘数据"""
        # 初始磁盘数据
        disk_data = {
            'percent': 72.4,
            'total': 500 * 1024 * 1024 * 1024,  # 500GB
            'used': 362 * 1024 * 1024 * 1024,   # 362GB
            'io_read': 15 * 1024 * 1024,        # 15MB读取
            'io_write': 8 * 1024 * 1024         # 8MB写入
        }
        
        # 处理磁盘数据
        processed = self.processor._process_disk_data(disk_data)
        
        # 验证结果
        self.assertIn('percent', processed)
        self.assertEqual(processed['percent'], 72.4)
        self.assertIn('status', processed)
        self.assertIn('usage_level', processed)
        self.assertTrue(0 <= processed['usage_level'] <= 1.0)
        self.assertIn('total_gb', processed)
        self.assertIn('used_gb', processed)
        # 检查GB转换是否正确
        self.assertAlmostEqual(processed['total_gb'], 500.0, places=1)
        self.assertAlmostEqual(processed['used_gb'], 362.0, places=1)
        
    def test_process_network_data(self):
        """测试处理网络数据"""
        # 准备网络测试数据
        raw_data = {
            "network": {
                "bytes_sent": 512000,         # 500KB
                "bytes_recv": 2048000,        # 2MB
                "packets_sent": 1000,
                "packets_recv": 3000,
                "dropin": 0,
                "dropout": 0,
                "connections": 120
            }
        }

        # 处理数据
        processed = self.processor._process_network_data(raw_data.get("network", {}))
        
        # 验证结果
        self.assertIsInstance(processed, dict)
        
        # 检查处理后的数据是否包含预期字段
        self.assertIn('upload_mb_per_sec', processed)
        self.assertIn('download_mb_per_sec', processed)
        self.assertIn('network_load', processed)
        self.assertIn('connections', processed)
        self.assertIn('status', processed)
        
        # 验证连接数
        self.assertEqual(processed['connections'], 120)
        
    def test_calculate_status(self):
        """测试计算状态"""
        # 测试正常状态
        status = self.processor._calculate_status(50.0, 70.0, 90.0)
        self.assertEqual(status, "normal")
        
        # 测试警告状态
        status = self.processor._calculate_status(75.0, 70.0, 90.0)
        self.assertEqual(status, "warning")
        
        # 测试危险状态
        status = self.processor._calculate_status(95.0, 70.0, 90.0)
        self.assertEqual(status, "danger")
        
    def test_normalize_value(self):
        """测试数值归一化"""
        # 在范围内的值
        normalized = self.processor._normalize_value(50, 0, 100)
        self.assertEqual(normalized, 0.5)
        
        # 超出上限的值
        normalized = self.processor._normalize_value(120, 0, 100)
        self.assertEqual(normalized, 1.0)
        
        # 低于下限的值
        normalized = self.processor._normalize_value(-10, 0, 100)
        self.assertEqual(normalized, 0.0)
        
        # 自定义范围
        normalized = self.processor._normalize_value(500, 200, 800)
        self.assertAlmostEqual(normalized, 0.5, places=1)
        
    def test_process_data(self):
        """测试处理完整数据集"""
        # 原始数据
        raw_data = {
            'cpu': {
                'usage': 65.0,
                'core_count': 4
            },
            'memory': {
                'percent': 70.0,
                'total': 8 * 1024 * 1024 * 1024,
                'used': 5.6 * 1024 * 1024 * 1024
            },
            'disk': {
                'percent': 80.0,
                'total': 256 * 1024 * 1024 * 1024,
                'used': 204.8 * 1024 * 1024 * 1024
            }
        }
        
        # 处理器方法模拟
        self.processor._process_cpu_data = MagicMock(return_value={
            'usage': 65.0,
            'status': 'normal',
            'load_level': 0.65
        })
        self.processor._process_memory_data = MagicMock(return_value={
            'percent': 70.0,
            'status': 'warning',
            'usage_level': 0.7,
            'total_gb': 8.0,
            'used_gb': 5.6
        })
        self.processor._process_disk_data = MagicMock(return_value={
            'percent': 80.0,
            'status': 'warning',
            'usage_level': 0.8,
            'total_gb': 256.0,
            'used_gb': 204.8
        })
        
        # 处理完整数据
        processed = self.processor.process_data(raw_data)
        
        # 验证结果
        self.assertIn('cpu', processed)
        self.assertIn('memory', processed)
        self.assertIn('disk', processed)
        self.assertIn('system', processed)
        
        # 检查系统总体状态
        self.assertIn('overall_status', processed['system'])
        self.assertIn('overall_load', processed['system'])
        
        # 验证调用情况
        self.processor._process_cpu_data.assert_called_once_with(raw_data['cpu'])
        self.processor._process_memory_data.assert_called_once_with(raw_data['memory'])
        self.processor._process_disk_data.assert_called_once_with(raw_data['disk'])
        
    def test_process_empty_data(self):
        """测试处理空数据"""
        # 处理空数据
        raw_data = {}
        processed = self.processor.process_data(raw_data)
        
        # 验证结果 - 应返回错误信息
        self.assertIsInstance(processed, dict)
        self.assertIn('error', processed)
        
        # 测试None数据
        processed = self.processor.process_data(None)
        
        # 验证结果
        self.assertIsInstance(processed, dict)
        self.assertIn('error', processed)
        
    def test_calculate_trends(self):
        """测试计算趋势"""
        # 启用趋势分析
        self.processor.config['enable_trends'] = True
        
        # 初始化历史数据
        self.processor.history = {
            'cpu': {'usage': [50.0, 55.0, 60.0, 65.0]},
            'memory': {'percent': [60.0, 65.0, 70.0, 75.0]}
        }
        
        # 处理新数据
        raw_data = {
            'cpu': {'usage': 70.0},
            'memory': {'percent': 80.0}
        }
        
        self.processor._process_cpu_data = MagicMock(return_value={
            'usage': 70.0,
            'status': 'normal'
        })
        self.processor._process_memory_data = MagicMock(return_value={
            'percent': 80.0,
            'status': 'warning'
        })
        
        processed = self.processor.process_data(raw_data)
        
        # 验证趋势计算
        self.assertIn('trend', processed['cpu'])
        self.assertIn('trend', processed['memory'])
        self.assertEqual(processed['cpu']['trend'], 'increasing')  # 上升趋势
        self.assertEqual(processed['memory']['trend'], 'increasing')  # 上升趋势
        
        # 验证历史数据更新
        self.assertEqual(len(self.processor.history['cpu']['usage']), 5)
        self.assertEqual(self.processor.history['cpu']['usage'][-1], 70.0)
        
    def test_smooth_data(self):
        """测试数据平滑"""
        # 设置平滑窗口
        self.processor.config['smoothing_window'] = 3
        
        # 测试数据
        values = [10.0, 20.0, 15.0, 25.0, 30.0]
        
        # 平滑数据
        smoothed = self.processor._smooth_data(values)
        
        # 验证结果
        self.assertEqual(len(smoothed), len(values))
        # 前两个值应保持不变，因为没有足够的历史数据进行平滑
        self.assertEqual(smoothed[0], values[0])
        self.assertEqual(smoothed[1], values[1])
        # 后面的值应该是移动平均
        self.assertEqual(smoothed[2], (10.0 + 20.0 + 15.0) / 3)
        self.assertEqual(smoothed[3], (20.0 + 15.0 + 25.0) / 3)
        self.assertEqual(smoothed[4], (15.0 + 25.0 + 30.0) / 3)
        
    def tearDown(self):
        """测试结束后的清理工作"""
        pass


if __name__ == '__main__':
    unittest.main() 