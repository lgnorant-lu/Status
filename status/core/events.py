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
----
"""

from enum import Enum, auto
import logging
from typing import Dict, Any, Optional, List

# 从event_system.py导入所有内容
from status.core.event_system import EventType # 直接导入原始 EventType
from status.core.event_system import Event
from status.core.event_system import EventSystem as _EventSystem

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
    
    def publish(self, event_type, data=None, sender=None):
        """发布事件 (兼容API)
        
        Args:
            event_type: 事件类型，可以是EventType枚举值或字符串
            data: 事件数据
            sender: 事件发送者，默认为None
            
        Note:
            此方法提供与事件管理器统一API的兼容性
            内部调用dispatch_event方法
        """
        # 字符串事件类型目前不支持，仅保留API
        if isinstance(event_type, str):
            self.logger.warning(f"字符串事件类型 '{event_type}' 暂不支持，请使用EventType枚举")
            return
        
        # 使用标准的dispatch_event方法
        self.dispatch_event(event_type, sender, data)
    
    def subscribe(self, event_type, handler):
        """订阅事件 (兼容API)
        
        Args:
            event_type: 事件类型，可以是EventType枚举值或字符串
            handler: 事件处理函数
            
        Returns:
            handler: 返回原始处理函数
            
        Note:
            此方法提供与事件管理器统一API的兼容性
            内部调用register_handler方法
        """
        # 字符串事件类型目前不支持，仅保留API
        if isinstance(event_type, str):
            self.logger.warning(f"字符串事件类型 '{event_type}' 暂不支持，请使用EventType枚举")
            return handler
        
        # 使用标准的register_handler方法
        self.register_handler(event_type, handler)
        return handler
    
    def unsubscribe(self, event_type, handler):
        """取消订阅事件 (兼容API)
        
        Args:
            event_type: 事件类型，可以是EventType枚举值或字符串
            handler: 事件处理函数
            
        Returns:
            bool: 取消订阅是否成功
            
        Note:
            此方法提供与事件管理器统一API的兼容性
            内部调用unregister_handler方法
        """
        # 字符串事件类型目前不支持，仅保留API
        if isinstance(event_type, str):
            self.logger.warning(f"字符串事件类型 '{event_type}' 暂不支持，请使用EventType枚举")
            return False
        
        # 使用标准的unregister_handler方法
        return self.unregister_handler(event_type, handler)
    
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