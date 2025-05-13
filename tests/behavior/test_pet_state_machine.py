"""
---------------------------------------------------------------
File name:                  test_pet_state_machine.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                测试宠物状态机逻辑
----------------------------------------------------------------
"""

import unittest
import os
import sys

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from status.behavior.pet_state_machine import PetStateMachine
from status.behavior.pet_state import PetState

class TestPetStateMachine(unittest.TestCase):
    """测试宠物状态机逻辑"""

    def setUp(self):
        """每个测试用例执行前的设置"""
        self.state_machine = PetStateMachine()
        self.cpu_threshold = self.state_machine.cpu_threshold # 假设阈值在状态机中可访问
        self.memory_threshold = self.state_machine.memory_threshold # 新增

    def test_initial_state(self):
        """测试初始状态是否为 IDLE"""
        self.assertEqual(self.state_machine.get_state(), PetState.IDLE, "初始状态应为 IDLE")

    # --- CPU 相关测试 ---
    def test_transition_idle_to_busy(self):
        """测试从 IDLE 到 BUSY 的转换 (内存正常)"""
        cpu_usage = self.cpu_threshold + 5
        memory_usage = self.memory_threshold - 5 # 内存正常
        changed = self.state_machine.update(cpu_usage, memory_usage)
        self.assertTrue(changed, "状态应已改变")
        self.assertEqual(self.state_machine.get_state(), PetState.BUSY, "状态应转换为 BUSY")

    def test_transition_busy_to_idle(self):
        """测试从 BUSY 到 IDLE 的转换 (内存正常)"""
        # 先设置为 BUSY
        self.state_machine.update(self.cpu_threshold + 5, self.memory_threshold - 5)
        self.assertEqual(self.state_machine.get_state(), PetState.BUSY)
        
        cpu_usage = self.cpu_threshold - 5
        memory_usage = self.memory_threshold - 5 # 内存正常
        changed = self.state_machine.update(cpu_usage, memory_usage)
        self.assertTrue(changed, "状态应已改变")
        self.assertEqual(self.state_machine.get_state(), PetState.IDLE, "状态应转换为 IDLE")

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

if __name__ == '__main__':
    unittest.main() 