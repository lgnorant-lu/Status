"""
---------------------------------------------------------------
File name:                  test_event_throttler.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                事件节流器测试
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

from status.interaction.event_throttler import (
    EventThrottler, TimeThrottler, CountThrottler, LastEventThrottler, QueueThrottler,
    EventThrottlerChain
)
from status.interaction.interaction_event import InteractionEvent, InteractionEventType


class MockEventThrottler(EventThrottler):
    """用于测试的模拟节流器"""
    
    def __init__(self, name="MockThrottler", should_throttle=False):
        super().__init__(name)
        self.should_throttle = should_throttle
        self.throttled_events = []
    
    def throttle(self, event):
        self.throttled_events.append(event)
        return not self.should_throttle  # 返回True表示不节流，False表示节流


class TestEventThrottler(unittest.TestCase):
    """事件节流器基类测试"""
    
    def test_initialization(self):
        """测试节流器初始化"""
        throttler = MockEventThrottler("TestThrottler")
        self.assertEqual(throttler.name, "TestThrottler")
        self.assertTrue(throttler.is_enabled)
    
    def test_enable_disable(self):
        """测试启用和禁用功能"""
        throttler = MockEventThrottler()
        self.assertTrue(throttler.is_enabled)
        
        throttler.disable()
        self.assertFalse(throttler.is_enabled)
        
        throttler.enable()
        self.assertTrue(throttler.is_enabled)
    
    def test_should_process_when_disabled(self):
        """测试禁用时的处理逻辑"""
        throttler = MockEventThrottler(should_throttle=True)
        throttler.disable()
        
        event = InteractionEvent(InteractionEventType.MOUSE_CLICK)
        self.assertTrue(throttler.should_process(event))
        # 验证throttle方法未被调用
        self.assertEqual(len(throttler.throttled_events), 0)
    
    def test_should_process_stats(self):
        """测试统计信息更新"""
        throttler = MockEventThrottler(should_throttle=False)
        event = InteractionEvent(InteractionEventType.MOUSE_CLICK)
        
        throttler.should_process(event)
        stats = throttler.get_stats()
        self.assertEqual(stats["total_processed"], 1)
        self.assertEqual(stats["total_throttled"], 0)
        
        # 测试节流的情况
        throttler.should_throttle = True
        throttler.should_process(event)
        stats = throttler.get_stats()
        self.assertEqual(stats["total_processed"], 2)
        self.assertEqual(stats["total_throttled"], 1)


class TestTimeThrottler(unittest.TestCase):
    """基于时间的节流器测试"""
    
    def test_initialization(self):
        """测试时间节流器初始化"""
        event_types = {
            InteractionEventType.MOUSE_MOVE,
            InteractionEventType.DRAG_MOVE
        }
        throttler = TimeThrottler(
            name="MoveThrottler",
            cooldown_ms=100,
            event_types=event_types,
            property_key="data.x"
        )
        self.assertEqual(throttler.name, "MoveThrottler")
        self.assertEqual(throttler.cooldown_ms, 100)
        self.assertEqual(throttler.event_types, event_types)
        self.assertEqual(throttler.property_key, "data.x")
    
    def test_throttle_by_time(self):
        """测试基于时间的节流"""
        throttler = TimeThrottler(cooldown_ms=100)
        
        event = InteractionEvent(InteractionEventType.MOUSE_MOVE, {"x": 100, "y": 200})
        
        # 第一次应该通过
        self.assertTrue(throttler.throttle(event))
        
        # 立即发送第二次应该被节流
        self.assertFalse(throttler.throttle(event))
        
        # 等待足够时间后应该通过
        time.sleep(0.11)  # 稍微超过cooldown时间
        self.assertTrue(throttler.throttle(event))
    
    def test_throttle_by_event_type(self):
        """测试基于事件类型的节流"""
        throttler = TimeThrottler(
            cooldown_ms=100,
            event_types={InteractionEventType.MOUSE_MOVE}
        )
        
        move_event = InteractionEvent(InteractionEventType.MOUSE_MOVE, {"x": 100, "y": 200})
        click_event = InteractionEvent(InteractionEventType.MOUSE_CLICK, {"x": 100, "y": 200})
        
        # 移动事件第一次应该通过
        self.assertTrue(throttler.throttle(move_event))
        
        # 移动事件第二次应该被节流
        self.assertFalse(throttler.throttle(move_event))
        
        # 但点击事件应该通过，因为它不在节流的事件类型列表中
        self.assertTrue(throttler.throttle(click_event))
    
    def test_throttle_by_property(self):
        """测试基于属性的节流"""
        throttler = TimeThrottler(
            cooldown_ms=100,
            property_key="data.x"
        )
        
        event1 = InteractionEvent(InteractionEventType.MOUSE_MOVE, {"x": 100, "y": 200})
        event2 = InteractionEvent(InteractionEventType.MOUSE_MOVE, {"x": 200, "y": 200})
        
        # 第一个事件应该通过
        self.assertTrue(throttler.throttle(event1))
        
        # 不同x坐标的事件应该通过，因为它被视为不同的键
        self.assertTrue(throttler.throttle(event2))
        
        # 相同x坐标的事件应该被节流
        self.assertFalse(throttler.throttle(event1))
    
    def test_reset(self):
        """测试重置功能"""
        throttler = TimeThrottler(cooldown_ms=100)
        
        event = InteractionEvent(InteractionEventType.MOUSE_MOVE, {"x": 100, "y": 200})
        
        # 第一次应该通过
        self.assertTrue(throttler.throttle(event))
        
        # 第二次应该被节流
        self.assertFalse(throttler.throttle(event))
        
        # 重置后应该可以通过
        throttler.reset()
        self.assertTrue(throttler.throttle(event))


class TestQueueThrottler(unittest.TestCase):
    """基于队列的节流器测试"""
    
    def test_initialization(self):
        """测试队列节流器初始化"""
        event_types = {
            InteractionEventType.MOUSE_MOVE,
            InteractionEventType.DRAG_MOVE
        }
        mock_processor = Mock()
        throttler = QueueThrottler(
            name="BatchMoveThrottler",
            batch_size=5,
            event_types=event_types,
            property_key="data.x",
            batch_processor=mock_processor
        )
        self.assertEqual(throttler.name, "BatchMoveThrottler")
        self.assertEqual(throttler.batch_size, 5)
        self.assertEqual(throttler.event_types, event_types)
        self.assertEqual(throttler.property_key, "data.x")
        self.assertEqual(throttler.batch_processor, mock_processor)
    
    def test_batch_processing(self):
        """测试批处理逻辑"""
        # 创建模拟批处理函数
        mock_processor = Mock()
        throttler = QueueThrottler(
            batch_size=3,
            batch_processor=mock_processor
        )
        
        event = InteractionEvent(InteractionEventType.MOUSE_MOVE, {"x": 100, "y": 200})
        
        # 前两个事件应该被节流（加入队列）
        self.assertFalse(throttler.throttle(event))
        self.assertFalse(throttler.throttle(event))
        
        # 第三个事件应该触发批处理并通过
        self.assertTrue(throttler.throttle(event))
        
        # 确认批处理函数被调用，且参数是一个包含3个事件的列表
        mock_processor.assert_called_once()
        events_list = mock_processor.call_args[0][0]
        self.assertEqual(len(events_list), 3)
        self.assertIsInstance(events_list[0], InteractionEvent)
    
    def test_event_type_filtering(self):
        """测试事件类型过滤"""
        throttler = QueueThrottler(
            batch_size=3,
            event_types={InteractionEventType.MOUSE_MOVE}
        )
        
        move_event = InteractionEvent(InteractionEventType.MOUSE_MOVE, {"x": 100, "y": 200})
        click_event = InteractionEvent(InteractionEventType.MOUSE_CLICK, {"x": 100, "y": 200})
        
        # 移动事件应该被节流（加入队列）
        self.assertFalse(throttler.throttle(move_event))
        
        # 点击事件不应该被节流，因为它不在节流的事件类型列表中
        self.assertTrue(throttler.throttle(click_event))
    
    def test_flush(self):
        """测试队列刷新功能"""
        throttler = QueueThrottler(batch_size=5)
        
        event = InteractionEvent(InteractionEventType.MOUSE_MOVE, {"x": 100, "y": 200})
        
        # 添加几个事件到队列
        throttler.throttle(event)
        throttler.throttle(event)
        
        # 刷新队列，应该返回已添加的事件
        events = throttler.flush()
        self.assertEqual(len(events), 2)
        self.assertIsInstance(events[0], InteractionEvent)
        
        # 刷新后队列应该为空
        events = throttler.flush()
        self.assertEqual(len(events), 0)


class TestLastEventThrottler(unittest.TestCase):
    """最后事件节流器测试"""
    
    def test_initialization(self):
        """测试最后事件节流器初始化"""
        event_types = {
            InteractionEventType.MOUSE_MOVE,
            InteractionEventType.DRAG_MOVE
        }
        throttler = LastEventThrottler(
            name="LastMoveThrottler",
            cooldown_ms=100,
            event_types=event_types,
            property_key="data.x"
        )
        self.assertEqual(throttler.name, "LastMoveThrottler")
        self.assertEqual(throttler.cooldown_ms, 100)
        self.assertEqual(throttler.event_types, event_types)
        self.assertEqual(throttler.property_key, "data.x")
    
    def test_last_event_processing(self):
        """测试最后事件处理逻辑"""
        throttler = LastEventThrottler(cooldown_ms=100)
        
        event1 = InteractionEvent(InteractionEventType.MOUSE_MOVE, {"x": 100, "y": 200})
        event2 = InteractionEvent(InteractionEventType.MOUSE_MOVE, {"x": 101, "y": 201})
        event3 = InteractionEvent(InteractionEventType.MOUSE_MOVE, {"x": 102, "y": 202})
        
        # 第一个事件应该被节流并保存
        self.assertFalse(throttler.throttle(event1))
        
        # 第二个事件应该替换第一个事件并被节流
        self.assertFalse(throttler.throttle(event2))
        
        # 第三个事件应该替换第二个事件并被节流
        self.assertFalse(throttler.throttle(event3))
        
        # 等待足够时间后，应该可以获取到最后一个挂起的事件
        time.sleep(0.11)  # 稍微超过cooldown时间
        pending_events = throttler.flush()
        self.assertEqual(len(pending_events), 1)
        self.assertEqual(pending_events[0].data["x"], 102)  # 应该是最后一个事件
    
    def test_flush_with_property_key(self):
        """测试使用属性键的刷新功能"""
        throttler = LastEventThrottler(
            cooldown_ms=100,
            property_key="data.x"
        )
        
        event1 = InteractionEvent(InteractionEventType.MOUSE_MOVE, {"x": 100, "y": 200})
        event2 = InteractionEvent(InteractionEventType.MOUSE_MOVE, {"x": 200, "y": 200})
        
        # 添加不同属性的事件
        throttler.throttle(event1)
        throttler.throttle(event2)
        
        # 刷新特定属性的事件
        events = throttler.flush(100)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].data["x"], 100)
        
        # 刷新另一个属性的事件
        events = throttler.flush(200)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].data["x"], 200)
        
        # 刷新所有事件（此时应该已经没有了）
        events = throttler.flush()
        self.assertEqual(len(events), 0)


class TestEventThrottlerChain(unittest.TestCase):
    """事件节流器链测试"""
    
    def test_add_remove_throttlers(self):
        """测试添加和移除节流器"""
        chain = EventThrottlerChain("TestChain")
        self.assertEqual(len(chain.get_throttlers()), 0)
        
        # 添加节流器
        throttler1 = MockEventThrottler("Throttler1")
        throttler2 = MockEventThrottler("Throttler2")
        
        self.assertTrue(chain.add_throttler(throttler1))
        self.assertTrue(chain.add_throttler(throttler2))
        self.assertEqual(len(chain.get_throttlers()), 2)
        
        # 尝试添加重复的节流器
        self.assertFalse(chain.add_throttler(throttler1))
        self.assertEqual(len(chain.get_throttlers()), 2)
        
        # 移除节流器
        self.assertTrue(chain.remove_throttler(throttler1))
        self.assertEqual(len(chain.get_throttlers()), 1)
        
        # 使用名称移除节流器
        self.assertTrue(chain.remove_throttler("Throttler2"))
        self.assertEqual(len(chain.get_throttlers()), 0)
        
        # 尝试移除不存在的节流器
        self.assertFalse(chain.remove_throttler("NonexistentThrottler"))
    
    def test_clear_throttlers(self):
        """测试清空节流器"""
        chain = EventThrottlerChain()
        throttler1 = MockEventThrottler("Throttler1")
        throttler2 = MockEventThrottler("Throttler2")
        
        chain.add_throttler(throttler1)
        chain.add_throttler(throttler2)
        self.assertEqual(len(chain.get_throttlers()), 2)
        
        chain.clear_throttlers()
        self.assertEqual(len(chain.get_throttlers()), 0)
    
    def test_throttle(self):
        """测试节流逻辑"""
        chain = EventThrottlerChain()
        throttler1 = MockEventThrottler("Throttler1", should_throttle=False)
        throttler2 = MockEventThrottler("Throttler2", should_throttle=False)
        
        chain.add_throttler(throttler1)
        chain.add_throttler(throttler2)
        
        event = InteractionEvent(InteractionEventType.MOUSE_CLICK)
        
        # 所有节流器都通过
        self.assertTrue(chain.throttle(event))
        
        # 一个节流器决定节流
        throttler2.should_throttle = True
        self.assertFalse(chain.throttle(event))
        
        # 禁用节流的节流器
        throttler2.disable()
        self.assertTrue(chain.throttle(event))
    
    def test_stats(self):
        """测试统计信息"""
        chain = EventThrottlerChain()
        throttler1 = MockEventThrottler("Throttler1", should_throttle=False)
        throttler2 = MockEventThrottler("Throttler2", should_throttle=True)
        
        chain.add_throttler(throttler1)
        chain.add_throttler(throttler2)
        
        event = InteractionEvent(InteractionEventType.MOUSE_CLICK)
        
        # 第一次处理，应该被节流
        self.assertFalse(chain.throttle(event))
        stats = chain.get_stats()
        self.assertEqual(stats["total_processed"], 1)
        self.assertEqual(stats["total_throttled"], 1)
        
        # 禁用节流的节流器
        throttler2.disable()
        
        # 第二次处理，应该通过
        self.assertTrue(chain.throttle(event))
        stats = chain.get_stats()
        self.assertEqual(stats["total_processed"], 2)
        self.assertEqual(stats["total_throttled"], 1)
        
        # 验证节流器统计数据
        self.assertEqual(stats["throttlers"]["Throttler1"]["processed"], 2)
        self.assertEqual(stats["throttlers"]["Throttler1"]["throttled"], 0)
        # Throttler2被禁用，第二次不应该增加计数
        self.assertEqual(stats["throttlers"]["Throttler2"]["processed"], 1)
        self.assertEqual(stats["throttlers"]["Throttler2"]["throttled"], 1)
    
    def test_reset(self):
        """测试重置所有节流器"""
        chain = EventThrottlerChain()
        
        # 添加两个时间节流器
        throttler1 = TimeThrottler(100, {InteractionEventType.MOUSE_MOVE}, name="MoveThrottler")
        throttler2 = TimeThrottler(100, {InteractionEventType.MOUSE_CLICK}, name="ClickThrottler")
        chain.add_throttler(throttler1)
        chain.add_throttler(throttler2)
        
        # 创建测试事件
        move_event = InteractionEvent(InteractionEventType.MOUSE_MOVE, {"x": 100, "y": 200})
        click_event = InteractionEvent(InteractionEventType.MOUSE_CLICK, {"x": 100, "y": 200})
        
        # 第一次事件应该通过
        self.assertTrue(chain.throttle(move_event))
        self.assertTrue(chain.throttle(click_event))
        
        # 立即发送第二次事件，应该被节流
        self.assertFalse(chain.throttle(move_event))
        self.assertFalse(chain.throttle(click_event))
        
        # 重置节流器链
        chain.reset()
        
        # 重置后应该可以通过
        self.assertTrue(chain.throttle(move_event))
        self.assertTrue(chain.throttle(click_event))


if __name__ == "__main__":
    unittest.main() 