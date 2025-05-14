"""
---------------------------------------------------------------
File name:                  lichun_placeholder.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                "立春"状态的L4占位符动画实现
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建，实现L4动画;
----
"""
import logging
import math
from typing import List, Optional
from PySide6.QtGui import (QImage, QPainter, QColor, QBrush, QPen, QPolygonF, 
                         QPainterPath, QLinearGradient, QTransform)
from PySide6.QtCore import Qt, QPointF, QRectF

from status.animation.animation import Animation

logger = logging.getLogger(__name__)

def _draw_sprout(painter: QPainter, base_x: float, base_y: float, progress: float, base_height: float, base_width: float):
    """绘制一个生长中的嫩芽"""
    current_height = base_height * progress
    current_width = base_width * (1 + progress * 0.3) # 嫩芽生长时会略微变宽

    if current_height < 1: return

    # 芽的主干
    stem_color = QColor(100, 180, 80, 220) # 嫩绿色
    painter.setPen(QPen(stem_color.darker(110), 1))
    painter.setBrush(QBrush(stem_color))
    
    path = QPainterPath()
    path.moveTo(base_x, base_y)
    # 使用二次贝塞尔曲线模拟生长弯曲
    ctrl_x_offset = current_width * 0.3 * math.sin(progress * math.pi) # 轻微摇摆
    path.quadTo(base_x + ctrl_x_offset, base_y - current_height * 0.5, base_x, base_y - current_height)
    path.quadTo(base_x - ctrl_x_offset, base_y - current_height * 1.5, base_x, base_y - current_height)
    painter.drawPath(path)

    # 叶片 (分阶段出现)
    leaf_color = QColor(120, 200, 100, 230)
    painter.setBrush(QBrush(leaf_color))
    painter.setPen(QPen(leaf_color.darker(110), 1))

    if progress > 0.3: # 第一片叶子
        leaf_path1 = QPainterPath()
        leaf_start_y = base_y - current_height * 0.4
        leaf_path1.moveTo(base_x, leaf_start_y)
        leaf_path1.quadTo(base_x - current_width * 0.5 * (progress-0.2), leaf_start_y - current_height * 0.2, 
                          base_x - current_width * 0.8 * (progress-0.2), leaf_start_y - current_height * 0.5 * (progress-0.2))
        leaf_path1.quadTo(base_x - current_width * 0.4 * (progress-0.2), leaf_start_y - current_height * 0.1, 
                          base_x, leaf_start_y)
        painter.drawPath(leaf_path1)

    if progress > 0.6: # 第二片叶子
        leaf_path2 = QPainterPath()
        leaf_start_y2 = base_y - current_height * 0.7
        leaf_path2.moveTo(base_x, leaf_start_y2)
        leaf_path2.quadTo(base_x + current_width * 0.5 * (progress-0.5), leaf_start_y2 - current_height * 0.2, 
                           base_x + current_width * 0.8 * (progress-0.5), leaf_start_y2 - current_height * 0.5 * (progress-0.5))
        leaf_path2.quadTo(base_x + current_width * 0.4 * (progress-0.5), leaf_start_y2 - current_height * 0.1, 
                           base_x, leaf_start_y2)
        painter.drawPath(leaf_path2)

def _draw_breeze_line(painter: QPainter, start_y: float, width: float, progress: float):
    """绘制一阵微风线条"""
    line_color = QColor(180, 220, 255, int(100 * math.sin(progress * math.pi))) # 随时间淡入淡出
    if line_color.alpha() < 10: return

    painter.setPen(QPen(line_color, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    
    # 飘动的线条
    x_start = -width * 0.2 + width * 1.4 * progress # 线条从左到右移动
    x_end = x_start + width * 0.3 # 线条长度
    
    path = QPainterPath()
    path.moveTo(x_start, start_y)
    ctrl_y_offset = 5 * math.sin(progress * math.pi * 2) # 上下波动
    path.quadTo(x_start + (x_end - x_start) / 2, start_y + ctrl_y_offset, x_end, start_y)
    painter.drawPath(path)

def _create_lichun_frame(width: int, height: int, frame_number: int, total_frames: int) -> Optional[QImage]:
    """为立春动画创建特定帧的图像 - L4质量"""
    try:
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        
        # 背景渐变 - 淡蓝到淡绿
        gradient = QLinearGradient(0, 0, 0, height)
        gradient.setColorAt(0, QColor(200, 230, 255, 200)) # 淡天蓝色
        gradient.setColorAt(1, QColor(210, 240, 200, 220)) # 淡草绿色
        painter = QPainter(image)
        painter.fillRect(image.rect(), gradient)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # --- 绘制生长中的嫩芽 --- 
        # 多个嫩芽，不同生长阶段和位置
        sprout_progress = frame_number / total_frames
        
        _draw_sprout(painter, width * 0.5, height * 0.85, sprout_progress, height * 0.5, width * 0.1)
        if sprout_progress > 0.2:
            _draw_sprout(painter, width * 0.3, height * 0.9, (sprout_progress - 0.2) / 0.8, height * 0.4, width * 0.08)
        if sprout_progress > 0.4:
            _draw_sprout(painter, width * 0.7, height * 0.88, (sprout_progress - 0.4) / 0.6, height * 0.45, width * 0.09)

        # --- 绘制微风效果 --- (贯穿整个动画)
        breeze_progress = (frame_number % (total_frames // 2)) / (total_frames // 2) # 半个周期循环的微风
        _draw_breeze_line(painter, height * 0.3, width, breeze_progress)
        _draw_breeze_line(painter, height * 0.5, width, (breeze_progress + 0.3) % 1.0) # 错开的另一条线
        _draw_breeze_line(painter, height * 0.7, width, (breeze_progress + 0.6) % 1.0)

        # --- 桌宠主体占位符 (感受春风的猫咪) ---
        pet_x = width * 0.5 - 24
        pet_y = height - 64 - 5 # 略微靠下，给嫩芽空间
        
        painter.setPen(QPen(QColor(200, 190, 170), 2)) # 暖灰色
        painter.setBrush(QBrush(QColor(240, 235, 220, 220))) # 浅米色

        # 身体和头部
        painter.drawEllipse(int(pet_x), int(pet_y) + 10, 48, 48) 
        painter.drawEllipse(int(pet_x) + 4, int(pet_y), 40, 40)
        
        # 耳朵 (被微风吹动)
        ear_sway = math.sin(frame_number * 0.2) * 2 # 轻微晃动
        # 左耳
        left_ear = QPolygonF([QPointF(pet_x + 8, pet_y + 10), QPointF(pet_x + 18 + ear_sway, pet_y - 5), QPointF(pet_x + 22, pet_y + 10)])
        painter.drawPolygon(left_ear)
        # 右耳
        right_ear = QPolygonF([QPointF(pet_x + 40, pet_y + 10), QPointF(pet_x + 30 + ear_sway, pet_y - 5), QPointF(pet_x + 26, pet_y + 10)])
        painter.drawPolygon(right_ear)

        # 眼睛 (享受状)
        eye_y = pet_y + 18
        painter.setPen(QPen(QColor(60, 60, 60), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        # 左眼 (向上弯的弧线)
        left_eye_path = QPainterPath()
        left_eye_path.moveTo(pet_x + 12, eye_y + 2)
        left_eye_path.quadTo(pet_x + 17, eye_y - 2, pet_x + 22, eye_y + 2)
        painter.drawPath(left_eye_path)
        # 右眼
        right_eye_path = QPainterPath()
        right_eye_path.moveTo(pet_x + 26, eye_y + 2)
        right_eye_path.quadTo(pet_x + 31, eye_y - 2, pet_x + 36, eye_y + 2)
        painter.drawPath(right_eye_path)
        
        # 嘴巴 (微笑)
        painter.setPen(QPen(QColor(200, 120, 120), 1.5))
        mouth_path = QPainterPath()
        mouth_path.moveTo(pet_x + 20, pet_y + 28)
        mouth_path.quadTo(pet_x + 24, pet_y + 31, pet_x + 28, pet_y + 28)
        painter.drawPath(mouth_path)
        
        painter.end()
        return image
    except Exception as e:
        logger.error(f"创建立春L4帧 {frame_number} 时出错: {e}", exc_info=True)
        return None

def create_animation() -> Animation:
    """创建"立春"状态的L4占位符动画
    
    Returns:
        Animation: "立春"状态的L4占位符动画对象
    """
    frames: List[QImage] = []
    width, height = 64, 64
    total_animation_frames = 30 # L4动画，帧数增加以表现生长和微风

    for i in range(total_animation_frames):
        frame_image = _create_lichun_frame(width, height, i, total_animation_frames)
        if frame_image:
            frames.append(frame_image)
    
    if not frames:
        logger.warning("未能为 LICHUN 状态创建任何L4帧，动画将为空。")
        fallback_image = QImage(width, height, QImage.Format.Format_ARGB32)
        fallback_image.fill(QColor(200,230,200,200))
        p = QPainter(fallback_image)
        p.setPen(QColor(50,100,50))
        p.drawText(QRectF(0,0,width,height), Qt.AlignmentFlag.AlignCenter, "春")
        p.end()
        frames.append(fallback_image)

    animation = Animation(name="lichun", frames=frames, fps=8) # 适中fps
    animation.metadata["placeholder"] = True
    animation.metadata["L4_quality"] = True
    animation.metadata["description"] = "立春 L4 占位符动画 - 嫩芽与微风"
    animation.set_loop(True) # 立春动画循环
    
    logger.debug(f"创建了立春L4状态的占位符动画，共 {len(frames)} 帧。")
    return animation 