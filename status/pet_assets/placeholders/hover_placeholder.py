"""
---------------------------------------------------------------
File name:                  hover_placeholder.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                "鼠标悬停"状态的占位符动画实现
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建;
----
"""
import logging
from typing import Optional
from PySide6.QtGui import QImage, QPainter, QColor, QBrush, QPen, QFont, QRadialGradient
from PySide6.QtCore import Qt, QRect, QPoint

from status.animation.animation import Animation
from status.behavior.pet_state import PetState

logger = logging.getLogger(__name__)

def _create_hover_image(width=64, height=64) -> Optional[QImage]:
    """创建一个代表'鼠标悬停'状态的占位符图像"""
    try:
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(QColor(0,0,0,0)) # Transparent
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        gradient = QRadialGradient(width / 2, height / 2, width / 2)
        gradient.setColorAt(0, QColor(255, 255, 200, 180))
        gradient.setColorAt(0.7, QColor(255, 255, 150, 100))
        gradient.setColorAt(1, QColor(255, 255, 100, 0))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, width - 4, height - 4)
        
        painter.setPen(QPen(QColor(80, 80, 80, 200)))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(QRect(0, 0, width, height), Qt.AlignmentFlag.AlignCenter, "Hover!")
        
        painter.setPen(QPen(QColor(255, 255, 0, 200), 1))
        star_points = [
            QPoint(width // 4, height // 4),
            QPoint(3 * width // 4, height // 4),
            QPoint(width // 2, 3 * height // 4),
            QPoint(width // 5, 2 * height // 3),
            QPoint(4 * width // 5, 2 * height // 3)
        ]
        for point in star_points:
            painter.drawLine(point.x() - 3, point.y(), point.x() + 3, point.y())
            painter.drawLine(point.x(), point.y() - 3, point.x(), point.y() + 3)
            
        painter.end()
        return image
    except Exception as e:
        logger.error(f"创建hover图像时出错: {str(e)}")
        return None

def create_animation() -> Animation:
    """创建\"鼠标悬停\"状态的占位符动画
    
    Returns:
        Animation: \"鼠标悬停\"状态的占位符动画对象
    """
    frames = []
    img = _create_hover_image()
    if img:
        frames.append(img)
    
    animation = Animation(name=PetState.HOVER.name.lower(), frames=frames, fps=2) # Original fps was 2
    animation.metadata["placeholder"] = True
    animation.metadata["description"] = "鼠标悬停状态占位符动画"
    animation.set_loop(False) # Interaction animations are usually not looping

    if not frames:
        logger.warning("未能为HOVER状态创建任何帧，动画将为空。")

    logger.debug("创建了鼠标悬停状态的占位符动画")
    return animation 