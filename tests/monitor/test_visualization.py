"""
---------------------------------------------------------------
File name:                  test_visualization.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                可视化映射器测试
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import unittest
from unittest.mock import patch, MagicMock
import logging

from status.monitor.visualization import VisualMapper


class TestVisualMapper(unittest.TestCase):
    """测试可视化映射器"""

    def setUp(self):
        """测试前的准备工作"""
        # 配置日志
        logging.basicConfig(level=logging.CRITICAL)
        
        # 创建可视化映射器实例
        self.mapper = VisualMapper()
        
    def test_init(self):
        """测试初始化"""
        # 默认配置初始化
        mapper = VisualMapper()
        self.assertIsNotNone(mapper)
        self.assertIsInstance(mapper.config, dict)
        
        # 自定义配置初始化
        config = {
            "color_scheme": "dark",
            "enable_animations": True,
            "indicator_style": "modern"
        }
        mapper = VisualMapper(config)
        self.assertEqual(mapper.config["color_scheme"], "dark")
        self.assertEqual(mapper.config["enable_animations"], True)
        self.assertEqual(mapper.config["indicator_style"], "modern")
        
    def test_update_config(self):
        """测试更新配置"""
        # 初始配置
        self.mapper.config = {
            "color_scheme": "light",
            "enable_animations": False,
            "animation_speed": 1.0
        }
        
        # 更新部分配置
        self.mapper.update_config({
            "color_scheme": "dark",
            "new_option": "value"
        })
        
        # 检查配置是否正确更新
        self.assertEqual(self.mapper.config["color_scheme"], "dark")
        self.assertEqual(self.mapper.config["enable_animations"], False)  # 保持不变
        self.assertEqual(self.mapper.config["animation_speed"], 1.0)  # 保持不变
        self.assertEqual(self.mapper.config["new_option"], "value")  # 新增配置
        
    def test_merge_configurations(self):
        """测试配置合并"""
        # 基础配置
        base_config = {
            "option1": "value1",
            "option2": {
                "sub1": "subvalue1",
                "sub2": "subvalue2"
            },
            "option3": [1, 2, 3]
        }
        
        # 新配置
        new_config = {
            "option1": "new_value",
            "option2": {
                "sub1": "new_subvalue",
                "sub3": "subvalue3"
            },
            "option4": True
        }
        
        # 合并配置
        merged = self.mapper._merge_config(base_config, new_config)
        
        # 验证结果
        self.assertEqual(merged["option1"], "new_value")  # 被覆盖
        self.assertEqual(merged["option2"]["sub1"], "new_subvalue")  # 被覆盖
        self.assertEqual(merged["option2"]["sub2"], "subvalue2")  # 保持不变
        self.assertEqual(merged["option2"]["sub3"], "subvalue3")  # 新增
        self.assertEqual(merged["option3"], [1, 2, 3])  # 保持不变
        self.assertEqual(merged["option4"], True)  # 新增
        
    def test_get_color_scheme(self):
        """测试获取配色方案"""
        # 配置默认配色方案
        self.mapper.config["color_scheme"] = "light"
        
        # 获取配色方案
        colors = self.mapper.get_color_scheme("normal")
        
        # 验证结果
        self.assertIsInstance(colors, dict)
        self.assertIn("primary", colors)
        self.assertIn("secondary", colors)
        self.assertIn("text", colors)
        
        # 测试未知状态
        colors = self.mapper.get_color_scheme("unknown_status")
        # 应该返回默认配色方案
        self.assertIsInstance(colors, dict)
        self.assertIn("primary", colors)
        
    def test_get_animation_config(self):
        """测试获取动画配置"""
        # 获取动画配置
        animation = self.mapper.get_animation_for_status("normal")
        
        # 验证结果
        self.assertIsInstance(animation, dict)
        self.assertIn("speed", animation)
        self.assertIn("scale", animation)
        self.assertIn("effects", animation)
        
        # 测试警告状态
        animation = self.mapper.get_animation_for_status("warning")
        self.assertIn("speed", animation)
        self.assertNotEqual(animation["effects"], [])  # 警告应该有特效
        
        # 测试未知状态
        animation = self.mapper.get_animation_for_status("unknown_status")
        # 应该返回默认动画配置
        self.assertIsInstance(animation, dict)
        self.assertIn("speed", animation)
        
    def test_map_cpu_data(self):
        """测试映射CPU数据到可视化"""
        # 处理后的CPU数据
        cpu_data = {
            'usage': 65.0,
            'status': 'normal',
            'load_level': 0.65,
            'core_count': 4
        }
        
        # 测试假设函数存在，目前实现中没有单独的映射CPU数据的方法
        self.skipTest("VisualMapper中没有单独的映射CPU数据的方法")
        
    def test_map_memory_data(self):
        """测试映射内存数据到可视化"""
        # 处理后的内存数据
        memory_data = {
            'percent': 75.0,
            'status': 'warning',
            'usage_level': 0.75,
            'total_gb': 16.0,
            'used_gb': 12.0
        }
        
        # 测试假设函数存在，目前实现中没有单独的映射内存数据的方法
        self.skipTest("VisualMapper中没有单独的映射内存数据的方法")
        
    def test_map_disk_data(self):
        """测试映射磁盘数据到可视化"""
        # 处理后的磁盘数据
        disk_data = {
            'percent': 85.0,
            'status': 'warning',
            'usage_level': 0.85,
            'total_gb': 500.0,
            'used_gb': 425.0,
            'disks': {
                'C:': {'total_gb': 250.0, 'used_gb': 220.0, 'percent': 88.0},
                'D:': {'total_gb': 250.0, 'used_gb': 205.0, 'percent': 82.0}
            }
        }
        
        # 测试假设函数存在，目前实现中没有单独的映射磁盘数据的方法
        self.skipTest("VisualMapper中没有单独的映射磁盘数据的方法")
        
    def test_map_network_data(self):
        """测试映射网络数据到可视化"""
        # 处理后的网络数据
        network_data = {
            'upload_mb_per_sec': 1.2,
            'download_mb_per_sec': 3.5,
            'network_load': 0.25,
            'connections': 120,
            'status': 'normal'
        }
        
        # 测试假设函数存在，目前实现中没有单独的映射网络数据的方法
        self.skipTest("VisualMapper中没有单独的映射网络数据的方法")
        
    def test_map_to_visual(self):
        """测试映射完整数据集到可视化"""
        # 处理后的完整数据集
        processed_data = {
            'cpu': {
                'usage': 65.0,
                'status': 'normal',
                'load_level': 0.65,
                'core_count': 4
            },
            'memory': {
                'percent': 75.0,
                'status': 'warning',
                'usage_level': 0.75,
                'total_gb': 16.0,
                'used_gb': 12.0
            },
            'disk': {
                'percent': 85.0,
                'status': 'warning',
                'usage_level': 0.85,
                'total_gb': 500.0,
                'used_gb': 425.0
            },
            'network': {
                'upload_mb_per_sec': 1.2,
                'download_mb_per_sec': 3.5,
                'network_load': 0.25,
                'connections': 120,
                'status': 'normal'
            },
            'system': {
                'overall_status': 'warning',
                'overall_load': 0.7,
                'alerts': [
                    {'level': 'warning', 'source': 'memory', 'message': '内存使用率超过75%'}
                ]
            }
        }
        
        # 映射完整数据集
        visual = self.mapper.map_data(processed_data)
        
        # 验证结果
        self.assertIsInstance(visual, dict)
        # 检查映射输出包含预期的关键部分
        self.assertIn('indicators', visual)
        self.assertIn('cpu', visual['indicators'])
        self.assertIn('memory', visual['indicators'])
        self.assertIn('disk', visual['indicators'])
        self.assertIn('network', visual['indicators'])
        self.assertIn('tooltips', visual)
        self.assertIn('alerts', visual)
        self.assertIn('summary', visual)
        
    def test_map_to_visual_with_empty_data(self):
        """测试映射空数据到可视化"""
        # 空数据
        processed_data = {}
        
        # 映射空数据
        visual = self.mapper.map_data(processed_data)
        
        # 验证结果
        self.assertIsInstance(visual, dict)
        self.assertIn('error', visual)
        
    def test_get_color_for_status(self):
        """测试根据状态获取颜色"""
        # 正常状态
        status = 'normal'
        color = self.mapper.get_color_for_metric('cpu', 0.5)
        
        # 验证结果
        self.assertIsNotNone(color)
        self.assertTrue(isinstance(color, str))
        
        # 警告状态
        color = self.mapper.get_color_for_metric('cpu', 0.8)
        
        # 验证结果
        self.assertIsNotNone(color)
        self.assertTrue(isinstance(color, str))
        
        # 危险状态
        color = self.mapper.get_color_for_metric('cpu', 0.95)
        
        # 验证结果
        self.assertIsNotNone(color)
        self.assertTrue(isinstance(color, str))
        
    def test_get_animation_for_status(self):
        """测试根据状态获取动画效果"""
        # 正常状态
        animation = self.mapper.get_animation_for_status('normal')
        
        # 验证结果
        self.assertIsInstance(animation, dict)
        self.assertIn('speed', animation)
        self.assertIn('scale', animation)
        self.assertIn('effects', animation)
        
        # 警告状态
        animation = self.mapper.get_animation_for_status('warning')
        
        # 验证结果
        self.assertIsInstance(animation, dict)
        self.assertIn('speed', animation)
        
        # 危险状态
        animation = self.mapper.get_animation_for_status('danger')
        
        # 验证结果
        self.assertIsInstance(animation, dict)
        self.assertTrue(animation['speed'] > 1.0)  # 危险状态应该加速
        
    def test_get_indicator_style(self):
        """测试获取指示器样式"""
        # 目前VisualMapper没有单独的获取指示器样式的方法
        self.skipTest("VisualMapper中没有单独的获取指示器样式的方法")
        
    def tearDown(self):
        """测试结束后的清理工作"""
        pass


if __name__ == '__main__':
    unittest.main() 