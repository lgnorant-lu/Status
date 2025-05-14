"""
---------------------------------------------------------------
File name:                  moderate_load_placeholder.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                "中等负载"状态的占位符动画实现 (L2/L3 基础)
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建，作为修复运行时错误的占位;
----
"""
import logging
from PySide6.QtGui import QImage, QPainter, QColor, QBrush
from PySide6.QtCore import Qt, QRectF

from status.animation.animation import Animation
from status.behavior.pet_state import PetState

logger = logging.getLogger(__name__)

def _create_moderate_load_frame(width: int = 64, height: int = 64) -> QImage:
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(QColor(0,0,0,0)) # Transparent background
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Simple busy/moderate_load indicator (e.g., a thinking bubble or slightly faster breathing)
    painter.setBrush(QBrush(QColor(200, 200, 100, 180))) # Yellowish
    painter.drawEllipse(QRectF(width * 0.3, height * 0.3, width * 0.4, height * 0.4))
    
    painter.setPen(QColor(0,0,0))
    painter.drawText(QRectF(0,0,width,height), Qt.AlignmentFlag.AlignCenter, "MODERATE")

    painter.end()
    return image

def create_animation() -> Animation:
    """创建\"中等负载\"状态的基础占位符动画
    
    Returns:
        Animation: \"中等负载\"状态的动画对象
    """
    frames = [_create_moderate_load_frame()]
    animation = Animation(name=PetState.MODERATE_LOAD.name.lower(), frames=frames, fps=1)
    animation.metadata["placeholder"] = True
    animation.metadata["L2_quality"] = True # Mark as L2 for now
    animation.metadata["description"] = "中等负载 L2 占位符动画"
    animation.set_loop(True)
    logger.debug(f"创建了MODERATE_LOAD状态的占位符动画，共 {len(frames)} 帧。")
    return animation 