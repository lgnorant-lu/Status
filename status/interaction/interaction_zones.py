"""
---------------------------------------------------------------
File name:                  interaction_zones.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                定义桌宠交互区域，支持不同的形状和交互类型
----------------------------------------------------------------

Changed history:            
                            2025/05/13: 初始创建;
----
"""

import math
import logging
from enum import Enum, auto
from typing import List, Tuple, Union, Optional, Set, Dict, Any, Callable
from status.core.event_system import EventSystem, EventType, Event

# 点坐标类型 (x, y)
Point = Tuple[float, float]

class InteractionType(Enum):
    """交互类型枚举"""
    CLICK = auto()      # 单击
    DOUBLE_CLICK = auto()  # 双击
    RIGHT_CLICK = auto()  # 右键点击
    HOVER = auto()      # 悬停
    DRAG = auto()       # 拖拽
    DROP = auto()       # 放下
    CUSTOM = auto()     # 自定义交互


class ZoneShape(Enum):
    """区域形状枚举"""
    CIRCLE = auto()    # 圆形
    RECTANGLE = auto()  # 矩形
    POLYGON = auto()    # 多边形


class InteractionZone:
    """交互区域定义类
    
    可以定义桌宠身上的可交互区域，支持圆形、矩形、多边形
    并提供点是否在区域内的检测方法
    """
    
    def __init__(self, 
                 zone_id: str, 
                 shape: ZoneShape, 
                 params: Dict[str, Any], 
                 supported_interactions: Optional[Set[InteractionType]] = None,
                 enabled: bool = True):
        """初始化交互区域
        
        Args:
            zone_id: 区域唯一标识符
            shape: 区域形状，ZoneShape枚举
            params: 形状参数，依形状类型不同而不同:
                   - CIRCLE: {'center': (x, y), 'radius': r}
                   - RECTANGLE: {'top_left': (x, y), 'width': w, 'height': h}
                   - POLYGON: {'points': [(x1, y1), (x2, y2), ...]}
            supported_interactions: 支持的交互类型集合
            enabled: 是否启用该区域
        """
        self.logger = logging.getLogger("Status.Interaction.InteractionZone")
        self.zone_id = zone_id
        self.shape = shape
        self.params = params
        self.enabled = enabled
        self.active = False  # 当前是否激活（如鼠标悬停其上）
        
        # 如果未指定支持的交互类型，则默认支持所有类型
        if supported_interactions is None:
            self.supported_interactions = set(InteractionType)
        else:
            self.supported_interactions = supported_interactions
            
        # 形状参数验证
        self._validate_params()
        
        # 事件系统 - 延迟获取，确保可以在测试中被mock
        self.event_system = None
        
        # 交互处理回调
        self.on_interaction_callbacks: Dict[InteractionType, List[Callable[[dict], None]]] = {}
        
        self.logger.debug(f"创建交互区域: {zone_id}, 形状: {shape.name}")
    
    def _validate_params(self) -> None:
        """验证形状参数有效性"""
        try:
            if self.shape == ZoneShape.CIRCLE:
                # 圆形需要 center 和 radius
                assert 'center' in self.params and isinstance(self.params['center'], tuple)
                assert 'radius' in self.params and isinstance(self.params['radius'], (int, float))
                assert self.params['radius'] > 0
                
            elif self.shape == ZoneShape.RECTANGLE:
                # 矩形需要 top_left, width, height
                assert 'top_left' in self.params and isinstance(self.params['top_left'], tuple)
                assert 'width' in self.params and isinstance(self.params['width'], (int, float))
                assert 'height' in self.params and isinstance(self.params['height'], (int, float))
                assert self.params['width'] > 0 and self.params['height'] > 0
                
            elif self.shape == ZoneShape.POLYGON:
                # 多边形需要至少3个points
                assert 'points' in self.params and isinstance(self.params['points'], list)
                assert len(self.params['points']) >= 3
                for point in self.params['points']:
                    assert isinstance(point, tuple) and len(point) == 2
            else:
                raise ValueError(f"不支持的形状类型: {self.shape}")
        except AssertionError as e:
            self.logger.error(f"区域参数验证失败: {e}")
            raise ValueError(f"区域参数验证失败: {self.shape.name} 需要有效的参数")
    
    def contains_point(self, point: Point) -> bool:
        """检查点是否在区域内
        
        Args:
            point: 要检测的点坐标 (x, y)
            
        Returns:
            bool: 点是否在区域内
        """
        if not self.enabled:
            return False
            
        if self.shape == ZoneShape.CIRCLE:
            return self._point_in_circle(point)
        elif self.shape == ZoneShape.RECTANGLE:
            return self._point_in_rectangle(point)
        elif self.shape == ZoneShape.POLYGON:
            return self._point_in_polygon(point)
        return False
    
    def _point_in_circle(self, point: Point) -> bool:
        """检查点是否在圆形区域内"""
        center = self.params['center']
        radius = self.params['radius']
        
        # 计算点到圆心的距离
        distance = math.sqrt((point[0] - center[0]) ** 2 + (point[1] - center[1]) ** 2)
        return distance <= radius
    
    def _point_in_rectangle(self, point: Point) -> bool:
        """检查点是否在矩形区域内"""
        top_left = self.params['top_left']
        width = self.params['width']
        height = self.params['height']
        
        # 检查是否在矩形范围内
        return (top_left[0] <= point[0] <= top_left[0] + width and
                top_left[1] <= point[1] <= top_left[1] + height)
    
    def _point_in_polygon(self, point: Point) -> bool:
        """检查点是否在多边形区域内（射线法）"""
        points = self.params['points']
        n = len(points)
        inside = False
        
        x, y = point
        for i in range(n):
            j = (i - 1) % n
            xi, yi = points[i]
            xj, yj = points[j]
            
            # 检查点是否在多边形的边上
            if (xi == x and yi == y) or (xj == x and yj == y):
                return True
                
            # 检查点是否在多边形的边上
            if (yi == yj) and (yi == y) and (min(xi, xj) <= x <= max(xi, xj)):
                return True
            
            # 检查射线与多边形边的交点
            intersect = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi)
            if intersect:
                inside = not inside
                
        return inside
    
    def activate(self) -> bool:
        """激活区域（如鼠标悬停其上）
        
        Returns:
            bool: 激活状态是否改变
        """
        if not self.enabled:
            return False
            
        if not self.active:
            self.active = True
            self.logger.debug(f"区域已激活: {self.zone_id}")
            # 发布区域激活事件
            self._publish_zone_event("activated")
            return True
        return False
    
    def deactivate(self) -> bool:
        """停用区域
        
        Returns:
            bool: 停用状态是否改变
        """
        if self.active:
            self.active = False
            self.logger.debug(f"区域已停用: {self.zone_id}")
            # 发布区域停用事件
            self._publish_zone_event("deactivated")
            return True
        return False
    
    def enable(self) -> bool:
        """启用区域
        
        Returns:
            bool: 启用状态是否改变
        """
        if not self.enabled:
            self.enabled = True
            self.logger.debug(f"区域已启用: {self.zone_id}")
            return True
        return False
    
    def disable(self) -> bool:
        """禁用区域
        
        Returns:
            bool: 禁用状态是否改变
        """
        if self.enabled:
            self.enabled = False
            self.active = False
            self.logger.debug(f"区域已禁用: {self.zone_id}")
            return True
        return False
    
    def handle_interaction(self, interaction_type: InteractionType, data: Optional[Dict[str, Any]] = None) -> bool:
        """处理交互事件
        
        Args:
            interaction_type: 交互类型
            data: 交互相关数据
            
        Returns:
            bool: 是否成功处理
        """
        if not self.enabled:
            return False
            
        if interaction_type not in self.supported_interactions:
            self.logger.debug(f"区域 {self.zone_id} 不支持此交互类型: {interaction_type.name}")
            return False
            
        self.logger.debug(f"区域 {self.zone_id} 处理交互: {interaction_type.name}")
        
        # 调用注册的回调函数
        if interaction_type in self.on_interaction_callbacks:
            for callback in self.on_interaction_callbacks[interaction_type]:
                try:
                    callback(data or {})
                except Exception as e:
                    self.logger.error(f"交互回调异常: {e}", exc_info=True)
        
        # 发布交互事件
        self._publish_interaction_event(interaction_type, data)
        
        return True
    
    def register_interaction_callback(self, interaction_type: InteractionType, 
                                    callback: Callable[[Dict[str, Any]], None]) -> None:
        """注册交互回调函数
        
        Args:
            interaction_type: 交互类型
            callback: 回调函数，接收交互数据字典
        """
        if interaction_type not in self.on_interaction_callbacks:
            self.on_interaction_callbacks[interaction_type] = []
            
        if callback not in self.on_interaction_callbacks[interaction_type]:
            self.on_interaction_callbacks[interaction_type].append(callback)
            self.logger.debug(f"区域 {self.zone_id} 注册交互回调: {interaction_type.name}")
    
    def unregister_interaction_callback(self, interaction_type: InteractionType, 
                                       callback: Callable[[Dict[str, Any]], None]) -> bool:
        """注销交互回调函数
        
        Args:
            interaction_type: 交互类型
            callback: 回调函数
            
        Returns:
            bool: 是否成功注销
        """
        if (interaction_type in self.on_interaction_callbacks and 
            callback in self.on_interaction_callbacks[interaction_type]):
            self.on_interaction_callbacks[interaction_type].remove(callback)
            self.logger.debug(f"区域 {self.zone_id} 注销交互回调: {interaction_type.name}")
            return True
        return False
    
    def _get_event_system(self):
        """获取事件系统实例，延迟获取以支持测试中的mock"""
        if self.event_system is None:
            self.event_system = EventSystem.get_instance()
        return self.event_system
        
    def _publish_zone_event(self, action: str) -> None:
        """发布区域事件
        
        Args:
            action: 动作名称 (activated, deactivated)
        """
        event_system = self._get_event_system()
        if event_system:
            event_data = {
                'zone_id': self.zone_id,
                'shape': self.shape.name,
                'action': action,
                'timestamp': None  # 事件系统会自动添加时间戳
            }
            event_system.dispatch_event(
                EventType.USER_INTERACTION,
                sender=self,
                data=event_data
            )
    
    def _publish_interaction_event(self, interaction_type: InteractionType, 
                                  data: Optional[Dict[str, Any]] = None) -> None:
        """发布交互事件
        
        Args:
            interaction_type: 交互类型
            data: 交互数据
        """
        event_system = self._get_event_system()
        if event_system:
            event_data = {
                'zone_id': self.zone_id,
                'interaction_type': interaction_type.name,
                'zone_shape': self.shape.name,
                'timestamp': None  # 事件系统会自动添加时间戳
            }
            
            # 合并附加数据
            if data:
                event_data.update(data)
                
            event_system.dispatch_event(
                EventType.USER_INTERACTION,
                sender=self,
                data=event_data
            )


class InteractionZoneManager:
    """交互区域管理器
    
    管理多个交互区域，处理重叠区域的交互优先级
    """
    
    def __init__(self):
        """初始化交互区域管理器"""
        self.logger = logging.getLogger("Status.Interaction.InteractionZoneManager")
        self.zones: Dict[str, InteractionZone] = {}
        self.event_system = EventSystem.get_instance()
        
    def add_zone(self, zone: InteractionZone) -> bool:
        """添加交互区域
        
        Args:
            zone: 交互区域对象
            
        Returns:
            bool: 是否成功添加
        """
        if zone.zone_id in self.zones:
            self.logger.warning(f"区域ID已存在: {zone.zone_id}")
            return False
            
        self.zones[zone.zone_id] = zone
        self.logger.debug(f"添加区域: {zone.zone_id}")
        return True
    
    def remove_zone(self, zone_id: str) -> bool:
        """移除交互区域
        
        Args:
            zone_id: 区域ID
            
        Returns:
            bool: 是否成功移除
        """
        if zone_id in self.zones:
            del self.zones[zone_id]
            self.logger.debug(f"移除区域: {zone_id}")
            return True
        return False
    
    def get_zone(self, zone_id: str) -> Optional[InteractionZone]:
        """获取交互区域
        
        Args:
            zone_id: 区域ID
            
        Returns:
            Optional[InteractionZone]: 交互区域对象，如不存在则返回None
        """
        return self.zones.get(zone_id)
    
    def get_zones_at_point(self, point: Point) -> List[InteractionZone]:
        """获取包含指定点的所有区域
        
        Args:
            point: 点坐标 (x, y)
            
        Returns:
            List[InteractionZone]: 包含该点的区域列表
        """
        return [zone for zone in self.zones.values() 
                if zone.enabled and zone.contains_point(point)]
    
    def activate_zones_at_point(self, point: Point) -> List[str]:
        """激活包含指定点的所有区域
        
        Args:
            point: 点坐标 (x, y)
            
        Returns:
            List[str]: 被激活的区域ID列表
        """
        activated = []
        for zone in self.get_zones_at_point(point):
            if zone.activate():
                activated.append(zone.zone_id)
        return activated
    
    def deactivate_all_zones(self) -> List[str]:
        """停用所有激活的区域
        
        Returns:
            List[str]: 被停用的区域ID列表
        """
        deactivated = []
        for zone in self.zones.values():
            if zone.active and zone.deactivate():
                deactivated.append(zone.zone_id)
        return deactivated
    
    def handle_interaction(self, point: Point, interaction_type: InteractionType,
                          data: Optional[Dict[str, Any]] = None) -> List[str]:
        """处理指定点的交互
        
        Args:
            point: 交互点坐标 (x, y)
            interaction_type: 交互类型
            data: 交互数据
            
        Returns:
            List[str]: 处理交互的区域ID列表
        """
        handled = []
        for zone in self.get_zones_at_point(point):
            if zone.handle_interaction(interaction_type, data):
                handled.append(zone.zone_id)
        return handled
    
    def clear(self) -> None:
        """清空所有区域"""
        self.zones.clear()
        self.logger.debug("清空所有区域")
    
    def enable_all(self) -> None:
        """启用所有区域"""
        for zone in self.zones.values():
            zone.enable()
        self.logger.debug("启用所有区域")
    
    def disable_all(self) -> None:
        """禁用所有区域"""
        for zone in self.zones.values():
            zone.disable()
        self.logger.debug("禁用所有区域")
    
    # 便利方法：创建常用形状的区域
    def create_circle_zone(self, zone_id: str, center: Point, radius: float,
                         supported_interactions: Optional[Set[InteractionType]] = None,
                         enabled: bool = True) -> InteractionZone:
        """创建圆形交互区域
        
        Args:
            zone_id: 区域ID
            center: 圆心坐标 (x, y)
            radius: 半径
            supported_interactions: 支持的交互类型
            enabled: 是否启用
            
        Returns:
            InteractionZone: 创建的区域对象
        """
        params = {'center': center, 'radius': radius}
        zone = InteractionZone(zone_id, ZoneShape.CIRCLE, params, 
                             supported_interactions, enabled)
        self.add_zone(zone)
        return zone
    
    def create_rectangle_zone(self, zone_id: str, top_left: Point, width: float, height: float,
                            supported_interactions: Optional[Set[InteractionType]] = None,
                            enabled: bool = True) -> InteractionZone:
        """创建矩形交互区域
        
        Args:
            zone_id: 区域ID
            top_left: 左上角坐标 (x, y)
            width: 宽度
            height: 高度
            supported_interactions: 支持的交互类型
            enabled: 是否启用
            
        Returns:
            InteractionZone: 创建的区域对象
        """
        params = {'top_left': top_left, 'width': width, 'height': height}
        zone = InteractionZone(zone_id, ZoneShape.RECTANGLE, params, 
                             supported_interactions, enabled)
        self.add_zone(zone)
        return zone
    
    def create_polygon_zone(self, zone_id: str, points: List[Point],
                          supported_interactions: Optional[Set[InteractionType]] = None,
                          enabled: bool = True) -> InteractionZone:
        """创建多边形交互区域
        
        Args:
            zone_id: 区域ID
            points: 多边形顶点坐标列表
            supported_interactions: 支持的交互类型
            enabled: 是否启用
            
        Returns:
            InteractionZone: 创建的区域对象
        """
        params = {'points': points}
        zone = InteractionZone(zone_id, ZoneShape.POLYGON, params, 
                             supported_interactions, enabled)
        self.add_zone(zone)
        return zone 