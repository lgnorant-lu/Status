"""
---------------------------------------------------------------
File name:                  events.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                事件系统模块导出，兼容性包装器
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
                            2025/04/05: 添加InteractionEvent和InteractionEventType类;
----
"""

from enum import Enum, auto

# 从event_system.py导入所有内容
from status.core.event_system import EventType # 直接导入原始 EventType
from status.core.event_system import Event
from status.core.event_system import EventSystem as _EventSystem

# 交互事件类型枚举
class InteractionEventType(Enum):
    """交互事件类型枚举"""
    MOUSE_CLICK = auto()       # 鼠标点击
    MOUSE_MOVE = auto()        # 鼠标移动
    DRAG_START = auto()        # 拖拽开始
    DRAG_MOVE = auto()         # 拖拽移动
    DRAG_END = auto()          # 拖拽结束
    HOTKEY_PRESSED = auto()    # 热键按下
    MENU_ACTION = auto()       # 菜单动作
    TRAY_ACTIVATED = auto()    # 托盘图标激活
    WINDOW_SHOW = auto()       # 窗口显示
    WINDOW_HIDE = auto()       # 窗口隐藏
    WINDOW_RESIZE = auto()     # 窗口大小改变
    TOUCH_START = auto()       # 触摸开始
    TOUCH_MOVE = auto()        # 触摸移动
    TOUCH_END = auto()         # 触摸结束
    GESTURE = auto()           # 手势
    KEYBOARD_INPUT = auto()    # 键盘输入

# 交互事件类
class InteractionEvent(Event):
    """交互事件类，继承自Event"""
    
    def __init__(self, event_type: InteractionEventType, sender=None, data=None, position=None):
        """初始化交互事件
        
        Args:
            event_type: 交互事件类型
            sender: 事件发送者
            data: 事件数据
            position: 事件位置，通常是(x, y)坐标
        """
        # 将InteractionEventType映射为EventType.USER_INTERACTION
        super().__init__(EventType.USER_INTERACTION, sender, data)
        
        # 保存原始的交互事件类型
        self.interaction_type = event_type
        
        # 事件位置
        self.position = position
    
    def __str__(self) -> str:
        """字符串表示"""
        return (f"InteractionEvent(type={self.interaction_type.name}, "
                f"sender={self.sender}, data={self.data}, position={self.position})")

# 重命名EventSystem为EventManager
class EventManager(_EventSystem):
    """
    事件管理器
    
    为保持与现有代码兼容，将EventSystem重命名为EventManager
    所有功能与EventSystem相同
    """
    
    # 为保持与接口文档一致，添加get_instance方法
    @classmethod
    def get_instance(cls):
        """获取事件管理器的单例实例
        
        Returns:
            EventManager: 事件管理器的单例实例
        """
        return cls()
    
    def dispatch_interaction_event(self, interaction_type: InteractionEventType, 
                                 sender=None, data=None, position=None) -> None:
        """分发交互事件
        
        Args:
            interaction_type: 交互事件类型
            sender: 事件发送者
            data: 事件数据
            position: 事件位置
        """
        event = InteractionEvent(interaction_type, sender, data, position)
        self.dispatch(event)

# 新的系统统计信息更新事件
class SystemStatsUpdatedEvent(Event):
    """当系统统计信息 (CPU, 内存等) 更新时触发的事件。"""
    def __init__(self, stats_data: dict, sender=None):
        """初始化系统统计信息更新事件。

        Args:
            stats_data (dict): 包含统计信息的字典，例如 {'cpu': 50.5, 'memory': 75.2}。
            sender: 事件发送者，通常是 SystemMonitor。
        """
        super().__init__(EventType.SYSTEM_STATS_UPDATED, sender, stats_data)
        self.stats_data = stats_data

    def __str__(self) -> str:
        return (f"SystemStatsUpdatedEvent(sender={self.sender}, stats_data={self.stats_data})")

# 新的窗口位置变更事件
class WindowPositionChangedEvent(Event):
    """当窗口位置变更时触发的事件。"""
    def __init__(self, position, size, sender=None):
        """初始化窗口位置变更事件。

        Args:
            position: 窗口的新位置，通常是QPoint对象
            size: 窗口的大小，通常是QSize对象
            sender: 事件发送者，通常是MainPetWindow
        """
        data = {"position": position, "size": size}
        super().__init__(EventType.WINDOW_POSITION_CHANGED, sender, data)
        self.position = position
        self.size = size

    def __str__(self) -> str:
        return (f"WindowPositionChangedEvent(sender={self.sender}, position={self.position}, size={self.size})")

# 导出所有成员
__all__ = ['EventType', 'Event', 'EventManager', 'InteractionEventType', 'InteractionEvent', 'SystemStatsUpdatedEvent', 'WindowPositionChangedEvent'] 