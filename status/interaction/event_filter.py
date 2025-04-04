"""
---------------------------------------------------------------
File name:                  event_filter.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                事件过滤器，用于过滤不需要处理的事件
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable, Union, Set

from .interaction_event import InteractionEvent, InteractionEventType

# 获取日志记录器
logger = logging.getLogger(__name__)


class EventFilter(ABC):
    """事件过滤器基类，定义过滤器接口"""
    
    def __init__(self, name: str = None):
        """初始化过滤器
        
        Args:
            name: 过滤器名称，用于日志和调试
        """
        self.name = name or self.__class__.__name__
        self.is_enabled = True  # 过滤器是否启用
        self.process_when_disabled = True  # 当过滤器禁用时是否处理事件
        logger.debug(f"创建事件过滤器: {self.name}")
    
    def enable(self):
        """启用过滤器"""
        self.is_enabled = True
        logger.debug(f"启用过滤器: {self.name}")
    
    def disable(self):
        """禁用过滤器"""
        self.is_enabled = False
        logger.debug(f"禁用过滤器: {self.name}")
    
    @abstractmethod
    def filter(self, event: InteractionEvent) -> bool:
        """过滤事件
        
        Args:
            event: 要过滤的交互事件
            
        Returns:
            bool: 如果事件应该继续处理返回True，否则返回False
        """
        pass
    
    def should_process(self, event: InteractionEvent) -> bool:
        """判断是否应该处理此事件
        
        如果过滤器被禁用，根据process_when_disabled决定是否处理
        
        Args:
            event: 要判断的交互事件
            
        Returns:
            bool: 如果应该处理返回True，否则返回False
        """
        if not self.is_enabled:
            return self.process_when_disabled
        
        return self.filter(event)
    
    def __str__(self) -> str:
        status = "启用" if self.is_enabled else "禁用"
        return f"{self.name} [{status}]"


class EventTypeFilter(EventFilter):
    """基于事件类型的过滤器"""
    
    def __init__(self, name: str = None, allowed_types: Union[Set[InteractionEventType], List[InteractionEventType]] = None):
        """初始化事件类型过滤器
        
        Args:
            name: 过滤器名称
            allowed_types: 允许处理的事件类型列表或集合
        """
        super().__init__(name)
        self.allowed_types = set(allowed_types) if allowed_types else set()
        logger.debug(f"事件类型过滤器 '{self.name}' 允许类型: {[t.name for t in self.allowed_types]}")
    
    def filter(self, event: InteractionEvent) -> bool:
        """检查事件类型是否在允许列表中
        
        Args:
            event: 要检查的交互事件
            
        Returns:
            bool: 如果事件类型在允许列表中返回True，否则返回False
        """
        result = event.event_type in self.allowed_types
        if not result:
            logger.debug(f"事件类型过滤器 '{self.name}' 拦截事件: {event.event_type}")
        return result


class EventPropertyFilter(EventFilter):
    """基于事件属性值的过滤器"""
    
    def __init__(self, name: str = None, property_name: str = None, property_value: Any = None, 
                 comparison: str = 'eq'):
        """初始化事件属性过滤器
        
        Args:
            name: 过滤器名称
            property_name: 属性名称，可以是嵌套属性，如 "data.x"
            property_value: 用于比较的属性值
            comparison: 比较方式，支持 'eq'(等于), 'ne'(不等于), 'gt'(大于), 
                        'lt'(小于), 'ge'(大于等于), 'le'(小于等于), 'in'(包含于), 
                        'contains'(包含), 'startswith'(以...开头), 'endswith'(以...结尾)
        """
        super().__init__(name)
        self.property_name = property_name
        self.property_value = property_value
        self.comparison = comparison
        
        # 验证比较方式是否有效
        valid_comparisons = ['eq', 'ne', 'gt', 'lt', 'ge', 'le', 'in', 'contains', 
                             'startswith', 'endswith', '==', '!=', '>', '<', '>=', '<=']
                             
        # 标准化比较运算符
        if comparison == '==':
            self.comparison = 'eq'
        elif comparison == '!=':
            self.comparison = 'ne'
        elif comparison == '>':
            self.comparison = 'gt'
        elif comparison == '<':
            self.comparison = 'lt'
        elif comparison == '>=':
            self.comparison = 'ge'
        elif comparison == '<=':
            self.comparison = 'le'
        
        if self.comparison not in valid_comparisons:
            raise ValueError(f"无效的比较方式: {comparison}. 有效值: {valid_comparisons}")
        
        logger.debug(f"事件属性过滤器 '{self.name}' 条件: {property_name} {comparison} {property_value}")
    
    def filter(self, event: InteractionEvent) -> bool:
        """检查事件的指定属性是否满足条件
        
        Args:
            event: 要检查的交互事件
            
        Returns:
            bool: 如果事件属性满足条件返回True，否则返回False
        """
        # 获取属性值，支持嵌套属性
        value = self._get_property_value(event)
        
        # 如果属性不存在，返回False
        if value is None:
            return False
        
        # 根据比较方式进行比较
        result = False
        try:
            if self.comparison == 'eq':
                result = value == self.property_value
            elif self.comparison == 'ne':
                result = value != self.property_value
            elif self.comparison == 'gt':
                result = value > self.property_value
            elif self.comparison == 'lt':
                result = value < self.property_value
            elif self.comparison == 'ge':
                result = value >= self.property_value
            elif self.comparison == 'le':
                result = value <= self.property_value
            elif self.comparison == 'in':
                result = value in self.property_value
            elif self.comparison == 'contains':
                result = self.property_value in value
            elif self.comparison == 'startswith':
                result = value.startswith(self.property_value)
            elif self.comparison == 'endswith':
                result = value.endswith(self.property_value)
        except (TypeError, AttributeError):
            # 如果比较出错，返回False
            logger.debug(f"事件属性过滤器 '{self.name}' 比较出错: 无法将 {value} 与 {self.property_value} 进行 {self.comparison} 比较")
            return False
        
        if not result:
            logger.debug(f"事件属性过滤器 '{self.name}' 拦截事件: {self.property_name}={value}")
        return result
    
    def _get_property_value(self, event: InteractionEvent) -> Any:
        """获取事件的指定属性值
        
        Args:
            event: 交互事件
            
        Returns:
            Any: 属性值，如果属性不存在则返回None
        """
        # 处理嵌套属性，如 "data.x"
        parts = self.property_name.split('.')
        value = event
        
        for part in parts:
            # 对于字典类型的属性
            if isinstance(value, dict) and part in value:
                value = value[part]
            # 对于对象属性
            elif hasattr(value, part):
                value = getattr(value, part)
            # 属性不存在
            else:
                logger.debug(f"属性 '{part}' 在 {value} 中不存在")
                return None
        
        return value


class CompositeFilter(EventFilter):
    """组合多个过滤器的复合过滤器"""
    
    def __init__(self, name: str = None, filters: List[EventFilter] = None, mode: str = 'AND'):
        """初始化复合过滤器
        
        Args:
            name: 过滤器名称
            filters: 过滤器列表
            mode: 组合模式，'AND'表示所有过滤器都通过才通过，'OR'表示任一过滤器通过即可
        """
        super().__init__(name)
        self.filters = filters or []
        self.mode = mode.upper()
        
        logger.debug(f"复合过滤器 '{self.name}' 创建: 模式={self.mode}, 包含{len(self.filters)}个过滤器")
    
    def filter(self, event: InteractionEvent) -> bool:
        """根据组合模式检查所有子过滤器
        
        Args:
            event: 要检查的交互事件
            
        Returns:
            bool: 根据组合模式返回结果
        """
        if not self.filters:
            logger.debug(f"复合过滤器 '{self.name}' 没有子过滤器，默认放行")
            return True
        
        if self.mode == 'AND':
            # 所有过滤器都必须通过
            for f in self.filters:
                if not f.should_process(event):
                    logger.debug(f"复合过滤器 '{self.name}' (AND) 拦截事件: 子过滤器 '{f.name}' 拦截")
                    return False
            return True
            
        elif self.mode == 'OR':
            # 任一过滤器通过即可
            for f in self.filters:
                if f.should_process(event):
                    return True
            logger.debug(f"复合过滤器 '{self.name}' (OR) 拦截事件: 没有子过滤器通过")
            return False
            
        else:
            logger.warning(f"复合过滤器 '{self.name}' 使用了未知的模式: {self.mode}，默认放行")
            return True


class EventFilterChain:
    """管理多个事件过滤器的过滤器链"""
    
    def __init__(self, name: str = "EventFilterChain"):
        """初始化过滤器链
        
        Args:
            name: 过滤器链名称
        """
        self.name = name
        self.filters: List[EventFilter] = []
        self.stats = {
            "total_processed": 0,
            "total_filtered": 0,
            "filters": {}  # 各过滤器统计
        }
        logger.debug(f"事件过滤器链 '{name}' 创建")
    
    def add_filter(self, filter: EventFilter) -> bool:
        """向过滤器链添加过滤器
        
        Args:
            filter: 要添加的过滤器
            
        Returns:
            bool: 添加成功返回True
        """
        if filter in self.filters:
            logger.warning(f"过滤器 '{filter.name}' 已存在于过滤器链 '{self.name}' 中")
            return False
            
        self.filters.append(filter)
        self.stats["filters"][filter.name] = {"processed": 0, "filtered": 0}
        logger.debug(f"过滤器 '{filter.name}' 添加到过滤器链 '{self.name}'")
        return True
    
    def remove_filter(self, filter_or_name) -> bool:
        """从过滤器链移除过滤器
        
        Args:
            filter_or_name: 要移除的过滤器对象或名称
            
        Returns:
            bool: 移除成功返回True
        """
        # 如果传入的是过滤器名称，查找对应的过滤器对象
        if isinstance(filter_or_name, str):
            filter_name = filter_or_name
            for f in self.filters:
                if f.name == filter_name:
                    self.filters.remove(f)
                    logger.debug(f"过滤器 '{filter_name}' 从过滤器链 '{self.name}' 中移除")
                    return True
            logger.warning(f"过滤器 '{filter_name}' 不存在于过滤器链 '{self.name}' 中")
            return False
        else:
            # 传入的是过滤器对象
            filter = filter_or_name
            if filter in self.filters:
                self.filters.remove(filter)
                logger.debug(f"过滤器 '{filter.name}' 从过滤器链 '{self.name}' 中移除")
                return True
            else:
                logger.warning(f"过滤器 '{filter.name}' 不存在于过滤器链 '{self.name}' 中")
                return False
    
    def clear_filters(self) -> None:
        """清空过滤器链中的所有过滤器"""
        count = len(self.filters)
        self.filters.clear()
        self.stats["filters"] = {}
        logger.debug(f"过滤器链 '{self.name}' 已清空，移除了 {count} 个过滤器")
    
    def get_filters(self) -> List[EventFilter]:
        """获取过滤器链中的所有过滤器
        
        Returns:
            List[EventFilter]: 过滤器列表
        """
        return self.filters.copy()
    
    def should_process(self, event: InteractionEvent) -> bool:
        """检查事件是否应该被处理
        
        按顺序检查所有过滤器，只有所有过滤器都返回True，事件才会被处理
        
        Args:
            event: 要检查的交互事件
            
        Returns:
            bool: 如果事件应该被处理返回True
        """
        self.stats["total_processed"] += 1
        
        # 如果没有过滤器，默认通过
        if not self.filters:
            return True
        
        # 所有过滤器都必须通过
        for filter in self.filters:
            if not filter.is_enabled:
                # 跳过禁用的过滤器
                continue
                
            # 更新统计信息
            if filter.name in self.stats["filters"]:
                self.stats["filters"][filter.name]["processed"] += 1
            
            if not filter.should_process(event):
                # 如果任一过滤器不通过，事件将被过滤
                logger.debug(f"事件 {event} 被过滤器 '{filter.name}' 过滤")
                
                # 更新统计信息
                self.stats["total_filtered"] += 1
                if filter.name in self.stats["filters"]:
                    self.stats["filters"][filter.name]["filtered"] += 1
                
                return False
        
        # 所有过滤器都通过
        return True
    
    def get_stats(self) -> dict:
        """获取过滤器链的统计信息
        
        Returns:
            dict: 过滤器链的统计信息
        """
        # 计算通过率
        total = self.stats["total_processed"]
        filtered = self.stats["total_filtered"]
        pass_rate = 1.0 if total == 0 else (total - filtered) / total
        
        # 返回详细统计信息
        return {
            "total_processed": total,
            "total_filtered": filtered,
            "pass_rate": pass_rate,
            "filters": self.stats["filters"]
        }
        
    def __str__(self) -> str:
        """返回过滤器链的字符串表示
        
        Returns:
            str: 过滤器链的字符串表示
        """
        return f"{self.name} ({len(self.filters)} 个过滤器)" 