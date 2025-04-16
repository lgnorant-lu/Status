"""
---------------------------------------------------------------
File name:                  pyqt_renderer.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                PyQt6渲染器实现，使用QPainter进行2D渲染
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

from PyQt6.QtCore import QRectF
import logging
from typing import Dict, Any, List, Tuple, Optional, Union
import math

try:
    from PyQt6.QtCore import Qt, QRect, QPoint, QPointF, QSize, QSizeF, QLineF
    from PyQt6.QtGui import (QPainter, QColor, QPen, QBrush, QPainterPath, QTransform,
                            QImage, QPixmap, QFont, QFontMetrics, QPaintDevice, QPolygonF)
    from PyQt6.QtWidgets import QWidget
    HAS_PYQT = True
except ImportError:
    HAS_PYQT = False
    # 不再需要定义占位符 QColor，因为 HAS_PYQT 会处理未安装的情况
    # class QColor:
    #     def __init__(self, *args, **kwargs):
    #         pass

from status.renderer.renderer_base import (RendererBase, Color, Rect, BlendMode, 
                                          TextAlign, RenderLayer)
from status.resources import ResourceType
from status.resources.asset_manager import AssetManager
from status.renderer.drawable import Drawable

# 尝试导入 pygame，如果失败则标记
HAS_PYGAME = False
try:
    import pygame
    from pygame import Surface as PygameSurface # 显式导入并别名
    HAS_PYGAME = True
except ImportError:
    PygameSurface = None # 定义一个占位符
    pass # Pygame 不是必需的，但如果传入 Surface 会失败

class PyQtRenderer(RendererBase):
    """PyQt6渲染器实现，使用QPainter进行2D渲染"""
    
    def __init__(self):
        """初始化PyQt6渲染器"""
        self.logger = logging.getLogger("Hollow-ming.Renderer.PyQtRenderer")
        
        if not HAS_PYQT:
            self.logger.error("PyQt6未安装，无法初始化PyQt6渲染器")
            return
            
        self.initialized = False
        self.width = 0
        self.height = 0
        self.painter = None
        self.paint_device = None
        self.transform_stack = []
        self.clip_rect = None
        self.asset_manager = AssetManager()
        self.default_font = None
        self.fonts_cache = {}  # 字体缓存
        
        # 混合模式映射
        self.blend_mode_map = {
            BlendMode.NORMAL: QPainter.CompositionMode.CompositionMode_SourceOver,
            BlendMode.ALPHA_BLEND: QPainter.CompositionMode.CompositionMode_SourceOver,
            BlendMode.ADDITIVE: QPainter.CompositionMode.CompositionMode_Plus,
            BlendMode.MULTIPLY: QPainter.CompositionMode.CompositionMode_Multiply,
            BlendMode.SCREEN: QPainter.CompositionMode.CompositionMode_Screen
        }
    
    def initialize(self, width: int, height: int, **kwargs) -> bool:
        """初始化渲染器
        
        Args:
            width: 渲染区域宽度
            height: 渲染区域高度
            **kwargs: 额外参数，可以包含:
                paint_device: QPaintDevice对象，如QWidget或QImage
                
        Returns:
            bool: 初始化是否成功
        """
        if not HAS_PYQT:
            self.logger.error("PyQt6未安装，无法初始化PyQt6渲染器")
            return False
            
        self.width = width
        self.height = height
        
        # 获取绘图设备，默认为None（将在begin_frame时创建临时设备）
        self.paint_device = kwargs.get('paint_device', None)
        
        # 初始化默认字体
        self.default_font = QFont("Arial", 12)
        
        self.initialized = True
        self.logger.info(f"PyQt6渲染器初始化完成，大小: {width}x{height}")
        return True
    
    def shutdown(self) -> None:
        """关闭渲染器"""
        if self.painter and self.painter.isActive():
            self.painter.end()
            
        self.painter = None
        self.initialized = False
        self.logger.info("PyQt6渲染器已关闭")
    
    def clear(self, color: Optional[Color] = None) -> None:
        """清除画面
        
        Args:
            color: 清除颜色，默认为透明
        """
        if not self.initialized or not self.painter:
            return
            
        if not color:
            color = Color(0, 0, 0, 0)  # 透明黑色
            
        qcolor = self._color_to_qcolor(color)
        self.painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        self.painter.fillRect(0, 0, self.width, self.height, qcolor)
        self.painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
    
    def begin_frame(self) -> None:
        """开始一帧渲染"""
        if not self.initialized:
            return
            
        # 如果没有提供绘图设备，使用临时QImage
        temp_image = None
        if not self.paint_device:
            temp_image = QImage(self.width, self.height, QImage.Format.Format_ARGB32_Premultiplied)
            temp_image.fill(Qt.GlobalColor.transparent)
            self.paint_device = temp_image
            
        # 创建或重用画家
        if not self.painter:
            self.painter = QPainter()
            
        # 开始绘制
        self.painter.begin(self.paint_device)
        
        # 设置抗锯齿
        self.painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    
    def end_frame(self) -> None:
        """结束一帧渲染并提交"""
        if not self.initialized or not self.painter:
            return
            
        # 清除变换栈
        self.transform_stack = []
        
        # 结束绘制
        self.painter.end()
    
    def set_viewport(self, x: int, y: int, width: int, height: int) -> None:
        """设置视口
        
        Args:
            x: 视口左上角X坐标
            y: 视口左上角Y坐标
            width: 视口宽度
            height: 视口高度
        """
        if not self.initialized or not self.painter:
            return
            
        self.painter.setViewport(x, y, width, height)
    
    def set_clip_rect(self, rect: Optional[Rect] = None) -> None:
        """设置裁剪矩形
        
        Args:
            rect: 裁剪矩形，None表示取消裁剪
        """
        if not self.initialized or not self.painter:
            return
            
        self.clip_rect = rect
        
        if rect:
            qrect = QRect(int(rect.x), int(rect.y), int(rect.width), int(rect.height))
            self.painter.setClipRect(qrect)
        else:
            self.painter.setClipping(False)
    
    def set_blend_mode(self, mode: BlendMode) -> None:
        """设置混合模式
        
        Args:
            mode: 混合模式
        """
        if not self.initialized or not self.painter:
            return
            
        if mode in self.blend_mode_map:
            self.painter.setCompositionMode(self.blend_mode_map[mode])
    
    def draw_point(self, x: float, y: float, color: Color, size: float = 1.0) -> None:
        """绘制点
        
        Args:
            x: X坐标
            y: Y坐标
            color: 颜色
            size: 点大小
        """
        if not self.initialized or not self.painter:
            return
            
        qcolor = self._color_to_qcolor(color)
        pen = QPen(qcolor)
        pen.setWidth(int(size))
        self.painter.setPen(pen)
        self.painter.drawPoint(QPointF(x, y))
    
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
        if not self.initialized or not self.painter:
            return
            
        qcolor = self._color_to_qcolor(color)
        pen = QPen(qcolor)
        pen.setWidthF(thickness)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.painter.setPen(pen)
        self.painter.drawLine(QLineF(x1, y1, x2, y2))
    
    def draw_rect(self, rect: Rect, color: Color, thickness: float = 1.0, filled: bool = False) -> None:
        """绘制矩形
        
        Args:
            rect: 矩形
            color: 颜色
            thickness: 线条粗细
            filled: 是否填充
        """
        if not self.initialized or not self.painter:
            return
            
        qcolor = self._color_to_qcolor(color)
        qrect = QRectF(rect.x, rect.y, rect.width, rect.height)
        
        if filled:
            self.painter.fillRect(qrect, qcolor)
        else:
            pen = QPen(qcolor)
            pen.setWidthF(thickness)
            self.painter.setPen(pen)
            self.painter.setBrush(Qt.BrushStyle.NoBrush)
            self.painter.drawRect(qrect)
    
    def draw_circle(self, x: float, y: float, radius: float, color: Color, thickness: float = 1.0, filled: bool = False) -> None:
        """绘制圆形
        
        Args:
            x: 中心X坐标
            y: 中心Y坐标
            radius: 半径
            color: 颜色
            thickness: 线条粗细
            filled: 是否填充
        """
        if not self.initialized or not self.painter:
            return
            
        qcolor = self._color_to_qcolor(color)
        qrect = QRectF(x - radius, y - radius, radius * 2, radius * 2)
        
        pen = QPen(qcolor)
        pen.setWidthF(thickness)
        self.painter.setPen(pen)
        
        if filled:
            self.painter.setBrush(QBrush(qcolor))
        else:
            self.painter.setBrush(Qt.BrushStyle.NoBrush)
            
        self.painter.drawEllipse(qrect)
    
    def draw_polygon(self, points: List[Tuple[float, float]], color: Color, thickness: float = 1.0, filled: bool = False) -> None:
        """绘制多边形
        
        Args:
            points: 顶点列表，每个顶点为 (x, y) 元组
            color: 颜色
            thickness: 线条粗细
            filled: 是否填充
        """
        if not self.initialized or not self.painter or not points:
            return
            
        qcolor = self._color_to_qcolor(color)
        polygon = QPolygonF()
        
        for point in points:
            polygon.append(QPointF(point[0], point[1]))
        
        pen = QPen(qcolor)
        pen.setWidthF(thickness)
        self.painter.setPen(pen)
        
        if filled:
            self.painter.setBrush(QBrush(qcolor))
        else:
            self.painter.setBrush(Qt.BrushStyle.NoBrush)
            
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
            Rect: 文本的边界矩形
        """
        if not self.initialized or not self.painter:
            return Rect(x, y, 0, 0)
            
        qcolor = self._color_to_qcolor(color)
        self.painter.setPen(qcolor)
        
        # 获取或创建字体
        font = self._get_font(font_name, font_size, bold, italic, underline)
        self.painter.setFont(font)
        
        # 获取文本度量
        fm = QFontMetrics(font)
        text_width = fm.horizontalAdvance(text)
        text_height = fm.height()
        
        # 根据对齐方式调整位置
        if align == TextAlign.CENTER:
            x -= text_width / 2
        elif align == TextAlign.RIGHT:
            x -= text_width
            
        # 绘制文本
        self.painter.drawText(QPointF(x, y + fm.ascent()), text)
        
        # 返回文本矩形
        return Rect(x, y, text_width, text_height)
    
    def draw_image(self, image: Any, x: float, y: float, width: Optional[float] = None, height: Optional[float] = None,
                  source_rect: Optional[Rect] = None, rotation: float = 0.0, origin: Optional[Tuple[float, float]] = None,
                  flip_h: bool = False, flip_v: bool = False, opacity: float = 1.0) -> None:
        """绘制图像
        
        Args:
            image: 图像对象（QImage, QPixmap或通过AssetManager加载的图像资源）
            x: 目标位置X坐标
            y: 目标位置Y坐标
            width: 目标宽度，None表示使用原始宽度
            height: 目标高度，None表示使用原始高度
            source_rect: 源矩形，用于指定图像的子区域，None表示整个图像
            rotation: 旋转角度（度）
            origin: 旋转原点 (ox, oy)，None表示中心点
            flip_h: 是否水平翻转
            flip_v: 是否垂直翻转
            opacity: 不透明度 (0.0-1.0)
        """
        if not self.initialized or not self.painter:
            return
            
        # 处理图像对象
        qimage = self._get_qimage(image)
        if not qimage:
            return
            
        # 转换为QPixmap用于绘制
        pixmap = QPixmap.fromImage(qimage)
        
        # 获取图像尺寸
        img_width = pixmap.width()
        img_height = pixmap.height()
        
        # 计算目标尺寸
        dest_width = width if width is not None else img_width
        dest_height = height if height is not None else img_height
        
        # 处理翻转
        if flip_h or flip_v:
            transform = QTransform()
            if flip_h:
                transform.scale(-1, 1)
                transform.translate(-img_width, 0)
            if flip_v:
                transform.scale(1, -1)
                transform.translate(0, -img_height)
            pixmap = pixmap.transformed(transform)
        
        # 处理源矩形
        if source_rect:
            src_rect = QRect(int(source_rect.x), int(source_rect.y), 
                            int(source_rect.width), int(source_rect.height))
            pixmap = pixmap.copy(src_rect)
        
        # 保存当前画家状态
        self.painter.save()
        
        # 设置不透明度
        if opacity < 1.0:
            self.painter.setOpacity(opacity)
        
        # 应用旋转
        if rotation != 0.0:
            # 计算旋转原点
            if origin:
                cx, cy = origin
            else:
                cx, cy = x + dest_width / 2, y + dest_height / 2
                
            self.painter.translate(cx, cy)
            self.painter.rotate(rotation)
            self.painter.translate(-cx, -cy)
        
        # 绘制图像
        target_rect = QRectF(x, y, dest_width, dest_height)
        self.painter.drawPixmap(target_rect, pixmap, QRectF(0, 0, pixmap.width(), pixmap.height()))
        
        # 恢复画家状态
        self.painter.restore()
    
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
            Tuple[float, float]: 文本的宽度和高度
        """
        if not self.initialized:
            return (0, 0)
            
        font = self._get_font(font_name, font_size, bold, italic, False)
        fm = QFontMetrics(font)
        
        width = fm.horizontalAdvance(text)
        height = fm.height()
        
        return (width, height)
    
    def push_transform(self) -> None:
        """保存当前变换状态"""
        if not self.initialized or not self.painter:
            return
            
        self.transform_stack.append(self.painter.transform())
    
    def pop_transform(self) -> None:
        """恢复之前保存的变换状态"""
        if not self.initialized or not self.painter or not self.transform_stack:
            return
            
        transform = self.transform_stack.pop()
        self.painter.setTransform(transform)
    
    def translate(self, x: float, y: float) -> None:
        """平移变换
        
        Args:
            x: X方向平移量
            y: Y方向平移量
        """
        if not self.initialized or not self.painter:
            return
            
        self.painter.translate(x, y)
    
    def rotate(self, angle: float) -> None:
        """旋转变换
        
        Args:
            angle: 旋转角度（度）
        """
        if not self.initialized or not self.painter:
            return
            
        self.painter.rotate(angle)
    
    def scale(self, sx: float, sy: float) -> None:
        """缩放变换
        
        Args:
            sx: X方向缩放因子
            sy: Y方向缩放因子
        """
        if not self.initialized or not self.painter:
            return
            
        self.painter.scale(sx, sy)
    
    def get_renderer_info(self) -> Dict[str, Any]:
        """获取渲染器信息
        
        Returns:
            Dict[str, Any]: 渲染器信息字典
        """
        info = {
            "name": "PyQt6渲染器",
            "type": "pyqt",
            "initialized": self.initialized,
            "width": self.width,
            "height": self.height,
            "has_painter": self.painter is not None,
            "transform_stack_depth": len(self.transform_stack),
            "has_clip_rect": self.clip_rect is not None,
        }
        
        return info
    
    # ----- 私有辅助方法 -----
    
    def _color_to_qcolor(self, color: Color) -> QColor:
        """将颜色转换为QColor
        
        Args:
            color: 颜色对象
            
        Returns:
            QColor: Qt颜色对象
        """
        return QColor(color.r, color.g, color.b, color.a)
    
    def _get_font(self, font_name: str, font_size: int, bold: bool, italic: bool, underline: bool) -> QFont:
        """获取或创建字体
        
        Args:
            font_name: 字体名称
            font_size: 字体大小
            bold: 是否粗体
            italic: 是否斜体
            underline: 是否下划线
            
        Returns:
            QFont: Qt字体对象
        """
        # 使用默认字体
        if font_name == "default":
            font = QFont(self.default_font)
            font.setPointSize(font_size)
        else:
            # 尝试从资源管理器加载字体
            try:
                # 注意：AssetManager 可能需要提供 get_font 或 load_font 返回 QFont
                font = self.asset_manager.load_font(font_name, font_size)
                # 如果返回的不是QFont对象（可能是 pygame.font.Font），需要转换或使用默认
                if not isinstance(font, QFont):
                    self.logger.warning(f"加载的字体 '{font_name}' 不是 QFont 类型，使用默认字体。")
                    font = QFont(self.default_font)
                    font.setPointSize(font_size)
            except Exception as e:
                self.logger.error(f"加载字体失败: '{font_name}', 错误: {e}, 使用系统字体。")
                # 如果加载失败，使用系统字体
                font = QFont(font_name, font_size)
        
        # 设置字体样式
        font.setBold(bold)
        font.setItalic(italic)
        font.setUnderline(underline)
        
        return font
    
    def _get_qimage(self, image: Any) -> Optional[QImage]:
        """获取 QImage 对象 (简化版，不再处理 Pygame Surface)。
        
        Args:
            image: 图像对象 (QImage, QPixmap, 或图像路径字符串)
            
        Returns:
            Optional[QImage]: Qt 图像对象，如果无法获取则为 None
        """
        if isinstance(image, QImage):
            return image
        elif isinstance(image, QPixmap):
            return image.toImage()
        elif isinstance(image, str):
            # 尝试从资源管理器加载图像 (假设 AssetManager.load_image 返回 QImage)
            try:
                loaded_image_obj = self.asset_manager.load_image(image)
                if isinstance(loaded_image_obj, QImage):
                    return loaded_image_obj
                elif loaded_image_obj is not None: # 检查是否加载了但类型不对
                    self.logger.warning(f"通过路径 '{image}' 加载了非 QImage 对象: {type(loaded_image_obj)}")
                    return None # 返回 None 因为类型不匹配
                else:
                    # load_image 内部应该已经记录了错误
                    # self.logger.warning(f"通过路径 '{image}' 未能加载到图像对象")
                    return None
            except Exception as e:
                self.logger.error(f"通过路径 '{image}' 加载图像失败: {e}")
                return None
        else:
             # 明确记录不支持的类型
             self.logger.warning(f"不支持的图像类型传递给 _get_qimage: {type(image)}")
             return None 