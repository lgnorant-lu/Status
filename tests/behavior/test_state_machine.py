"""
---------------------------------------------------------------
File name:                  test_state_machine.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                状态机单元测试
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import unittest
from unittest.mock import Mock, patch

# 导入状态机模块的所有类
from status.behavior.state_machine import (
    State, StateMachine, Condition, Transition, AndCondition, OrCondition
)


class TestState(unittest.TestCase):
    """测试状态基类"""

    def setUp(self):
        # 创建一个具体状态类用于测试
        class ConcreteState(State):
            def enter(self, entity):
                entity.on_enter_called = True
                
            def exit(self, entity):
                entity.on_exit_called = True
                
            def update(self, entity, delta_time):
                entity.on_update_called = True
                entity.update_delta = delta_time
                
            def check_transitions(self, entity):
                if hasattr(entity, 'should_transition') and entity.should_transition:
                    return "next_state"
                return None
                
        self.state_class = ConcreteState
        self.entity = Mock()
        self.state = self.state_class()
        
    def test_enter_method(self):
        """测试enter方法是否正确调用"""
        self.state.enter(self.entity)
        self.assertTrue(self.entity.on_enter_called)
        
    def test_exit_method(self):
        """测试exit方法是否正确调用"""
        self.state.exit(self.entity)
        self.assertTrue(self.entity.on_exit_called)
        
    def test_update_method(self):
        """测试update方法是否正确调用并传递delta_time"""
        delta_time = 0.016  # 60fps
        self.state.update(self.entity, delta_time)
        self.assertTrue(self.entity.on_update_called)
        self.assertEqual(self.entity.update_delta, delta_time)
        
    def test_check_transitions_with_no_transition(self):
        """测试当没有转换条件满足时check_transitions返回None"""
        self.entity.should_transition = False
        result = self.state.check_transitions(self.entity)
        self.assertIsNone(result)
        
    def test_check_transitions_with_transition(self):
        """测试当转换条件满足时check_transitions返回正确的下一个状态ID"""
        self.entity.should_transition = True
        result = self.state.check_transitions(self.entity)
        self.assertEqual(result, "next_state")


class TestStateMachine(unittest.TestCase):
    """测试状态机类"""

    def setUp(self):
        self.entity = Mock()
        self.state_machine = StateMachine(self.entity)
        
        # 创建测试状态
        self.state1 = Mock(spec=State)
        self.state2 = Mock(spec=State)
        self.global_state = Mock(spec=State)
        
        # 配置状态行为
        self.state1.check_transitions.return_value = None
        self.state2.check_transitions.return_value = None
        self.global_state.check_transitions.return_value = None
        
    def test_add_state(self):
        """测试添加状态"""
        self.state_machine.add_state("state1", self.state1)
        self.assertEqual(self.state_machine.states["state1"], self.state1)
        
    def test_set_current_state(self):
        """测试设置当前状态"""
        self.state_machine.add_state("state1", self.state1)
        self.state_machine.set_current_state("state1")
        
        self.assertEqual(self.state_machine.current_state, self.state1)
        self.state1.enter.assert_called_once_with(self.entity)
        
    def test_set_global_state(self):
        """测试设置全局状态"""
        self.state_machine.add_state("global", self.global_state)
        self.state_machine.set_global_state("global")
        
        self.assertEqual(self.state_machine.global_state, self.global_state)
        self.global_state.enter.assert_called_once_with(self.entity)
        
    def test_change_state(self):
        """测试状态切换"""
        # 添加状态
        self.state_machine.add_state("state1", self.state1)
        self.state_machine.add_state("state2", self.state2)
        
        # 设置初始状态
        self.state_machine.set_current_state("state1")
        self.state1.enter.assert_called_once_with(self.entity)
        
        # 清除调用历史
        self.state1.reset_mock()
        
        # 切换状态
        self.state_machine.change_state("state2")
        
        # 验证状态退出和进入调用
        self.state1.exit.assert_called_once_with(self.entity)
        self.state2.enter.assert_called_once_with(self.entity)
        
        # 验证当前状态和前一个状态
        self.assertEqual(self.state_machine.current_state, self.state2)
        self.assertEqual(self.state_machine.previous_state, self.state1)
        
    def test_revert_to_previous_state(self):
        """测试回退到前一个状态"""
        # 添加状态
        self.state_machine.add_state("state1", self.state1)
        self.state_machine.add_state("state2", self.state2)
        
        # 设置状态并切换
        self.state_machine.set_current_state("state1")
        self.state_machine.change_state("state2")
        
        # 清除调用历史
        self.state1.reset_mock()
        self.state2.reset_mock()
        
        # 回退到前一个状态
        self.state_machine.revert_to_previous_state()
        
        # 验证状态退出和进入调用
        self.state2.exit.assert_called_once_with(self.entity)
        self.state1.enter.assert_called_once_with(self.entity)
        
        # 验证当前状态和前一个状态
        self.assertEqual(self.state_machine.current_state, self.state1)
        self.assertEqual(self.state_machine.previous_state, self.state2)
        
    def test_update_with_no_state_change(self):
        """测试状态机更新，无状态变化"""
        # 添加状态
        self.state_machine.add_state("state1", self.state1)
        self.state_machine.add_state("global", self.global_state)
        
        # 设置状态
        self.state_machine.set_current_state("state1")
        self.state_machine.set_global_state("global")
        
        # 清除调用历史
        self.state1.reset_mock()
        self.global_state.reset_mock()
        
        # 配置状态不触发转换
        self.state1.check_transitions.return_value = None
        self.global_state.check_transitions.return_value = None
        
        # 更新状态机
        delta_time = 0.016
        self.state_machine.update(delta_time)
        
        # 验证状态更新调用
        self.global_state.update.assert_called_once_with(self.entity, delta_time)
        self.state1.update.assert_called_once_with(self.entity, delta_time)
        
        # 验证转换检查调用
        self.global_state.check_transitions.assert_called_once_with(self.entity)
        self.state1.check_transitions.assert_called_once_with(self.entity)
        
    def test_update_with_state_change(self):
        """测试状态机更新，有状态变化"""
        # 添加状态
        self.state_machine.add_state("state1", self.state1)
        self.state_machine.add_state("state2", self.state2)
        
        # 设置状态
        self.state_machine.set_current_state("state1")
        
        # 清除调用历史
        self.state1.reset_mock()
        
        # 配置状态触发转换
        self.state1.check_transitions.return_value = "state2"
        
        # 更新状态机
        delta_time = 0.016
        self.state_machine.update(delta_time)
        
        # 验证状态更新和转换调用
        self.state1.update.assert_called_once_with(self.entity, delta_time)
        self.state1.check_transitions.assert_called_once_with(self.entity)
        self.state1.exit.assert_called_once_with(self.entity)
        self.state2.enter.assert_called_once_with(self.entity)
        
        # 验证状态已变更
        self.assertEqual(self.state_machine.current_state, self.state2)
        
    def test_is_in_state(self):
        """测试当前状态检查"""
        # 添加状态
        self.state_machine.add_state("state1", self.state1)
        self.state_machine.add_state("state2", self.state2)
        
        # 设置状态
        self.state_machine.set_current_state("state1")
        
        # 验证状态检查
        self.assertTrue(self.state_machine.is_in_state("state1"))
        self.assertFalse(self.state_machine.is_in_state("state2"))
        

class TestCondition(unittest.TestCase):
    """测试状态转换条件"""

    def setUp(self):
        self.entity = Mock()
        
    def test_and_condition(self):
        """测试AND条件组合"""
        # 创建两个基本条件
        condition1 = Mock(spec=Condition)
        condition2 = Mock(spec=Condition)
        
        # 配置条件返回值
        condition1.evaluate.return_value = True
        condition2.evaluate.return_value = True
        
        # 创建AND条件
        and_condition = AndCondition([condition1, condition2])
        
        # 测试两个条件都为True
        self.assertTrue(and_condition.evaluate(self.entity))
        
        # 测试一个条件为False
        condition2.evaluate.return_value = False
        self.assertFalse(and_condition.evaluate(self.entity))
        
        # 测试两个条件都为False
        condition1.evaluate.return_value = False
        self.assertFalse(and_condition.evaluate(self.entity))
        
    def test_or_condition(self):
        """测试OR条件组合"""
        # 创建两个基本条件
        condition1 = Mock(spec=Condition)
        condition2 = Mock(spec=Condition)
        
        # 配置条件返回值
        condition1.evaluate.return_value = True
        condition2.evaluate.return_value = True
        
        # 创建OR条件
        or_condition = OrCondition([condition1, condition2])
        
        # 测试两个条件都为True
        self.assertTrue(or_condition.evaluate(self.entity))
        
        # 测试一个条件为False
        condition2.evaluate.return_value = False
        self.assertTrue(or_condition.evaluate(self.entity))
        
        # 测试两个条件都为False
        condition1.evaluate.return_value = False
        self.assertFalse(or_condition.evaluate(self.entity))


class TestTransition(unittest.TestCase):
    """测试状态转换"""

    def setUp(self):
        self.entity = Mock()
        self.condition = Mock(spec=Condition)
        self.transition = Transition("next_state", self.condition)
        
    def test_should_transition_when_condition_is_true(self):
        """测试当条件为True时应该转换"""
        self.condition.evaluate.return_value = True
        self.assertTrue(self.transition.should_transition(self.entity))
        self.condition.evaluate.assert_called_once_with(self.entity)
        
    def test_should_transition_when_condition_is_false(self):
        """测试当条件为False时不应该转换"""
        self.condition.evaluate.return_value = False
        self.assertFalse(self.transition.should_transition(self.entity))
        self.condition.evaluate.assert_called_once_with(self.entity)


if __name__ == '__main__':
    unittest.main() 