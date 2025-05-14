"""
---------------------------------------------------------------
File name:                  event_manager.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                事件管理器
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

import time
import logging
import asyncio
import threading
from typing import Dict, List, Set, Optional, Callable, Any, Tuple, Union
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor

from status.core.types import SingletonType
from status.events.event_types import (
    EventType, EventData, EventHandler, AsyncEventHandler, EventFilter,
    EventPriority, ThrottleMode
)


class EventSubscription:
    """事件订阅信息"""
    
    def __init__(
            self,
            handler: Union[EventHandler, AsyncEventHandler],
            event_type: EventType,
            priority: EventPriority = EventPriority.NORMAL,
            filters: Optional[List[EventFilter]] = None,
            is_async: bool = False,
            throttle: Optional[Tuple[ThrottleMode, float]] = None,
            once: bool = False
    ):
        """初始化事件订阅
        
        Args:
            handler: 事件处理器
            event_type: 事件类型
            priority: 事件优先级
            filters: 事件过滤器列表
            is_async: 是否为异步处理器
            throttle: 事件节流设置，格式为(模式, 间隔秒数)
            once: 是否只触发一次
        """
        self.handler = handler
        self.event_type = event_type
        self.priority = priority
        self.filters = filters or []
        self.is_async = is_async
        self.throttle = throttle
        self.once = once
        
        # 用于节流的状态跟踪
        self.last_fired_time: float = 0
        self.queued_event: Optional[Tuple[EventType, EventData]] = None
        self.is_throttled: bool = False
        
        # 生成唯一ID，用于标识和移除订阅
        self.id = id(self)
    
    def matches(self, event_type: EventType, event_data: EventData) -> bool:
        """检查事件是否匹配此订阅
        
        Args:
            event_type: 事件类型
            event_data: 事件数据
            
        Returns:
            bool: 是否匹配
        """
        # 检查事件类型是否匹配
        if self.event_type != event_type and self.event_type != "*":
            return False
        
        # 应用所有过滤器
        for filter_func in self.filters:
            if not filter_func(event_type, event_data):
                return False
        
        return True
    
    def should_throttle(self) -> bool:
        """检查是否应该节流此事件
        
        Returns:
            bool: 是否应该节流
        """
        if not self.throttle:
            return False
        
        mode, interval = self.throttle
        current_time = time.time()
        elapsed = current_time - self.last_fired_time
        
        if elapsed < interval:
            self.is_throttled = True
            return True
        
        self.is_throttled = False
        self.last_fired_time = current_time
        return False


class EventManager(metaclass=SingletonType):
    """事件管理器，负责事件的分发和处理
    
    采用单例模式确保全局只有一个事件管理器实例
    """
    
    def __init__(self):
        """初始化事件管理器"""
        self.logger = logging.getLogger("Status.Events.EventManager")
        
        # 事件订阅，按事件类型分组
        self.subscriptions: Dict[EventType, List[EventSubscription]] = {}
        # 通配符订阅，接收所有事件
        self.wildcard_subscriptions: List[EventSubscription] = []
        
        # 用于异步事件处理的队列
        self.async_event_queue: Queue = Queue()
        # 异步事件处理线程
        self.async_thread: Optional[threading.Thread] = None
        # 线程运行标志
        self.running: bool = False
        # 线程池，用于并行处理事件
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
        # 已注册事件类型合集
        self.registered_event_types: Set[EventType] = set()
    
    def start(self) -> None:
        """启动异步事件处理线程"""
        if self.async_thread is not None and self.async_thread.is_alive():
            return
        
        self.running = True
        self.async_thread = threading.Thread(target=self._process_async_events, daemon=True)
        self.async_thread.start()
        self.logger.info("事件管理器异步处理线程已启动")
    
    def stop(self) -> None:
        """停止异步事件处理线程"""
        self.running = False
        if self.async_thread and self.async_thread.is_alive():
            self.async_thread.join(timeout=1.0)
            self.logger.info("事件管理器异步处理线程已停止")
    
    def register_event_type(self, event_type: EventType) -> None:
        """注册事件类型
        
        Args:
            event_type: 事件类型
        """
        self.registered_event_types.add(event_type)
    
    def register_event_types(self, event_types: List[EventType]) -> None:
        """批量注册事件类型
        
        Args:
            event_types: 事件类型列表
        """
        for event_type in event_types:
            self.register_event_type(event_type)
    
    def is_event_type_registered(self, event_type: EventType) -> bool:
        """检查事件类型是否已注册
        
        Args:
            event_type: 事件类型
            
        Returns:
            bool: 是否已注册
        """
        return event_type in self.registered_event_types
    
    def subscribe(
            self,
            event_type: EventType,
            handler: Union[EventHandler, AsyncEventHandler],
            priority: EventPriority = EventPriority.NORMAL,
            filters: Optional[List[EventFilter]] = None,
            is_async: bool = False,
            throttle: Optional[Tuple[ThrottleMode, float]] = None,
            once: bool = False
    ) -> EventSubscription:
        """订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
            priority: 事件优先级
            filters: 事件过滤器列表
            is_async: 是否为异步处理器
            throttle: 事件节流设置，格式为(模式, 间隔秒数)
            once: 是否只触发一次
            
        Returns:
            EventSubscription: 事件订阅对象
        """
        subscription = EventSubscription(
            handler=handler,
            event_type=event_type,
            priority=priority,
            filters=filters,
            is_async=is_async,
            throttle=throttle,
            once=once
        )
        
        if event_type == "*":
            # 通配符订阅
            self.wildcard_subscriptions.append(subscription)
            self.wildcard_subscriptions.sort(key=lambda s: s.priority.value)
        else:
            # 特定事件类型订阅
            if event_type not in self.subscriptions:
                self.subscriptions[event_type] = []
            
            self.subscriptions[event_type].append(subscription)
            self.subscriptions[event_type].sort(key=lambda s: s.priority.value)
        
        self.logger.debug(f"已订阅事件: {event_type}")
        return subscription
    
    def unsubscribe(self, subscription: EventSubscription) -> bool:
        """取消事件订阅
        
        Args:
            subscription: 事件订阅对象
            
        Returns:
            bool: 是否成功取消
        """
        event_type = subscription.event_type
        
        if event_type == "*":
            # 通配符订阅
            if subscription in self.wildcard_subscriptions:
                self.wildcard_subscriptions.remove(subscription)
                self.logger.debug("已取消通配符事件订阅")
                return True
        elif event_type in self.subscriptions:
            # 特定事件类型订阅
            if subscription in self.subscriptions[event_type]:
                self.subscriptions[event_type].remove(subscription)
                if not self.subscriptions[event_type]:
                    del self.subscriptions[event_type]
                self.logger.debug(f"已取消事件订阅: {event_type}")
                return True
        
        self.logger.warning(f"尝试取消不存在的事件订阅: {event_type}")
        return False
    
    def unsubscribe_all(self, event_type: Optional[EventType] = None) -> None:
        """取消所有事件订阅
        
        Args:
            event_type: 如果提供，则只取消指定事件类型的订阅
        """
        if event_type is None:
            # 取消所有订阅
            self.subscriptions.clear()
            self.wildcard_subscriptions.clear()
            self.logger.debug("已取消所有事件订阅")
        elif event_type == "*":
            # 取消所有通配符订阅
            self.wildcard_subscriptions.clear()
            self.logger.debug("已取消所有通配符事件订阅")
        elif event_type in self.subscriptions:
            # 取消特定事件类型的订阅
            del self.subscriptions[event_type]
            self.logger.debug(f"已取消所有 {event_type} 事件订阅")
    
    def emit(self, event_type: EventType, event_data: Optional[EventData] = None) -> None:
        """发出事件
        
        Args:
            event_type: 事件类型
            event_data: 事件数据
        """
        if event_data is None:
            event_data = {}
        
        # 记录日志
        self.logger.debug(f"发出事件: {event_type} {event_data}")
        
        # 收集需要处理的订阅
        to_process = []
        
        # 添加特定事件类型的订阅
        if event_type in self.subscriptions:
            to_process.extend(self.subscriptions[event_type])
        
        # 添加通配符订阅
        to_process.extend(self.wildcard_subscriptions)
        
        # 按优先级排序
        to_process.sort(key=lambda s: s.priority.value)
        
        # 收集需要移除的订阅
        to_remove = []
        
        # 处理每个订阅
        for subscription in to_process:
            if subscription.matches(event_type, event_data):
                # 检查是否需要节流
                if subscription.should_throttle():
                    # 根据节流模式处理
                    mode, _ = subscription.throttle
                    if mode == ThrottleMode.FIRST:
                        # 保持第一个事件，忽略后续事件
                        continue
                    elif mode == ThrottleMode.LAST:
                        # 替换为最新事件
                        subscription.queued_event = (event_type, event_data.copy())
                        continue
                    elif mode == ThrottleMode.RATE:
                        # 将事件放入队列，稍后处理
                        subscription.queued_event = (event_type, event_data.copy())
                        continue
                
                # 处理事件
                self._process_subscription(subscription, event_type, event_data)
                
                # 如果是一次性订阅，添加到移除列表
                if subscription.once:
                    to_remove.append(subscription)
        
        # 移除一次性订阅
        for subscription in to_remove:
            self.unsubscribe(subscription)
    
    def _process_subscription(
            self,
            subscription: EventSubscription,
            event_type: EventType,
            event_data: EventData
    ) -> None:
        """处理单个订阅的事件
        
        Args:
            subscription: 事件订阅
            event_type: 事件类型
            event_data: 事件数据
        """
        try:
            if subscription.is_async:
                # 异步处理
                self.async_event_queue.put((subscription, event_type, event_data.copy()))
            else:
                # 同步处理
                subscription.handler(event_type, event_data)
        except Exception as e:
            self.logger.error(f"处理事件 {event_type} 时出错: {str(e)}", exc_info=True)
    
    def _process_async_events(self) -> None:
        """处理异步事件队列中的事件"""
        while self.running:
            try:
                # 从队列中获取事件，最多等待0.5秒
                subscription, event_type, event_data = self.async_event_queue.get(timeout=0.5)
                
                try:
                    # 提交到线程池执行
                    self.thread_pool.submit(subscription.handler, event_type, event_data)
                except Exception as e:
                    self.logger.error(f"异步处理事件 {event_type} 时出错: {str(e)}", exc_info=True)
                
                # 标记任务完成
                self.async_event_queue.task_done()
            except Empty:
                # 队列为空，继续等待
                continue
            except Exception as e:
                self.logger.error(f"异步事件处理线程出错: {str(e)}", exc_info=True)
    
    def process_throttled_events(self) -> None:
        """处理节流队列中的事件
        
        此方法应定期调用，以处理使用RATE模式节流的事件
        """
        for event_type, subscriptions in self.subscriptions.items():
            for subscription in subscriptions:
                if subscription.throttle and subscription.queued_event:
                    mode, interval = subscription.throttle
                    current_time = time.time()
                    
                    if current_time - subscription.last_fired_time >= interval:
                        # 可以处理下一个事件了
                        queued_type, queued_data = subscription.queued_event
                        self._process_subscription(subscription, queued_type, queued_data)
                        subscription.last_fired_time = current_time
                        subscription.queued_event = None
                        subscription.is_throttled = False
        
        # 处理通配符订阅的节流事件
        for subscription in self.wildcard_subscriptions:
            if subscription.throttle and subscription.queued_event:
                mode, interval = subscription.throttle
                current_time = time.time()
                
                if current_time - subscription.last_fired_time >= interval:
                    # 可以处理下一个事件了
                    queued_type, queued_data = subscription.queued_event
                    self._process_subscription(subscription, queued_type, queued_data)
                    subscription.last_fired_time = current_time
                    subscription.queued_event = None
                    subscription.is_throttled = False
    
    def get_subscription_count(self, event_type: Optional[EventType] = None) -> int:
        """获取事件订阅数量
        
        Args:
            event_type: 如果提供，则只计算指定事件类型的订阅数量
            
        Returns:
            int: 订阅数量
        """
        if event_type is None:
            # 计算所有订阅数量
            count = len(self.wildcard_subscriptions)
            for subs in self.subscriptions.values():
                count += len(subs)
            return count
        elif event_type == "*":
            # 计算通配符订阅数量
            return len(self.wildcard_subscriptions)
        elif event_type in self.subscriptions:
            # 计算特定事件类型的订阅数量
            return len(self.subscriptions[event_type])
        else:
            return 0 