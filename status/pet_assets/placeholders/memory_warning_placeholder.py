"""
---------------------------------------------------------------
File name:                  memory_warning_placeholder.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                "内存警告"状态的占位符动画实现
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

def _create_memory_warning_image(width=64, height=64) -> Optional[QImage]:
    """创建一个代表'内存警告'状态的占位符图像"""
    try:
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(QColor(0, 0, 0, 0))  # 透明背景
        
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.setPen(QPen(QColor(150, 50, 0), 2)) # 深橙色边框
        painter.setBrush(QBrush(QColor(255, 100, 0, 220))) # 橙红色填充
        painter.drawEllipse(10, 10, 44, 44) # Head
        
        painter.setBrush(QBrush(QColor(220, 80, 0, 220))) # Ears color adjusted
        painter.drawPolygon([QPoint(15, 15), QPoint(25, 5), QPoint(30, 15)]) # Left Ear
        painter.drawPolygon([QPoint(49, 15), QPoint(39, 5), QPoint(34, 15)]) # Right Ear
        
        painter.setPen(QPen(QColor(50, 0, 0), 1))
        painter.setBrush(QBrush(QColor(50, 0, 0)))
        painter.drawEllipse(18, 23, 12, 12) # Left Eye (wide)
        painter.drawEllipse(34, 23, 12, 12) # Right Eye (wide)
        painter.setBrush(QBrush(QColor(255, 200, 200)))
        painter.drawEllipse(21, 26, 6, 6) # Highlight in left eye
        painter.drawEllipse(37, 26, 6, 6) # Highlight in right eye
        
        painter.setBrush(QBrush(QColor(255, 150, 150)))
        painter.drawEllipse(29, 35, 6, 4) # Nose

        painter.setPen(QPen(QColor(70, 70, 70), 1))
        painter.setBrush(QBrush(QColor(70,70,70)))
        painter.drawEllipse(28, 40, 8, 8) # Mouth (open, surprised/warning)
        
        painter.end()
        return image
    except Exception as e:
        logger.error(f"创建memory_warning图像时出错: {str(e)}")
        return None

def create_animation() -> Animation:
    """创建\"内存警告\"状态的占位符动画
    
    Returns:
        Animation: \"内存警告\"状态的占位符动画对象
    """
    frames = []
    img = _create_memory_warning_image()
    if img:
        frames.append(img)
    
    animation = Animation(name=PetState.MEMORY_WARNING.name.lower(), frames=frames, fps=1)
    animation.metadata["placeholder"] = True
    animation.metadata["description"] = "内存警告状态占位符动画"
    animation.set_loop(True)

    if not frames:
        logger.warning("未能为MEMORY_WARNING状态创建任何帧，动画将为空。")

    logger.debug("创建了内存警告状态的占位符动画")
    return animation 