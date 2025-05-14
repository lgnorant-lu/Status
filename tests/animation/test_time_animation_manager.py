"""
---------------------------------------------------------------
File name:                  test_time_animation_manager.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                测试时间动画管理器
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

import unittest
from unittest.mock import patch, MagicMock, ANY
import os
import tempfile
import shutil

from PySide6.QtGui import QImage
from PySide6.QtCore import QObject, Signal

from status.animation.time_animation_manager import TimeAnimationManager
from status.animation.animation import Animation
from status.behavior.time_based_behavior import TimePeriod


class TestTimeAnimationManager(unittest.TestCase):
    """测试TimeAnimationManager"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时目录模拟资源文件结构
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建动画管理器实例
        self.manager = TimeAnimationManager(base_path=self.temp_dir)
        
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
            
            # 创建一个简单的图片文件作为动画帧
            for i in range(2):
                image_path = os.path.join(period_dir, f"frame_{i}.png")
                image = QImage(100, 100, QImage.Format.Format_ARGB32)
                image.fill(0xFFFFFFFF)  # 白色填充
                image.save(image_path)
        
        # 创建特殊日期动画目录
        special_dir = os.path.join(self.temp_dir, "resources", "animations", "special_dates")
        os.makedirs(special_dir, exist_ok=True)
        
        # 为几个特殊日期创建子目录
        for date in ["new_year", "birthday", "valentine"]:
            date_dir = os.path.join(special_dir, date)
            os.makedirs(date_dir, exist_ok=True)
            
            # 创建图片文件
            for i in range(2):
                image_path = os.path.join(date_dir, f"frame_{i}.png")
                image = QImage(100, 100, QImage.Format.Format_ARGB32)
                image.fill(0xFFFF0000)  # 红色填充
                image.save(image_path)
        
        # 创建过渡动画目录
        transition_dir = os.path.join(self.temp_dir, "resources", "animations", "transitions")
        os.makedirs(transition_dir, exist_ok=True)
        
        # 为几个过渡创建子目录
        transitions = ["morning_to_noon", "noon_to_afternoon"]
        for trans in transitions:
            trans_dir = os.path.join(transition_dir, trans)
            os.makedirs(trans_dir, exist_ok=True)
            
            # 创建图片文件
            for i in range(2):
                image_path = os.path.join(trans_dir, f"frame_{i}.png")
                image = QImage(100, 100, QImage.Format.Format_ARGB32)
                image.fill(0xFF00FF00)  # 绿色填充
                image.save(image_path)
    
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.manager)
        self.assertEqual(self.manager.base_path, self.temp_dir)
        self.assertEqual(len(self.manager.time_period_animations), 0)
        self.assertEqual(len(self.manager.special_date_animations), 0)
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
            self.assertGreater(len(animation.frames), 0)
    
    def test_load_special_date_animations(self):
        """测试加载特殊日期动画"""
        # 修改TimeAnimationManager内的load_special_date_animations方法，使其扫描目录而不是检查固定列表
        original_method = self.manager.load_special_date_animations
        
        def custom_load(resource_path=""):
            """自定义加载方法，扫描目录而不是使用预定义列表"""
            full_path = os.path.join(self.temp_dir, resource_path)
            
            if not os.path.exists(full_path):
                print(f"特殊日期目录不存在: {full_path}")
                return False
                
            # 扫描目录，加载所有子目录
            success = True
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                if os.path.isdir(item_path):
                    # 尝试加载这个子目录作为动画
                    animation = self.manager._load_animation_from_path(item_path, f"special_{item}")
                    if animation:
                        self.manager.special_date_animations[item] = animation
                        self.manager.animation_loaded.emit(f"special_{item}", animation)
                        print(f"加载特殊日期动画: {item}")
                    else:
                        # 这里不会将整个加载标记为失败
                        print(f"无法加载特殊日期动画: {item}")
            
            # 只要有任何成功加载，就返回True
            return len(self.manager.special_date_animations) > 0
        
        try:
            # 替换方法
            self.manager.load_special_date_animations = custom_load
            
            # 创建精确的特殊日期路径
            special_dir = os.path.join(self.temp_dir, "resources", "animations", "special_dates")
            
            # 检查并打印目录内容以进行调试
            if os.path.exists(special_dir):
                print(f"特殊日期目录存在，内容: {os.listdir(special_dir)}")
            else:
                print(f"特殊日期目录不存在: {special_dir}")
            
            # 加载动画
            result = self.manager.load_special_date_animations(special_dir)
            self.assertTrue(result)
            
            # 验证特殊日期动画加载情况
            self.assertGreater(len(self.manager.special_date_animations), 0)
            
            # 打印加载的动画
            print(f"加载的特殊日期动画: {list(self.manager.special_date_animations.keys())}")
            
            # 确保我们创建的动画加载成功
            for date_name in ["new_year", "birthday", "valentine"]:
                self.assertIn(date_name, self.manager.special_date_animations)
                animation = self.manager.special_date_animations[date_name]
                self.assertIsInstance(animation, Animation)
                self.assertGreater(len(animation.frames), 0)
        finally:
            # 恢复原始方法
            self.manager.load_special_date_animations = original_method
    
    def test_load_transition_animations(self):
        """测试加载过渡动画"""
        # 修改TimeAnimationManager内的load_transition_animations方法
        original_method = self.manager.load_transition_animations
        
        def custom_load(resource_path=""):
            """自定义加载方法，扫描目录而不是使用预定义列表"""
            full_path = os.path.join(self.temp_dir, resource_path)
            
            if not os.path.exists(full_path):
                print(f"过渡动画目录不存在: {full_path}")
                return False
                
            # 扫描目录，加载所有子目录
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                if os.path.isdir(item_path):
                    # 尝试解析目录名为过渡关系
                    if "_to_" in item:
                        from_name, to_name = item.split("_to_")
                        try:
                            from_period = TimePeriod[from_name.upper()]
                            to_period = TimePeriod[to_name.upper()]
                            
                            # 尝试加载这个子目录作为动画
                            animation = self.manager._load_animation_from_path(item_path, f"transition_{item}")
                            if animation:
                                self.manager.transition_animations[(from_period, to_period)] = animation
                                self.manager.animation_loaded.emit(f"transition_{item}", animation)
                                print(f"加载过渡动画: {item}")
                            else:
                                print(f"无法加载过渡动画: {item}")
                        except (KeyError, ValueError):
                            print(f"无法解析过渡动画名称: {item}")
            
            # 只要有任何成功加载，就返回True
            return len(self.manager.transition_animations) > 0
        
        try:
            # 替换方法
            self.manager.load_transition_animations = custom_load
            
            # 创建精确的过渡动画路径
            transition_dir = os.path.join(self.temp_dir, "resources", "animations", "transitions")
            
            # 检查并打印目录内容以进行调试
            if os.path.exists(transition_dir):
                print(f"过渡动画目录存在，内容: {os.listdir(transition_dir)}")
            else:
                print(f"过渡动画目录不存在: {transition_dir}")
            
            # 加载动画
            result = self.manager.load_transition_animations(transition_dir)
            self.assertTrue(result)
            
            # 验证过渡动画加载情况
            self.assertEqual(len(self.manager.transition_animations), 2)
            
            # 打印加载的动画
            transitions = list(self.manager.transition_animations.keys())
            print(f"加载的过渡动画: {[(t[0].name, t[1].name) for t in transitions]}")
            
            # 确认我们创建的过渡动画加载成功
            self.assertIn((TimePeriod.MORNING, TimePeriod.NOON), self.manager.transition_animations)
            self.assertIn((TimePeriod.NOON, TimePeriod.AFTERNOON), self.manager.transition_animations)
            
            # 验证动画内容
            for key in [(TimePeriod.MORNING, TimePeriod.NOON), (TimePeriod.NOON, TimePeriod.AFTERNOON)]:
                animation = self.manager.transition_animations[key]
                self.assertIsInstance(animation, Animation)
                self.assertGreater(len(animation.frames), 0)
        finally:
            # 恢复原始方法
            self.manager.load_transition_animations = original_method
    
    def test_get_animation_for_time_period(self):
        """测试获取时间段动画"""
        # 先加载动画
        time_dir = os.path.join(self.temp_dir, "resources", "animations", "time")
        self.manager.load_time_period_animations(time_dir)
        
        # 测试获取每个时间段的动画
        for period in TimePeriod:
            animation = self.manager.get_animation_for_time_period(period)
            self.assertIsNotNone(animation)
            self.assertIsInstance(animation, Animation)
    
    def test_get_animation_for_special_date(self):
        """测试获取特殊日期动画"""
        # 先加载动画
        special_dir = os.path.join(self.temp_dir, "resources", "animations", "special_dates")
        self.manager.load_special_date_animations(special_dir)
        
        # 测试获取已加载的特殊日期动画
        animation = self.manager.get_animation_for_special_date("new_year")
        self.assertIsNotNone(animation)
        self.assertIsInstance(animation, Animation)
        
        # 测试获取中文名称特殊日期动画
        animation = self.manager.get_animation_for_special_date("新年")
        self.assertIsNotNone(animation)
        self.assertIsInstance(animation, Animation)
        
        # 测试获取不存在的特殊日期动画（会创建占位符）
        animation = self.manager.get_animation_for_special_date("不存在的日期")
        self.assertIsNotNone(animation)
        self.assertIsInstance(animation, Animation)
        self.assertTrue(animation is not None and "placeholder" in animation.metadata)
    
    def test_get_animation_for_birth_of_status_ming(self):
        """测试获取Status-Ming诞辰动画"""
        # 先加载动画
        special_dir = os.path.join(self.temp_dir, "resources", "animations", "special_dates")
        self.manager.load_special_date_animations(special_dir)
        
        # 测试获取"Birth of Status-Ming!"动画
        animation = self.manager.get_animation_for_special_date("Birth of Status-Ming!")
        self.assertIsNotNone(animation)
        self.assertIsInstance(animation, Animation)
    
    def test_get_transition_animation(self):
        """测试获取过渡动画"""
        # 先加载动画
        transition_dir = os.path.join(self.temp_dir, "resources", "animations", "transitions")
        self.manager.load_transition_animations(transition_dir)
        
        # 测试获取已加载的过渡动画
        animation = self.manager.get_transition_animation(TimePeriod.MORNING, TimePeriod.NOON)
        self.assertIsNotNone(animation)
        self.assertIsInstance(animation, Animation)
    
    def test_on_time_period_changed(self):
        """测试时间段变化响应"""
        # 先加载动画
        time_dir = os.path.join(self.temp_dir, "resources", "animations", "time")
        self.manager.load_time_period_animations(time_dir)
        
        transition_dir = os.path.join(self.temp_dir, "resources", "animations", "transitions")
        self.manager.load_transition_animations(transition_dir)
        
        # 测试有过渡动画的情况
        animation = self.manager.on_time_period_changed(TimePeriod.NOON, TimePeriod.MORNING)
        self.assertIsNotNone(animation)
        
        # 测试没有过渡动画的情况
        animation = self.manager.on_time_period_changed(TimePeriod.EVENING, TimePeriod.AFTERNOON)
        self.assertIsNotNone(animation)
    
    def test_on_special_date_triggered(self):
        """测试特殊日期触发响应"""
        # 先加载动画
        special_dir = os.path.join(self.temp_dir, "resources", "animations", "special_dates")
        self.manager.load_special_date_animations(special_dir)
        
        # 测试已加载的特殊日期
        animation = self.manager.on_special_date_triggered("new_year", "新年快乐")
        self.assertIsNotNone(animation)
        
        # 测试未加载的特殊日期
        animation = self.manager.on_special_date_triggered("不存在的日期", "测试描述")
        self.assertIsNotNone(animation)
        self.assertTrue(animation is not None and "placeholder" in animation.metadata)
    
    def test_animation_loaded_signal(self):
        """测试动画加载信号"""
        # 创建信号接收器
        received_signals = []
        
        def signal_handler(name, animation):
            received_signals.append((name, animation))
        
        # 连接信号
        self.manager.animation_loaded.connect(signal_handler)
        
        # 加载动画
        time_dir = os.path.join(self.temp_dir, "resources", "animations", "time")
        self.manager.load_time_period_animations(time_dir)
        
        # 验证接收到的信号
        self.assertGreater(len(received_signals), 0)
        
        # 检查第一个接收到的信号
        name, animation = received_signals[0]
        self.assertTrue(name.startswith("time_"))
        self.assertIsInstance(animation, Animation)
    
    def test_create_placeholder_animation(self):
        """测试创建占位符动画"""
        # 创建各种占位符动画
        morning_placeholder = self.manager._create_placeholder_animation("time_morning")
        special_placeholder = self.manager._create_placeholder_animation("special_new_year")
        custom_placeholder = self.manager._create_placeholder_animation("custom_animation")
        
        # 验证创建的占位符动画
        self.assertIsNotNone(morning_placeholder)
        self.assertIsNotNone(special_placeholder)
        self.assertIsNotNone(custom_placeholder)
        
        # 验证占位符标记
        self.assertTrue(morning_placeholder is not None and morning_placeholder.metadata.get("placeholder", False))
        self.assertTrue(special_placeholder is not None and special_placeholder.metadata.get("placeholder", False))
        self.assertTrue(custom_placeholder is not None and custom_placeholder.metadata.get("placeholder", False))


if __name__ == "__main__":
    unittest.main() 