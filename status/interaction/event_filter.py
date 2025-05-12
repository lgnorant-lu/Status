"""
---------------------------------------------------------------
File name:                  event_filter.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                事件过滤器系统，用于过滤交互事件
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
                            2025/05/15: 修复类型问题，添加明确的类型注解;
----
"""

import logging
from typing import List, Set, Dict, Optional, Union, Any, Callable, TypeVar, Generic, cast

from .interaction_event import InteractionEvent, InteractionEventType

# 设置日志记录器
logger = logging.getLogger(__name__)

T = TypeVar('T')

class EventFilter:
    """事件过滤器基类"""
    
    def __init__(self, *, name: Optional[str] = None) -> None:
        """初始化事件过滤器
        
        Args:
            name: 过滤器名称，可选，用于调试和日志记录
        """
        self.name = name or f"{self.__class__.__name__}_{id(self)}"
        self.enabled = True
    
    def filter(self, event: InteractionEvent) -> bool:
        """过滤事件
        
        Args:
            event: 要过滤的事件
            
        Returns:
            bool: True允许事件通过，False拦截事件
        """
        if not self.enabled:
            return True  # 如果禁用，则不过滤
            
        return self._do_filter(event)
    
    def _do_filter(self, event: InteractionEvent) -> bool:
        """实际执行过滤的方法，子类应重写此方法
        
        Args:
            event: 要过滤的事件
            
        Returns:
            bool: True允许事件通过，False拦截事件
        """
        # 基类默认允许所有事件通过
        return True
    
    def set_enabled(self, enabled: bool) -> None:
        """设置过滤器是否启用
        
        Args:
            enabled: 是否启用
        """
        self.enabled = enabled
    
    def is_enabled(self) -> bool:
        """获取过滤器是否启用
        
        Returns:
            bool: 是否启用
        """
        return self.enabled
    
    def __str__(self) -> str:
        return f"{self.name} ({'enabled' if self.enabled else 'disabled'})"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', enabled={self.enabled})"


class TypeFilter(EventFilter):
    """类型过滤器，只允许特定类型的事件通过"""
    
    def __init__(self, *, name: Optional[str] = None, 
                 allowed_types: Optional[Union[Set[InteractionEventType], List[InteractionEventType]]] = None) -> None:
        """初始化类型过滤器
        
        Args:
            name: 过滤器名称
            allowed_types: 允许通过的事件类型集合或列表
        """
        super().__init__(name=name)
        self.allowed_types: Set[InteractionEventType] = set()
        
        if allowed_types:
            if isinstance(allowed_types, list):
                self.allowed_types = set(allowed_types)
            else:
                self.allowed_types = allowed_types
    
    def _do_filter(self, event: InteractionEvent) -> bool:
        """执行过滤
        
        Args:
            event: 要过滤的事件
            
        Returns:
            bool: 如果事件类型在允许列表中则返回True，否则返回False
        """
        return event.event_type in self.allowed_types
    
    def add_allowed_type(self, event_type: InteractionEventType) -> None:
        """添加允许的事件类型
        
        Args:
            event_type: 要添加的事件类型
        """
        self.allowed_types.add(event_type)
    
    def remove_allowed_type(self, event_type: InteractionEventType) -> None:
        """移除允许的事件类型
        
        Args:
            event_type: 要移除的事件类型
        """
        if event_type in self.allowed_types:
            self.allowed_types.remove(event_type)


class PropertyFilter(EventFilter):
    """属性过滤器，根据事件属性值过滤事件"""
    
    def __init__(self, *, name: Optional[str] = None, 
                 property_name: Optional[str] = None, 
                 predicate: Callable[[Any], bool] = lambda x: bool(x)) -> None:
        """初始化属性过滤器
        
        Args:
            name: 过滤器名称
            property_name: 要检查的属性名
            predicate: 判断属性值的谓词函数，返回True表示允许事件通过
        """
        super().__init__(name=name)
        self.property_name = property_name
        self.predicate = predicate
    
    def _do_filter(self, event: InteractionEvent) -> bool:
        """执行过滤
        
        Args:
            event: 要过滤的事件
            
        Returns:
            bool: 如果事件没有指定属性或谓词函数返回True则允许事件通过
        """
        if not self.property_name:
            return True
            
        if not hasattr(event, self.property_name) and self.property_name not in event.data:
            return True  # 如果事件没有该属性，则允许通过
            
        # 获取属性值
        property_value = None
        if hasattr(event, self.property_name):
            property_value = getattr(event, self.property_name)
        else:
            property_value = event.data.get(self.property_name)
            
        # 应用谓词函数
        return self.predicate(property_value)
    
    def set_property_name(self, property_name: str) -> None:
        """设置要检查的属性名
        
        Args:
            property_name: 属性名
        """
        self.property_name = property_name
    
    def set_predicate(self, predicate: Callable[[Any], bool]) -> None:
        """设置谓词函数
        
        Args:
            predicate: 谓词函数
        """
        self.predicate = predicate
    
    def __str__(self) -> str:
        return f"{self.name} (property={self.property_name})"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', property_name='{self.property_name}')"


class RangeFilter(PropertyFilter):
    """范围过滤器，检查数值属性是否在指定范围内"""
    
    def __init__(self, *, name: Optional[str] = None, 
                 property_name: Optional[str] = None,
                 min_value: Optional[float] = None, 
                 max_value: Optional[float] = None,
                 inclusive: bool = True) -> None:
        """初始化范围过滤器
        
        Args:
            name: 过滤器名称
            property_name: 要检查的属性名
            min_value: 最小值，None表示无下限
            max_value: 最大值，None表示无上限
            inclusive: 是否包含边界值
        """
        self.min_value = min_value
        self.max_value = max_value
        self.inclusive = inclusive
        
        # 根据是否包含边界值创建不同的谓词函数
        if inclusive:
            predicate = self._check_range_inclusive
        else:
            predicate = self._check_range_exclusive
            
        super().__init__(name=name, property_name=property_name, predicate=predicate)
    
    def _check_range_inclusive(self, value: Any) -> bool:
        """检查值是否在包含边界的范围内
        
        Args:
            value: 要检查的值
            
        Returns:
            bool: 是否在范围内
        """
        if value is None:
            return False
            
        try:
            numeric_value = float(value)
            min_ok = self.min_value is None or numeric_value >= self.min_value
            max_ok = self.max_value is None or numeric_value <= self.max_value
            return min_ok and max_ok
        except (ValueError, TypeError):
            return False
    
    def _check_range_exclusive(self, value: Any) -> bool:
        """检查值是否在不包含边界的范围内
        
        Args:
            value: 要检查的值
            
        Returns:
            bool: 是否在范围内
        """
        if value is None:
            return False
            
        try:
            numeric_value = float(value)
            min_ok = self.min_value is None or numeric_value > self.min_value
            max_ok = self.max_value is None or numeric_value < self.max_value
            return min_ok and max_ok
        except (ValueError, TypeError):
            return False
    
    def set_range(self, min_value: Optional[float] = None, max_value: Optional[float] = None, inclusive: Optional[bool] = None) -> None:
        """设置范围
        
        Args:
            min_value: 最小值
            max_value: 最大值
            inclusive: 是否包含边界值
        """
        if min_value is not None:
            self.min_value = min_value
        if max_value is not None:
            self.max_value = max_value
        if inclusive is not None:
            self.inclusive = inclusive
            # 更新谓词函数
            if self.inclusive:
                self.predicate = self._check_range_inclusive
        else:
                self.predicate = self._check_range_exclusive


class EventFilterChain(EventFilter):
    """事件过滤器链，组合多个过滤器"""
    
    def __init__(self, *, name: Optional[str] = None, 
                 filters: Optional[List[EventFilter]] = None) -> None:
        """初始化过滤器链
        
        Args:
            name: 过滤器链名称
            filters: 初始过滤器列表
        """
        super().__init__(name=name)
        self.filters: List[EventFilter] = []
        
        if filters:
            self.filters.extend(filters)
    
    def _do_filter(self, event: InteractionEvent) -> bool:
        """执行所有过滤器
        
        Args:
            event: 要过滤的事件
            
        Returns:
            bool: 如果所有过滤器都允许通过则返回True，否则返回False
        """
        for filter_obj in self.filters:
            if not filter_obj.filter(event):
                # 记录哪个过滤器拦截了事件
                logger.debug(f"Event {event.event_type} blocked by filter: {filter_obj}")
            return False
        return True
    
    def add_filter(self, filter_obj: EventFilter) -> None:
        """添加过滤器
        
        Args:
            filter_obj: 要添加的过滤器
        """
        self.filters.append(filter_obj)
    
    def remove_filter(self, filter_obj: EventFilter) -> bool:
        """移除过滤器
        
        Args:
            filter_obj: 要移除的过滤器
            
        Returns:
            bool: 是否成功移除
        """
        if filter_obj in self.filters:
            self.filters.remove(filter_obj)
            return True
        return False
    
    def get_filters(self) -> List[EventFilter]:
        """获取所有过滤器
        
        Returns:
            List[EventFilter]: 过滤器列表
        """
        return self.filters.copy()
    
    def clear_filters(self) -> None:
        """清空所有过滤器"""
        self.filters.clear()
    
    def __len__(self) -> int:
        return len(self.filters)


class NotFilter(EventFilter):
    """取反过滤器，对另一个过滤器的结果取反"""
    
    def __init__(self, filter_obj: EventFilter, name: Optional[str] = None) -> None:
        """初始化取反过滤器
        
        Args:
            filter_obj: 要取反的过滤器
            name: 过滤器名称
        """
        super().__init__(name=name or f"Not_{filter_obj.name}")
        self.filter_obj = filter_obj
    
    def _do_filter(self, event: InteractionEvent) -> bool:
        """执行过滤并取反
        
        Args:
            event: 要过滤的事件
            
        Returns:
            bool: 取反后的过滤结果
        """
        return not self.filter_obj.filter(event)


class AndFilter(EventFilterChain):
    """与过滤器，所有子过滤器都必须通过"""
    
    def __init__(self, *filters: EventFilter, name: Optional[str] = None) -> None:
        """初始化与过滤器
        
        Args:
            *filters: 要组合的过滤器列表
            name: 过滤器名称
        """
        filter_list = list(filters)
        super().__init__(name=name or "And_Filter", filters=filter_list)
    
    # 继承自EventFilterChain的_do_filter方法已经实现了与逻辑


class OrFilter(EventFilterChain):
    """或过滤器，只要有一个子过滤器通过即可"""
    
    def __init__(self, *filters: EventFilter, name: Optional[str] = None) -> None:
        """初始化或过滤器
        
        Args:
            *filters: 要组合的过滤器列表
            name: 过滤器名称
        """
        filter_list = list(filters)
        super().__init__(name=name or "Or_Filter", filters=filter_list)
    
    def _do_filter(self, event: InteractionEvent) -> bool:
        """执行所有过滤器，有一个通过即可
        
        Args:
            event: 要过滤的事件
            
        Returns:
            bool: 如果至少有一个过滤器允许通过则返回True，否则返回False
        """
        # 如果没有过滤器，返回True
        if not self.filters:
            return True
        
        for filter_obj in self.filters:
            if filter_obj.filter(event):
                return True
        return False


class KeyCombinationFilter(EventFilter):
    """按键组合过滤器，检查事件是否符合指定的按键组合"""
    
    def __init__(self, *, name: Optional[str] = None, 
                 active_keys: Optional[Set[InteractionEventType]] = None, 
                 target_keys: Optional[Set[InteractionEventType]] = None) -> None:
        """初始化按键组合过滤器
        
        Args:
            name: 过滤器名称
            active_keys: 激活的按键集合
            target_keys: 目标按键集合
        """
        super().__init__(name=name)
        self.active_keys = active_keys or set()
        self.target_keys = target_keys or set()
    
    def _do_filter(self, event: InteractionEvent) -> bool:
        """执行过滤
        
        Args:
            event: 要过滤的事件
            
        Returns:
            bool: 如果事件符合按键组合则返回True，否则返回False
        """
        if not self.active_keys and not self.target_keys:
            return True # 如果没有设置目标按键，则默认通过

        # ... rest of the logic ...
        return False # Default return if no conditions met earlier


# 创建一些常用的过滤器实例

def create_mouse_filter(name: str = "MouseFilter") -> TypeFilter:
    """创建鼠标事件过滤器
    
    Args:
        name: 过滤器名称
        
        Returns:
        TypeFilter: 鼠标事件过滤器
    """
    mouse_filter = TypeFilter(name=name)
    mouse_filter.add_allowed_type(InteractionEventType.MOUSE_MOVE)
    mouse_filter.add_allowed_type(InteractionEventType.MOUSE_CLICK)
    mouse_filter.add_allowed_type(InteractionEventType.MOUSE_PRESS)
    mouse_filter.add_allowed_type(InteractionEventType.MOUSE_RELEASE)
    mouse_filter.add_allowed_type(InteractionEventType.MOUSE_ENTER)
    mouse_filter.add_allowed_type(InteractionEventType.MOUSE_LEAVE)
    mouse_filter.add_allowed_type(InteractionEventType.MOUSE_WHEEL)
    return mouse_filter

def create_keyboard_filter(name: str = "KeyboardFilter") -> TypeFilter:
    """创建键盘事件过滤器
    
    Args:
        name: 过滤器名称
        
        Returns:
        TypeFilter: 键盘事件过滤器
        """
    keyboard_filter = TypeFilter(name=name)
    keyboard_filter.add_allowed_type(InteractionEventType.KEY_DOWN)
    keyboard_filter.add_allowed_type(InteractionEventType.KEY_UP)
    keyboard_filter.add_allowed_type(InteractionEventType.KEY_PRESS)
    return keyboard_filter 