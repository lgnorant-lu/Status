"""
---------------------------------------------------------------
File name:                  pyside_renderer.py
Author:                     Ignorant-lu
Date created:               2025/04/17
Description:                PySide6渲染器实现
----------------------------------------------------------------

Changed history:            
                            2025/04/17: 从PyQt渲染器迁移到PySide渲染器;
                            2025/05/11: 修复枚举类型使用方式；
                            2025/05/11: 修复元类冲突问题；
----
"""

import logging
from typing import Tuple, List, Optional, Dict, Any, Union, cast

from PySide6.QtCore import Qt, QPoint, QRect, QSize
from PySide6.QtGui import (
    QPixmap, QPainter, QColor, QPen, QBrush, QFont, QFontMetrics,
    QTransform, QPainterPath, QImage, QPolygon
)
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Signal, QObject

from status.renderer.renderer_base import (
    RendererBase, Color, Rect, BlendMode, TextAlign, RenderLayer
)

# 设置日志记录器
logger = logging.getLogger(__name__)

class PySideRenderer(RendererBase):
    """PySide6渲染器实现"""
    
    # 信号必须定义在类的作用域内，而不是实例的作用域内
    rendering_started = Signal()
    rendering_finished = Signal()
    
    def __init__(self):
        """初始化PySide渲染器"""
        super().__init__()  # 初始化 RendererBase 基类
        
        self.painter = None
        self.pixmap = None
        self.widget = None
        self.width = 0
        self.height = 0
        self.transform_stack = []  # 变换矩阵栈
        self.clip_rect = None  # 当前裁剪矩形
        self.blend_mode = BlendMode.NORMAL  # 当前混合模式
        self.fonts_cache = {}  # 字体缓存
        
        # 创建默认字体
        self.default_font = QFont()
        self.default_font.setFamily("Arial")
        self.default_font.setPointSize(12)
        
        logger.info("PySide渲染器实例已创建")
    
    def initialize(self, width: int, height: int, **kwargs) -> bool:
        """初始化渲染器
        
        Args:
            width: 渲染区域宽度
            height: 渲染区域高度
            **kwargs: 额外参数，可包含:
                      - widget: 要渲染到的QWidget
                      
        Returns:
            bool: 初始化是否成功
        """
        self.width = width
        self.height = height
        
        # 如果提供了widget，保存它
        if 'widget' in kwargs:
            self.widget = kwargs['widget']
        
        # 创建QPixmap作为渲染缓冲区
        try:
            self.pixmap = QPixmap(width, height)
            # 使用透明色填充
            self.pixmap.fill(QColor(0, 0, 0, 0))
            logger.info(f"PySide渲染器初始化成功 ({width}x{height})")
            return True
        except Exception as e:
            logger.error(f"PySide渲染器初始化失败: {e}")
            return False
    
    def shutdown(self) -> None:
        """关闭渲染器"""
        if self.painter and self.painter.isActive():
            self.painter.end()
            
        self.painter = None
        self.pixmap = None
        self.widget = None
        self.fonts_cache.clear()
        
        logger.info("PySide渲染器已关闭")
    
    def clear(self, color: Optional[Color] = None) -> None:
        """清除画面
        
        Args:
            color: 清除颜色，默认为透明
        """
        if not self.pixmap:
            return
            
        if color:
            self.pixmap.fill(QColor(color.r, color.g, color.b, color.a))
        else:
            # 使用透明色填充
            self.pixmap.fill(QColor(0, 0, 0, 0))
    
    def begin_frame(self) -> None:
        """开始一帧渲染"""
        if not self.pixmap:
            logger.error("渲染缓冲区未初始化")
            return
            
        if self.painter and self.painter.isActive():
            self.painter.end()
            
        self.painter = QPainter(self.pixmap)
        self.painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        
        # 发射信号
        self.rendering_started.emit()
    
    def end_frame(self) -> None:
        """结束一帧渲染并提交"""
        if not self.painter or not self.painter.isActive():
            return
            
        self.painter.end()
        self.painter = None
        
        # 如果有绑定的widget，触发重绘
        if self.widget:
            self.widget.update()
            
        # 发射信号
        self.rendering_finished.emit()
    
    def get_pixmap(self) -> Optional[QPixmap]:
        """获取渲染的QPixmap
        
        Returns:
            Optional[QPixmap]: 渲染的QPixmap，可能为None
        """
        return self.pixmap
    
    def set_viewport(self, x: int, y: int, width: int, height: int) -> None:
        """设置视口
        
        Args:
            x: 视口X坐标
            y: 视口Y坐标
            width: 视口宽度
            height: 视口高度
        """
        if not self.painter or not self.painter.isActive():
            return
            
        self.painter.setViewport(x, y, width, height)
    
    def set_clip_rect(self, rect: Optional[Rect] = None) -> None:
        """设置裁剪矩形
        
        Args:
            rect: 裁剪矩形，None表示取消裁剪
        """
        if not self.painter or not self.painter.isActive():
            return
            
        self.clip_rect = rect
        
        if rect:
            self.painter.setClipRect(QRect(
                int(rect.x), int(rect.y), 
                int(rect.width), int(rect.height)
            ))
        else:
            self.painter.setClipping(False)
    
    def set_blend_mode(self, mode: BlendMode) -> None:
        """设置混合模式
        
        Args:
            mode: 混合模式
        """
        if not self.painter or not self.painter.isActive():
            return
            
        self.blend_mode = mode
        
        # 映射混合模式
        if mode == BlendMode.NORMAL:
            self.painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        elif mode == BlendMode.ALPHA_BLEND:
            self.painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        elif mode == BlendMode.ADDITIVE:
            self.painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
        elif mode == BlendMode.MULTIPLY:
            self.painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Multiply)
        elif mode == BlendMode.SCREEN:
            self.painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Screen)
    
    def draw_point(self, x: float, y: float, color: Color, size: float = 1.0) -> None:
        """绘制点
        
        Args:
            x: X坐标
            y: Y坐标
            color: 颜色
            size: 点大小
        """
        if not self.painter or not self.painter.isActive():
            return
            
        pen = QPen(QColor(color.r, color.g, color.b, color.a))
        pen.setWidth(int(size))
        self.painter.setPen(pen)
        
        self.painter.drawPoint(int(x), int(y))
    
    def draw_line(self, x1: float, y1: float, x2: float, y2: float, color: Color, thickness: float = 1.0) -> None:
        """绘制线段
        
        Args:
            x1: 起点X坐标
            y1: 起点Y坐标
            x2: 终点X坐标
            y2: 终点Y坐标
            color: 颜色
            thickness: 线条粗细
        """
        if not self.painter or not self.painter.isActive():
            return
            
        pen = QPen(QColor(color.r, color.g, color.b, color.a))
        pen.setWidthF(thickness)
        self.painter.setPen(pen)
        
        self.painter.drawLine(
            int(x1), int(y1),
            int(x2), int(y2)
        )
    
    def draw_rect(self, rect: Rect, color: Color, thickness: float = 1.0, filled: bool = False) -> None:
        """绘制矩形
        
        Args:
            rect: 矩形
            color: 颜色
            thickness: 线条粗细
            filled: 是否填充
        """
        if not self.painter or not self.painter.isActive():
            return
            
        pen = QPen(QColor(color.r, color.g, color.b, color.a))
        pen.setWidthF(thickness)
        self.painter.setPen(pen)
        
        if filled:
            self.painter.setBrush(QBrush(QColor(color.r, color.g, color.b, color.a)))
        else:
            self.painter.setBrush(QBrush())
        
        self.painter.drawRect(
            int(rect.x), int(rect.y),
            int(rect.width), int(rect.height)
        )
    
    def draw_circle(self, x: float, y: float, radius: float, color: Color, thickness: float = 1.0, filled: bool = False) -> None:
        """绘制圆形
        
        Args:
            x: 圆心X坐标
            y: 圆心Y坐标
            radius: 半径
            color: 颜色
            thickness: 线条粗细
            filled: 是否填充
        """
        if not self.painter or not self.painter.isActive():
            return
            
        pen = QPen(QColor(color.r, color.g, color.b, color.a))
        pen.setWidthF(thickness)
        self.painter.setPen(pen)
        
        if filled:
            self.painter.setBrush(QBrush(QColor(color.r, color.g, color.b, color.a)))
        else:
            self.painter.setBrush(QBrush())
        
        self.painter.drawEllipse(
            int(x - radius), int(y - radius),
            int(radius * 2), int(radius * 2)
        )
    
    def draw_polygon(self, points: List[Tuple[float, float]], color: Color, thickness: float = 1.0, filled: bool = False) -> None:
        """绘制多边形
        
        Args:
            points: 顶点列表 [(x1, y1), (x2, y2), ...]
            color: 颜色
            thickness: 线条粗细
            filled: 是否填充
        """
        if not self.painter or not self.painter.isActive() or not points:
            return
            
        pen = QPen(QColor(color.r, color.g, color.b, color.a))
        pen.setWidthF(thickness)
        self.painter.setPen(pen)
        
        if filled:
            self.painter.setBrush(QBrush(QColor(color.r, color.g, color.b, color.a)))
        else:
            self.painter.setBrush(QBrush())
        
        # 创建多边形
        polygon = QPolygon()
        for point in points:
            polygon.append(QPoint(int(point[0]), int(point[1])))
        
        self.painter.drawPolygon(polygon)
    
    def draw_text(self, text: str, x: float, y: float, color: Color, font_name: str = "default", font_size: int = 12,
                 align: TextAlign = TextAlign.LEFT, bold: bool = False, italic: bool = False, underline: bool = False) -> Rect:
        """绘制文本
        
        Args:
            text: 文本内容
            x: X坐标
            y: Y坐标
            color: 颜色
            font_name: 字体名称
            font_size: 字体大小
            align: 对齐方式
            bold: 是否粗体
            italic: 是否斜体
            underline: 是否下划线
            
        Returns:
            Rect: 文本绘制的矩形区域
        """
        if not self.painter or not self.painter.isActive() or not text:
            return Rect(x, y, 0, 0)
            
        # 创建字体
        font_key = f"{font_name}_{font_size}_{bold}_{italic}_{underline}"
        if font_key in self.fonts_cache:
            font = self.fonts_cache[font_key]
        else:
            font = QFont(font_name if font_name != "default" else self.default_font.family())
            font.setPointSize(font_size)
            font.setBold(bold)
            font.setItalic(italic)
            font.setUnderline(underline)
            self.fonts_cache[font_key] = font
        
        self.painter.setFont(font)
        self.painter.setPen(QColor(color.r, color.g, color.b, color.a))
        
        # 计算文本大小
        font_metrics = QFontMetrics(font)
        text_width = font_metrics.horizontalAdvance(text)
        text_height = font_metrics.height()
        
        # 根据对齐方式调整X坐标
        draw_x = x
        if align == TextAlign.CENTER:
            draw_x = x - text_width / 2
        elif align == TextAlign.RIGHT:
            draw_x = x - text_width
        
        # 绘制文本
        self.painter.drawText(int(draw_x), int(y + text_height), text)
        
        # 返回文本区域
        return Rect(draw_x, y, text_width, text_height)
    
    def draw_image(self, image: Any, x: float, y: float, width: Optional[float] = None, height: Optional[float] = None,
                  source_rect: Optional[Rect] = None, rotation: float = 0.0, origin: Optional[Tuple[float, float]] = None,
                  flip_h: bool = False, flip_v: bool = False, opacity: float = 1.0) -> None:
        """绘制图像
        
        Args:
            image: 图像对象（QPixmap、QImage或文件路径）
            x: X坐标
            y: Y坐标
            width: 绘制宽度，None表示使用图像原始宽度
            height: 绘制高度，None表示使用图像原始高度
            source_rect: 源矩形（图像的裁剪区域），None表示使用整个图像
            rotation: 旋转角度（度）
            origin: 旋转原点，None表示使用图像中心
            flip_h: 是否水平翻转
            flip_v: 是否垂直翻转
            opacity: 不透明度（0.0-1.0）
        """
        if not self.painter or not self.painter.isActive():
            return
            
        # 获取QPixmap
        pixmap = None
        if isinstance(image, QPixmap):
            pixmap = image
        elif isinstance(image, QImage):
            pixmap = QPixmap.fromImage(image)
        elif isinstance(image, str):
            # 尝试从文件加载
            pixmap = QPixmap(image)
            if pixmap.isNull():
                logger.error(f"无法加载图像: {image}")
                return
        else:
            logger.error(f"不支持的图像类型: {type(image)}")
            return
        
        # 应用裁剪
        if source_rect:
            src_rect = QRect(
                int(source_rect.x), int(source_rect.y),
                int(source_rect.width), int(source_rect.height)
            )
            pixmap = pixmap.copy(src_rect)
        
        # 应用缩放
        if width is not None and height is not None:
            if int(width) != pixmap.width() or int(height) != pixmap.height():
                pixmap = pixmap.scaled(
                    int(width), int(height),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
        
        # 应用翻转
        if flip_h or flip_v:
            pixmap = pixmap.transformed(
                QTransform().scale(-1 if flip_h else 1, -1 if flip_v else 1)
            )
        
        # 应用旋转
        if rotation != 0:
            transform = QTransform()
            
            # 确定旋转原点
            if origin:
                rot_x, rot_y = origin
            else:
                rot_x = pixmap.width() / 2
                rot_y = pixmap.height() / 2
            
            transform.translate(rot_x, rot_y)
            transform.rotate(rotation)
            transform.translate(-rot_x, -rot_y)
            
            pixmap = pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        
        # 应用不透明度
        if opacity < 1.0:
            self.painter.setOpacity(opacity)
        
        # 绘制图像
        self.painter.drawPixmap(int(x), int(y), pixmap)
        
        # 重置不透明度
        if opacity < 1.0:
            self.painter.setOpacity(1.0)
    
    def get_text_size(self, text: str, font_name: str = "default", font_size: int = 12, 
                     bold: bool = False, italic: bool = False) -> Tuple[float, float]:
        """获取文本尺寸
        
        Args:
            text: 文本内容
            font_name: 字体名称
            font_size: 字体大小
            bold: 是否粗体
            italic: 是否斜体
            
        Returns:
            Tuple[float, float]: 文本宽度和高度
        """
        if not text:
            return (0, 0)
            
        # 创建字体
        font = QFont(font_name if font_name != "default" else self.default_font.family())
        font.setPointSize(font_size)
        font.setBold(bold)
        font.setItalic(italic)
        
        # 计算文本大小
        font_metrics = QFontMetrics(font)
        text_width = font_metrics.horizontalAdvance(text)
        text_height = font_metrics.height()
        
        return (text_width, text_height)
    
    def push_transform(self) -> None:
        """保存当前变换矩阵"""
        if not self.painter or not self.painter.isActive():
            return
            
        self.transform_stack.append(self.painter.transform())
    
    def pop_transform(self) -> None:
        """恢复上一个变换矩阵"""
        if not self.painter or not self.painter.isActive() or not self.transform_stack:
            return
            
        transform = self.transform_stack.pop()
        self.painter.setTransform(transform)
    
    def translate(self, x: float, y: float) -> None:
        """平移变换
        
        Args:
            x: X平移量
            y: Y平移量
        """
        if not self.painter or not self.painter.isActive():
            return
            
        self.painter.translate(x, y)
    
    def rotate(self, angle: float) -> None:
        """旋转变换
        
        Args:
            angle: 旋转角度（度）
        """
        if not self.painter or not self.painter.isActive():
            return
            
        self.painter.rotate(angle)
    
    def scale(self, sx: float, sy: float) -> None:
        """缩放变换
        
        Args:
            sx: X缩放因子
            sy: Y缩放因子
        """
        if not self.painter or not self.painter.isActive():
            return
            
        self.painter.scale(sx, sy)
    
    def get_width(self) -> int:
        """获取渲染区域宽度
        
        Returns:
            int: 宽度
        """
        return self.width
    
    def get_height(self) -> int:
        """获取渲染区域高度
        
        Returns:
            int: 高度
        """
        return self.height
    
    def get_renderer_info(self) -> Dict[str, Any]:
        """获取渲染器信息
        
        Returns:
            Dict[str, Any]: 渲染器信息
        """
        return {
            "name": "PySide6 Renderer",
            "version": "1.0",
            "size": (self.width, self.height),
            "features": [
                "hardware_acceleration",
                "alpha_blending",
                "antialiasing",
                "transformations"
            ]
        }
    
    def set_alpha(self, alpha: float) -> None:
        """设置全局透明度
        
        Args:
            alpha: 透明度（0.0-1.0）
        """
        if not self.painter or not self.painter.isActive():
            return
            
        self.painter.setOpacity(alpha)
    
    def set_opacity(self, opacity: float) -> None:
        """设置不透明度
        
        Args:
            opacity: 不透明度，0.0表示完全透明，1.0表示完全不透明
        """
        if not self.painter or not self.painter.isActive():
            return
            
        # 设置全局透明度
        self.painter.setOpacity(max(0.0, min(1.0, opacity)))
    
    def get_opacity(self) -> float:
        """获取当前不透明度
        
        Returns:
            float: 当前不透明度，0.0表示完全透明，1.0表示完全不透明
        """
        if not self.painter or not self.painter.isActive():
            return 1.0
            
        return self.painter.opacity()
    
    def get_viewport_size(self) -> Tuple[int, int]:
        """获取当前视口尺寸
        
        Returns:
            Tuple[int, int]: 视口尺寸 (宽度, 高度)
        """
        return (self.width, self.height)
    
    # 添加save_state方法 
    def save_state(self) -> None:
        """保存当前渲染状态（变换、透明度、裁剪等）"""
        if not self.painter or not self.painter.isActive():
            return
        
        self.painter.save()
    
    # 添加restore_state方法
    def restore_state(self) -> None:
        """恢复之前保存的渲染状态"""
        if not self.painter or not self.painter.isActive():
            return
        
        self.painter.restore()
    
    # 添加create_surface方法
    def create_surface(self, width: Optional[int] = None, height: Optional[int] = None) -> Any:
        """创建离屏渲染表面/目标
        
        Args:
            width: 表面宽度（可选，默认为视口宽度）
            height: 表面高度（可选，默认为视口高度）
            
        Returns:
            QPixmap: 创建的表面对象
        """
        w = width if width is not None else self.width
        h = height if height is not None else self.height
        return QPixmap(w, h)
    
    # 添加set_target方法
    def set_target(self, surface: Optional[Any]) -> None:
        """设置渲染目标
        
        Args:
            surface: 目标表面对象，或None表示默认屏幕
        """
        if not self.painter or not self.painter.isActive():
            return
        
        # 结束当前绘制
        self.painter.end()
        
        # 如果没有提供表面，使用默认表面
        if surface is None:
            self.pixmap = QPixmap(self.width, self.height)
        else:
            # 否则，使用提供的表面
            self.pixmap = surface
        
        # 在新表面上开始绘制
        self.painter.begin(self.pixmap)
    
    # 添加reset_target方法
    def reset_target(self) -> None:
        """重置渲染目标为默认屏幕"""
        self.set_target(None)
    
    # 添加set_dissolve_effect方法
    def set_dissolve_effect(self, pattern: Any, progress: float) -> None:
        """应用溶解效果（特定于溶解转场）
        
        Args:
            pattern: 溶解模式纹理
            progress: 溶解进度 (0.0到1.0)
        """
        # 简单实现：不支持特殊效果
        logger.warning("溶解效果在当前渲染器中不受支持")
    
    # 添加clear_effects方法
    def clear_effects(self) -> None:
        """清除当前活动的特殊效果"""
        # 简单实现：不支持特殊效果
        pass

    def fill_rect(self, x: int, y: int, width: int, height: int, color: Tuple[int, int, int]) -> None:
        """填充矩形区域
        
        Args:
            x: X坐标
            y: Y坐标
            width: 宽度
            height: 高度
            color: 颜色元组 (r, g, b)
        """
        if not self.painter or not self.painter.isActive():
            return
            
        r, g, b = color
        qcolor = QColor(r, g, b, 255)  # 完全不透明
        self.painter.fillRect(
            int(x), int(y), int(width), int(height),
            qcolor
        )
    
    def draw_surface(self, surface: Any, x: float, y: float, opacity: float = 1.0) -> None:
        """绘制表面（QPixmap或QImage）
        
        Args:
            surface: 表面对象
            x: X坐标
            y: Y坐标
            opacity: 不透明度 (0.0-1.0)
        """
        if not self.painter or not self.painter.isActive():
            return

        original_opacity = self.painter.opacity() # Store original
        if opacity < 1.0:
            self.painter.setOpacity(opacity * original_opacity) # Modulate with current painter opacity
            
        if isinstance(surface, QPixmap):
            self.painter.drawPixmap(int(x), int(y), surface)
        elif isinstance(surface, QImage):
            self.painter.drawImage(int(x), int(y), surface)
        else:
            logger.error(f"不支持的表面类型: {type(surface)}")
    
        if opacity < 1.0: # Restore original
            self.painter.setOpacity(original_opacity)
    
    def draw_surface_scaled(self, surface: Any, x: float, y: float, width: float, height: float, opacity: float = 1.0) -> None:
        """绘制缩放的表面
        
        Args:
            surface: 表面对象
            x: X坐标
            y: Y坐标
            width: 宽度
            height: 高度
            opacity: 不透明度 (0.0-1.0)
        """
        if not self.painter or not self.painter.isActive():
            return

        original_opacity = self.painter.opacity()
        if opacity < 1.0:
            self.painter.setOpacity(opacity * original_opacity)
            
        if isinstance(surface, QPixmap):
            self.painter.drawPixmap(
                QRect(int(x), int(y), int(width), int(height)),
                surface
            )
        elif isinstance(surface, QImage):
            self.painter.drawImage(
                QRect(int(x), int(y), int(width), int(height)),
                surface
            )
        else:
            logger.error(f"不支持的表面类型: {type(surface)}") 

        if opacity < 1.0:
            self.painter.setOpacity(original_opacity) 