"""
---------------------------------------------------------------
File name:                  busy_placeholder.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                "忙碌"状态的占位符动画实现
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建;
----
"""
import logging
from typing import Optional
from PySide6.QtGui import QImage, QPainter, QColor, QBrush, QPen
from PySide6.QtCore import Qt, QPoint

from status.animation.animation import Animation
from status.behavior.pet_state import PetState

logger = logging.getLogger(__name__)

def _create_busy_image(width=64, height=64) -> Optional[QImage]:
    """创建一个代表'忙碌'状态的占位符图像
    
    Args:
        width: 图像宽度
        height: 图像高度
        
    Returns:
        QImage: 创建的图像，如果失败则为None
    """
    try:
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(QColor(0, 0, 0, 0))  # 透明背景
        
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.setPen(QPen(QColor(70, 70, 70), 2))
        painter.setBrush(QBrush(QColor(200, 200, 200, 220)))
        painter.drawEllipse(10, 10, 44, 44) # Head
        painter.setBrush(QBrush(QColor(180, 180, 180, 220)))
        painter.drawPolygon([QPoint(15, 15), QPoint(25, 5), QPoint(30, 15)]) # Left Ear
        painter.drawPolygon([QPoint(49, 15), QPoint(39, 5), QPoint(34, 15)]) # Right Ear
        
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        painter.setBrush(QBrush(QColor(30, 30, 30)))
        painter.drawEllipse(20, 28, 8, 4) # y=28, height=4, Left Eye (narrower)
        painter.drawEllipse(36, 28, 8, 4) # y=28, height=4, Right Eye (narrower)
        
        painter.setBrush(QBrush(QColor(255, 150, 150)))
        painter.drawEllipse(29, 35, 6, 4) # Nose

        painter.setPen(QPen(QColor(70, 70, 70), 1))
        painter.drawLine(32, 39, 32, 42)
        painter.drawLine(32, 42, 28, 45)
        painter.drawLine(32, 42, 36, 45) # Mouth
        
        painter.end()
        return image
    except Exception as e:
        logger.error(f"创建busy图像时出错: {str(e)}")
        return None

def create_animation() -> Animation:
    """创建\"忙碌\"状态的占位符动画
    
    Returns:
        Animation: \"忙碌\"状态的占位符动画对象
    """
    frames = []
    busy_image = _create_busy_image()
    if busy_image:
        frames.append(busy_image)
    
    animation = Animation(name=PetState.BUSY.name.lower(), frames=frames, fps=1)
    animation.metadata["placeholder"] = True
    animation.metadata["description"] = "忙碌状态占位符动画"
    animation.set_loop(True)
    
    if not frames:
        logger.warning("未能为BUSY状态创建任何帧，动画将为空。")

    logger.debug("创建了忙碌状态的占位符动画")
    return animation 