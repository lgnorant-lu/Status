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
from typing import Dict, List, Optional, Set, Type, Callable, Any, Tuple

from .interaction_event import InteractionEvent, InteractionEventType

# 获取日志记录器
logger = logging.getLogger(__name__)


class EventThrottler(ABC):
    """事件节流器基类，定义节流器接口"""
    
    def __init__(self, name: str = None):
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
    
    def get_stats(self) -> dict:
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


class TimeThrottler(EventThrottler):
    """基于时间的节流器，限制事件的处理频率"""
    
    def __init__(self, cooldown_ms: int, event_types: Set[InteractionEventType] = None, 
                 property_key: str = None, name: str = None):
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
        """重置节流器状态
        
        Args:
            event_key: 要重置的事件键，如果为None则重置所有
        """
        with self.lock:
            if event_key is None:
                # 重置所有
                self.last_processed.clear()
                logger.debug(f"时间节流器 '{self.name}' 已重置所有事件计时")
            elif event_key in self.last_processed:
                # 重置指定键
                del self.last_processed[event_key]
                logger.debug(f"时间节流器 '{self.name}' 已重置事件键 {event_key} 的计时")


class CountThrottler(EventThrottler):
    """基于数量的节流器，限制事件的处理次数"""
    
    def __init__(self, max_count: int, time_window_ms: int = None, event_types: Set[InteractionEventType] = None, 
                 property_key: str = None, name: str = None):
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
        """重置节流器状态
        
        Args:
            event_key: 要重置的事件键，如果为None则重置所有
        """
        with self.lock:
            if event_key is None:
                # 重置所有
                self.event_counts.clear()
                self.event_timestamps.clear()
                logger.debug(f"数量节流器 '{self.name}' 已重置所有事件计数")
            else:
                # 重置指定键
                if event_key in self.event_counts:
                    del self.event_counts[event_key]
                if event_key in self.event_timestamps:
                    del self.event_timestamps[event_key]
                logger.debug(f"数量节流器 '{self.name}' 已重置事件键 {event_key} 的计数")


class QueueThrottler(EventThrottler):
    """基于队列的节流器，积累多个事件后批量处理一次"""
    
    def __init__(self, batch_size: int, event_types: Set[InteractionEventType] = None,
                 property_key: str = None, batch_processor: Callable[[List[InteractionEvent]], None] = None,
                 name: str = None):
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
        """重置节流器状态，清空所有事件队列"""
        with self.lock:
            self.event_queues.clear()
            logger.debug(f"队列节流器 '{self.name}' 已重置，所有队列已清空")


class LastEventThrottler(EventThrottler):
    """只处理冷却时间内最后一个事件的节流器"""
    
    def __init__(self, cooldown_ms: int, event_types: Set[InteractionEventType] = None,
                 property_key: str = None, name: str = None):
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
        
        # 用于存储待处理的最后事件
        self.pending_events: Dict[Any, Tuple[InteractionEvent, float]] = {}
        # 上次处理时间记录
        self.last_processed: Dict[Any, float] = {}
        # 用于线程安全
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
            
            # 对于第一个事件(last_time=0)或时间差小于冷却时间的事件，将其存储并节流
            if last_time == 0 or time_diff < self.cooldown_ms:
                # 保存事件以便稍后处理
                self.pending_events[event_key] = (event, current_time)
                if last_time == 0:
                    logger.debug(f"最后事件节流器 '{self.name}' 保存首个事件: {event.event_type}")
                else:
                    logger.debug(f"最后事件节流器 '{self.name}' 更新挂起事件: {event.event_type}, "
                               f"间隔={time_diff:.2f}ms < {self.cooldown_ms}ms")
                return False
            
            # 更新上次处理时间
            self.last_processed[event_key] = current_time
            
            # 清除挂起事件
            if event_key in self.pending_events:
                del self.pending_events[event_key]
            
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
    
    def flush(self, event_key: Any = None) -> List[InteractionEvent]:
        """强制处理挂起的事件
        
        Args:
            event_key: 要处理的事件键，如果为None则处理所有
                       如果使用property_key，可以传入具体的属性值(如100)来处理特定事件
            
        Returns:
            List[InteractionEvent]: 挂起的事件列表
        """
        with self.lock:
            result = []
            
            if event_key is None:
                # 处理所有挂起事件
                for key, (event, _) in list(self.pending_events.items()):
                    result.append(event)
                    # 更新上次处理时间
                    self.last_processed[key] = time.time() * 1000
                    # 清除挂起事件
                    del self.pending_events[key]
                    logger.debug(f"最后事件节流器 '{self.name}' 强制处理挂起事件: {key}")
            else:
                # 处理特定事件键，这可以是从property_key获取的值
                # 需要检查每个事件的键，因为flush的参数可能是property_key中的值
                matched_keys = []
                for key, (event, _) in list(self.pending_events.items()):
                    # 处理元组键，如(EventType, property_value)
                    if isinstance(key, tuple) and len(key) > 1:
                        if key[1] == event_key:
                            result.append(event)
                            matched_keys.append(key)
                            logger.debug(f"最后事件节流器 '{self.name}' 强制处理挂起事件(属性匹配): {key}")
                    # 处理直接匹配键
                    elif key == event_key:
                        result.append(event)
                        matched_keys.append(key)
                        logger.debug(f"最后事件节流器 '{self.name}' 强制处理挂起事件(直接匹配): {key}")
                    # 处理事件数据中的属性值
                    elif hasattr(event, 'data') and isinstance(event.data, dict):
                        if self.property_key and self.property_key in event.data and event.data[self.property_key] == event_key:
                            result.append(event)
                            matched_keys.append(key)
                            logger.debug(f"最后事件节流器 '{self.name}' 强制处理挂起事件(数据属性匹配): {key}")
                        elif self.property_key and self.property_key.startswith("data."):
                            # 处理嵌套属性路径
                            attr_path = self.property_key[5:]  # 去掉"data."
                            parts = attr_path.split('.')
                            value = event.data
                            match = True
                            
                            # 遍历属性路径
                            for part in parts:
                                if isinstance(value, dict) and part in value:
                                    value = value[part]
                                else:
                                    match = False
                                    break
                            
                            if match and value == event_key:
                                result.append(event)
                                matched_keys.append(key)
                                logger.debug(f"最后事件节流器 '{self.name}' 强制处理挂起事件(嵌套属性匹配): {key}")
                
                # 更新处理时间并清除已处理的事件
                current_time = time.time() * 1000
                for key in matched_keys:
                    self.last_processed[key] = current_time
                    del self.pending_events[key]
            
            return result


class EventThrottlerChain:
    """管理多个事件节流器的节流器链"""
    
    def __init__(self, name: str = "EventThrottlerChain"):
        """初始化节流器链
        
        Args:
            name: 节流器链名称
        """
        self.name = name
        self.throttlers: List[EventThrottler] = []
        self.stats = {
            "total_processed": 0,
            "total_throttled": 0,
            "throttlers": {}  # 各节流器统计
        }
        logger.debug(f"事件节流器链 '{name}' 创建")
    
    def add_throttler(self, throttler: EventThrottler) -> bool:
        """向节流器链添加节流器
        
        Args:
            throttler: 要添加的节流器
            
        Returns:
            bool: 添加成功返回True
        """
        if throttler in self.throttlers:
            logger.warning(f"节流器 '{throttler.name}' 已存在于节流器链 '{self.name}' 中")
            return False
            
        self.throttlers.append(throttler)
        self.stats["throttlers"][throttler.name] = {"processed": 0, "throttled": 0}
        logger.debug(f"节流器 '{throttler.name}' 添加到节流器链 '{self.name}'")
        return True
    
    def remove_throttler(self, throttler_or_name) -> bool:
        """从节流器链移除节流器
        
        Args:
            throttler_or_name: 要移除的节流器对象或名称
            
        Returns:
            bool: 移除成功返回True
        """
        # 如果传入的是节流器名称，查找对应的节流器对象
        if isinstance(throttler_or_name, str):
            throttler_name = throttler_or_name
            for t in self.throttlers:
                if t.name == throttler_name:
                    self.throttlers.remove(t)
                    if throttler_name in self.stats["throttlers"]:
                        del self.stats["throttlers"][throttler_name]
                    logger.debug(f"节流器 '{throttler_name}' 从节流器链 '{self.name}' 中移除")
                    return True
            logger.warning(f"节流器 '{throttler_name}' 不存在于节流器链 '{self.name}' 中")
            return False
        else:
            # 传入的是节流器对象
            throttler = throttler_or_name
            if throttler in self.throttlers:
                self.throttlers.remove(throttler)
                if throttler.name in self.stats["throttlers"]:
                    del self.stats["throttlers"][throttler.name]
                logger.debug(f"节流器 '{throttler.name}' 从节流器链 '{self.name}' 中移除")
                return True
            else:
                logger.warning(f"节流器 '{throttler.name}' 不存在于节流器链 '{self.name}' 中")
                return False
    
    def clear_throttlers(self) -> None:
        """清空节流器链中的所有节流器"""
        count = len(self.throttlers)
        self.throttlers.clear()
        self.stats["throttlers"] = {}
        logger.debug(f"节流器链 '{self.name}' 已清空，移除了 {count} 个节流器")
    
    def get_throttlers(self) -> List[EventThrottler]:
        """获取节流器链中的所有节流器
        
        Returns:
            List[EventThrottler]: 节流器列表
        """
        return self.throttlers.copy()
    
    def throttle(self, event: InteractionEvent) -> bool:
        """判断是否应该节流事件
        
        按顺序检查所有节流器，只要有一个节流器决定节流，就会节流事件
        
        Args:
            event: 要检查的交互事件
            
        Returns:
            bool: 如果任一节流器决定节流返回False，否则返回True
        """
        self.stats["total_processed"] += 1
        
        # 如果没有节流器，默认通过
        if not self.throttlers:
            return True
        
        # 只要有一个节流器决定节流，就会节流事件
        for throttler in self.throttlers:
            if not throttler.is_enabled:
                # 跳过禁用的节流器
                continue
                
            # 更新统计信息
            if throttler.name in self.stats["throttlers"]:
                self.stats["throttlers"][throttler.name]["processed"] += 1
            
            if not throttler.should_process(event):
                # 更新统计信息
                self.stats["total_throttled"] += 1
                if throttler.name in self.stats["throttlers"]:
                    self.stats["throttlers"][throttler.name]["throttled"] += 1
                
                logger.debug(f"事件 {event} 被节流器 '{throttler.name}' 节流")
                return False
        
        # 所有节流器都通过
        return True
    
    def get_stats(self) -> dict:
        """获取节流器链的统计信息
        
        Returns:
            dict: 节流器链的统计信息
        """
        # 计算通过率
        total = self.stats["total_processed"]
        throttled = self.stats["total_throttled"]
        pass_rate = 1.0 if total == 0 else (total - throttled) / total
        
        # 返回详细统计信息
        return {
            "total_processed": total,
            "total_throttled": throttled,
            "pass_rate": pass_rate,
            "throttlers": self.stats["throttlers"]
        }
    
    def __str__(self) -> str:
        """返回节流器链的字符串表示
        
        Returns:
            str: 节流器链的字符串表示
        """
        return f"{self.name} ({len(self.throttlers)} 个节流器)"

    def reset(self) -> None:
        """重置所有节流器的状态"""
        for throttler in self.throttlers:
            if hasattr(throttler, 'reset'):
                throttler.reset()
        logger.debug(f"节流器链 '{self.name}' 的所有节流器已重置") 