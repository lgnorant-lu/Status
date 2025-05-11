"""
---------------------------------------------------------------
File name:                  event_system.py
Author:                     Ignorant-lu
Date created:               2025/04/15
Description:                事件系统核心模块（最小实现，供测试用）
----------------------------------------------------------------
Changed history:            
                            2025/04/15: 初始创建，最小实现以通过pytest测试;
----
"""

from enum import Enum, auto
from threading import Lock
import logging

class EventType(Enum):
    SYSTEM_STATUS_UPDATE = auto()
    ERROR = auto()
    CUSTOM = auto()
    USER_INTERACTION = auto()
    APPLICATION_START = auto()
    APPLICATION_EXIT = auto()

class Event:
    """事件对象"""
    def __init__(self, event_type, sender=None, data=None):
        self.type = event_type
        self.sender = sender
        self.data = data
        self.handled = False

class EventSystem:
    """事件系统（单例模式）"""
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance.handlers = {}
                    cls._instance.logger = logging.getLogger(__name__)
        return cls._instance

    def register_handler(self, event_type, handler):
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        if handler not in self.handlers[event_type]:
            self.handlers[event_type].append(handler)

    def unregister_handler(self, event_type, handler):
        if event_type in self.handlers and handler in self.handlers[event_type]:
            self.handlers[event_type].remove(handler)
            return True
        return False

    def dispatch(self, event):
        if event.type in self.handlers:
            for handler in list(self.handlers[event.type]):
                handler(event)

    def dispatch_event(self, event_type, sender, data):
        """测试API：根据event_type、sender、data构造Event并分发，支持handled短路"""
        event = Event(event_type, sender=sender, data=data)
        if event_type in self.handlers:
            for handler in list(self.handlers[event_type]):
                try:
                    handler(event)
                    if hasattr(event, "handled") and event.handled:
                        break
                except Exception as e:
                    self.logger.error(f"Handler error: {e}")

    def get_handlers_count(self, event_type=None):
        if event_type is None:
            return sum(len(hs) for hs in self.handlers.values())
        return len(self.handlers.get(event_type, []))

    def clear_handlers(self, event_type=None):
        if event_type is None:
            self.handlers.clear()
        else:
            self.handlers[event_type] = []
