"""
---------------------------------------------------------------
File name:                  test_disk_io_monitor.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                测试磁盘I/O监控功能
----------------------------------------------------------------

Changed history:            
                            2025/05/13: 初始创建;
----
"""

import unittest
import time
from unittest.mock import patch, MagicMock
import sys
import os

# 将项目根目录添加到路径，便于导入
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from status.monitoring.system_monitor import get_disk_io, calculate_disk_io_speed

class TestDiskIOMonitor(unittest.TestCase):
    """测试磁盘I/O监控功能"""
    
    def test_get_disk_io_basic(self):
        """测试获取磁盘I/O数据的基本功能"""
        # 调用函数获取磁盘I/O数据
        io_data = get_disk_io()
        
        # 验证返回的数据格式和内容
        self.assertIsInstance(io_data, dict)
        self.assertIn('read_bytes', io_data)
        self.assertIn('write_bytes', io_data)
        self.assertIsInstance(io_data['read_bytes'], int)
        self.assertIsInstance(io_data['write_bytes'], int)
    
    def test_calculate_disk_io_speed(self):
        """测试基于两次I/O数据计算读写速率"""
        # 模拟两次I/O数据
        prev_io = {'read_bytes': 1000000, 'write_bytes': 500000}
        curr_io = {'read_bytes': 1001024, 'write_bytes': 500512}
        time_diff = 1.0  # 1秒
        
        # 计算速率
        io_speed = calculate_disk_io_speed(prev_io, curr_io, time_diff)
        
        # 验证计算结果 (1024字节/秒 = 1 KB/秒)
        self.assertIsInstance(io_speed, dict)
        self.assertIn('read_kbps', io_speed)
        self.assertIn('write_kbps', io_speed)
        self.assertAlmostEqual(io_speed['read_kbps'], 1.0, delta=0.1)  # 1 KB/s
        self.assertAlmostEqual(io_speed['write_kbps'], 0.5, delta=0.1)  # 0.5 KB/s
    
    def test_calculate_disk_io_speed_zero_time_diff(self):
        """测试时间差为零的情况"""
        prev_io = {'read_bytes': 1000000, 'write_bytes': 500000}
        curr_io = {'read_bytes': 1001024, 'write_bytes': 500512}
        time_diff = 0.0  # 零秒，这会导致除以零错误如果没有正确处理
        
        # 计算速率 - 应该处理零时间差的情况并返回零速率
        io_speed = calculate_disk_io_speed(prev_io, curr_io, time_diff)
        
        # 验证计算结果 - 应该返回零而不是错误
        self.assertEqual(io_speed['read_kbps'], 0)
        self.assertEqual(io_speed['write_kbps'], 0)
    
    @patch('psutil.disk_io_counters')
    def test_disk_io_not_available(self, mock_disk_io_counters):
        """测试磁盘I/O数据不可用的情况"""
        # 模拟psutil.disk_io_counters返回None
        mock_disk_io_counters.return_value = None
        
        # 获取磁盘I/O数据
        io_data = get_disk_io()
        
        # 验证返回了默认值而不是崩溃
        self.assertIsInstance(io_data, dict)
        self.assertEqual(io_data['read_bytes'], 0)
        self.assertEqual(io_data['write_bytes'], 0)
    
    def test_real_io_speed_calculation(self):
        """测试真实环境下连续两次调用计算速率"""
        # 第一次获取数据
        io_data_1 = get_disk_io()
        time_1 = time.time()
        
        # 小延迟，确保有足够时间差
        time.sleep(0.5)
        
        # 第二次获取数据
        io_data_2 = get_disk_io()
        time_2 = time.time()
        
        # 计算速率
        time_diff = time_2 - time_1
        io_speed = calculate_disk_io_speed(io_data_1, io_data_2, time_diff)
        
        # 验证结果格式
        self.assertIsInstance(io_speed, dict)
        self.assertIn('read_kbps', io_speed)
        self.assertIn('write_kbps', io_speed)
        self.assertIsInstance(io_speed['read_kbps'], float)
        self.assertIsInstance(io_speed['write_kbps'], float)
        # 不验证具体值，因为实际磁盘活动不可预测

if __name__ == '__main__':
    unittest.main() 