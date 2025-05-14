"""
---------------------------------------------------------------
File name:                  morning_placeholder.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                "早晨"状态的L4占位符动画实现
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建;
                            2025/05/15: 提升至L4质量，实现伸懒腰和打哈欠动画;
----
"""
import logging
import math
from typing import List, Optional
from PySide6.QtGui import QImage, QPainter, QColor, QBrush, QPen, QPainterPath, QLinearGradient, QRadialGradient
from PySide6.QtCore import Qt, QPoint, QRect, QPointF, QRectF

from status.animation.animation import Animation
from status.behavior.pet_state import PetState

logger = logging.getLogger(__name__)

def _create_morning_frame(width: int = 64, height: int = 64, frame_number: int = 0, total_frames: int = 20) -> Optional[QImage]:
    """为L4早晨动画创建特定帧的图像 (伸懒腰、打哈欠、晨光)
    
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
        image.fill(QColor(0,0,0,0)) # Transparent
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        progress = frame_number / total_frames # 0.0 to 1.0

        # 1. 晨光背景 (从底部升起的柔和光晕)
        sun_progress = min(1.0, progress * 2) # 晨光在动画前半段完全升起
        sun_radius = width * 0.8 * sun_progress
        sun_center_y = height + width * 0.5 - (width * 0.8 * sun_progress) 
        
        if sun_radius > 0:
            radial_grad = QRadialGradient(QPointF(width / 2, sun_center_y), sun_radius)
            light_yellow = QColor(255, 255, 200, int(100 * sun_progress)) # 中心较亮
            transparent_yellow = QColor(255, 255, 200, 0) # 边缘透明
            radial_grad.setColorAt(0, light_yellow)
            radial_grad.setColorAt(0.6, QColor(255, 230, 180, int(80*sun_progress)))
            radial_grad.setColorAt(1, transparent_yellow)
            painter.setBrush(QBrush(radial_grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(width / 2, sun_center_y), sun_radius, sun_radius)

        # 2. 猫咪动画 (前伸懒腰 -> 打哈欠)
        # 动画分为两部分：0-0.5 伸懒腰，0.5-1.0 打哈欠
        body_color = QColor(220, 200, 180, 230) # 米黄色
        darker_body_color = body_color.darker(120)
        
        pet_center_x = width / 2
        pet_base_y = height - 15 # 猫咪底部基线

        # 通用头部绘制函数
        def draw_head(h_center_x, h_center_y, h_radius, eye_open_factor, mouth_open_factor):
            painter.setPen(QPen(darker_body_color, 1.5))
            painter.setBrush(QBrush(body_color))
            painter.drawEllipse(QPointF(h_center_x, h_center_y), h_radius, h_radius)
            # Ears
            ear_h = h_radius * 0.7
            ear_w = h_radius * 0.5
            painter.drawPolygon([QPointF(h_center_x - h_radius*0.3, h_center_y - h_radius*0.4),
                                 QPointF(h_center_x - h_radius*0.6, h_center_y - h_radius*0.4 - ear_h),
                                 QPointF(h_center_x - h_radius*0.1, h_center_y - h_radius*0.5)])
            painter.drawPolygon([QPointF(h_center_x + h_radius*0.3, h_center_y - h_radius*0.4),
                                 QPointF(h_center_x + h_radius*0.6, h_center_y - h_radius*0.4 - ear_h),
                                 QPointF(h_center_x + h_radius*0.1, h_center_y - h_radius*0.5)])
            # Eyes
            eye_y = h_center_y - h_radius * 0.1
            eye_h = h_radius * 0.3 * max(0.1, eye_open_factor) # 最小高度防止完全消失
            painter.setBrush(QColor(30,30,30))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(h_center_x - h_radius*0.45, eye_y - eye_h/2, h_radius*0.3, eye_h))
            painter.drawEllipse(QRectF(h_center_x + h_radius*0.15, eye_y - eye_h/2, h_radius*0.3, eye_h))
            # Mouth (打哈欠时张大)
            mouth_y_center = h_center_y + h_radius * 0.4
            mouth_h = h_radius * 0.5 * mouth_open_factor
            mouth_w = h_radius * 0.6
            if mouth_h > 1:
                painter.setBrush(QColor(200, 100, 100, 200)) # 舌头颜色
                painter.drawEllipse(QRectF(h_center_x - mouth_w/2, mouth_y_center - mouth_h/2, mouth_w, mouth_h))
            else: # 微笑
                painter.setPen(QPen(darker_body_color,1))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawArc(QRectF(h_center_x - mouth_w/3, mouth_y_center-mouth_h/3 , mouth_w*2/3, mouth_h*2/3), 0, -180*16)

        if progress < 0.5: # 伸懒腰
            stretch_progress = progress / 0.5 # 0 to 1
            # 身体前倾，拉长
            body_angle = -15 * math.sin(stretch_progress * math.pi) # 向前倾斜最多15度
            body_length_scale = 1 + 0.3 * math.sin(stretch_progress * math.pi) # 身体拉长
            body_height_scale = 1 - 0.2 * math.sin(stretch_progress * math.pi) # 身体压扁

            body_w = 25 * body_length_scale
            body_h = 20 * body_height_scale
            head_r = 12

            painter.save()
            painter.translate(pet_center_x, pet_base_y - body_h/2)
            painter.rotate(body_angle)
            
            # Body
            painter.setPen(QPen(darker_body_color, 1.5))
            painter.setBrush(QBrush(body_color))
            painter.drawEllipse(QRectF(-body_w/2, -body_h/2, body_w, body_h))
            
            # Head (位置相对于身体前端)
            head_local_x = body_w/2 
            head_local_y = 0
            draw_head(head_local_x, head_local_y, head_r, 1 - 0.8 * math.sin(stretch_progress*math.pi), 0.2) # 伸懒腰时眼睛眯起
            
            # Paws (向前伸)
            paw_length = 15 * math.sin(stretch_progress*math.pi)
            painter.setBrush(QBrush(body_color.lighter(110)))
            if paw_length > 1:
                painter.drawEllipse(QRectF(head_local_x + head_r*0.5, head_local_y + head_r*0.2 - 3, paw_length, 6))
                painter.drawEllipse(QRectF(head_local_x + head_r*0.5, head_local_y - head_r*0.2 - 3, paw_length, 6))
            painter.restore()

        else: # 打哈欠
            yawn_progress = (progress - 0.5) / 0.5 # 0 to 1
            # 身体恢复，头部略微后仰然后向前
            head_tilt = math.sin(yawn_progress * math.pi) * 10 # 后仰再恢复
            mouth_open = math.sin(yawn_progress * math.pi) # 张嘴幅度
            eye_squeeze = abs(math.sin(yawn_progress * math.pi * 1.5)) # 打哈欠时眼睛眯得更紧
            
            body_w = 25
            body_h = 20
            head_r = 12
            head_base_x = pet_center_x
            head_base_y = pet_base_y - body_h * 0.7 - head_r * 0.8

            painter.setPen(QPen(darker_body_color, 1.5))
            painter.setBrush(QBrush(body_color))
            painter.drawEllipse(QRectF(pet_center_x - body_w/2, pet_base_y - body_h, body_w, body_h)) # Body
            
            painter.save()
            painter.translate(head_base_x, head_base_y)
            painter.rotate(-head_tilt)
            draw_head(0, 0, head_r, 1 - 0.9*eye_squeeze, mouth_open)
            painter.restore()
            
        painter.end()
        return image
    except Exception as e:
        logger.error(f"创建L4 morning帧 {frame_number} 时出错: {e}", exc_info=True)
        return None

def create_animation() -> Animation:
    """创建\"早晨\"状态的L4占位符动画
    
    Returns:
        Animation: \"早晨\"状态的L4占位符动画对象
    """
    frames: List[QImage] = []
    width, height = 64, 64
    total_animation_frames = 20 # L4动画帧数
    fps = 10 # L4 FPS

    for i in range(total_animation_frames):
        frame_image = _create_morning_frame(width, height, i, total_animation_frames)
        if frame_image:
            frames.append(frame_image)
    
    if not frames:
        logger.warning("未能为MORNING状态创建任何L4帧，动画将为空。将使用单帧回退。")
        fallback_image = QImage(width, height, QImage.Format.Format_ARGB32)
        fallback_image.fill(QColor(255,250,220,100))
        p = QPainter(fallback_image)
        p.drawText(QRectF(0,0,width,height), Qt.AlignmentFlag.AlignCenter, "L4 Morning")
        p.end()
        frames.append(fallback_image)

    animation = Animation(name=PetState.MORNING.name.lower(), frames=frames, fps=fps)
    animation.metadata["placeholder"] = True
    animation.metadata["L4_quality"] = True
    animation.metadata["description"] = "早晨 L4 占位符动画 - 伸懒腰与晨光"
    animation.set_loop(True)
    
    logger.debug(f"创建了早晨L4状态的占位符动画，共 {len(frames)} 帧。")
    return animation 