"""
---------------------------------------------------------------
File name:                  event_types.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                事件类型定义
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

from typing import Dict, Any, Callable, List, Set, Optional, Union
from enum import Enum, auto

# 事件类型定义
EventType = str
EventData = Dict[str, Any]

# 事件处理器类型
EventHandler = Callable[[EventType, EventData], None]
AsyncEventHandler = Callable[[EventType, EventData], None]  # 将来会改为协程类型

# 事件过滤器类型
EventFilter = Callable[[EventType, EventData], bool]

# 标准事件类型枚举
class SystemEventType(str, Enum):
    """系统事件类型"""
    APPLICATION_START = "system.application.start"
    APPLICATION_EXIT = "system.application.exit"
    ERROR = "system.error"
    WARNING = "system.warning"
    INFO = "system.info"
    DEBUG = "system.debug"
    PLUGIN_LOADED = "system.plugin.loaded"
    PLUGIN_ENABLED = "system.plugin.enabled"
    PLUGIN_DISABLED = "system.plugin.disabled"
    PLUGIN_UNLOADED = "system.plugin.unloaded"
    CONFIG_CHANGED = "system.config.changed"


class UIEventType(str, Enum):
    """UI事件类型"""
    WINDOW_RESIZE = "ui.window.resize"
    WINDOW_MOVE = "ui.window.move"
    WINDOW_CLOSE = "ui.window.close"
    WINDOW_MINIMIZE = "ui.window.minimize"
    WINDOW_RESTORE = "ui.window.restore"
    MOUSE_ENTER = "ui.mouse.enter"
    MOUSE_LEAVE = "ui.mouse.leave"
    MOUSE_MOVE = "ui.mouse.move"
    MOUSE_CLICK = "ui.mouse.click"
    MOUSE_DOUBLE_CLICK = "ui.mouse.double_click"
    MOUSE_PRESS = "ui.mouse.press"
    MOUSE_RELEASE = "ui.mouse.release"
    KEY_PRESS = "ui.key.press"
    KEY_RELEASE = "ui.key.release"


class PetEventType(str, Enum):
    """宠物事件类型"""
    STATE_CHANGE = "pet.state.change"
    BEHAVIOR_CHANGE = "pet.behavior.change"
    ANIMATION_CHANGE = "pet.animation.change"
    ANIMATION_COMPLETE = "pet.animation.complete"
    MOOD_CHANGE = "pet.mood.change"
    HEALTH_CHANGE = "pet.health.change"
    ENERGY_CHANGE = "pet.energy.change"
    HUNGER_CHANGE = "pet.hunger.change"
    INTERACTION_START = "pet.interaction.start"
    INTERACTION_END = "pet.interaction.end"
    PET_SLEEP = "pet.sleep"
    PET_WAKE = "pet.wake"
    PET_EAT = "pet.eat"
    PET_PLAY = "pet.play"
    PET_IDLE = "pet.idle"


class NotificationEventType(str, Enum):
    """通知事件类型"""
    NOTIFICATION_SHOW = "notification.show"
    NOTIFICATION_HIDE = "notification.hide"
    NOTIFICATION_ACTION = "notification.action"
    NOTIFICATION_CLICK = "notification.click"
    TASK_REMINDER = "notification.task.reminder"
    SYSTEM_ALERT = "notification.system.alert"
    SYSTEM_WARNING = "notification.system.warning"
    SYSTEM_INFO = "notification.system.info"


# 事件优先级
class EventPriority(Enum):
    """事件优先级，数值越小优先级越高"""
    HIGHEST = 0
    HIGH = 25
    NORMAL = 50
    LOW = 75
    LOWEST = 100


# 事件节流模式
class ThrottleMode(Enum):
    """事件节流模式"""
    # 丢弃快速连续触发的事件，只保留第一个
    FIRST = auto()
    # 丢弃快速连续触发的事件，只保留最后一个
    LAST = auto()
    # 以固定速率处理事件，不丢弃事件而是延迟处理
    RATE = auto()
    # 不进行节流
    NONE = auto()