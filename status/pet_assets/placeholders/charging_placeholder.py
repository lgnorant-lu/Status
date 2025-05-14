"""
---------------------------------------------------------------
File name:                  charging_placeholder.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                "充电中"状态的占位符动画实现
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建;
----
"""
import logging
from PySide6.QtGui import QImage, QPainter, QColor, QBrush, QPen, QFont, QPainterPath
from PySide6.QtCore import Qt, QRectF

from status.animation.animation import Animation
from status.behavior.pet_state import PetState

logger = logging.getLogger(__name__)

def _create_charging_frame(width: int = 64, height: int = 64) -> QImage:
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(QColor(0,0,0,0)) # Transparent background
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Simple charging indicator (e.g., a green rectangle with a lightning bolt)
    painter.setBrush(QBrush(QColor(50, 200, 50, 180))) # Greenish
    painter.drawRect(QRectF(width * 0.25, height * 0.35, width * 0.5, height * 0.3))
    
    font = QFont("Arial", 10)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QPen(QColor(255,255,255))) # White text
    painter.drawText(QRectF(0,0,width,height), Qt.AlignmentFlag.AlignCenter, "CHARGING")
    
    # Simple lightning bolt symbol (could be improved)
    painter.setPen(QPen(QColor(255, 255, 0), 2)) # Yellow lightning
    path = QPainterPath()
    path.moveTo(width * 0.5, height * 0.25)
    path.lineTo(width * 0.4, height * 0.5)
    path.lineTo(width * 0.6, height * 0.5)
    path.lineTo(width * 0.5, height * 0.75)
    painter.drawPath(path)

    painter.end()
    return image

def create_animation() -> Animation:
    """创建\"充电中\"状态的基础占位符动画
    
    Returns:
        Animation: \"充电中\"状态的动画对象
    """
    frames = [_create_charging_frame()]
    animation = Animation(name=PetState.CHARGING.name.lower(), frames=frames, fps=1)
    animation.metadata["placeholder"] = True
    animation.metadata["L2_quality"] = True
    animation.metadata["description"] = "充电中 L2 占位符动画"
    animation.set_loop(True)
    logger.debug(f"创建了{PetState.CHARGING.name.upper()}状态的占位符动画，共 {len(frames)} 帧。")
    return animation 