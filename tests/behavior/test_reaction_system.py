"""
---------------------------------------------------------------
File name:                  test_reaction_system.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                桌宠反应系统单元测试
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
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
        test_event = {'x': 100, 'y': 100}
        
        # 测试点击事件处理
        self.mock_reaction_system.handle_event.return_value = True
        result = self.event_handler.on_mouse_click(test_event)
        self.assertTrue(result)
        self.mock_reaction_system.handle_event.assert_called_with('click', test_event)
        
        # 测试双击事件处理
        self.mock_reaction_system.reset_mock()
        self.event_handler.on_mouse_double_click(test_event)
        self.mock_reaction_system.handle_event.assert_called_with('double_click', test_event)
        
        # 测试拖拽开始事件处理
        self.mock_reaction_system.reset_mock()
        self.event_handler.on_drag_start(test_event)
        self.mock_reaction_system.handle_event.assert_called_with('drag_start', test_event)
        
        # 测试拖拽结束事件处理
        self.mock_reaction_system.reset_mock()
        self.event_handler.on_drag_end(test_event)
        self.mock_reaction_system.handle_event.assert_called_with('drag_end', test_event)
        
        # 测试悬停事件处理
        self.mock_reaction_system.reset_mock()
        self.event_handler.hover_start_time = None
        self.event_handler.on_mouse_hover(test_event)
        # 验证悬停事件包含了持续时间
        args, kwargs = self.mock_reaction_system.handle_event.call_args
        self.assertEqual(args[0], 'hover')
        self.assertIn('hover_duration', args[1])
        self.assertEqual(kwargs['debounce'], False)
        
        # 测试鼠标离开事件处理
        self.mock_reaction_system.reset_mock()
        self.event_handler.hover_start_time = time.time()
        self.event_handler.on_mouse_leave(test_event)
        self.assertIsNone(self.event_handler.hover_start_time)  # 应该重置悬停开始时间
        self.mock_reaction_system.handle_event.assert_called_with('leave', test_event)
        
        # 测试托盘菜单事件处理
        self.mock_reaction_system.reset_mock()
        self.event_handler.on_tray_menu_show(test_event)
        self.mock_reaction_system.handle_event.assert_called_with('tray_menu_show', test_event)


class TestDefaultReactions(unittest.TestCase):
    """测试默认反应规则"""
    
    def test_initialize_default_reactions(self):
        """测试初始化默认反应规则"""
        # 创建模拟反应系统
        mock_reaction_system = Mock()
        
        # 初始化默认反应
        initialize_default_reactions(mock_reaction_system)
        
        # 验证反应系统的add_reaction被调用了适当的次数
        # 我们至少应该有点击、双击、拖拽开始/结束、悬停、离开和托盘菜单这些基本反应
        self.assertGreaterEqual(mock_reaction_system.add_reaction.call_count, 7)


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