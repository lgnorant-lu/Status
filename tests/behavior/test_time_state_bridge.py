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
from unittest.mock import MagicMock, patch, ANY
import datetime
# from freezegun import freeze_time # Not strictly necessary for these tests

from status.behavior.time_based_behavior import TimeBasedBehaviorSystem, TimePeriod, SpecialDate
from status.behavior.time_state_bridge import TimeStateBridge
from status.behavior.pet_state_machine import PetStateMachine, PetState, StateCategory
# from status.core.event_system import EventSystem, EventType, Event # Removed


class TestTimeStateBridge(unittest.TestCase):
    """测试TimeStateBridge (重构后)"""
    
    def setUp(self):
        """设置测试环境"""
        # 模拟状态机
        self.mock_pet_state_machine = MagicMock(spec=PetStateMachine)
        
        # 模拟时间系统
        self.mock_time_system = MagicMock(spec=TimeBasedBehaviorSystem)
        
        # 为时间系统添加signals属性 (需要模拟 connect 方法)
        self.mock_time_system.signals = MagicMock()
        self.mock_time_system.signals.time_period_changed = MagicMock()
        self.mock_time_system.signals.special_date_triggered = MagicMock()
        
        # 设置时间系统 get_current_period 的默认返回值
        self.mock_time_system.get_current_period.return_value = TimePeriod.MORNING
        self.mock_time_system.get_current_special_dates.return_value = [] 
        self.mock_time_system.is_active = True # Add is_active attribute for the mock

        # 创建时间状态桥接器
        self.bridge = TimeStateBridge(
            pet_state_machine=self.mock_pet_state_machine,
            time_system=self.mock_time_system
        )
        # self.bridge.event_system = self.mock_event_system_instance # Removed

    def tearDown(self):
        """清理测试环境"""
        pass # No patcher to stop for now, unless we mock TimeBasedBehaviorSystem's signals more deeply

    def test_init_and_mappings(self):
        """测试初始化和状态映射表"""
        self.assertIsNotNone(self.bridge)
        self.assertEqual(self.bridge._pet_state_machine, self.mock_pet_state_machine)
        self.assertEqual(self.bridge._time_system, self.mock_time_system)
        
        self.assertEqual(self.bridge.period_to_state_mapping[TimePeriod.MORNING], PetState.MORNING)
        self.assertEqual(self.bridge.period_to_state_mapping[TimePeriod.NOON], PetState.NOON)
        self.assertEqual(self.bridge.period_to_state_mapping[TimePeriod.AFTERNOON], PetState.AFTERNOON)
        self.assertEqual(self.bridge.period_to_state_mapping[TimePeriod.EVENING], PetState.EVENING)
        self.assertEqual(self.bridge.period_to_state_mapping[TimePeriod.NIGHT], PetState.NIGHT)

        # Use Chinese keys as defined in TimeStateBridge
        self.assertEqual(self.bridge.special_date_to_state_mapping["新年"], PetState.NEW_YEAR)
        self.assertTrue("圣诞节" in self.bridge.special_date_to_state_mapping) 
        self.assertEqual(self.bridge.special_date_to_state_mapping["立春"], PetState.LICHUN)


    def test_initialize_connects_signals_and_sets_initial_state(self):
        """测试_initialize方法连接信号并设置初始状态"""
        # 模拟时间系统返回当前时间段和无特殊日期
        self.mock_time_system.get_current_period.return_value = TimePeriod.AFTERNOON
        self.mock_time_system.get_current_special_dates.return_value = [] # No initial special dates

        self.bridge._initialize()
        
        # 验证信号连接
        self.mock_time_system.signals.time_period_changed.connect.assert_called_once_with(
            self.bridge._on_time_period_changed
        )
        self.mock_time_system.signals.special_date_triggered.connect.assert_called_once_with(
            self.bridge._on_special_date_triggered
        )
        
        # 验证获取当前时间段和特殊日期
        self.mock_time_system.get_current_period.assert_called_once()
        self.mock_time_system.get_current_special_dates.assert_called_once() # Called during _sync_initial_states

        # 验证通过 update_time_state 设置了初始时间段状态
        self.mock_pet_state_machine.update_time_state.assert_called_with(PetState.AFTERNOON)
        
        # 确保没有因为 initial_special_date 为 None 而调用 set_special_date
        self.mock_pet_state_machine.set_special_date.assert_not_called() # Should not be called if list is empty


    def test_initialize_with_initial_special_date(self):
        """测试 _initialize 在有初始特殊日期时设置状态"""
        # Use Chinese key for mapping, consistent with TimeStateBridge
        mock_special_date = SpecialDate(name="春节", month=1, day=1, type="festival", description="Happy Spring Festival")
        self.mock_time_system.get_current_period.return_value = TimePeriod.MORNING
        self.mock_time_system.get_current_special_dates.return_value = [mock_special_date]
        # Ensure mapping exists for test using the CHINESE name of the holiday from mock_special_date
        self.bridge.special_date_to_state_mapping["春节"] = PetState.SPRING_FESTIVAL 

        self.bridge._initialize()

        self.mock_pet_state_machine.update_time_state.assert_called_with(PetState.MORNING)
        self.mock_pet_state_machine.set_special_date.assert_called_with(PetState.SPRING_FESTIVAL)


    def test_on_time_period_changed_updates_state_machine(self):
        """测试时间段变化时更新状态机"""
        new_period = TimePeriod.EVENING
        old_period = TimePeriod.AFTERNOON
        
        # Ensure the period is in the mapping before test
        self.assertIn(new_period, self.bridge.period_to_state_mapping)

        self.bridge._on_time_period_changed(new_period, old_period)
        
        # 验证状态机 update_time_state 调用
        self.mock_pet_state_machine.update_time_state.assert_called_once_with(PetState.EVENING)

    def test_on_time_period_changed_unknown_period(self):
        """测试当时间段未在映射中时 _on_time_period_changed 不更新状态"""
        # Use a valid TimePeriod enum that we will remove from the mapping
        unmapped_period = TimePeriod.NOON 
        old_period = TimePeriod.MORNING
        
        # Remove the period from the mapping to simulate it being unknown/unmapped
        original_mapping_value = None
        if unmapped_period in self.bridge.period_to_state_mapping:
            original_mapping_value = self.bridge.period_to_state_mapping.pop(unmapped_period)

        self.assertNotIn(unmapped_period, self.bridge.period_to_state_mapping)

        with patch.object(self.bridge.logger, 'warning') as mock_log_warning:
            self.bridge._on_time_period_changed(unmapped_period, old_period)
        
        self.mock_pet_state_machine.update_time_state.assert_not_called()
        mock_log_warning.assert_called_once()

        # Restore mapping if it was changed, to not affect other tests
        if original_mapping_value is not None:
            self.bridge.period_to_state_mapping[unmapped_period] = original_mapping_value


    def test_on_special_date_triggered_updates_state_machine(self):
        """测试特殊日期触发时更新状态机"""
        special_date_name_chinese = "新年" # Use Chinese name matching the bridge's map key
        description = "Happy New Year!"
        # Ensure the mock_date_info also uses the Chinese name if its .name attribute is checked by the bridge
        mock_date_info = SpecialDate(name=special_date_name_chinese, month=1, day=1, description=description, type="festival")

        # Ensure the mapping exists for the Chinese name
        self.assertTrue(special_date_name_chinese in self.bridge.special_date_to_state_mapping)
        self.assertEqual(self.bridge.special_date_to_state_mapping[special_date_name_chinese], PetState.NEW_YEAR)

        self.bridge._on_special_date_triggered(special_date_name_chinese, description, mock_date_info)
        
        self.mock_pet_state_machine.set_special_date.assert_called_once_with(PetState.NEW_YEAR)

    def test_on_special_date_triggered_unknown_date(self):
        """测试当特殊日期未知时 _on_special_date_triggered 不更新状态"""
        unknown_date_name = "UNKNOWN_HOLIDAY"
        description = "Some unknown holiday"
        mock_date_info = SpecialDate(name=unknown_date_name, month=1, day=1, description=description, type="custom")

        # Ensure the unknown_date_name is not in the mapping
        if unknown_date_name in self.bridge.special_date_to_state_mapping:
            del self.bridge.special_date_to_state_mapping[unknown_date_name]

        with patch.object(self.bridge.logger, 'warning') as mock_log_warning:
            self.bridge._on_special_date_triggered(unknown_date_name, description, mock_date_info)

        self.mock_pet_state_machine.set_special_date.assert_not_called()
        mock_log_warning.assert_called_once()


    def test_update_pet_time_state_valid_period(self):
        """测试 _update_pet_time_state 使用有效时间段"""
        self.bridge._update_pet_time_state(TimePeriod.NIGHT)
        self.mock_pet_state_machine.update_time_state.assert_called_once_with(PetState.NIGHT)

    def test_update_pet_time_state_invalid_state_machine(self):
        """测试 _update_pet_time_state 当状态机为None时不执行操作"""
        # To properly test this, we'd need to make _pet_state_machine None *after* bridge init
        # or mock the logger on the bridge instance if _pet_state_machine is None from the start (which __init__ prevents)
        # For now, assume __init__ ensures _pet_state_machine is valid.
        # If bridge._pet_state_machine could become None later, test that path.
        # Current bridge.__init__ raises ValueError if pet_state_machine is None.
        pass # This case is hard to test now due to __init__ raising ValueError


    def test_update_pet_special_date_state_valid_date(self):
        """测试 _update_pet_special_date_state 使用有效特殊日期"""
        self.bridge.special_date_to_state_mapping["CHRISTMAS"] = PetState.HAPPY 
        self.bridge._update_pet_special_date_state("CHRISTMAS", "Merry Christmas")
        self.mock_pet_state_machine.set_special_date.assert_called_once_with(PetState.HAPPY)

    def test_update_pet_special_date_state_invalid_date_name(self):
        """测试 _update_pet_special_date_state 使用无效特殊日期名时不执行操作"""
        with patch.object(self.bridge.logger, 'warning') as mock_log_warning:
            self.bridge._update_pet_special_date_state("NON_EXISTENT_HOLIDAY", "...")
        self.mock_pet_state_machine.set_special_date.assert_not_called()
        mock_log_warning.assert_called_once()

    # Removed test_on_time_event and test_on_special_date_event as TimeStateBridge now uses signals directly.
    # Removed test_get_current_time_state as TimeStateBridge's role is to *set* state, not query it.

if __name__ == "__main__":
    unittest.main() 