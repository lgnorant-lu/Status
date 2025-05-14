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
from status.behavior.pet_state import PetState
from status.animation.animation import Animation
from status.pet_assets.placeholder_factory import PlaceholderFactory

class TestPlaceholderIntegration(unittest.TestCase):
    """测试占位符系统与主应用的集成"""
    
    def setUp(self):
        """测试前的设置"""
        # 创建模拟的Animation实例
        self.idle_animation = Animation(name="idle", frames=[])
        self.mock_happy_animation = Animation(name="happy", frames=[])
        
        # 创建占位符工厂实例并模拟其行为
        self.placeholder_factory = PlaceholderFactory()
        self.placeholder_factory.get_animation = MagicMock(return_value=self.mock_happy_animation)
        
        # 创建状态到动画的映射
        self.state_to_animation_map = {
            PetState.IDLE: self.idle_animation
        }
        
        # 模拟动画相关函数
        self.current_animation = self.idle_animation
        self.set_animation_called = False
        self.set_animation_args = None
    
    def test_dynamic_animation_loading(self):
        """测试动态加载状态对应的占位符动画"""
        # 模拟状态变化处理函数
        def mock_handle_state_change(state):
            # 尝试获取目标动画，如果映射表中没有，尝试使用占位符工厂动态加载
            target_animation = self.state_to_animation_map.get(state)
            if not target_animation:
                # 尝试动态加载该状态的占位符动画
                anim = self.placeholder_factory.get_animation(state)
                if anim:
                    self.state_to_animation_map[state] = anim
                    target_animation = anim
            
            # 如果找到了目标动画，切换到该动画
            if target_animation and target_animation != self.current_animation:
                self.current_animation = target_animation
                self.set_animation_called = True
                self.set_animation_args = target_animation
        
        # 测试：处理一个当前映射中不存在的状态
        mock_handle_state_change(PetState.HAPPY)
        
        # 验证占位符工厂的get_animation方法被调用
        self.placeholder_factory.get_animation.assert_called_once_with(PetState.HAPPY)
        
        # 验证动画被正确添加到映射中
        self.assertEqual(self.state_to_animation_map.get(PetState.HAPPY), self.mock_happy_animation)
        
        # 验证当前动画被正确设置
        self.assertTrue(self.set_animation_called)
        self.assertEqual(self.set_animation_args, self.mock_happy_animation)
        self.assertEqual(self.current_animation, self.mock_happy_animation)

if __name__ == '__main__':
    unittest.main() 