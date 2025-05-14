"""
---------------------------------------------------------------
File name:                  clicked_placeholder.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                "被点击"状态的L4占位符动画实现
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建;
                            2025/05/15: 提升至L4质量，实现点击反馈动画;
----
"""
import logging
import math # Added math
from typing import List, Optional # Added List
from PySide6.QtGui import QImage, QPainter, QColor, QBrush, QPen, QFont, QPainterPath # Added QPainterPath
from PySide6.QtCore import Qt, QRect, QPointF, QRectF # Added QPointF, QRectF

from status.animation.animation import Animation
from status.behavior.pet_state import PetState

logger = logging.getLogger(__name__)

def _create_clicked_frame(width: int = 64, height: int = 64, frame_number: int = 0, total_frames: int = 16) -> Optional[QImage]:
    """为L4点击动画创建特定帧的图像 (果冻效果 + 惊讶表情)
    
    Args:
        width: 图像宽度
        height: 图像高度
        frame_number: 当前帧序号
        total_frames: 总帧数 (例如16帧，前8帧压缩，后8帧回弹)
        
    Returns:
        QImage: 创建的图像，如果失败则为None
    """
    try:
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(QColor(0,0,0,0)) # Transparent
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        progress = frame_number / total_frames # 0.0 to 1.0
        
        # 果冻效果参数
        # 阶段1: 压缩 (0 -> 0.5 progress)
        # 阶段2: 回弹 (0.5 -> 1.0 progress)
        squash_factor_y = 1.0
        squash_factor_x = 1.0
        translate_y = 0

        if progress < 0.1: # 快速下压
            squash_factor_y = 1.0 - (progress / 0.1) * 0.4 # 最多压缩到0.6倍高度
            squash_factor_x = 1.0 + (progress / 0.1) * 0.2 # 宽度相应增加
            translate_y = (1.0 - squash_factor_y) * (height / 2) * 0.8 # 向下移动以保持底部接触感
        elif progress < 0.5: # 保持压缩一小段时间，然后开始回弹准备
            # 在0.1时: y=0.6, x=1.2
            # 慢慢恢复到 y=0.8, x=1.1 (在progress=0.5前)
            sub_progress = (progress - 0.1) / 0.4
            squash_factor_y = 0.6 + sub_progress * 0.2 
            squash_factor_x = 1.2 - sub_progress * 0.1
            translate_y = (1.0 - squash_factor_y) * (height / 2) * 0.8
        else: # 回弹阶段
            sub_progress = (progress - 0.5) / 0.5 # 0 to 1 for rebound
            # 从 y=0.8, x=1.1 回弹过头一点再恢复
            # 使用sin曲线模拟弹性回弹: y 从 0.8 -> 1.1 -> 0.95 -> 1.0
            # x 从 1.1 -> 0.9 -> 1.02 -> 1.0
            if sub_progress < 0.4: # 过度回弹
                p = sub_progress / 0.4
                squash_factor_y = 0.8 + p * 0.3 # 0.8 -> 1.1
                squash_factor_x = 1.1 - p * 0.2 # 1.1 -> 0.9
            elif sub_progress < 0.7: # 反向压缩
                p = (sub_progress - 0.4) / 0.3
                squash_factor_y = 1.1 - p * 0.15 # 1.1 -> 0.95
                squash_factor_x = 0.9 + p * 0.12 # 0.9 -> 1.02
            else: # 恢复正常
                p = (sub_progress - 0.7) / 0.3
                squash_factor_y = 0.95 + p * 0.05 # 0.95 -> 1.0
                squash_factor_x = 1.02 - p * 0.02 # 1.02 -> 1.0
            translate_y = (1.0 - squash_factor_y) * (height / 2) * 0.5 # 回弹时向上偏移减少

        # 猫咪主体
        body_base_color = QColor(180, 180, 210, 220) # 淡紫色
        painter.setPen(QPen(body_base_color.darker(120), 2))
        painter.setBrush(QBrush(body_base_color))

        original_body_w = width * 0.6
        original_body_h = height * 0.5
        body_w = original_body_w * squash_factor_x
        body_h = original_body_h * squash_factor_y
        body_x = (width - body_w) / 2
        body_y = (height - original_body_h) / 2 + translate_y # 保持中心附近，并应用偏移
        
        painter.drawEllipse(QRectF(body_x, body_y, body_w, body_h))

        # 眼睛 (惊讶状: O O)
        eye_color = QColor(255, 255, 255, 230)
        pupil_color = QColor(30, 30, 30, 220)
        eye_radius = original_body_w * 0.15 * squash_factor_x # 眼睛也随身体略微变形
        pupil_radius = eye_radius * 0.5
        eye_offset_x = original_body_w * 0.2 * squash_factor_x

        # 根据压缩程度调整眼睛位置
        eye_center_y = body_y + body_h * 0.45 

        # 左眼
        painter.setBrush(QBrush(eye_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(body_x + body_w/2 - eye_offset_x, eye_center_y), eye_radius, eye_radius)
        painter.setBrush(QBrush(pupil_color))
        painter.drawEllipse(QPointF(body_x + body_w/2 - eye_offset_x, eye_center_y), pupil_radius, pupil_radius)
        # 右眼
        painter.setBrush(QBrush(eye_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(body_x + body_w/2 + eye_offset_x, eye_center_y), eye_radius, eye_radius)
        painter.setBrush(QBrush(pupil_color))
        painter.drawEllipse(QPointF(body_x + body_w/2 + eye_offset_x, eye_center_y), pupil_radius, pupil_radius)
        
        # 点击时的星光效果 (在压缩最厉害的时候出现几帧)
        if progress > 0.05 and progress < 0.25:
            star_color = QColor(255, 255, 100, 180 - int((progress-0.05)/0.2 * 180)) # 淡出
            painter.setPen(QPen(star_color, 2))
            num_points = 5
            outer_radius = width * 0.15
            inner_radius = width * 0.07
            angle_offset = (progress - 0.05) * math.pi * 10 # 旋转
            
            for i in range(2): # 两颗小星星
                star_center_x = body_x + (body_w * (0.2 + i*0.6)) 
                star_center_y = body_y + body_h * (0.2 if i == 0 else 0.8)
                star_path = QPainterPath()
                for i in range(num_points * 2):
                    radius = outer_radius if i % 2 == 0 else inner_radius
                    angle = (i / (num_points * 2)) * 2 * math.pi + angle_offset
                    x = star_center_x + radius * math.cos(angle)
                    y = star_center_y + radius * math.sin(angle)
                    if i == 0:
                        star_path.moveTo(x,y)
                    else:
                        star_path.lineTo(x,y)
                star_path.closeSubpath()
                painter.drawPath(star_path)

        painter.end()
        return image
    except Exception as e:
        logger.error(f"创建L4 clicked帧 {frame_number} 时出错: {e}", exc_info=True)
        return None

def create_animation() -> Animation:
    """创建\"被点击\"状态的L4占位符动画
    
    Returns:
        Animation: \"被点击\"状态的L4占位符动画对象
    """
    frames: List[QImage] = []
    width, height = 64, 64
    total_animation_frames = 16 # L4 点击动画帧数
    fps = 12 # L4 FPS

    for i in range(total_animation_frames):
        frame_image = _create_clicked_frame(width, height, i, total_animation_frames)
        if frame_image:
            frames.append(frame_image)
    
    if not frames:
        logger.warning("未能为CLICKED状态创建任何L4帧，动画将为空。将使用单帧回退。")
        fallback_image = QImage(width, height, QImage.Format.Format_ARGB32)
        fallback_image.fill(QColor(100,200,255,100))
        p = QPainter(fallback_image)
        p.setFont(QFont("Arial", 10))
        p.drawText(QRectF(0,0,width,height), Qt.AlignmentFlag.AlignCenter, "L4 Click!")
        p.end()
        frames.append(fallback_image)

    animation = Animation(name=PetState.CLICKED.name.lower(), frames=frames, fps=fps)
    animation.metadata["placeholder"] = True
    animation.metadata["L4_quality"] = True
    animation.metadata["description"] = "点击 L4 占位符动画 - Q弹的点击反馈与惊讶表情"
    animation.set_loop(False) # 点击动画通常不循环

    logger.debug(f"创建了被点击L4状态的占位符动画，共 {len(frames)} 帧。")
    return animation 