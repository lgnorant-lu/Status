"""
---------------------------------------------------------------
File name:                  night_placeholder.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                "夜晚"状态的L4占位符动画实现
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建;
                            2025/05/15: 提升至L4质量，实现睡眠呼吸和星空动画;
----
"""
import logging
import math
from typing import List, Optional
from PySide6.QtGui import QImage, QPainter, QColor, QBrush, QPen, QPainterPath, QLinearGradient, QFont
from PySide6.QtCore import Qt, QPoint, QRect, QPointF, QRectF

from status.animation.animation import Animation
from status.behavior.pet_state import PetState

logger = logging.getLogger(__name__)

def _create_night_frame(width: int = 64, height: int = 64, frame_number: int = 0, total_frames: int = 24) -> Optional[QImage]:
    """为L4夜晚动画创建特定帧的图像 (睡眠呼吸、星空、月亮)
    
    Args:
        width: 图像宽度
        height: 图像高度
        frame_number: 当前帧序号
        total_frames: 总帧数
        
    Returns:
        QImage: 创建的图像，如果失败则为None
    """
    try:
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(QColor(0,0,0,0)) # Transparent background, actual night sky drawn
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        progress = frame_number / total_frames # 0.0 to 1.0

        # 1. 夜空背景 (深蓝色渐变)
        sky_gradient = QLinearGradient(0, 0, 0, height)
        sky_gradient.setColorAt(0, QColor(10, 10, 40, 240)) # 深夜蓝
        sky_gradient.setColorAt(1, QColor(30, 30, 70, 220)) # 略浅的底部
        painter.fillRect(QRect(0,0,width,height), sky_gradient)

        # 2. 月亮 (简单的圆形，略微移动或变化亮度)
        moon_cycle = math.sin(progress * 2 * math.pi * 0.1) # 缓慢的亮度变化周期
        moon_brightness = 200 + int(55 * moon_cycle) # 200 +/- 55
        moon_color = QColor(moon_brightness, moon_brightness, moon_brightness - 20, 240) # 略带黄色的月光
        moon_radius = 7
        moon_x = width * 0.8
        moon_y = height * 0.2 + math.sin(progress * math.pi * 0.5) * 2 # 缓慢上下浮动
        painter.setBrush(QBrush(moon_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(moon_x, moon_y), moon_radius, moon_radius)

        # 3. 闪烁的星星
        num_stars = 10
        star_positions = [
            (width * 0.15, height * 0.18), (width * 0.3, height * 0.1),
            (width * 0.5, height * 0.22), (width * 0.7, height * 0.08),
            (width * 0.9, height * 0.25), (width * 0.2, height * 0.35),
            (width * 0.4, height * 0.45), (width * 0.65, height * 0.3),
            (width * 0.85, height * 0.42), (width*0.05, height*0.5)
        ]
        for i, (sx, sy) in enumerate(star_positions):
            # 每个星星有自己的闪烁周期和相位
            twinkle_progress = (progress + i * 0.1) % 1.0 
            star_alpha = 0
            if twinkle_progress < 0.3:
                star_alpha = int( (twinkle_progress / 0.3) * 200 )
            elif twinkle_progress < 0.6:
                star_alpha = 200
            elif twinkle_progress < 0.9:
                star_alpha = int( (1 - (twinkle_progress - 0.6)/0.3) * 200)
            
            if star_alpha > 20:
                star_size = 1 + (i % 2) # 大小交替
                painter.setBrush(QBrush(QColor(240, 240, 220, star_alpha)))
                painter.drawEllipse(QPointF(sx, sy), star_size, star_size)

        # 4. 熟睡的猫咪
        body_color = QColor(80, 80, 100, 220) # 深灰色，夜晚色调
        darker_body_color = body_color.darker(120)
        
        pet_center_x = width / 2
        pet_base_y = height - 20 # 猫咪底部基线

        # 呼吸效果: 身体轻微起伏
        breath_offset_y = math.sin(progress * 2 * math.pi) * 1.5 # 上下浮动1.5像素 (原为1.0)
        body_scale_y = 1 + math.sin(progress * 2 * math.pi) * 0.025 # Y轴轻微缩放 (原为0.015)

        # 身体 (躺卧姿势)
        body_width = 35
        body_height = 22 * body_scale_y
        body_rect = QRectF(pet_center_x - body_width / 2, 
                           pet_base_y - body_height + breath_offset_y, 
                           body_width, body_height)
        painter.setPen(QPen(darker_body_color, 1.5))
        painter.setBrush(QBrush(body_color))
        painter.drawEllipse(body_rect)

        # 头部 (靠在身体上)
        head_radius = 13
        head_center_x = pet_center_x - body_width * 0.15
        head_center_y = pet_base_y - body_height * 0.6 + breath_offset_y 
        painter.drawEllipse(QPointF(head_center_x, head_center_y), head_radius, head_radius)
        
        # 耳朵 (放松下垂)
        ear_color = body_color.lighter(110)
        painter.setBrush(QBrush(ear_color))
        # 左耳
        left_ear_path = QPainterPath()
        left_ear_path.moveTo(head_center_x - head_radius * 0.5, head_center_y - head_radius * 0.3)
        left_ear_path.quadTo(head_center_x - head_radius * 0.9, head_center_y + head_radius * 0.5, 
                           head_center_x - head_radius * 0.3, head_center_y + head_radius * 0.6)
        painter.drawPath(left_ear_path)
        # 右耳 (大部分被头挡住，只露一点)
        right_ear_path = QPainterPath()
        right_ear_path.moveTo(head_center_x + head_radius * 0.5, head_center_y - head_radius * 0.2)
        right_ear_path.quadTo(head_center_x + head_radius * 0.8, head_center_y + head_radius * 0.4, 
                            head_center_x + head_radius * 0.4, head_center_y + head_radius * 0.5)
        painter.drawPath(right_ear_path)

        # 闭着的眼睛 (弯月形)
        eye_color = darker_body_color.darker(110)
        painter.setPen(QPen(eye_color, 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        eye_y = head_center_y + head_radius * 0.1
        # 左眼
        left_eye_rect = QRectF(head_center_x - head_radius*0.5, eye_y - head_radius*0.1, head_radius*0.4, head_radius*0.3)
        painter.drawArc(left_eye_rect, 45*16, 90*16)
        # 右眼
        right_eye_rect = QRectF(head_center_x + head_radius*0.1, eye_y - head_radius*0.1, head_radius*0.4, head_radius*0.3)
        painter.drawArc(right_eye_rect, 45*16, 90*16)
        
        # 偶尔出现的 Zzz 气泡
        zzz_progress = (progress + 0.3) % 1.0 # 调整相位
        if zzz_progress > 0.7 and zzz_progress < 0.95: # 在周期的特定时间出现
            bubble_alpha = int(math.sin((zzz_progress - 0.7) / 0.25 * math.pi) * 150) # 淡入淡出
            if bubble_alpha > 20:
                font = QFont("Comic Sans MS", 14)
                font.setWeight(QFont.Weight.Bold)
                painter.setFont(font)
                painter.setPen(QColor(250, 250, 250, bubble_alpha))
                # 简单的上升效果
                zzz_y_offset = (0.95 - zzz_progress) / 0.25 * 10 # 从0到10向上移动
                painter.drawText(QPointF(head_center_x + head_radius*0.8, head_center_y - head_radius*0.7 - zzz_y_offset), "Z")
                painter.drawText(QPointF(head_center_x + head_radius, head_center_y - head_radius*0.9 - zzz_y_offset -2), "z") 
                painter.drawText(QPointF(head_center_x + head_radius*1.2, head_center_y - head_radius*1.1 - zzz_y_offset -4), "z")

        painter.end()
        return image
    except Exception as e:
        logger.error(f"创建L4 night帧 {frame_number} 时出错: {e}", exc_info=True)
        return None

def create_animation() -> Animation:
    """创建\"夜晚\"状态的L4占位符动画
    
    Returns:
        Animation: \"夜晚\"状态的L4占位符动画对象
    """
    frames: List[QImage] = []
    width, height = 64, 64
    total_animation_frames = 24 # L4动画帧数
    fps = 6 # L4 FPS, 夜晚更慢

    for i in range(total_animation_frames):
        frame_image = _create_night_frame(width, height, i, total_animation_frames)
        if frame_image:
            frames.append(frame_image)
    
    if not frames:
        logger.warning("未能为NIGHT状态创建任何L4帧，动画将为空。将使用单帧回退。")
        fallback_image = QImage(width, height, QImage.Format.Format_ARGB32)
        fallback_image.fill(QColor(20,20,60,200))
        p = QPainter(fallback_image)
        p.setPen(QColor(200,200,255))
        p.drawText(QRectF(0,0,width,height), Qt.AlignmentFlag.AlignCenter, "L4 Zzz...")
        p.end()
        frames.append(fallback_image)

    animation = Animation(name=PetState.NIGHT.name.lower(), frames=frames, fps=fps)
    animation.metadata["placeholder"] = True
    animation.metadata["L4_quality"] = True
    animation.metadata["description"] = "夜晚 L4 占位符动画 - 安睡与静谧星空"
    animation.set_loop(True)
    
    logger.debug(f"创建了夜晚L4状态的占位符动画，共 {len(frames)} 帧。")
    return animation 