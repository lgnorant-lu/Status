"""
---------------------------------------------------------------
File name:                  evening_placeholder.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                "傍晚"状态的占位符动画实现
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

def _create_evening_image(width=64, height=64) -> Optional[QImage]:
    """创建一个代表'傍晚'状态的占位符图像"""
    try:
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg_color = QColor(40, 50, 100, 50)  # Pale blue translucent background for evening
        moon_color = QColor(255, 200, 100)  # Orange-yellow moon/sun for evening
        
        painter.fillRect(0, 0, width, height, bg_color)
        painter.setBrush(QBrush(moon_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(8, 20, 12, 12) # Setting sun in bottom-left
        
        painter.setBrush(QBrush(QColor(150, 120, 200, 100))) # Clouds
        painter.drawEllipse(30, 15, 10, 6)
        painter.drawEllipse(25, 12, 12, 8)

        gray_level = 180
        painter.setBrush(QBrush(QColor(gray_level, gray_level, gray_level)))
        painter.setPen(QPen(QColor(70, 70, 70), 1))
        painter.drawEllipse(20, 25, 24, 20) # Body
        painter.drawEllipse(32, 18, 16, 16) # Head
        painter.drawEllipse(34, 10, 8, 8) # Ear 1
        painter.drawEllipse(42, 12, 8, 8) # Ear 2
        
        painter.setBrush(QBrush(QColor(70, 70, 70)))
        painter.drawEllipse(35, 21, 3, 2) # Eye 1 (half-open)
        painter.drawEllipse(42, 22, 3, 2) # Eye 2 (half-open)
        
        painter.setBrush(QBrush(QColor(255, 150, 150)))
        painter.drawEllipse(29, 35, 6, 4) # Nose
        
        painter.setPen(QPen(QColor(70, 70, 70), 1))
        painter.drawLine(28, 42, 36, 42)  # Simple mouth line
        
        painter.setPen(QPen(QColor(200, 200, 255, 200), 1))
        painter.drawText(QPoint(48, 15), "z") # Sleepy zzz
            
        painter.end()
        return image
    except Exception as e:
        logger.error(f"创建evening图像时出错: {str(e)}")
        return None

def create_animation() -> Animation:
    """创建\"傍晚\"状态的占位符动画
    
    Returns:
        Animation: \"傍晚\"状态的占位符动画对象
    """
    frames = []
    img = _create_evening_image()
    if img:
        frames.append(img)
    
    animation = Animation(name=PetState.EVENING.name.lower(), frames=frames, fps=1) # Original fps was 1
    animation.metadata["placeholder"] = True
    animation.metadata["description"] = "傍晚状态占位符动画"
    animation.set_loop(True)

    if not frames:
        logger.warning("未能为EVENING状态创建任何帧，动画将为空。")

    logger.debug("创建了傍晚状态的占位符动画")
    return animation 