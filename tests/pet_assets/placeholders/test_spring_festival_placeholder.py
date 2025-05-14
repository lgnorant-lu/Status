"""
---------------------------------------------------------------
File name:                  test_spring_festival_placeholder.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                春节L4占位符模块的单元测试
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始化测试;
----
"""

import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QColor

from status.animation.animation import Animation
from status.pet_assets.placeholders import spring_festival_placeholder

class TestSpringFestivalPlaceholder(unittest.TestCase):
    """
    春节L4占位符模块的单元测试
    """
    _app = None

    @classmethod
    def setUpClass(cls):
        if QApplication.instance() is None:
            cls._app = QApplication([])
        else:
            cls._app = QApplication.instance()

    @classmethod
    def tearDownClass(cls):
        cls._app = None

    def test_create_animation_returns_animation_object(self):
        """测试create_animation()返回一个Animation对象。"""
        animation = spring_festival_placeholder.create_animation()
        self.assertIsInstance(animation, Animation, "应该返回一个Animation实例。")

    def test_animation_properties_l4(self):
        """测试创建的L4动画的属性。"""
        animation = spring_festival_placeholder.create_animation()
        self.assertEqual(animation.name, "spring_festival", "动画名称应为'spring_festival'。")
        self.assertEqual(animation.fps, 10, "FPS应为10 (L4动画预期)。")
        self.assertTrue(animation.is_looping, "春节动画应为循环的。")
        self.assertTrue(animation.metadata.get("placeholder"), "动画应在元数据中标记为占位符。")
        self.assertTrue(animation.metadata.get("L4_quality"), "动画应在元数据中标记为L4质量。")
        self.assertEqual(animation.metadata.get("description"), "春节 L4 占位符动画 - 烟花与灯笼", "描述不匹配。")
        self.assertGreaterEqual(len(animation.frames), 15, "L4动画预期有较多帧 (至少15帧)。") # 预期20帧

    def test_animation_frames_are_valid(self):
        """测试动画帧是有效的QImage对象并且不为空。"""
        animation = spring_festival_placeholder.create_animation()
        self.assertTrue(len(animation.frames) > 0, "动画应至少有一个帧。")
        for frame_image in animation.frames:
            self.assertIsInstance(frame_image, QImage, "每个帧应为QImage。")
            self.assertFalse(frame_image.isNull(), "帧QImage不应为空。")
            self.assertGreater(frame_image.width(), 0, "帧宽度应大于0。")
            self.assertGreater(frame_image.height(), 0, "帧高度应大于0。")
            self.assertGreater(frame_image.sizeInBytes(), 0, "帧QImage应有数据。")

    def test_animation_frame_size(self):
        """测试动画帧具有指定的尺寸。"""
        expected_size = (64, 64) 
        animation = spring_festival_placeholder.create_animation()
        for frame_image in animation.frames:
            self.assertEqual(frame_image.width(), expected_size[0], f"帧宽度应为{expected_size[0]}。")
            self.assertEqual(frame_image.height(), expected_size[1], f"帧高度应为{expected_size[1]}。")

    def test_l4_specific_content_hint(self):
        """L4内容提示性检查：检查是否有红色/橙色/黄色系像素（烟花/灯笼颜色），以及深色背景。"""
        animation = spring_festival_placeholder.create_animation()
        if not animation.frames:
            self.fail("动画没有帧可供检查内容。")
        
        frame_to_check = animation.frames[len(animation.frames) // 2] # 检查中间一帧
        
        has_festive_color = False
        has_dark_background = False
        width = frame_to_check.width()
        height = frame_to_check.height()
        
        # 检查背景色 (期望深红色系)
        # 采样多个点避免单个像素异常
        bg_colors_samples = [
            frame_to_check.pixelColor(0,0),
            frame_to_check.pixelColor(width-1, 0),
            frame_to_check.pixelColor(0, height-1),
            frame_to_check.pixelColor(width-1, height-1),
            frame_to_check.pixelColor(width//4, height//4) # 避开可能的灯笼区域
        ]
        dark_bg_count = 0
        for bg_color_sample in bg_colors_samples:
            if bg_color_sample.red() < 120 and bg_color_sample.green() < 70 and bg_color_sample.blue() < 70 and bg_color_sample.alpha() > 180:
                dark_bg_count +=1
        if dark_bg_count >=3: # 多数采样点符合则认为背景色正确
            has_dark_background = True

        # 简单采样检查是否有节日色彩 (烟花通常在中间上半部分)
        # 烟花中心大致在 (width/2, height/3), max_radius = width/3
        # 采样区域可以集中在烟花可能出现的区域
        firework_center_x = width // 2
        firework_center_y = height // 3
        max_firework_radius = width // 3

        search_start_x = max(0, firework_center_x - max_firework_radius - 5)
        search_end_x = min(width, firework_center_x + max_firework_radius + 5)
        search_start_y = max(0, firework_center_y - max_firework_radius - 5)
        search_end_y = min(height, firework_center_y + max_firework_radius + 5)

        for x in range(search_start_x, search_end_x, 2): # 减小步长
            for y in range(search_start_y, search_end_y, 2): # 减小步长
                color = frame_to_check.pixelColor(x, y)
                # 检查红色系、黄色系、橙色系 (烟花/灯笼颜色)，放宽对G/B通道的限制，主要看R通道，并确保不是背景色
                is_background_approx = color.red() < 120 and color.green() < 70 and color.blue() < 70
                if not is_background_approx and color.alpha() > 100: # 确保不是透明或纯背景色
                    if (color.red() > 180 and color.green() < 180 and color.blue() < 180) or \
                       (color.red() > 180 and color.green() > 180 and color.blue() < 150) or \
                       (color.red() > 180 and color.green() > 120 and color.green() < 220 and color.blue() < 120):
                        has_festive_color = True
                        break
            if has_festive_color:
                break
        
        self.assertTrue(has_dark_background, f"L4春节动画背景色调应偏暗红。采样点颜色: {[c.name() for c in bg_colors_samples]}")
        self.assertTrue(has_festive_color, "L4春节动画中应能找到烟花或灯笼的特征颜色。")

if __name__ == '__main__':
    unittest.main()
