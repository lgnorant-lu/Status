"""
---------------------------------------------------------------
File name:                  test_pet_state_machine.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                测试宠物状态机功能
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

import unittest
import time
from unittest.mock import Mock, patch

from status.behavior.pet_state_machine import PetStateMachine, StateCategory
from status.behavior.pet_state import PetState
from status.core.event_system import EventSystem

class TestPetStateMachine(unittest.TestCase):
    """测试宠物状态机的核心功能"""
    
    def setUp(self):
        """在每个测试之前设置环境"""
        # 创建一个状态机实例
        self.state_machine = PetStateMachine(
            cpu_light_threshold=10.0,
            cpu_moderate_threshold=30.0,
            cpu_heavy_threshold=50.0,
            cpu_very_heavy_threshold=70.0,
            memory_warning_threshold=70.0,
            memory_critical_threshold=90.0
        )
        
        # 模拟事件系统
        self.mock_event_system = Mock()
        self.state_machine.event_system = self.mock_event_system
    
    def test_initial_state(self):
        """测试状态机初始状态"""
        # 初始状态应该是IDLE
        self.assertEqual(self.state_machine.get_state(), PetState.IDLE)
        
        # 检查活动状态
        active_states = self.state_machine.get_active_states()
        self.assertEqual(active_states[StateCategory.SYSTEM], PetState.IDLE)
        self.assertIsNone(active_states[StateCategory.TIME])
        self.assertIsNone(active_states[StateCategory.SPECIAL_DATE])
        self.assertIsNone(active_states[StateCategory.INTERACTION])
    
    def test_update_cpu_usage(self):
        """测试CPU使用率变化导致的状态变化"""
        # 测试不同的CPU使用率导致的状态变化
        self.state_machine.update(cpu_usage=5.0, memory_usage=30.0)
        self.assertEqual(self.state_machine.get_state(), PetState.IDLE)
        
        self.state_machine.update(cpu_usage=15.0, memory_usage=30.0)
        self.assertEqual(self.state_machine.get_state(), PetState.LIGHT_LOAD)
        
        self.state_machine.update(cpu_usage=35.0, memory_usage=30.0)
        self.assertEqual(self.state_machine.get_state(), PetState.MODERATE_LOAD)
        
        self.state_machine.update(cpu_usage=55.0, memory_usage=30.0)
        self.assertEqual(self.state_machine.get_state(), PetState.HEAVY_LOAD)
        
        self.state_machine.update(cpu_usage=75.0, memory_usage=30.0)
        self.assertEqual(self.state_machine.get_state(), PetState.VERY_HEAVY_LOAD)
        
        self.state_machine.update(cpu_usage=96.0, memory_usage=30.0)
        self.assertEqual(self.state_machine.get_state(), PetState.CPU_CRITICAL)
    
    def test_memory_overrides_cpu(self):
        """测试内存使用率超过阈值时覆盖CPU状态"""
        # 内存警告状态的优先级应高于一般CPU状态
        self.state_machine.update(cpu_usage=55.0, memory_usage=75.0)
        self.assertEqual(self.state_machine.get_state(), PetState.MEMORY_WARNING)
        
        # 内存临界状态的优先级应高于大多数状态
        self.state_machine.update(cpu_usage=96.0, memory_usage=95.0)
        self.assertEqual(self.state_machine.get_state(), PetState.MEMORY_CRITICAL)
    
    def test_time_state_update(self):
        """测试时间状态更新"""
        # 设置时间状态
        self.state_machine.update_time_state(PetState.MORNING)
        
        # 检查当前活动状态
        active_states = self.state_machine.get_active_states()
        self.assertEqual(active_states[StateCategory.TIME], PetState.MORNING)
        
        # 如果无更高优先级状态，时间状态应该是当前状态
        self.assertEqual(self.state_machine.get_state(), PetState.MORNING)
        
        # 更新CPU和内存使用率，应该覆盖时间状态
        self.state_machine.update(cpu_usage=55.0, memory_usage=30.0)
        self.assertEqual(self.state_machine.get_state(), PetState.HEAVY_LOAD)
    
    def test_special_date_update(self):
        """测试特殊日期状态更新"""
        # 设置特殊日期状态
        self.state_machine.set_special_date(PetState.BIRTHDAY)
        
        # 检查当前活动状态
        active_states = self.state_machine.get_active_states()
        self.assertEqual(active_states[StateCategory.SPECIAL_DATE], PetState.BIRTHDAY)
        
        # 特殊日期状态的优先级应该高于时间状态
        self.state_machine.update_time_state(PetState.MORNING)
        self.assertEqual(self.state_machine.get_state(), PetState.BIRTHDAY)
        
        # 更新内存使用率至警告级别，应该覆盖特殊日期状态
        self.state_machine.update(cpu_usage=55.0, memory_usage=75.0)
        self.assertEqual(self.state_machine.get_state(), PetState.MEMORY_WARNING)
    
    def test_interaction_state(self):
        """测试交互状态优先级"""
        # 设置交互状态
        self.state_machine.set_interaction_state(PetState.CLICKED)
        
        # 交互状态应该有最高优先级
        self.assertEqual(self.state_machine.get_state(), PetState.CLICKED)
        
        # 即使在内存临界状态，交互状态仍然应该有最高优先级
        self.state_machine.update(cpu_usage=96.0, memory_usage=95.0)
        self.assertEqual(self.state_machine.get_state(), PetState.CLICKED)
        
        # 清除交互状态，内存临界状态应该生效
        self.state_machine.set_interaction_state(None)
        self.assertEqual(self.state_machine.get_state(), PetState.MEMORY_CRITICAL)
    
    def test_recalculate_active_state(self):
        """测试重新计算活动状态"""
        # 设置各种状态
        self.state_machine.update(cpu_usage=55.0, memory_usage=30.0)
        self.state_machine.update_time_state(PetState.MORNING)
        self.state_machine.set_special_date(PetState.BIRTHDAY)
        
        # 当前状态应该是HEAVY_LOAD（因为系统资源状态优先级高于特殊日期）
        self.assertEqual(self.state_machine.get_state(), PetState.HEAVY_LOAD)
        
        # 手动调用_recalculate_active_state测试优先级顺序
        self.state_machine._recalculate_active_state()
        
        # 检查优先级正确：特殊日期应该高于系统状态
        self.assertEqual(self.state_machine.get_state(), PetState.BIRTHDAY)
        
        # 设置交互状态
        self.state_machine.set_interaction_state(PetState.CLICKED)
        
        # 交互状态应该是当前状态
        self.assertEqual(self.state_machine.get_state(), PetState.CLICKED)
    
    def test_state_history(self):
        """测试状态历史记录功能"""
        # 初始状态
        self.assertEqual(len(self.state_machine.state_history), 0)
        
        # 触发状态变化
        self.state_machine.update(cpu_usage=75.0, memory_usage=30.0)
        
        # 检查历史记录是否更新
        self.assertEqual(len(self.state_machine.state_history), 1)
        history = self.state_machine.get_state_history()
        self.assertEqual(history[0]["current_state_name"], "VERY_HEAVY_LOAD")
        
        # 再次更新状态
        self.state_machine.update(cpu_usage=35.0, memory_usage=30.0)
        
        # 检查历史记录是否再次更新
        self.assertEqual(len(self.state_machine.state_history), 2)
        history = self.state_machine.get_state_history()
        self.assertEqual(history[0]["current_state_name"], "MODERATE_LOAD")
        self.assertEqual(history[1]["current_state_name"], "VERY_HEAVY_LOAD")
        
        # 测试清除历史记录
        self.state_machine.clear_state_history()
        self.assertEqual(len(self.state_machine.state_history), 0)
    
    def test_event_publishing(self):
        """测试状态变化事件发布"""
        # 触发状态变化
        self.state_machine.update(cpu_usage=75.0, memory_usage=30.0)
        
        # 检查事件系统是否收到分发请求
        self.mock_event_system.dispatch_event.assert_called_once()
        
        # 确保事件携带的数据正确
        call_args = self.mock_event_system.dispatch_event.call_args[1]
        self.assertEqual(call_args["data"]["previous_state_name"], "IDLE")
        self.assertEqual(call_args["data"]["current_state_name"], "VERY_HEAVY_LOAD")

if __name__ == "__main__":
    unittest.main() 