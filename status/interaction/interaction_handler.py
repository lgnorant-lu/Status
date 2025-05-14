"""
---------------------------------------------------------------
File name:                  interaction_handler.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                交互处理器，处理桌宠的交互事件，连接交互区域和交互跟踪器
----------------------------------------------------------------

Changed history:            
                            2025/05/13: 初始创建;
----
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Set, Callable
import time

from PySide6.QtCore import QObject, Signal, Slot, QPoint, Qt, QTimer
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QWidget  # 添加QWidget导入

from status.core.component_base import ComponentBase
from status.interaction.interaction_zones import (
    InteractionZone, InteractionZoneManager, 
    InteractionType, Point, ZoneShape
)
from status.behavior.interaction_tracker import InteractionTracker, InteractionPattern
from status.core.event_system import EventSystem, EventType


class InteractionHandler(ComponentBase):
    """交互处理器
    
    负责处理用户与桌宠的交互事件，连接交互区域和交互跟踪器
    """
    
    def __init__(self, parent_window: Optional[QWidget] = None):  # 使用QWidget替代QObject
        """初始化交互处理器
        
        Args:
            parent_window: 父窗口对象，一般是MainPetWindow
        """
        super().__init__()
        
        self.logger = logging.getLogger("Status.Interaction.InteractionHandler")
        self.parent_window = parent_window
        
        # 创建区域管理器
        self.zone_manager = InteractionZoneManager()
        
        # 创建交互跟踪器
        self.tracker = InteractionTracker()
        
        # 交互状态
        self.is_dragging = False
        self.last_click_pos: Optional[QPoint] = None
        self.last_click_time = 0  # 用于检测双击
        self.double_click_interval = 500  # 双击间隔(毫秒)
        self.drag_zone: Optional[str] = None
        
        # 当前悬停区域ID
        self.current_hover_zone: Optional[str] = None
        
        # 事件系统
        self.event_system = EventSystem.get_instance()
        
        # 设置自动停用计时器
        self.hover_timer = QTimer()
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self._on_hover_timeout)
        self.hover_timeout = 1000  # 鼠标离开后1秒停用区域
        
        self.logger.info("交互处理器初始化完成")
    
    def _initialize(self) -> bool:
        """初始化组件
        
        Returns:
            bool: 初始化是否成功
        """
        # 注册事件监听
        self.event_system.register_handler(EventType.USER_INTERACTION, self._on_interaction_event)
        
        # 创建默认交互区域
        self._create_default_zones()
        
        return True
    
    def _shutdown(self) -> bool:
        """关闭组件
        
        Returns:
            bool: 关闭是否成功
        """
        # 注销事件监听
        self.event_system.unregister_handler(EventType.USER_INTERACTION, self._on_interaction_event)
        
        # 停止定时器
        if self.hover_timer.isActive():
            self.hover_timer.stop()
        
        # 保存交互数据
        if self.tracker:
            self.tracker.persist_interaction_data()
        
        return True
    
    def _create_default_zones(self) -> None:
        """创建默认交互区域"""
        if not self.zone_manager:
            self.logger.warning("区域管理器未初始化，无法创建默认区域")
            return
            
        try:
            # 获取窗口大小
            window_width = 200  # Default width
            window_height = 200 # Default height
            
            # 使用安全的方式获取窗口尺寸
            # 首先检查属性是否存在，然后再调用
            # 这样即使parent_window是None或不支持这些方法，也不会出错
            if self.parent_window:
                try:
                    window_width = self.parent_window.width()
                    window_height = self.parent_window.height()
                except (AttributeError, TypeError):
                    self.logger.warning("无法获取父窗口尺寸，使用默认值 (200x200)")
            
            # 创建头部区域（上方圆形）
            self.zone_manager.create_circle_zone(
                zone_id="head",
                center=(float(window_width // 2), float(window_height // 4)),  # 转换为float
                radius=float(window_width // 4),  # 转换为float
                supported_interactions={
                    InteractionType.CLICK,
                    InteractionType.DOUBLE_CLICK,
                    InteractionType.HOVER,
                    InteractionType.DRAG
                }
            )
            self.logger.debug(f"已创建头部交互区域: center=({window_width//2}, {window_height//4}), radius={window_width//4}")
            
            # 创建身体区域（中间矩形）
            self.zone_manager.create_rectangle_zone(
                zone_id="body",
                top_left=(float(window_width // 4), float(window_height // 4)),  # 转换为float
                width=float(window_width // 2),  # 转换为float
                height=float(window_height // 2),  # 转换为float
                supported_interactions={
                    InteractionType.CLICK,
                    InteractionType.DOUBLE_CLICK,
                    InteractionType.HOVER,
                    InteractionType.DRAG
                }
            )
            self.logger.debug(f"已创建身体交互区域: top_left=({window_width//4}, {window_height//4}), width={window_width//2}, height={window_height//2}")
            
            # 创建尾巴区域（下方多边形）
            # 显式转换为List[Point]类型
            tail_points: List[Point] = [
                (float(window_width // 2), float(3 * window_height // 4)),  # 上中
                (float(window_width // 3), float(7 * window_height // 8)),  # 左下
                (float(window_width // 2), float(window_height)),           # 下中
                (float(2 * window_width // 3), float(7 * window_height // 8)),  # 右下
            ]
            self.zone_manager.create_polygon_zone(
                zone_id="tail",
                points=tail_points,
                supported_interactions={
                    InteractionType.CLICK,
                    InteractionType.DOUBLE_CLICK,
                    InteractionType.HOVER
                }
            )
            self.logger.debug(f"已创建尾巴交互区域: points={tail_points}")
            
            # 注册交互回调，测试用
            for zone_id in ["head", "body", "tail"]:
                for interaction_type in [InteractionType.CLICK, InteractionType.HOVER, InteractionType.DOUBLE_CLICK]:
                    # 添加类型注解
                    self.register_zone_callback(
                        zone_id, 
                        interaction_type,
                        lambda data: self.logger.debug(f"交互: {zone_id} - {interaction_type.name}, data={data}")
                    )
            
            self.logger.info("已创建默认交互区域")
        except Exception as e:
            self.logger.error(f"创建默认交互区域失败: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
    
    def handle_mouse_event(self, event: QMouseEvent, event_type: str) -> bool:
        """处理鼠标事件
        
        Args:
            event: Qt鼠标事件
            event_type: 事件类型，可以是'press', 'release', 'move', 'doubleclick'
            
        Returns:
            bool: 是否已处理事件
        """
        # 获取鼠标位置(相对于窗口)
        pos = (event.position().x(), event.position().y())
        
        # 处理不同类型的鼠标事件
        if event_type == 'press':
            return self._handle_mouse_press(pos, event)
        elif event_type == 'release':
            return self._handle_mouse_release(pos, event)
        elif event_type == 'move':
            return self._handle_mouse_move(pos, event)
        elif event_type == 'doubleclick':
            return self._handle_mouse_double_click(pos, event)
        
        return False
    
    def _handle_mouse_press(self, pos: Point, event: QMouseEvent) -> bool:
        """处理鼠标按下事件
        
        Args:
            pos: 鼠标位置 (x, y)
            event: Qt鼠标事件
            
        Returns:
            bool: 是否已处理事件
        """
        # 获取点击位置的区域
        zones = self.zone_manager.get_zones_at_point(pos)
        
        # 如果点击到了区域
        if zones:
            # 记录点击位置和时间，用于拖拽和双击检测
            self.last_click_pos = QPoint(int(pos[0]), int(pos[1]))
            import time
            current_time = int(time.time() * 1000)  # 毫秒
            
            # 检查是否是右键点击
            is_right_click = event.button() == Qt.MouseButton.RightButton
            
            # 对每个区域处理点击
            for zone in zones:
                interaction_type = InteractionType.RIGHT_CLICK if is_right_click else InteractionType.CLICK
                
                # 如果区域支持该交互类型
                if interaction_type in zone.supported_interactions:
                    # 处理交互
                    data = {
                        'x': pos[0],
                        'y': pos[1],
                        'button': str(event.button()),
                        'zone_id': zone.zone_id,
                        'original_qt_event_type': 'press'
                    }
                    # self.tracker.track_interaction(interaction_type, zone.zone_id, data) # Tracker listens to event
                    self._publish_interaction_event(interaction_type, zone.zone_id, data)
                    
                    # 如果支持拖拽，标记开始拖拽
                    if event.button() == Qt.MouseButton.LeftButton and InteractionType.DRAG in zone.supported_interactions:
                        self.is_dragging = True
                        self.drag_zone = zone.zone_id
                        self.logger.debug(f"Dragging initiated in zone {zone.zone_id}")
                    
                    # 记录最近一次点击的时间，用于双击检测
                    self.last_click_time = current_time
                    
                    return True
        
        return False
    
    def _handle_mouse_release(self, pos: Point, event: QMouseEvent) -> bool:
        """处理鼠标释放事件
        
        Args:
            pos: 鼠标位置 (x, y)
            event: Qt鼠标事件
            
        Returns:
            bool: 是否已处理事件
        """
        released_on_zone = False
        was_dragging = self.is_dragging
        if self.is_dragging:
            self.logger.debug(f"Dragging finished. Was dragging in zone: {self.drag_zone}")
            self.is_dragging = False

        zones = self.zone_manager.get_zones_at_point(pos)
        if zones:
            for zone in zones:
                interaction_type = InteractionType.CLICK 
                if interaction_type in zone.supported_interactions:
                    released_on_zone = True
                    data = {
                        'x': pos[0],
                        'y': pos[1],
                        'button': str(event.button()),
                        'zone_id': zone.zone_id,
                        'original_qt_event_type': 'release' 
                    }
                    # self.tracker.track_interaction(interaction_type, zone.zone_id, data) # Tracker listens
                    self._publish_interaction_event(interaction_type, zone.zone_id, data)
        
        if was_dragging and not released_on_zone and not zones: 
             self.logger.debug("Drag ended by releasing outside any zone. Publishing DROP event.")
             self._publish_interaction_event(InteractionType.DROP, "no_zone_release", { 
                'x': pos[0], 'y': pos[1], 'button': str(event.button()), 
                'original_qt_event_type': 'release'
            })

        self.last_click_pos = None 
        return True
    
    def _handle_mouse_move(self, pos: Point, event: QMouseEvent) -> bool:
        """处理鼠标移动事件
        
        Args:
            pos: 鼠标位置 (x, y)
            event: Qt鼠标事件
            
        Returns:
            bool: 是否已处理事件
        """
        # self.logger.debug(f"Mouse move at {pos}") # DEBUG: 可选的高频日志

        # 如果正在拖拽，则处理拖拽逻辑
        if self.is_dragging and self.last_click_pos:
            # 触发拖拽事件
            # 如果没有定义拖拽区域，则使用默认的"body"区域或特定的拖拽区域ID
            drag_zone_id = self.drag_zone if self.drag_zone else "body"
            
            data = {
                'start_x': self.last_click_pos.x(),
                'start_y': self.last_click_pos.y(),
                'current_x': pos[0],
                'current_y': pos[1],
                'original_qt_event_type': 'move' # 添加原始事件类型
            }
            self._publish_interaction_event(InteractionType.DRAG, drag_zone_id, data)
            # self.logger.debug(f"Dragging in zone {drag_zone_id} from {self.last_click_pos} to {pos}")
            return True

        # 非拖拽状态下的鼠标移动，处理悬停逻辑
        zones_at_point = self.zone_manager.get_zones_at_point(pos)
        self.logger.debug(f"_handle_mouse_move: Zones at {pos}: {zones_at_point}") # 日志: 确认区域

        current_zone_ids: Set[str] = {zone.zone_id for zone in zones_at_point}
        
        # 检查是否进入新的悬停区域
        newly_hovered_zones = current_zone_ids - (set() if self.current_hover_zone is None else {self.current_hover_zone})
        # 检查是否离开之前的悬停区域
        left_hover_zone = self.current_hover_zone is not None and self.current_hover_zone not in current_zone_ids

        if newly_hovered_zones:
            # 假设我们一次只处理一个主要的悬停区域（例如列表中的第一个）
            # 或者可以迭代所有 newly_hovered_zones 如果需要支持多区域同时悬停事件
            new_hover_target_zone_id = list(newly_hovered_zones)[0]
            self.current_hover_zone = new_hover_target_zone_id
            
            # 发布 HOVER 事件
            hover_data = {'x': pos[0], 'y': pos[1], 'original_qt_event_type': 'move'}
            self._publish_interaction_event(InteractionType.HOVER, self.current_hover_zone, hover_data)
            self.logger.info(f"_handle_mouse_move: Published HOVER for zone {self.current_hover_zone}") # 日志: 确认HOVER发布
            
            # 如果之前有悬停计时器在运行，停止它，因为我们进入了新区域
            if self.hover_timer.isActive():
                self.hover_timer.stop()
            return True # 事件已处理

        elif left_hover_zone:
            self.logger.debug(f"_handle_mouse_move: Left hover zone {self.current_hover_zone}")
            # 之前悬停的区域不再悬停，可以启动计时器来最终清除悬停状态，或者发布HOVER_OUT事件
            # 目前的逻辑是：如果鼠标移出所有区域，由 hover_timer 超时处理（如果它启动了）
            # 或者如果进入了另一个区域，上面的 newly_hovered_zones 会处理
            # 此处可能需要一个明确的 HOVER_OUT 事件发布，如果业务逻辑需要
            # self._publish_interaction_event(InteractionType.HOVER_OUT, self.current_hover_zone, {'x': pos[0], 'y': pos[1]})
            self.current_hover_zone = None # 清除当前悬停区
            # 可以考虑启动一个短计时器，如果在短时间内没有进入新区域，则认为悬停结束
            # self.hover_timer.start(self.hover_timeout) # hover_timer用于更通用的"无活动"检测
            return True # 事件已处理
        
        # 如果鼠标在区域外移动，并且之前有悬停区域，现在离开了，也应清除 self.current_hover_zone
        if not current_zone_ids and self.current_hover_zone is not None:
            self.logger.debug(f"_handle_mouse_move: Mouse moved outside all zones, clearing previous hover zone {self.current_hover_zone}")
            self.current_hover_zone = None
            # 这里也可以考虑启动 hover_timer，如果希望在一段时间无交互后触发特定行为

        # 如果鼠标在区域内移动，但区域未变，则不需要操作
        # 如果鼠标在区域外移动，且之前也不在任何区域，也不需要操作

        return False # 事件未被拖拽或新的悬停事件处理
    
    def _handle_mouse_double_click(self, pos: Point, event: QMouseEvent) -> bool:
        """处理鼠标双击事件
        
        Args:
            pos: 鼠标位置 (x, y)
            event: Qt鼠标事件
            
        Returns:
            bool: 是否已处理事件
        """
        zones = self.zone_manager.get_zones_at_point(pos)
        if zones:
            for zone in zones:
                if InteractionType.DOUBLE_CLICK in zone.supported_interactions:
                    data = {
                        'x': pos[0],
                        'y': pos[1],
                        'button': str(event.button()),
                        'zone_id': zone.zone_id,
                        'original_qt_event_type': 'doubleclick'
                    }
                    # self.tracker.track_interaction(InteractionType.DOUBLE_CLICK, zone.zone_id, data) # Tracker listens
                    self._publish_interaction_event(InteractionType.DOUBLE_CLICK, zone.zone_id, data)
                    return True
        return False
    
    def _on_hover_timeout(self) -> None:
        """悬停超时处理"""
        if self.current_hover_zone:
            zone = self.zone_manager.get_zone(self.current_hover_zone)
            if zone:
                zone.deactivate()
            
            self.current_hover_zone = None
    
    def _on_interaction_event(self, event: Any) -> None:
        """处理交互事件
        
        Args:
            event: 交互事件
        """
        # 转发到交互跟踪器
        if self.tracker:
            self.tracker._on_user_interaction(event)
    
    def set_zone_enabled(self, zone_id: str, enabled: bool) -> bool:
        """设置区域是否启用
        
        Args:
            zone_id: 区域ID
            enabled: 是否启用
            
        Returns:
            bool: 操作是否成功
        """
        zone = self.zone_manager.get_zone(zone_id)
        if zone:
            if enabled:
                return zone.enable()
            else:
                return zone.disable()
        return False
    
    def get_interaction_pattern(self, zone_id: str) -> Optional[InteractionPattern]:
        """获取区域的交互模式
        
        Args:
            zone_id: 区域ID
            
        Returns:
            Optional[InteractionPattern]: 交互模式，如不存在则返回None
        """
        if not self.tracker:
            return None
            
        # 检查是否有任何类型的交互
        interaction_types = self.tracker.get_all_interaction_types()
        for interaction_type in interaction_types:
            zones = self.tracker.get_all_zones(interaction_type)
            if zone_id in zones:
                return self.tracker.get_interaction_pattern(interaction_type, zone_id)
        
        return None
    
    def update_zone_position(self, zone_id: str, new_position: Any) -> bool:
        """更新区域位置
        
        Args:
            zone_id: 区域ID
            new_position: 新位置，格式根据区域类型不同:
                          - 圆形: (center_x, center_y)
                          - 矩形: (top_left_x, top_left_y)
                          - 多边形: [(x1, y1), (x2, y2), ...]
            
        Returns:
            bool: 更新是否成功
        """
        zone = self.zone_manager.get_zone(zone_id)
        if not zone:
            return False
        
        try:
            if zone.shape == ZoneShape.CIRCLE:
                zone.params['center'] = (new_position[0], new_position[1])
                return True
            elif zone.shape == ZoneShape.RECTANGLE:
                zone.params['top_left'] = (new_position[0], new_position[1])
                return True
            elif zone.shape == ZoneShape.POLYGON:
                zone.params['points'] = new_position
                return True
            return False
        except (IndexError, KeyError, TypeError):
            self.logger.error(f"更新区域位置失败: {zone_id}", exc_info=True)
            return False
    
    def register_zone_callback(self, zone_id: str, interaction_type: InteractionType, 
                             callback: Callable[[Dict[str, Any]], None]) -> bool:
        """注册区域交互回调
        
        Args:
            zone_id: 区域ID
            interaction_type: 交互类型
            callback: 回调函数，接收交互数据字典
            
        Returns:
            bool: 是否成功注册
        """
        zone = self.zone_manager.get_zone(zone_id)
        if zone:
            zone.register_interaction_callback(interaction_type, callback)
            return True
        return False
    
    def get_frequentcy_interactions(self, zone_id: str) -> List[Tuple[str, float]]:
        """获取区域的交互频率信息
        
        Args:
            zone_id: 区域ID
            
        Returns:
            List[Tuple[str, float]]: 交互类型和频率的列表，按频率降序排序
        """
        if not self.tracker:
            return []
            
        result = []
        interaction_types = self.tracker.get_all_interaction_types()
        
        for interaction_type in interaction_types:
            zones = self.tracker.get_all_zones(interaction_type)
            if zone_id in zones:
                freq = self.tracker.get_interaction_frequency(interaction_type, zone_id)
                result.append((interaction_type, freq))
        
        # 按频率降序排序
        result.sort(key=lambda x: x[1], reverse=True)
        return result
    
    def _publish_interaction_event(self, interaction_type: InteractionType, zone_id: str, data: Dict[str, Any]) -> None:
        """发布交互事件到事件系统
        
        Args:
            interaction_type: 交互类型
            zone_id: 区域ID
            data: 交互数据
        """
        if self.event_system:
            event_data = {
                'interaction_type': interaction_type.name,
                'zone_id': zone_id,
                'data': data,
                'timestamp': time.time()
            }
            
            self.event_system.dispatch_event(
                EventType.USER_INTERACTION,
                sender=self,
                data=event_data
            )
            
            self.logger.debug(f"已发布交互事件: {interaction_type.name} 区域: {zone_id}") 