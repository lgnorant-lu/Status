"""
---------------------------------------------------------------
File name:                  idle_placeholder.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                "空闲"状态的占位符动画实现
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

def _create_idle_image(width=64, height=64) -> Optional[QImage]:
    """创建一个占位符图像
    
    Args:
        width: 图像宽度
        height: 图像高度
        
    Returns:
        QImage: 创建的图像，如果失败则为None
    """
    try:
        # 创建一个QImage
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(QColor(0, 0, 0, 0))  # 透明背景
        
        # 添加绘制代码，使图像可见
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制猫咪轮廓
        painter.setPen(QPen(QColor(70, 70, 70), 2))
        painter.setBrush(QBrush(QColor(200, 200, 200, 220)))
        
        # 绘制头部（圆形）
        painter.drawEllipse(10, 10, 44, 44)
        
        # 绘制耳朵
        painter.setBrush(QBrush(QColor(180, 180, 180, 220)))
        # 左耳
        painter.drawPolygon([
            QPoint(15, 15),
            QPoint(25, 5),
            QPoint(30, 15)
        ])
        # 右耳
        painter.drawPolygon([
            QPoint(49, 15),
            QPoint(39, 5),
            QPoint(34, 15)
        ])
        
        # 绘制眼睛
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        painter.setBrush(QBrush(QColor(30, 30, 30)))
        # 左眼
        painter.drawEllipse(20, 25, 8, 8)
        # 右眼
        painter.drawEllipse(36, 25, 8, 8)
        
        # 绘制鼻子
        painter.setBrush(QBrush(QColor(255, 150, 150)))
        painter.drawEllipse(29, 35, 6, 4)

        # 绘制嘴
        painter.setPen(QPen(QColor(70, 70, 70), 1))
        painter.drawLine(32, 39, 32, 42)
        painter.drawLine(32, 42, 28, 45)
        painter.drawLine(32, 42, 36, 45)
        
        painter.end()
        
        return image
    except Exception as e:
        logger.error(f"创建idle图像时出错: {str(e)}")
        return None

def create_animation() -> Animation:
    """创建\"空闲\"状态的占位符动画
    
    Returns:
        Animation: \"空闲\"状态的占位符动画对象
    """
    frames = []
    idle_image = _create_idle_image()
    if idle_image:
        frames.append(idle_image)
    
    # 创建并返回Animation对象
    # 对于单帧动画，fps设为1即可
    animation = Animation(name=PetState.IDLE.name.lower(), frames=frames, fps=1)
    animation.metadata["placeholder"] = True
    animation.metadata["description"] = "空闲状态占位符动画"
    animation.set_loop(True) # 通常idle动画是循环的
    
    if not frames:
        logger.warning("未能为IDLE状态创建任何帧，动画将为空。")
        # 返回一个空的动画或包含默认空白帧的动画
        # return Animation(name=PetState.IDLE.name.lower(), frames=[QImage(64,64,QImage.Format.Format_ARGB32_Premultiplied)], fps=1)


    logger.debug("创建了空闲状态的占位符动画")
    return animation 