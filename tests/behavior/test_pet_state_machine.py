"""
---------------------------------------------------------------
File name:                  test_pet_state_machine.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                测试宠物状态机逻辑
----------------------------------------------------------------

Changed history:            
                            2025/05/13: 初始创建;
                            2025/05/13: 更新测试以适应多状态系统;
                            2025/05/13: 添加多系统资源状态优先级处理测试;
----
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from status.behavior.pet_state_machine import PetStateMachine, StateCategory
from status.behavior.pet_state import PetState

class TestPetStateMachine(unittest.TestCase):
    """测试宠物状态机逻辑"""

    def setUp(self):
        """每个测试用例执行前的设置"""
        # 模拟事件系统
        with patch('status.core.event_system.EventSystem') as mock_event_system:
            mock_instance = MagicMock()
            mock_event_system.get_instance.return_value = mock_instance
            
        self.state_machine = PetStateMachine()
        self.mock_event_system = mock_instance
            
        self.cpu_threshold = self.state_machine.cpu_threshold
        self.memory_threshold = self.state_machine.memory_threshold

    def test_initial_state(self):
        """测试初始状态是否为 IDLE"""
        self.assertEqual(self.state_machine.get_state(), PetState.IDLE, "初始状态应为 IDLE")
        self.assertEqual(self.state_machine.active_states[StateCategory.SYSTEM], PetState.IDLE, "初始系统状态应为 IDLE")
        self.assertIsNone(self.state_machine.active_states[StateCategory.TIME], "初始时间状态应为 None")
        self.assertIsNone(self.state_machine.active_states[StateCategory.SPECIAL_DATE], "初始特殊日期状态应为 None")

    # --- CPU 相关测试 ---
    def test_transition_idle_to_busy(self):
        """测试从 IDLE 到 BUSY 的转换 (内存正常)"""
        cpu_usage = self.cpu_threshold + 5
        memory_usage = self.memory_threshold - 5 # 内存正常
        changed = self.state_machine.update(cpu_usage, memory_usage)
        self.assertTrue(changed, "状态应已改变")
        self.assertEqual(self.state_machine.get_state(), PetState.BUSY, "状态应转换为 BUSY")
        self.assertEqual(self.state_machine.active_states[StateCategory.SYSTEM], PetState.BUSY, "系统状态应为 BUSY")
        
        # 验证事件发布
        self.mock_event_system.dispatch_event.assert_called_once()

    def test_transition_busy_to_idle(self):
        """测试从 BUSY 到 IDLE 的转换 (内存正常)"""
        # 先设置为 BUSY
        self.state_machine.update(self.cpu_threshold + 5, self.memory_threshold - 5)
        self.assertEqual(self.state_machine.get_state(), PetState.BUSY)
        
        # 重置 mock
        self.mock_event_system.dispatch_event.reset_mock()
        
        cpu_usage = self.cpu_threshold - 5
        memory_usage = self.memory_threshold - 5 # 内存正常
        changed = self.state_machine.update(cpu_usage, memory_usage)
        self.assertTrue(changed, "状态应已改变")
        self.assertEqual(self.state_machine.get_state(), PetState.IDLE, "状态应转换为 IDLE")
        self.assertEqual(self.state_machine.active_states[StateCategory.SYSTEM], PetState.IDLE, "系统状态应为 IDLE")
        
        # 验证事件发布
        self.mock_event_system.dispatch_event.assert_called_once()

    def test_stay_idle(self):
        """测试 IDLE 状态下保持 IDLE (内存正常)"""
        cpu_usage = self.cpu_threshold - 5
        memory_usage = self.memory_threshold - 5
        changed = self.state_machine.update(cpu_usage, memory_usage)
        self.assertFalse(changed, "状态不应改变")
        self.assertEqual(self.state_machine.get_state(), PetState.IDLE, "状态应保持 IDLE")

    def test_stay_busy(self):
        """测试 BUSY 状态下保持 BUSY (内存正常)"""
        self.state_machine.update(self.cpu_threshold + 5, self.memory_threshold - 5)
        self.assertEqual(self.state_machine.get_state(), PetState.BUSY)
        
        cpu_usage = self.cpu_threshold + 10
        memory_usage = self.memory_threshold - 5
        changed = self.state_machine.update(cpu_usage, memory_usage)
        self.assertFalse(changed, "状态不应改变")
        self.assertEqual(self.state_machine.get_state(), PetState.BUSY, "状态应保持 BUSY")

    def test_cpu_threshold_edge_case_idle(self):
        """测试CPU阈值边界情况 (略低于阈值应为 IDLE, 内存正常)"""
        cpu_usage = self.cpu_threshold - 0.1
        memory_usage = self.memory_threshold - 5
        self.state_machine.update(cpu_usage, memory_usage) # 可能初始就是IDLE，但确保update被调用
        self.assertEqual(self.state_machine.get_state(), PetState.IDLE, "略低于CPU阈值应为 IDLE")

    def test_cpu_threshold_edge_case_busy(self):
        """测试CPU阈值边界情况 (刚好达到阈值应为 BUSY, 内存正常)"""
        cpu_usage = self.cpu_threshold
        memory_usage = self.memory_threshold - 5
        self.state_machine.update(cpu_usage, memory_usage)
        self.assertEqual(self.state_machine.get_state(), PetState.BUSY, "达到CPU阈值应为 BUSY")

    # --- 内存警告相关测试 ---
    def test_memory_warning_when_idle_cpu(self):
        """测试当CPU空闲但内存过高时，进入 MEMORY_WARNING"""
        cpu_usage = self.cpu_threshold - 10
        memory_usage = self.memory_threshold + 5 # 内存过高
        changed = self.state_machine.update(cpu_usage, memory_usage)
        self.assertTrue(changed, "状态应变为 MEMORY_WARNING")
        self.assertEqual(self.state_machine.get_state(), PetState.MEMORY_WARNING)
        self.assertEqual(self.state_machine.active_states[StateCategory.SYSTEM], PetState.MEMORY_WARNING, 
                         "系统状态应为 MEMORY_WARNING")

    def test_memory_warning_when_busy_cpu(self):
        """测试当CPU繁忙且内存过高时，进入 MEMORY_WARNING"""
        cpu_usage = self.cpu_threshold + 10
        memory_usage = self.memory_threshold + 5 # 内存过高
        changed = self.state_machine.update(cpu_usage, memory_usage)
        self.assertTrue(changed, "状态应变为 MEMORY_WARNING")
        self.assertEqual(self.state_machine.get_state(), PetState.MEMORY_WARNING)

    def test_memory_warning_threshold_edge_case(self):
        """测试内存阈值边界情况 (刚好达到内存阈值应为 MEMORY_WARNING)"""
        cpu_usage = self.cpu_threshold - 5 # CPU不重要
        memory_usage = self.memory_threshold # 刚好达到内存阈值
        changed = self.state_machine.update(cpu_usage, memory_usage)
        self.assertTrue(changed, "状态应变为 MEMORY_WARNING")
        self.assertEqual(self.state_machine.get_state(), PetState.MEMORY_WARNING)

    def test_recovery_from_memory_warning_to_idle(self):
        """测试从 MEMORY_WARNING 恢复到 IDLE"""
        # 先进入 MEMORY_WARNING
        self.state_machine.update(self.cpu_threshold - 5, self.memory_threshold + 5)
        self.assertEqual(self.state_machine.get_state(), PetState.MEMORY_WARNING)

        cpu_usage = self.cpu_threshold - 5 # CPU 空闲
        memory_usage = self.memory_threshold - 5 # 内存恢复正常
        changed = self.state_machine.update(cpu_usage, memory_usage)
        self.assertTrue(changed, "状态应变为 IDLE")
        self.assertEqual(self.state_machine.get_state(), PetState.IDLE)

    def test_recovery_from_memory_warning_to_busy(self):
        """测试从 MEMORY_WARNING 恢复到 BUSY"""
        # 先进入 MEMORY_WARNING
        self.state_machine.update(self.cpu_threshold + 5, self.memory_threshold + 5) # CPU可以是繁忙的
        self.assertEqual(self.state_machine.get_state(), PetState.MEMORY_WARNING)

        cpu_usage = self.cpu_threshold + 5 # CPU 繁忙
        memory_usage = self.memory_threshold - 5 # 内存恢复正常
        changed = self.state_machine.update(cpu_usage, memory_usage)
        self.assertTrue(changed, "状态应变为 BUSY")
        self.assertEqual(self.state_machine.get_state(), PetState.BUSY)

    def test_stay_memory_warning(self):
        """测试 MEMORY_WARNING 状态下保持 (CPU和内存都高)"""
        # 先进入 MEMORY_WARNING
        self.state_machine.update(self.cpu_threshold + 5, self.memory_threshold + 5)
        self.assertEqual(self.state_machine.get_state(), PetState.MEMORY_WARNING)

        cpu_usage = self.cpu_threshold + 10 # CPU 保持繁忙
        memory_usage = self.memory_threshold + 10 # 内存保持过高
        changed = self.state_machine.update(cpu_usage, memory_usage)
        self.assertFalse(changed, "状态不应改变")
        self.assertEqual(self.state_machine.get_state(), PetState.MEMORY_WARNING)

    # --- 时间相关状态测试 ---
    def test_update_time_state(self):
        """测试更新时间状态"""
        changed = self.state_machine.update_time_state(PetState.MORNING)
        self.assertTrue(changed, "时间状态应已更新")
        self.assertEqual(self.state_machine.active_states[StateCategory.TIME], PetState.MORNING, 
                         "时间状态应为 MORNING")
        
        # 由于时间状态优先级低于默认系统状态，所以总体状态仍为系统状态
        self.assertEqual(self.state_machine.get_state(), PetState.IDLE, 
                         "由于优先级，总体状态仍应为 IDLE")
        
        # 验证事件发布
        self.mock_event_system.dispatch_event.assert_called_once()

    def test_update_time_state_priority(self):
        """测试时间状态和系统状态的优先级"""
        # 先设置系统状态为 IDLE
        self.state_machine.update(self.cpu_threshold - 5, self.memory_threshold - 5)
        
        # 设置时间状态为 NIGHT (优先级高于 IDLE)
        self.mock_event_system.dispatch_event.reset_mock()  # 重置mock
        self.state_machine.update_time_state(PetState.NIGHT)
        
        # 因为 NIGHT 优先级高于 IDLE
        self.assertEqual(self.state_machine.get_state(), PetState.NIGHT, 
                         "夜晚状态优先级应高于空闲状态")
        
        # 验证事件发布
        self.mock_event_system.dispatch_event.assert_called_once()

    def test_invalid_time_state(self):
        """测试设置无效的时间状态"""
        # 尝试设置一个非时间类别的状态
        changed = self.state_machine.update_time_state(PetState.BUSY)
        self.assertFalse(changed, "不应允许设置无效的时间状态")
        self.assertIsNone(self.state_machine.active_states[StateCategory.TIME], 
                          "时间状态应保持为 None")

    # --- 特殊日期测试 ---
    def test_set_special_date(self):
        """测试设置特殊日期状态"""
        changed = self.state_machine.set_special_date(PetState.NEW_YEAR)
        self.assertTrue(changed, "特殊日期状态应已设置")
        self.assertEqual(self.state_machine.active_states[StateCategory.SPECIAL_DATE], PetState.NEW_YEAR, 
                         "特殊日期状态应为 NEW_YEAR")
        
        # 由于特殊日期优先级高，所以总体状态应为特殊日期
        self.assertEqual(self.state_machine.get_state(), PetState.NEW_YEAR, 
                         "特殊日期应成为主导状态")
        
        # 验证事件发布
        self.mock_event_system.dispatch_event.assert_called_once()

    def test_memory_warning_vs_special_date(self):
        """测试内存警告与特殊日期的优先级"""
        # 设置内存警告
        self.state_machine.update(0, self.memory_threshold + 5)
        
        # 重置 mock
        self.mock_event_system.dispatch_event.reset_mock()
        
        # 设置特殊日期
        self.state_machine.set_special_date(PetState.NEW_YEAR)
        
        # 查看总体状态 (根据我们的优先级设置，内存警告应该比特殊日期高)
        self.assertEqual(self.state_machine.get_state(), PetState.MEMORY_WARNING, 
                         "内存警告优先级应高于特殊日期")

    def test_multiple_states_active(self):
        """测试多个状态同时活跃时的状态获取"""
        # 设置系统状态为 BUSY
        self.state_machine.update(self.cpu_threshold + 5, self.memory_threshold - 5)
        
        # 设置时间状态为 MORNING
        self.state_machine.update_time_state(PetState.MORNING)
        
        # 设置特殊日期
        self.state_machine.set_special_date(PetState.NEW_YEAR)
        
        # 获取所有活动状态
        active_states = self.state_machine.get_active_states()
        
        self.assertEqual(active_states[StateCategory.SYSTEM], PetState.BUSY)
        self.assertEqual(active_states[StateCategory.TIME], PetState.MORNING)
        self.assertEqual(active_states[StateCategory.SPECIAL_DATE], PetState.NEW_YEAR)
        
        # 检查总体状态 (应该是优先级最高的)
        self.assertEqual(self.state_machine.get_state(), PetState.NEW_YEAR, 
                         "总体状态应是优先级最高的状态")

    def test_cancel_special_date(self):
        """测试取消特殊日期状态"""
        # 先设置特殊日期
        self.state_machine.set_special_date(PetState.NEW_YEAR)
        self.assertEqual(self.state_machine.get_state(), PetState.NEW_YEAR)
        
        # 重置 mock
        self.mock_event_system.dispatch_event.reset_mock()
        
        # 取消特殊日期
        changed = self.state_machine.set_special_date(None)
        self.assertTrue(changed, "特殊日期状态应已取消")
        self.assertIsNone(self.state_machine.active_states[StateCategory.SPECIAL_DATE], 
                         "特殊日期状态应为 None")
        
        # 总体状态应回到系统状态
        self.assertEqual(self.state_machine.get_state(), PetState.IDLE, 
                         "总体状态应回到空闲")
        
        # 验证事件发布
        self.mock_event_system.dispatch_event.assert_called_once()

    # --- 细分的CPU负载状态测试 ---
    def test_cpu_load_states(self):
        """测试细分的CPU负载状态"""
        # 测试IDLE状态 (0-20%)
        self.state_machine.update(15.0, 20.0)
        self.assertEqual(self.state_machine.get_state(), PetState.IDLE)
        
        # 测试LIGHT_LOAD状态 (20-40%)
        self.state_machine.update(30.0, 20.0)
        self.assertEqual(self.state_machine.get_state(), PetState.LIGHT_LOAD)
        
        # 测试MODERATE_LOAD状态 (40-60%)
        self.state_machine.update(50.0, 20.0)
        self.assertEqual(self.state_machine.get_state(), PetState.MODERATE_LOAD)
        
        # 测试HEAVY_LOAD状态 (60-80%)
        self.state_machine.update(70.0, 20.0)
        self.assertEqual(self.state_machine.get_state(), PetState.HEAVY_LOAD)
        
        # 测试VERY_HEAVY_LOAD状态 (80-100%)
        self.state_machine.update(90.0, 20.0)
        self.assertEqual(self.state_machine.get_state(), PetState.VERY_HEAVY_LOAD)
    
    def test_cpu_critical_state(self):
        """测试CPU临界状态"""
        # 测试CPU_CRITICAL状态 (>95%)
        self.state_machine.update(96.0, 20.0)
        self.assertEqual(self.state_machine.get_state(), PetState.CPU_CRITICAL)
        
        # 验证CPU_CRITICAL优先级高于VERY_HEAVY_LOAD
        self.state_machine.update(96.0, 20.0, gpu_usage=95.0)  # 添加GPU_VERY_BUSY
        self.assertEqual(self.state_machine.get_state(), PetState.CPU_CRITICAL)
    
    # --- 多系统资源状态优先级测试 ---
    def test_memory_critical_highest_priority(self):
        """测试内存临界状态具有最高优先级"""
        # 设置所有资源都处于高负载状态，但内存达到临界值
        self.state_machine.update(
            cpu_usage=90.0,  # VERY_HEAVY_LOAD
            memory_usage=95.0,  # MEMORY_CRITICAL (>90%)
            gpu_usage=95.0,  # GPU_VERY_BUSY
            disk_usage=95.0,  # DISK_VERY_BUSY
            network_usage=95.0  # NETWORK_VERY_BUSY
        )
        
        # 内存临界状态应该具有最高优先级
        self.assertEqual(self.state_machine.get_state(), PetState.MEMORY_CRITICAL)
    
    def test_system_resource_priority(self):
        """测试系统资源状态的优先级排序"""
        # 按照声明的优先级，顺序应该是：
        # MEMORY_CRITICAL > CPU_CRITICAL > MEMORY_WARNING > VERY_HEAVY_LOAD > 
        # GPU_VERY_BUSY > DISK_VERY_BUSY > NETWORK_VERY_BUSY > ... 
        
        # 测试 MEMORY_WARNING vs VERY_HEAVY_LOAD
        self.state_machine.update(cpu_usage=90.0, memory_usage=75.0)
        self.assertEqual(self.state_machine.get_state(), PetState.MEMORY_WARNING)
        
        # 测试 GPU_VERY_BUSY vs HEAVY_LOAD
        self.state_machine.update(cpu_usage=70.0, memory_usage=50.0, gpu_usage=95.0)
        self.assertEqual(self.state_machine.get_state(), PetState.GPU_VERY_BUSY)
        
        # 测试 DISK_VERY_BUSY vs GPU_BUSY
        self.state_machine.update(cpu_usage=50.0, memory_usage=50.0, 
                                gpu_usage=75.0, disk_usage=95.0)
        self.assertEqual(self.state_machine.get_state(), PetState.DISK_VERY_BUSY)
        
        # 测试 NETWORK_VERY_BUSY vs DISK_BUSY
        self.state_machine.update(cpu_usage=50.0, memory_usage=50.0, 
                                gpu_usage=0.0, disk_usage=75.0, network_usage=95.0)
        self.assertEqual(self.state_machine.get_state(), PetState.NETWORK_VERY_BUSY)
    
    def test_all_resources_low(self):
        """测试所有资源都处于低负载状态时为SYSTEM_IDLE"""
        self.state_machine.update(cpu_usage=3.0, memory_usage=3.0, 
                               gpu_usage=3.0, disk_usage=3.0, network_usage=3.0)
        self.assertEqual(self.state_machine.get_state(), PetState.SYSTEM_IDLE)
    
    def test_update_multiple_resources(self):
        """测试同时更新多种系统资源时的状态优先级处理"""
        # 测试仅CPU高负载时的状态
        self.state_machine.update(
            cpu_usage=70.0,  # HEAVY_LOAD
            memory_usage=30.0,  # 正常
            gpu_usage=10.0,   # 正常
            disk_usage=10.0,  # 正常
            network_usage=10.0  # 正常
        )
        self.assertEqual(self.state_machine.get_state(), PetState.HEAVY_LOAD)
        
        # 测试CPU和内存都高负载时，应选择优先级更高的MEMORY_WARNING
        self.state_machine.update(
            cpu_usage=70.0,  # HEAVY_LOAD
            memory_usage=80.0,  # MEMORY_WARNING
            gpu_usage=10.0,   # 正常
            disk_usage=10.0,  # 正常
            network_usage=10.0  # 正常
        )
        self.assertEqual(self.state_machine.get_state(), PetState.MEMORY_WARNING)
        
        # 测试所有资源都高负载时，应选择优先级最高的MEMORY_CRITICAL
        self.state_machine.update(
            cpu_usage=90.0,  # VERY_HEAVY_LOAD
            memory_usage=95.0,  # MEMORY_CRITICAL
            gpu_usage=95.0,   # GPU_VERY_BUSY
            disk_usage=95.0,  # DISK_VERY_BUSY
            network_usage=95.0  # NETWORK_VERY_BUSY
        )
        self.assertEqual(self.state_machine.get_state(), PetState.MEMORY_CRITICAL)
        
        # 测试所有资源都极低时，应选择SYSTEM_IDLE
        self.state_machine.update(
            cpu_usage=2.0,
            memory_usage=2.0,
            gpu_usage=2.0,
            disk_usage=2.0,
            network_usage=2.0
        )
        self.assertEqual(self.state_machine.get_state(), PetState.SYSTEM_IDLE)
    
    def test_interaction_overrides_system_states(self):
        """测试交互状态会覆盖系统状态"""
        # 首先设置一个系统状态
        self.state_machine.update(cpu_usage=90.0, memory_usage=95.0)  # MEMORY_CRITICAL
        self.assertEqual(self.state_machine.get_state(), PetState.MEMORY_CRITICAL)
        
        # 设置交互状态
        self.state_machine.set_interaction_state(PetState.CLICKED)
        
        # 交互状态应该覆盖系统状态
        self.assertEqual(self.state_machine.get_state(), PetState.CLICKED)
        
        # 清除交互状态
        self.state_machine.set_interaction_state(None)
        
        # 应该恢复到系统状态
        self.assertEqual(self.state_machine.get_state(), PetState.MEMORY_CRITICAL)
    
    def test_interaction_using_integer_value(self):
        """测试使用整数值设置交互状态"""
        # 使用整数值设置交互状态 (PetState.CLICKED.value)
        self.state_machine.set_interaction_state(156)  # CLICKED的值
        
        # 应该成功设置交互状态
        self.assertEqual(self.state_machine.get_state(), PetState.CLICKED)
        self.assertEqual(self.state_machine.active_states[StateCategory.INTERACTION], PetState.CLICKED)


if __name__ == '__main__':
    unittest.main() 