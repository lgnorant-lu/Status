"""
---------------------------------------------------------------
File name:                  test_system_info.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                系统信息收集模块测试
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import unittest
import time
from unittest.mock import Mock, patch, MagicMock

from status.monitoring.system_info import SystemInfo


class TestSystemInfo(unittest.TestCase):
    """测试系统信息收集类"""
    
    def setUp(self):
        """测试前准备"""
        # 重置单例
        SystemInfo._instance = None
        SystemInfo._instance_initialized = False
        
        # 创建假的psutil模块
        self.mock_psutil = Mock()
        self.mock_psutil.cpu_percent.return_value = 25.5
        self.mock_psutil.cpu_count.return_value = 4
        
        # 创建内存信息Mock
        mock_virtual_memory = MagicMock()
        mock_virtual_memory._asdict.return_value = {
            "total": 8589934592,  # 8GB
            "available": 4294967296,  # 4GB
            "percent": 50.0,
            "used": 4294967296,  # 4GB
            "free": 4294967296,  # 4GB
        }
        self.mock_psutil.virtual_memory.return_value = mock_virtual_memory
        
        # 创建交换内存信息Mock
        mock_swap_memory = MagicMock()
        mock_swap_memory._asdict.return_value = {
            "total": 2147483648,  # 2GB
            "used": 0,
            "free": 2147483648,  # 2GB
            "percent": 0.0,
        }
        self.mock_psutil.swap_memory.return_value = mock_swap_memory
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        # 创建两个实例
        instance1 = SystemInfo()
        instance2 = SystemInfo()
        
        # 验证它们是相同的实例
        self.assertIs(instance1, instance2)
    
    @patch('status.monitoring.system_info.psutil', None)
    def test_init_without_psutil(self):
        """测试在没有psutil的情况下初始化"""
        # 创建实例
        system_info = SystemInfo()
        
        # 验证基本信息仍然可以获取
        basic_info = system_info.get_basic_info()
        self.assertIn('system', basic_info)
        self.assertIn('platform', basic_info)
        self.assertIn('python_version', basic_info)
    
    @patch('status.monitoring.system_info.psutil')
    def test_get_basic_info(self, mock_psutil):
        """测试获取基本系统信息"""
        # 设置mock
        mock_psutil.cpu_count.side_effect = lambda logical: 8 if logical else 4
        
        # 创建实例
        system_info = SystemInfo()
        
        # 获取基本信息
        basic_info = system_info.get_basic_info()
        
        # 验证结果
        self.assertIn('system', basic_info)
        self.assertIn('platform', basic_info)
        self.assertIn('python_version', basic_info)
        self.assertIn('cpu_count_physical', basic_info)
        self.assertIn('cpu_count_logical', basic_info)
        self.assertEqual(basic_info['cpu_count_physical'], 4)
        self.assertEqual(basic_info['cpu_count_logical'], 8)
    
    @patch('status.monitoring.system_info.psutil')
    def test_get_cpu_info(self, mock_psutil):
        """测试获取CPU信息"""
        # 设置mock
        mock_psutil.cpu_percent.side_effect = [25.0, [20.0, 30.0, 25.0, 35.0]]
        
        mock_cpu_times = MagicMock()
        mock_cpu_times._asdict.return_value = {
            "user": 10000.0,
            "system": 5000.0,
            "idle": 50000.0,
        }
        mock_psutil.cpu_times.return_value = mock_cpu_times
        
        mock_cpu_stats = MagicMock()
        mock_cpu_stats._asdict.return_value = {
            "ctx_switches": 100000,
            "interrupts": 50000,
            "soft_interrupts": 25000,
            "syscalls": 75000,
        }
        mock_psutil.cpu_stats.return_value = mock_cpu_stats
        
        mock_cpu_freq = MagicMock()
        mock_cpu_freq._asdict.return_value = {
            "current": 2500.0,
            "min": 1200.0,
            "max": 3500.0,
        }
        mock_psutil.cpu_freq.return_value = mock_cpu_freq
        
        # 创建实例
        system_info = SystemInfo()
        
        # 获取CPU信息
        cpu_info = system_info.get_cpu_info()
        
        # 验证结果
        self.assertIn('percent_overall', cpu_info)
        self.assertIn('percent_per_cpu', cpu_info)
        self.assertIn('times', cpu_info)
        self.assertIn('stats', cpu_info)
        self.assertIn('freq', cpu_info)
        
        self.assertEqual(cpu_info['percent_overall'], 25.0)
        self.assertEqual(len(cpu_info['percent_per_cpu']), 4)
        self.assertEqual(cpu_info['times']['user'], 10000.0)
        self.assertEqual(cpu_info['stats']['ctx_switches'], 100000)
        self.assertEqual(cpu_info['freq']['current'], 2500.0)
    
    @patch('status.monitoring.system_info.psutil')
    def test_get_memory_info(self, mock_psutil):
        """测试获取内存信息"""
        # 设置mock
        mock_virtual_memory = MagicMock()
        mock_virtual_memory._asdict.return_value = {
            "total": 8589934592,  # 8GB
            "available": 4294967296,  # 4GB
            "percent": 50.0,
            "used": 4294967296,  # 4GB
            "free": 4294967296,  # 4GB
        }
        mock_psutil.virtual_memory.return_value = mock_virtual_memory
        
        mock_swap_memory = MagicMock()
        mock_swap_memory._asdict.return_value = {
            "total": 2147483648,  # 2GB
            "used": 0,
            "free": 2147483648,  # 2GB
            "percent": 0.0,
        }
        mock_psutil.swap_memory.return_value = mock_swap_memory
        
        # 创建实例
        system_info = SystemInfo()
        
        # 获取内存信息
        memory_info = system_info.get_memory_info()
        
        # 验证结果
        self.assertIn('virtual', memory_info)
        self.assertIn('swap', memory_info)
        self.assertIn('percent', memory_info)
        self.assertIn('total_gb', memory_info)
        self.assertIn('available_gb', memory_info)
        self.assertIn('used_gb', memory_info)
        
        self.assertEqual(memory_info['percent'], 50.0)
        self.assertEqual(memory_info['total_gb'], 8.0)
        self.assertEqual(memory_info['available_gb'], 4.0)
        self.assertEqual(memory_info['used_gb'], 4.0)
        self.assertEqual(memory_info['swap']['percent'], 0.0)
    
    @patch('status.monitoring.system_info.psutil')
    def test_update_metrics(self, mock_psutil):
        """测试更新所有系统指标"""
        # 创建实例并打补丁方法
        system_info = SystemInfo()
        system_info.get_cpu_info = Mock(return_value={"percent_overall": 30.0})
        system_info.get_memory_info = Mock(return_value={"percent": 45.0})
        system_info.get_disk_info = Mock(return_value={"partitions": []})
        system_info.get_network_info = Mock(return_value={"io_counters": {}})
        system_info.get_battery_info = Mock(return_value={"percent": 75.0})
        system_info._send_update_event = Mock()
        
        # 更新指标
        metrics = system_info.update_metrics()
        
        # 验证结果
        self.assertIn('cpu', metrics)
        self.assertIn('memory', metrics)
        self.assertIn('disk', metrics)
        self.assertIn('network', metrics)
        self.assertIn('battery', metrics)
        
        self.assertEqual(metrics['cpu']['percent_overall'], 30.0)
        self.assertEqual(metrics['memory']['percent'], 45.0)
        self.assertEqual(metrics['battery']['percent'], 75.0)
        
        # 验证方法被调用
        system_info.get_cpu_info.assert_called_once()
        system_info.get_memory_info.assert_called_once()
        system_info.get_disk_info.assert_called_once()
        system_info.get_network_info.assert_called_once()
        system_info.get_battery_info.assert_called_once()
        system_info._send_update_event.assert_called_once()
    
    @patch('status.monitoring.system_info.threading.Thread')
    def test_start_stop_auto_update(self, mock_thread):
        """测试启动和停止自动更新"""
        # 创建实例
        system_info = SystemInfo()
        
        # 启动自动更新
        result = system_info.start_auto_update()
        self.assertTrue(result)
        self.assertTrue(system_info.auto_update_enabled)
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()
        
        # 再次启动应该返回False
        result = system_info.start_auto_update()
        self.assertFalse(result)
        
        # 停止自动更新
        mock_thread.return_value.is_alive.return_value = True
        result = system_info.stop_auto_update()
        self.assertTrue(result)
        self.assertFalse(system_info.auto_update_enabled)
        mock_thread.return_value.join.assert_called_once()
        
        # 再次停止应该返回False
        result = system_info.stop_auto_update()
        self.assertFalse(result)
    
    def test_set_update_interval(self):
        """测试设置更新间隔"""
        # 创建实例
        system_info = SystemInfo(update_interval=1.0)
        self.assertEqual(system_info.update_interval, 1.0)
        
        # 设置有效值
        system_info.set_update_interval(2.5)
        self.assertEqual(system_info.update_interval, 2.5)
        
        # 设置无效值
        system_info.set_update_interval(0)
        self.assertEqual(system_info.update_interval, 2.5)  # 应该保持不变
        
        system_info.set_update_interval(-1)
        self.assertEqual(system_info.update_interval, 2.5)  # 应该保持不变


if __name__ == '__main__':
    unittest.main() 