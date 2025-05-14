"""
---------------------------------------------------------------
File name:                  happy_placeholder.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                "开心"状态的占位符动画实现
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建;
----
"""
import logging
from PySide6.QtGui import QPixmap, QPainter, QColor, QBrush, QPen, QRadialGradient
from PySide6.QtCore import Qt, QPoint, QRect

from status.animation.animation import Animation

logger = logging.getLogger(__name__)

def create_animation() -> Animation:
    """创建"开心"状态的占位符动画
    
    Returns:
        Animation: "开心"状态的占位符动画对象
    """
    frames = []
    size = 64  # 动画帧大小
    fps = 8    # 帧率 - 每秒8帧，使动画流畅而不过快

    # 帧1: 基础笑脸
    pixmap1 = QPixmap(size, size)
    pixmap1.fill(Qt.GlobalColor.transparent)
    painter1 = QPainter(pixmap1)
    painter1.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # 创建头部渐变背景
    gradient1 = QRadialGradient(size/2, size/2, size/2)
    gradient1.setColorAt(0, QColor(255, 255, 150, 230))  # 中心亮黄色
    gradient1.setColorAt(0.8, QColor(255, 220, 100, 200))  # 边缘淡黄色
    painter1.setBrush(QBrush(gradient1))
    
    # 绘制头部
    painter1.drawEllipse(4, 4, size-8, size-8)
    
    # 眼睛
    painter1.setBrush(QBrush(QColor(40, 40, 40)))
    painter1.drawEllipse(size//3 - 4, size//3 - 2, 8, 8)  # 左眼
    painter1.drawEllipse(2*size//3 - 4, size//3 - 2, 8, 8)  # 右眼
    
    # 笑容
    pen = QPen(QColor(40, 40, 40), 2)
    painter1.setPen(pen)
    painter1.drawArc(size//4, size//2, size//2, size//3, 0, -180 * 16)  # 笑脸弧
    
    # 红晕
    painter1.setPen(Qt.PenStyle.NoPen)
    painter1.setBrush(QBrush(QColor(255, 150, 150, 100)))
    painter1.drawEllipse(size//5, size//2, size//5, size//6)  # 左脸红晕
    painter1.drawEllipse(3*size//5, size//2, size//5, size//6)  # 右脸红晕
    
    painter1.end()
    frames.append(pixmap1)

    # 帧2: 更开心的笑脸(眼睛更眯)
    pixmap2 = QPixmap(size, size)
    pixmap2.fill(Qt.GlobalColor.transparent)
    painter2 = QPainter(pixmap2)
    painter2.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # 创建头部渐变背景，稍亮一些
    gradient2 = QRadialGradient(size/2, size/2, size/2)
    gradient2.setColorAt(0, QColor(255, 255, 160, 230))  # 中心亮黄色
    gradient2.setColorAt(0.8, QColor(255, 225, 110, 200))  # 边缘淡黄色
    painter2.setBrush(QBrush(gradient2))
    
    # 绘制头部，稍微放大一点
    painter2.drawEllipse(3, 3, size-6, size-6)
    
    # 眼睛(微笑眼)
    pen = QPen(QColor(40, 40, 40), 2)
    painter2.setPen(pen)
    painter2.drawArc(size//3 - 5, size//3 - 2, 10, 6, 0, 180 * 16)  # 左眼(弯曲)
    painter2.drawArc(2*size//3 - 5, size//3 - 2, 10, 6, 0, 180 * 16)  # 右眼(弯曲)
    
    # 更大的笑容
    painter2.drawArc(size//5, size//2, 3*size//5, size//3, 0, -180 * 16)  # 更宽的笑脸弧
    
    # 更明显的红晕
    painter2.setPen(Qt.PenStyle.NoPen)
    painter2.setBrush(QBrush(QColor(255, 130, 130, 120)))
    painter2.drawEllipse(size//5 - 2, size//2, size//4, size//5)  # 左脸红晕
    painter2.drawEllipse(3*size//5 - 2, size//2, size//4, size//5)  # 右脸红晕
    
    painter2.end()
    frames.append(pixmap2)
    
    # 帧3: 微微波动效果
    pixmap3 = QPixmap(size, size)
    pixmap3.fill(Qt.GlobalColor.transparent)
    painter3 = QPainter(pixmap3)
    painter3.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # 创建头部渐变背景，再次变化
    gradient3 = QRadialGradient(size/2, size/2, size/2)
    gradient3.setColorAt(0, QColor(255, 255, 170, 230))  # 中心亮黄色
    gradient3.setColorAt(0.8, QColor(255, 235, 120, 200))  # 边缘淡黄色
    painter3.setBrush(QBrush(gradient3))
    
    # 绘制头部，形状稍有变化
    painter3.drawEllipse(4, 2, size-8, size-4)  # 微微向上扁平一点
    
    # 眼睛(介于帧1和帧2之间)
    painter3.setBrush(QBrush(QColor(40, 40, 40)))
    painter3.drawEllipse(size//3 - 4, size//3 - 3, 7, 7)  # 左眼
    painter3.drawEllipse(2*size//3 - 3, size//3 - 3, 7, 7)  # 右眼
    
    # 笑容
    pen = QPen(QColor(40, 40, 40), 2)
    painter3.setPen(pen)
    painter3.drawArc(size//4 + 2, size//2 - 1, size//2, size//3 + 2, 0, -180 * 16)  # 笑脸弧
    
    # 红晕
    painter3.setPen(Qt.PenStyle.NoPen)
    painter3.setBrush(QBrush(QColor(255, 140, 140, 110)))
    painter3.drawEllipse(size//5, size//2 - 1, size//5, size//6)  # 左脸红晕
    painter3.drawEllipse(3*size//5, size//2 - 1, size//5, size//6)  # 右脸红晕
    
    painter3.end()
    frames.append(pixmap3)
        
    # 创建并返回Animation对象
    animation = Animation(name="happy", frames=frames, fps=fps)
    animation.metadata["placeholder"] = True
    animation.metadata["description"] = "开心状态占位符动画"
    
    logger.debug("创建了开心状态的占位符动画")
    return animation 