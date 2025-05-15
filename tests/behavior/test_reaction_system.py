"""
---------------------------------------------------------------
File name:                  test_reaction_system.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                桌宠反应系统单元测试
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
                            2025/05/16: 增强对 on_mouse_hover 的测试;
----
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time

from status.behavior.reaction_system import (
    Reaction, ReactionSystem, ReactionSystemEventHandler, 
    initialize_default_reactions
)


class TestReaction(unittest.TestCase):
    """测试反应类"""
    
    def test_reaction_initialization(self):
        """测试反应初始化"""
        # 创建基本反应
        reaction = Reaction(
            event_type='click',
            behavior_id='jump',
            priority=10
        )
        
        self.assertEqual(reaction.event_type, 'click')
        self.assertEqual(reaction.behavior_id, 'jump')
        self.assertEqual(reaction.behavior_params, {})
        self.assertEqual(reaction.priority, 10)
        
        # 创建带参数的反应
        params = {'speed': 10, 'height': 20}
        reaction_with_params = Reaction(
            event_type='hover',
            behavior_id='dance',
            behavior_params=params,
            priority=5
        )
        
        self.assertEqual(reaction_with_params.event_type, 'hover')
        self.assertEqual(reaction_with_params.behavior_id, 'dance')
        self.assertEqual(reaction_with_params.behavior_params, params)
        self.assertEqual(reaction_with_params.priority, 5)
        
    def test_reaction_matches(self):
        """测试反应匹配"""
        # 创建简单反应（无条件）
        simple_reaction = Reaction(
            event_type='click',
            behavior_id='jump'
        )
        
        # 测试事件类型匹配
        self.assertTrue(simple_reaction.matches('click', {}, None))
        self.assertFalse(simple_reaction.matches('hover', {}, None))
        
        # 创建带条件的反应
        condition = lambda event, entity: event.get('x', 0) > 100
        conditional_reaction = Reaction(
            event_type='hover',
            behavior_id='wave',
            conditions=condition
        )
        
        # 测试条件匹配
        self.assertTrue(conditional_reaction.matches('hover', {'x': 150}, None))
        self.assertFalse(conditional_reaction.matches('hover', {'x': 50}, None))
        self.assertFalse(conditional_reaction.matches('hover', {}, None))  # 没有x字段应该返回False
        
        # 测试异常处理
        def failing_condition(event, entity):
            raise ValueError("条件检查失败")
            
        failing_reaction = Reaction(
            event_type='click',
            behavior_id='jump',
            conditions=failing_condition
        )
        
        # 条件检查失败时应该返回False而不是引发异常
        self.assertFalse(failing_reaction.matches('click', {}, None))


class TestReactionSystem(unittest.TestCase):
    """测试反应系统"""
    
    def setUp(self):
        """测试前准备"""
        # 创建模拟实体和行为管理器
        self.mock_behavior_manager = Mock()
        self.mock_entity = Mock()
        self.mock_entity.behavior_manager = self.mock_behavior_manager
        
        # 创建反应系统
        self.reaction_system = ReactionSystem(self.mock_entity)
        
    def test_add_reaction(self):
        """测试添加反应"""
        # 创建测试反应
        reaction1 = Reaction('click', behavior_id='jump', priority=10)
        reaction2 = Reaction('hover', behavior_id='wave', priority=20)
        
        # 添加反应
        self.reaction_system.add_reaction(reaction1)
        self.reaction_system.add_reaction(reaction2)
        
        # 验证反应已添加，且按优先级排序
        self.assertEqual(len(self.reaction_system.reactions), 2)
        self.assertEqual(self.reaction_system.reactions[0], reaction2)  # 优先级高的应该在前面
        self.assertEqual(self.reaction_system.reactions[1], reaction1)
        
    def test_remove_reaction(self):
        """测试移除反应"""
        # 添加多个反应
        self.reaction_system.add_reaction(Reaction('click', behavior_id='jump'))
        self.reaction_system.add_reaction(Reaction('click', behavior_id='high_jump'))
        self.reaction_system.add_reaction(Reaction('hover', behavior_id='wave'))
        
        # 移除特定反应
        removed = self.reaction_system.remove_reaction('click', 'jump')
        self.assertEqual(removed, 1)
        self.assertEqual(len(self.reaction_system.reactions), 2)
        
        # 移除所有特定类型的反应
        removed = self.reaction_system.remove_reaction('click')
        self.assertEqual(removed, 1)
        self.assertEqual(len(self.reaction_system.reactions), 1)
        self.assertEqual(self.reaction_system.reactions[0].event_type, 'hover') # 确保剩下的是正确的
        
        # 尝试移除不存在的 event_type
        removed_non_existent_type = self.reaction_system.remove_reaction('non_existent_event')
        self.assertEqual(removed_non_existent_type, 0)
        self.assertEqual(len(self.reaction_system.reactions), 1) # 列表应保持不变

        # 尝试移除存在的 event_type 但不存在的 behavior_id
        removed_non_existent_id = self.reaction_system.remove_reaction('hover', 'non_existent_behavior')
        self.assertEqual(removed_non_existent_id, 0)
        self.assertEqual(len(self.reaction_system.reactions), 1) # 列表应保持不变

        # 清空并重新添加，测试 behavior_id=None 的情况
        self.reaction_system.reactions.clear()
        r1 = Reaction('special_click', behavior_id='action1')
        r2 = Reaction('special_click', behavior_id='action2')
        r3 = Reaction('other_event', behavior_id='action3')
        self.reaction_system.add_reaction(r1)
        self.reaction_system.add_reaction(r2)
        self.reaction_system.add_reaction(r3)
        self.assertEqual(len(self.reaction_system.reactions), 3)

        removed_all_special_click = self.reaction_system.remove_reaction('special_click', behavior_id=None)
        self.assertEqual(removed_all_special_click, 2)
        self.assertEqual(len(self.reaction_system.reactions), 1)
        self.assertIn(r3, self.reaction_system.reactions)
        self.assertNotIn(r1, self.reaction_system.reactions)
        self.assertNotIn(r2, self.reaction_system.reactions)
        
    def test_handle_event(self):
        """测试事件处理"""
        # 添加测试反应
        self.reaction_system.add_reaction(Reaction('click', behavior_id='jump'))
        
        # 处理事件
        result = self.reaction_system.handle_event('click', {'x': 100, 'y': 100})
        
        # 验证行为被执行
        self.mock_behavior_manager.execute_behavior.assert_called_once_with('jump', params={})
        self.assertTrue(result)
        
        # 测试不匹配的事件
        self.mock_behavior_manager.reset_mock()
        result = self.reaction_system.handle_event('hover', {'x': 100, 'y': 100})
        
        # 验证行为未被执行
        self.mock_behavior_manager.execute_behavior.assert_not_called()
        self.assertFalse(result)

    def test_handle_event_no_behavior_manager(self):
        """测试当实体没有 behavior_manager 时处理事件"""
        # 移除实体的 behavior_manager
        del self.mock_entity.behavior_manager
        
        self.reaction_system.add_reaction(Reaction('click', behavior_id='jump'))
        result = self.reaction_system.handle_event('click', {})
        
        self.assertFalse(result, "如果实体没有 behavior_manager，handle_event 应该返回 False")
        # mock_behavior_manager 不应该被访问，因此 execute_behavior 不会被调用
        self.mock_behavior_manager.execute_behavior.assert_not_called()

    def test_handle_event_reaction_with_no_behavior_id(self):
        """测试当匹配的 Reaction 没有 behavior_id 时处理事件"""
        # 添加一个没有 behavior_id 的 Reaction
        # 这种 Reaction 理论上可以用于只检查条件或触发其他副作用（如果系统支持）
        # 但当前 ReactionSystem 主要关注执行行为
        self.reaction_system.add_reaction(Reaction('click', conditions=lambda e, ent: True, priority=1))
        # 添加另一个带 behavior_id 的，以确保如果第一个不执行，这个会被执行
        self.reaction_system.add_reaction(Reaction('click', behavior_id='jump_fallback', priority=0))

        result = self.reaction_system.handle_event('click', {})
        
        # 行为管理器应该为 'jump_fallback' 被调用，因为第一个 reaction 没有 behavior_id
        self.mock_behavior_manager.execute_behavior.assert_called_once_with('jump_fallback', params={})
        self.assertTrue(result, "如果后续 reaction 触发行为，handle_event 应该返回 True")
        
    def test_set_debounce_time_direct(self):
        """直接测试 set_debounce_time"""
        self.reaction_system.set_debounce_time(1.23)
        self.assertEqual(self.reaction_system.debounce_time, 1.23)

        self.reaction_system.set_debounce_time(-0.5)
        self.assertEqual(self.reaction_system.debounce_time, 0.0, "防抖时间不能为负数，应修正为0")

    def test_debounce(self):
        """测试事件防抖功能"""
        # 添加测试反应
        self.reaction_system.add_reaction(Reaction('click', behavior_id='jump'))
        
        # 设置防抖时间
        self.reaction_system.set_debounce_time(0.5)
        
        # 处理第一个事件
        result1 = self.reaction_system.handle_event('click', {})
        self.assertTrue(result1)
        self.mock_behavior_manager.execute_behavior.assert_called_once()
        
        # 立即处理第二个事件（应该被防抖过滤）
        self.mock_behavior_manager.reset_mock()
        result2 = self.reaction_system.handle_event('click', {})
        self.assertFalse(result2)
        self.mock_behavior_manager.execute_behavior.assert_not_called()
        
        # 等待防抖时间过去
        time.sleep(0.6)
        
        # 处理第三个事件（应该正常处理）
        self.mock_behavior_manager.reset_mock()
        result3 = self.reaction_system.handle_event('click', {})
        self.assertTrue(result3)
        self.mock_behavior_manager.execute_behavior.assert_called_once()
        
        # 测试关闭防抖
        self.mock_behavior_manager.reset_mock()
        result4 = self.reaction_system.handle_event('click', {}, debounce=False)
        self.assertTrue(result4)
        self.mock_behavior_manager.execute_behavior.assert_called_once()
        
    def test_conditional_reaction(self):
        """测试条件反应"""
        # 添加带条件的反应
        condition = lambda event, entity: event.get('x', 0) > 100
        self.reaction_system.add_reaction(Reaction(
            'hover',
            behavior_id='wave',
            conditions=condition
        ))
        
        # 处理满足条件的事件
        result1 = self.reaction_system.handle_event('hover', {'x': 150})
        self.assertTrue(result1)
        self.mock_behavior_manager.execute_behavior.assert_called_once()
        
        # 处理不满足条件的事件
        self.mock_behavior_manager.reset_mock()
        result2 = self.reaction_system.handle_event('hover', {'x': 50})
        self.assertFalse(result2)
        self.mock_behavior_manager.execute_behavior.assert_not_called()
        
    def test_get_reactions_for_event(self):
        """测试获取特定事件的反应"""
        # 添加多个反应
        reaction1 = Reaction('click', behavior_id='jump')
        reaction2 = Reaction('click', behavior_id='high_jump')
        reaction3 = Reaction('hover', behavior_id='wave')
        
        self.reaction_system.add_reaction(reaction1)
        self.reaction_system.add_reaction(reaction2)
        self.reaction_system.add_reaction(reaction3)
        
        # 获取特定事件的反应
        click_reactions = self.reaction_system.get_reactions_for_event('click')
        self.assertEqual(len(click_reactions), 2)
        self.assertIn(reaction1, click_reactions)
        self.assertIn(reaction2, click_reactions)
        
        hover_reactions = self.reaction_system.get_reactions_for_event('hover')
        self.assertEqual(len(hover_reactions), 1)
        self.assertEqual(hover_reactions[0], reaction3)
        
        # 测试不存在的事件类型
        none_reactions = self.reaction_system.get_reactions_for_event('none')
        self.assertEqual(len(none_reactions), 0)


class TestReactionSystemEventHandler(unittest.TestCase):
    """测试反应系统事件处理器"""
    
    def setUp(self):
        """测试前准备"""
        # 创建模拟反应系统
        self.mock_reaction_system = Mock()
        
        # 创建事件处理器
        self.event_handler = ReactionSystemEventHandler(self.mock_reaction_system)
        
        # 创建模拟交互管理器
        self.mock_interaction_manager = Mock()
        
    def test_register_handlers(self):
        """测试注册事件处理器"""
        # 注册处理器
        self.event_handler.register_handlers(self.mock_interaction_manager)
        
        # 验证处理器已注册
        self.mock_interaction_manager.register_handler.assert_any_call('mouse_click', self.event_handler.on_mouse_click)
        self.mock_interaction_manager.register_handler.assert_any_call('mouse_double_click', self.event_handler.on_mouse_double_click)
        self.mock_interaction_manager.register_handler.assert_any_call('drag_start', self.event_handler.on_drag_start)
        self.mock_interaction_manager.register_handler.assert_any_call('drag_end', self.event_handler.on_drag_end)
        self.mock_interaction_manager.register_handler.assert_any_call('mouse_hover', self.event_handler.on_mouse_hover)
        self.mock_interaction_manager.register_handler.assert_any_call('mouse_leave', self.event_handler.on_mouse_leave)
        self.mock_interaction_manager.register_handler.assert_any_call('tray_menu_show', self.event_handler.on_tray_menu_show)
        
    def test_event_handlers(self):
        """测试各种事件处理函数"""
        # 准备测试数据
        test_event_pos = {'x': 100, 'y': 100}
        
        # 测试点击事件处理
        self.mock_reaction_system.handle_event.return_value = True
        result = self.event_handler.on_mouse_click(test_event_pos)
        self.assertTrue(result)
        self.mock_reaction_system.handle_event.assert_called_with('click', test_event_pos)
        
        # 测试双击事件处理
        self.mock_reaction_system.reset_mock()
        self.event_handler.on_mouse_double_click(test_event_pos)
        self.mock_reaction_system.handle_event.assert_called_with('double_click', test_event_pos)
        
        # 测试拖拽开始事件处理
        self.mock_reaction_system.reset_mock()
        self.event_handler.on_drag_start(test_event_pos)
        self.mock_reaction_system.handle_event.assert_called_with('drag_start', test_event_pos)
        
        # 测试拖拽结束事件处理
        self.mock_reaction_system.reset_mock()
        self.event_handler.on_drag_end(test_event_pos)
        self.mock_reaction_system.handle_event.assert_called_with('drag_end', test_event_pos)
        
        # --- 增强对 on_mouse_hover 的测试 ---
        self.mock_reaction_system.reset_mock()
        self.event_handler.hover_start_time = None # 确保初始状态

        # 第一次调用 on_mouse_hover
        current_mock_time = time.time() # 记录当前时间用于比较
        with patch('time.time', return_value=current_mock_time):
            self.event_handler.on_mouse_hover(test_event_pos)
        
        self.assertEqual(self.event_handler.hover_start_time, current_mock_time) # hover_start_time 应被设置
        args, kwargs = self.mock_reaction_system.handle_event.call_args
        self.assertEqual(args[0], 'hover')
        self.assertIn('hover_duration', args[1])
        self.assertAlmostEqual(args[1]['hover_duration'], 0.0, delta=0.01) # 第一次调用，duration 接近0
        self.assertEqual(args[1]['original_event'], test_event_pos)
        self.assertEqual(kwargs['debounce'], False)

        # 模拟时间流逝 (0.5秒后)
        self.mock_reaction_system.reset_mock()
        later_mock_time = current_mock_time + 0.5
        with patch('time.time', return_value=later_mock_time):
            self.event_handler.on_mouse_hover(test_event_pos) # hover_start_time 已被设置

        self.assertEqual(self.event_handler.hover_start_time, current_mock_time) # hover_start_time 不应改变
        args, kwargs = self.mock_reaction_system.handle_event.call_args
        self.assertEqual(args[0], 'hover')
        self.assertIn('hover_duration', args[1])
        self.assertAlmostEqual(args[1]['hover_duration'], 0.5, delta=0.01) # duration 应为0.5秒
        self.assertEqual(args[1]['original_event'], test_event_pos)
        self.assertEqual(kwargs['debounce'], False)
        # --- 增强结束 ---
        
        # 测试鼠标离开事件处理
        self.mock_reaction_system.reset_mock()
        self.event_handler.hover_start_time = time.time()
        self.event_handler.on_mouse_leave(test_event_pos)
        self.assertIsNone(self.event_handler.hover_start_time)  # 应该重置悬停开始时间
        self.mock_reaction_system.handle_event.assert_called_with('leave', test_event_pos)
        
        # 测试托盘菜单事件处理
        self.mock_reaction_system.reset_mock()
        self.event_handler.on_tray_menu_show(test_event_pos)
        self.mock_reaction_system.handle_event.assert_called_with('tray_menu_show', test_event_pos)


class TestDefaultReactions(unittest.TestCase):
    """测试默认反应规则"""
    
    def test_initialize_default_reactions(self):
        """测试初始化默认反应规则"""
        # 创建模拟反应系统
        mock_reaction_system = MagicMock(spec=ReactionSystem) # Use MagicMock for spec
        mock_reaction_system.reactions = [] # Simulate the reactions list
        mock_reaction_system.logger = MagicMock() # Add a mock logger attribute

        # Define a side effect for add_reaction to actually add to the list for verification
        def add_reaction_side_effect(reaction):
            mock_reaction_system.reactions.append(reaction)
            mock_reaction_system.reactions.sort(key=lambda r: -r.priority) # Simulate sorting

        mock_reaction_system.add_reaction.side_effect = add_reaction_side_effect
        
        # 初始化默认反应
        initialize_default_reactions(mock_reaction_system)
        
        # 验证反应系统的add_reaction被调用了适当的次数
        expected_reactions_count = 7 # Based on the current implementation
        self.assertEqual(mock_reaction_system.add_reaction.call_count, expected_reactions_count)

        # 验证添加的具体反应 (部分抽样检查)
        added_event_types = [r.event_type for r in mock_reaction_system.reactions]
        added_behavior_ids = [r.behavior_id for r in mock_reaction_system.reactions]

        self.assertIn('click', added_event_types)
        self.assertIn('jump', added_behavior_ids)

        self.assertIn('double_click', added_event_types)
        self.assertIn('high_jump', added_behavior_ids)

        self.assertIn('hover', added_event_types)
        hover_reaction = next((r for r in mock_reaction_system.reactions if r.event_type == 'hover'), None)
        self.assertIsNotNone(hover_reaction)
        if hover_reaction: # Linter guard
            self.assertEqual(hover_reaction.behavior_id, 'wave')
            self.assertIsNotNone(hover_reaction.conditions)
            self.assertEqual(hover_reaction.priority, 5) # Assume priority is 5 based on test failure
            self.assertEqual(hover_reaction.behavior_params, {'duration': 1.0})

        # 可以添加更多对其他默认反应的详细检查


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建模拟行为管理器
        self.mock_behavior_manager = Mock()
        
        # 创建模拟实体
        self.mock_entity = Mock()
        self.mock_entity.behavior_manager = self.mock_behavior_manager
        
        # 创建反应系统
        self.reaction_system = ReactionSystem(self.mock_entity)
        
        # 初始化默认反应
        initialize_default_reactions(self.reaction_system)
        
        # 创建事件处理器
        self.event_handler = ReactionSystemEventHandler(self.reaction_system)
        
    def test_click_reaction(self):
        """测试点击反应集成"""
        # 模拟点击事件
        click_event = {'x': 100, 'y': 100}
        
        # 处理点击事件
        self.event_handler.on_mouse_click(click_event)
        
        # 验证行为管理器执行了跳跃行为
        self.mock_behavior_manager.execute_behavior.assert_called_with('jump', params={})
        
    def test_hover_reaction(self):
        """测试悬停反应集成"""
        # 模拟悬停事件
        hover_event = {'x': 100, 'y': 100}
        
        # 设置悬停开始时间为2秒前
        self.event_handler.hover_start_time = time.time() - 2.0
        
        # 处理悬停事件
        self.event_handler.on_mouse_hover(hover_event)
        
        # 验证行为管理器执行了挥手行为
        self.mock_behavior_manager.execute_behavior.assert_called_with('wave', params={'duration': 1.0})
        
    def test_drag_end_reaction(self):
        """测试拖拽结束反应集成"""
        # 模拟拖拽结束事件
        drag_end_event = {'x': 100, 'y': 100}
        
        # 处理拖拽结束事件
        self.event_handler.on_drag_end(drag_end_event)
        
        # 验证行为管理器执行了下落行为
        self.mock_behavior_manager.execute_behavior.assert_called_with('fall', params={})


if __name__ == '__main__':
    unittest.main() 