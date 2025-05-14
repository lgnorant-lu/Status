"""
---------------------------------------------------------------
File name:                  morning_placeholder.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                "早晨"状态的占位符动画实现
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建;
----
"""
import logging
import math
from typing import Optional
from PySide6.QtGui import QImage, QPainter, QColor, QBrush, QPen
from PySide6.QtCore import Qt, QPoint, QRect

from status.animation.animation import Animation
from status.behavior.pet_state import PetState

logger = logging.getLogger(__name__)

def _create_morning_image(width=64, height=64) -> Optional[QImage]:
    """创建一个代表'早晨'状态的占位符图像"""
    try:
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(QColor(0, 0, 0, 0))  # 透明背景
        
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.setPen(QPen(QColor(70, 70, 70), 2))
        painter.setBrush(QBrush(QColor(255, 230, 180, 220)))
        painter.drawEllipse(10, 10, 44, 44) # Head
        
        painter.setBrush(QBrush(QColor(255, 210, 160, 220)))
        painter.drawPolygon([QPoint(15, 15), QPoint(25, 5), QPoint(30, 15)]) # Left Ear
        painter.drawPolygon([QPoint(49, 15), QPoint(39, 5), QPoint(34, 15)]) # Right Ear
        
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        painter.setBrush(QBrush(QColor(30, 30, 30)))
        painter.drawEllipse(20, 25, 8, 8)  # Left Eye
        painter.drawEllipse(36, 25, 8, 8)  # Right Eye
        
        painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
        painter.setPen(QPen(QColor(255, 255, 255, 0)))
        painter.drawEllipse(22, 27, 3, 3)  # Left Eye Highlight
        painter.drawEllipse(38, 27, 3, 3)  # Right Eye Highlight
        
        painter.setPen(QPen(QColor(70, 70, 70), 1))
        painter.setBrush(QBrush(QColor(255, 150, 150)))
        painter.drawEllipse(29, 35, 6, 4) # Nose
        
        painter.setPen(QPen(QColor(70, 70, 70), 1))
        painter.drawArc(QRect(25, 38, 14, 10), 0, -180 * 16)  # Smiling mouth
        
        painter.setPen(QPen(QColor(255, 200, 0, 100), 1))
        for i in range(8):
            angle = i * 45
            rad = angle * math.pi / 180 # Corrected math.pi
            x1 = width / 2 + (width / 2 - 5) * math.cos(rad)
            y1 = height / 2 + (height / 2 - 5) * math.sin(rad)
            x2 = width / 2 + (width / 2 + 5) * math.cos(rad)
            y2 = height / 2 + (height / 2 + 5) * math.sin(rad)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            
        painter.end()
        return image
    except Exception as e:
        logger.error(f"创建morning图像时出错: {str(e)}")
        return None

def create_animation() -> Animation:
    """创建\"早晨\"状态的占位符动画
    
    Returns:
        Animation: \"早晨\"状态的占位符动画对象
    """
    frames = []
    img = _create_morning_image()
    if img:
        frames.append(img)
    
    animation = Animation(name=PetState.MORNING.name.lower(), frames=frames, fps=1) # Original fps was 1
    animation.metadata["placeholder"] = True
    animation.metadata["description"] = "早晨状态占位符动画"
    animation.set_loop(True)

    if not frames:
        logger.warning("未能为MORNING状态创建任何帧，动画将为空。")

    logger.debug("创建了早晨状态的占位符动画")
    return animation 