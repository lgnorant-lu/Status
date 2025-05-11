"""
---------------------------------------------------------------
File name:                  behavior_trigger.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                桌宠行为触发器管理模块
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import logging
import time
import uuid
import threading
from datetime import datetime, timedelta
from PySide6.QtCore import QObject, QTimer, pyqtSignal
from status.core.events import EventManager
from status.interaction.interaction_event import InteractionEvent, InteractionEventType

# 配置日志
logger = logging.getLogger(__name__)


class Trigger:
    """触发器基类
    
    定义所有触发器的基本接口。
    """
    
    def __init__(self, trigger_id=None, callback=None):
        """初始化触发器
        
        Args:
            trigger_id (str, optional): 触发器ID. 默认为None，会自动生成
            callback (function, optional): 触发时的回调函数. 默认为None
        """
        self.trigger_id = trigger_id or str(uuid.uuid4())
        self.callback = callback
        self.enabled = True
        
    def enable(self):
        """启用触发器
        """
        self.enabled = True
        
    def disable(self):
        """禁用触发器
        """
        self.enabled = False
        
    def is_enabled(self):
        """检查触发器是否启用
        
        Returns:
            bool: 触发器是否启用
        """
        return self.enabled
    
    def check(self):
        """检查触发器是否应该触发
        
        这是一个抽象方法，子类应该重写它。
        
        Returns:
            bool: 是否应该触发
        """
        return False
    
    def trigger(self, data=None):
        """触发触发器
        
        调用回调函数，如果有的话。
        
        Args:
            data (dict, optional): 传递给回调函数的数据. 默认为None
            
        Returns:
            bool: 触发是否成功
        """
        if not self.enabled:
            return False
        
        if self.callback:
            try:
                self.callback(self.trigger_id, data)
                return True
            except Exception as e:
                logger.error(f"Error triggering {self.trigger_id}: {str(e)}")
                return False
        
        return False


class TimeTrigger(Trigger):
    """时间触发器
    
    基于时间的触发器，可以是一次性的或重复的。
    """
    
    def __init__(self, interval, callback=None, trigger_id=None, repeat=False, start_delay=0):
        """初始化时间触发器
        
        Args:
            interval (float): 触发间隔，单位为秒
            callback (function, optional): 触发时的回调函数. 默认为None
            trigger_id (str, optional): 触发器ID. 默认为None，会自动生成
            repeat (bool, optional): 是否重复触发. 默认为False
            start_delay (float, optional): 首次触发的延迟时间，单位为秒. 默认为0
        """
        super().__init__(trigger_id, callback)
        self.interval = interval
        self.repeat = repeat
        self.last_trigger_time = time.time() - interval + start_delay
        self.triggered = False  # 用于一次性触发器
        
    def check(self):
        """检查是否应该触发
        
        基于当前时间和上次触发时间来决定。
        
        Returns:
            bool: 是否应该触发
        """
        # 如果禁用或已触发（对于一次性触发器），则不触发
        if not self.enabled or (not self.repeat and self.triggered):
            return False
        
        # 检查是否到达触发时间
        current_time = time.time()
        if current_time - self.last_trigger_time >= self.interval:
            self.last_trigger_time = current_time
            self.triggered = True
            return True
        
        return False
    
    def reset(self):
        """重置触发器
        
        重置上次触发时间和触发状态。
        """
        self.last_trigger_time = time.time()
        self.triggered = False


class ScheduledTrigger(Trigger):
    """定时触发器
    
    在特定时间点触发的触发器。
    """
    
    def __init__(self, schedule_time, callback=None, trigger_id=None, days=None):
        """初始化定时触发器
        
        Args:
            schedule_time (str): 触发时间，格式为"HH:MM:SS"或"HH:MM"
            callback (function, optional): 触发时的回调函数. 默认为None
            trigger_id (str, optional): 触发器ID. 默认为None，会自动生成
            days (list, optional): 触发的星期几，0-6表示周一到周日. 默认为None，表示每天
        """
        super().__init__(trigger_id, callback)
        
        # 解析时间
        time_parts = schedule_time.split(':')
        self.hour = int(time_parts[0])
        self.minute = int(time_parts[1])
        self.second = int(time_parts[2]) if len(time_parts) > 2 else 0
        
        # 设置日期
        self.days = days  # None表示每天，否则是包含0-6的列表
        
        # 上次检查日期，用于确保每天只触发一次
        self.last_check_date = datetime.now().date()
        self.triggered_today = False
        
    def check(self):
        """检查是否应该触发
        
        基于当前时间和设定的触发时间来决定。
        
        Returns:
            bool: 是否应该触发
        """
        if not self.enabled:
            return False
        
        now = datetime.now()
        current_date = now.date()
        
        # 如果是新的一天，重置触发状态
        if current_date != self.last_check_date:
            self.last_check_date = current_date
            self.triggered_today = False
        
        # 如果今天已经触发过，不再触发
        if self.triggered_today:
            return False
        
        # 检查是否是指定的日期
        if self.days is not None and now.weekday() not in self.days:
            return False
        
        # 检查是否到达触发时间
        if (now.hour == self.hour and 
            now.minute == self.minute and 
            now.second == self.second):
            self.triggered_today = True
            return True
        
        return False


class EventTrigger(Trigger):
    """事件触发器
    
    基于事件的触发器，当特定事件发生时触发。
    """
    
    def __init__(self, event_type, callback=None, trigger_id=None, condition=None):
        """初始化事件触发器
        
        Args:
            event_type (str): 要监听的事件类型
            callback (function, optional): 触发时的回调函数. 默认为None
            trigger_id (str, optional): 触发器ID. 默认为None，会自动生成
            condition (function, optional): 条件函数，接受事件作为参数，返回布尔值. 默认为None
        """
        super().__init__(trigger_id, callback)
        self.event_type = event_type
        self.condition = condition
        
    def check_event(self, event):
        """检查事件是否满足触发条件
        
        Args:
            event: 要检查的事件
            
        Returns:
            bool: 是否应该触发
        """
        if not self.enabled:
            return False
        
        # 检查事件类型
        if not hasattr(event, 'event_type') or event.event_type != self.event_type:
            return False
        
        # 检查条件
        if self.condition:
            try:
                return self.condition(event)
            except Exception as e:
                logger.error(f"Error checking condition for {self.trigger_id}: {str(e)}")
                return False
        
        # 没有条件，直接触发
        return True


class IdleTrigger(Trigger):
    """空闲触发器
    
    在用户空闲一段时间后触发。
    """
    
    def __init__(self, idle_time, callback=None, trigger_id=None, repeat_interval=None):
        """初始化空闲触发器
        
        Args:
            idle_time (float): 空闲时间阈值，单位为秒
            callback (function, optional): 触发时的回调函数. 默认为None
            trigger_id (str, optional): 触发器ID. 默认为None，会自动生成
            repeat_interval (float, optional): 重复触发的间隔，单位为秒. 默认为None，表示不重复
        """
        super().__init__(trigger_id, callback)
        self.idle_time = idle_time
        self.repeat_interval = repeat_interval
        self.last_activity_time = time.time()
        self.last_trigger_time = 0
        self.triggered = False
        
    def update_activity(self):
        """更新最后活动时间
        
        当用户有活动时调用此方法。
        """
        self.last_activity_time = time.time()
        self.triggered = False
        
    def check(self):
        """检查是否应该触发
        
        基于当前时间和上次活动时间来决定。
        
        Returns:
            bool: 是否应该触发
        """
        if not self.enabled:
            return False
        
        current_time = time.time()
        idle_duration = current_time - self.last_activity_time
        
        # 检查是否达到空闲时间阈值
        if idle_duration >= self.idle_time:
            # 如果已经触发过，检查是否需要重复触发
            if self.triggered:
                if self.repeat_interval and current_time - self.last_trigger_time >= self.repeat_interval:
                    self.last_trigger_time = current_time
                    return True
                return False
            
            # 首次触发
            self.triggered = True
            self.last_trigger_time = current_time
            return True
        
        return False


class BehaviorTrigger(QObject):
    """行为触发器管理类
    
    管理各种触发器，包括时间触发器、事件触发器和空闲触发器。
    """
    
    # 定义信号
    trigger_signal = pyqtSignal(str, object)
    
    def __init__(self):
        """初始化行为触发器管理器
        """
        super().__init__()
        self.event_manager = EventManager.get_instance()
        
        # 触发器字典，键是触发器ID，值是触发器对象
        self.triggers = {}
        
        # 事件触发器字典，键是事件类型，值是触发器ID的集合
        self.event_triggers = {}
        
        # 定时器，用于定期检查时间触发器和空闲触发器
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_triggers)
        self.timer.start(1000)  # 每秒检查一次
        
        # 上次用户活动时间
        self.last_activity_time = time.time()
        
        # 注册事件处理器
        self.event_manager.register_handler("*", self.handle_event)
        
        logger.info("BehaviorTrigger initialized")
    
    def add_time_trigger(self, interval, callback=None, trigger_id=None, repeat=False, start_delay=0):
        """添加时间触发器
        
        Args:
            interval (float): 触发间隔，单位为秒
            callback (function, optional): 触发时的回调函数. 默认为None
            trigger_id (str, optional): 触发器ID. 默认为None，会自动生成
            repeat (bool, optional): 是否重复触发. 默认为False
            start_delay (float, optional): 首次触发的延迟时间，单位为秒. 默认为0
            
        Returns:
            str: 触发器ID
        """
        trigger = TimeTrigger(interval, callback, trigger_id, repeat, start_delay)
        return self._add_trigger(trigger)
    
    def add_scheduled_trigger(self, schedule_time, callback=None, trigger_id=None, days=None):
        """添加定时触发器
        
        Args:
            schedule_time (str): 触发时间，格式为"HH:MM:SS"或"HH:MM"
            callback (function, optional): 触发时的回调函数. 默认为None
            trigger_id (str, optional): 触发器ID. 默认为None，会自动生成
            days (list, optional): 触发的星期几，0-6表示周一到周日. 默认为None，表示每天
            
        Returns:
            str: 触发器ID
        """
        trigger = ScheduledTrigger(schedule_time, callback, trigger_id, days)
        return self._add_trigger(trigger)
    
    def add_event_trigger(self, event_type, callback=None, trigger_id=None, condition=None):
        """添加事件触发器
        
        Args:
            event_type (str): 要监听的事件类型
            callback (function, optional): 触发时的回调函数. 默认为None
            trigger_id (str, optional): 触发器ID. 默认为None，会自动生成
            condition (function, optional): 条件函数，接受事件作为参数，返回布尔值. 默认为None
            
        Returns:
            str: 触发器ID
        """
        trigger = EventTrigger(event_type, callback, trigger_id, condition)
        trigger_id = self._add_trigger(trigger)
        
        # 添加到事件触发器字典
        if event_type not in self.event_triggers:
            self.event_triggers[event_type] = set()
        self.event_triggers[event_type].add(trigger_id)
        
        return trigger_id
    
    def add_idle_trigger(self, idle_time, callback=None, trigger_id=None, repeat_interval=None):
        """添加空闲触发器
        
        Args:
            idle_time (float): 空闲时间阈值，单位为秒
            callback (function, optional): 触发时的回调函数. 默认为None
            trigger_id (str, optional): 触发器ID. 默认为None，会自动生成
            repeat_interval (float, optional): 重复触发的间隔，单位为秒. 默认为None，表示不重复
            
        Returns:
            str: 触发器ID
        """
        trigger = IdleTrigger(idle_time, callback, trigger_id, repeat_interval)
        return self._add_trigger(trigger)
    
    def _add_trigger(self, trigger):
        """添加触发器到管理器
        
        Args:
            trigger: 要添加的触发器
            
        Returns:
            str: 触发器ID
        """
        trigger_id = trigger.trigger_id
        
        # 如果回调函数为None，使用默认回调
        if trigger.callback is None:
            trigger.callback = self._default_trigger_callback
        
        # 添加到触发器字典
        self.triggers[trigger_id] = trigger
        
        logger.debug(f"Added trigger {trigger_id}")
        return trigger_id
    
    def remove_trigger(self, trigger_id):
        """移除触发器
        
        Args:
            trigger_id (str): 要移除的触发器ID
            
        Returns:
            bool: 是否成功移除
        """
        if trigger_id not in self.triggers:
            logger.warning(f"Trigger {trigger_id} not found")
            return False
        
        # 获取触发器
        trigger = self.triggers[trigger_id]
        
        # 如果是事件触发器，从事件触发器字典中移除
        if isinstance(trigger, EventTrigger):
            event_type = trigger.event_type
            if event_type in self.event_triggers and trigger_id in self.event_triggers[event_type]:
                self.event_triggers[event_type].remove(trigger_id)
                if not self.event_triggers[event_type]:
                    del self.event_triggers[event_type]
        
        # 从触发器字典中移除
        del self.triggers[trigger_id]
        
        logger.debug(f"Removed trigger {trigger_id}")
        return True
    
    def enable_trigger(self, trigger_id, enabled=True):
        """启用或禁用触发器
        
        Args:
            trigger_id (str): 触发器ID
            enabled (bool, optional): 是否启用. 默认为True
            
        Returns:
            bool: 操作是否成功
        """
        if trigger_id not in self.triggers:
            logger.warning(f"Trigger {trigger_id} not found")
            return False
        
        if enabled:
            self.triggers[trigger_id].enable()
            logger.debug(f"Enabled trigger {trigger_id}")
        else:
            self.triggers[trigger_id].disable()
            logger.debug(f"Disabled trigger {trigger_id}")
        
        return True
    
    def check_triggers(self):
        """检查所有时间触发器和空闲触发器
        
        定期调用此方法以检查触发器是否应该触发。
        """
        # 复制触发器字典的键，因为在循环中可能会修改字典
        trigger_ids = list(self.triggers.keys())
        
        for trigger_id in trigger_ids:
            if trigger_id not in self.triggers:
                continue
                
            trigger = self.triggers[trigger_id]
            
            # 只检查时间触发器和空闲触发器
            if isinstance(trigger, (TimeTrigger, ScheduledTrigger, IdleTrigger)):
                if trigger.check():
                    # 触发
                    data = {
                        "trigger_id": trigger_id,
                        "trigger_type": type(trigger).__name__,
                        "timestamp": time.time()
                    }
                    trigger.trigger(data)
    
    def handle_event(self, event):
        """处理事件
        
        检查是否有事件触发器应该触发。
        
        Args:
            event: 要处理的事件
        """
        # 更新上次活动时间，用于空闲触发器
        if (hasattr(event, 'interaction_type') and 
            event.interaction_type.name.startswith(('MOUSE_', 'TRAY_', 'MENU_', 'HOTKEY_'))):
            self.update_activity()
        
        # 检查事件触发器
        event_type = getattr(event, 'event_type', None)
        if event_type and event_type in self.event_triggers:
            for trigger_id in list(self.event_triggers[event_type]):
                if trigger_id not in self.triggers:
                    continue
                    
                trigger = self.triggers[trigger_id]
                
                if isinstance(trigger, EventTrigger) and trigger.check_event(event):
                    # 触发
                    data = {
                        "trigger_id": trigger_id,
                        "trigger_type": "EventTrigger",
                        "event": event,
                        "timestamp": time.time()
                    }
                    trigger.trigger(data)
    
    def update_activity(self):
        """更新用户活动
        
        当用户有活动时调用此方法，更新空闲触发器。
        """
        self.last_activity_time = time.time()
        
        # 更新所有空闲触发器
        for trigger in self.triggers.values():
            if isinstance(trigger, IdleTrigger):
                trigger.update_activity()
    
    def _default_trigger_callback(self, trigger_id, data):
        """默认的触发器回调函数
        
        当触发器没有指定回调函数时使用此函数。
        
        Args:
            trigger_id (str): 触发器ID
            data (dict): 触发数据
        """
        # 发出信号
        self.trigger_signal.emit(trigger_id, data)
        
        # 创建并发布触发器事件
        trigger_type = data.get("trigger_type", "Unknown")
        
        if trigger_type == "IdleTrigger":
            event_type = InteractionEventType.IDLE_TRIGGER
        else:
            event_type = InteractionEventType.TIMER_TRIGGER
        
        ev = InteractionEvent.create_timer_event(trigger_id, data)
        self.event_manager.post_event(ev)
        
        logger.debug(f"Trigger {trigger_id} fired with default callback")
    
    def shutdown(self):
        """关闭行为触发器管理器
        
        清理资源，停止定时器，移除所有触发器。
        """
        logger.info("Shutting down BehaviorTrigger")
        
        # 停止定时器
        if self.timer.isActive():
            self.timer.stop()
        
        # 注销事件处理器
        self.event_manager.unregister_handler("*", self.handle_event)
        
        # 清空触发器
        self.triggers.clear()
        self.event_triggers.clear() 