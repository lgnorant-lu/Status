"""
---------------------------------------------------------------
File name:                  idle_placeholder.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                "空闲"状态的L4占位符动画实现
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建;
                            2025/05/15: 提升至L4质量，增加动画细节和帧数;
----
"""
import logging
import math
from typing import List, Optional
from PySide6.QtGui import QImage, QPainter, QColor, QBrush, QPen, QPainterPath
from PySide6.QtCore import Qt, QPointF, QRectF

from status.animation.animation import Animation
from status.behavior.pet_state import PetState

logger = logging.getLogger(__name__)

def _create_idle_frame(width: int = 64, height: int = 64, frame_number: int = 0, total_frames: int = 24) -> Optional[QImage]:
    """为L4空闲动画创建特定帧的图像
    
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
        image.fill(QColor(0, 0, 0, 0))  # 透明背景
        
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 动画参数
        progress = (frame_number % total_frames) / total_frames  # 0.0 to 1.0
        
        # 呼吸效果: 身体轻微起伏
        breath_offset_y = math.sin(progress * 2 * math.pi) * 1.5 # 上下浮动1.5像素
        body_scale_y = 1 + math.sin(progress * 2 * math.pi) * 0.02 # Y轴轻微缩放

        # 耳朵轻微摆动
        ear_angle_offset = math.sin(progress * 2 * math.pi + math.pi / 2) * 3 # 左右摆动3度

        # 尾巴轻微摆动
        tail_sway_x = math.cos(progress * 2 * math.pi) * 2 # X轴摆动
        tail_sway_y = math.sin(progress * 2 * math.pi * 1.5) * 1 # Y轴轻微摆动 (不同频率)

        # --- 绘制猫咪 ---
        pet_center_x = width / 2
        pet_base_y = height - 30 # 猫咪底部基线 (为尾巴留空间)

        # 身体
        body_width = 38
        body_height = 28 * body_scale_y
        body_rect = QRectF(pet_center_x - body_width / 2, 
                           pet_base_y - body_height + breath_offset_y, 
                           body_width, body_height)
        painter.setPen(QPen(QColor(60, 60, 60), 2))
        painter.setBrush(QBrush(QColor(210, 210, 210, 230))) # 浅灰色
        painter.drawEllipse(body_rect)

        # 头部
        head_radius = 18
        head_center_x = pet_center_x
        head_center_y = pet_base_y - body_height * 0.8 + breath_offset_y 
        painter.setBrush(QBrush(QColor(200, 200, 200, 230))) # 略浅的灰色
        painter.drawEllipse(QPointF(head_center_x, head_center_y), head_radius, head_radius)
        
        # 绘制耳朵 (旋转方式实现摆动)
        ear_color = QColor(180, 180, 180, 220)
        painter.setBrush(QBrush(ear_color))
        
        # 左耳
        painter.save()
        painter.translate(head_center_x - head_radius * 0.5, head_center_y - head_radius * 0.6)
        painter.rotate(ear_angle_offset)
        left_ear_path = QPainterPath()
        left_ear_path.moveTo(0, 0)
        left_ear_path.lineTo(-8, -12) # 三角形顶点
        left_ear_path.lineTo(5, -8)  # 三角形底边一点
        left_ear_path.closeSubpath()
        painter.drawPath(left_ear_path)
        painter.restore()

        # 右耳
        painter.save()
        painter.translate(head_center_x + head_radius * 0.5, head_center_y - head_radius * 0.6)
        painter.rotate(-ear_angle_offset) # 反向旋转
        right_ear_path = QPainterPath()
        right_ear_path.moveTo(0, 0)
        right_ear_path.lineTo(8, -12)
        right_ear_path.lineTo(-5, -8)
        right_ear_path.closeSubpath()
        painter.drawPath(right_ear_path)
        painter.restore()

        # 绘制眼睛 (眨眼效果 - 每隔一段时间)
        eye_color = QColor(30, 30, 30)
        painter.setBrush(QBrush(eye_color))
        painter.setPen(Qt.PenStyle.NoPen)
        
        blink_cycle = total_frames * 2 # 假设一个眨眼周期为2倍动画长度
        blink_progress = (frame_number % blink_cycle) / blink_cycle
        eye_open_factor = 1.0
        if blink_progress > 0.9: # 10%的时间用于眨眼
            eye_open_factor = max(0.1, 1.0 - (blink_progress - 0.9) / 0.1 * 5) # 快速闭合和睁开
            if blink_progress > 0.95: # 在闭合的中间阶段再打开一点
                 eye_open_factor = max(0.1, (blink_progress - 0.95) / 0.05 * 5)


        eye_base_y = head_center_y - head_radius * 0.1
        eye_height = 6 * eye_open_factor
        # 左眼
        painter.drawEllipse(QPointF(head_center_x - head_radius * 0.35, eye_base_y), 4, eye_height)
        # 右眼
        painter.drawEllipse(QPointF(head_center_x + head_radius * 0.35, eye_base_y), 4, eye_height)
        
        # 绘制鼻子和嘴巴 (静态)
        nose_color = QColor(255, 150, 150, 220)
        painter.setBrush(QBrush(nose_color))
        painter.drawEllipse(QPointF(head_center_x, head_center_y + head_radius * 0.3), 3, 2.5)
        
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        mouth_y = head_center_y + head_radius * 0.45
        painter.drawLine(QPointF(head_center_x, mouth_y), QPointF(head_center_x, mouth_y + 3))
        painter.drawLine(QPointF(head_center_x, mouth_y + 3), QPointF(head_center_x - 3, mouth_y + 5))
        painter.drawLine(QPointF(head_center_x, mouth_y + 3), QPointF(head_center_x + 3, mouth_y + 5))

        # 绘制尾巴 (曲线，带摆动)
        tail_color = QColor(190, 190, 190, 220)
        painter.setBrush(QBrush(tail_color))
        painter.setPen(QPen(tail_color.darker(110), 2))
        
        tail_path = QPainterPath()
        tail_start_x = pet_center_x + body_width * 0.35
        tail_start_y = pet_base_y - body_height * 0.1 + breath_offset_y

        tail_path.moveTo(tail_start_x, tail_start_y)
        tail_path.quadTo(tail_start_x + 10 + tail_sway_x, tail_start_y + 10 + tail_sway_y, 
                         tail_start_x + 5 + tail_sway_x * 0.5, tail_start_y + 20 + tail_sway_y * 0.8) # 尾巴尖端
        painter.drawPath(tail_path)
        
        painter.end()
        return image
    except Exception as e:
        logger.error(f"创建L4 idle帧 {frame_number} 时出错: {e}", exc_info=True)
        return None

def create_animation() -> Animation:
    """创建\"空闲\"状态的L4占位符动画
    
    Returns:
        Animation: \"空闲\"状态的L4占位符动画对象
    """
    frames: List[QImage] = []
    width, height = 64, 64
    total_animation_frames = 24 # L4动画帧数增加
    fps = 8 # L4动画FPS

    for i in range(total_animation_frames):
        frame_image = _create_idle_frame(width, height, i, total_animation_frames)
        if frame_image:
            frames.append(frame_image)
    
    if not frames:
        logger.warning("未能为IDLE状态创建任何L4帧，动画将为空。将使用单帧回退。")
        # Fallback to a very simple static image if frame creation fails
        fallback_image = QImage(width, height, QImage.Format.Format_ARGB32)
        fallback_image.fill(QColor(0,0,0,0))
        p = QPainter(fallback_image)
        p.setPen(QColor(100,100,100))
        p.setBrush(QColor(200,200,200))
        p.drawEllipse(10,10,44,44) # Simple head
        p.drawText(QRectF(0,0,width,height), Qt.AlignmentFlag.AlignCenter, "IDLE")
        p.end()
        frames.append(fallback_image)

    animation = Animation(name=PetState.IDLE.name.lower(), frames=frames, fps=fps)
    animation.metadata["placeholder"] = True
    animation.metadata["L4_quality"] = True # 标记为L4
    animation.metadata["description"] = "空闲 L4 占位符动画 - 更自然的待机与细节" # L4描述
    animation.set_loop(True)
    
    logger.debug(f"创建了空闲L4状态的占位符动画，共 {len(frames)} 帧。")
    return animation 