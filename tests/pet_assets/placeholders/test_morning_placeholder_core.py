"""
---------------------------------------------------------------
File name:                  test_morning_placeholder_core.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                早晨L4占位符核心模块的单元测试
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
from status.pet_assets.placeholders import morning_placeholder

class TestMorningPlaceholderCore(unittest.TestCase):
    """
    早晨L4占位符核心模块的单元测试
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
        animation = morning_placeholder.create_animation()
        self.assertIsInstance(animation, Animation, "应该返回一个Animation实例。")

    def test_animation_properties(self):
        """
        测试创建的L4动画的属性。
        """
        animation = morning_placeholder.create_animation()
        self.assertEqual(animation.name, "morning", "动画名称应为'morning'。")
        self.assertEqual(animation.fps, 10, "L4动画的FPS应为10。")
        self.assertTrue(animation.is_looping, "早晨动画应循环。")
        self.assertTrue(animation.metadata.get("placeholder"), "动画应在元数据中标记为占位符。")
        self.assertTrue(animation.metadata.get("L4_quality"), "动画应在元数据中标记为L4质量。")
        self.assertEqual(animation.metadata.get("description"), "早晨 L4 占位符动画 - 伸懒腰与晨光", "L4动画描述不匹配。")
        self.assertEqual(len(animation.frames), 20, "L4动画应有20帧。")

    def test_animation_frames_are_valid(self):
        """
        测试动画帧是有效的QImage对象并且不为空。
        """
        animation = morning_placeholder.create_animation()
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
        animation = morning_placeholder.create_animation()
        for frame_image in animation.frames:
            self.assertEqual(frame_image.width(), expected_size[0], f"帧宽度应为{expected_size[0]}。")
            self.assertEqual(frame_image.height(), expected_size[1], f"帧高度应为{expected_size[1]}。")

    def test_l4_specific_content_hint_morning(self):
        """
        L4内容提示性检查：检查早晨动画的动态效果（如身体姿态变化、晨光）。
        """
        animation = morning_placeholder.create_animation()
        self.assertEqual(len(animation.frames), 20, "测试依赖于20帧动画。")

        frame_initial = animation.frames[0]  # 初始状态 (progress=0)
        frame_stretch_peak = animation.frames[4] # 伸懒腰顶峰附近 (progress=0.2, stretch_progress=0.4)
        frame_yawn_peak = animation.frames[14] # 打哈欠顶峰附近 (progress=0.7, yawn_progress=0.4)
        frame_sun_mid = animation.frames[9] # 晨光效果较明显时 (progress=0.45, sun_progress=0.9)

        # 1. 检查身体姿态变化 (伸懒腰/打哈欠)
        body_pixel_diff_count_stretch = 0
        sample_points_body = [
            (frame_initial.width() // 2, frame_initial.height() // 2), # 中心点
            (frame_initial.width() // 2, frame_initial.height() // 3), # 头部大致区域
            (frame_initial.width() // 2, frame_initial.height() * 2 // 3)  # 身体大致区域
        ]
        stretch_log = ["Stretch check (frame 0 vs 4):"]
        for x, y in sample_points_body:
            c0 = frame_initial.pixelColor(x,y)
            c_stretch = frame_stretch_peak.pixelColor(x,y)
            stretch_log.append(f"  Sample ({x},{y}): F0={c0.name()}, F4={c_stretch.name()}")
            if c0.rgba() != c_stretch.rgba():
                body_pixel_diff_count_stretch +=1
        self.assertGreater(body_pixel_diff_count_stretch, 0, 
                           f"伸懒腰效果不明显，初始帧与伸懒腰帧像素差异点数: {body_pixel_diff_count_stretch}.\n" + "\n".join(stretch_log))

        mouth_pixel_changed_for_yawn = False
        # 粗略估计打哈欠时嘴巴中心y坐标: head_base_y(约25.4) + mouth_y_center_local(约4.8) -> 约30
        # 头部可能会有tilt，所以实际采样点可能需要微调
        mouth_sample_x, mouth_sample_y = frame_initial.width() // 2, 30 
        yawn_log = ["Yawn check (mouth area frame 0 vs 14):"]
        c0_mouth_area = frame_initial.pixelColor(mouth_sample_x, mouth_sample_y)
        c_yawn_mouth_area = frame_yawn_peak.pixelColor(mouth_sample_x, mouth_sample_y)
        yawn_log.append(f"  Mouth Sample ({mouth_sample_x},{mouth_sample_y}): F0={c0_mouth_area.name()}, F14={c_yawn_mouth_area.name()}")
        
        # 检查颜色是否显著变化，并且打哈欠帧的嘴部颜色是否偏红
        if c0_mouth_area.rgba() != c_yawn_mouth_area.rgba():
            yawn_log.append(f"    INFO: Mouth area color DID change. Initial: {c0_mouth_area.name()}, Yawn: {c_yawn_mouth_area.name()}")
            # 检查打哈欠时嘴部颜色是否偏红 (舌头)
            # 要求红色分量显著高于绿色和蓝色分量，并且有一定alpha值
            if (c_yawn_mouth_area.red() > c_yawn_mouth_area.green() + 20 and 
                c_yawn_mouth_area.red() > c_yawn_mouth_area.blue() + 20 and 
                c_yawn_mouth_area.red() > 150 and 
                c_yawn_mouth_area.alpha() > 100):
                mouth_pixel_changed_for_yawn = True
                yawn_log.append(f"    SUCCESS: Yawn mouth color F14={c_yawn_mouth_area.name()} is reddish as expected.")
            else:
                yawn_log.append(f"    WARN: Yawn mouth color F14={c_yawn_mouth_area.name()} (R={c_yawn_mouth_area.red()}, G={c_yawn_mouth_area.green()}, B={c_yawn_mouth_area.blue()}) not distinctly reddish as expected.")
        else:
             yawn_log.append(f"    FAIL: Mouth area color did NOT change between F0 and F14 at ({mouth_sample_x},{mouth_sample_y}). Both are {c0_mouth_area.name()}")

        self.assertTrue(mouth_pixel_changed_for_yawn, 
                           f"打哈欠效果不明显或嘴部颜色不符合预期（需要红色调且与初始帧不同）。\n" + "\n".join(yawn_log))

        # 2. 检查晨光效果 (底部是否出现暖色调，且与初始帧不同)
        has_sun_hint = False
        bottom_sample_y = frame_sun_mid.height() - 10 # 靠近底部
        sun_log = ["Sun effect check (frame 0 vs 9 at bottom):"]
        sun_points_checked = 0
        sun_points_changed_and_warm = 0

        for x_offset_factor in [-0.25, 0, 0.25]: # 采样底部左中右区域
            x = int(frame_sun_mid.width() / 2 + frame_sun_mid.width() * x_offset_factor)
            c_initial_bottom = frame_initial.pixelColor(x, bottom_sample_y)
            c_sun_bottom = frame_sun_mid.pixelColor(x, bottom_sample_y)
            sun_log.append(f"  Sample ({x},{bottom_sample_y}): InitialBottom={c_initial_bottom.name()}, SunBottom={c_sun_bottom.name()}")
            sun_points_checked += 1
            if c_initial_bottom.rgba() != c_sun_bottom.rgba(): # 必须与初始帧不同
                # 检查颜色是否为暖色调 (黄/橙/浅红)
                if c_sun_bottom.red() > 180 and c_sun_bottom.green() > 150 and c_sun_bottom.blue() < 200 and c_sun_bottom.alpha() > 50:
                    sun_points_changed_and_warm +=1
                    sun_log.append("    -> Sun hint FOUND: changed and warm.")
                else:
                    sun_log.append("    -> Changed but NOT WARM enough: R={c_sun_bottom.red()} G={c_sun_bottom.green()} B={c_sun_bottom.blue()} A={c_sun_bottom.alpha()}")
            else:
                sun_log.append("    -> No change from initial frame at this sun sample point.")

        if sun_points_checked > 0 and sun_points_changed_and_warm > 0:
            has_sun_hint = True
            
        self.assertTrue(has_sun_hint, 
                        f"晨光效果不明显，底部区域颜色应变为暖色调且与初始帧不同。符合条件的点: {sun_points_changed_and_warm}/{sun_points_checked}.\n" + "\n".join(sun_log))

if __name__ == '__main__':
    unittest.main() 