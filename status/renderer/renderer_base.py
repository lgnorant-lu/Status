"""
---------------------------------------------------------------
File name:                  renderer_base.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                渲染器基类，定义渲染系统的抽象接口
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
                            2025/05/11: 创建混合元类以解决QObject和ABC的元类冲突；
----
"""

from abc import ABC, ABCMeta, abstractmethod
from typing import Tuple, List, Optional, Dict, Any, Union
import enum

from PySide6.QtCore import QObject, Signal

# 创建一个混合元类，解决QObject和ABC的元类冲突
class QObjectABCMeta(type(QObject), ABCMeta):
    """混合元类，继承自QObject的元类和ABCMeta"""
    pass

class BlendMode(enum.Enum):
    """混合模式枚举"""
    NORMAL = 0          # 正常（覆盖）
    ALPHA_BLEND = 1     # 半透明混合
    ADDITIVE = 2        # 加法混合
    MULTIPLY = 3        # 乘法混合
    SCREEN = 4          # 屏幕混合

class TextAlign(enum.Enum):
    """文本对齐方式枚举"""
    LEFT = 0            # 左对齐
    CENTER = 1          # 居中对齐
    RIGHT = 2           # 右对齐
    
class RenderLayer(enum.Enum):
    """渲染层级枚举"""
    BACKGROUND = 0      # 背景层
    MIDDLE = 1          # 中间层
    FOREGROUND = 2      # 前景层
    UI = 3              # UI层
    DEBUG = 4           # 调试层

class Color:
    """颜色类"""
    
    def __init__(self, r: int, g: int, b: int, a: int = 255):
        """初始化颜色
        
        Args:
            r: 红色分量 (0-255)
            g: 绿色分量 (0-255)
            b: 蓝色分量 (0-255)
            a: 透明度 (0-255)，255为不透明
        """
        self.r = max(0, min(255, r))
        self.g = max(0, min(255, g))
        self.b = max(0, min(255, b))
        self.a = max(0, min(255, a))
    
    @classmethod
    def from_hex(cls, hex_color: str):
        """从十六进制颜色代码创建颜色
        
        Args:
            hex_color: 十六进制颜色代码，如 "#FF0000" 或 "#FF0000FF"
        
        Returns:
            Color: 颜色对象
        """
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            return cls(r, g, b)
        elif len(hex_color) == 8:
            r, g, b, a = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4, 6))
            return cls(r, g, b, a)
        else:
            raise ValueError(f"无效的十六进制颜色代码: {hex_color}")
    
    def copy(self) -> 'Color':
        """创建颜色对象的副本
        
        Returns:
            Color: 颜色对象的副本
        """
        return Color(self.r, self.g, self.b, self.a)
    
    def __eq__(self, other: object) -> bool:
        """比较两个颜色对象是否相等
        
        Args:
            other: 另一个颜色对象
            
        Returns:
            bool: 是否相等
        """
        if not isinstance(other, Color):
            return False
        return (self.r == other.r and 
                self.g == other.g and 
                self.b == other.b and 
                self.a == other.a)
    
    def to_tuple(self) -> Tuple[int, int, int, int]:
        """转换为元组 (r, g, b, a)
        
        Returns:
            Tuple[int, int, int, int]: 颜色元组
        """
        return (self.r, self.g, self.b, self.a)
    
    def __repr__(self):
        return f"Color(r={self.r}, g={self.g}, b={self.b}, a={self.a})"

class Rect:
    """矩形类"""
    
    def __init__(self, x: float, y: float, width: float, height: float):
        """初始化矩形
        
        Args:
            x: X坐标
            y: Y坐标
            width: 宽度
            height: 高度
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    @property
    def left(self) -> float:
        """左边界X坐标"""
        return self.x
    
    @property
    def right(self) -> float:
        """右边界X坐标"""
        return self.x + self.width
    
    @property
    def top(self) -> float:
        """上边界Y坐标"""
        return self.y
    
    @property
    def bottom(self) -> float:
        """下边界Y坐标"""
        return self.y + self.height
    
    @property
    def center(self) -> Tuple[float, float]:
        """中心点坐标"""
        return (self.x + self.width / 2, self.y + self.height / 2)
    
    @property
    def size(self) -> Tuple[float, float]:
        """尺寸"""
        return (self.width, self.height)
    
    @property
    def topleft(self) -> Tuple[float, float]:
        """左上角坐标"""
        return (self.x, self.y)
    
    def contains_point(self, x: float, y: float) -> bool:
        """检查点是否在矩形内
        
        Args:
            x: 点的X坐标
            y: 点的Y坐标
            
        Returns:
            bool: 点是否在矩形内
        """
        return self.x <= x <= self.right and self.y <= y <= self.bottom
    
    def intersects(self, other: 'Rect') -> bool:
        """检查是否与另一个矩形相交
        
        Args:
            other: 另一个矩形
            
        Returns:
            bool: 是否相交
        """
        return (self.left < other.right and self.right > other.left and
                self.top < other.bottom and self.bottom > other.top)
    
    def __repr__(self):
        return f"Rect(x={self.x}, y={self.y}, width={self.width}, height={self.height})"
    
    def __eq__(self, other: object) -> bool:
        """比较两个矩形对象是否相等
        
        Args:
            other: 另一个矩形对象
            
        Returns:
            bool: 是否相等
        """
        if not isinstance(other, Rect):
            return False
        return (self.x == other.x and 
                self.y == other.y and 
                self.width == other.width and 
                self.height == other.height)

class RendererBase(QObject, ABC, metaclass=QObjectABCMeta):
    """渲染器基类，定义渲染系统的抽象接口"""
    
    def __init__(self):
        """初始化渲染器基类"""
        super().__init__()  # 初始化QObject
    
    @abstractmethod
    def initialize(self, width: int, height: int, **kwargs) -> bool:
        """初始化渲染器
        
        Args:
            width: 渲染区域宽度
            height: 渲染区域高度
            **kwargs: 额外参数
            
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """关闭渲染器"""
        pass
    
    @abstractmethod
    def clear(self, color: Optional[Color] = None) -> None:
        """清除画面
        
        Args:
            color: 清除颜色，默认为透明
        """
        pass
    
    @abstractmethod
    def begin_frame(self) -> None:
        """开始一帧渲染"""
        pass
    
    @abstractmethod
    def end_frame(self) -> None:
        """结束一帧渲染并提交"""
        pass
    
    @abstractmethod
    def set_viewport(self, x: int, y: int, width: int, height: int) -> None:
        """设置视口
        
        Args:
            x: 视口左上角X坐标
            y: 视口左上角Y坐标
            width: 视口宽度
            height: 视口高度
        """
        pass
    
    @abstractmethod
    def set_clip_rect(self, rect: Optional[Rect] = None) -> None:
        """设置裁剪矩形
        
        Args:
            rect: 裁剪矩形，None表示取消裁剪
        """
        pass
    
    @abstractmethod
    def set_blend_mode(self, mode: BlendMode) -> None:
        """设置混合模式
        
        Args:
            mode: 混合模式
        """
        pass
    
    @abstractmethod
    def draw_point(self, x: float, y: float, color: Color, size: float = 1.0) -> None:
        """绘制点
        
        Args:
            x: X坐标
            y: Y坐标
            color: 颜色
            size: 点大小
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def draw_rect(self, rect: Rect, color: Color, thickness: float = 1.0, filled: bool = False) -> None:
        """绘制矩形
        
        Args:
            rect: 矩形
            color: 颜色
            thickness: 线条粗细
            filled: 是否填充
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def draw_polygon(self, points: List[Tuple[float, float]], color: Color, thickness: float = 1.0, filled: bool = False) -> None:
        """绘制多边形
        
        Args:
            points: 顶点列表，每个顶点为 (x, y) 元组
            color: 颜色
            thickness: 线条粗细
            filled: 是否填充
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def draw_image(self, image: Any, x: float, y: float, width: Optional[float] = None, height: Optional[float] = None,
                  source_rect: Optional[Rect] = None, rotation: float = 0.0, origin: Optional[Tuple[float, float]] = None,
                  flip_h: bool = False, flip_v: bool = False, opacity: float = 1.0) -> None:
        """绘制图像
        
        Args:
            image: 图像对象
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def push_transform(self) -> None:
        """保存当前变换状态"""
        pass
    
    @abstractmethod
    def pop_transform(self) -> None:
        """恢复之前保存的变换状态"""
        pass
    
    @abstractmethod
    def translate(self, x: float, y: float) -> None:
        """平移变换
        
        Args:
            x: X方向平移量
            y: Y方向平移量
        """
        pass
    
    @abstractmethod
    def rotate(self, angle: float) -> None:
        """旋转变换
        
        Args:
            angle: 旋转角度（度）
        """
        pass
    
    @abstractmethod
    def scale(self, sx: float, sy: float) -> None:
        """缩放变换
        
        Args:
            sx: X方向缩放因子
            sy: Y方向缩放因子
        """
        pass
    
    @abstractmethod
    def get_renderer_info(self) -> Dict[str, Any]:
        """获取渲染器信息
        
        Returns:
            Dict[str, Any]: 渲染器信息字典
        """
        pass 