"""
---------------------------------------------------------------
File name:                  test_interaction_tracker.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                InteractionTracker单元测试
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建;
----
"""

import unittest
from unittest.mock import patch, MagicMock
import time
import os
import tempfile
import json
import shutil

from status.behavior.interaction_tracker import InteractionTracker, InteractionPattern
from status.interaction.interaction_zones import InteractionType


class TestInteractionTracker(unittest.TestCase):
    """InteractionTracker单元测试"""
    
    def setUp(self):
        """每个测试前的设置"""
        # 创建临时目录用于测试数据存储
        self.temp_dir = tempfile.mkdtemp()
        self.storage_file = "test_interaction_history.json"
        
        # 模拟事件系统
        with patch('status.core.event_system.EventSystem') as mock_event_system:
            mock_instance = MagicMock()
            mock_event_system.get_instance.return_value = mock_instance
            
            # 创建测试对象
            self.tracker = InteractionTracker(
                decay_factor=0.5, 
                storage_file=self.storage_file,
                storage_dir=self.temp_dir
            )
            
            # 存储mock对象
            self.mock_event_system = mock_instance
    
    def tearDown(self):
        """每个测试后的清理"""
        # 删除临时目录
        shutil.rmtree(self.temp_dir)
    
    def test_track_interaction(self):
        """测试记录交互"""
        # 记录一次交互
        self.tracker.track_interaction(InteractionType.CLICK, "test_zone")
        
        # 验证交互记录
        self.assertIn("CLICK", self.tracker.interaction_history)
        self.assertIn("test_zone", self.tracker.interaction_history["CLICK"])
        self.assertEqual(len(self.tracker.interaction_history["CLICK"]["test_zone"]), 1)
        
        # 记录多次交互
        self.tracker.track_interaction(InteractionType.CLICK, "test_zone")
        self.tracker.track_interaction(InteractionType.CLICK, "test_zone")
        
        # 验证交互计数
        self.assertEqual(self.tracker.interaction_counts["CLICK"]["test_zone"], 3)
        
        # 测试使用字符串交互类型
        self.tracker.track_interaction("HOVER", "test_zone")
        self.assertIn("HOVER", self.tracker.interaction_history)
        self.assertEqual(self.tracker.interaction_counts["HOVER"]["test_zone"], 1)
    
    def test_get_interaction_count(self):
        """测试获取交互次数"""
        # 记录多次交互
        for _ in range(5):
            self.tracker.track_interaction(InteractionType.CLICK, "test_zone")
        
        # 获取总交互次数
        count = self.tracker.get_interaction_count(InteractionType.CLICK, "test_zone")
        self.assertEqual(count, 5)
        
        # 获取不存在的交互类型
        count = self.tracker.get_interaction_count(InteractionType.DRAG, "test_zone")
        self.assertEqual(count, 0)
        
        # 获取不存在的区域
        count = self.tracker.get_interaction_count(InteractionType.CLICK, "non_existent")
        self.assertEqual(count, 0)
        
        # 测试时间窗口过滤
        now = time.time()
        
        # 修改一条交互记录的时间戳为过去时间（超出窗口）
        self.tracker.interaction_history["CLICK"]["test_zone"][0] = now - 3600  # 1小时前
        
        # 获取最近30分钟的交互次数
        count = self.tracker.get_interaction_count(InteractionType.CLICK, "test_zone", 30 * 60)
        self.assertEqual(count, 4)  # 应该只有4条在30分钟内
    
    def test_interaction_decay(self):
        """测试交互衰减"""
        # 记录交互
        self.tracker.track_interaction(InteractionType.CLICK, "test_zone")
        
        # 修改交互时间为过去的时间
        now = time.time()
        day_ago = now - 25 * 3600  # 25小时前（超过24小时衰减阈值）
        self.tracker.interaction_history["CLICK"]["test_zone"] = [day_ago]
        self.tracker.interaction_counts["CLICK"]["test_zone"] = 1
        
        # 再次记录交互，触发衰减
        self.tracker.track_interaction(InteractionType.CLICK, "test_zone")
        
        # 应该只保留新的交互记录
        self.assertEqual(len(self.tracker.interaction_history["CLICK"]["test_zone"]), 1)
        self.assertEqual(self.tracker.interaction_counts["CLICK"]["test_zone"], 1)
        self.assertGreater(self.tracker.interaction_history["CLICK"]["test_zone"][0], day_ago)
    
    def test_interaction_frequency(self):
        """测试交互频率计算"""
        # 记录多次交互
        for _ in range(20):
            self.tracker.track_interaction(InteractionType.CLICK, "test_zone")
        
        # 获取每小时频率
        frequency = self.tracker.get_interaction_frequency(InteractionType.CLICK, "test_zone")
        self.assertEqual(frequency, 20.0)  # 20次/小时
        
        # 获取每半小时频率
        frequency = self.tracker.get_interaction_frequency(InteractionType.CLICK, "test_zone", 0.5)
        self.assertEqual(frequency, 40.0)  # 20次/0.5小时 = 40次/小时
        
        # 修改一部分交互记录的时间戳为过去时间
        now = time.time()
        self.tracker.interaction_history["CLICK"]["test_zone"][0:10] = [now - 3600] * 10  # 前10条设为1小时前
        
        # 获取最近半小时的频率（修正错误：删除了多余的time_window参数）
        frequency = self.tracker.get_interaction_frequency(
            InteractionType.CLICK, "test_zone", 0.5
        )
        self.assertEqual(frequency, 40.0)  # 频率计算基于时间窗口，不是基于历史记录
    
    def test_interaction_pattern(self):
        """测试交互模式判断"""
        # 无交互 - RARE
        pattern = self.tracker.get_interaction_pattern(InteractionType.CLICK, "test_zone")
        self.assertEqual(pattern, InteractionPattern.RARE)
        
        # 记录少量交互 - OCCASIONAL
        for _ in range(3):
            self.tracker.track_interaction(InteractionType.CLICK, "test_zone")
        pattern = self.tracker.get_interaction_pattern(InteractionType.CLICK, "test_zone")
        self.assertEqual(pattern, InteractionPattern.OCCASIONAL)
        
        # 记录更多交互 - REGULAR
        for _ in range(7):
            self.tracker.track_interaction(InteractionType.CLICK, "test_zone")
        pattern = self.tracker.get_interaction_pattern(InteractionType.CLICK, "test_zone")
        self.assertEqual(pattern, InteractionPattern.REGULAR)
        
        # 记录大量交互 - FREQUENT
        for _ in range(10):
            self.tracker.track_interaction(InteractionType.CLICK, "test_zone")
        pattern = self.tracker.get_interaction_pattern(InteractionType.CLICK, "test_zone")
        self.assertEqual(pattern, InteractionPattern.FREQUENT)
        
        # 记录过量交互 - EXCESSIVE
        for _ in range(20):
            self.tracker.track_interaction(InteractionType.CLICK, "test_zone")
        pattern = self.tracker.get_interaction_pattern(InteractionType.CLICK, "test_zone")
        self.assertEqual(pattern, InteractionPattern.EXCESSIVE)
    
    def test_zones_tracking(self):
        """测试多区域交互追踪"""
        # 记录不同区域的交互
        self.tracker.track_interaction(InteractionType.CLICK, "zone1")
        self.tracker.track_interaction(InteractionType.CLICK, "zone2")
        self.tracker.track_interaction(InteractionType.HOVER, "zone1")
        
        # 获取所有区域
        zones = self.tracker.get_all_zones()
        self.assertEqual(len(zones), 2)
        self.assertIn("zone1", zones)
        self.assertIn("zone2", zones)
        
        # 获取特定交互类型的区域
        click_zones = self.tracker.get_all_zones(InteractionType.CLICK)
        self.assertEqual(len(click_zones), 2)
        
        hover_zones = self.tracker.get_all_zones(InteractionType.HOVER)
        self.assertEqual(len(hover_zones), 1)
        self.assertEqual(hover_zones[0], "zone1")
        
        # 获取不存在交互类型的区域
        drag_zones = self.tracker.get_all_zones(InteractionType.DRAG)
        self.assertEqual(len(drag_zones), 0)
    
    def test_persist_interaction_data(self):
        """测试持久化交互数据"""
        # 记录一些交互
        self.tracker.track_interaction(InteractionType.CLICK, "test_zone")
        self.tracker.track_interaction(InteractionType.HOVER, "test_zone")
        
        # 保存数据
        result = self.tracker.persist_interaction_data()
        self.assertTrue(result)
        
        # 验证文件已创建
        storage_path = os.path.join(self.temp_dir, self.storage_file)
        self.assertTrue(os.path.exists(storage_path))
        
        # 验证文件内容
        with open(storage_path, 'r') as f:
            data = json.load(f)
            
        self.assertIn("interaction_history", data)
        self.assertIn("CLICK", data["interaction_history"])
        self.assertIn("HOVER", data["interaction_history"])
    
    def test_load_interaction_data(self):
        """测试加载交互数据"""
        # 创建测试数据
        test_data = {
            "interaction_history": {
                "CLICK": {
                    "test_zone": [time.time()]
                }
            },
            "interaction_counts": {
                "CLICK": {
                    "test_zone": 1
                }
            },
            "last_updated": time.time()
        }
        
        # 保存测试数据
        storage_path = os.path.join(self.temp_dir, self.storage_file)
        with open(storage_path, 'w') as f:
            json.dump(test_data, f)
        
        # 创建新的跟踪器实例
        with patch('status.core.event_system.EventSystem') as mock_event_system:
            mock_instance = MagicMock()
            mock_event_system.get_instance.return_value = mock_instance
            
            tracker = InteractionTracker(
                storage_file=self.storage_file,
                storage_dir=self.temp_dir
            )
        
        # 验证数据已加载
        self.assertIn("CLICK", tracker.interaction_history)
        self.assertIn("test_zone", tracker.interaction_history["CLICK"])
        self.assertEqual(tracker.interaction_counts["CLICK"]["test_zone"], 1)
    
    def test_clear_interaction_data(self):
        """测试清除交互数据"""
        # 记录多个交互类型和区域的交互
        self.tracker.track_interaction(InteractionType.CLICK, "zone1")
        self.tracker.track_interaction(InteractionType.CLICK, "zone2")
        self.tracker.track_interaction(InteractionType.HOVER, "zone1")
        
        # 清除特定类型和区域的数据
        self.tracker.clear_interaction_data(InteractionType.CLICK, "zone1")
        
        # 验证清除结果
        self.assertNotIn("zone1", self.tracker.interaction_history["CLICK"])
        self.assertIn("zone2", self.tracker.interaction_history["CLICK"])
        self.assertIn("zone1", self.tracker.interaction_history["HOVER"])
        
        # 清除整个交互类型的数据
        self.tracker.clear_interaction_data(InteractionType.HOVER)
        
        # 验证清除结果
        self.assertNotIn("HOVER", self.tracker.interaction_history)
        
        # 清除特定区域的所有数据
        self.tracker.track_interaction(InteractionType.DRAG, "zone2")
        self.tracker.clear_interaction_data(zone_id="zone2")
        
        # 验证清除结果
        self.assertNotIn("zone2", self.tracker.interaction_history["CLICK"])
        self.assertNotIn("zone2", self.tracker.interaction_history["DRAG"])
        
        # 清除所有数据
        self.tracker.track_interaction(InteractionType.CLICK, "zone3")
        self.tracker.clear_interaction_data()
        
        # 验证清除结果
        self.assertEqual(len(self.tracker.interaction_history), 0)
        self.assertEqual(len(self.tracker.interaction_counts), 0)
    
    def test_multiple_interaction_types(self):
        """测试多种交互类型"""
        # 记录多种交互类型
        interaction_types = [
            InteractionType.CLICK,
            InteractionType.DOUBLE_CLICK,
            InteractionType.RIGHT_CLICK,
            InteractionType.HOVER,
            InteractionType.DRAG,
            InteractionType.DROP
        ]
        
        for interaction_type in interaction_types:
            self.tracker.track_interaction(interaction_type, "test_zone")
        
        # 获取所有交互类型
        tracked_types = self.tracker.get_all_interaction_types()
        self.assertEqual(len(tracked_types), len(interaction_types))
        
        for interaction_type in interaction_types:
            self.assertIn(interaction_type.name, tracked_types)
            
        # 验证每种类型的计数
        for interaction_type in interaction_types:
            count = self.tracker.get_interaction_count(interaction_type, "test_zone")
            self.assertEqual(count, 1)
    
    def test_event_handling(self):
        """测试事件处理"""
        # 创建交互事件数据
        event_data = {
            'interaction_type': 'CLICK',
            'zone_id': 'test_zone',
            'timestamp': time.time()
        }
        
        # 创建模拟事件
        mock_event = MagicMock()
        mock_event.data = event_data
        
        # 处理事件
        self.tracker._on_user_interaction(mock_event)
        
        # 验证交互已记录
        self.assertIn('CLICK', self.tracker.interaction_history)
        self.assertIn('test_zone', self.tracker.interaction_history['CLICK'])
        self.assertEqual(self.tracker.interaction_counts['CLICK']['test_zone'], 1)
        
        # 测试无数据的事件
        mock_event.data = None
        self.tracker._on_user_interaction(mock_event)
        
        # 测试缺少必要字段的事件
        mock_event.data = {'timestamp': time.time()}
        self.tracker._on_user_interaction(mock_event)
        
        # 不应更改计数
        self.assertEqual(self.tracker.interaction_counts['CLICK']['test_zone'], 1)
    
    def test_get_last_interaction_time(self):
        """测试获取最近交互时间"""
        # 记录交互
        self.tracker.track_interaction(InteractionType.CLICK, "test_zone")
        
        # 获取最近交互时间
        last_time = self.tracker.get_last_interaction_time(InteractionType.CLICK, "test_zone")
        self.assertIsNotNone(last_time)
        
        # 修复linter错误：确保last_time不为None后再使用assertAlmostEqual
        if last_time is not None:  # 安全检查
            self.assertAlmostEqual(last_time, time.time(), delta=1)
        
        # 获取不存在的交互
        last_time = self.tracker.get_last_interaction_time(InteractionType.DRAG, "test_zone")
        self.assertIsNone(last_time)
    
    def test_get_interaction_times(self):
        """测试获取交互时间列表"""
        # 记录多次交互
        now = time.time()
        
        # 生成一些历史交互记录
        self.tracker.interaction_history["CLICK"] = {
            "test_zone": [
                now - 3600,  # 1小时前
                now - 1800,  # 30分钟前
                now - 600,   # 10分钟前
                now          # 现在
            ]
        }
        self.tracker.interaction_counts["CLICK"] = {"test_zone": 4}
        
        # 获取所有交互时间
        times = self.tracker.get_interaction_times(InteractionType.CLICK, "test_zone")
        self.assertEqual(len(times), 4)
        
        # 获取特定时间窗口内的交互
        times = self.tracker.get_interaction_times(
            InteractionType.CLICK, "test_zone", 1200  # 20分钟
        )
        self.assertEqual(len(times), 2)  # 应该只有2条在20分钟内


if __name__ == '__main__':
    unittest.main() 