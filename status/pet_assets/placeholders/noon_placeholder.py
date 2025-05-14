"""
---------------------------------------------------------------
File name:                  noon_placeholder.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                "中午"状态的占位符动画实现
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

def _create_noon_image(width=64, height=64) -> Optional[QImage]:
    """创建一个代表'中午'状态的占位符图像"""
    try:
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        sun_color = QColor(255, 220, 0)  # Bright yellow for noon sun
        painter.setBrush(QBrush(sun_color))
        painter.setPen(Qt.PenStyle.NoPen)
        sun_x, sun_y = 32, 10  # Top center
        painter.drawEllipse(sun_x, sun_y, 12, 12)
        
        painter.setBrush(QBrush(QColor(200, 200, 200)))
        painter.setPen(QPen(QColor(70, 70, 70), 1))
        painter.drawEllipse(20, 25, 24, 20) # Body
        painter.drawEllipse(32, 18, 16, 16) # Head
        painter.drawEllipse(34, 10, 8, 8) # Ear 1
        painter.drawEllipse(42, 12, 8, 8) # Ear 2
        
        painter.setBrush(QBrush(QColor(70, 70, 70)))
        painter.drawEllipse(35, 21, 3, 1) # Eye 1 (squinting)
        painter.drawEllipse(42, 22, 3, 1) # Eye 2 (squinting)
        
        painter.setBrush(QBrush(QColor(255, 150, 150)))
        painter.drawEllipse(38, 26, 4, 2) # Mouth (tongue out)
        
        painter.setPen(QPen(QColor(255, 200, 100, 150), 1, Qt.PenStyle.DashLine))
        painter.drawLine(28, 18, 26, 10) # Heat wave 1
        painter.drawLine(46, 20, 48, 12) # Heat wave 2
            
        painter.end()
        return image
    except Exception as e:
        logger.error(f"创建noon图像时出错: {str(e)}")
        return None

def create_animation() -> Animation:
    """创建\"中午\"状态的占位符动画
    
    Returns:
        Animation: \"中午\"状态的占位符动画对象
    """
    frames = []
    img = _create_noon_image()
    if img:
        frames.append(img)
    
    animation = Animation(name=PetState.NOON.name.lower(), frames=frames, fps=1) # Original fps was 1
    animation.metadata["placeholder"] = True
    animation.metadata["description"] = "中午状态占位符动画"
    animation.set_loop(True)

    if not frames:
        logger.warning("未能为NOON状态创建任何帧，动画将为空。")

    logger.debug("创建了中午状态的占位符动画")
    return animation 