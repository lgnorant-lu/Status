"""
---------------------------------------------------------------
File name:                  error_placeholder.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                "错误"状态的占位符动画实现
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建;
----
"""
import logging
from typing import Optional
from PySide6.QtGui import QImage, QPainter, QColor, QBrush, QPen, QFont
from PySide6.QtCore import Qt, QRect

from status.animation.animation import Animation
from status.behavior.pet_state import PetState # Assuming SYSTEM_ERROR is a PetState

logger = logging.getLogger(__name__)

def _create_error_image(width=64, height=64) -> Optional[QImage]:
    """创建一个代表'错误'状态的占位符图像"""
    try:
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(QColor(0,0,0,0)) # Transparent
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.setBrush(QBrush(QColor(139, 0, 0, 200))) # Dark Red
        painter.drawRect(0, 0, width, height)
        
        painter.setPen(QPen(QColor(255, 255, 255))) # White text
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        text_rect = QRect(0, 0, width, height)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "ERROR")
        
        painter.end()
        return image
    except Exception as e:
        logger.error(f"创建error图像时出错: {str(e)}")
        return None

def create_animation() -> Animation:
    """创建\"错误\"状态的占位符动画
    
    Returns:
        Animation: \"错误\"状态的占位符动画对象
    """
    frames = []
    img = _create_error_image()
    if img:
        frames.append(img)
    
    # Assuming SYSTEM_ERROR is the correct PetState enum for this
    animation = Animation(name=PetState.SYSTEM_ERROR.name.lower(), frames=frames, fps=1)
    animation.metadata["placeholder"] = True
    animation.metadata["description"] = "错误状态占位符动画"
    animation.set_loop(False) # Error animation probably shouldn't loop

    if not frames:
        logger.warning("未能为ERROR状态创建任何帧，动画将为空。")

    logger.debug("创建了错误状态的占位符动画")
    return animation 