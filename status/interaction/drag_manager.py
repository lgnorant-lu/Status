"""
---------------------------------------------------------------
File name:                  drag_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                桌宠拖拽管理模块
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
                            2025/04/04: 添加拖拽移动事件节流;
----
"""

import logging
from PySide6.QtCore import QObject, QRect, pyqtSignal
from status.core.events import EventManager
from status.interaction.interaction_event import InteractionEvent, InteractionEventType
from status.interaction.event_throttler import TimeThrottler

# 配置日志
logger = logging.getLogger(__name__)

# 拖拽移动事件节流间隔（毫秒）
DRAG_MOVE_THROTTLE_MS = 30

class DragManager(QObject):
    """拖拽管理器
    
    管理桌宠窗口的拖拽功能，允许用户通过鼠标拖拽移动窗口。
    """
    
    # 定义信号
    drag_start_signal = pyqtSignal(int, int)  # 拖拽开始信号
    drag_move_signal = pyqtSignal(int, int)   # 拖拽移动信号
    drag_end_signal = pyqtSignal(int, int)    # 拖拽结束信号
    
    def __init__(self, window):
        """初始化拖拽管理器
        
        Args:
            window: 桌宠主窗口实例
        """
        super().__init__()
        self.window = window
        self.event_manager = EventManager.get_instance()
        
        # 拖拽状态
        self.is_dragging = False
        self.drag_start_pos = None
        self.drag_start_window_pos = None
        
        # 可拖拽区域
        self.draggable_regions = []
        self.whole_window_draggable = True  # 默认整个窗口可拖拽
        
        # 创建拖拽移动事件节流器
        self.drag_move_throttler = TimeThrottler(
            DRAG_MOVE_THROTTLE_MS,
            {InteractionEventType.DRAG_MOVE},
            name="DragMoveThrottler"
        )
        
        logger.info("DragManager initialized")
    
    def add_draggable_region(self, rect, region_id=None):
        """添加可拖拽区域
        
        Args:
            rect (QRect): 可拖拽的矩形区域
            region_id (str, optional): 区域ID. 默认为None
            
        Returns:
            str: 区域ID
        """
        self.draggable_regions.append((rect, region_id))
        logger.debug(f"Added draggable region {region_id} at {rect}")
        return region_id
    
    def remove_draggable_region(self, region_id):
        """移除可拖拽区域
        
        Args:
            region_id (str): 要移除的区域ID
            
        Returns:
            bool: 是否成功移除
        """
        for i, (_, rid) in enumerate(self.draggable_regions):
            if rid == region_id:
                self.draggable_regions.pop(i)
                logger.debug(f"Removed draggable region {region_id}")
                return True
        logger.warning(f"Draggable region {region_id} not found")
        return False
    
    def clear_draggable_regions(self):
        """清空所有可拖拽区域"""
        self.draggable_regions.clear()
        logger.debug("Cleared all draggable regions")
    
    def set_whole_window_draggable(self, draggable):
        """设置整个窗口是否可拖拽
        
        Args:
            draggable (bool): 是否可拖拽
        """
        self.whole_window_draggable = draggable
        logger.debug(f"Set whole window draggable: {draggable}")
    
    def set_drag_throttle_interval(self, interval_ms):
        """设置拖拽移动事件节流间隔
        
        Args:
            interval_ms (int): 节流间隔（毫秒）
        """
        # 创建新的节流器替换旧的
        self.drag_move_throttler = TimeThrottler(
            interval_ms,
            {InteractionEventType.DRAG_MOVE},
            name="DragMoveThrottler"
        )
        logger.debug(f"Drag move throttle interval set to {interval_ms}ms")
    
    def _can_start_drag(self, x, y):
        """检查是否可以开始拖拽
        
        Args:
            x (int): 鼠标x坐标
            y (int): 鼠标y坐标
            
        Returns:
            bool: 是否可以开始拖拽
        """
        # 如果整个窗口可拖拽，直接返回True
        if self.whole_window_draggable:
            return True
        
        # 检查是否在任一可拖拽区域内
        for rect, _ in self.draggable_regions:
            if rect.contains(x, y):
                return True
        
        return False
    
    def start_drag(self, x, y):
        """开始拖拽
        
        Args:
            x (int): 鼠标x坐标
            y (int): 鼠标y坐标
            
        Returns:
            bool: 拖拽是否成功开始
        """
        if not self._can_start_drag(x, y):
            logger.debug(f"Cannot start drag at ({x}, {y})")
            return False
        
        # 记录起始位置
        self.is_dragging = True
        self.drag_start_pos = (x, y)
        self.drag_start_window_pos = self.window.pos()
        
        # 发出拖拽开始信号
        self.drag_start_signal.emit(x, y)
        logger.debug(f"Started dragging at ({x}, {y})")
        return True
    
    def update_drag(self, x, y):
        """更新拖拽位置
        
        Args:
            x (int): 当前鼠标x坐标
            y (int): 当前鼠标y坐标
            
        Returns:
            bool: 更新是否成功
        """
        if not self.is_dragging:
            return False
        
        # 计算偏移量
        dx = x - self.drag_start_pos[0]
        dy = y - self.drag_start_pos[1]
        
        # 移动窗口
        new_pos = self.drag_start_window_pos.x() + dx, self.drag_start_window_pos.y() + dy
        self.window.move(new_pos[0], new_pos[1])
        
        # 发出拖拽移动信号
        self.drag_move_signal.emit(x, y)
        
        # 创建拖拽移动事件
        move_event = InteractionEvent(
            event_type=InteractionEventType.DRAG_MOVE,
            data={"position": (x, y), "offset": (dx, dy)}
        )
        
        # 应用节流器，决定是否发送事件
        if self.drag_move_throttler.throttle(move_event):
            self.event_manager.emit("interaction", move_event)
        
        return True
    
    def end_drag(self, x, y):
        """结束拖拽
        
        Args:
            x (int): 鼠标松开时的x坐标
            y (int): 鼠标松开时的y坐标
            
        Returns:
            bool: 结束是否成功
        """
        if not self.is_dragging:
            return False
        
        # 重置拖拽状态
        self.is_dragging = False
        self.drag_start_pos = None
        
        # 发出拖拽结束信号
        self.drag_end_signal.emit(x, y)
        logger.debug(f"Ended dragging at ({x}, {y})")
        return True
    
    def handle_event(self, event):
        """处理交互事件
        
        处理从交互管理器传来的事件。
        
        Args:
            event: 交互事件
        """
        # 目前没有需要特殊处理的事件
        # 此方法留作扩展用
        pass
    
    def shutdown(self):
        """关闭拖拽管理器
        
        清理资源，结束拖拽操作。
        
        Returns:
            bool: 关闭是否成功
        """
        # 如果有正在进行的拖拽，立即结束
        if self.is_dragging:
            # 使用最后位置结束拖拽
            self.end_drag(0, 0)
        
        # 清空可拖拽区域
        self.draggable_regions.clear()
        logger.info("DragManager shut down")
        return True 