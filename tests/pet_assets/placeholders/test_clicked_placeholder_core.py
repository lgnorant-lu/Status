"""
---------------------------------------------------------------
File name:                  test_clicked_placeholder_core.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                点击占位符核心模块的单元测试
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始化测试;
----
"""

import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage

from status.animation.animation import Animation
from status.pet_assets.placeholders import clicked_placeholder

class TestClickedPlaceholderCore(unittest.TestCase):
    """
    点击占位符核心模块的单元测试
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
        animation = clicked_placeholder.create_animation()
        self.assertIsInstance(animation, Animation, "应该返回一个Animation实例。")

    def test_animation_properties(self):
        animation = clicked_placeholder.create_animation()
        self.assertEqual(animation.name, "clicked", "动画名称应为'clicked'。")
        self.assertEqual(animation.fps, 2, "FPS应为2。")
        self.assertFalse(animation.is_looping, "点击动画不应循环。")
        self.assertTrue(animation.metadata.get("placeholder"), "动画应在元数据中标记为占位符。")
        self.assertIsNotNone(animation.metadata.get("description"), "动画描述不应在元数据中为None。")
        self.assertTrue(len(animation.metadata.get("description", "")) > 0, "动画描述在元数据中不应为空。")

    def test_animation_frames_are_valid(self):
        animation = clicked_placeholder.create_animation()
        self.assertGreater(len(animation.frames), 0, "动画应至少有一个帧。")
        for frame_image in animation.frames:
            self.assertIsInstance(frame_image, QImage, "每个帧应为QImage。")
            self.assertFalse(frame_image.isNull(), "帧QImage不应为空。")
            self.assertGreater(frame_image.width(), 0, "帧宽度应大于0。")
            self.assertGreater(frame_image.height(), 0, "帧高度应大于0。")
            self.assertGreater(frame_image.sizeInBytes(), 0, "帧QImage应有数据。")

    def test_animation_frame_size(self):
        expected_size = (64, 64)  # 默认尺寸来自_create_clicked_image
        animation = clicked_placeholder.create_animation()
        for frame_image in animation.frames:
            self.assertEqual(frame_image.width(), expected_size[0], f"帧宽度应为{expected_size[0]}。")
            self.assertEqual(frame_image.height(), expected_size[1], f"帧高度应为{expected_size[1]}。")

if __name__ == '__main__':
    unittest.main() 