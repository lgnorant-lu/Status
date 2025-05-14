"""
---------------------------------------------------------------
File name:                  petted_placeholder.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                "被抚摸"状态的占位符动画实现
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建;
----
"""
import logging
from typing import Optional
from PySide6.QtGui import QImage, QPainter, QColor, QBrush, QPen, QFont, QPainterPath
from PySide6.QtCore import Qt, QRect

from status.animation.animation import Animation
from status.behavior.pet_state import PetState

logger = logging.getLogger(__name__)

def _create_petted_image(width=64, height=64) -> Optional[QImage]:
    """创建一个代表'被抚摸'状态的占位符图像"""
    try:
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(QColor(0,0,0,0)) # Transparent
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor(255, 100, 200, 200))) # Pinkish
        # Draw a heart shape (simplified)
        path = QPainterPath()
        path.moveTo(width / 2, height / 4)
        path.cubicTo(width / 10, height / 5, width / 3, height * 3 / 4, width / 2, height * 3 / 4)
        path.cubicTo(width * 2 / 3, height * 3 / 4, width * 9 / 10, height / 5, width / 2, height / 4)
        painter.drawPath(path)
        painter.setPen(QPen(Qt.GlobalColor.black))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(QRect(0,0,width,height), Qt.AlignmentFlag.AlignCenter, "Petted!")
        painter.end()
        return image
    except Exception as e:
        logger.error(f"创建petted图像时出错: {str(e)}")
        return None

def create_animation() -> Animation:
    """创建\"被抚摸\"状态的占位符动画
    
    Returns:
        Animation: \"被抚摸\"状态的占位符动画对象
    """
    frames = []
    img = _create_petted_image()
    if img:
        frames.append(img)
    
    animation = Animation(name=PetState.PETTED.name.lower(), frames=frames, fps=2) # Original fps was 2
    animation.metadata["placeholder"] = True
    animation.metadata["description"] = "被抚摸状态占位符动画"
    animation.set_loop(False) # Interaction animations are usually not looping

    if not frames:
        logger.warning("未能为PETTED状态创建任何帧，动画将为空。")

    logger.debug("创建了被抚摸状态的占位符动画")
    return animation 