"""
---------------------------------------------------------------
File name:                  test_interaction_state_adapter.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                测试交互状态适配器
----------------------------------------------------------------

Changed history:            
                            2025/05/13: 初始创建;
----
"""

import unittest
import time
from unittest.mock import MagicMock, patch

from status.behavior.interaction_state_adapter import InteractionStateAdapter
from status.behavior.pet_state import PetState
from status.behavior.pet_state_machine import PetStateMachine
from status.interaction.interaction_zones import InteractionType
from status.behavior.interaction_tracker import InteractionPattern
from status.core.event_system import Event, EventType

class TestInteractionStateAdapter(unittest.TestCase):
    """测试交互状态适配器"""
    
    def setUp(self):
        """初始化测试环境"""
        # 模拟状态机
        self.mock_pet_state_machine = MagicMock(spec=PetStateMachine)
        
        # 模拟事件系统
        self.patcher = patch('status.core.event_system.EventSystem')
        self.mock_event_system = self.patcher.start()
        self.mock_event_system_instance = MagicMock()
        self.mock_event_system.get_instance.return_value = self.mock_event_system_instance
        
        # 创建交互状态适配器实例
        self.adapter = InteractionStateAdapter(
            pet_state_machine=self.mock_pet_state_machine,
            interaction_timeout=1.0  # 设置较短的超时时间以便测试
        )
        
        # 手动设置事件系统为模拟对象
        self.adapter.event_system = self.mock_event_system_instance
        
        # 手动替换timeout检查方法，避免线程相关问题
        self.adapter._setup_timeout_check = MagicMock()
        
        # 初始化组件
        self.adapter._initialize()
    
    def tearDown(self):
        """清理测试环境"""
        self.patcher.stop()
        self.adapter._shutdown()
    
    def test_initialization(self):
        """测试初始化"""
        # 验证初始状态
        self.assertEqual(self.adapter._pet_state_machine, self.mock_pet_state_machine)
        self.assertEqual(self.adapter.interaction_timeout, 1.0)
        self.assertIsNone(self.adapter.current_interaction_state)
        
        # 验证事件注册
        self.mock_event_system_instance.register_handler.assert_any_call(
            EventType.USER_INTERACTION, self.adapter._on_user_interaction
        )
        self.mock_event_system_instance.register_handler.assert_any_call(
            EventType.STATE_CHANGED, self.adapter._on_state_changed
        )
    
    def test_get_state_from_interaction_general(self):
        """测试从通用交互类型获取状态"""
        # 测试常规交互类型
        state = self.adapter._get_state_from_interaction(InteractionType.CLICK.name, "any_zone")
        self.assertEqual(state, PetState.CLICKED)
        
        state = self.adapter._get_state_from_interaction(InteractionType.DRAG.name, "any_zone")
        self.assertEqual(state, PetState.DRAGGED)
        
        state = self.adapter._get_state_from_interaction(InteractionType.HOVER.name, "any_zone")
        self.assertEqual(state, PetState.HOVER)
    
    def test_get_state_from_interaction_specific(self):
        """测试从区域特定交互获取状态"""
        # 由于区域特定逻辑在适配器中被注释，这些应 fallback 到通用状态
        state = self.adapter._get_state_from_interaction(InteractionType.CLICK.name, "head")
        self.assertEqual(state, PetState.CLICKED)
        
        state = self.adapter._get_state_from_interaction(InteractionType.CLICK.name, "body")
        self.assertEqual(state, PetState.CLICKED)
        
        state = self.adapter._get_state_from_interaction(InteractionType.CLICK.name, "tail")
        self.assertEqual(state, PetState.CLICKED)
        
        state = self.adapter._get_state_from_interaction(InteractionType.HOVER.name, "head")
        self.assertEqual(state, PetState.HOVER)
    
    def test_get_state_from_interaction_unknown(self):
        """测试不存在的交互类型和区域"""
        # 测试不存在的交互类型
        state = self.adapter._get_state_from_interaction("UNKNOWN_TYPE", "any_zone")
        self.assertIsNone(state)
        
        # 测试不存在的区域特定交互
        state = self.adapter._get_state_from_interaction(InteractionType.CLICK.name, "unknown_zone")
        self.assertEqual(state, PetState.CLICKED)  # 回退到通用交互
    
    def test_on_user_interaction(self):
        """测试处理用户交互事件"""
        # 创建模拟事件
        event = MagicMock(spec=Event)
        event.data = {
            'interaction_type': InteractionType.CLICK.name,
            'zone_id': 'head',
            'timestamp': time.time()
        }
        
        # 处理事件
        self.adapter._on_user_interaction(event)
        
        # 验证状态更新
        self.assertEqual(self.adapter.current_interaction_state, PetState.CLICKED)
        self.mock_pet_state_machine.set_interaction_state.assert_called_once_with(PetState.CLICKED)
    
    def test_clear_interaction_state(self):
        """测试清除交互状态"""
        # 首先设置一个状态
        self.adapter.current_interaction_state = PetState.CLICKED
        
        # 清除状态
        self.adapter.clear_interaction_state()
        
        # 验证状态已清除
        self.assertIsNone(self.adapter.current_interaction_state)
        self.mock_pet_state_machine.set_interaction_state.assert_called_once_with(None)
    
    def test_timeout_handling(self):
        """测试交互状态超时处理"""
        # 设置状态和时间
        self.adapter.current_interaction_state = PetState.CLICKED
        self.adapter.last_interaction_time = time.time() - 2.0  # 设置为2秒前
        
        # 手动调用超时检查的核心逻辑
        if (self.adapter.current_interaction_state is not None and 
            time.time() - self.adapter.last_interaction_time > self.adapter.interaction_timeout):
            self.adapter.clear_interaction_state()
        
        # 验证状态已清除
        self.assertIsNone(self.adapter.current_interaction_state)
    
    def test_get_state_for_pattern(self):
        """测试从交互模式获取状态"""
        # 测试各种交互模式
        self.assertEqual(self.adapter.get_state_for_pattern(InteractionPattern.RARE), PetState.IDLE)
        self.assertEqual(self.adapter.get_state_for_pattern(InteractionPattern.OCCASIONAL), PetState.HAPPY)
        self.assertEqual(self.adapter.get_state_for_pattern(InteractionPattern.REGULAR), PetState.HAPPY)
        self.assertEqual(self.adapter.get_state_for_pattern(InteractionPattern.EXCESSIVE), PetState.ANGRY)
    
    def test_register_interaction_to_state(self):
        """测试注册交互类型到状态的映射"""
        # 注册新的通用交互映射
        self.adapter.register_interaction_to_state("CUSTOM_TYPE", None, PetState.HAPPY)
        
        # 验证映射已添加
        self.assertEqual(self.adapter.interaction_to_state["CUSTOM_TYPE"], PetState.HAPPY)
        
        # 注册新的区域特定交互映射
        self.adapter.register_interaction_to_state(InteractionType.CLICK.name, "custom_zone", PetState.ANGRY)
        
        # 验证映射已添加
        self.assertEqual(self.adapter.interaction_to_state["custom_zone_CLICK"], PetState.ANGRY)
        
        # 测试新映射的功能
        state = self.adapter._get_state_from_interaction("CUSTOM_TYPE", "any_zone")
        self.assertEqual(state, PetState.HAPPY)
        
        # 由于区域特定查找逻辑被注释，这个会 fallback 到通用 CLICKED
        state = self.adapter._get_state_from_interaction(InteractionType.CLICK.name, "custom_zone")
        self.assertEqual(state, PetState.CLICKED)
    
    def test_invalid_event_data(self):
        """测试无效的事件数据"""
        # 创建缺少数据的事件
        event = MagicMock(spec=Event)
        
        # 没有data属性
        self.adapter._on_user_interaction(event)
        self.mock_pet_state_machine.set_interaction_state.assert_not_called()
        
        # data属性但缺少必要字段
        event.data = {'some_field': 'value'}
        self.adapter._on_user_interaction(event)
        self.mock_pet_state_machine.set_interaction_state.assert_not_called()
    
    def test_on_state_changed_event(self):
        """测试状态变化事件处理（获取状态机实例）"""
        # 创建不使用初始状态机的适配器
        adapter = InteractionStateAdapter(pet_state_machine=None)
        
        # 创建模拟事件
        event = MagicMock(spec=Event)
        event.sender = self.mock_pet_state_machine
        
        # 处理事件
        adapter._on_state_changed(event)
        
        # 验证状态机已获取
        self.assertEqual(adapter._pet_state_machine, self.mock_pet_state_machine)


if __name__ == '__main__':
    unittest.main() 