"""
---------------------------------------------------------------
File name:                  test_time_state_adapter.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                TimeStateAdapter单元测试
----------------------------------------------------------------

Changed history:            
                            2025/05/13: 初始创建;
                            2025/05/13: 更新测试以适应特殊日期状态变更;
                            2025/05/15: 添加更多测试用例，包括边界情况和错误处理;
----
"""

import unittest
from unittest.mock import patch, MagicMock, call

from status.behavior.time_state_adapter import TimeStateAdapter
from status.behavior.time_based_behavior import TimePeriod
from status.behavior.pet_state_machine import PetStateMachine, StateCategory
from status.behavior.pet_state import PetState
from status.core.event_system import EventType, Event


class TestTimeStateAdapter(unittest.TestCase):
    """TimeStateAdapter单元测试"""
    
    def setUp(self):
        """每个测试前的设置"""
        # 模拟依赖对象
        self.mock_pet_state_machine = MagicMock(spec=PetStateMachine)
        self.mock_time_behavior_system = MagicMock()
        
        # 模拟event_system
        with patch('status.core.event_system.EventSystem') as mock_event_system:
            mock_instance = MagicMock()
            mock_event_system.get_instance.return_value = mock_instance
            
            # 创建适配器实例
            self.adapter = TimeStateAdapter(
                self.mock_pet_state_machine,
                self.mock_time_behavior_system
            )
            self.mock_event_system = mock_instance
    
    def test_initialize(self):
        """测试初始化"""
        # 设置get_current_period返回值
        self.mock_time_behavior_system.get_current_period.return_value = TimePeriod.MORNING
        
        # 设置is_special_date返回值
        self.mock_time_behavior_system.is_special_date.return_value = (False, None)
        
        # 初始化
        result = self.adapter._initialize()
        
        # 验证结果
        self.assertTrue(result)
        
        # 注册事件处理程序的调用难以验证，因此我们将测试_on_scene_change方法是否正常工作
        # 创建一个模拟事件
        test_event = Event(EventType.SCENE_CHANGE, "test_sender", {
            'new_period': TimePeriod.NOON
        })
        
        # 调用事件处理方法
        self.adapter._on_scene_change(test_event)
        
        # 验证处理方法能够正确处理事件
        self.mock_pet_state_machine.update_time_state.assert_called_with(PetState.NOON)
        
        # 验证时间状态同步和特殊日期检查在初始化时被调用
        self.mock_time_behavior_system.get_current_period.assert_called()
        self.mock_time_behavior_system.is_special_date.assert_called_once()
        self.mock_pet_state_machine.set_special_date.assert_called_once_with(None)
    
    def test_time_period_mapping_complete(self):
        """测试时间段到状态的映射是否完整"""
        # 确保所有TimePeriod枚举值都有对应的映射
        for period in TimePeriod:
            self.assertIn(period, self.adapter.period_to_state)
            pet_state = self.adapter.period_to_state[period]
            self.assertIsInstance(pet_state, PetState)
            
        # 确保映射正确
        self.assertEqual(self.adapter.period_to_state[TimePeriod.MORNING], PetState.MORNING)
        self.assertEqual(self.adapter.period_to_state[TimePeriod.NOON], PetState.NOON)
        self.assertEqual(self.adapter.period_to_state[TimePeriod.AFTERNOON], PetState.AFTERNOON)
        self.assertEqual(self.adapter.period_to_state[TimePeriod.EVENING], PetState.EVENING)
        self.assertEqual(self.adapter.period_to_state[TimePeriod.NIGHT], PetState.NIGHT)
    
    def test_initialize_with_special_date(self):
        """测试在特殊日期初始化"""
        # 设置get_current_period返回值
        self.mock_time_behavior_system.get_current_period.return_value = TimePeriod.AFTERNOON
        
        # 设置is_special_date返回值 (是特殊日期)
        self.mock_time_behavior_system.is_special_date.return_value = (True, "New Year")
        
        # 初始化
        result = self.adapter._initialize()
        
        # 验证结果
        self.assertTrue(result)
        
        # 验证特殊日期设置
        self.mock_pet_state_machine.set_special_date.assert_called_once_with(PetState.NEW_YEAR)
        self.assertTrue(self.adapter.is_current_special_date)
    
    def test_sync_time_state_null_period(self):
        """测试同步时间状态时遇到null时间段的处理"""
        # 设置get_current_period返回空值
        self.mock_time_behavior_system.get_current_period.return_value = None
        
        # 调用同步方法
        self.adapter._sync_time_state()
        
        # 验证状态机未更新
        self.mock_pet_state_machine.update_time_state.assert_not_called()
    
    def test_sync_time_state_unmapped_period(self):
        """测试同步时间状态时遇到未映射的时间段的处理"""
        # 创建一个临时的adapter，修改其period_to_state映射以模拟缺失映射
        adapter = TimeStateAdapter(self.mock_pet_state_machine, self.mock_time_behavior_system)
        
        # 删除一个映射
        del adapter.period_to_state[TimePeriod.MORNING]
        
        # 设置get_current_period返回的就是这个没有映射的时间段
        self.mock_time_behavior_system.get_current_period.return_value = TimePeriod.MORNING
        
        # 调用同步方法
        adapter._sync_time_state()
        
        # 验证状态机未更新
        self.mock_pet_state_machine.update_time_state.assert_not_called()
    
    def test_handle_period_change(self):
        """测试处理时间段变化"""
        # 创建测试数据
        event_data = {
            'old_period': TimePeriod.MORNING,
            'new_period': TimePeriod.AFTERNOON,
            'timestamp': 1234567890
        }
        
        # 调用处理方法
        self.adapter._handle_period_change(event_data)
        
        # 验证状态机更新
        self.mock_pet_state_machine.update_time_state.assert_called_once_with(PetState.AFTERNOON)
    
    def test_handle_period_change_no_change(self):
        """测试处理相同时间段变化时的行为"""
        # 先设置一个初始状态
        self.mock_pet_state_machine.update_time_state.return_value = False  # 表示状态没有变化
        
        # 创建测试数据 (old_period和new_period相同)
        event_data = {
            'old_period': TimePeriod.MORNING,
            'new_period': TimePeriod.MORNING,
            'timestamp': 1234567890
        }
        
        # 调用处理方法
        self.adapter._handle_period_change(event_data)
        
        # 验证状态机调用，但应该返回False表示没有变化
        self.mock_pet_state_machine.update_time_state.assert_called_once_with(PetState.MORNING)
    
    def test_handle_invalid_period(self):
        """测试处理无效的时间段"""
        # 创建测试数据 (无效的new_period)
        event_data = {
            'old_period': TimePeriod.MORNING,
            'new_period': "NOT_A_VALID_PERIOD",  # 非TimePeriod类型
            'timestamp': 1234567890
        }
        
        # 调用处理方法
        self.adapter._handle_period_change(event_data)
        
        # 验证状态机未更新
        self.mock_pet_state_machine.update_time_state.assert_not_called()
    
    def test_handle_special_date(self):
        """测试处理特殊日期事件"""
        # 创建测试数据
        event_data = {
            'date': (12, 25),
            'name': "Christmas",
            'timestamp': 1234567890
        }
        
        # 调用处理方法
        self.adapter._handle_special_date(event_data)
        
        # 验证特殊日期状态设置
        # 由于我们在_get_special_date_state方法中将"Christmas"映射到PetState.NEW_YEAR
        self.mock_pet_state_machine.set_special_date.assert_called_once_with(PetState.NEW_YEAR)
        self.assertTrue(self.adapter.is_current_special_date)
    
    def test_handle_special_date_no_name(self):
        """测试处理缺少名称的特殊日期事件"""
        # 创建测试数据 (缺少name字段)
        event_data = {
            'date': (12, 25),
            'timestamp': 1234567890
        }
        
        # 调用处理方法
        self.adapter._handle_special_date(event_data)
        
        # 验证特殊日期状态未设置
        self.mock_pet_state_machine.set_special_date.assert_not_called()
        self.assertFalse(self.adapter.is_current_special_date)
    
    def test_scene_change_event_period(self):
        """测试接收时间段变化事件"""
        # 创建事件对象
        event_data = {
            'old_period': TimePeriod.MORNING,
            'new_period': TimePeriod.NOON,
            'timestamp': 1234567890
        }
        event = Event(EventType.SCENE_CHANGE, "test_sender", event_data)
        
        # 调用事件处理方法
        self.adapter._on_scene_change(event)
        
        # 验证调用了正确的处理方法
        self.mock_pet_state_machine.update_time_state.assert_called_once_with(PetState.NOON)
    
    def test_scene_change_event_special_date(self):
        """测试接收特殊日期事件"""
        # 创建事件对象
        event_data = {
            'date': (1, 1),
            'name': "New Year",
            'timestamp': 1234567890
        }
        event = Event(EventType.SCENE_CHANGE, "test_sender", event_data)
        
        # 调用事件处理方法
        self.adapter._on_scene_change(event)
        
        # 验证调用了正确的处理方法
        self.mock_pet_state_machine.set_special_date.assert_called_once_with(PetState.NEW_YEAR)
        self.assertTrue(self.adapter.is_current_special_date)
    
    def test_scene_change_event_empty_data(self):
        """测试接收空数据事件"""
        # 创建事件对象 (空数据)
        event = Event(EventType.SCENE_CHANGE, "test_sender", None)
        
        # 调用事件处理方法
        self.adapter._on_scene_change(event)
        
        # 验证没有调用任何处理方法
        self.mock_pet_state_machine.update_time_state.assert_not_called()
        self.mock_pet_state_machine.set_special_date.assert_not_called()
    
    def test_get_special_date_state(self):
        """测试特殊日期状态映射"""
        # 测试已知映射
        self.assertEqual(self.adapter._get_special_date_state("New Year"), PetState.NEW_YEAR)
        self.assertEqual(self.adapter._get_special_date_state("Valentine's Day"), PetState.VALENTINE)
        
        # 测试未知映射 (应返回默认值)
        self.assertEqual(self.adapter._get_special_date_state("Unknown Holiday"), PetState.NEW_YEAR)
    
    def test_get_all_special_date_states(self):
        """测试所有特殊日期状态是否都有合适的映射"""
        # 测试映射表中所有特殊日期
        special_date_names = [
            "Status Ming", "New Year", "Valentine's Day", 
            "Christmas", "Labor Day", "National Day"
        ]
        
        for date_name in special_date_names:
            pet_state = self.adapter._get_special_date_state(date_name)
            self.assertIsInstance(pet_state, PetState)
            self.assertIn(pet_state, [PetState.NEW_YEAR, PetState.VALENTINE])


if __name__ == '__main__':
    unittest.main()