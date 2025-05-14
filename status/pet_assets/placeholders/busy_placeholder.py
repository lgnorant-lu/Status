"""
---------------------------------------------------------------
File name:                  busy_placeholder.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                "忙碌"状态的L4占位符动画实现
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建;
                            2025/05/15: 提升至L4质量，实现打字动画;
----
"""
import logging
import math
from typing import List, Optional
from PySide6.QtGui import QImage, QPainter, QColor, QBrush, QPen, QPainterPath, QPolygonF
from PySide6.QtCore import Qt, QPoint, QPointF, QRectF

from status.animation.animation import Animation
from status.behavior.pet_state import PetState

logger = logging.getLogger(__name__)

def _create_busy_frame(width: int = 64, height: int = 64, frame_number: int = 0, total_frames: int = 30) -> Optional[QImage]:
    """为L4忙碌动画（打字）创建特定帧的图像
    
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
        
        progress = (frame_number % total_frames) / total_frames
        cycle_progress = (frame_number % (total_frames // 2)) / (total_frames // 2) # 用于左右手交替

        # 猫咪身体和头部 (略微上下晃动)
        bob_offset_y = math.sin(progress * 4 * math.pi) * 1 # 快速晃动
        pet_base_y = height - 25

        # 头部
        head_radius = 16
        head_center_x = width / 2
        head_center_y = pet_base_y - 30 + bob_offset_y
        painter.setPen(QPen(QColor(60, 60, 60), 1.5))
        painter.setBrush(QBrush(QColor(200, 200, 200, 230)))
        painter.drawEllipse(QPointF(head_center_x, head_center_y), head_radius, head_radius)

        # 耳朵 (专注时略微前倾或竖起)
        ear_color = QColor(180, 180, 180, 220)
        painter.setBrush(QBrush(ear_color))
        # 左耳 (更竖直)
        left_ear_path = QPainterPath()
        left_ear_path.moveTo(head_center_x - head_radius * 0.4, head_center_y - head_radius * 0.5)
        left_ear_path.lineTo(head_center_x - head_radius * 0.6, head_center_y - head_radius * 1.2)
        left_ear_path.lineTo(head_center_x - head_radius * 0.1, head_center_y - head_radius * 0.7)
        left_ear_path.closeSubpath()
        painter.drawPath(left_ear_path)
        # 右耳
        right_ear_path = QPainterPath()
        right_ear_path.moveTo(head_center_x + head_radius * 0.4, head_center_y - head_radius * 0.5)
        right_ear_path.lineTo(head_center_x + head_radius * 0.6, head_center_y - head_radius * 1.2)
        right_ear_path.lineTo(head_center_x + head_radius * 0.1, head_center_y - head_radius * 0.7)
        right_ear_path.closeSubpath()
        painter.drawPath(right_ear_path)
        
        # 眼睛 (专注，看向键盘方向)
        eye_color = QColor(30, 30, 30)
        painter.setBrush(QBrush(eye_color))
        painter.setPen(Qt.PenStyle.NoPen)
        eye_y_offset = head_radius * 0.1 # 眼睛略微向下看
        # 左眼 (椭圆，模拟专注)
        painter.drawEllipse(QRectF(head_center_x - head_radius * 0.5, head_center_y + eye_y_offset - 2.5, 6, 5))
        # 右眼
        painter.drawEllipse(QRectF(head_center_x + head_radius * 0.5 - 6, head_center_y + eye_y_offset - 2.5, 6, 5))

        # 键盘
        kb_height = 15
        kb_width = 45
        kb_x = (width - kb_width) / 2
        kb_y = height - kb_height - 5 # 键盘在底部
        painter.setBrush(QBrush(QColor(80, 80, 90, 220)))
        painter.setPen(QPen(QColor(50,50,60), 1))
        painter.drawRoundedRect(QRectF(kb_x, kb_y, kb_width, kb_height), 3, 3)
        # 键盘上的按键暗示 (几条线)
        for i in range(1, 4):
            painter.drawLine(QPointF(kb_x + 5, kb_y + kb_height * i / 4), QPointF(kb_x + kb_width - 5, kb_y + kb_height * i / 4))
        for i in range(1, 6):
             painter.drawLine(QPointF(kb_x + kb_width * i / 6, kb_y + 5), QPointF(kb_x + kb_width * i / 6, kb_y + kb_height - 5))

        # 爪子/手 (交替敲击键盘)
        paw_color = QColor(210, 210, 210, 230)
        painter.setBrush(QBrush(paw_color))
        painter.setPen(QPen(QColor(150,150,150),1))
        paw_size = 8
        
        # 左手
        left_paw_x = kb_x + kb_width * 0.25
        left_paw_y_base = kb_y - paw_size * 0.3
        left_paw_y = left_paw_y_base - (math.sin(cycle_progress * 2 * math.pi) * 3 if cycle_progress < 0.5 else 0) # 前半周期抬起
        painter.drawEllipse(QPointF(left_paw_x, left_paw_y), paw_size, paw_size * 0.8)
        if cycle_progress > 0.4 and cycle_progress < 0.6: # 按下时的效果
             painter.setPen(QPen(QColor(255,255,100,150), 2))
             painter.drawLine(QPointF(left_paw_x, left_paw_y + paw_size*0.4), QPointF(left_paw_x, left_paw_y + paw_size*0.4 - 5)) # 向上的小线条

        # 右手
        right_paw_x = kb_x + kb_width * 0.75
        right_paw_y_base = kb_y - paw_size * 0.3
        right_paw_y = right_paw_y_base - (math.sin(cycle_progress * 2 * math.pi) * 3 if cycle_progress >= 0.5 else 0) # 后半周期抬起
        painter.setBrush(QBrush(paw_color))
        painter.setPen(QPen(QColor(150,150,150),1))
        painter.drawEllipse(QPointF(right_paw_x, right_paw_y), paw_size, paw_size * 0.8)
        if cycle_progress > 0.9 or cycle_progress < 0.1: # 按下时的效果
             painter.setPen(QPen(QColor(255,255,100,150), 2))
             painter.drawLine(QPointF(right_paw_x, right_paw_y + paw_size*0.4), QPointF(right_paw_x, right_paw_y + paw_size*0.4 - 5))

        # 努力的汗珠 (随机出现一个)
        if frame_number % (total_frames // 3) == 0 and frame_number > 0: # 每1/3周期出现一次
            sweat_x = head_center_x + head_radius * 0.7 * (1 if frame_number % 2 == 0 else -1) # 左右交替
            sweat_y = head_center_y - head_radius * 0.5
            painter.setBrush(QBrush(QColor(150, 200, 255, 200)))
            painter.setPen(Qt.PenStyle.NoPen)
            sweat_path = QPainterPath()
            sweat_path.moveTo(sweat_x, sweat_y)
            sweat_path.quadTo(sweat_x + 2, sweat_y + 5, sweat_x, sweat_y + 7)
            sweat_path.quadTo(sweat_x - 2, sweat_y + 5, sweat_x, sweat_y)
            painter.drawPath(sweat_path)

        painter.end()
        return image
    except Exception as e:
        logger.error(f"创建L4 busy帧 {frame_number} 时出错: {e}", exc_info=True)
        return None

def create_animation() -> Animation:
    """创建\"忙碌\"状态的L4占位符动画
    
    Returns:
        Animation: \"忙碌\"状态的L4占位符动画对象
    """
    frames: List[QImage] = []
    width, height = 64, 64
    total_animation_frames = 30 # L4动画帧数
    fps = 12 # L4动画FPS

    for i in range(total_animation_frames):
        frame_image = _create_busy_frame(width, height, i, total_animation_frames)
        if frame_image:
            frames.append(frame_image)
    
    if not frames:
        logger.warning("未能为BUSY状态创建任何L4帧，动画将为空。将使用单帧回退。")
        fallback_image = QImage(width, height, QImage.Format.Format_ARGB32)
        fallback_image.fill(QColor(0,0,0,0))
        p = QPainter(fallback_image)
        p.setPen(QColor(100,100,100))
        p.setBrush(QColor(200,200,200))
        p.drawEllipse(10,10,44,44)
        p.drawText(QRectF(0,0,width,height), Qt.AlignmentFlag.AlignCenter, "BUSY")
        p.end()
        frames.append(fallback_image)

    # 确保动画名称正确
    animation = Animation(name="busy", frames=frames, fps=fps)
    animation.metadata["placeholder"] = True
    animation.metadata["L4_quality"] = True
    animation.metadata["description"] = "忙碌 L4 占位符动画 - 激烈的键盘输入与专注表情"
    animation.set_loop(True)
    
    logger.debug(f"创建了忙碌L4状态的占位符动画，共 {len(frames)} 帧。")
    return animation