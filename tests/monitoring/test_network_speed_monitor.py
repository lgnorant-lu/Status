"""
---------------------------------------------------------------
File name:                  test_network_speed_monitor.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                测试网络速度监控功能
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

from status.monitoring.system_monitor import get_network_io, calculate_network_speed

class TestNetworkSpeedMonitor(unittest.TestCase):
    """测试网络速度监控功能"""
    
    def test_get_network_io_basic(self):
        """测试获取网络流量数据的基本功能"""
        # 调用函数获取网络流量数据
        net_data = get_network_io()
        
        # 验证返回的数据格式和内容
        self.assertIsInstance(net_data, dict)
        self.assertIn('bytes_sent', net_data)
        self.assertIn('bytes_recv', net_data)
        self.assertIsInstance(net_data['bytes_sent'], int)
        self.assertIsInstance(net_data['bytes_recv'], int)
    
    def test_calculate_network_speed(self):
        """测试基于两次网络数据计算上传下载速率"""
        # 模拟两次网络数据
        prev_net = {'bytes_sent': 1000000, 'bytes_recv': 2000000}
        curr_net = {'bytes_sent': 1001024, 'bytes_recv': 2002048}
        time_diff = 1.0  # 1秒
        
        # 计算速率
        net_speed = calculate_network_speed(prev_net, curr_net, time_diff)
        
        # 验证计算结果 (1024字节/秒 = 1 KB/秒)
        self.assertIsInstance(net_speed, dict)
        self.assertIn('upload_kbps', net_speed)
        self.assertIn('download_kbps', net_speed)
        self.assertAlmostEqual(net_speed['upload_kbps'], 1.0, delta=0.1)  # 1 KB/s上传
        self.assertAlmostEqual(net_speed['download_kbps'], 2.0, delta=0.1)  # 2 KB/s下载
    
    def test_calculate_network_speed_zero_time_diff(self):
        """测试时间差为零的情况"""
        prev_net = {'bytes_sent': 1000000, 'bytes_recv': 2000000}
        curr_net = {'bytes_sent': 1001024, 'bytes_recv': 2002048}
        time_diff = 0.0  # 零秒，这会导致除以零错误如果没有正确处理
        
        # 计算速率 - 应该处理零时间差的情况并返回零速率
        net_speed = calculate_network_speed(prev_net, curr_net, time_diff)
        
        # 验证计算结果 - 应该返回零而不是错误
        self.assertEqual(net_speed['upload_kbps'], 0)
        self.assertEqual(net_speed['download_kbps'], 0)
    
    @patch('psutil.net_io_counters')
    def test_network_io_not_available(self, mock_net_io_counters):
        """测试网络流量数据不可用的情况"""
        # 模拟psutil.net_io_counters返回None
        mock_net_io_counters.return_value = None
        
        # 获取网络流量数据
        net_data = get_network_io()
        
        # 验证返回了默认值而不是崩溃
        self.assertIsInstance(net_data, dict)
        self.assertEqual(net_data['bytes_sent'], 0)
        self.assertEqual(net_data['bytes_recv'], 0)
    
    def test_real_network_speed_calculation(self):
        """测试真实环境下连续两次调用计算速率"""
        # 第一次获取数据
        net_data_1 = get_network_io()
        time_1 = time.time()
        
        # 小延迟，确保有足够时间差
        time.sleep(0.5)
        
        # 第二次获取数据
        net_data_2 = get_network_io()
        time_2 = time.time()
        
        # 计算速率
        time_diff = time_2 - time_1
        net_speed = calculate_network_speed(net_data_1, net_data_2, time_diff)
        
        # 验证结果格式
        self.assertIsInstance(net_speed, dict)
        self.assertIn('upload_kbps', net_speed)
        self.assertIn('download_kbps', net_speed)
        self.assertIsInstance(net_speed['upload_kbps'], float)
        self.assertIsInstance(net_speed['download_kbps'], float)
        # 不验证具体值，因为实际网络活动不可预测

if __name__ == '__main__':
    unittest.main() 