"""
---------------------------------------------------------------
File name:                  test_lichun_placeholder.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                立春L4占位符模块的单元测试
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始化测试;
----
"""

import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QColor

from status.animation.animation import Animation
from status.pet_assets.placeholders import lichun_placeholder

class TestLichunPlaceholder(unittest.TestCase):
    """
    立春L4占位符模块的单元测试
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
        animation = lichun_placeholder.create_animation()
        self.assertIsInstance(animation, Animation, "应该返回一个Animation实例。")

    def test_animation_properties_l4(self):
        """测试创建的L4动画的属性。"""
        animation = lichun_placeholder.create_animation()
        self.assertEqual(animation.name, "lichun", "动画名称应为'lichun'。")
        self.assertEqual(animation.fps, 8, "FPS应为8 (L4动画预期)。")
        self.assertTrue(animation.is_looping, "立春动画应为循环的。")
        self.assertTrue(animation.metadata.get("placeholder"), "动画应在元数据中标记为占位符。")
        self.assertTrue(animation.metadata.get("L4_quality"), "动画应在元数据中标记为L4质量。")
        self.assertEqual(animation.metadata.get("description"), "立春 L4 占位符动画 - 嫩芽与微风", "描述不匹配。")
        self.assertGreaterEqual(len(animation.frames), 20, "L4动画预期有较多帧 (至少20帧)。") # 预期30帧

    def test_animation_frames_are_valid(self):
        """测试动画帧是有效的QImage对象并且不为空。"""
        animation = lichun_placeholder.create_animation()
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
        animation = lichun_placeholder.create_animation()
        for frame_image in animation.frames:
            self.assertEqual(frame_image.width(), expected_size[0], f"帧宽度应为{expected_size[0]}。")
            self.assertEqual(frame_image.height(), expected_size[1], f"帧高度应为{expected_size[1]}。")

    def test_l4_specific_content_hint(self):
        """L4内容提示性检查：检查是否有绿色系像素（嫩芽颜色）和浅色背景。"""
        animation = lichun_placeholder.create_animation()
        if not animation.frames:
            self.fail("动画没有帧可供检查内容。")
        
        frame_to_check = animation.frames[len(animation.frames) // 2] # 检查中间一帧
        
        has_sprout_color = False
        has_light_background = False
        
        # 检查背景色 (期望淡蓝/淡绿色系)
        bg_color_sample = frame_to_check.pixelColor(5, 5) # 背景通常占据大部分区域
        if bg_color_sample.red() > 180 and bg_color_sample.green() > 200 and bg_color_sample.blue() > 180:
            has_light_background = True

        # 简单采样检查是否有嫩绿色
        for x in range(frame_to_check.width() // 4, frame_to_check.width() * 3 // 4, 3):
            for y in range(frame_to_check.height() // 2, frame_to_check.height(), 3): # 嫩芽通常在下半部分
                color = frame_to_check.pixelColor(x, y)
                # 检查嫩绿色系
                if color.green() > 150 and color.red() < 150 and color.blue() < 150:
                    has_sprout_color = True
                    break
            if has_sprout_color:
                break
        
        self.assertTrue(has_light_background, "L4立春动画背景色调应偏浅蓝/浅绿。")
        self.assertTrue(has_sprout_color, "L4立春动画中应能找到嫩芽的绿色。")

if __name__ == '__main__':
    unittest.main()
