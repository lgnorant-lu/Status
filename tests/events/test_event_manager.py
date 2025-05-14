"""
---------------------------------------------------------------
File name:                  test_event_manager.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                测试事件管理器
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

import unittest
import time
import threading
from unittest.mock import MagicMock

from status.events.event_manager import EventManager, EventSubscription
from status.events.event_types import EventPriority, ThrottleMode


class TestEventSubscription(unittest.TestCase):
    """测试EventSubscription类"""
    
    def setUp(self):
        """测试前准备"""
        self.handler = MagicMock()
        self.event_type = "test.event"
        self.event_data = {"param": "value"}
        self.filter_true = lambda t, d: True
        self.filter_false = lambda t, d: False
        
        # 创建基本订阅
        self.subscription = EventSubscription(
            handler=self.handler,
            event_type=self.event_type,
            priority=EventPriority.NORMAL,
            filters=None,
            is_async=False,
            throttle=None,
            once=False
        )
    
    def test_initialization(self):
        """测试初始化"""
        # 验证基本属性
        self.assertEqual(self.subscription.handler, self.handler)
        self.assertEqual(self.subscription.event_type, self.event_type)
        self.assertEqual(self.subscription.priority, EventPriority.NORMAL)
        self.assertEqual(self.subscription.filters, [])
        self.assertFalse(self.subscription.is_async)
        self.assertIsNone(self.subscription.throttle)
        self.assertFalse(self.subscription.once)
        
        # 验证计算属性
        self.assertEqual(self.subscription.last_fired_time, 0)
        self.assertIsNone(self.subscription.queued_event)
        self.assertFalse(self.subscription.is_throttled)
        self.assertIsNotNone(self.subscription.id)
    
    def test_matches_event_type(self):
        """测试匹配事件类型"""
        # 相同事件类型应匹配
        self.assertTrue(self.subscription.matches(self.event_type, self.event_data))
        
        # 不同事件类型不应匹配
        self.assertFalse(self.subscription.matches("other.event", self.event_data))
        
        # 通配符订阅应匹配任何事件类型
        wildcard_subscription = EventSubscription(
            handler=self.handler,
            event_type="*",
            priority=EventPriority.NORMAL
        )
        self.assertTrue(wildcard_subscription.matches(self.event_type, self.event_data))
        self.assertTrue(wildcard_subscription.matches("other.event", self.event_data))
    
    def test_matches_with_filters(self):
        """测试带过滤器的匹配"""
        # 创建带过滤器的订阅
        subscription_true_filter = EventSubscription(
            handler=self.handler,
            event_type=self.event_type,
            filters=[self.filter_true]
        )
        subscription_false_filter = EventSubscription(
            handler=self.handler,
            event_type=self.event_type,
            filters=[self.filter_false]
        )
        subscription_mixed_filters = EventSubscription(
            handler=self.handler,
            event_type=self.event_type,
            filters=[self.filter_true, self.filter_false]
        )
        
        # 验证过滤器结果
        self.assertTrue(subscription_true_filter.matches(self.event_type, self.event_data))
        self.assertFalse(subscription_false_filter.matches(self.event_type, self.event_data))
        self.assertFalse(subscription_mixed_filters.matches(self.event_type, self.event_data))
    
    def test_should_throttle(self):
        """测试节流逻辑"""
        # 没有设置节流，不应该节流
        self.assertFalse(self.subscription.should_throttle())
        
        # 创建带节流的订阅
        throttle_subscription = EventSubscription(
            handler=self.handler,
            event_type=self.event_type,
            throttle=(ThrottleMode.FIRST, 0.1)  # 0.1秒节流间隔
        )
        
        # 首次调用，不应该节流
        self.assertFalse(throttle_subscription.should_throttle())
        self.assertFalse(throttle_subscription.is_throttled)
        self.assertGreater(throttle_subscription.last_fired_time, 0)
        
        # 立即再次调用，应该节流
        self.assertTrue(throttle_subscription.should_throttle())
        self.assertTrue(throttle_subscription.is_throttled)
        
        # 等待节流间隔后再调用，不应该节流
        time.sleep(0.2)
        self.assertFalse(throttle_subscription.should_throttle())
        self.assertFalse(throttle_subscription.is_throttled)


class TestEventManager(unittest.TestCase):
    """测试EventManager类"""
    
    def setUp(self):
        """测试前准备"""
        self.event_manager = EventManager()
        
        # 清空现有数据
        self.event_manager.subscriptions.clear()
        self.event_manager.wildcard_subscriptions.clear()
        self.event_manager.registered_event_types.clear()
        
        # 停止任何可能运行的异步线程
        if self.event_manager.running:
            self.event_manager.stop()
        
        # 测试事件类型和数据
        self.event_type = "test.event"
        self.event_data = {"param": "value"}
        
        # 创建处理器
        self.handler = MagicMock()
    
    def tearDown(self):
        """测试后清理"""
        # 停止异步处理线程
        if self.event_manager.running:
            self.event_manager.stop()
    
    def test_singleton(self):
        """测试单例模式"""
        manager1 = EventManager()
        manager2 = EventManager()
        self.assertIs(manager1, manager2)
    
    def test_register_event_type(self):
        """测试注册事件类型"""
        # 注册事件类型
        self.event_manager.register_event_type(self.event_type)
        
        # 验证注册状态
        self.assertIn(self.event_type, self.event_manager.registered_event_types)
        self.assertTrue(self.event_manager.is_event_type_registered(self.event_type))
        self.assertFalse(self.event_manager.is_event_type_registered("unregistered.event"))
    
    def test_register_event_types(self):
        """测试批量注册事件类型"""
        # 批量注册事件类型
        event_types = ["event1", "event2", "event3"]
        self.event_manager.register_event_types(event_types)
        
        # 验证注册状态
        for event_type in event_types:
            self.assertIn(event_type, self.event_manager.registered_event_types)
    
    def test_subscribe(self):
        """测试订阅事件"""
        # 订阅事件
        subscription = self.event_manager.subscribe(
            event_type=self.event_type,
            handler=self.handler,
            priority=EventPriority.HIGH
        )
        
        # 验证订阅状态
        self.assertIn(self.event_type, self.event_manager.subscriptions)
        self.assertIn(subscription, self.event_manager.subscriptions[self.event_type])
        self.assertEqual(subscription.priority, EventPriority.HIGH)
    
    def test_subscribe_wildcard(self):
        """测试订阅通配符事件"""
        # 订阅通配符事件
        subscription = self.event_manager.subscribe(
            event_type="*",
            handler=self.handler
        )
        
        # 验证订阅状态
        self.assertIn(subscription, self.event_manager.wildcard_subscriptions)
    
    def test_unsubscribe(self):
        """测试取消订阅"""
        # 订阅事件
        subscription = self.event_manager.subscribe(
            event_type=self.event_type,
            handler=self.handler
        )
        
        # 取消订阅
        result = self.event_manager.unsubscribe(subscription)
        
        # 验证结果
        self.assertTrue(result)
        self.assertNotIn(self.event_type, self.event_manager.subscriptions)
    
    def test_unsubscribe_wildcard(self):
        """测试取消通配符订阅"""
        # 订阅通配符事件
        subscription = self.event_manager.subscribe(
            event_type="*",
            handler=self.handler
        )
        
        # 取消订阅
        result = self.event_manager.unsubscribe(subscription)
        
        # 验证结果
        self.assertTrue(result)
        self.assertNotIn(subscription, self.event_manager.wildcard_subscriptions)
    
    def test_unsubscribe_nonexistent(self):
        """测试取消不存在的订阅"""
        # 创建一个未注册的订阅
        subscription = EventSubscription(
            handler=self.handler,
            event_type=self.event_type
        )
        
        # 取消订阅
        result = self.event_manager.unsubscribe(subscription)
        
        # 验证结果
        self.assertFalse(result)
    
    def test_unsubscribe_all(self):
        """测试取消所有订阅"""
        # 添加多个订阅
        self.event_manager.subscribe(event_type="event1", handler=MagicMock())
        self.event_manager.subscribe(event_type="event2", handler=MagicMock())
        self.event_manager.subscribe(event_type="*", handler=MagicMock())
        
        # 取消所有订阅
        self.event_manager.unsubscribe_all()
        
        # 验证结果
        self.assertEqual(len(self.event_manager.subscriptions), 0)
        self.assertEqual(len(self.event_manager.wildcard_subscriptions), 0)
    
    def test_unsubscribe_all_specific_type(self):
        """测试取消特定类型的所有订阅"""
        # 添加多个订阅
        self.event_manager.subscribe(event_type="event1", handler=MagicMock())
        self.event_manager.subscribe(event_type="event1", handler=MagicMock())
        self.event_manager.subscribe(event_type="event2", handler=MagicMock())
        
        # 取消特定类型的所有订阅
        self.event_manager.unsubscribe_all("event1")
        
        # 验证结果
        self.assertNotIn("event1", self.event_manager.subscriptions)
        self.assertIn("event2", self.event_manager.subscriptions)
    
    def test_unsubscribe_all_wildcard(self):
        """测试取消所有通配符订阅"""
        # 添加多个订阅
        self.event_manager.subscribe(event_type="event1", handler=MagicMock())
        self.event_manager.subscribe(event_type="*", handler=MagicMock())
        self.event_manager.subscribe(event_type="*", handler=MagicMock())
        
        # 取消所有通配符订阅
        self.event_manager.unsubscribe_all("*")
        
        # 验证结果
        self.assertEqual(len(self.event_manager.wildcard_subscriptions), 0)
        self.assertIn("event1", self.event_manager.subscriptions)
    
    def test_emit_basic(self):
        """测试基本事件发送"""
        # 订阅事件
        self.event_manager.subscribe(
            event_type=self.event_type,
            handler=self.handler
        )
        
        # 发送事件
        self.event_manager.emit(self.event_type, self.event_data)
        
        # 验证处理器被调用
        self.handler.assert_called_once_with(self.event_type, self.event_data)
    
    def test_emit_wildcard(self):
        """测试通配符事件发送"""
        # 订阅通配符事件
        wildcard_handler = MagicMock()
        self.event_manager.subscribe(
            event_type="*",
            handler=wildcard_handler
        )
        
        # 发送事件
        self.event_manager.emit(self.event_type, self.event_data)
        
        # 验证处理器被调用
        wildcard_handler.assert_called_once_with(self.event_type, self.event_data)
    
    def test_emit_priority(self):
        """测试事件优先级"""
        # 创建记录调用顺序的辅助函数
        call_order = []
        
        def make_handler(name):
            def handler(_, __):
                call_order.append(name)
            return handler
        
        # 以不同优先级订阅事件
        self.event_manager.subscribe(
            event_type=self.event_type,
            handler=make_handler("normal"),
            priority=EventPriority.NORMAL
        )
        self.event_manager.subscribe(
            event_type=self.event_type,
            handler=make_handler("high"),
            priority=EventPriority.HIGH
        )
        self.event_manager.subscribe(
            event_type=self.event_type,
            handler=make_handler("low"),
            priority=EventPriority.LOW
        )
        
        # 发送事件
        self.event_manager.emit(self.event_type, self.event_data)
        
        # 验证调用顺序
        self.assertEqual(call_order, ["high", "normal", "low"])
    
    def test_emit_filter(self):
        """测试事件过滤器"""
        # 创建过滤器
        def filter_true(_, __):
            return True
            
        def filter_false(_, __):
            return False
        
        # 订阅带过滤器的事件
        handler_true = MagicMock()
        handler_false = MagicMock()
        
        self.event_manager.subscribe(
            event_type=self.event_type,
            handler=handler_true,
            filters=[filter_true]
        )
        self.event_manager.subscribe(
            event_type=self.event_type,
            handler=handler_false,
            filters=[filter_false]
        )
        
        # 发送事件
        self.event_manager.emit(self.event_type, self.event_data)
        
        # 验证处理器调用
        handler_true.assert_called_once_with(self.event_type, self.event_data)
        handler_false.assert_not_called()
    
    def test_emit_once(self):
        """测试一次性事件订阅"""
        # 订阅一次性事件
        self.event_manager.subscribe(
            event_type=self.event_type,
            handler=self.handler,
            once=True
        )
        
        # 发送事件两次
        self.event_manager.emit(self.event_type, self.event_data)
        self.event_manager.emit(self.event_type, self.event_data)
        
        # 验证处理器只被调用一次
        self.handler.assert_called_once_with(self.event_type, self.event_data)
        self.assertEqual(len(self.event_manager.subscriptions), 0)
    
    def test_emit_throttle_first(self):
        """测试事件节流 - 仅保留第一个"""
        # 订阅带节流的事件
        self.event_manager.subscribe(
            event_type=self.event_type,
            handler=self.handler,
            throttle=(ThrottleMode.FIRST, 0.2)  # 0.2秒内只处理第一个事件
        )
        
        # 快速连续发送事件
        self.event_manager.emit(self.event_type, {"seq": 1})
        self.event_manager.emit(self.event_type, {"seq": 2})
        
        # 验证只有第一个事件被处理
        self.handler.assert_called_once_with(self.event_type, {"seq": 1})
        
        # 等待节流间隔后再次发送
        time.sleep(0.3)
        self.event_manager.emit(self.event_type, {"seq": 3})
        
        # 验证第三个事件被处理
        self.assertEqual(self.handler.call_count, 2)
        self.handler.assert_called_with(self.event_type, {"seq": 3})
    
    def test_emit_throttle_last(self):
        """测试事件节流 - 仅保留最后一个"""
        # 订阅带节流的事件
        self.event_manager.subscribe(
            event_type=self.event_type,
            handler=self.handler,
            throttle=(ThrottleMode.LAST, 0.2)  # 0.2秒内只处理最后一个事件
        )
        
        # 快速连续发送事件
        self.event_manager.emit(self.event_type, {"seq": 1})
        self.event_manager.emit(self.event_type, {"seq": 2})
        
        # 验证只有第一个事件被立即处理
        self.handler.assert_called_once_with(self.event_type, {"seq": 1})
        
        # 等待节流间隔后检查
        time.sleep(0.3)
        self.event_manager.process_throttled_events()
        
        # 验证最后一个事件被延迟处理
        self.assertEqual(self.handler.call_count, 2)
        self.handler.assert_called_with(self.event_type, {"seq": 2})
    
    def test_emit_throttle_rate(self):
        """测试事件节流 - 固定速率"""
        # 订阅带节流的事件
        self.event_manager.subscribe(
            event_type=self.event_type,
            handler=self.handler,
            throttle=(ThrottleMode.RATE, 0.2)  # 0.2秒内只处理一个事件
        )
        
        # 快速连续发送事件
        self.event_manager.emit(self.event_type, {"seq": 1})
        self.event_manager.emit(self.event_type, {"seq": 2})
        
        # 验证只有第一个事件被立即处理
        self.handler.assert_called_once_with(self.event_type, {"seq": 1})
        
        # 等待节流间隔后处理下一个事件
        time.sleep(0.3)
        self.event_manager.process_throttled_events()
        
        # 验证下一个事件被处理
        self.assertEqual(self.handler.call_count, 2)
        self.handler.assert_called_with(self.event_type, {"seq": 2})
    
    def test_async_events(self):
        """测试异步事件处理"""
        # 启动异步处理线程
        self.event_manager.start()
        
        # 创建一个同步点
        sync_event = threading.Event()
        
        # 创建一个异步处理器，它将在调用时设置同步点
        def async_handler(_, __):
            time.sleep(0.1)  # 模拟异步工作
            sync_event.set()
        
        # 订阅异步事件
        self.event_manager.subscribe(
            event_type=self.event_type,
            handler=async_handler,
            is_async=True
        )
        
        # 发送事件
        self.event_manager.emit(self.event_type, self.event_data)
        
        # 等待异步处理完成
        self.assertTrue(sync_event.wait(1.0))
    
    def test_get_subscription_count(self):
        """测试获取订阅数量"""
        # 添加多个订阅
        self.event_manager.subscribe(event_type="event1", handler=MagicMock())
        self.event_manager.subscribe(event_type="event1", handler=MagicMock())
        self.event_manager.subscribe(event_type="event2", handler=MagicMock())
        self.event_manager.subscribe(event_type="*", handler=MagicMock())
        
        # 验证订阅数量
        self.assertEqual(self.event_manager.get_subscription_count(), 4)
        self.assertEqual(self.event_manager.get_subscription_count("event1"), 2)
        self.assertEqual(self.event_manager.get_subscription_count("event2"), 1)
        self.assertEqual(self.event_manager.get_subscription_count("*"), 1)
        self.assertEqual(self.event_manager.get_subscription_count("nonexistent"), 0)


if __name__ == "__main__":
    unittest.main() 