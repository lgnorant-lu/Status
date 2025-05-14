"""
---------------------------------------------------------------
File name:                  low_battery_placeholder.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                "低电量"状态的占位符动画实现
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

def _create_low_battery_frame(width: int = 64, height: int = 64) -> QImage:
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(QColor(0,0,0,0)) # Transparent background
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Simple low_battery indicator (e.g., a red rectangle)
    painter.setBrush(QBrush(QColor(220, 50, 50, 180))) # Reddish
    painter.drawRect(QRectF(width * 0.25, height * 0.35, width * 0.5, height * 0.3))
    
    font = QFont("Arial", 10)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QPen(QColor(255,255,255))) # White text
    painter.drawText(QRectF(0,0,width,height), Qt.AlignmentFlag.AlignCenter, "LOW_BATT")

    painter.end()
    return image

def create_animation() -> Animation:
    """创建\"低电量\"状态的基础占位符动画
    
    Returns:
        Animation: \"低电量\"状态的动画对象
    """
    frames = [_create_low_battery_frame()]
    # 使用 PetState.LOW_BATTERY.name.lower() 来确保动画名称与工厂期望的一致
    animation = Animation(name=PetState.LOW_BATTERY.name.lower(), frames=frames, fps=1)
    animation.metadata["placeholder"] = True
    animation.metadata["L2_quality"] = True 
    animation.metadata["description"] = "低电量 L2 占位符动画"
    animation.set_loop(True)
    logger.debug(f"创建了{PetState.LOW_BATTERY.name.upper()}状态的占位符动画，共 {len(frames)} 帧。")
    return animation 