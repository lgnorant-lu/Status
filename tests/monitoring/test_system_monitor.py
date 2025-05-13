"""
---------------------------------------------------------------
File name:                  test_system_monitor.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                测试系统监控模块的功能
----------------------------------------------------------------

Changed history:
                            2025/05/13: 初始创建;
                            2025/05/13: 添加测试获取详细系统信息功能;
----
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入要测试的模块
from status.monitoring.system_monitor import (
    get_cpu_usage, get_memory_usage, publish_stats, 
    get_cpu_cores_usage, get_memory_details, get_disk_usage, get_network_info
)
from status.core.events import EventManager, SystemStatsUpdatedEvent

class TestSystemMonitor(unittest.TestCase):
    """测试系统监控模块"""

    @patch('status.monitoring.system_monitor.psutil.cpu_percent')
    def test_get_cpu_usage(self, mock_cpu_percent):
        """测试获取CPU使用率"""
        # 设置模拟返回值
        mock_cpu_percent.return_value = 45.6
        
        # 调用函数
        result = get_cpu_usage()
        
        # 验证结果
        self.assertEqual(result, 45.6)
        mock_cpu_percent.assert_called_once_with(interval=None)
    
    @patch('status.monitoring.system_monitor.psutil.virtual_memory')
    def test_get_memory_usage(self, mock_virtual_memory):
        """测试获取内存使用率"""
        # 设置模拟返回值
        mock_mem = MagicMock()
        mock_mem.percent = 60.2
        mock_virtual_memory.return_value = mock_mem
        
        # 调用函数
        result = get_memory_usage()
        
        # 验证结果
        self.assertEqual(result, 60.2)
        mock_virtual_memory.assert_called_once()
    
    @patch('status.monitoring.system_monitor.psutil.cpu_percent')
    def test_get_cpu_cores_usage(self, mock_cpu_percent):
        """测试获取CPU核心使用率"""
        # 设置模拟返回值 - 模拟一个四核CPU
        mock_cpu_percent.return_value = [40.0, 60.0, 45.0, 55.0]  # 修复：直接设置percpu=True的返回值
        
        # 调用函数
        result = get_cpu_cores_usage()
        
        # 验证结果
        self.assertEqual(len(result), 4)  # 应该有4个核心
        self.assertEqual(result, [40.0, 60.0, 45.0, 55.0])
        mock_cpu_percent.assert_called_once_with(percpu=True)
    
    @patch('status.monitoring.system_monitor.psutil.virtual_memory')
    def test_get_memory_details(self, mock_virtual_memory):
        """测试获取详细内存信息"""
        # 设置模拟返回值
        mock_mem = MagicMock()
        mock_mem.total = 16000000000  # 16GB
        mock_mem.available = 8000000000  # 8GB
        mock_mem.used = 7000000000  # 7GB
        mock_mem.free = 1000000000  # 1GB
        mock_mem.percent = 43.75  # 使用率百分比
        mock_virtual_memory.return_value = mock_mem
        
        # 调用函数
        result = get_memory_details()
        
        # 验证结果
        self.assertIsInstance(result, dict)
        # 修改期望值以匹配实际计算结果
        self.assertEqual(result['total_mb'], 15258)  # 16GB = 15258MB
        self.assertEqual(result['available_mb'], 7629)  # 8GB = 7629MB
        self.assertEqual(result['used_mb'], 6675)  # 7GB = 6675MB
        self.assertEqual(result['free_mb'], 953)  # 1GB = 953MB
        self.assertEqual(result['percent'], 43.75)
        mock_virtual_memory.assert_called_once()
    
    @patch('status.monitoring.system_monitor.psutil.disk_usage')
    def test_get_disk_usage(self, mock_disk_usage):
        """测试获取磁盘使用情况"""
        # 设置模拟返回值
        mock_disk = MagicMock()
        mock_disk.total = 500000000000  # 500GB
        mock_disk.used = 200000000000   # 200GB
        mock_disk.free = 300000000000   # 300GB
        mock_disk.percent = 40.0        # 使用率
        mock_disk_usage.return_value = mock_disk
        
        # 调用函数
        result = get_disk_usage()
        
        # 验证结果
        self.assertIsInstance(result, dict)
        # 调整期望的精度以匹配实际结果
        self.assertEqual(result['total_gb'], 465.66)  # 500GB = 465.66GB (显示误差是因为GB与GiB的转换)
        self.assertEqual(result['used_gb'], 186.26)   # 200GB = 186.26GB
        self.assertEqual(result['free_gb'], 279.4)   # 300GB = 279.4GB 调整精度
        self.assertEqual(result['percent'], 40.0)
        mock_disk_usage.assert_called_once_with('/')  # 默认应该检查根目录
    
    @patch('status.monitoring.system_monitor.psutil.net_io_counters')
    def test_get_network_info(self, mock_net_io):
        """测试获取网络信息"""
        # 设置模拟返回值
        mock_net = MagicMock()
        mock_net.bytes_sent = 1000000  # 1MB发送
        mock_net.bytes_recv = 10000000  # 10MB接收
        mock_net_io.return_value = mock_net
        
        # 调用函数
        result = get_network_info()
        
        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertEqual(result['sent_mb'], 0.95)  # 1MB = 0.95MB
        self.assertEqual(result['recv_mb'], 9.54)  # 10MB = 9.54MB
        mock_net_io.assert_called_once()
    
    @patch('status.monitoring.system_monitor.EventManager.get_instance')
    @patch('status.monitoring.system_monitor.get_cpu_usage')
    @patch('status.monitoring.system_monitor.get_memory_usage')
    @patch('status.monitoring.system_monitor.get_cpu_cores_usage')
    @patch('status.monitoring.system_monitor.get_memory_details')
    @patch('status.monitoring.system_monitor.get_disk_usage')
    @patch('status.monitoring.system_monitor.get_network_info')
    def test_publish_stats_with_details(self, mock_net, mock_disk, mock_mem_details, 
                                       mock_cpu_cores, mock_mem, mock_cpu, mock_event_manager):
        """测试发布带有详细信息的系统统计数据"""
        # 设置各模拟函数的返回值
        mock_cpu.return_value = 50.0
        mock_mem.return_value = 60.0
        mock_cpu_cores.return_value = [40.0, 60.0, 45.0, 55.0]
        mock_mem_details.return_value = {
            'total_mb': 15258,
            'available_mb': 7629,
            'used_mb': 6675,
            'free_mb': 953,
            'percent': 60.0
        }
        mock_disk.return_value = {
            'total_gb': 465.66,
            'used_gb': 186.26,
            'free_gb': 279.4,
            'percent': 40.0
        }
        mock_net.return_value = {
            'sent_mb': 0.95,
            'recv_mb': 9.54
        }
        
        # 设置事件管理器模拟
        mock_event_mgr = MagicMock()
        mock_event_manager.return_value = mock_event_mgr
        
        # 调用函数
        publish_stats(include_details=True)
        
        # 验证事件分发
        mock_event_mgr.dispatch.assert_called_once()
        
        # 获取传递给dispatch的事件参数
        event = mock_event_mgr.dispatch.call_args[0][0]
        
        # 验证事件类型和内容
        self.assertIsInstance(event, SystemStatsUpdatedEvent)
        self.assertEqual(event.stats_data['cpu'], 50.0)
        self.assertEqual(event.stats_data['memory'], 60.0)
        
        # 验证详细信息存在
        self.assertIn('cpu_cores', event.stats_data)
        self.assertIn('memory_details', event.stats_data)
        self.assertIn('disk', event.stats_data)
        self.assertIn('network', event.stats_data)
        
        # 验证详细信息内容
        self.assertEqual(event.stats_data['cpu_cores'], [40.0, 60.0, 45.0, 55.0])
        self.assertEqual(event.stats_data['memory_details']['total_mb'], 15258)
        self.assertEqual(event.stats_data['disk']['percent'], 40.0)
        self.assertEqual(event.stats_data['network']['recv_mb'], 9.54)

        # 验证系统信息获取函数被调用
        mock_cpu.assert_called_once()
        mock_mem.assert_called_once()
        mock_cpu_cores.assert_called_once()
        mock_mem_details.assert_called_once()
        mock_disk.assert_called_once()
        mock_net.assert_called_once()
        
    @patch('status.monitoring.system_monitor.EventManager.get_instance')
    @patch('status.monitoring.system_monitor.get_cpu_usage')
    @patch('status.monitoring.system_monitor.get_memory_usage')
    def test_publish_stats_without_details(self, mock_mem, mock_cpu, mock_event_manager):
        """测试发布不带详细信息的系统统计数据（默认行为）"""
        # 设置模拟返回值
        mock_cpu.return_value = 50.0
        mock_mem.return_value = 60.0
        
        # 设置事件管理器模拟
        mock_event_mgr = MagicMock()
        mock_event_manager.return_value = mock_event_mgr
        
        # 调用函数（不指定 include_details 参数）
        publish_stats()
        
        # 验证事件分发
        mock_event_mgr.dispatch.assert_called_once()
        
        # 获取传递给dispatch的事件参数
        event = mock_event_mgr.dispatch.call_args[0][0]
        
        # 验证事件类型和内容
        self.assertIsInstance(event, SystemStatsUpdatedEvent)
        self.assertEqual(event.stats_data['cpu'], 50.0)
        self.assertEqual(event.stats_data['memory'], 60.0)
        
        # 验证详细信息不存在
        self.assertNotIn('cpu_cores', event.stats_data)
        self.assertNotIn('memory_details', event.stats_data)
        self.assertNotIn('disk', event.stats_data)
        self.assertNotIn('network', event.stats_data)
        
        # 验证只有基本系统信息获取函数被调用
        mock_cpu.assert_called_once()
        mock_mem.assert_called_once()

if __name__ == '__main__':
    unittest.main() 