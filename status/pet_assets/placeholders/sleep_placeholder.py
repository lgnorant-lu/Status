"""
---------------------------------------------------------------
File name:                  sleep_placeholder.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                "睡眠"状态的占位符动画实现 (区别于NIGHT)
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

def _create_sleep_frame(width: int = 64, height: int = 64) -> QImage:
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(QColor(0,0,0,0)) # Transparent background
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Simple sleep indicator (e.g., a dark purple rectangle with Zzz)
    painter.setBrush(QBrush(QColor(100, 50, 150, 180))) # Dark bluish-purple
    painter.drawRect(QRectF(width * 0.2, height * 0.3, width * 0.6, height * 0.4))
    
    font = QFont("Comic Sans MS", 12) # Using a more playful font for Zzz
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QPen(QColor(200,200,255))) # Light purple/blue text
    painter.drawText(QRectF(0,0,width,height), Qt.AlignmentFlag.AlignCenter, "Zzz...")

    painter.end()
    return image

def create_animation() -> Animation:
    """创建\"睡眠\"状态的基础占位符动画
    
    Returns:
        Animation: \"睡眠\"状态的动画对象
    """
    frames = [_create_sleep_frame()]
    animation = Animation(name=PetState.SLEEP.name.lower(), frames=frames, fps=1)
    animation.metadata["placeholder"] = True
    animation.metadata["L2_quality"] = True
    animation.metadata["description"] = "睡眠 L2 占位符动画 (区别于NIGHT)"
    animation.set_loop(True)
    logger.debug(f"创建了{PetState.SLEEP.name.upper()}状态的占位符动画，共 {len(frames)} 帧。")
    return animation 