"""
---------------------------------------------------------------
File name:                  test_time_state_bridge.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                测试时间状态桥接器
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
                            2025/05/14: 更新测试以适应信号实现变更;
----
"""

import unittest
from unittest.mock import patch, MagicMock, ANY
import datetime
from freezegun import freeze_time

from status.behavior.time_based_behavior import TimeBasedBehaviorSystem, TimePeriod
from status.behavior.time_state_bridge import TimeStateBridge
from status.behavior.pet_state_machine import PetStateMachine, PetState
from status.core.event_system import EventSystem, EventType, Event


class TestTimeStateBridge(unittest.TestCase):
    """测试TimeStateBridge"""
    
    def setUp(self):
        """设置测试环境"""
        # 模拟事件系统
        self.patcher = patch('status.core.event_system.EventSystem')
        self.mock_event_system = self.patcher.start()
        self.mock_event_system_instance = MagicMock()
        self.mock_event_system.get_instance.return_value = self.mock_event_system_instance
        
        # 模拟状态机
        self.mock_pet_state_machine = MagicMock(spec=PetStateMachine)
        
        # 模拟时间系统
        self.mock_time_system = MagicMock(spec=TimeBasedBehaviorSystem)
        
        # 为时间系统添加signals属性
        self.mock_time_system.signals = MagicMock()
        
        # 设置当前时间段的返回值
        self.mock_time_system.get_current_period.return_value = TimePeriod.MORNING
        
        # 创建时间状态桥接器
        self.bridge = TimeStateBridge(
            pet_state_machine=self.mock_pet_state_machine,
            time_system=self.mock_time_system
        )
        
        # 手动设置事件系统
        self.bridge.event_system = self.mock_event_system_instance
    
    def tearDown(self):
        """清理测试环境"""
        self.patcher.stop()
    
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.bridge)
        self.assertEqual(self.bridge._pet_state_machine, self.mock_pet_state_machine)
        self.assertEqual(self.bridge._time_system, self.mock_time_system)
        
        # 验证映射表
        self.assertEqual(self.bridge.period_to_state[TimePeriod.MORNING], PetState.MORNING)
        self.assertEqual(self.bridge.period_to_state[TimePeriod.NOON], PetState.NOON)
        self.assertEqual(self.bridge.period_to_state[TimePeriod.AFTERNOON], PetState.AFTERNOON)
        self.assertEqual(self.bridge.period_to_state[TimePeriod.EVENING], PetState.EVENING)
        self.assertEqual(self.bridge.period_to_state[TimePeriod.NIGHT], PetState.NIGHT)
    
    def test_initialize(self):
        """测试初始化方法"""
        # 调用初始化
        self.assertTrue(self.bridge._initialize())
        
        # 验证信号连接，不要对具体调用次数做假设
        self.mock_time_system.signals.time_period_changed.connect.assert_called()
        self.mock_time_system.signals.special_date_triggered.connect.assert_called()
        
        # 验证获取当前时间段
        self.mock_time_system.get_current_period.assert_called()
        
        # 验证更新宠物时间状态
        self.mock_pet_state_machine.update_time_state.assert_called_with(PetState.MORNING)
    
    def test_on_time_period_changed(self):
        """测试时间段变化处理"""
        # 调用处理方法
        old_period = TimePeriod.NIGHT
        new_period = TimePeriod.MORNING
        self.bridge._on_time_period_changed(new_period, old_period)
        
        # 验证宠物状态更新
        self.mock_pet_state_machine.update_time_state.assert_called_once_with(PetState.MORNING)
    
    def test_on_special_date_triggered(self):
        """测试特殊日期触发处理"""
        # 调用处理方法
        self.bridge._on_special_date_triggered("新年", "新的一年开始了")
        
        # 验证宠物状态更新
        self.mock_pet_state_machine.set_special_date.assert_called_once_with(PetState.NEW_YEAR)
    
    def test_update_pet_time_state(self):
        """测试更新宠物时间状态"""
        # 测试有效时间段
        self.bridge._update_pet_time_state(TimePeriod.MORNING)
        self.mock_pet_state_machine.update_time_state.assert_called_once_with(PetState.MORNING)
        
        # 重置模拟对象
        self.mock_pet_state_machine.reset_mock()
        
        # 测试无效状态机
        self.bridge._pet_state_machine = None
        self.bridge._update_pet_time_state(TimePeriod.MORNING)
        self.mock_pet_state_machine.update_time_state.assert_not_called()
    
    def test_update_pet_special_date_state(self):
        """测试更新宠物特殊日期状态"""
        # 测试有效特殊日期
        self.bridge._update_pet_special_date_state("新年")
        self.mock_pet_state_machine.set_special_date.assert_called_once_with(PetState.NEW_YEAR)
        
        # 重置模拟对象
        self.mock_pet_state_machine.reset_mock()
        
        # 测试无效特殊日期
        self.bridge._update_pet_special_date_state("无效日期")
        self.mock_pet_state_machine.set_special_date.assert_not_called()
    
    def test_on_time_event(self):
        """测试时间事件处理"""
        # 创建模拟事件
        event = Event(
            event_type=EventType.TIME_PERIOD_CHANGED,
            sender=self.mock_time_system,
            data={
                'period': TimePeriod.EVENING.name,
                'timestamp': datetime.datetime.now().timestamp()
            }
        )
        
        # 调用事件处理方法
        with patch.object(self.bridge, '_update_pet_time_state') as mock_update:
            self.bridge._on_time_event(event)
            
            # 验证更新方法调用
            mock_update.assert_called_once_with(TimePeriod.EVENING)
    
    def test_on_special_date_event(self):
        """测试特殊日期事件处理"""
        # 创建模拟事件
        event = Event(
            event_type=EventType.SPECIAL_DATE,
            sender=self.mock_time_system,
            data={
                'name': "新年",
                'description': "新的一年开始了",
                'timestamp': datetime.datetime.now().timestamp()
            }
        )
        
        # 调用事件处理方法
        with patch.object(self.bridge, '_update_pet_special_date_state') as mock_update:
            self.bridge._on_special_date_event(event)
            
            # 验证更新方法调用
            mock_update.assert_called_once_with("新年")
    
    def test_get_current_time_state(self):
        """测试获取当前时间状态"""
        # 设置时间系统返回值
        self.mock_time_system.get_current_period.return_value = TimePeriod.AFTERNOON
        
        # 调用方法
        state = self.bridge.get_current_time_state()
        
        # 验证结果
        self.assertEqual(state, PetState.AFTERNOON)
        
        # 测试无效状态机或时间系统
        self.bridge._pet_state_machine = None
        self.assertIsNone(self.bridge.get_current_time_state())


if __name__ == "__main__":
    unittest.main() 