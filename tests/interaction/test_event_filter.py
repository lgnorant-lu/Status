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
    EventFilter, EventTypeFilter, EventPropertyFilter, 
    CompositeFilter, EventFilterChain
)
from status.interaction.interaction_event import InteractionEvent, InteractionEventType


class MockEventFilter(EventFilter):
    """用于测试的模拟过滤器"""
    
    def __init__(self, name="MockFilter", should_pass=True):
        super().__init__(name)
        self.should_pass = should_pass
        self.filtered_events = []
        self.stats = {
            "total_processed": 0,
            "total_throttled": 0
        }
    
    def filter(self, event):
        self.filtered_events.append(event)
        return self.should_pass
        
    def should_process(self, event):
        """判断是否应该处理事件
        
        首先检查过滤器是否启用，然后调用filter方法判断是否过滤
        
        Args:
            event: 要判断的交互事件
            
        Returns:
            bool: 如果应该处理返回True，否则返回False
        """
        # 更新统计信息
        self.stats["total_processed"] += 1
        
        # 如果过滤器禁用，直接通过
        if not self.is_enabled:
            return True
        
        # 调用子类的filter方法判断是否过滤
        result = self.filter(event)
        
        # 如果被过滤，更新统计信息
        if not result:
            self.stats["total_throttled"] += 1
        
        return result
    
    def get_stats(self):
        """获取过滤器的统计信息
        
        Returns:
            dict: 过滤器的统计信息
        """
        return self.stats


class TestEventFilter(unittest.TestCase):
    """事件过滤器基类测试"""
    
    def test_initialization(self):
        """测试过滤器初始化"""
        filter = MockEventFilter("TestFilter")
        self.assertEqual(filter.name, "TestFilter")
        self.assertTrue(filter.is_enabled)
    
    def test_enable_disable(self):
        """测试启用和禁用功能"""
        filter = MockEventFilter()
        self.assertTrue(filter.is_enabled)
        
        filter.disable()
        self.assertFalse(filter.is_enabled)
        
        filter.enable()
        self.assertTrue(filter.is_enabled)
    
    def test_should_process_when_disabled(self):
        """测试禁用时的处理逻辑"""
        filter = MockEventFilter(should_pass=False)
        filter.disable()
        
        event = InteractionEvent(InteractionEventType.MOUSE_CLICK)
        self.assertTrue(filter.should_process(event))
        # 验证filter方法未被调用
        self.assertEqual(len(filter.filtered_events), 0)
    
    def test_should_process_stats(self):
        """测试统计信息更新"""
        filter = MockEventFilter(should_pass=True)
        event = InteractionEvent(InteractionEventType.MOUSE_CLICK)
        
        filter.should_process(event)
        stats = filter.get_stats()
        self.assertEqual(stats["total_processed"], 1)
        self.assertEqual(stats["total_throttled"], 0)
        
        # 测试不通过的情况
        filter.should_pass = False
        filter.should_process(event)
        stats = filter.get_stats()
        self.assertEqual(stats["total_processed"], 2)
        self.assertEqual(stats["total_throttled"], 1)


class TestEventTypeFilter(unittest.TestCase):
    """事件类型过滤器测试"""
    
    def test_initialization(self):
        """测试类型过滤器初始化"""
        allowed_types = {
            InteractionEventType.MOUSE_CLICK,
            InteractionEventType.MOUSE_DOUBLE_CLICK
        }
        filter = EventTypeFilter("TypeFilter", allowed_types)
        self.assertEqual(filter.name, "TypeFilter")
        self.assertEqual(filter.allowed_types, allowed_types)
    
    def test_filter_allowed_type(self):
        """测试允许的事件类型"""
        filter = EventTypeFilter(
            allowed_types={InteractionEventType.MOUSE_CLICK}
        )
        
        event = InteractionEvent(InteractionEventType.MOUSE_CLICK)
        self.assertTrue(filter.filter(event))
    
    def test_filter_blocked_type(self):
        """测试阻止的事件类型"""
        filter = EventTypeFilter(
            allowed_types={InteractionEventType.MOUSE_CLICK}
        )
        
        event = InteractionEvent(InteractionEventType.MOUSE_MOVE)
        self.assertFalse(filter.filter(event))


class TestEventPropertyFilter(unittest.TestCase):
    """事件属性过滤器测试"""
    
    def test_initialization(self):
        """测试属性过滤器初始化"""
        filter = EventPropertyFilter(
            name="PositionFilter",
            property_name="data.x",
            property_value=100,
            comparison="gt"
        )
        self.assertEqual(filter.name, "PositionFilter")
        self.assertEqual(filter.property_name, "data.x")
        self.assertEqual(filter.property_value, 100)
        self.assertEqual(filter.comparison, "gt")
    
    def test_comparison_operators(self):
        """测试各种比较运算符"""
        # 测试相等
        filter_eq = EventPropertyFilter(
            property_name="data.x",
            property_value=100,
            comparison="eq"
        )
        event = InteractionEvent(InteractionEventType.MOUSE_CLICK, {"x": 100})
        self.assertTrue(filter_eq.filter(event))
        event = InteractionEvent(InteractionEventType.MOUSE_CLICK, {"x": 101})
        self.assertFalse(filter_eq.filter(event))
        
        # 测试大于
        filter_gt = EventPropertyFilter(
            property_name="data.x",
            property_value=100,
            comparison="gt"
        )
        event = InteractionEvent(InteractionEventType.MOUSE_CLICK, {"x": 101})
        self.assertTrue(filter_gt.filter(event))
        event = InteractionEvent(InteractionEventType.MOUSE_CLICK, {"x": 100})
        self.assertFalse(filter_gt.filter(event))
        
        # 测试包含
        filter_contains = EventPropertyFilter(
            property_name="data.text",
            property_value="test",
            comparison="contains"
        )
        event = InteractionEvent(InteractionEventType.MENU_COMMAND, {"text": "this is a test message"})
        self.assertTrue(filter_contains.filter(event))
        event = InteractionEvent(InteractionEventType.MENU_COMMAND, {"text": "no match here"})
        self.assertFalse(filter_contains.filter(event))
    
    def test_nested_property(self):
        """测试嵌套属性"""
        filter = EventPropertyFilter(
            property_name="data.position.x",
            property_value=100,
            comparison="eq"
        )
        event = InteractionEvent(
            InteractionEventType.MOUSE_CLICK, 
            {"position": {"x": 100, "y": 200}}
        )
        self.assertTrue(filter.filter(event))


class TestCompositeFilter(unittest.TestCase):
    """复合过滤器测试"""
    
    def test_and_mode(self):
        """测试AND模式"""
        filter1 = MockEventFilter(should_pass=True)
        filter2 = MockEventFilter(should_pass=True)
        composite = CompositeFilter(
            name="AndFilter",
            filters=[filter1, filter2],
            mode="AND"
        )
        
        event = InteractionEvent(InteractionEventType.MOUSE_CLICK)
        self.assertTrue(composite.filter(event))
        
        # 如果任一过滤器不通过，复合过滤器就不通过
        filter2.should_pass = False
        self.assertFalse(composite.filter(event))
    
    def test_or_mode(self):
        """测试OR模式"""
        filter1 = MockEventFilter(should_pass=False)
        filter2 = MockEventFilter(should_pass=True)
        composite = CompositeFilter(
            name="OrFilter",
            filters=[filter1, filter2],
            mode="OR"
        )
        
        event = InteractionEvent(InteractionEventType.MOUSE_CLICK)
        self.assertTrue(composite.filter(event))
        
        # 只有所有过滤器都不通过，复合过滤器才不通过
        filter2.should_pass = False
        self.assertFalse(composite.filter(event))
    
    def test_disabled_filters(self):
        """测试禁用的子过滤器"""
        filter1 = MockEventFilter(should_pass=False)
        filter2 = MockEventFilter(should_pass=False)
        composite = CompositeFilter(
            name="AndWithDisabled",
            filters=[filter1, filter2],
            mode="AND"
        )
        
        # 禁用第一个过滤器
        filter1.disable()
        
        event = InteractionEvent(InteractionEventType.MOUSE_CLICK)
        # 通过composite.should_process调用，因为第一个过滤器被禁用，只看第二个
        self.assertFalse(composite.should_process(event))
        
        # 禁用所有过滤器
        filter2.disable()
        # 所有过滤器都被禁用，应该通过
        self.assertTrue(composite.should_process(event))


class TestEventFilterChain(unittest.TestCase):
    """事件过滤器链测试"""
    
    def test_add_remove_filters(self):
        """测试添加和移除过滤器"""
        chain = EventFilterChain("TestChain")
        self.assertEqual(len(chain.get_filters()), 0)
        
        # 添加过滤器
        filter1 = MockEventFilter("Filter1")
        filter2 = MockEventFilter("Filter2")
        
        self.assertTrue(chain.add_filter(filter1))
        self.assertTrue(chain.add_filter(filter2))
        self.assertEqual(len(chain.get_filters()), 2)
        
        # 尝试添加重复的过滤器
        self.assertFalse(chain.add_filter(filter1))
        self.assertEqual(len(chain.get_filters()), 2)
        
        # 移除过滤器
        self.assertTrue(chain.remove_filter(filter1))
        self.assertEqual(len(chain.get_filters()), 1)
        
        # 使用名称移除过滤器
        self.assertTrue(chain.remove_filter("Filter2"))
        self.assertEqual(len(chain.get_filters()), 0)
        
        # 尝试移除不存在的过滤器
        self.assertFalse(chain.remove_filter("NonexistentFilter"))
    
    def test_clear_filters(self):
        """测试清空过滤器"""
        chain = EventFilterChain()
        filter1 = MockEventFilter("Filter1")
        filter2 = MockEventFilter("Filter2")
        
        chain.add_filter(filter1)
        chain.add_filter(filter2)
        self.assertEqual(len(chain.get_filters()), 2)
        
        chain.clear_filters()
        self.assertEqual(len(chain.get_filters()), 0)
    
    def test_should_process(self):
        """测试事件处理逻辑"""
        chain = EventFilterChain()
        filter1 = MockEventFilter("Filter1", should_pass=True)
        filter2 = MockEventFilter("Filter2", should_pass=True)
        
        chain.add_filter(filter1)
        chain.add_filter(filter2)
        
        event = InteractionEvent(InteractionEventType.MOUSE_CLICK)
        
        # 所有过滤器都通过
        self.assertTrue(chain.should_process(event))
        
        # 一个过滤器不通过
        filter2.should_pass = False
        self.assertFalse(chain.should_process(event))
        
        # 禁用不通过的过滤器
        filter2.disable()
        self.assertTrue(chain.should_process(event))
    
    def test_stats(self):
        """测试统计信息"""
        chain = EventFilterChain()
        filter1 = MockEventFilter("Filter1", should_pass=True)
        filter2 = MockEventFilter("Filter2", should_pass=False)
        
        chain.add_filter(filter1)
        chain.add_filter(filter2)
        
        event = InteractionEvent(InteractionEventType.MOUSE_CLICK)
        
        # 第一次处理，应该被拦截
        self.assertFalse(chain.should_process(event))
        stats = chain.get_stats()
        self.assertEqual(stats["total_processed"], 1)
        self.assertEqual(stats["total_filtered"], 1)
        
        # 禁用拦截的过滤器
        filter2.disable()
        
        # 第二次处理，应该通过
        self.assertTrue(chain.should_process(event))
        stats = chain.get_stats()
        self.assertEqual(stats["total_processed"], 2)
        self.assertEqual(stats["total_filtered"], 1)
        
        # 验证过滤器统计数据
        self.assertEqual(stats["filters"]["Filter1"]["processed"], 2)
        self.assertEqual(stats["filters"]["Filter1"]["filtered"], 0)
        # Filter2被禁用，第二次不应该增加计数
        self.assertEqual(stats["filters"]["Filter2"]["processed"], 1)
        self.assertEqual(stats["filters"]["Filter2"]["filtered"], 1)


if __name__ == "__main__":
    unittest.main() 