"""
---------------------------------------------------------------
File name:                  mouse_interaction.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                桌宠鼠标交互处理模块
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
                            2025/04/04: 添加鼠标移动事件节流;
----
"""

import logging
from PyQt6.QtCore import QObject, QRect, pyqtSignal, Qt
from PyQt6.QtGui import QMouseEvent
from status.core.events import EventManager
from status.interaction.interaction_event import InteractionEvent, InteractionEventType
from status.interaction.event_throttler import TimeThrottler

# 配置日志
logger = logging.getLogger(__name__)

# 鼠标移动事件节流间隔（毫秒）
MOUSE_MOVE_THROTTLE_MS = 50

class ClickableRegion:
    """可点击区域
    
    定义一个矩形区域，当鼠标点击该区域时，会触发指定的回调函数。
    """
    
    def __init__(self, rect, callback, region_id=None, z_index=0):
        """初始化可点击区域
        
        Args:
            rect (QRect): 区域的矩形范围
            callback (function): 点击时的回调函数
            region_id (str, optional): 区域的唯一标识符. 默认为None
            z_index (int, optional): 区域的层叠顺序. 默认为0
        """
        self.rect = rect
        self.callback = callback
        self.region_id = region_id
        self.z_index = z_index  # 用于确定重叠区域的优先级
        
    def contains(self, x, y):
        """检查点(x, y)是否在区域内
        
        Args:
            x (int): 点的x坐标
            y (int): 点的y坐标
            
        Returns:
            bool: 点是否在区域内
        """
        return self.rect.contains(x, y)
    
    def handle_click(self, x, y, button):
        """处理点击事件
        
        Args:
            x (int): 点击的x坐标
            y (int): 点击的y坐标
            button (str): 点击的按钮
            
        Returns:
            bool: 处理是否成功
        """
        try:
            self.callback(x, y, button, self.region_id)
            return True
        except Exception as e:
            logger.error(f"Error handling click in region {self.region_id}: {str(e)}")
            return False


class MouseInteraction(QObject):
    """鼠标交互处理类
    
    处理与桌宠的鼠标交互，包括点击、悬停、拖拽等。
    """
    
    # 定义信号
    # 这些信号会在特定鼠标事件发生时发出
    click_signal = pyqtSignal(int, int, str)
    double_click_signal = pyqtSignal(int, int, str)
    right_click_signal = pyqtSignal(int, int)
    hover_signal = pyqtSignal(int, int)
    enter_signal = pyqtSignal(int, int)
    leave_signal = pyqtSignal(int, int)
    
    def __init__(self, window):
        """初始化鼠标交互处理类
        
        Args:
            window: 桌宠的主窗口
        """
        super().__init__()
        self.window = window
        self.event_manager = EventManager.get_instance()
        
        # 可点击区域列表
        self.clickable_regions = []
        
        # 拖拽相关
        self.drag_manager = None
        self.is_dragging = False
        
        # 鼠标跟踪状态
        self.mouse_inside = False
        self.last_position = None
        
        # 创建鼠标移动事件节流器
        self.mouse_move_throttler = TimeThrottler(
            MOUSE_MOVE_THROTTLE_MS,
            {InteractionEventType.MOUSE_MOVE},
            name="MouseMoveThrottler"
        )
        
        # 设置窗口属性
        if window:
            window.setMouseTracking(True)
            
        logger.info("MouseInteraction initialized")
    
    def register_clickable_region(self, rect, callback, region_id=None, z_index=0):
        """注册可点击区域
        
        Args:
            rect (QRect): 区域的矩形范围
            callback (function): 点击时的回调函数
            region_id (str, optional): 区域的唯一标识符. 默认为None
            z_index (int, optional): 区域的层叠顺序. 默认为0
            
        Returns:
            str: 区域的唯一标识符
        """
        region = ClickableRegion(rect, callback, region_id, z_index)
        self.clickable_regions.append(region)
        logger.debug(f"Registered clickable region {region_id} at {rect}")
        return region_id
    
    def unregister_clickable_region(self, region_id):
        """注销可点击区域
        
        Args:
            region_id (str): 区域的唯一标识符
            
        Returns:
            bool: 注销是否成功
        """
        for i, region in enumerate(self.clickable_regions):
            if region.region_id == region_id:
                self.clickable_regions.pop(i)
                logger.debug(f"Unregistered clickable region {region_id}")
                return True
        logger.warning(f"Clickable region {region_id} not found")
        return False
    
    def register_drag_manager(self, drag_manager):
        """注册拖拽管理器
        
        Args:
            drag_manager: 拖拽管理器实例
        """
        self.drag_manager = drag_manager
        logger.debug("Drag manager registered")
    
    def set_move_throttle_interval(self, interval_ms):
        """设置鼠标移动事件节流间隔
        
        Args:
            interval_ms (int): 节流间隔（毫秒）
        """
        # 创建新的节流器替换旧的
        self.mouse_move_throttler = TimeThrottler(
            interval_ms,
            {InteractionEventType.MOUSE_MOVE},
            name="MouseMoveThrottler"
        )
        logger.debug(f"Mouse move throttle interval set to {interval_ms}ms")
    
    def eventFilter(self, obj, event):
        """Qt事件过滤器
        
        过滤并处理所有与鼠标相关的事件。
        
        Args:
            obj: 事件的对象
            event: 事件
            
        Returns:
            bool: 事件是否已处理
        """
        # 只处理与鼠标相关的事件
        if isinstance(event, QMouseEvent):
            # 获取鼠标坐标
            x, y = event.x(), event.y()
            
            # 检查事件类型
            if event.type() == QMouseEvent.MouseButtonPress:
                return self.handle_mouse_press(x, y, event)
                
            elif event.type() == QMouseEvent.MouseButtonRelease:
                return self.handle_mouse_release(x, y, event)
                
            elif event.type() == QMouseEvent.MouseButtonDblClick:
                return self.handle_mouse_double_click(x, y, event)
                
            elif event.type() == QMouseEvent.MouseMove:
                return self.handle_mouse_move(x, y, event)
                
            elif event.type() == QMouseEvent.Enter:
                return self.handle_mouse_enter(x, y, event)
                
            elif event.type() == QMouseEvent.Leave:
                return self.handle_mouse_leave(x, y, event)
        
        # 不处理其他类型的事件
        return super().eventFilter(obj, event)
    
    def handle_mouse_press(self, x, y, event):
        """处理鼠标按下事件
        
        Args:
            x (int): 鼠标x坐标
            y (int): 鼠标y坐标
            event: 鼠标事件
            
        Returns:
            bool: 事件是否已处理
        """
        button_type = ""
        event_type = InteractionEventType.MOUSE_PRESS
        
        # 右键点击
        if event.button() == Qt.RightButton:
            self.right_click_signal.emit(x, y)
            button_type = "right"
            event_type = InteractionEventType.MOUSE_RIGHT_CLICK
        
        # 左键点击 - 可能是拖拽开始
        elif event.button() == Qt.LeftButton:
            button_type = "left"
            
            # 检查是否可以开始拖拽
            if self.drag_manager and self.drag_manager._can_start_drag(x, y):
                self.is_dragging = True
                self.drag_manager.start_drag(x, y)
                # 特殊事件类型，不需要发送普通的点击事件
                ev = InteractionEvent(
                    event_type=InteractionEventType.DRAG_START,
                    data={"position": (x, y), "button": button_type}
                )
                self.event_manager.emit("interaction", ev)
                return True
            
            # 检查是否点击了某个可点击区域
            clicked = self._find_clicked_region(x, y)
            if clicked:
                clicked.handle_click(x, y, button_type)
                
            self.click_signal.emit(x, y, button_type)
            event_type = InteractionEventType.MOUSE_CLICK
        
        # 中键点击
        elif event.button() == Qt.MiddleButton:
            button_type = "middle"
            self.click_signal.emit(x, y, button_type)
        
        # 创建并发送事件
        ev = InteractionEvent(
            event_type=event_type,
            data={"position": (x, y), "button": button_type}
        )
        self.event_manager.emit("interaction", ev)
        return True
    
    def handle_mouse_release(self, x, y, event):
        """处理鼠标释放事件
        
        Args:
            x (int): 鼠标x坐标
            y (int): 鼠标y坐标
            event: 鼠标事件
            
        Returns:
            bool: 事件是否已处理
        """
        button_type = ""
        
        # 右键释放
        if event.button() == Qt.RightButton:
            button_type = "right"
        
        # 左键释放 - 可能是拖拽结束
        elif event.button() == Qt.LeftButton:
            button_type = "left"
            
            # 如果正在拖拽，则结束拖拽
            if self.is_dragging and self.drag_manager:
                self.is_dragging = False
                self.drag_manager.end_drag(x, y)
                # 创建并发送拖拽结束事件
                ev = InteractionEvent(
                    event_type=InteractionEventType.DRAG_END,
                    data={"position": (x, y), "button": button_type}
                )
                self.event_manager.emit("interaction", ev)
                return True
        
        # 中键释放
        elif event.button() == Qt.MiddleButton:
            button_type = "middle"
        
        # 创建并发送鼠标释放事件
        ev = InteractionEvent(
            event_type=InteractionEventType.MOUSE_RELEASE,
            data={"position": (x, y), "button": button_type}
        )
        self.event_manager.emit("interaction", ev)
        return True
    
    def handle_mouse_double_click(self, x, y, event):
        """处理鼠标双击事件
        
        Args:
            x (int): 鼠标x坐标
            y (int): 鼠标y坐标
            event: 鼠标事件
            
        Returns:
            bool: 事件是否已处理
        """
        button_type = ""
        
        # 右键双击
        if event.button() == Qt.RightButton:
            button_type = "right"
        
        # 左键双击
        elif event.button() == Qt.LeftButton:
            button_type = "left"
            
            # 检查是否双击了某个可点击区域
            clicked = self._find_clicked_region(x, y)
            if clicked:
                clicked.handle_click(x, y, button_type + "_double")
        
        # 中键双击
        elif event.button() == Qt.MiddleButton:
            button_type = "middle"
        
        self.double_click_signal.emit(x, y, button_type)
        
        # 创建并发送鼠标双击事件
        ev = InteractionEvent(
            event_type=InteractionEventType.MOUSE_DOUBLE_CLICK,
            data={"position": (x, y), "button": button_type}
        )
        self.event_manager.emit("interaction", ev)
        return True
    
    def handle_mouse_move(self, x, y, event):
        """处理鼠标移动事件
        
        Args:
            x (int): 鼠标x坐标
            y (int): 鼠标y坐标
            event: 鼠标事件
            
        Returns:
            bool: 事件是否已处理
        """
        # 更新最后位置
        self.last_position = (x, y)
        
        # 如果正在拖拽，则更新拖拽位置
        if self.is_dragging and self.drag_manager:
            self.drag_manager.update_drag(x, y)
            # 创建并发送拖拽移动事件
            ev = InteractionEvent(
                event_type=InteractionEventType.DRAG_MOVE,
                data={"position": (x, y)}
            )
            self.event_manager.emit("interaction", ev)
            return True
        
        # 发出悬停信号
        self.hover_signal.emit(x, y)
        
        # 创建鼠标移动事件
        move_event = InteractionEvent(
            event_type=InteractionEventType.MOUSE_MOVE,
            data={"position": (x, y)}
        )
        
        # 应用节流器，决定是否发送事件
        if self.mouse_move_throttler.throttle(move_event):
            self.event_manager.emit("interaction", move_event)
        
        return False  # 返回False以允许其他处理器也处理此事件
    
    def handle_mouse_enter(self, x, y, event):
        """处理鼠标进入事件
        
        Args:
            x (int): 鼠标x坐标
            y (int): 鼠标y坐标
            event: 鼠标事件
            
        Returns:
            bool: 事件是否已处理
        """
        self.mouse_inside = True
        self.last_position = (x, y)
        self.enter_signal.emit(x, y)
        
        # 创建并发送鼠标进入事件
        ev = InteractionEvent(
            event_type=InteractionEventType.MOUSE_ENTER,
            data={"position": (x, y)}
        )
        self.event_manager.emit("interaction", ev)
        return True
    
    def handle_mouse_leave(self, x, y, event):
        """处理鼠标离开事件
        
        Args:
            x (int): 鼠标x坐标
            y (int): 鼠标y坐标
            event: 鼠标事件
            
        Returns:
            bool: 事件是否已处理
        """
        self.mouse_inside = False
        self.last_position = None
        self.leave_signal.emit(x, y)
        
        # 如果正在拖拽，则结束拖拽
        if self.is_dragging and self.drag_manager:
            self.is_dragging = False
            self.drag_manager.end_drag(x, y)
        
        # 创建并发送鼠标离开事件
        ev = InteractionEvent(
            event_type=InteractionEventType.MOUSE_LEAVE,
            data={"position": (x, y)}
        )
        self.event_manager.emit("interaction", ev)
        return True
    
    def _find_clicked_region(self, x, y):
        """查找点击的区域
        
        查找包含点(x, y)的所有可点击区域中z_index最高的一个。
        
        Args:
            x (int): 点的x坐标
            y (int): 点的y坐标
            
        Returns:
            ClickableRegion: 找到的区域，如果没有找到则返回None
        """
        # 找到所有包含点(x, y)的区域
        contained_regions = [r for r in self.clickable_regions if r.contains(x, y)]
        
        # 如果没有找到区域，则返回None
        if not contained_regions:
            return None
        
        # 返回z_index最高的区域
        return max(contained_regions, key=lambda r: r.z_index)
    
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
        """关闭鼠标交互处理
        
        清理资源，移除事件过滤器。
        
        Returns:
            bool: 关闭是否成功
        """
        if self.window:
            self.window.removeEventFilter(self)
        
        self.clickable_regions.clear()
        logger.info("MouseInteraction shut down")
        return True 