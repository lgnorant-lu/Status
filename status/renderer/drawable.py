"""
---------------------------------------------------------------
File name:                  drawable.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                可绘制对象基类，定义可绘制对象的接口和属性
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import uuid
from typing import Tuple, Dict, Any, Optional, List
import math

from status.renderer.renderer_base import RendererBase, Rect, RenderLayer

class Transform:
    """表示2D变换的类，包括位置、旋转和缩放"""
    
    def __init__(self, x: float = 0, y: float = 0, rotation: float = 0, 
                 scale_x: float = 1.0, scale_y: float = 1.0):
        """初始化变换
        
        Args:
            x: X坐标
            y: Y坐标
            rotation: 旋转角度（度）
            scale_x: X轴缩放
            scale_y: Y轴缩放
        """
        self.x = x
        self.y = y
        self.rotation = rotation
        self.scale_x = scale_x
        self.scale_y = scale_y
        self.origin_x = 0.0  # 旋转原点X（相对于左上角）
        self.origin_y = 0.0  # 旋转原点Y（相对于左上角）
        
    @property
    def position(self) -> Tuple[float, float]:
        """获取位置
        
        Returns:
            Tuple[float, float]: (x, y)坐标
        """
        return (self.x, self.y)
        
    @position.setter
    def position(self, value: Tuple[float, float]) -> None:
        """设置位置
        
        Args:
            value: (x, y)坐标
        """
        self.x, self.y = value
        
    def set_position(self, x: float, y: float) -> None:
        """设置位置
        
        Args:
            x: X坐标
            y: Y坐标
        """
        self.x = x
        self.y = y
        
    def translate(self, dx: float, dy: float) -> None:
        """移动位置
        
        Args:
            dx: X方向移动距离
            dy: Y方向移动距离
        """
        self.x += dx
        self.y += dy
        
    def set_rotation(self, angle: float) -> None:
        """设置旋转角度
        
        Args:
            angle: 旋转角度（度）
        """
        self.rotation = angle
        
    def rotate(self, angle: float) -> None:
        """增加旋转角度
        
        Args:
            angle: 旋转角度增量（度）
        """
        self.rotation += angle
        
    def set_scale(self, scale_x: float, scale_y: float = None) -> None:
        """设置缩放
        
        Args:
            scale_x: X轴缩放
            scale_y: Y轴缩放，如果为None则使用scale_x
        """
        self.scale_x = scale_x
        self.scale_y = scale_y if scale_y is not None else scale_x
        
    def set_origin(self, origin_x: float, origin_y: float) -> None:
        """设置旋转和缩放的原点
        
        Args:
            origin_x: 原点X坐标
            origin_y: 原点Y坐标
        """
        self.origin_x = origin_x
        self.origin_y = origin_y
        
    def apply_to_point(self, point_x: float, point_y: float) -> Tuple[float, float]:
        """将变换应用到一个点上
        
        Args:
            point_x: 点的X坐标
            point_y: 点的Y坐标
            
        Returns:
            Tuple[float, float]: 变换后的点坐标
        """
        # 平移点使原点位于旋转中心
        tx = point_x - self.origin_x
        ty = point_y - self.origin_y
        
        # 应用旋转
        angle_rad = math.radians(self.rotation)
        cos_val = math.cos(angle_rad)
        sin_val = math.sin(angle_rad)
        
        rx = tx * cos_val - ty * sin_val
        ry = tx * sin_val + ty * cos_val
        
        # 应用缩放
        sx = rx * self.scale_x
        sy = ry * self.scale_y
        
        # 平移回去并应用位置偏移
        result_x = sx + self.origin_x + self.x
        result_y = sy + self.origin_y + self.y
        
        return (result_x, result_y)
        
    def combine(self, other: 'Transform') -> 'Transform':
        """组合两个变换，返回一个新的变换
        
        Args:
            other: 要组合的另一个变换
            
        Returns:
            Transform: 组合后的变换
        """
        result = Transform()
        result.x = self.x + other.x * self.scale_x
        result.y = self.y + other.y * self.scale_y
        result.rotation = self.rotation + other.rotation
        result.scale_x = self.scale_x * other.scale_x
        result.scale_y = self.scale_y * other.scale_y
        
        # 计算组合后的原点
        # 简化处理，实际上复合变换的原点计算会更复杂
        result.origin_x = self.origin_x
        result.origin_y = self.origin_y
        
        return result
        
    def __str__(self) -> str:
        """字符串表示
        
        Returns:
            str: 变换的字符串表示
        """
        return (f"Transform(pos=({self.x}, {self.y}), "
                f"rot={self.rotation}, "
                f"scale=({self.scale_x}, {self.scale_y}), "
                f"origin=({self.origin_x}, {self.origin_y}))")


class Drawable:
    """可绘制对象基类"""
    
    def __init__(self, x: float = 0, y: float = 0, width: float = 0, height: float = 0, 
                layer: RenderLayer = RenderLayer.MIDDLE, priority: int = 0, visible: bool = True):
        """初始化可绘制对象
        
        Args:
            x: X坐标
            y: Y坐标
            width: 宽度
            height: 高度
            layer: 渲染层级
            priority: 优先级（同层内）
            visible: 是否可见
        """
        self.id = uuid.uuid4()  # 唯一标识符
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.rotation = 0.0  # 旋转角度（度）
        self.origin_x = 0.0  # 旋转原点X（相对于左上角）
        self.origin_y = 0.0  # 旋转原点Y（相对于左上角）
        self.layer = layer
        self.priority = priority
        self.visible = visible
        self.opacity = 1.0
        self.parent = None  # 父对象
        self.children = []  # 子对象列表
        self.tags = set()  # 标签集合
        self.data = {}  # 自定义数据字典
        
        # 坐标变换缓存
        self._world_x = None
        self._world_y = None
        self._dirty = True  # 是否需要更新
    
    @property
    def position(self) -> Tuple[float, float]:
        """获取位置"""
        return (self.x, self.y)
    
    @position.setter
    def position(self, value: Tuple[float, float]) -> None:
        """设置位置"""
        self.x, self.y = value
        self._dirty = True
    
    @property
    def size(self) -> Tuple[float, float]:
        """获取尺寸"""
        return (self.width, self.height)
    
    @size.setter
    def size(self, value: Tuple[float, float]) -> None:
        """设置尺寸"""
        self.width, self.height = value
        self._dirty = True
    
    @property
    def center(self) -> Tuple[float, float]:
        """获取中心点"""
        return (self.x + self.width / 2, self.y + self.height / 2)
    
    @center.setter
    def center(self, value: Tuple[float, float]) -> None:
        """设置中心点"""
        cx, cy = value
        self.x = cx - self.width / 2
        self.y = cy - self.height / 2
        self._dirty = True
    
    @property
    def rect(self) -> Rect:
        """获取矩形边界"""
        return Rect(self.x, self.y, self.width, self.height)
    
    @property
    def world_position(self) -> Tuple[float, float]:
        """获取世界坐标位置（考虑父对象）"""
        if self._dirty or self._world_x is None or self._world_y is None:
            self._update_world_transform()
        return (self._world_x, self._world_y)
    
    @property
    def world_rect(self) -> Rect:
        """获取世界坐标矩形边界"""
        wx, wy = self.world_position
        return Rect(wx, wy, self.width * self.scale_x, self.height * self.scale_y)
    
    def add_child(self, child: 'Drawable') -> None:
        """添加子对象
        
        Args:
            child: 子对象
        """
        if child not in self.children:
            # 如果子对象已有父对象，先从原父对象中移除
            if child.parent:
                child.parent.remove_child(child)
                
            self.children.append(child)
            child.parent = self
            child._dirty = True
    
    def remove_child(self, child: 'Drawable') -> bool:
        """移除子对象
        
        Args:
            child: 子对象
            
        Returns:
            bool: 是否成功移除
        """
        if child in self.children:
            self.children.remove(child)
            child.parent = None
            child._dirty = True
            return True
        return False
    
    def get_all_children(self) -> List['Drawable']:
        """获取所有子对象（递归）
        
        Returns:
            List[Drawable]: 子对象列表
        """
        result = []
        for child in self.children:
            result.append(child)
            result.extend(child.get_all_children())
        return result
    
    def set_origin(self, origin_x: float, origin_y: float) -> None:
        """设置旋转和缩放的原点（相对于左上角）
        
        Args:
            origin_x: 原点X
            origin_y: 原点Y
        """
        self.origin_x = origin_x
        self.origin_y = origin_y
        self._dirty = True
    
    def set_center_origin(self) -> None:
        """设置原点为中心点"""
        self.origin_x = self.width / 2
        self.origin_y = self.height / 2
        self._dirty = True
    
    def move(self, dx: float, dy: float) -> None:
        """移动对象
        
        Args:
            dx: X方向移动距离
            dy: Y方向移动距离
        """
        self.x += dx
        self.y += dy
        self._dirty = True
    
    def rotate(self, angle: float) -> None:
        """旋转对象
        
        Args:
            angle: 旋转角度（度）
        """
        self.rotation += angle
        self._dirty = True
    
    def set_rotation(self, angle: float) -> None:
        """设置对象的旋转角度
        
        Args:
            angle: 旋转角度（度）
        """
        self.rotation = angle
        self._dirty = True
    
    def set_scale(self, scale_x: float, scale_y: float) -> None:
        """设置对象的缩放因子
        
        Args:
            scale_x: X方向缩放因子
            scale_y: Y方向缩放因子
        """
        self.scale_x = scale_x
        self.scale_y = scale_y
        self._dirty = True
    
    def set_opacity(self, opacity: float) -> None:
        """设置对象的不透明度
        
        Args:
            opacity: 不透明度 (0.0-1.0)
        """
        self.opacity = max(0.0, min(1.0, opacity))
    
    def set_visible(self, visible: bool) -> None:
        """设置对象是否可见
        
        Args:
            visible: 是否可见
        """
        self.visible = visible
    
    def add_tag(self, tag: str) -> None:
        """添加标签
        
        Args:
            tag: 标签
        """
        self.tags.add(tag)
    
    def remove_tag(self, tag: str) -> None:
        """移除标签
        
        Args:
            tag: 标签
        """
        if tag in self.tags:
            self.tags.remove(tag)
    
    def has_tag(self, tag: str) -> bool:
        """检查是否有指定标签
        
        Args:
            tag: 标签
            
        Returns:
            bool: 是否有该标签
        """
        return tag in self.tags
    
    def set_data(self, key: str, value: Any) -> None:
        """设置自定义数据
        
        Args:
            key: 键
            value: 值
        """
        self.data[key] = value
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """获取自定义数据
        
        Args:
            key: 键
            default: 默认值
            
        Returns:
            Any: 值
        """
        return self.data.get(key, default)
    
    def contains_point(self, x: float, y: float) -> bool:
        """检查点是否在对象内（局部坐标）
        
        Args:
            x: X坐标
            y: Y坐标
            
        Returns:
            bool: 点是否在对象内
        """
        return (self.x <= x <= self.x + self.width and 
                self.y <= y <= self.y + self.height)
    
    def contains_point_world(self, x: float, y: float) -> bool:
        """检查点是否在对象内（世界坐标）
        
        Args:
            x: X坐标
            y: Y坐标
            
        Returns:
            bool: 点是否在对象内
        """
        # 如果有旋转，需要将点转换到局部坐标
        if self.rotation != 0:
            # 获取世界坐标下的旋转原点
            wx, wy = self.world_position
            ox = wx + self.origin_x * self.scale_x
            oy = wy + self.origin_y * self.scale_y
            
            # 将点坐标相对于旋转原点
            dx = x - ox
            dy = y - oy
            
            # 应用旋转变换的逆变换
            rad = math.radians(-self.rotation)
            cos_val = math.cos(rad)
            sin_val = math.sin(rad)
            
            rx = dx * cos_val - dy * sin_val
            ry = dx * sin_val + dy * cos_val
            
            # 转换回相对于对象左上角的坐标
            x = rx + ox - self.world_position[0]
            y = ry + oy - self.world_position[1]
        else:
            # 转换到局部坐标
            x = (x - self.world_position[0]) / self.scale_x
            y = (y - self.world_position[1]) / self.scale_y
            
        return self.contains_point(x, y)
    
    def intersects(self, other: 'Drawable') -> bool:
        """检查是否与另一个可绘制对象相交
        
        Args:
            other: 另一个可绘制对象
            
        Returns:
            bool: 是否相交
        """
        return self.rect.intersects(other.rect)
    
    def update(self, dt: float) -> None:
        """更新对象状态
        
        Args:
            dt: 时间增量（秒）
        """
        # 基类中的默认实现仅更新子对象
        for child in self.children:
            child.update(dt)
    
    def draw(self, renderer: RendererBase) -> None:
        """绘制对象
        
        Args:
            renderer: 渲染器
        """
        # 基类不实现具体绘制，由子类实现
        pass
    
    def draw_debug(self, renderer: RendererBase) -> None:
        """绘制调试信息
        
        Args:
            renderer: 渲染器
        """
        from status.renderer.renderer_base import Color
        
        # 绘制边界矩形
        debug_color = Color(0, 255, 0, 128)  # 半透明绿色
        renderer.draw_rect(self.rect, debug_color, 1.0, False)
        
        # 绘制原点
        origin_color = Color(255, 0, 0, 192)  # 半透明红色
        ox = self.x + self.origin_x
        oy = self.y + self.origin_y
        renderer.draw_circle(ox, oy, 3, origin_color, 1.0, True)
    
    def _update_world_transform(self) -> None:
        """更新世界变换"""
        if self.parent:
            # 获取父对象的世界坐标
            parent_x, parent_y = self.parent.world_position
            
            # 如果父对象有旋转和缩放，需要考虑这些变换
            if self.parent.rotation != 0 or self.parent.scale_x != 1 or self.parent.scale_y != 1:
                # 旋转和缩放的原点（在父对象局部坐标系中）
                origin_x = self.parent.origin_x
                origin_y = self.parent.origin_y
                
                # 计算相对于原点的坐标
                rel_x = self.x - origin_x
                rel_y = self.y - origin_y
                
                # 应用父对象的缩放
                rel_x *= self.parent.scale_x
                rel_y *= self.parent.scale_y
                
                # 应用父对象的旋转
                rad = math.radians(self.parent.rotation)
                cos_val = math.cos(rad)
                sin_val = math.sin(rad)
                
                rot_x = rel_x * cos_val - rel_y * sin_val
                rot_y = rel_x * sin_val + rel_y * cos_val
                
                # 转换回相对于父对象左上角的坐标
                self._world_x = parent_x + rot_x + origin_x * self.parent.scale_x
                self._world_y = parent_y + rot_y + origin_y * self.parent.scale_y
            else:
                # 简单情况：父对象没有旋转和缩放
                self._world_x = parent_x + self.x
                self._world_y = parent_y + self.y
        else:
            # 没有父对象，世界坐标等于局部坐标
            self._world_x = self.x
            self._world_y = self.y
            
        self._dirty = False
        
        # 子对象也需要更新
        for child in self.children:
            child._dirty = True 