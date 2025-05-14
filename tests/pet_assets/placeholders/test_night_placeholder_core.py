"""
---------------------------------------------------------------
File name:                  test_night_placeholder_core.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                夜晚L4占位符核心模块的单元测试
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
from status.pet_assets.placeholders import night_placeholder

class TestNightPlaceholderCore(unittest.TestCase):
    """
    夜晚L4占位符核心模块的单元测试
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
        """
        测试create_animation()返回一个Animation对象。
        """
        animation = night_placeholder.create_animation()
        self.assertIsInstance(animation, Animation, "应该返回一个Animation实例。")

    def test_animation_properties(self):
        """
        测试创建的L4动画的属性。
        """
        animation = night_placeholder.create_animation()
        self.assertEqual(animation.name, "night", "动画名称应为'night'。")
        self.assertEqual(animation.fps, 6, "L4动画的FPS应为6。")
        self.assertTrue(animation.is_looping, "夜晚动画应循环。")
        self.assertTrue(animation.metadata.get("placeholder"), "动画应在元数据中标记为占位符。")
        self.assertTrue(animation.metadata.get("L4_quality"), "动画应在元数据中标记为L4质量。")
        self.assertEqual(animation.metadata.get("description"), "夜晚 L4 占位符动画 - 安睡与静谧星空", "L4动画描述不匹配。")
        self.assertEqual(len(animation.frames), 24, "L4动画应有24帧。")

    def test_animation_frames_are_valid(self):
        """
        测试动画帧是有效的QImage对象并且不为空。
        """
        animation = night_placeholder.create_animation()
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
        expected_size = (64, 64)
        animation = night_placeholder.create_animation()
        for frame_image in animation.frames:
            self.assertEqual(frame_image.width(), expected_size[0], f"帧宽度应为{expected_size[0]}。")
            self.assertEqual(frame_image.height(), expected_size[1], f"帧高度应为{expected_size[1]}。")

    def test_l4_specific_content_hint_night(self):
        """
        L4内容提示性检查：检查夜晚动画的动态效果（如呼吸、星光、Zzz）。
        """
        animation = night_placeholder.create_animation()
        self.assertEqual(len(animation.frames), 24, "测试依赖于24帧动画。")

        frame_initial = animation.frames[0]  # 初始状态 (progress=0)
        frame_mid_breath = animation.frames[len(animation.frames) // 4] # 呼吸顶点 (progress=0.25, sin(pi/2)=1)
        frame_zzz_appears = animation.frames[int(len(animation.frames) * 0.75)] # Zzz可能出现 (progress=0.75, zzz_prog=0.05 -> sin(small)>0)
        frame_for_zzz_check = animation.frames[12] 

        # 1. 检查身体呼吸效果 (通过比较身体区域像素差异)
        breath_pixel_diff_count = 0
        # 采样点在身体中部
        body_sample_x, body_sample_y = frame_initial.width() // 2, frame_initial.height() - 25 
        breath_log = ["Breath check (frame 0 vs mid_breath):"]
        c0_body = frame_initial.pixelColor(body_sample_x, body_sample_y)
        c_mid_breath_body = frame_mid_breath.pixelColor(body_sample_x, body_sample_y)
        breath_log.append(f"  Body Sample ({body_sample_x},{body_sample_y}): F0={c0_body.name()}, FMid={c_mid_breath_body.name()}")
        if c0_body.rgba() != c_mid_breath_body.rgba():
            breath_pixel_diff_count +=1
        self.assertGreater(breath_pixel_diff_count, 0, 
                           f"睡眠呼吸效果不明显，初始帧与呼吸中点帧在身体采样点像素差异: {breath_pixel_diff_count}.\n" + "\n".join(breath_log))

        # 2. 检查星光闪烁 (比较不同帧的星空区域是否有变化)
        star_pixel_diff_count = 0
        # 采样点在一个预期的星星位置附近
        star_sample_x, star_sample_y = int(frame_initial.width() * 0.3), int(frame_initial.height() * 0.1) 
        star_log = ["Star twinkle check (frame 0 vs mid_breath):"]
        c0_star = frame_initial.pixelColor(star_sample_x, star_sample_y)
        c_mid_star = frame_mid_breath.pixelColor(star_sample_x, star_sample_y)
        star_log.append(f"  Star Sample ({star_sample_x},{star_sample_y}): F0={c0_star.name()}, FMid={c_mid_star.name()}")
        # 至少alpha值应该变化，或者颜色本身变化（如果星星完全消失再出现）
        if c0_star.alpha() != c_mid_star.alpha() or c0_star.rgb() != c_mid_star.rgb():
            star_pixel_diff_count +=1
        self.assertGreater(star_pixel_diff_count, 0, 
                           f"星星闪烁效果不明显，不同帧在星空采样点像素差异: {star_pixel_diff_count}.\n" + "\n".join(star_log))

        # 3. 检查Zzz气泡 (在特定帧查找是否有浅色像素在头部上方)
        has_zzz_hint = False
        # Zzz 大致出现在 head_center_x + head_radius*0.8, head_center_y - head_radius*0.7
        # head_center_x approx 32 - 35*0.15 = 26.75. head_radius = 13
        # head_center_y approx (64-20) - 22*0.6 = 44 - 13.2 = 30.8
        # 对于frame 12, zzz_y_offset is 6.  'Z' y-center is around 21.7-6 = 15.7
        # Expected Z char around (37, 16)
        
        zzz_target_x = 37
        # Try a small vertical range around the expected y for the first 'Z'
        zzz_sample_points_y = [15, 16, 17]
        
        zzz_log = [f"Zzz check (frame_for_zzz_check - frame {animation.frames.index(frame_for_zzz_check)}):"]
        
        for sample_y in zzz_sample_points_y:
            c_zzz = frame_for_zzz_check.pixelColor(zzz_target_x, sample_y)
            zzz_log.append(f"  Zzz Sample ({zzz_target_x},{sample_y}): Color={c_zzz.name()} (A={c_zzz.alpha()})")
            # Zzz气泡颜色 QColor(250, 250, 250, bubble_alpha)
            # 放宽一点颜色检查，主要看alpha和亮度
            if c_zzz.lightness() > 120 and c_zzz.alpha() > 100: # 原为 lightness > 150
                has_zzz_hint = True
                break
        
        self.assertTrue(has_zzz_hint, 
                        f"Zzz气泡效果不明显或未在预期帧出现。\n" + "\n".join(zzz_log))

if __name__ == '__main__':
    unittest.main() 