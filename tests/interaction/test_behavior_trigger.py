"""
---------------------------------------------------------------
File name:                  test_behavior_trigger.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                桌宠行为触发器测试
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import unittest
from unittest.mock import Mock, patch
import time
from datetime import datetime, timedelta

from status.interaction.behavior_trigger import (
    Trigger, BehaviorTrigger, TimeTrigger, ScheduledTrigger, EventTrigger, IdleTrigger
)
from status.interaction.interaction_event import InteractionEvent, InteractionEventType


class TestTrigger(unittest.TestCase):
    """测试触发器基类"""
    
    def setUp(self):
        """每个测试前初始化"""
        self.callback = Mock()
        self.trigger_id = "test_base_trigger"
        self.trigger = Trigger(trigger_id=self.trigger_id, callback=self.callback)
    
    def test_initialization(self):
        """测试初始化"""
        # 验证属性设置正确
        self.assertEqual(self.trigger.trigger_id, self.trigger_id)
        self.assertEqual(self.trigger.callback, self.callback)
        self.assertTrue(self.trigger.enabled)
    
    def test_enable_disable(self):
        """测试启用和禁用触发器"""
        # 默认应该启用
        self.assertTrue(self.trigger.is_enabled())
        
        # 禁用触发器
        self.trigger.disable()
        self.assertFalse(self.trigger.is_enabled())
        
        # 启用触发器
        self.trigger.enable()
        self.assertTrue(self.trigger.is_enabled())
    
    def test_check_and_trigger(self):
        """测试检查和触发"""
        # 基类的check方法应该返回False
        self.assertFalse(self.trigger.check())
        
        # 测试触发
        result = self.trigger.trigger(data={"test": "data"})
        self.assertTrue(result)
        self.callback.assert_called_once_with(self.trigger_id, {"test": "data"})
        
        # 禁用触发器，应该不能触发
        self.trigger.disable()
        result = self.trigger.trigger(data={"test": "more_data"})
        self.assertFalse(result)
        self.callback.assert_called_once()  # 仍然只被调用一次


class TestTimeTrigger(unittest.TestCase):
    """测试定时触发器类"""
    
    def setUp(self):
        """每个测试前初始化"""
        # 设置测试数据
        self.interval = 5  # 5秒触发间隔
        self.callback = Mock()
        self.trigger_id = "test_time_trigger"
        self.current_time = 1000.0  # 使用固定时间，避免依赖系统时间
        
        # 创建定时触发器
        with patch('time.time', return_value=self.current_time):
            self.time_trigger = TimeTrigger(
                interval=self.interval,
                callback=self.callback,
                trigger_id=self.trigger_id
            )
    
    def test_initialization(self):
        """测试初始化"""
        # 验证属性设置正确
        self.assertEqual(self.time_trigger.interval, self.interval)
        self.assertEqual(self.time_trigger.callback, self.callback)
        self.assertEqual(self.time_trigger.trigger_id, self.trigger_id)
        # 初始时间应该是当前时间减去间隔(考虑到默认start_delay=0)
        self.assertEqual(self.time_trigger.last_trigger_time, self.current_time - self.interval)
        self.assertTrue(self.time_trigger.enabled)
    
    def test_check_before_interval(self):
        """测试在间隔之前的检查"""
        # 模拟当前时间为上次触发后2秒(小于间隔)
        new_time = self.current_time + 2
        
        # 先重置last_trigger_time确保时间差小于间隔
        self.time_trigger.last_trigger_time = self.current_time
        
        # 检查是否应该触发
        with patch('time.time', return_value=new_time):
            result = self.time_trigger.check()
        
        # 验证结果 - 应返回False表示不触发
        self.assertFalse(result)
        
        # 验证回调没有被调用
        self.callback.assert_not_called()
        
        # 验证最后触发时间未变
        self.assertEqual(self.time_trigger.last_trigger_time, self.current_time)
    
    def test_check_after_interval(self):
        """测试在间隔之后的检查"""
        # 模拟当前时间为上次触发后6秒(大于间隔)
        new_time = self.current_time + 6
        
        # 先重置last_trigger_time确保时间差大于间隔
        self.time_trigger.last_trigger_time = self.current_time
        
        # 检查是否应该触发
        with patch('time.time', return_value=new_time):
            result = self.time_trigger.check()
        
        # 验证结果 - 应返回True表示应该触发
        self.assertTrue(result)
        
        # 验证最后触发时间已更新
        self.assertEqual(self.time_trigger.last_trigger_time, new_time)
    
    def test_trigger(self):
        """测试触发"""
        # 模拟当前时间为上次触发后6秒(大于间隔)
        old_time = self.current_time
        new_time = old_time + 6
        
        # 重置触发时间
        self.time_trigger.last_trigger_time = old_time
        
        # 检查并确认可以触发
        with patch('time.time', return_value=new_time):
            self.time_trigger.check()
        
        # 触发
        self.time_trigger.trigger()
        
        # 验证回调被调用
        self.callback.assert_called_once_with(self.trigger_id, None)
    
    def test_disabled_trigger(self):
        """测试禁用触发器"""
        # 禁用触发器
        self.time_trigger.disable()
        
        # 模拟当前时间为上次触发后6秒(大于间隔)
        new_time = self.current_time + 6
        
        # 先重置last_trigger_time确保时间差大于间隔
        self.time_trigger.last_trigger_time = self.current_time
        
        # 检查是否应该触发
        with patch('time.time', return_value=new_time):
            result = self.time_trigger.check()
        
        # 验证结果 - 应返回False表示不触发(因为已禁用)
        self.assertFalse(result)
        
        # 验证回调没有被调用
        self.callback.assert_not_called()


class TestScheduledTrigger(unittest.TestCase):
    """测试计划触发器类"""
    
    def setUp(self):
        """每个测试前初始化"""
        # 设置测试数据
        self.callback = Mock()
        self.trigger_id = "test_scheduled_trigger"
        
        # 设置计划时间
        now = datetime.now()
        future_time = now + timedelta(seconds=5)
        self.schedule_time = future_time.strftime("%H:%M:%S")
        
        # 创建计划触发器
        self.scheduled_trigger = ScheduledTrigger(
            schedule_time=self.schedule_time,
            callback=self.callback,
            trigger_id=self.trigger_id
        )
    
    def test_initialization(self):
        """测试初始化"""
        # 验证属性设置正确
        self.assertEqual(self.scheduled_trigger.trigger_id, self.trigger_id)
        self.assertEqual(self.scheduled_trigger.callback, self.callback)
        self.assertTrue(self.scheduled_trigger.enabled)
        
        # 验证时间解析正确
        time_parts = self.schedule_time.split(':')
        self.assertEqual(self.scheduled_trigger.hour, int(time_parts[0]))
        self.assertEqual(self.scheduled_trigger.minute, int(time_parts[1]))
        self.assertEqual(self.scheduled_trigger.second, int(time_parts[2]))
    
    def test_check_before_scheduled_time(self):
        """测试在计划时间之前的检查"""
        # 模拟当前时间为计划时间前一分钟
        current_time = datetime.now() - timedelta(minutes=1)
        
        # 使用mock替换datetime.now
        with patch('status.interaction.behavior_trigger.datetime') as mock_datetime:
            mock_datetime.now.return_value = current_time
            
            # 检查是否应该触发
            result = self.scheduled_trigger.check()
        
        # 验证结果 - 应返回False表示不触发
        self.assertFalse(result)
    
    def test_check_after_scheduled_time(self):
        """测试在计划时间的检查"""
        # 解析计划时间
        time_parts = self.schedule_time.split(':')
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        second = int(time_parts[2])
        
        # 模拟当前时间为计划时间
        current_time = datetime.now().replace(hour=hour, minute=minute, second=second)
        
        # 使用mock替换datetime.now
        with patch('status.interaction.behavior_trigger.datetime') as mock_datetime:
            mock_datetime.now.return_value = current_time
            
            # 检查是否应该触发
            result = self.scheduled_trigger.check()
        
        # 验证结果 - 应返回True表示应该触发
        self.assertTrue(result)
        
        # 验证触发状态已变
        self.assertTrue(self.scheduled_trigger.triggered_today)
    
    def test_trigger(self):
        """测试触发"""
        # 解析计划时间
        time_parts = self.schedule_time.split(':')
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        second = int(time_parts[2])
        
        # 模拟当前时间为计划时间并检查
        current_time = datetime.now().replace(hour=hour, minute=minute, second=second)
        with patch('status.interaction.behavior_trigger.datetime') as mock_datetime:
            mock_datetime.now.return_value = current_time
            self.scheduled_trigger.check()
        
        # 触发
        self.scheduled_trigger.trigger()
        
        # 验证回调被调用
        self.callback.assert_called_once_with(self.trigger_id, None)
    
    def test_only_trigger_once(self):
        """测试只触发一次"""
        # 解析计划时间
        time_parts = self.schedule_time.split(':')
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        second = int(time_parts[2])
        
        # 模拟当前时间为计划时间
        current_time = datetime.now().replace(hour=hour, minute=minute, second=second)
        
        # 第一次检查
        with patch('status.interaction.behavior_trigger.datetime') as mock_datetime:
            mock_datetime.now.return_value = current_time
            result1 = self.scheduled_trigger.check()
        
        # 验证结果 - 应返回True表示应该触发
        self.assertTrue(result1)
        
        # 触发
        self.scheduled_trigger.trigger()
        self.callback.assert_called_once_with(self.trigger_id, None)
        
        # 重置回调计数
        self.callback.reset_mock()
        
        # 第二次检查 - 即使仍在计划时间也不应触发
        with patch('status.interaction.behavior_trigger.datetime') as mock_datetime:
            mock_datetime.now.return_value = current_time
            result2 = self.scheduled_trigger.check()
        
        # 验证结果 - 应返回False表示不应触发
        self.assertFalse(result2)
        
        # 验证回调没有被再次调用
        self.callback.assert_not_called()
    
    def test_disabled_trigger(self):
        """测试禁用触发器"""
        # 禁用触发器
        self.scheduled_trigger.disable()
        
        # 解析计划时间
        time_parts = self.schedule_time.split(':')
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        second = int(time_parts[2])
        
        # 模拟当前时间为计划时间
        current_time = datetime.now().replace(hour=hour, minute=minute, second=second)
        
        # 检查是否应该触发
        with patch('status.interaction.behavior_trigger.datetime') as mock_datetime:
            mock_datetime.now.return_value = current_time
            result = self.scheduled_trigger.check()
        
        # 验证结果 - 应返回False表示不触发(因为已禁用)
        self.assertFalse(result)
        
        # 验证回调没有被调用
        self.callback.assert_not_called()


class TestEventTrigger(unittest.TestCase):
    """测试事件触发器类"""
    
    def setUp(self):
        """每个测试前初始化"""
        # 设置测试数据
        self.event_type = InteractionEventType.MOUSE_CLICK
        self.callback = Mock()
        self.trigger_id = "test_event_trigger"
        self.condition = lambda event: event.data.get("button") == "left"
        
        # 创建事件触发器
        self.event_trigger = EventTrigger(
            event_type=self.event_type,
            callback=self.callback,
            trigger_id=self.trigger_id,
            condition=self.condition
        )
        
        # 添加current_event属性
        self.event_trigger.current_event = None
    
    def test_initialization(self):
        """测试初始化"""
        # 验证属性设置正确
        self.assertEqual(self.event_trigger.event_type, self.event_type)
        self.assertEqual(self.event_trigger.callback, self.callback)
        self.assertEqual(self.event_trigger.trigger_id, self.trigger_id)
        self.assertEqual(self.event_trigger.condition, self.condition)
        self.assertTrue(self.event_trigger.enabled)
    
    def test_check_event_matching(self):
        """测试处理匹配的事件"""
        # 创建匹配事件
        event = InteractionEvent(
            event_type=self.event_type,
            data={"button": "left"}
        )
        
        # 处理事件
        result = self.event_trigger.check_event(event)
        
        # 验证结果 - 应返回True表示事件应被处理
        self.assertTrue(result)
    
    def test_check_event_non_matching(self):
        """测试处理不匹配的事件"""
        # 创建不匹配的事件类型
        event = InteractionEvent(
            event_type=InteractionEventType.MOUSE_MOVE,
            data={"button": "left"}
        )
        
        # 处理事件
        result = self.event_trigger.check_event(event)
        
        # 验证结果 - 应返回False表示事件不应被处理
        self.assertFalse(result)
        
        # 创建匹配事件类型但不匹配条件的事件
        event = InteractionEvent(
            event_type=self.event_type,
            data={"button": "right"}
        )
        
        # 处理事件
        result = self.event_trigger.check_event(event)
        
        # 验证结果 - 应返回False表示事件不应被处理
        self.assertFalse(result)
    
    def test_check_event_with_condition(self):
        """测试带条件的事件处理"""
        # 创建匹配事件类型和条件的事件
        event = InteractionEvent(
            event_type=self.event_type,
            data={"button": "left"}
        )
        
        # 禁用触发器
        self.event_trigger.disable()
        
        # 处理事件
        result = self.event_trigger.check_event(event)
        
        # 验证结果 - 应返回False表示事件不应被处理(因为触发器已禁用)
        self.assertFalse(result)
        
        # 启用触发器
        self.event_trigger.enable()
        
        # 处理事件
        result = self.event_trigger.check_event(event)
        
        # 验证结果 - 应返回True表示事件应被处理
        self.assertTrue(result)
    
    def test_trigger(self):
        """测试触发"""
        # 创建匹配事件
        event = InteractionEvent(
            event_type=self.event_type,
            data={"button": "left"}
        )
        
        # 模拟检查事件，正常情况下会设置current_event
        self.event_trigger.current_event = event
        
        # 触发
        self.event_trigger.trigger()
        
        # 验证回调被调用，传递trigger_id和数据
        self.callback.assert_called_once_with(self.trigger_id, None)


class TestIdleTrigger(unittest.TestCase):
    """测试空闲触发器类"""
    
    def setUp(self):
        """每个测试前初始化"""
        # 设置测试数据
        self.idle_time = 5  # 5秒空闲时间
        self.callback = Mock()
        self.trigger_id = "test_idle_trigger"
        
        # 模拟当前时间
        self.current_time = time.time()
        
        # 创建空闲触发器
        with patch('time.time', return_value=self.current_time):
            self.idle_trigger = IdleTrigger(
                idle_time=self.idle_time,
                callback=self.callback,
                trigger_id=self.trigger_id
            )
    
    def test_initialization(self):
        """测试初始化"""
        # 验证属性设置正确
        self.assertEqual(self.idle_trigger.idle_time, self.idle_time)
        self.assertEqual(self.idle_trigger.callback, self.callback)
        self.assertEqual(self.idle_trigger.trigger_id, self.trigger_id)
        self.assertEqual(self.idle_trigger.last_activity_time, self.current_time)
        self.assertTrue(self.idle_trigger.enabled)
    
    def test_update_activity(self):
        """测试更新用户活动时间"""
        # 模拟经过了2秒
        new_time = self.current_time + 2
        
        # 更新活动时间
        with patch('time.time', return_value=new_time):
            self.idle_trigger.update_activity()
        
        # 验证活动时间已更新
        self.assertEqual(self.idle_trigger.last_activity_time, new_time)
    
    def test_check_not_idle(self):
        """测试非空闲状态检查"""
        # 模拟经过了2秒(小于空闲时间)
        new_time = self.current_time + 2
        
        # 检查是否空闲
        with patch('time.time', return_value=new_time):
            result = self.idle_trigger.check()
        
        # 验证结果 - 应返回False表示不空闲
        self.assertFalse(result)
        
        # 验证回调没有被调用
        self.callback.assert_not_called()
    
    def test_check_idle(self):
        """测试空闲状态检查"""
        # 模拟经过了6秒(大于空闲时间)
        new_time = self.current_time + 6
        
        # 检查是否空闲
        with patch('time.time', return_value=new_time):
            result = self.idle_trigger.check()
        
        # 验证结果 - 应返回True表示空闲
        self.assertTrue(result)
        
    def test_trigger(self):
        """测试触发"""
        # 模拟经过了6秒(大于空闲时间)
        new_time = self.current_time + 6
        
        # 设置为空闲状态
        with patch('time.time', return_value=new_time):
            self.idle_trigger.check()
            
        # 触发
        self.idle_trigger.trigger()
        
        # 验证回调被调用
        self.callback.assert_called_once()
        
    def test_disabled_trigger(self):
        """测试禁用触发器"""
        # 禁用触发器
        self.idle_trigger.disable()
        
        # 模拟经过了6秒(大于空闲时间)
        new_time = self.current_time + 6
        
        # 检查是否空闲
        with patch('time.time', return_value=new_time):
            result = self.idle_trigger.check()
        
        # 验证结果 - 应返回False表示不触发(因为已禁用)
        self.assertFalse(result)
        
        # 验证回调没有被调用
        self.callback.assert_not_called()


class TestBehaviorTrigger(unittest.TestCase):
    """测试行为触发器管理器类"""
    
    def setUp(self):
        """每个测试前初始化"""
        # 模拟事件管理器
        self.mock_event_manager = Mock()
        
        # 模拟QTimer
        self.mock_timer = Mock()
        
        # 使用补丁替换QTimer和EventManager.get_instance
        with patch('status.interaction.behavior_trigger.QTimer', return_value=self.mock_timer):
            with patch('status.core.events.EventManager.get_instance', return_value=self.mock_event_manager):
                self.behavior_trigger = BehaviorTrigger()
        
        # 模拟触发器
        self.mock_trigger = Mock()
        self.mock_trigger.trigger_id = "test_trigger"
        self.mock_trigger.check.return_value = False
        self.mock_trigger.is_enabled.return_value = True
    
    def test_add_trigger(self):
        """测试添加触发器"""
        # 使用_add_trigger方法添加触发器
        result = self.behavior_trigger._add_trigger(self.mock_trigger)
        
        # 验证触发器被添加到字典中
        self.assertEqual(result, "test_trigger")
        self.assertIn(self.mock_trigger.trigger_id, self.behavior_trigger.triggers)
        
        # 模拟TimeTrigger创建，以测试add_trigger方法
        with patch('status.interaction.behavior_trigger.TimeTrigger') as mock_time_trigger_class:
            mock_time_trigger = Mock()
            mock_time_trigger.trigger_id = "new_time_trigger"
            mock_time_trigger_class.return_value = mock_time_trigger
            
            # 调用add_time_trigger方法
            trigger_id = self.behavior_trigger.add_time_trigger(interval=5)
            
            # 验证方法调用
            mock_time_trigger_class.assert_called_once()
            self.assertEqual(trigger_id, "new_time_trigger")
    
    def test_remove_trigger(self):
        """测试移除触发器"""
        # 先添加触发器
        self.behavior_trigger.triggers[self.mock_trigger.trigger_id] = self.mock_trigger
        
        # 移除触发器
        result = self.behavior_trigger.remove_trigger(self.mock_trigger.trigger_id)
        
        # 验证触发器已从字典中移除
        self.assertTrue(result)
        self.assertNotIn(self.mock_trigger.trigger_id, self.behavior_trigger.triggers)
        
        # 尝试移除不存在的触发器
        result = self.behavior_trigger.remove_trigger("nonexistent_trigger")
        self.assertFalse(result)
    
    def test_remove_trigger_by_name(self):
        """测试按名称移除触发器"""
        # 先添加触发器
        self.behavior_trigger.triggers[self.mock_trigger.trigger_id] = self.mock_trigger
        
        # 按ID移除触发器
        result = self.behavior_trigger.remove_trigger(self.mock_trigger.trigger_id)
        
        # 验证触发器已从字典中移除
        self.assertTrue(result)
        self.assertNotIn(self.mock_trigger.trigger_id, self.behavior_trigger.triggers)
        
        # 尝试移除不存在的触发器
        result = self.behavior_trigger.remove_trigger("nonexistent_trigger")
        self.assertFalse(result)
    
    def test_enable_disable_trigger(self):
        """测试启用和禁用触发器"""
        # 先添加触发器
        self.behavior_trigger.triggers[self.mock_trigger.trigger_id] = self.mock_trigger
        
        # 禁用触发器
        result = self.behavior_trigger.enable_trigger(self.mock_trigger.trigger_id, False)
        
        # 验证disable方法被调用
        self.assertTrue(result)
        self.mock_trigger.disable.assert_called_once()
        
        # 启用触发器
        result = self.behavior_trigger.enable_trigger(self.mock_trigger.trigger_id, True)
        
        # 验证enable方法被调用
        self.assertTrue(result)
        self.mock_trigger.enable.assert_called_once()
    
    def test_enable_disable_trigger_by_name(self):
        """测试按名称启用和禁用触发器"""
        # 先添加触发器
        self.behavior_trigger.triggers[self.mock_trigger.trigger_id] = self.mock_trigger
        
        # 按ID禁用触发器
        result = self.behavior_trigger.enable_trigger(self.mock_trigger.trigger_id, False)
        
        # 验证disable方法被调用
        self.assertTrue(result)
        self.mock_trigger.disable.assert_called_once()
        
        # 按ID启用触发器
        result = self.behavior_trigger.enable_trigger(self.mock_trigger.trigger_id, True)
        
        # 验证enable方法被调用
        self.assertTrue(result)
        self.mock_trigger.enable.assert_called_once()
        
        # 尝试操作不存在的触发器
        result = self.behavior_trigger.enable_trigger("nonexistent_trigger", True)
        self.assertFalse(result)
        result = self.behavior_trigger.enable_trigger("nonexistent_trigger", False)
        self.assertFalse(result)
    
    def test_check_triggers(self):
        """测试检查触发器"""
        # 创建模拟触发器
        triggering_trigger = Mock(spec=TimeTrigger)
        triggering_trigger.trigger_id = "triggering_trigger"
        triggering_trigger.check.return_value = True
        
        non_triggering_trigger = Mock(spec=TimeTrigger)
        non_triggering_trigger.trigger_id = "non_triggering_trigger"
        non_triggering_trigger.check.return_value = False
        
        # 添加触发器到字典
        self.behavior_trigger.triggers[triggering_trigger.trigger_id] = triggering_trigger
        self.behavior_trigger.triggers[non_triggering_trigger.trigger_id] = non_triggering_trigger
        
        # 检查触发器
        self.behavior_trigger.check_triggers()
        
        # 验证检查方法被调用
        triggering_trigger.check.assert_called_once()
        non_triggering_trigger.check.assert_called_once()
        
        # 验证触发方法被调用
        triggering_trigger.trigger.assert_called_once()
        non_triggering_trigger.trigger.assert_not_called()
    
    def test_handle_event(self):
        """测试处理事件"""
        # 创建一个模拟事件触发器
        event_trigger = Mock(spec=EventTrigger)
        event_trigger.trigger_id = "event_trigger"
        event_trigger.check_event.return_value = True
        event_trigger.event_type = InteractionEventType.MOUSE_CLICK
        
        # 添加触发器到字典和事件触发器字典
        self.behavior_trigger.triggers[event_trigger.trigger_id] = event_trigger
        self.behavior_trigger.event_triggers[event_trigger.event_type] = {event_trigger.trigger_id}
        
        # 创建事件
        event = Mock()
        event.event_type = InteractionEventType.MOUSE_CLICK
        
        # 处理事件
        self.behavior_trigger.handle_event(event)
        
        # 验证check_event方法被调用
        event_trigger.check_event.assert_called_once_with(event)
        
        # 验证触发方法被调用
        event_trigger.trigger.assert_called_once()
    
    def test_shutdown(self):
        """测试关闭行为触发器管理器"""
        # 添加几个触发器
        trigger1 = Mock()
        trigger1.trigger_id = "trigger1"
        
        trigger2 = Mock()
        trigger2.trigger_id = "trigger2"
        
        self.behavior_trigger.triggers[trigger1.trigger_id] = trigger1
        self.behavior_trigger.triggers[trigger2.trigger_id] = trigger2
        
        # 模拟定时器状态
        self.mock_timer.isActive.return_value = True
        
        # 关闭管理器
        self.behavior_trigger.shutdown()
        
        # 验证定时器被停止
        self.mock_timer.stop.assert_called_once()
        
        # 验证事件管理器的unregister_handler方法被调用
        self.mock_event_manager.unregister_handler.assert_called_once()
        
        # 验证触发器字典被清空
        self.assertEqual(len(self.behavior_trigger.triggers), 0)
        self.assertEqual(len(self.behavior_trigger.event_triggers), 0)


if __name__ == '__main__':
    unittest.main() 