"""
---------------------------------------------------------------
File name:                  test_idle_placeholder_core.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                空闲L4占位符核心模块的单元测试
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始化测试;
                            2025/05/15: 更新测试以适应L4标准;
----
"""

import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QImage, QColor

from status.animation.animation import Animation
from status.pet_assets.placeholders import idle_placeholder

class TestIdlePlaceholderCore(unittest.TestCase):
    """
    空闲L4占位符核心模块的单元测试
    """
    _app = None

    @classmethod
    def setUpClass(cls):
        """
        在任何测试运行之前设置QApplication实例。
        """
        # QApplication是QPixmap操作所必需的
        if QApplication.instance() is None:
            cls._app = QApplication([])
        else:
            cls._app = QApplication.instance()

    @classmethod
    def tearDownClass(cls):
        """
        在所有测试运行之后清理资源。
        """
        if cls._app is not None and QApplication.instance() is not None:
            # 仅在创建它并且它仍然存在时退出
            # QApplication.quit() # 这有时会导致问题，如果其他测试需要它
            pass
        cls._app = None

    def test_create_animation_returns_animation_object(self):
        """
        测试create_animation()返回一个Animation对象。
        """
        animation = idle_placeholder.create_animation()
        self.assertIsInstance(animation, Animation, "应该返回一个Animation实例。")

    def test_animation_properties(self):
        """
        测试创建的L4动画的属性。
        """
        animation = idle_placeholder.create_animation()
        self.assertEqual(animation.name, "idle", "动画名称应为'idle'。")
        self.assertEqual(animation.fps, 8, "L4动画的FPS应为8。")
        self.assertTrue(animation.is_looping, "空闲动画应为循环的。")
        self.assertTrue(animation.metadata.get("placeholder"), "动画应在元数据中标记为占位符。")
        self.assertTrue(animation.metadata.get("L4_quality"), "动画应在元数据中标记为L4质量。")
        self.assertEqual(animation.metadata.get("description"), "空闲 L4 占位符动画 - 更自然的待机与细节", "L4动画描述不匹配。")
        self.assertEqual(len(animation.frames), 24, "L4动画应有24帧。")

    def test_animation_frames_are_valid(self):
        """
        测试动画帧是有效的QImage对象并且不为空。
        """
        animation = idle_placeholder.create_animation()
        self.assertGreater(len(animation.frames), 0, "动画应至少有一个帧。")
        for frame_image in animation.frames:
            self.assertIsInstance(frame_image, QImage, "每个帧应为QImage。")
            self.assertFalse(frame_image.isNull(), "帧QImage不应为空。")
            self.assertGreater(frame_image.width(), 0, "帧宽度应大于0。")
            self.assertGreater(frame_image.height(), 0, "帧高度应大于0。")
            self.assertGreater(frame_image.sizeInBytes(), 0, "帧QImage应有数据。")

    def test_animation_frame_size(self):
        """
        测试动画帧具有指定的尺寸。
        """
        # _create_idle_frame 的默认尺寸是(64, 64)
        expected_size = (64, 64) 
        animation = idle_placeholder.create_animation()
        for frame_image in animation.frames:
            self.assertEqual(frame_image.width(), expected_size[0], f"帧宽度应为{expected_size[0]}。")
            self.assertEqual(frame_image.height(), expected_size[1], f"帧高度应为{expected_size[1]}。")

    def test_l4_specific_content_hint_idle(self):
        """L4内容提示性检查：检查是否有非静态元素（例如，比较帧之间的像素差异）。"""
        animation = idle_placeholder.create_animation()
        self.assertGreaterEqual(len(animation.frames), 2, "需要至少2帧来比较差异。")

        frame1 = animation.frames[0]
        frame_mid = animation.frames[len(animation.frames) // 2] # 中间帧

        # 身体采样点 (中心区域)
        body_sample_x = frame1.width() // 2 # 32
        body_sample_y = int((frame1.height() - 30) - (28 / 2)) # (64-30) - 14 = 34 - 14 = 20

        # 左耳尖端大致区域采样点
        ear_sample_x = frame1.width() // 2 - int(18 * 0.5) + (-4) # head_center_x - head_radius*0.5 (translateX) + ear_tip_local_x
        ear_sample_y = int((frame1.height() - 30) - (28 * 0.8) - (18 * 0.6) + (-6)) # head_center_y - head_radius*0.6 (translateY) + ear_tip_local_y
        # Simplified ear sampling for now, as precise calculation is tricky due to rotation
        ear_sample_x = 20 # Approximate left ear area
        ear_sample_y = 15 # Approximate left ear area

        # 尾巴中部大致区域采样点
        tail_base_x = frame1.width() // 2 + int(38 * 0.35) # approx 45
        tail_base_y = int((frame1.height() - 30) - (28*0.1)) # approx 31
        tail_sample_x = tail_base_x + 5 # approx 50
        tail_sample_y = tail_base_y + 8 # approx 39
        
        pixel_diff_count = 0
        # 比较帧0和中间帧的选定像素
        # 身体部分
        if frame1.pixelColor(body_sample_x, body_sample_y) != frame_mid.pixelColor(body_sample_x, body_sample_y):
            pixel_diff_count += 1
        # 尾巴部分
        if frame1.pixelColor(tail_sample_x, tail_sample_y) != frame_mid.pixelColor(tail_sample_x, tail_sample_y):
            pixel_diff_count += 1
        # 耳朵部分
        if frame1.pixelColor(ear_sample_x, ear_sample_y) != frame_mid.pixelColor(ear_sample_x, ear_sample_y):
            pixel_diff_count += 1

        # 对于一个24帧的呼吸、耳朵、尾巴摆动动画，第一帧和中间帧在这些采样点很可能不同
        self.assertGreater(pixel_diff_count, 0, 
                         (f"L4空闲动画应该在不同帧之间有像素差异，暗示动态效果。差异点数: {pixel_diff_count}. "
                          f"帧0: Body={frame1.pixelColor(body_sample_x, body_sample_y).name()}, "
                          f"Tail={frame1.pixelColor(tail_sample_x, tail_sample_y).name()}, "
                          f"Ear={frame1.pixelColor(ear_sample_x, ear_sample_y).name()} "
                          f"帧Mid: Body={frame_mid.pixelColor(body_sample_x, body_sample_y).name()}, "
                          f"Tail={frame_mid.pixelColor(tail_sample_x, tail_sample_y).name()}, "
                          f"Ear={frame_mid.pixelColor(ear_sample_x, ear_sample_y).name()}"))

if __name__ == '__main__':
    unittest.main() 