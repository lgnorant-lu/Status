"""
---------------------------------------------------------------
File name:                  test_system_monitor.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                测试系统监控功能，特别是CPU使用率获取
----------------------------------------------------------------
"""

import unittest
import os
import sys
from unittest.mock import patch, MagicMock
import psutil # 实际测试范围时需要

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from status.monitoring.system_monitor import get_cpu_usage, get_memory_usage

class TestSystemMonitor(unittest.TestCase):
    """测试系统监控功能"""

    def test_get_cpu_usage_returns_float(self):
        """测试 get_cpu_usage 是否返回浮点数"""
        with patch('psutil.cpu_percent') as mock_cpu_percent:
            mock_cpu_percent.return_value = 10.5
            cpu_usage = get_cpu_usage()
            self.assertIsInstance(cpu_usage, float, "CPU使用率应该是一个浮点数")

    def test_get_cpu_usage_range(self):
        """测试 get_cpu_usage 返回值是否在 0 到 100 之间"""
        with patch('psutil.cpu_percent') as mock_cpu_percent:
            for val in [0.0, 50.0, 100.0]:
                mock_cpu_percent.return_value = val
                cpu_usage = get_cpu_usage()
                self.assertGreaterEqual(cpu_usage, 0.0, f"CPU使用率 {cpu_usage} 不能小于 0")
                self.assertLessEqual(cpu_usage, 100.0, f"CPU使用率 {cpu_usage} 不能大于 100")

    @patch('status.monitoring.system_monitor.psutil.cpu_percent')
    def test_get_cpu_usage_calls_psutil(self, mock_cpu_percent):
        """测试 get_cpu_usage 是否正确调用 psutil.cpu_percent 并返回其值"""
        mock_value = 15.5
        mock_cpu_percent.return_value = mock_value

        cpu_usage = get_cpu_usage()

        mock_cpu_percent.assert_called_once_with(interval=None)

        self.assertEqual(cpu_usage, mock_value, "返回值应等于 psutil.cpu_percent 的返回值")

    # --- 新增内存监控测试 ---
    def test_get_memory_usage_returns_float(self):
        """测试 get_memory_usage 是否返回浮点数"""
        mem_usage = get_memory_usage()
        self.assertIsInstance(mem_usage, float)

    def test_get_memory_usage_range(self):
        """测试 get_memory_usage 返回值是否在 0 到 100 之间"""
        mem_usage = get_memory_usage()
        self.assertTrue(0.0 <= mem_usage <= 100.0)

    @patch('status.monitoring.system_monitor.psutil.virtual_memory')
    def test_get_memory_usage_calls_psutil(self, mock_virtual_memory):
        """测试 get_memory_usage 是否正确调用 psutil"""
        # 设置模拟对象的返回值
        mock_vm_instance = MagicMock()
        mock_vm_instance.percent = 42.5
        mock_virtual_memory.return_value = mock_vm_instance

        result = get_memory_usage()

        # 断言 psutil.virtual_memory() 被调用一次
        mock_virtual_memory.assert_called_once()
        # 断言返回了模拟的百分比
        self.assertEqual(result, 42.5)

if __name__ == '__main__':
    unittest.main() 