"""
---------------------------------------------------------------
File name:                  fully_charged_placeholder.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                "已充满"状态的占位符动画实现
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建;
----
"""
import logging
from PySide6.QtGui import QImage, QPainter, QColor, QBrush, QPen, QFont
from PySide6.QtCore import Qt, QRectF

from status.animation.animation import Animation
from status.behavior.pet_state import PetState

logger = logging.getLogger(__name__)

def _create_fully_charged_frame(width: int = 64, height: int = 64) -> QImage:
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(QColor(0,0,0,0)) # Transparent background
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Simple fully_charged indicator (e.g., a bright green rectangle)
    painter.setBrush(QBrush(QColor(50, 220, 50, 220))) # Bright Green
    painter.drawRect(QRectF(width * 0.25, height * 0.35, width * 0.5, height * 0.3))
    
    font = QFont("Arial", 10)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QPen(QColor(0,0,0))) # Black text for contrast on bright green
    painter.drawText(QRectF(0,0,width,height), Qt.AlignmentFlag.AlignCenter, "FULL_CHG")

    painter.end()
    return image

def create_animation() -> Animation:
    """创建\"已充满\"状态的基础占位符动画
    
    Returns:
        Animation: \"已充满\"状态的动画对象
    """
    frames = [_create_fully_charged_frame()]
    animation = Animation(name=PetState.FULLY_CHARGED.name.lower(), frames=frames, fps=1)
    animation.metadata["placeholder"] = True
    animation.metadata["L2_quality"] = True
    animation.metadata["description"] = "已充满 L2 占位符动画"
    animation.set_loop(True)
    logger.debug(f"创建了{PetState.FULLY_CHARGED.name.upper()}状态的占位符动画，共 {len(frames)} 帧。")
    return animation 