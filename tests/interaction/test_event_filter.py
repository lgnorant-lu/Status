"""
---------------------------------------------------------------
File name:                  test_event_filter.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                事件过滤器测试
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import unittest
import time
from unittest.mock import Mock, patch

# 导入测试配置，确保模拟模块已设置
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import tests.conftest

from status.interaction.event_filter import (
    EventFilter, TypeFilter, PropertyFilter,
    EventFilterChain, AndFilter, OrFilter, RangeFilter
)
from status.interaction.interaction_event import InteractionEvent, InteractionEventType


class MockEventFilter(EventFilter):
    """用于测试的模拟过滤器"""
    
    def __init__(self, name="MockFilter", should_pass=True, enabled=True):
        super().__init__(name=name)
        self.should_pass = should_pass
        self.filtered_events = []
        self.set_enabled(enabled) # 使用基类方法设置 enabled 状态

    def _do_filter(self, event: InteractionEvent) -> bool:
        """模拟执行过滤的方法，子类应重写此方法
        
        Args:
            event: 要过滤的事件
            
        Returns:
            bool: True允许事件通过，False拦截事件
        """
        # 记录被过滤的事件
        self.filtered_events.append(event)
        return self.should_pass


class TestEventFilter(unittest.TestCase):
    """事件过滤器基类测试"""
    
    def test_initialization(self):
        """测试过滤器初始化"""
        filter = MockEventFilter("TestFilter")
        self.assertEqual(filter.name, "TestFilter")
        self.assertTrue(filter.is_enabled())
    
    def test_enable_disable(self):
        """测试启用和禁用功能"""
        filter = MockEventFilter()
        self.assertTrue(filter.is_enabled())
        
        filter.set_enabled(False) # 使用 set_enabled
        self.assertFalse(filter.is_enabled())
        
        filter.set_enabled(True) # 使用 set_enabled
        self.assertTrue(filter.is_enabled())
    
    def test_filter_when_disabled(self):
        """测试禁用时的过滤行为"""
        # 当过滤器禁用时，EventFilter.filter 应该直接返回 True，不调用 _do_filter
        filter = MockEventFilter(should_pass=False, enabled=False)
        
        event = InteractionEvent(InteractionEventType.MOUSE_CLICK)
        # 当过滤器禁用时，EventFilter.filter 应该返回 True
        self.assertTrue(filter.filter(event))
        # 验证 _do_filter 方法没有被调用
        self.assertEqual(len(filter.filtered_events), 0)
        
    # 移除了与 should_process 和 stats 相关的测试


class TestTypeFilter(unittest.TestCase):
    """事件类型过滤器测试"""
    
    def test_initialization(self):
        """测试类型过滤器初始化"""
        allowed_types = {
            InteractionEventType.MOUSE_CLICK,
            InteractionEventType.MOUSE_DOUBLE_CLICK
        }
        filter = TypeFilter(name="TypeFilter", allowed_types=list(allowed_types))
        self.assertEqual(filter.name, "TypeFilter")
        self.assertEqual(filter.allowed_types, allowed_types)
    
    def test_filter_allowed_type(self):
        """测试允许的事件类型"""
        filter = TypeFilter(
            allowed_types={InteractionEventType.MOUSE_CLICK}
        )
        
        event = InteractionEvent(InteractionEventType.MOUSE_CLICK)
        self.assertTrue(filter.filter(event))
    
    def test_filter_blocked_type(self):
        """测试阻止的事件类型"""
        filter = TypeFilter(
            allowed_types={InteractionEventType.MOUSE_CLICK}
        )
        
        event = InteractionEvent(InteractionEventType.MOUSE_MOVE)
        self.assertFalse(filter.filter(event))


class TestPropertyFilter(unittest.TestCase):
    """事件属性过滤器测试"""
    
    def test_initialization(self):
        """测试属性过滤器初始化"""
        filter = PropertyFilter(
            name="PositionFilter",
            property_name="data.x",
            predicate=lambda x: x is not None and x > 0 # 示例谓词
        )
        self.assertEqual(filter.name, "PositionFilter")
        self.assertEqual(filter.property_name, "data.x")
        self.assertTrue(callable(filter.predicate))

    def test_predicate_filtering(self):
        """测试谓词过滤"""
        filter_gt_100 = PropertyFilter(
            property_name="value",
            predicate=lambda x: x is not None and float(x) > 100
        )
        event_pass = InteractionEvent(InteractionEventType.SYSTEM_EVENT, data={"value": 150})
        event_fail = InteractionEvent(InteractionEventType.SYSTEM_EVENT, data={"value": 50})
        event_none = InteractionEvent(InteractionEventType.SYSTEM_EVENT, data={"value": None})
        event_missing = InteractionEvent(InteractionEventType.SYSTEM_EVENT, data={})

        self.assertTrue(filter_gt_100.filter(event_pass))
        self.assertFalse(filter_gt_100.filter(event_fail))
        self.assertTrue(filter_gt_100.filter(event_missing))
        self.assertFalse(filter_gt_100.filter(event_none))


class TestEventFilterChain(unittest.TestCase):
    """事件过滤器链测试"""
    
    def test_initialization(self):
        """测试过滤器链初始化"""
        filter1 = MockEventFilter("Filter1")
        filter2 = MockEventFilter("Filter2")
        filter_chain = EventFilterChain(name="Chain", filters=[filter1, filter2])

        self.assertEqual(filter_chain.name, "Chain")
        self.assertEqual(len(filter_chain.filters), 2)
        self.assertIn(filter1, filter_chain.filters)
        self.assertIn(filter2, filter_chain.filters)
    
    def test_add_remove_filters(self):
        """测试添加和移除过滤器"""
        filter_chain = EventFilterChain()
        filter1 = MockEventFilter("Filter1")
        filter2 = MockEventFilter("Filter2")
        
        filter_chain.add_filter(filter1)
        self.assertEqual(len(filter_chain.filters), 1)
        self.assertIn(filter1, filter_chain.filters)

        filter_chain.add_filter(filter2)
        self.assertEqual(len(filter_chain.filters), 2)
        self.assertIn(filter2, filter_chain.filters)

        # 移除存在的过滤器
        removed = filter_chain.remove_filter(filter1)
        self.assertTrue(removed)
        self.assertEqual(len(filter_chain.filters), 1)
        self.assertNotIn(filter1, filter_chain.filters)
        self.assertIn(filter2, filter_chain.filters)
        
        # 尝试移除不存在的过滤器
        nonexistent_filter = MockEventFilter("Nonexistent")
        removed = filter_chain.remove_filter(nonexistent_filter)
        self.assertFalse(removed)
        self.assertEqual(len(filter_chain.filters), 1)
    
    def test_clear_filters(self):
        """测试清空过滤器"""
        filter1 = MockEventFilter("Filter1")
        filter_chain = EventFilterChain(filters=[filter1])

        self.assertEqual(len(filter_chain.filters), 1)

        filter_chain.clear_filters()
        self.assertEqual(len(filter_chain.filters), 0)

    def test_filter_logic(self):
        """测试过滤器链的AND逻辑 (EventFilterChain 默认是AND)"""
        filter1_pass = MockEventFilter("PassFilter1", should_pass=True)
        filter2_pass = MockEventFilter("PassFilter2", should_pass=True)
        filter3_fail = MockEventFilter("FailFilter3", should_pass=False)

        # 所有都通过
        chain_all_pass = EventFilterChain(filters=[filter1_pass, filter2_pass])
        event = InteractionEvent(InteractionEventType.SYSTEM_EVENT)
        self.assertTrue(chain_all_pass.filter(event))
        self.assertEqual(len(filter1_pass.filtered_events), 1)
        self.assertEqual(len(filter2_pass.filtered_events), 1)

        # 其中一个不通过
        chain_one_fail = EventFilterChain(filters=[filter1_pass, filter3_fail])
        event = InteractionEvent(InteractionEventType.SYSTEM_EVENT)
        self.assertFalse(chain_one_fail.filter(event))
        self.assertEqual(len(filter1_pass.filtered_events), 2) # 之前调用过一次
        self.assertEqual(len(filter3_fail.filtered_events), 1)


class TestAndOrFilter(unittest.TestCase):
    """AndFilter 和 OrFilter 测试"""

    def test_and_filter(self):
        """测试AndFilter"""
        filter1_pass = MockEventFilter("PassFilter1", should_pass=True)
        filter2_pass = MockEventFilter("PassFilter2", should_pass=True)
        filter3_fail = MockEventFilter("FailFilter3", should_pass=False)

        # 所有都通过
        and_filter_all_pass = AndFilter(filter1_pass, filter2_pass)
        event = InteractionEvent(InteractionEventType.SYSTEM_EVENT)
        self.assertTrue(and_filter_all_pass.filter(event))

        # 其中一个不通过
        and_filter_one_fail = AndFilter(filter1_pass, filter3_fail)
        event = InteractionEvent(InteractionEventType.SYSTEM_EVENT)
        self.assertFalse(and_filter_one_fail.filter(event))

    def test_or_filter(self):
        """测试OrFilter"""
        filter1_pass = MockEventFilter("PassFilter1", should_pass=True)
        filter2_fail = MockEventFilter("FailFilter2", should_pass=False)
        filter3_fail = MockEventFilter("FailFilter3", should_pass=False)

        # 其中一个通过
        or_filter_one_pass = OrFilter(filter1_pass, filter2_fail)
        event = InteractionEvent(InteractionEventType.SYSTEM_EVENT)
        self.assertTrue(or_filter_one_pass.filter(event))

        # 所有都不通过
        or_filter_all_fail = OrFilter(filter2_fail, filter3_fail)
        event = InteractionEvent(InteractionEventType.SYSTEM_EVENT)
        self.assertFalse(or_filter_all_fail.filter(event))


class TestRangeFilter(unittest.TestCase):
    """范围过滤器测试"""

    def test_initialization(self):
        """测试范围过滤器初始化"""
        filter = RangeFilter(
            name="RangeFilter",
            property_name="value",
            min_value=0,
            max_value=100,
            inclusive=True
        )
        self.assertEqual(filter.name, "RangeFilter")
        self.assertEqual(filter.property_name, "value")
        self.assertEqual(filter.min_value, 0)
        self.assertEqual(filter.max_value, 100)
        self.assertTrue(filter.inclusive)

    def test_inclusive_range(self):
        """测试包含边界的范围过滤"""
        filter = RangeFilter(property_name="value", min_value=0, max_value=100, inclusive=True)
        event_in = InteractionEvent(InteractionEventType.SYSTEM_EVENT, data={"value": 50})
        event_min = InteractionEvent(InteractionEventType.SYSTEM_EVENT, data={"value": 0})
        event_max = InteractionEvent(InteractionEventType.SYSTEM_EVENT, data={"value": 100})
        event_out_min = InteractionEvent(InteractionEventType.SYSTEM_EVENT, data={"value": -10})
        event_out_max = InteractionEvent(InteractionEventType.SYSTEM_EVENT, data={"value": 110})
        event_none = InteractionEvent(InteractionEventType.SYSTEM_EVENT, data={"value": None})
        event_missing = InteractionEvent(InteractionEventType.SYSTEM_EVENT, data={})

        self.assertTrue(filter.filter(event_in))
        self.assertTrue(filter.filter(event_min))
        self.assertTrue(filter.filter(event_max))
        self.assertFalse(filter.filter(event_out_min))
        self.assertFalse(filter.filter(event_out_max))
        self.assertFalse(filter.filter(event_none))
        self.assertTrue(filter.filter(event_missing)) # PropertyFilter base allows if property missing

    def test_exclusive_range(self):
        """测试不包含边界的范围过滤"""
        filter = RangeFilter(property_name="value", min_value=0, max_value=100, inclusive=False)
        event_in = InteractionEvent(InteractionEventType.SYSTEM_EVENT, data={"value": 50})
        event_min = InteractionEvent(InteractionEventType.SYSTEM_EVENT, data={"value": 0})
        event_max = InteractionEvent(InteractionEventType.SYSTEM_EVENT, data={"value": 100})
        event_out_min = InteractionEvent(InteractionEventType.SYSTEM_EVENT, data={"value": -10})
        event_out_max = InteractionEvent(InteractionEventType.SYSTEM_EVENT, data={"value": 110})
        event_none = InteractionEvent(InteractionEventType.SYSTEM_EVENT, data={"value": None})
        event_missing = InteractionEvent(InteractionEventType.SYSTEM_EVENT, data={})

        self.assertTrue(filter.filter(event_in))
        self.assertFalse(filter.filter(event_min))
        self.assertFalse(filter.filter(event_max))
        self.assertFalse(filter.filter(event_out_min))
        self.assertFalse(filter.filter(event_out_max))
        self.assertFalse(filter.filter(event_none))
        self.assertTrue(filter.filter(event_missing)) # PropertyFilter base allows if property missing

    def test_set_range(self):
        """测试动态设置范围"""
        filter = RangeFilter(property_name="value", min_value=0, max_value=100, inclusive=True)
        event_test = InteractionEvent(InteractionEventType.SYSTEM_EVENT, data={"value": 150})

        self.assertFalse(filter.filter(event_test))

        filter.set_range(min_value=100, max_value=200, inclusive=True)
        self.assertTrue(filter.filter(event_test))

        filter.set_range(min_value=100, max_value=200, inclusive=False)
        self.assertFalse(filter.filter(event_test)) # 150 在非包含范围内

    def test_missing_or_none_value(self):
        """测试属性缺失或值为None时RangeFilter的行为"""
        filter = RangeFilter(property_name="value", min_value=0, max_value=100)
        event_none = InteractionEvent(InteractionEventType.SYSTEM_EVENT, data={"value": None})
        event_missing = InteractionEvent(InteractionEventType.SYSTEM_EVENT, data={})

        # PropertyFilter 基类在属性缺失时返回 True，RangeFilter 在值为 None 时返回 False
        self.assertFalse(filter.filter(event_none))
        self.assertTrue(filter.filter(event_missing))


if __name__ == "__main__":
    unittest.main() 