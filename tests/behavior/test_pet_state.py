"""
---------------------------------------------------------------
File name:                  test_pet_state.py
Author:                     Ignorant-lu
Date created:               2025/05/16
Description:                PetState 枚举的单元测试
----------------------------------------------------------------

Changed history:            
                            2025/05/16: 初始创建;
----
"""

import unittest
from status.behavior.pet_state import PetState

class TestPetState(unittest.TestCase):
    """测试 PetState 枚举"""

    def test_basic_states_exist(self):
        """测试基础和关键状态成员是否存在"""
        self.assertIsNotNone(PetState.IDLE)
        self.assertIsNotNone(PetState.LIGHT_LOAD)
        self.assertIsNotNone(PetState.MODERATE_LOAD)
        self.assertIsNotNone(PetState.HEAVY_LOAD)
        self.assertIsNotNone(PetState.VERY_HEAVY_LOAD)
        self.assertIsNotNone(PetState.MEMORY_WARNING)
        self.assertIsNotNone(PetState.LOW_BATTERY)
        self.assertIsNotNone(PetState.MORNING)
        self.assertIsNotNone(PetState.NEW_YEAR)
        self.assertIsNotNone(PetState.HAPPY)
        self.assertIsNotNone(PetState.CLICKED)

    def test_compatibility_states_mapping(self):
        """测试兼容性状态 (BUSY, VERY_BUSY) 是否正确映射"""       
        self.assertEqual(PetState.BUSY, PetState.MODERATE_LOAD)
        self.assertEqual(PetState.VERY_BUSY, PetState.HEAVY_LOAD)
        self.assertEqual(PetState.CPU_CRITICAL, PetState.VERY_HEAVY_LOAD)

    def test_state_values_are_unique(self):
        """测试所有枚举成员的值是否唯一"""
        state_values = [state.value for state in PetState]
        self.assertEqual(len(state_values), len(set(state_values)), "PetState 枚举值不唯一")

    # 如果未来 is_interaction_state 等方法被启用，添加相应的测试
    # def test_is_interaction_state_method(self):
    #     self.assertTrue(PetState.is_interaction_state(PetState.HAPPY.value))
    #     self.assertTrue(PetState.is_interaction_state(PetState.CLICKED.value))
    #     self.assertFalse(PetState.is_interaction_state(PetState.IDLE.value))
    #     self.assertFalse(PetState.is_interaction_state(PetState.MORNING.value))

if __name__ == '__main__':
    unittest.main() 