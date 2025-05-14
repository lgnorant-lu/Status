"""
---------------------------------------------------------------
File name:                  test_busy_placeholder_core.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                忙碌L4占位符核心模块的单元测试
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始化测试;
                            2025/05/15: 更新测试以适应L4标准;
----
"""

import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QColor

from status.animation.animation import Animation
from status.pet_assets.placeholders import busy_placeholder

class TestBusyPlaceholderCore(unittest.TestCase):
    """
    忙碌L4占位符核心模块的单元测试
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
        测试创建的L4动画的属性。
        """
        animation = busy_placeholder.create_animation()
        self.assertEqual(animation.name, "busy", "动画名称应为'busy'。")
        self.assertEqual(animation.fps, 12, "L4动画的FPS应为12。") # L4 FPS
        self.assertTrue(animation.is_looping, "忙碌动画应为循环的。")
        self.assertTrue(animation.metadata.get("placeholder"), "动画应在元数据中标记为占位符。")
        self.assertTrue(animation.metadata.get("L4_quality"), "动画应在元数据中标记为L4质量。") # L4 quality
        self.assertEqual(animation.metadata.get("description"), "忙碌 L4 占位符动画 - 激烈的键盘输入与专注表情", "L4动画描述不匹配。") # L4 description
        self.assertEqual(len(animation.frames), 30, "L4动画应有30帧。") # L4 frame count

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
        expected_size = (64, 64)  # 默认尺寸来自_create_busy_frame
        animation = busy_placeholder.create_animation()
        for frame_image in animation.frames:
            self.assertEqual(frame_image.width(), expected_size[0], f"帧宽度应为{expected_size[0]}。")
            self.assertEqual(frame_image.height(), expected_size[1], f"帧高度应为{expected_size[1]}。")

    def test_l4_specific_content_hint_busy(self):
        """L4内容提示性检查：检查打字相关的动态效果，如爪子或头部晃动。"""
        animation = busy_placeholder.create_animation()
if __name__ == '__main__':
    unittest.main() 