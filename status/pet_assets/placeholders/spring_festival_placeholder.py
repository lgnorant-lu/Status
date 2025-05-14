"""
---------------------------------------------------------------
File name:                  spring_festival_placeholder.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                "春节"状态的L4占位符动画实现
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建，实现L4动画;
----
"""
import logging
from typing import List, Optional
from PySide6.QtGui import QImage, QPainter, QColor, QBrush, QPen, QPolygon, QPainterPath, QRadialGradient
from PySide6.QtCore import Qt, QPoint, QRectF

from status.animation.animation import Animation

logger = logging.getLogger(__name__)

def _create_lantern(painter: QPainter, x: int, y: int, size: int, color: QColor, tassel_color: QColor):
    """绘制一个灯笼"""
    # 灯笼主体
    painter.setBrush(QBrush(color))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(x, y, size, int(size * 1.2))

    # 上下盖
    cap_height = int(size * 0.2)
    painter.setBrush(QBrush(color.darker(120)))
    painter.drawRect(x, y - cap_height // 2, size, cap_height)
    painter.drawRect(x, y + int(size * 1.2) - cap_height // 2, size, cap_height)
    
    # 穗子
    painter.setPen(QPen(tassel_color, 2))
    tassel_y_start = y + int(size * 1.2) + cap_height // 2
    for i in range(3):
        painter.drawLine(x + size // 2 - (i-1)*5, tassel_y_start, x + size // 2 - (i-1)*5, tassel_y_start + int(size*0.3))

def _create_firework_particle(painter: QPainter, cx: int, cy: int, radius: int, angle_deg: float, color: QColor, length: int):
    """绘制烟花的一个粒子轨迹"""
    import math
    angle_rad = math.radians(angle_deg)
    end_x = cx + int((radius + length) * math.cos(angle_rad))
    end_y = cy + int((radius + length) * math.sin(angle_rad))
    start_x = cx + int(radius * math.cos(angle_rad))
    start_y = cy + int(radius * math.sin(angle_rad))
    
    painter.setPen(QPen(color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawLine(start_x, start_y, end_x, end_y)

def _create_spring_festival_frame(width: int, height: int, frame_number: int, total_frames: int) -> Optional[QImage]:
    """为春节动画创建特定帧的图像 - L4质量"""
    try:
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(QColor(30, 0, 0, 200))  # 深红色背景，略透明

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # --- 绘制灯笼 ---
        lantern_size = width // 5
        _create_lantern(painter, width // 6, height // 4, lantern_size, QColor(255, 50, 50, 230), QColor(255,223,0, 220))
        _create_lantern(painter, width - width // 6 - lantern_size, height // 3, int(lantern_size*0.8), QColor(255, 80, 20, 230), QColor(255,223,0, 220))

        # --- 绘制动态烟花 ---
        # 烟花参数
        num_particles = 12
        max_firework_radius = width / 3
        firework_center_x = width // 2
        firework_center_y = height // 3
        
        # 模拟烟花爆炸的不同阶段
        # 阶段1: 扩展 (0 -> total_frames/2)
        # 阶段2: 消散 (total_frames/2 -> total_frames)
        
        progress = frame_number / total_frames
        current_radius_factor = 0
        current_length_factor = 0
        alpha_factor = 255

        if progress < 0.5: # 扩展阶段
            current_radius_factor = (progress / 0.5) # 0 to 1
            current_length_factor = current_radius_factor * 0.3 # 粒子长度也随之变化
            alpha_factor = 255 * (1 - (progress / 0.5) * 0.3) # 亮度逐渐减弱
        else: # 消散阶段
            current_radius_factor = 1.0 # 保持最大半径
            current_length_factor = 0.3 * (1 - (progress - 0.5) / 0.5) # 粒子长度逐渐缩短至消失
            alpha_factor = 255 * (1 - (progress - 0.5) / 0.5) # 透明度逐渐降低至消失

        current_radius = int(max_firework_radius * current_radius_factor)
        current_length = int(max_firework_radius * current_length_factor * 0.5) # 粒子相对半径的长度

        firework_colors = [
            QColor(255, 100, 100, int(alpha_factor)),  # 红色系
            QColor(255, 255, 100, int(alpha_factor)),  # 黄色系
            QColor(255, 180, 80, int(alpha_factor))   # 橙色系
        ]

        if current_length > 1 and alpha_factor > 10: # 只有在粒子可见时绘制
            for i in range(num_particles):
                angle = (360 / num_particles) * i + (progress * 30) # 烟花粒子旋转效果
                color = firework_colors[i % len(firework_colors)]
                _create_firework_particle(painter, firework_center_x, firework_center_y, current_radius, angle, color, current_length)

        # --- 桌宠主体占位符 (一个简化的快乐猫咪) ---
        pet_x = width // 2 - 24
        pet_y = height - 64 - 10 # 底部
        
        painter.setPen(QPen(QColor(230, 230, 200), 2)) # 浅米色
        painter.setBrush(QBrush(QColor(255, 250, 220, 220))) # 更亮的米色
        
        # 身体
        painter.drawEllipse(pet_x, pet_y + 10, 48, 48) 
        # 头
        painter.drawEllipse(pet_x + 4, pet_y, 40, 40)
        
        # 耳朵 (略微动态)
        ear_offset_y = int(3 * (progress if progress < 0.5 else 1-progress) * 2) # 随烟花节奏轻微摆动
        painter.drawPolygon([QPoint(pet_x + 8, pet_y + 10 - ear_offset_y), QPoint(pet_x + 18, pet_y - 5 - ear_offset_y), QPoint(pet_x + 22, pet_y + 10 - ear_offset_y)]) # 左耳
        painter.drawPolygon([QPoint(pet_x + 40, pet_y + 10 - ear_offset_y), QPoint(pet_x + 30, pet_y - 5 - ear_offset_y), QPoint(pet_x + 26, pet_y + 10 - ear_offset_y)]) # 右耳

        # 眼睛 (开心眯眼)
        eye_y = pet_y + 18
        painter.setPen(QPen(QColor(50, 50, 50), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        # 左眼
        left_eye_path = QPainterPath()
        left_eye_path.moveTo(pet_x + 12, eye_y)
        left_eye_path.quadTo(pet_x + 17, eye_y + 5, pet_x + 22, eye_y)
        painter.drawPath(left_eye_path)
        # 右眼
        right_eye_path = QPainterPath()
        right_eye_path.moveTo(pet_x + 26, eye_y)
        right_eye_path.quadTo(pet_x + 31, eye_y + 5, pet_x + 36, eye_y)
        painter.drawPath(right_eye_path)
        
        # 嘴巴 (微笑)
        mouth_path = QPainterPath()
        mouth_path.moveTo(pet_x + 18, pet_y + 28)
        mouth_path.quadTo(pet_x + 24, pet_y + 33, pet_x + 30, pet_y + 28)
        painter.drawPath(mouth_path)

        painter.end()
        return image
    except Exception as e:
        logger.error(f"创建春节L4帧 {frame_number} 时出错: {e}", exc_info=True)
        return None

def create_animation() -> Animation:
    """创建"春节"状态的L4占位符动画
    
    Returns:
        Animation: "春节"状态的L4占位符动画对象
    """
    frames: List[QImage] = []
    width, height = 64, 64  # 标准尺寸
    total_animation_frames = 20 # L4动画帧数增加

    for i in range(total_animation_frames):
        frame_image = _create_spring_festival_frame(width, height, i, total_animation_frames)
        if frame_image:
            frames.append(frame_image)
    
    # 如果没有成功创建任何帧，可以考虑添加一个默认的静态帧或记录更严重的警告
    if not frames:
        logger.warning("未能为 SPRING_FESTIVAL 状态创建任何L4帧，动画将为空。可以考虑添加一个静态回退图像。")
        # 作为回退，可以创建一个非常简单的静态图像
        fallback_image = QImage(width, height, QImage.Format.Format_ARGB32)
        fallback_image.fill(QColor(200,0,0,200))
        p = QPainter(fallback_image)
        p.setPen(QColor(255,255,255))
        p.drawText(QRectF(0,0,width,height), Qt.AlignmentFlag.AlignCenter, "春")
        p.end()
        frames.append(fallback_image)

    animation = Animation(name="spring_festival", frames=frames, fps=10) # 提高fps以获得更流畅的烟花效果
    animation.metadata["placeholder"] = True
    animation.metadata["L4_quality"] = True
    animation.metadata["description"] = "春节 L4 占位符动画 - 烟花与灯笼"
    animation.set_loop(True) # 春节动画循环播放
    
    logger.debug(f"创建了春节L4状态的占位符动画，共 {len(frames)} 帧。")
    return animation 