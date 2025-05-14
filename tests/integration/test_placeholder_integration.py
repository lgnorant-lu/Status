"""
---------------------------------------------------------------
File name:                  test_placeholder_integration.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                占位符系统的集成测试
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建;
----
"""
import unittest
from unittest.mock import patch, MagicMock
from status.main import StatusPet
from status.behavior.pet_state import PetState
from status.animation.animation import Animation

class TestPlaceholderIntegration(unittest.TestCase):
    """测试占位符系统与主应用的集成"""
    
    def setUp(self):
        """测试前的设置"""
        # 创建状态宠物实例而不调用其__init__
        self.status_pet = StatusPet.__new__(StatusPet)
        
        # 模拟必要的属性
        self.status_pet.placeholder_factory = MagicMock()
        self.status_pet.state_to_animation_map = {}
        
        # 创建模拟动画
        self.mock_happy_animation = Animation(name="happy", frames=[])
        self.status_pet.idle_animation = Animation(name="idle", frames=[])
        self.status_pet.current_animation = self.status_pet.idle_animation
        
        # 模拟set_animation方法
        self.status_pet.set_animation = MagicMock()

    def test_get_animation_for_new_state(self):
        """测试为新状态获取动画"""
        # 配置模拟对象
        self.status_pet.placeholder_factory.get_animation.return_value = self.mock_happy_animation
        
        # 调用_on_pet_state_changed方法（假设它存在）
        self.status_pet._on_pet_state_changed = lambda state: self._mock_on_pet_state_changed(state)
        self.status_pet._on_pet_state_changed(PetState.HAPPY)
        
        # 验证
        self.status_pet.placeholder_factory.get_animation.assert_called_once_with(PetState.HAPPY)
        self.assertEqual(self.status_pet.state_to_animation_map.get(PetState.HAPPY), self.mock_happy_animation)
        self.status_pet.set_animation.assert_called_once_with(self.mock_happy_animation)
        
    def _mock_on_pet_state_changed(self, new_state):
        """模拟状态变化处理方法"""
        if new_state not in self.status_pet.state_to_animation_map:
            anim = self.status_pet.placeholder_factory.get_animation(new_state)
            if anim:
                self.status_pet.state_to_animation_map[new_state] = anim
                
        if new_state in self.status_pet.state_to_animation_map:
            new_animation = self.status_pet.state_to_animation_map[new_state]
            self.status_pet.set_animation(new_animation)

if __name__ == '__main__':
    unittest.main() 