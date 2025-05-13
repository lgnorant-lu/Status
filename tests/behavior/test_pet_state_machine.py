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

from status.behavior.pet_state import PetState
from status.behavior.pet_state_machine import PetStateMachine

# 可以定义一个阈值常量，方便测试
TEST_BUSY_THRESHOLD = 30.0

class TestPetStateMachine(unittest.TestCase):
    """测试宠物状态机"""

    def setUp(self):
        """为每个测试设置状态机实例"""
        self.state_machine = PetStateMachine(busy_threshold=TEST_BUSY_THRESHOLD)

    def test_initial_state(self):
        """测试初始状态是否为 IDLE"""
        self.assertEqual(self.state_machine.get_state(), PetState.IDLE, "初始状态应为 IDLE")

    def test_transition_idle_to_busy(self):
        """测试从 IDLE 到 BUSY 的转换"""
        self.state_machine.update(TEST_BUSY_THRESHOLD + 10) # 高于阈值
        self.assertEqual(self.state_machine.get_state(), PetState.BUSY, "状态应转换为 BUSY")

    def test_transition_busy_to_idle(self):
        """测试从 BUSY 到 IDLE 的转换"""
        # 先设置为 BUSY 状态
        self.state_machine.current_state = PetState.BUSY
        self.state_machine.update(TEST_BUSY_THRESHOLD - 10) # 低于阈值
        self.assertEqual(self.state_machine.get_state(), PetState.IDLE, "状态应转换回 IDLE")

    def test_stay_idle(self):
        """测试 IDLE 状态下保持 IDLE"""
        self.state_machine.update(TEST_BUSY_THRESHOLD - 5) # 低于阈值
        self.assertEqual(self.state_machine.get_state(), PetState.IDLE, "状态应保持 IDLE")

    def test_stay_busy(self):
        """测试 BUSY 状态下保持 BUSY"""
        # 先设置为 BUSY 状态
        self.state_machine.current_state = PetState.BUSY
        self.state_machine.update(TEST_BUSY_THRESHOLD + 20) # 高于阈值
        self.assertEqual(self.state_machine.get_state(), PetState.BUSY, "状态应保持 BUSY")

    def test_threshold_edge_case_busy(self):
        """测试阈值边界情况 (刚好达到阈值应为 BUSY)"""
        self.state_machine.update(TEST_BUSY_THRESHOLD)
        self.assertEqual(self.state_machine.get_state(), PetState.BUSY, "达到阈值应为 BUSY")

    def test_threshold_edge_case_idle(self):
        """测试阈值边界情况 (略低于阈值应为 IDLE)"""
        self.state_machine.current_state = PetState.BUSY # Start as busy
        self.state_machine.update(TEST_BUSY_THRESHOLD - 0.1)
        self.assertEqual(self.state_machine.get_state(), PetState.IDLE, "略低于阈值应为 IDLE")

if __name__ == '__main__':
    unittest.main() 