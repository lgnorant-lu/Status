"""
---------------------------------------------------------------
File name:                  test_clicked_placeholder_core.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                点击L4占位符核心模块的单元测试
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
from status.pet_assets.placeholders import clicked_placeholder

class TestClickedPlaceholderCore(unittest.TestCase):
    """
    点击L4占位符核心模块的单元测试
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
        animation = clicked_placeholder.create_animation()
        self.assertIsInstance(animation, Animation, "应该返回一个Animation实例。")

    def test_animation_properties(self):
        """
        测试创建的L4动画的属性。
        """
        animation = clicked_placeholder.create_animation()
        self.assertEqual(animation.name, "clicked", "动画名称应为'clicked'。")
        self.assertEqual(animation.fps, 12, "L4动画的FPS应为12。")
        self.assertFalse(animation.is_looping, "点击动画不应循环。")
        self.assertTrue(animation.metadata.get("placeholder"), "动画应在元数据中标记为占位符。")
        self.assertTrue(animation.metadata.get("L4_quality"), "动画应在元数据中标记为L4质量。")
        self.assertEqual(animation.metadata.get("description"), "点击 L4 占位符动画 - Q弹的点击反馈与惊讶表情", "L4动画描述不匹配。")
        self.assertEqual(len(animation.frames), 16, "L4动画应有16帧。")

    def test_animation_frames_are_valid(self):
        """
        测试动画帧是有效的QImage对象并且不为空。
        """
        animation = clicked_placeholder.create_animation()
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
        animation = clicked_placeholder.create_animation()
        for frame_image in animation.frames:
            self.assertEqual(frame_image.width(), expected_size[0], f"帧宽度应为{expected_size[0]}。")
            self.assertEqual(frame_image.height(), expected_size[1], f"帧高度应为{expected_size[1]}。")

    def test_l4_specific_content_hint_clicked(self):
        """L4内容提示性检查：检查点击动画的动态效果（如身体变形或星光）。"""
        animation = clicked_placeholder.create_animation()
        self.assertEqual(len(animation.frames), 16, "测试依赖于16帧动画。")

        frame_initial = animation.frames[0]  # 初始状态
        # 选择变形更剧烈的帧进行比较
        # frame_number = 1 (progress = 0.0625) -> squash_factor_y=0.75, squash_factor_x=1.125
        # frame_number = 2 (progress = 0.125) -> sub_progress=(0.125-0.1)/0.4 = 0.025/0.4 = 0.0625
        #                                   squash_factor_y = 0.6 + 0.0625*0.2 = 0.6125
        #                                   squash_factor_x = 1.2 - 0.0625*0.1 = 1.19375
        frame_deformed = animation.frames[2] # 第2帧，变形应该比较明显
        frame_star_effect = animation.frames[2] # 星光效果也可能在第2帧

        # 1. 检查身体变形 (比较多个采样点的像素差异)
        pixel_diff_count = 0
        sample_points_deformation = [
            (frame_initial.width() // 2, frame_initial.height() // 2), # 中心
            (frame_initial.width() // 4, frame_initial.height() // 2), # 左中
            (frame_initial.width() * 3 // 4, frame_initial.height() // 2), # 右中
            (frame_initial.width() // 2, frame_initial.height() // 4), # 上中
            (frame_initial.width() // 2, frame_initial.height() * 3 // 4)  # 下中
        ]

        log_messages = ["Deformation check:"]
        for x, y in sample_points_deformation:
            color_initial = frame_initial.pixelColor(x, y)
            color_deformed = frame_deformed.pixelColor(x, y)
            log_messages.append(f"  Sample ({x},{y}): Initial={color_initial.name()}, Deformed={color_deformed.name()}")
            if color_initial.rgba() != color_deformed.rgba():
                pixel_diff_count += 1
        
        self.assertGreater(pixel_diff_count, 0, 
                         ("点击动画的初始帧和变形帧之间应存在像素差异，暗示变形。 "
                          f"差异点数: {pixel_diff_count}.\n" + "\n".join(log_messages)))

        # 2. 检查星光效果 (在特定帧查找是否有接近黄色的像素)
        has_star_hint = False
        star_color_base = QColor(255, 255, 100) # 黄色系基准
        # 增加更多采样点，特别是身体周围
        body_rect_approx_center_x = frame_star_effect.width() // 2
        body_rect_approx_center_y = frame_star_effect.height() // 2
        body_w_approx = frame_star_effect.width() * 0.6 
        body_h_approx = frame_star_effect.height() * 0.5 * (0.6125) # squash_factor_y for frame 2

        sample_points_star = [
            # 原有采样点
            (frame_star_effect.width() // 4, frame_star_effect.height() // 4), # (16,16)
            (frame_star_effect.width() * 3 // 4, frame_star_effect.height() // 4),# (48,16)
            (frame_star_effect.width() // 2, frame_star_effect.height() // 2), # (32,32)
            # 新增采样点，围绕变形后的身体区域
            (int(body_rect_approx_center_x - body_w_approx*0.4), int(body_rect_approx_center_y - body_h_approx*0.4)),
            (int(body_rect_approx_center_x + body_w_approx*0.4), int(body_rect_approx_center_y - body_h_approx*0.4)),
            (int(body_rect_approx_center_x - body_w_approx*0.4), int(body_rect_approx_center_y + body_h_approx*0.4)),
            (int(body_rect_approx_center_x + body_w_approx*0.4), int(body_rect_approx_center_y + body_h_approx*0.4)),
            (int(body_rect_approx_center_x), int(body_rect_approx_center_y - body_h_approx*0.3)), # Body top-center
            (int(body_rect_approx_center_x), int(body_rect_approx_center_y + body_h_approx*0.3)), # Body bottom-center
        ]
        star_log_messages = ["Star effect check (frame 2):EXPECTING YELLOWISH STARS"]
        for x, y in sample_points_star:
            # 确保采样点在图像范围内
            if not (0 <= x < frame_star_effect.width() and 0 <= y < frame_star_effect.height()):
                star_log_messages.append(f"  Sample ({x},{y}): Out of bounds")
                continue
            pixel_color = frame_star_effect.pixelColor(x, y)
            star_log_messages.append(f"  Sample ({x},{y}): Color={pixel_color.name()} (R={pixel_color.red()}, G={pixel_color.green()}, B={pixel_color.blue()}, A={pixel_color.alpha()})")
            # 简单颜色比较：红色和绿色分量较高，蓝色较低，且alpha不低于80 (略微放宽)
            if pixel_color.red() > 180 and pixel_color.green() > 180 and pixel_color.blue() < 180 and pixel_color.alpha() > 80:
                has_star_hint = True
                star_log_messages.append(f"    -> STAR HINT FOUND AT ({x},{y})!")
                break
        self.assertTrue(has_star_hint, 
                        ("点击动画的特定帧 (如第2帧) 应包含星光效果的视觉提示 (黄色系像素)。" 
                         f"未找到明显星光.\n" + "\n".join(star_log_messages)))

if __name__ == '__main__':
    unittest.main() 