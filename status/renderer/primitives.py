"""
---------------------------------------------------------------
File name:                  primitives.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                基本图形元素实现，包括点、线、矩形、圆和多边形
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

from typing import List, Tuple, Optional
import math

from status.renderer.renderer_base import RendererBase, Color, Rect, RenderLayer
from status.renderer.drawable import Drawable

class Point(Drawable):
    """点元素"""
    
    def __init__(self, x: float, y: float, color: Color = Color(255, 255, 255), 
                size: float = 1.0, layer: RenderLayer = RenderLayer.MIDDLE, priority: int = 0):
        """初始化点元素
        
        Args:
            x: X坐标
            y: Y坐标
            color: 颜色
            size: 点大小
            layer: 渲染层级
            priority: 优先级
        """
        super().__init__(x, y, size, size, layer, priority)
        self.color = color
        self.size = size
    
    def draw(self, renderer: RendererBase) -> None:
        """绘制点
        
        Args:
            renderer: 渲染器
        """
        if not self.visible or self.opacity <= 0:
            return
            
        # 获取世界坐标
        wx, wy = self.world_position
        
        # 应用不透明度
        draw_color = Color(self.color.r, self.color.g, self.color.b, 
                          int(self.color.a * self.opacity))
        
        # 绘制点
        renderer.draw_point(wx, wy, draw_color, self.size)

class Line(Drawable):
    """线段元素"""
    
    def __init__(self, x1: float, y1: float, x2: float, y2: float, 
                color: Color = Color(255, 255, 255), thickness: float = 1.0,
                layer: RenderLayer = RenderLayer.MIDDLE, priority: int = 0):
        """初始化线段元素
        
        Args:
            x1: 起点X坐标
            y1: 起点Y坐标
            x2: 终点X坐标
            y2: 终点Y坐标
            color: 颜色
            thickness: 线条粗细
            layer: 渲染层级
            priority: 优先级
        """
        # 计算包围盒
        min_x = min(x1, x2)
        min_y = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        
        super().__init__(min_x, min_y, width, height, layer, priority)
        
        # 存储相对于左上角的局部坐标
        self.x1 = x1 - min_x
        self.y1 = y1 - min_y
        self.x2 = x2 - min_x
        self.y2 = y2 - min_y
        self.color = color
        self.thickness = thickness
    
    def set_start_point(self, x: float, y: float) -> None:
        """设置起点
        
        Args:
            x: X坐标
            y: Y坐标
        """
        # 更新包围盒
        old_min_x = self.x
        old_min_y = self.y
        new_min_x = min(x, self.x + self.x2)
        new_min_y = min(y, self.y + self.y2)
        
        # 更新相对坐标
        self.x1 = x - new_min_x
        self.y1 = y - new_min_y
        self.x2 = (self.x + self.x2) - new_min_x
        self.y2 = (self.y + self.y2) - new_min_y
        
        # 更新位置和尺寸
        self.x = new_min_x
        self.y = new_min_y
        self.width = abs(self.x2 - self.x1)
        self.height = abs(self.y2 - self.y1)
        
        self._dirty = True
    
    def set_end_point(self, x: float, y: float) -> None:
        """设置终点
        
        Args:
            x: X坐标
            y: Y坐标
        """
        # 更新包围盒
        old_min_x = self.x
        old_min_y = self.y
        new_min_x = min(self.x + self.x1, x)
        new_min_y = min(self.y + self.y1, y)
        
        # 更新相对坐标
        self.x1 = (self.x + self.x1) - new_min_x
        self.y1 = (self.y + self.y1) - new_min_y
        self.x2 = x - new_min_x
        self.y2 = y - new_min_y
        
        # 更新位置和尺寸
        self.x = new_min_x
        self.y = new_min_y
        self.width = abs(self.x2 - self.x1)
        self.height = abs(self.y2 - self.y1)
        
        self._dirty = True
    
    def get_start_point(self) -> Tuple[float, float]:
        """获取起点（世界坐标）
        
        Returns:
            Tuple[float, float]: 起点坐标
        """
        wx, wy = self.world_position
        return (wx + self.x1, wy + self.y1)
    
    def get_end_point(self) -> Tuple[float, float]:
        """获取终点（世界坐标）
        
        Returns:
            Tuple[float, float]: 终点坐标
        """
        wx, wy = self.world_position
        return (wx + self.x2, wy + self.y2)
    
    def draw(self, renderer: RendererBase) -> None:
        """绘制线段
        
        Args:
            renderer: 渲染器
        """
        if not self.visible or self.opacity <= 0:
            return
            
        # 获取世界坐标
        wx, wy = self.world_position
        
        # 计算实际点坐标
        x1 = wx + self.x1
        y1 = wy + self.y1
        x2 = wx + self.x2
        y2 = wy + self.y2
        
        # 应用不透明度
        draw_color = Color(self.color.r, self.color.g, self.color.b, 
                          int(self.color.a * self.opacity))
        
        # 绘制线段
        renderer.draw_line(x1, y1, x2, y2, draw_color, self.thickness)

class Rectangle(Drawable):
    """矩形元素"""
    
    def __init__(self, x: float, y: float, width: float, height: float, 
                color: Color = Color(255, 255, 255), thickness: float = 1.0,
                filled: bool = False, layer: RenderLayer = RenderLayer.MIDDLE, priority: int = 0):
        """初始化矩形元素
        
        Args:
            x: X坐标
            y: Y坐标
            width: 宽度
            height: 高度
            color: 颜色
            thickness: 线条粗细
            filled: 是否填充
            layer: 渲染层级
            priority: 优先级
        """
        super().__init__(x, y, width, height, layer, priority)
        self.color = color
        self.thickness = thickness
        self.filled = filled
    
    def draw(self, renderer: RendererBase) -> None:
        """绘制矩形
        
        Args:
            renderer: 渲染器
        """
        if not self.visible or self.opacity <= 0:
            return
            
        # 获取世界坐标和尺寸
        wx, wy = self.world_position
        width = self.width * self.scale_x
        height = self.height * self.scale_y
        
        # 应用不透明度
        draw_color = Color(self.color.r, self.color.g, self.color.b, 
                          int(self.color.a * self.opacity))
        
        # 如果有旋转，需要特殊处理
        if self.rotation != 0:
            # 保存当前变换
            renderer.push_transform()
            
            # 计算旋转中心
            cx = wx + self.origin_x * self.scale_x
            cy = wy + self.origin_y * self.scale_y
            
            # 平移到旋转中心
            renderer.translate(cx, cy)
            
            # 应用旋转
            renderer.rotate(self.rotation)
            
            # 平移回去，考虑旋转原点
            renderer.translate(-self.origin_x * self.scale_x, -self.origin_y * self.scale_y)
            
            # 绘制矩形
            rect = Rect(0, 0, width, height)
            renderer.draw_rect(rect, draw_color, self.thickness, self.filled)
            
            # 恢复变换
            renderer.pop_transform()
        else:
            # 无旋转，直接绘制
            rect = Rect(wx, wy, width, height)
            renderer.draw_rect(rect, draw_color, self.thickness, self.filled)

class Circle(Drawable):
    """圆形元素"""
    
    def __init__(self, x: float, y: float, radius: float, 
                color: Color = Color(255, 255, 255), thickness: float = 1.0,
                filled: bool = False, layer: RenderLayer = RenderLayer.MIDDLE, priority: int = 0):
        """初始化圆形元素
        
        Args:
            x: 中心X坐标
            y: 中心Y坐标
            radius: 半径
            color: 颜色
            thickness: 线条粗细
            filled: 是否填充
            layer: 渲染层级
            priority: 优先级
        """
        # 以中心点为基准，计算左上角坐标
        super().__init__(x - radius, y - radius, radius * 2, radius * 2, layer, priority)
        self.set_center_origin()  # 设置旋转原点为中心
        self.radius = radius
        self.color = color
        self.thickness = thickness
        self.filled = filled
    
    @property
    def center_x(self) -> float:
        """获取中心X坐标"""
        return self.x + self.radius
    
    @center_x.setter
    def center_x(self, value: float) -> None:
        """设置中心X坐标"""
        self.x = value - self.radius
        self._dirty = True
    
    @property
    def center_y(self) -> float:
        """获取中心Y坐标"""
        return self.y + self.radius
    
    @center_y.setter
    def center_y(self, value: float) -> None:
        """设置中心Y坐标"""
        self.y = value - self.radius
        self._dirty = True
    
    def set_radius(self, radius: float) -> None:
        """设置半径
        
        Args:
            radius: 半径
        """
        # 保持中心点不变
        center_x = self.center_x
        center_y = self.center_y
        
        self.radius = radius
        self.width = radius * 2
        self.height = radius * 2
        
        # 更新左上角坐标
        self.x = center_x - radius
        self.y = center_y - radius
        
        self._dirty = True
    
    def contains_point(self, x: float, y: float) -> bool:
        """检查点是否在圆内（局部坐标）
        
        Args:
            x: X坐标
            y: Y坐标
            
        Returns:
            bool: 点是否在圆内
        """
        dx = x - self.center_x
        dy = y - self.center_y
        return (dx * dx + dy * dy) <= (self.radius * self.radius)
    
    def draw(self, renderer: RendererBase) -> None:
        """绘制圆形
        
        Args:
            renderer: 渲染器
        """
        if not self.visible or self.opacity <= 0:
            return
            
        # 获取世界坐标
        wx, wy = self.world_position
        
        # 如果有不均匀缩放，会变成椭圆，但当前渲染器不支持直接绘制椭圆
        # 这里简化处理，取平均缩放
        scale = (self.scale_x + self.scale_y) / 2
        radius = self.radius * scale
        
        # 计算中心点
        cx = wx + radius
        cy = wy + radius
        
        # 应用不透明度
        draw_color = Color(self.color.r, self.color.g, self.color.b, 
                          int(self.color.a * self.opacity))
        
        # 绘制圆形
        renderer.draw_circle(cx, cy, radius, draw_color, self.thickness, self.filled)

class Polygon(Drawable):
    """多边形元素"""
    
    def __init__(self, points: List[Tuple[float, float]], 
                color: Color = Color(255, 255, 255), thickness: float = 1.0,
                filled: bool = False, layer: RenderLayer = RenderLayer.MIDDLE, priority: int = 0):
        """初始化多边形元素
        
        Args:
            points: 顶点列表，每个顶点为 (x, y) 元组
            color: 颜色
            thickness: 线条粗细
            filled: 是否填充
            layer: 渲染层级
            priority: 优先级
        """
        if not points or len(points) < 3:
            raise ValueError("多边形至少需要3个顶点")
            
        # 计算包围盒
        min_x = min(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_x = max(p[0] for p in points)
        max_y = max(p[1] for p in points)
        
        width = max_x - min_x
        height = max_y - min_y
        
        super().__init__(min_x, min_y, width, height, layer, priority)
        
        # 存储相对于左上角的局部坐标
        self.relative_points = [(p[0] - min_x, p[1] - min_y) for p in points]
        self.color = color
        self.thickness = thickness
        self.filled = filled
        
        # 计算中心点并设置为旋转原点
        center_x = width / 2
        center_y = height / 2
        self.set_origin(center_x, center_y)
    
    def set_points(self, points: List[Tuple[float, float]]) -> None:
        """设置顶点列表
        
        Args:
            points: 顶点列表，每个顶点为 (x, y) 元组
        """
        if not points or len(points) < 3:
            raise ValueError("多边形至少需要3个顶点")
            
        # 计算包围盒
        min_x = min(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_x = max(p[0] for p in points)
        max_y = max(p[1] for p in points)
        
        width = max_x - min_x
        height = max_y - min_y
        
        # 更新位置和尺寸
        self.x = min_x
        self.y = min_y
        self.width = width
        self.height = height
        
        # 更新相对坐标
        self.relative_points = [(p[0] - min_x, p[1] - min_y) for p in points]
        
        # 更新旋转原点
        center_x = width / 2
        center_y = height / 2
        self.set_origin(center_x, center_y)
        
        self._dirty = True
    
    def get_world_points(self) -> List[Tuple[float, float]]:
        """获取世界坐标系中的顶点列表
        
        Returns:
            List[Tuple[float, float]]: 世界坐标系中的顶点列表
        """
        wx, wy = self.world_position
        
        if self.rotation == 0 and self.scale_x == 1 and self.scale_y == 1:
            # 简单情况：无旋转和缩放
            return [(wx + p[0], wy + p[1]) for p in self.relative_points]
        else:
            # 复杂情况：有旋转或缩放
            result = []
            
            # 旋转中心（世界坐标）
            cx = wx + self.origin_x * self.scale_x
            cy = wy + self.origin_y * self.scale_y
            
            # 旋转角度（弧度）
            rad = math.radians(self.rotation)
            cos_val = math.cos(rad)
            sin_val = math.sin(rad)
            
            for p in self.relative_points:
                # 应用缩放
                px = p[0] * self.scale_x
                py = p[1] * self.scale_y
                
                # 相对于旋转中心的坐标
                dx = px - self.origin_x * self.scale_x
                dy = py - self.origin_y * self.scale_y
                
                # 应用旋转
                rx = dx * cos_val - dy * sin_val
                ry = dx * sin_val + dy * cos_val
                
                # 转换回世界坐标
                world_x = cx + rx
                world_y = cy + ry
                
                result.append((world_x, world_y))
                
            return result
    
    def contains_point(self, x: float, y: float) -> bool:
        """检查点是否在多边形内（局部坐标）
        
        使用射线法判断点是否在多边形内
        
        Args:
            x: X坐标
            y: Y坐标
            
        Returns:
            bool: 点是否在多边形内
        """
        # 相对于左上角的坐标
        x -= self.x
        y -= self.y
        
        points = self.relative_points
        n = len(points)
        inside = False
        
        p1x, p1y = points[0]
        for i in range(n + 1):
            p2x, p2y = points[i % n]
            
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            x_intersect = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= x_intersect:
                            inside = not inside
            p1x, p1y = p2x, p2y
            
        return inside
    
    def draw(self, renderer: RendererBase) -> None:
        """绘制多边形
        
        Args:
            renderer: 渲染器
        """
        if not self.visible or self.opacity <= 0:
            return
            
        # 获取世界坐标系中的顶点
        world_points = self.get_world_points()
        
        # 应用不透明度
        draw_color = Color(self.color.r, self.color.g, self.color.b, 
                          int(self.color.a * self.opacity))
        
        # 绘制多边形
        renderer.draw_polygon(world_points, draw_color, self.thickness, self.filled) 