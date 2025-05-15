"""
---------------------------------------------------------------
File name:                  event_throttler.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                事件节流器，用于减少高频事件的处理次数
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import logging
import time
from abc import ABC, abstractmethod
from collections import deque
from threading import Lock
from typing import Dict, List, Optional, Set, Type, Callable, Any, Tuple, Union, cast

from .interaction_event import InteractionEvent, InteractionEventType

# 获取日志记录器
logger = logging.getLogger(__name__)


class EventThrottler(ABC):
    """事件节流器基类，定义节流器接口"""
    
    def __init__(self, name: Optional[str] = None):
        """初始化节流器
        
        Args:
            name: 节流器名称，用于日志和调试
        """
        self.name = name or self.__class__.__name__
        self.is_enabled = True
        self.stats = {
            "total_processed": 0,
            "total_throttled": 0
        }
        logger.debug(f"创建事件节流器: {self.name}")
    
    def enable(self) -> None:
        """启用节流器"""
        if not self.is_enabled:
            self.is_enabled = True
            logger.debug(f"节流器 '{self.name}' 已启用")
    
    def disable(self) -> None:
        """禁用节流器"""
        if self.is_enabled:
            self.is_enabled = False
            logger.debug(f"节流器 '{self.name}' 已禁用")
    
    @abstractmethod
    def throttle(self, event: InteractionEvent) -> bool:
        """判断是否应该节流（跳过）此事件
        
        Args:
            event: 要判断的交互事件
            
        Returns:
            bool: 如果应该通过(不节流)返回True，如果应该节流返回False
        """
        pass
    
    def should_process(self, event: InteractionEvent) -> bool:
        """判断是否应该处理事件
        
        首先检查节流器是否启用，然后调用throttle方法判断是否节流
        
        Args:
            event: 要判断的交互事件
            
        Returns:
            bool: 如果应该处理返回True，否则返回False
        """
        # 更新统计信息
        self.stats["total_processed"] += 1
        
        # 如果节流器禁用，直接通过
        if not self.is_enabled:
            return True
        
        # 调用子类的throttle方法判断是否节流
        result = self.throttle(event)
        
        # 如果被节流，更新统计信息
        if not result:
            self.stats["total_throttled"] += 1
        
        return result
    
    def get_stats(self) -> Dict[str, Union[int, float]]:
        """获取节流器的统计信息
        
        Returns:
            dict: 节流器的统计信息
        """
        total = self.stats["total_processed"]
        throttled = self.stats["total_throttled"]
        pass_rate = 1.0 if total == 0 else (total - throttled) / total
        
        return {
            "total_processed": total,
            "total_throttled": throttled,
            "pass_rate": pass_rate
        }
    
    def __str__(self) -> str:
        status = "启用" if self.is_enabled else "禁用"
        return f"{self.name} ({status})"

    def reset(self) -> None:
        """重置节流器的内部状态（可选实现）"""
        pass


class TimeThrottler(EventThrottler):
    """基于时间的节流器，限制事件的处理频率"""
    
    def __init__(self, cooldown_ms: int, event_types: Optional[Set[InteractionEventType]] = None, 
                 property_key: Optional[str] = None, name: Optional[str] = None):
        """初始化基于时间的节流器
        
        Args:
            cooldown_ms: 冷却时间（毫秒），即两次事件处理之间的最小时间间隔
            event_types: 要节流的事件类型集合，如果为None则节流所有类型
            property_key: 用于区分事件的属性键，如果指定，则按此属性分别节流
            name: 节流器名称
        """
        super().__init__(name)
        self.cooldown_ms = cooldown_ms
        self.event_types = event_types
        self.property_key = property_key
        
        # 用于记录上次处理的时间戳
        self.last_processed: Dict[Any, float] = {}
        # 用于线程安全
        self.lock = Lock()
        
        logger.debug(f"时间节流器 '{self.name}' 配置: 冷却时间={cooldown_ms}ms, "
                    f"事件类型={event_types}, 属性键={property_key}")
    
    def throttle(self, event: InteractionEvent) -> bool:
        """判断是否应该节流此事件
        
        Args:
            event: 要判断的交互事件
            
        Returns:
            bool: 如果应该通过(不节流)返回True，如果应该节流返回False
        """
        # 如果指定了事件类型，且当前事件不在列表中，则不节流
        if self.event_types is not None and event.event_type not in self.event_types:
            return True
        
        # 获取当前时间（毫秒）
        current_time = time.time() * 1000
        
        # 确定事件的唯一键
        event_key = self._get_event_key(event)
        
        with self.lock:
            # 获取上次处理此类事件的时间
            last_time = self.last_processed.get(event_key, 0)
            
            # 计算时间差
            time_diff = current_time - last_time
            
            # 如果时间差小于冷却时间，则节流
            if time_diff < self.cooldown_ms:
                logger.debug(f"时间节流器 '{self.name}' 节流事件: {event.event_type}, "
                            f"间隔={time_diff:.2f}ms < {self.cooldown_ms}ms")
                return False
            
            # 更新上次处理时间
            self.last_processed[event_key] = current_time
            
            # 通过事件
            return True
    
    def _get_event_key(self, event: InteractionEvent) -> Any:
        """获取事件的唯一键
        
        Args:
            event: 交互事件
            
        Returns:
            Any: 事件的唯一键
        """
        if self.property_key is None:
            # 如果没有指定属性键，则使用事件类型作为键
            return event.event_type
        
        # 处理属性路径，例如"data.x"
        if self.property_key.startswith("data."):
            # 提取data之后的路径部分
            attr_path = self.property_key[5:]  # 去掉"data."
            
            # 确保event.data存在且是字典
            if hasattr(event, 'data') and isinstance(event.data, dict):
                # 处理嵌套属性，例如"position.x"
                parts = attr_path.split('.')
                value = event.data
                
                # 遍历属性路径
                for part in parts:
                    if isinstance(value, dict) and part in value:
                        value = value[part]
                    else:
                        # 如果路径中有无效部分，就返回默认键
                        return event.event_type
                
                # 返回类型和属性值的组合
                return (event.event_type, value)
        
        # 直接检查data字典
        elif hasattr(event, 'data') and isinstance(event.data, dict):
            if self.property_key in event.data:
                # 使用事件类型和指定属性组合作为键
                return (event.event_type, event.data[self.property_key])
        
        # 默认使用事件类型
        return event.event_type
    
    def reset(self, event_key: Any = None) -> None:
        """重置指定键或所有键的上次处理时间
        
        Args:
            event_key: 要重置的事件键，如果为None则重置所有键
        """
        with self.lock:
            if event_key is not None:
                if event_key in self.last_processed:
                    del self.last_processed[event_key]
                    logger.debug(f"时间节流器 '{self.name}' 重置了键: {event_key}")
            else:
                self.last_processed.clear()
                logger.debug(f"时间节流器 '{self.name}' 已重置所有键")


class CountThrottler(EventThrottler):
    """基于数量的节流器，限制事件的处理次数"""
    
    def __init__(self, max_count: int, time_window_ms: Optional[int] = None, event_types: Optional[Set[InteractionEventType]] = None, 
                 property_key: Optional[str] = None, name: Optional[str] = None):
        """初始化基于数量的节流器
        
        Args:
            max_count: 最大处理次数，在时间窗口内允许通过的最大事件数
            time_window_ms: 时间窗口（毫秒），如果为None则表示全局计数
            event_types: 要节流的事件类型集合，如果为None则节流所有类型
            property_key: 用于区分事件的属性键，如果指定，则按此属性分别节流
            name: 节流器名称
        """
        super().__init__(name)
        self.max_count = max_count
        self.time_window_ms = time_window_ms
        self.event_types = event_types
        self.property_key = property_key
        
        # 用于记录事件处理计数和时间
        self.event_counts: Dict[Any, int] = {}  # 全局计数模式
        self.event_timestamps: Dict[Any, List[float]] = {}  # 时间窗口模式
        # 用于线程安全
        self.lock = Lock()
        
        logger.debug(f"数量节流器 '{self.name}' 配置: 最大次数={max_count}, "
                    f"时间窗口={time_window_ms}ms, 事件类型={event_types}, 属性键={property_key}")
    
    def throttle(self, event: InteractionEvent) -> bool:
        """判断是否应该节流此事件
        
        Args:
            event: 要判断的交互事件
            
        Returns:
            bool: 如果应该通过(不节流)返回True，如果应该节流返回False
        """
        # 如果指定了事件类型，且当前事件不在列表中，则不节流
        if self.event_types is not None and event.event_type not in self.event_types:
            return True
        
        # 确定事件的唯一键
        event_key = self._get_event_key(event)
        
        with self.lock:
            current_time = time.time() * 1000
            
            if self.time_window_ms is None:
                # 全局计数模式
                count = self.event_counts.get(event_key, 0)
                
                if count >= self.max_count:
                    logger.debug(f"数量节流器 '{self.name}' 节流事件: {event.event_type}, "
                               f"计数={count} >= {self.max_count}")
                    return False
                
                # 增加计数并通过
                self.event_counts[event_key] = count + 1
                return True
            else:
                # 时间窗口模式
                if event_key not in self.event_timestamps:
                    self.event_timestamps[event_key] = []
                
                timestamps = self.event_timestamps[event_key]
                
                # 清除窗口外的时间戳
                cutoff_time = current_time - self.time_window_ms
                while timestamps and timestamps[0] < cutoff_time:
                    timestamps.pop(0)
                
                # 检查窗口内的事件数量
                if len(timestamps) >= self.max_count:
                    logger.debug(f"数量节流器 '{self.name}' 节流事件: {event.event_type}, "
                               f"窗口内计数={len(timestamps)} >= {self.max_count}")
                    return False
                
                # 添加当前时间戳并通过
                timestamps.append(current_time)
                return True
    
    def _get_event_key(self, event: InteractionEvent) -> Any:
        """获取事件的唯一键
        
        Args:
            event: 交互事件
            
        Returns:
            Any: 事件的唯一键
        """
        if self.property_key is None:
            # 如果没有指定属性键，则使用事件类型作为键
            return event.event_type
        
        # 处理属性路径，例如"data.x"
        if self.property_key.startswith("data."):
            # 提取data之后的路径部分
            attr_path = self.property_key[5:]  # 去掉"data."
            
            # 确保event.data存在且是字典
            if hasattr(event, 'data') and isinstance(event.data, dict):
                # 处理嵌套属性，例如"position.x"
                parts = attr_path.split('.')
                value = event.data
                
                # 遍历属性路径
                for part in parts:
                    if isinstance(value, dict) and part in value:
                        value = value[part]
                    else:
                        # 如果路径中有无效部分，就返回默认键
                        return event.event_type
                
                # 返回类型和属性值的组合
                return (event.event_type, value)
        
        # 直接检查data字典
        elif hasattr(event, 'data') and isinstance(event.data, dict):
            if self.property_key in event.data:
                # 使用事件类型和指定属性组合作为键
                return (event.event_type, event.data[self.property_key])
        
        # 默认使用事件类型
        return event.event_type
    
    def reset(self, event_key: Any = None) -> None:
        """重置指定键或所有键的事件计数和时间窗口
        
        Args:
            event_key: 要重置的事件键，如果为None则重置所有键
        """
        with self.lock:
            if event_key is not None:
                if event_key in self.event_counts:
                    del self.event_counts[event_key]
                if event_key in self.event_timestamps:
                    del self.event_timestamps[event_key]
                logger.debug(f"数量节流器 '{self.name}' 重置了键: {event_key}")
            else:
                self.event_counts.clear()
                self.event_timestamps.clear()
                logger.debug(f"数量节流器 '{self.name}' 已重置所有键")


class QueueThrottler(EventThrottler):
    """基于队列的节流器，积累多个事件后批量处理一次"""
    
    def __init__(self, batch_size: int, event_types: Optional[Set[InteractionEventType]] = None,
                 property_key: Optional[str] = None, batch_processor: Optional[Callable[[List[InteractionEvent]], None]] = None,
                 name: Optional[str] = None):
        """初始化基于队列的节流器
        
        Args:
            batch_size: 批处理大小，积累这么多事件后处理一次
            event_types: 要节流的事件类型集合，如果为None则节流所有类型
            property_key: 用于区分事件的属性键，如果指定，则按此属性分别批处理
            batch_processor: 批处理函数，如果提供，则在达到批量大小时调用此函数
            name: 节流器名称
        """
        super().__init__(name)
        self.batch_size = batch_size
        self.event_types = event_types
        self.property_key = property_key
        self.batch_processor = batch_processor
        
        # 事件队列字典，按键分类
        self.event_queues: Dict[Any, deque] = {}
        # 用于线程安全
        self.lock = Lock()
        
        logger.debug(f"队列节流器 '{self.name}' 配置: 批处理大小={batch_size}, "
                    f"事件类型={event_types}, 属性键={property_key}, "
                    f"批处理函数={'已提供' if batch_processor else '未提供'}")
    
    def throttle(self, event: InteractionEvent) -> bool:
        """判断是否应该节流此事件
        
        Args:
            event: 要判断的交互事件
            
        Returns:
            bool: 如果应该通过(不节流)返回True，如果应该节流返回False
        """
        # 如果指定了事件类型，且当前事件不在列表中，则不节流
        if self.event_types is not None and event.event_type not in self.event_types:
            return True
        
        # 确定事件的唯一键
        event_key = self._get_event_key(event)
        
        with self.lock:
            # 确保队列存在
            if event_key not in self.event_queues:
                self.event_queues[event_key] = deque()
            
            # 获取队列
            queue = self.event_queues[event_key]
            
            # 添加到队列
            queue.append(event)
            
            # 如果达到批处理大小，则处理并返回True
            if len(queue) >= self.batch_size:
                if self.batch_processor:
                    # 如果提供了批处理函数，则调用
                    events_to_process = list(queue)
                    queue.clear()
                    # 在锁外执行批处理，避免长时间占用锁
                    self.lock.release()
                    try:
                        self.batch_processor(events_to_process)
                    finally:
                        self.lock.acquire()
                else:
                    # 如果没有提供批处理函数，则只保留最新的事件
                    queue.clear()
                
                logger.debug(f"队列节流器 '{self.name}' 处理批次事件: {event_key}, 数量={self.batch_size}")
                return True
            else:
                # 未达到批处理大小，添加到队列并节流
                logger.debug(f"队列节流器 '{self.name}' 积累事件: {event_key}, 当前队列大小={len(queue)}/{self.batch_size}")
                return False
    
    def _get_event_key(self, event: InteractionEvent) -> Any:
        """获取事件的唯一键
        
        Args:
            event: 交互事件
            
        Returns:
            Any: 事件的唯一键
        """
        if self.property_key is None:
            # 如果没有指定属性键，则使用事件类型作为键
            return event.event_type
        
        # 处理属性路径，例如"data.x"
        if self.property_key.startswith("data."):
            # 提取data之后的路径部分
            attr_path = self.property_key[5:]  # 去掉"data."
            
            # 确保event.data存在且是字典
            if hasattr(event, 'data') and isinstance(event.data, dict):
                # 处理嵌套属性，例如"position.x"
                parts = attr_path.split('.')
                value = event.data
                
                # 遍历属性路径
                for part in parts:
                    if isinstance(value, dict) and part in value:
                        value = value[part]
                    else:
                        # 如果路径中有无效部分，就返回默认键
                        return event.event_type
                
                # 返回类型和属性值的组合
                return (event.event_type, value)
        
        # 直接检查data字典
        elif hasattr(event, 'data') and isinstance(event.data, dict):
            if self.property_key in event.data:
                # 使用事件类型和指定属性组合作为键
                return (event.event_type, event.data[self.property_key])
        
        # 默认使用事件类型
        return event.event_type
    
    def flush(self, event_key: Any = None) -> List[InteractionEvent]:
        """强制处理队列中的事件
        
        Args:
            event_key: 要处理的事件键，如果为None则处理所有
            
        Returns:
            List[InteractionEvent]: 队列中的事件列表，如果使用了batch_processor则队列会被清空
        """
        with self.lock:
            if event_key is None:
                # 处理所有队列
                result = []
                for key, queue in self.event_queues.items():
                    if queue:
                        events = list(queue)
                        if self.batch_processor:
                            # 如果提供了批处理函数，则调用
                            self.lock.release()
                            try:
                                self.batch_processor(events)
                            finally:
                                self.lock.acquire()
                        else:
                            # 如果没有提供批处理函数，则添加到结果
                            result.extend(events)
                        queue.clear()
                        logger.debug(f"队列节流器 '{self.name}' 强制处理事件: {key}, 数量={len(events)}")
                
                return result
            elif event_key in self.event_queues:
                # 处理指定队列
                queue = self.event_queues[event_key]
                if queue:
                    events = list(queue)
                    if self.batch_processor:
                        # 如果提供了批处理函数，则调用
                        self.lock.release()
                        try:
                            self.batch_processor(events)
                        finally:
                            self.lock.acquire()
                    queue.clear()
                    logger.debug(f"队列节流器 '{self.name}' 强制处理事件: {event_key}, 数量={len(events)}")
                    return events
            
            return []

    def reset(self) -> None:
        """清空所有队列，不处理其中的事件"""
        with self.lock:
            self.event_queues.clear()
            logger.debug(f"队列节流器 '{self.name}' 已重置，所有队列已清空")


class LastEventThrottler(EventThrottler):
    """只处理冷却时间内最后一个事件的节流器"""
    
    def __init__(self, cooldown_ms: int, event_types: Optional[Set[InteractionEventType]] = None,
                 property_key: Optional[str] = None, name: Optional[str] = None):
        """初始化最后事件节流器
        
        Args:
            cooldown_ms: 冷却时间（毫秒），在此时间内只处理最后一个事件
            event_types: 要节流的事件类型集合，如果为None则节流所有类型
            property_key: 用于区分事件的属性键，如果指定，则按此属性分别节流
            name: 节流器名称
        """
        super().__init__(name)
        self.cooldown_ms = cooldown_ms
        self.event_types = event_types
        self.property_key = property_key
        
        self.pending_events: Dict[Any, Tuple[InteractionEvent, float]] = {}
        self.last_processed: Dict[Any, float] = {}
        self.lock = Lock()
        
        logger.debug(f"最后事件节流器 '{self.name}' 配置: 冷却时间={cooldown_ms}ms, "
                    f"事件类型={event_types}, 属性键={property_key}")

    def throttle(self, event: InteractionEvent) -> bool:
        """判断是否应该节流此事件
        
        Args:
            event: 要判断的交互事件
            
        Returns:
            bool: 如果应该通过(不节流)返回True，如果应该节流返回False
        """
        # Note: Stats (total_processed, total_throttled) are handled by the base EventThrottler.should_process() method.
        # This method should only return True if the event should PASS (not be throttled by this specific throttler),
        # and False if it should BE THROTTLED.

        # No need to check self.is_enabled here, base class should_process does that.
        # No need to check self.event_types here if we assume should_process or another layer handles it,
        # or if the design is that this throttler type *always* checks event_types internally.
        # For now, retaining event_types check as it was part of its specific logic.
        if self.event_types is not None and event.event_type not in self.event_types:
            return True # Not of interest to this throttler, so it passes.
        
        current_time = time.time() * 1000
        event_key = self._get_event_key(event)
        
        decision_to_pass = False 

        with self.lock:
            last_time = self.last_processed.get(event_key, 0)
            time_diff = current_time - last_time
            
            if last_time == 0 or time_diff < self.cooldown_ms:
                # Condition met to throttle and store/update pending event
                self.pending_events[event_key] = (event, current_time)
                # logger call for debug was here, can be restored if needed for fine-grained logging
                decision_to_pass = False # Event is throttled by this logic
            else:
                # Condition not met, event should pass through this throttler's logic
                self.last_processed[event_key] = current_time
                if event_key in self.pending_events:
                    # An event was pending, but now a new event is passing after cooldown,
                    # so the pending one is superseded and should be cleared.
                    del self.pending_events[event_key]
                decision_to_pass = True # Event passes this throttler's logic
        
        return decision_to_pass

    def _get_event_key(self, event: InteractionEvent) -> Any:
        """获取事件的唯一键
        
        Args:
            event: 交互事件
            
        Returns:
            Any: 事件的唯一键
        """
        if self.property_key is None:
            # 如果没有指定属性键，则使用事件类型作为键
            return event.event_type
        
        # 处理属性路径，例如"data.x"
        if self.property_key.startswith("data."):
            # 提取data之后的路径部分
            attr_path = self.property_key[5:]  # 去掉"data."
            
            # 确保event.data存在且是字典
            if hasattr(event, 'data') and isinstance(event.data, dict):
                # 处理嵌套属性，例如"position.x"
                parts = attr_path.split('.')
                value = event.data
                
                # 遍历属性路径
                for part in parts:
                    if isinstance(value, dict) and part in value:
                        value = value[part]
                    else:
                        # 如果路径中有无效部分，就返回默认键
                        return event.event_type
                
                # 返回类型和属性值的组合
                return (event.event_type, value)
        
        # 直接检查data字典
        elif hasattr(event, 'data') and isinstance(event.data, dict):
            if self.property_key in event.data:
                # 使用事件类型和指定属性组合作为键
                return (event.event_type, event.data[self.property_key])
        
        # 默认使用事件类型
        return event.event_type
    
    def flush(self, event_key: Any = None) -> List[InteractionEvent]:
        result: List[InteractionEvent] = []
        with self.lock:
            if event_key is None: 
                items_to_flush = list(self.pending_events.items()) 
                for key, (event_data, pending_time) in items_to_flush:
                    result.append(event_data)
                    self.last_processed[key] = time.time() * 1000 
                    if key in self.pending_events: 
                        del self.pending_events[key]
                    # logger call for debug was here
            else: 
                # Simplified specific key flush logic, ensure it's robust if used heavily.
                # The test case primarily uses event_key=None.
                matched_keys_to_remove: List[Any] = []
                items_to_check = list(self.pending_events.items())

                for key, (event, p_time) in items_to_check:
                    should_match = False
                    if self.property_key is None and key == event_key: 
                        should_match = True
                    elif self.property_key is not None: 
                        # This logic needs to be robust for various property_key scenarios
                        # Example: if event_key is the property value, not the compound key
                        current_event_key_for_comparison = self._get_event_key(event) # Get the compound key
                        if current_event_key_for_comparison == event_key: # direct match of compound key
                             should_match = True
                        elif isinstance(current_event_key_for_comparison, tuple) and current_event_key_for_comparison[1] == event_key:
                             # If event_key is just the property value part of a compound key
                             should_match = True
                    
                    if should_match:
                        result.append(event)
                        matched_keys_to_remove.append(key)
                
                current_flush_time = time.time() * 1000
                for key_to_remove in matched_keys_to_remove:
                    self.last_processed[key_to_remove] = current_flush_time
                    if key_to_remove in self.pending_events:
                         del self.pending_events[key_to_remove]
                    # logger call for debug was here
        return result

    def reset(self, event_key: Any = None) -> None:
        with self.lock:
            if event_key is not None:
                if event_key in self.pending_events: del self.pending_events[event_key]
                if event_key in self.last_processed: del self.last_processed[event_key]
            else:
                self.pending_events.clear()
                self.last_processed.clear()
            logger.debug(f"最后事件节流器 '{self.name}' {'已重置所有键' if event_key is None else f'重置了键: {event_key}'}")


class EventThrottlerChain(EventThrottler):
    """事件节流器链，按顺序应用多个节流器"""
    
    def __init__(self, name: str = "EventThrottlerChain"):
        super().__init__(name)
        self.throttlers: List[EventThrottler] = []
        self.lock = Lock()
        logger.debug(f"创建节流器链: {self.name}")
    
    def add_throttler(self, throttler: EventThrottler) -> bool:
        with self.lock:
            if throttler not in self.throttlers:
                self.throttlers.append(throttler)
                logger.debug(f"节流器 '{throttler.name}' 已添加到链 '{self.name}'")
                return True
            logger.warning(f"尝试添加重复的节流器 '{throttler.name}' 到链 '{self.name}'")
            return False

    def remove_throttler(self, throttler_or_name) -> bool:
        with self.lock:
            initial_len = len(self.throttlers)
            if isinstance(throttler_or_name, EventThrottler):
                self.throttlers = [t for t in self.throttlers if t is not throttler_or_name]
            elif isinstance(throttler_or_name, str):
                self.throttlers = [t for t in self.throttlers if t.name != throttler_or_name]
            else:
                logger.error(f"无效的参数类型用于移除节流器: {type(throttler_or_name)}")
                return False
            
            removed_count = initial_len - len(self.throttlers)
            if removed_count > 0:
                logger.debug(f"从链 '{self.name}' 移除了 {removed_count} 个节流器 (基于 '{throttler_or_name}')")
                return True
            logger.warning(f"未找到节流器 '{throttler_or_name}' 在链 '{self.name}' 中")
            return False

    def clear_throttlers(self) -> None:
        with self.lock:
            self.throttlers.clear()
            logger.debug(f"节流器链 '{self.name}' 已清空")

    def get_throttlers(self) -> List[EventThrottler]:
        with self.lock:
            return self.throttlers.copy()

    def throttle(self, event: InteractionEvent) -> bool:
        if not self.is_enabled:
            return True

        self.stats["total_processed"] += 1

        processed_by_all = True
        current_throttlers = self.get_throttlers()
        for throttler in current_throttlers:
            if not throttler.should_process(event):
                processed_by_all = False
                break
        
        if not processed_by_all:
            self.stats["total_throttled"] += 1

        return processed_by_all
    
    def get_stats(self) -> Dict[str, Any]:
        throttler_details: Dict[str, Any] = {}
        sum_children_processed = 0
        sum_children_throttled = 0

        current_throttlers = self.get_throttlers()
        for throttler in current_throttlers:
            stats = throttler.get_stats()
            throttler_details[throttler.name] = stats
            sum_children_processed += cast(int, stats.get("total_processed", 0))
            sum_children_throttled += cast(int, stats.get("total_throttled", 0))
        
        sum_children_pass_rate = 1.0
        if sum_children_processed > 0:
            sum_children_pass_rate = (sum_children_processed - sum_children_throttled) / sum_children_processed
        
        chain_own_pass_rate = 1.0
        if "total_processed" in self.stats and self.stats["total_processed"] > 0:
            chain_own_pass_rate = (self.stats["total_processed"] - self.stats.get("total_throttled", 0)) / self.stats["total_processed"]
        elif "total_processed" not in self.stats or self.stats["total_processed"] == 0:
            pass

        return {
            "name": self.name,
            "total_throttlers": len(current_throttlers),
            
            "total_processed": self.stats.get("total_processed", 0),
            "total_throttled": self.stats.get("total_throttled", 0),
            "pass_rate": chain_own_pass_rate,

            "children_total_processed": sum_children_processed,
            "children_total_throttled": sum_children_throttled,
            "children_pass_rate": sum_children_pass_rate,
            
            "throttlers": throttler_details
        }
    
    def __str__(self) -> str:
        return f"{self.name} ({len(self.throttlers)} 个节流器)"

    def reset(self) -> None:
        for throttler in self.throttlers:
            throttler.reset()
        self.stats = {"total_processed": 0, "total_throttled": 0}
        logger.debug(f"节流器链 '{self.name}' 已重置所有节流器和统计") 