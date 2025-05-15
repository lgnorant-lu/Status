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
                            2025/04/09: 添加系统状态更新事件;
                            2025/05/13: 添加全局访问函数;
                            2025/05/14: 添加获取应用实例函数;
                            2025/05/16: 将 EventManager 指向 LegacyEventManagerAdapter
----
"""

from enum import Enum, auto
import logging
from typing import Dict, Any, Optional, List, Tuple

from PySide6.QtCore import QPoint, QSize # Added import

# 从event_system.py导入所有内容 (旧事件系统的基础)
from status.core.event_system import EventType # 直接导入原始 EventType
from status.core.event_system import Event
# from status.core.event_system import EventSystem as _EventSystem # 不再直接使用 _EventSystem 作为基类

# 导入新的适配器
from status.events.legacy_adapter import LegacyEventManagerAdapter

# 创建模块级日志器
logger = logging.getLogger(__name__)

# 应用实例缓存
_app_instance = None


def get_app_instance():
    """获取应用程序主实例
    
    Returns:
        Any: 应用实例，如果无法获取则返回None
    """
    global _app_instance
    
    # 如果缓存中有实例，直接返回
    if _app_instance is not None:
        return _app_instance
    
    # 尝试从各种方式获取应用实例
    try:
        # 方法1：直接从main模块导入instance变量
        try:
            import status.main
            if hasattr(status.main, 'instance'):
                _app_instance = status.main.instance
                if _app_instance is not None:
                    logger.debug(f"从status.main模块获取到应用实例")
                    return _app_instance
        except (ImportError, AttributeError) as e:
            logger.debug(f"无法从status.main直接导入: {e}")
        
        # 方法2：遍历sys.modules查找instance变量
        import sys
        if 'status.main' in sys.modules and hasattr(sys.modules['status.main'], 'instance'):
            _app_instance = sys.modules['status.main'].instance
            if _app_instance is not None:
                logger.debug(f"从sys.modules获取到应用实例")
                return _app_instance
        
        # 方法3：直接获取StatusPet类并实例化（如果存在）
        if 'status.main' in sys.modules and hasattr(sys.modules['status.main'], 'StatusPet'):
            StatusPet = sys.modules['status.main'].StatusPet
            # 检查是否已有实例（通过单例模式或实例跟踪）
            if hasattr(StatusPet, 'instance') and StatusPet.instance is not None:
                _app_instance = StatusPet.instance
                logger.debug("从StatusPet类获取到现有实例")
                return _app_instance
        
        # 方法4：从其他位置查找实例
        for module_name, module in list(sys.modules.items()):
            if 'status.' in module_name and hasattr(module, 'instance') and module.instance is not None:
                _app_instance = module.instance
                logger.debug(f"从模块 {module_name} 获取到应用实例")
                return _app_instance
        
        # 如果上面的方法都失败，但这只是首次调用而不是错误
        if not hasattr(get_app_instance, '_logged_warning'):
            logger.info("首次尝试获取应用实例失败，这可能是正常的初始化序列")
            get_app_instance._logged_warning = True
        return None
    except Exception as e:
        logger.error(f"获取应用实例出错: {e}")
        return None

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

# EventManager 现在应该指向 LegacyEventManagerAdapter 的 get_instance 方法
# 以便 EventManager() 调用可以返回实例。
EventManager = LegacyEventManagerAdapter.get_instance

# 原来的 EventManager(_EventSystem) 子类及其兼容方法被移除，
# 因为适配器现在负责处理旧API的兼容性。

# 新的系统统计信息更新事件
class SystemStatsUpdatedEvent(Event):
    """系统状态更新事件"""
    
    def __init__(self, stats_data: Dict[str, Any], sender: Optional[object] = None):
        """初始化系统状态更新事件

        Args:
            stats_data: 系统状态数据字典
            sender: 事件发送者
        """
        super().__init__(EventType.SYSTEM_STATS_UPDATED, sender)
        self.stats_data = stats_data

    def __str__(self) -> str:
        return f"SystemStatsUpdatedEvent(sender={self.sender}, stats_count={len(self.stats_data)})"

# 窗口位置改变事件
class WindowPositionChangedEvent(Event):
    """窗口位置或大小改变事件"""
    position: Optional[QPoint] # Changed type hint
    size: Optional[QSize]     # Changed type hint

    def __init__(self, position: Optional[QPoint] = None, size: Optional[QSize] = None, window_id: Optional[str] = None, sender: Optional[object] = None):
        """初始化窗口位置/大小改变事件

        Args:
            position: 新的位置 (QPoint)，可选
            size: 新的大小 (QSize)，可选
            window_id: 关联的窗口ID (例如，对于多窗口应用)，可选
            sender: 事件发送者
        """
        # 确保 window_id 参数在 super 调用之前处理，或者如果 Event 基类不接受它，则不传递
        # Event class __init__ is (self, type, sender=None, data=None)
        # So, window_id should be stored as an attribute if needed, not passed to super.
        
        if position is None and size is None:
            raise ValueError("WindowPositionChangedEvent must have at least position or size.")
        
        super().__init__(EventType.WINDOW_POSITION_CHANGED, sender)
        self.position = position
        self.size = size
        self.window_id = window_id # Store window_id

    def __str__(self) -> str:
        return f"WindowPositionChangedEvent(pos={self.position}, size={self.size}, sender={self.sender})"

# 导出所有成员
__all__ = ['EventType', 'Event', 'EventManager', 'InteractionEventType', 'InteractionEvent', 'SystemStatsUpdatedEvent', 'WindowPositionChangedEvent'] 