"""
---------------------------------------------------------------
File name:                  drawable.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                可绘制对象基类，定义可绘制对象的接口和属性
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
                            2025/05/15: 修复类型提示错误;
----
"""

import uuid
from typing import Tuple, Dict, Any, Optional, List, Set, cast
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
        self.x: float = x
        self.y: float = y
        self.rotation: float = rotation
        self.scale_x: float = scale_x
        self.scale_y: float = scale_y
        self.origin_x: float = 0.0  # 旋转原点X（相对于左上角）
        self.origin_y: float = 0.0  # 旋转原点Y（相对于左上角）
        
    @property
    def position(self) -> Tuple[float, float]:
        """获取位置"""
        return (self.x, self.y)
        
    @position.setter
    def position(self, value: Tuple[float, float]) -> None:
        """设置位置"""
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
        
    def set_scale(self, scale_x: float, scale_y: Optional[float] = None) -> None:
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
        self.id: uuid.UUID = uuid.uuid4()  # 唯一标识符
        self.x: float = x
        self.y: float = y
        self.width: float = width
        self.height: float = height
        self.scale_x: float = 1.0
        self.scale_y: float = 1.0
        self.rotation: float = 0.0  # 旋转角度（度）
        self.origin_x: float = 0.0  # 旋转原点X（相对于左上角）
        self.origin_y: float = 0.0  # 旋转原点Y（相对于左上角）
        self.layer: RenderLayer = layer
        self.priority: int = priority
        self.visible: bool = visible
        self.opacity: float = 1.0
        self.parent: Optional['Drawable'] = None  # 父对象
        self.children: List['Drawable'] = []  # 子对象列表
        self.tags: Set[str] = set()  # 标签集合
        self.data: Dict[str, Any] = {}  # 自定义数据字典
        
        # 坐标变换缓存
        # Initialize world transform cache to match local transform initially
        self._world_x: float = self.x
        self._world_y: float = self.y
        self._world_scale_x: float = self.scale_x
        self._world_scale_y: float = self.scale_y
        self._world_rotation: float = self.rotation
        self._dirty: bool = True  # Whether the world transform needs updating
    
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
    
    def add_child(self, child: 'Drawable') -> None:
        """添加子对象"""
        if child not in self.children:
            self.children.append(child)
            child.parent = self
            child._dirty = True
    
    def remove_child(self, child: 'Drawable') -> bool:
        """移除子对象"""
        if child in self.children:
            self.children.remove(child)
            child.parent = None
            child._dirty = True
            return True
        return False
    
    def get_all_children(self) -> List['Drawable']:
        """获取所有子对象（包括子对象的子对象）"""
        all_children = []
        for child in self.children:
            all_children.append(child)
            all_children.extend(child.get_all_children())
        return all_children
    
    def set_origin(self, origin_x: float, origin_y: float) -> None:
        """设置旋转和缩放的原点（相对于对象左上角）"""
        self.origin_x = origin_x
        self.origin_y = origin_y
        self._dirty = True
    
    def set_center_origin(self) -> None:
        """设置旋转和缩放的原点为对象中心"""
        self.origin_x = self.width / 2
        self.origin_y = self.height / 2
        self._dirty = True
    
    def move(self, dx: float, dy: float) -> None:
        """移动对象"""
        self.x += dx
        self.y += dy
        self._dirty = True
    
    def rotate(self, angle: float) -> None:
        """增加旋转角度"""
        self.rotation += angle
        self._dirty = True
    
    def set_rotation(self, angle: float) -> None:
        """设置旋转角度"""
        self.rotation = angle
        self._dirty = True
    
    def set_scale(self, scale_x: float, scale_y: float) -> None:
        """设置缩放"""
        self.scale_x = scale_x
        self.scale_y = scale_y
        self._dirty = True
    
    def set_opacity(self, opacity: float) -> None:
        """设置透明度 (0.0 - 1.0)"""
        self.opacity = max(0.0, min(1.0, opacity))
    
    def set_visible(self, visible: bool) -> None:
        """设置可见性"""
        self.visible = visible
    
    def add_tag(self, tag: str) -> None:
        """添加标签"""
        self.tags.add(tag)
    
    def remove_tag(self, tag: str) -> None:
        """移除标签"""
        self.tags.discard(tag)
    
    def has_tag(self, tag: str) -> bool:
        """检查是否包含标签"""
        return tag in self.tags
    
    def set_data(self, key: str, value: Any) -> None:
        """设置自定义数据"""
        self.data[key] = value
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """获取自定义数据"""
        return self.data.get(key, default)
    
    def contains_point(self, x: float, y: float) -> bool:
        """检查点是否在对象边界内"""
        # 将传入的(x,y)视为世界坐标，转换为对象局部坐标
        local_x = x - self.x
        local_y = y - self.y
        return 0 <= local_x <= self.width and 0 <= local_y <= self.height
    
    def contains_point_world(self, x: float, y: float) -> bool:
        """检查世界坐标点是否在对象边界内"""
        # 这是一个简化的实现，只考虑了平移和缩放，没有考虑旋转和原点
        # 更精确的实现需要将世界坐标点反向变换到对象的局部坐标系，再进行判断
        # 考虑父对象的世界变换
        if self.parent:
            parent_world_x, parent_world_y = self.parent.world_position
            parent_world_scale_x, parent_world_scale_y = self.parent.world_scale
            parent_world_rotation = self.parent.world_rotation

            # 反向应用父对象的平移
            relative_x = x - parent_world_x
            relative_y = y - parent_world_y

            # 反向应用父对象的旋转 (简化处理)
            # angle_rad = math.radians(-parent_world_rotation)
            # cos_val = math.cos(angle_rad)
            # sin_val = math.sin(angle_rad)
            # rotated_x = relative_x * cos_val - relative_y * sin_val
            # rotated_y = relative_x * sin_val + relative_y * cos_val
            rotated_x, rotated_y = relative_x, relative_y # 暂时忽略旋转

            # 反向应用父对象的缩放
            local_x = rotated_x / parent_world_scale_x if parent_world_scale_x != 0 else rotated_x
            local_y = rotated_y / parent_world_scale_y if parent_world_scale_y != 0 else rotated_y

            # 再减去对象自身的局部位置，得到相对于对象左上角的坐标
            object_local_x = local_x - self.x
            object_local_y = local_y - self.y

        else:
            # 没有父对象，世界坐标就是局部坐标
            object_local_x = x - self.x
            object_local_y = y - self.y

        # 检查点是否在对象的局部边界内
        return 0 <= object_local_x <= self.width * self.scale_x and \
               0 <= object_local_y <= self.height * self.scale_y
    
    def intersects(self, other: 'Drawable') -> bool:
        """检查是否与另一个可绘制对象相交（考虑世界变换）"""
        # 这是一个简化的实现，只检查世界坐标系的矩形边界是否相交
        # 更精确的实现需要将两个对象的边界都变换到同一个坐标系（如世界坐标系），再进行相交测试
        # 并且需要考虑旋转
        return self.world_rect.intersects(other.world_rect)
    
    def update(self, dt: float) -> None:
        """更新对象状态"""
        # 默认实现为空，子类可以重写此方法
        pass
    
    def draw(self, renderer: RendererBase) -> None:
        """绘制对象"""
        # 默认实现为空，子类必须重写此方法
        # 绘制时应该先设置渲染器变换，然后调用渲染器的绘制方法
        pass
    
    def draw_debug(self, renderer: RendererBase) -> None:
        """绘制调试信息"""
        # 默认实现为空，子类可以重写此方法
        pass
    
    def _update_world_transform(self) -> None:
        """更新世界坐标变换缓存"""
        if not self._dirty:
            return

        if self.parent:
            # Recursive update of parent's transform
            self.parent._update_world_transform()

            # Calculate world position, scale, and rotation
            parent_world_x, parent_world_y = self.parent.world_position
            parent_world_scale_x, parent_world_scale_y = self.parent.world_scale
            parent_world_rotation = self.parent.world_rotation

            # Apply parent's scale and rotation to local position
            # This is a simplified 2D transformation composition
            translated_x = self.x * parent_world_scale_x
            translated_y = self.y * parent_world_scale_y

            angle_rad = math.radians(parent_world_rotation)
            cos_val = math.cos(angle_rad)
            sin_val = math.sin(angle_rad)
                
            rotated_x = translated_x * cos_val - translated_y * sin_val
            rotated_y = translated_x * sin_val + translated_y * cos_val
                
            # Apply parent's world position
            self._world_x = parent_world_x + rotated_x
            self._world_y = parent_world_y + rotated_y

            # Combine scales and rotations
            self._world_scale_x = self.scale_x * parent_world_scale_x
            self._world_scale_y = self.scale_y * parent_world_scale_y
            self._world_rotation = self.rotation + parent_world_rotation

        else:
            # No parent, world transform is same as local transform
            self._world_x = self.x
            self._world_y = self.y
            self._world_scale_x = self.scale_x
            self._world_scale_y = self.scale_y
            self._world_rotation = self.rotation
            
        self._dirty = False
        
    @property
    def world_position(self) -> Tuple[float, float]:
        """获取对象在世界坐标系中的位置"""
        self._update_world_transform()
        # Now that _world_x and _world_y are guaranteed to be set as floats,
        # we can directly return the tuple.
        return (self._world_x, self._world_y)

    @property
    def world_rect(self) -> Rect:
        """获取对象在世界坐标系中的矩形区域"""
        # This calculation needs to transform the object's four corner points to world coordinates,
        # then find the min/max coordinates. This is a simplified implementation.
        # We'll use world position and world size, ignoring rotation for the bounding box.
        world_x, world_y = self.world_position
        world_scale_x, world_scale_y = self.world_scale
        world_width = self.width * world_scale_x
        world_height = self.height * world_scale_y
        # Need to consider the origin if width/height are used relative to it.
        # For simplicity, assuming origin (0,0) relative to top-left for this rect.
        return Rect(world_x, world_y, world_width, world_height)

    @property
    def world_scale(self) -> Tuple[float, float]:
        """获取对象在世界坐标系中的缩放"""
        self._update_world_transform()
        # Similar to world_position, attributes are now guaranteed floats.
        return (self._world_scale_x, self._world_scale_y)

    @property
    def world_rotation(self) -> float:
        """获取对象在世界坐标系中的旋转角度"""
        self._update_world_transform()
        # _world_rotation is now a float
        return self._world_rotation