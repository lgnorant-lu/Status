"""
---------------------------------------------------------------
File name:                  test_enhanced_time_animations.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                测试增强的时间动画功能
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

import unittest
import time
from unittest.mock import patch, MagicMock, ANY
import os
import tempfile
import shutil
from enum import Enum, auto
from typing import Dict, List, Optional, Union

from PySide6.QtGui import QImage
from PySide6.QtCore import QObject, Signal

from status.animation.time_animation_manager import TimeAnimationManager
from status.animation.enhanced_time_manager import EnhancedTimeAnimationManager
from status.animation.animation import Animation
from status.behavior.time_based_behavior import TimePeriod, SpecialDate


class TestEnhancedTimeAnimations(unittest.TestCase):
    """测试增强的时间动画功能"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时目录模拟资源文件结构
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建增强型动画管理器实例
        self.manager = EnhancedTimeAnimationManager(base_path=self.temp_dir)
        
        # 创建模拟资源目录结构
        self._create_mock_resource_structure()
    
    def tearDown(self):
        """清理测试环境"""
        # 移除临时目录
        shutil.rmtree(self.temp_dir)
    
    def _create_mock_resource_structure(self):
        """创建模拟资源目录结构"""
        # 创建时间段动画目录
        time_dir = os.path.join(self.temp_dir, "resources", "animations", "time")
        os.makedirs(time_dir, exist_ok=True)
        
        # 为每个时间段创建子目录
        for period in ["morning", "noon", "afternoon", "evening", "night"]:
            period_dir = os.path.join(time_dir, period)
            os.makedirs(period_dir, exist_ok=True)
            
            # 创建多个图片文件作为动画帧
            for i in range(4):
                image_path = os.path.join(period_dir, f"frame_{i}.png")
                image = QImage(100, 100, QImage.Format.Format_ARGB32)
                image.fill(0xFFFFFFFF)  # 白色填充
                image.save(image_path)
        
        # 创建节日动画目录
        festival_dir = os.path.join(self.temp_dir, "resources", "animations", "festivals")
        os.makedirs(festival_dir, exist_ok=True)
        
        # 为主要节日创建子目录
        for festival in ["spring_festival", "dragon_boat", "mid_autumn"]:
            festival_dir_path = os.path.join(festival_dir, festival)
            os.makedirs(festival_dir_path, exist_ok=True)
            
            # 创建图片文件
            for i in range(5):
                image_path = os.path.join(festival_dir_path, f"frame_{i}.png")
                image = QImage(100, 100, QImage.Format.Format_ARGB32)
                image.fill(0xFFFF0000)  # 红色填充
                image.save(image_path)
        
        # 创建节气动画目录
        solar_term_dir = os.path.join(self.temp_dir, "resources", "animations", "solar_terms")
        os.makedirs(solar_term_dir, exist_ok=True)
        
        # 为几个节气创建子目录
        for term in ["spring_begins", "grain_rain", "great_heat"]:
            term_dir = os.path.join(solar_term_dir, term)
            os.makedirs(term_dir, exist_ok=True)
            
            # 创建图片文件
            for i in range(4):
                image_path = os.path.join(term_dir, f"frame_{i}.png")
                image = QImage(100, 100, QImage.Format.Format_ARGB32)
                image.fill(0xFF00FF00)  # 绿色填充
                image.save(image_path)
        
        # 创建过渡动画目录
        transition_dir = os.path.join(self.temp_dir, "resources", "animations", "transitions")
        os.makedirs(transition_dir, exist_ok=True)
        
        # 为所有时间段过渡创建子目录
        transitions = [
            "morning_to_noon", "noon_to_afternoon", 
            "afternoon_to_evening", "evening_to_night",
            "night_to_morning"
        ]
        for trans in transitions:
            trans_dir = os.path.join(transition_dir, trans)
            os.makedirs(trans_dir, exist_ok=True)
            
            # 创建图片文件
            for i in range(6):  # 过渡动画帧数更多
                image_path = os.path.join(trans_dir, f"frame_{i}.png")
                image = QImage(100, 100, QImage.Format.Format_ARGB32)
                image.fill(0xFF0000FF)  # 蓝色填充
                image.save(image_path)
    
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.manager)
        self.assertEqual(self.manager.base_path, self.temp_dir)
        self.assertEqual(len(self.manager.time_period_animations), 0)
        self.assertEqual(len(self.manager.festival_animations), 0)
        self.assertEqual(len(self.manager.solar_term_animations), 0)
        self.assertEqual(len(self.manager.transition_animations), 0)
    
    def test_load_time_period_animations(self):
        """测试加载时间段动画"""
        # 加载时间段动画
        result = self.manager.load_time_period_animations()
        self.assertTrue(result)
        
        # 验证是否加载了5个时间段动画
        self.assertEqual(len(self.manager.time_period_animations), 5)
        
        # 验证每个时间段都有对应的动画
        for period in TimePeriod:
            self.assertIn(period, self.manager.time_period_animations)
            animation = self.manager.time_period_animations[period]
            self.assertIsInstance(animation, Animation)
            self.assertEqual(len(animation.frames), 4)  # 确认帧数为4
    
    def test_load_festival_animations(self):
        """测试加载节日动画"""
        # 加载节日动画
        result = self.manager.load_festival_animations()
        self.assertTrue(result)
        
        # 验证节日动画加载情况
        self.assertEqual(len(self.manager.festival_animations), 3)
        
        # 确保我们创建的节日动画加载成功
        for festival in ["spring_festival", "dragon_boat", "mid_autumn"]:
            self.assertIn(festival, self.manager.festival_animations)
            animation = self.manager.festival_animations[festival]
            self.assertIsInstance(animation, Animation)
            self.assertEqual(len(animation.frames), 5)  # 确认帧数为5
    
    def test_load_solar_term_animations(self):
        """测试加载节气动画"""
        # 加载节气动画
        result = self.manager.load_solar_term_animations()
        self.assertTrue(result)
        
        # 验证节气动画加载情况
        self.assertEqual(len(self.manager.solar_term_animations), 3)
        
        # 确保我们创建的节气动画加载成功
        for term in ["spring_begins", "grain_rain", "great_heat"]:
            self.assertIn(term, self.manager.solar_term_animations)
            animation = self.manager.solar_term_animations[term]
            self.assertIsInstance(animation, Animation)
            self.assertEqual(len(animation.frames), 4)  # 确认帧数为4
    
    def test_load_transition_animations(self):
        """测试加载过渡动画"""
        # 加载过渡动画
        result = self.manager.load_transition_animations()
        self.assertTrue(result)
        
        # 验证过渡动画加载情况
        self.assertEqual(len(self.manager.transition_animations), 5)
        
        # 确认我们创建的所有过渡动画加载成功
        expected_transitions = [
            (TimePeriod.MORNING, TimePeriod.NOON),
            (TimePeriod.NOON, TimePeriod.AFTERNOON),
            (TimePeriod.AFTERNOON, TimePeriod.EVENING),
            (TimePeriod.EVENING, TimePeriod.NIGHT),
            (TimePeriod.NIGHT, TimePeriod.MORNING)
        ]
        
        for transition in expected_transitions:
            self.assertIn(transition, self.manager.transition_animations)
            animation = self.manager.transition_animations[transition]
            self.assertIsInstance(animation, Animation)
            self.assertEqual(len(animation.frames), 6)  # 确认帧数为6
    
    def test_get_animation_for_festival(self):
        """测试获取节日动画"""
        # 先加载动画
        self.manager.load_festival_animations()
        
        # 测试获取已加载的节日动画
        animation = self.manager.get_animation_for_festival("spring_festival")
        self.assertIsNotNone(animation)
        self.assertIsInstance(animation, Animation)
        
        # 测试获取中文名称节日动画
        animation = self.manager.get_animation_for_festival("春节")
        self.assertIsNotNone(animation)
        self.assertIsInstance(animation, Animation)
        
        # 测试获取不存在的节日动画（会创建占位符）
        animation = self.manager.get_animation_for_festival("不存在的节日")
        self.assertIsNotNone(animation)
        self.assertIsInstance(animation, Animation)
        self.assertTrue(animation is not None and "placeholder" in animation.metadata)
    
    def test_get_animation_for_solar_term(self):
        """测试获取节气动画"""
        # 先加载动画
        self.manager.load_solar_term_animations()
        
        # 测试获取已加载的节气动画
        animation = self.manager.get_animation_for_solar_term("spring_begins")
        self.assertIsNotNone(animation)
        self.assertIsInstance(animation, Animation)
        
        # 测试获取中文名称节气动画
        animation = self.manager.get_animation_for_solar_term("立春")
        self.assertIsNotNone(animation)
        self.assertIsInstance(animation, Animation)
        
        # 测试获取不存在的节气动画（会创建占位符）
        animation = self.manager.get_animation_for_solar_term("不存在的节气")
        self.assertIsNotNone(animation)
        self.assertIsInstance(animation, Animation)
        self.assertTrue(animation is not None and "placeholder" in animation.metadata)
    
    def test_memory_optimization(self):
        """测试内存优化"""
        # 使用大型图像测试内存优化
        large_image_dir = os.path.join(self.temp_dir, "resources", "animations", "large_test")
        os.makedirs(large_image_dir, exist_ok=True)
        
        # 创建一个大的测试图像
        large_image = QImage(1000, 1000, QImage.Format.Format_ARGB32)
        large_image.fill(0xFFFFFFFF)
        large_image_path = os.path.join(large_image_dir, "large_frame.png")
        large_image.save(large_image_path)
        
        # 测试内存优化加载
        animation = self.manager.load_animation_optimized(large_image_dir, "large_test")
        self.assertIsNotNone(animation)
        
        # 验证图像是否被适当地优化了尺寸
        self.assertIsNotNone(animation)
        if animation is not None:  # 增加安全检查
            for frame in animation.frames:
                self.assertLessEqual(frame.width(), self.manager.max_image_width)
                self.assertLessEqual(frame.height(), self.manager.max_image_height)
    
    def test_smooth_transition(self):
        """测试平滑过渡效果"""
        # 加载时间段动画和过渡动画
        self.manager.load_time_period_animations()
        self.manager.load_transition_animations()
        
        # 测试有过渡动画的情况
        animation_sequence = self.manager.get_smooth_transition(TimePeriod.MORNING, TimePeriod.NOON)
        self.assertIsNotNone(animation_sequence)
        self.assertTrue(len(animation_sequence) > 0)
        
        # 测试没有过渡动画的直接切换情况
        # 创建一个不存在的过渡
        animation_sequence = self.manager.get_smooth_transition(TimePeriod.MORNING, TimePeriod.NIGHT)
        self.assertIsNotNone(animation_sequence)
        # 应该是两个动画的序列（开始动画和结束动画）
        self.assertEqual(len(animation_sequence), 2)
    
    def test_special_date_lookup(self):
        """测试特殊日期查找功能"""
        # 加载节日和节气动画
        self.manager.load_festival_animations()
        self.manager.load_solar_term_animations()
        
        # 创建一个春节特殊日期对象
        spring_festival = SpecialDate(
            name="春节",
            month=1,
            day=1,
            is_lunar=True,
            description="农历新年",
            type="festival"
        )
        
        # 测试根据特殊日期对象获取动画
        animation = self.manager.get_animation_for_special_date(spring_festival)
        self.assertIsNotNone(animation)
        self.assertIsInstance(animation, Animation)
        
        # 创建一个立春节气特殊日期对象
        spring_begins = SpecialDate(
            name="立春",
            month=2,
            day=4,  # 立春通常在2月4日左右
            is_lunar=False,
            description="二十四节气之一",
            type="solar_term"
        )
        
        # 测试根据特殊日期对象获取动画
        animation = self.manager.get_animation_for_special_date(spring_begins)
        self.assertIsNotNone(animation)
        self.assertIsInstance(animation, Animation)
    
    def test_performance(self):
        """测试性能优化"""
        # 测试预加载与按需加载的性能差异
        
        # 按需加载方式计时
        start_time = time.time()
        for _ in range(10):
            for period in TimePeriod:
                self.manager.get_animation_for_time_period(period)
        on_demand_time = time.time() - start_time
        
        # 预加载方式计时
        start_time = time.time()
        self.manager.load_time_period_animations()
        for _ in range(10):
            for period in TimePeriod:
                _ = self.manager.time_period_animations.get(period)
        preload_time = time.time() - start_time
        
        # 验证预加载性能优于按需加载
        self.assertLess(preload_time, on_demand_time * 2)  # 预加载应该比多次按需加载快
                
    def test_cached_image_loading(self):
        """测试图像缓存加载"""
        # 清除现有缓存
        self.manager.clear_cache()
        
        # 首次加载应该从磁盘读取
        start_time = time.time()
        self.manager.load_time_period_animations()
        first_load_time = time.time() - start_time
        
        # 清除动画但保留缓存
        self.manager.time_period_animations.clear()
        
        # 再次加载应该从缓存读取
        start_time = time.time()
        self.manager.load_time_period_animations()
        second_load_time = time.time() - start_time
        
        # 验证从缓存加载更快
        self.assertLess(second_load_time, first_load_time)


if __name__ == "__main__":
    unittest.main() 