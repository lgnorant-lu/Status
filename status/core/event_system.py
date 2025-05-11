"""
---------------------------------------------------------------
File name:                  event_system.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                事件系统，实现模块间事件通知和处理
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
                            2025/04/04: 添加系统监控相关事件类型;
----
"""

import logging
from typing import Dict, List, Any, Callable, Optional
from enum import Enum, auto

class EventType(Enum):
    """事件类型枚举"""
    SYSTEM_STATUS_UPDATE = auto()  # 系统状态更新
    SYSTEM_MONITOR_STATE = auto()  # 系统监控器状态变更
    SYSTEM_ALERT = auto()          # 系统告警
    SCENE_CHANGE = auto()          # 场景切换
    USER_INTERACTION = auto()      # 用户交互
    RESOURCE_STATUS = auto()       # 资源状态
    CONFIG_CHANGE = auto()         # 配置变更
    APPLICATION_START = auto()     # 应用启动
    APPLICATION_EXIT = auto()      # 应用退出
    RENDER_FRAME = auto()          # 渲染帧
    TIMER_TICK = auto()            # 定时器滴答
    ERROR = auto()                 # 错误事件

class Event:
    """事件基类"""
    
    def __init__(self, event_type: EventType, sender: Any = None, data: Any = None):
        """初始化事件
        
        Args:
            event_type: 事件类型
            sender: 事件发送者
            data: 事件数据
        """
        self.type = event_type
        self.sender = sender
        self.data = data
        self.handled = False
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"Event(type={self.type.name}, sender={self.sender}, data={self.data})"

# 事件处理器类型: 接收事件对象，无返回值
EventHandler = Callable[[Event], None]

class EventSystem:
    """事件系统，实现观察者模式进行事件分发"""
    
    _instance = None  # 单例实例
    
    def __new__(cls, *args, **kwargs):
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super(EventSystem, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        """获取单例实例
        
        Returns:
            EventSystem: 事件系统单例
        """
        if cls._instance is None:
            cls._instance = EventSystem()
        return cls._instance
    
    def __init__(self):
        """初始化事件系统"""
        # 只在首次创建时初始化
        if not hasattr(self, 'initialized'):
            self.logger = logging.getLogger("Status.Core.EventSystem")
            self.handlers = {}  # 类型 -> 处理器列表的映射
            self.initialized = True
            self.logger.info("事件系统初始化")
    
    def register_handler(self, event_type: EventType, handler: EventHandler) -> None:
        """注册事件处理器
        
        Args:
            event_type: 事件类型
            handler: 事件处理函数
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        if handler not in self.handlers[event_type]:
            self.handlers[event_type].append(handler)
            self.logger.debug(f"事件处理器已注册: {event_type.name}")
        else:
            self.logger.warning(f"事件处理器重复注册: {event_type.name}")
    
    def unregister_handler(self, event_type: EventType, handler: EventHandler) -> bool:
        """注销事件处理器
        
        Args:
            event_type: 事件类型
            handler: 事件处理函数
            
        Returns:
            bool: 是否成功注销
        """
        if event_type not in self.handlers:
            self.logger.warning(f"尝试注销不存在的事件类型: {event_type.name}")
            return False
        
        if handler not in self.handlers[event_type]:
            self.logger.warning(f"尝试注销未注册的处理器: {event_type.name}")
            return False
        
        self.handlers[event_type].remove(handler)
        self.logger.debug(f"事件处理器已注销: {event_type.name}")
        return True
    
    def dispatch(self, event: Event) -> None:
        """分发事件到所有注册的处理器
        
        Args:
            event: 要分发的事件
        """
        if event.type not in self.handlers:
            self.logger.debug(f"没有处理器注册事件类型: {event.type.name}")
            return
        
        self.logger.debug(f"分发事件: {event}")
        
        # 复制处理器列表，避免处理过程中列表被修改
        handlers = self.handlers[event.type].copy()
        
        for handler in handlers:
            try:
                handler(event)
                if event.handled:
                    # 如果事件被标记为已处理，停止继续分发
                    self.logger.debug(f"事件被标记为已处理，停止分发: {event}")
                    break
            except Exception as e:
                self.logger.error(f"事件处理器异常: {str(e)}", exc_info=True)
    
    def dispatch_event(self, event_type: EventType, sender: Any = None, data: Any = None) -> None:
        """创建并分发事件的便捷方法
        
        Args:
            event_type: 事件类型
            sender: 事件发送者
            data: 事件数据
        """
        event = Event(event_type, sender, data)
        self.dispatch(event)
    
    def get_handlers_count(self, event_type: Optional[EventType] = None) -> int:
        """获取已注册的处理器数量
        
        Args:
            event_type: 可选的事件类型过滤器
            
        Returns:
            int: 处理器数量
        """
        if event_type is None:
            # 所有处理器总数
            return sum(len(handlers) for handlers in self.handlers.values())
        elif event_type in self.handlers:
            # 特定类型的处理器数量
            return len(self.handlers[event_type])
        else:
            return 0
    
    def clear_handlers(self, event_type: Optional[EventType] = None) -> None:
        """清除事件处理器
        
        Args:
            event_type: 可选的事件类型，如果为None则清除所有处理器
        """
        if event_type is None:
            # 清除所有处理器
            self.handlers.clear()
            self.logger.info("所有事件处理器已清除")
        elif event_type in self.handlers:
            # 清除特定类型的处理器
            self.handlers[event_type].clear()
            self.logger.info(f"事件类型的处理器已清除: {event_type.name}")
    
    def shutdown(self) -> None:
        """关闭事件系统"""
        self.logger.info("事件系统关闭")
        self.clear_handlers() 