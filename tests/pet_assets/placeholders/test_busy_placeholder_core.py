"""
---------------------------------------------------------------
File name:                  test_busy_placeholder_core.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                忙碌占位符核心模块的单元测试
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始化测试;
----
"""

import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage

from status.animation.animation import Animation
from status.pet_assets.placeholders import busy_placeholder

class TestBusyPlaceholderCore(unittest.TestCase):
    """
    忙碌占位符核心模块的单元测试
    """
    _app = None

    @classmethod
    def setUpClass(cls):
        """
        在任何测试运行之前设置QApplication实例。
        """
        if QApplication.instance() is None:
            cls._app = QApplication([])
        else:
            cls._app = QApplication.instance()

    @classmethod
    def tearDownClass(cls):
        """
        在所有测试运行之后清理资源。
        """
        cls._app = None # 允许实例在已经存在的情况下被外部管理

    def test_create_animation_returns_animation_object(self):
        """
        测试create_animation()返回一个Animation对象。
        """
        animation = busy_placeholder.create_animation()
        self.assertIsInstance(animation, Animation, "应该返回一个Animation实例。")

    def test_animation_properties(self):
        """
        测试创建的动画的属性(名称、fps、循环、占位符)。
        """
        animation = busy_placeholder.create_animation()
        self.assertEqual(animation.name, "busy", "动画名称应为'busy'。")
        self.assertGreater(animation.fps, 0, "FPS应大于0。") # fps=1是预期的
        self.assertTrue(animation.is_looping, "忙碌动画应为循环的。")
        self.assertTrue(animation.metadata.get("placeholder"), "动画应在元数据中标记为占位符。")
        self.assertIsNotNone(animation.metadata.get("description"), "动画描述不应在元数据中为None。")
        self.assertTrue(len(animation.metadata.get("description", "")) > 0, "动画描述在元数据中不应为空。")

    def test_animation_frames_are_valid(self):
        """
        测试动画帧是有效的QImage对象并且不为空。
        """
        animation = busy_placeholder.create_animation()
        self.assertGreater(len(animation.frames), 0, "动画应至少有一个帧。")
        for frame_image in animation.frames:
            self.assertIsInstance(frame_image, QImage, "每个帧应为QImage。")
            self.assertFalse(frame_image.isNull(), "帧QImage不应为空。")
            self.assertGreater(frame_image.width(), 0, "帧宽度应大于0。")
            self.assertGreater(frame_image.height(), 0, "帧高度应大于0。")
            self.assertGreater(frame_image.sizeInBytes(), 0, "帧QImage应有数据。")

    def test_animation_frame_size(self):
        """
        测试动画帧具有默认尺寸。
        """
        expected_size = (64, 64)  # 默认尺寸来自_create_busy_image
        animation = busy_placeholder.create_animation()
        for frame_image in animation.frames:
            self.assertEqual(frame_image.width(), expected_size[0], f"帧宽度应为{expected_size[0]}。")
            self.assertEqual(frame_image.height(), expected_size[1], f"帧高度应为{expected_size[1]}。")

if __name__ == '__main__':
    unittest.main() 