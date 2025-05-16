"""
---------------------------------------------------------------
File name:                  test_decision_maker.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                决策系统单元测试
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
                            2025/04/04: 修复测试问题;
----
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import Optional, Tuple, Dict, Any

from PySide6.QtCore import QRect, QPoint

# 导入被测试的模块
from status.behavior.decision_maker import (
    DecisionMaker, Decision, DecisionRule
)
from status.behavior.environment_sensor import EnvironmentSensor, DesktopObject
from status.behavior.behavior_manager import BehaviorManager
# from status.behavior.state_machine import StateMachine # Assuming StateMachine might not be directly used by entity mock for these tests


class TestDecisionRule(unittest.TestCase):
    """测试决策规则"""

    def setUp(self):
        """每次测试前的准备工作"""
        self.mock_env_sensor = Mock(spec=EnvironmentSensor)
        self.mock_entity = Mock()
        
        # 重构后的 action，返回 (behavior_id, params, priority_override)
        self.action_return_value = ("test_behavior", {"param": "value"}, 15)
        self.mock_action_func = Mock(return_value=self.action_return_value)
        
        self.rule = DecisionRule(
            name="test_rule", 
            condition=lambda entity, env_sensor: True,
            action=self.mock_action_func, # 使用 mock action
            priority=10
        )
        
    def test_rule_initialization(self):
        """测试规则初始化"""
        self.assertEqual(self.rule.name, "test_rule")
        self.assertEqual(self.rule.priority, 10)
        self.assertTrue(callable(self.rule.condition))
        self.assertEqual(self.rule.action, self.mock_action_func)
        
    def test_evaluate_condition(self):
        """测试条件评估"""
        self.assertTrue(self.rule.evaluate(self.mock_entity, self.mock_env_sensor))
        
        false_condition = lambda entity, env_sensor: False
        false_rule = DecisionRule("false_rule", false_condition, self.mock_action_func, 5)
        self.assertFalse(false_rule.evaluate(self.mock_entity, self.mock_env_sensor))
        
    def test_evaluate_condition_with_exception(self):
        """测试条件评估时发生异常"""
        exception_condition = Mock(side_effect=Exception("Test condition error"))
        rule_with_exception = DecisionRule("exception_rule", exception_condition, self.mock_action_func)
        self.assertFalse(rule_with_exception.evaluate(self.mock_entity, self.mock_env_sensor))
        exception_condition.assert_called_once_with(self.mock_entity, self.mock_env_sensor)

    def test_execute_action_returns_value(self):
        """测试执行动作并返回预期的元组"""
        result = self.rule.execute(self.mock_entity)
        self.mock_action_func.assert_called_once_with(self.mock_entity)
        self.assertEqual(result, self.action_return_value)

    def test_execute_action_returns_none(self):
        """测试执行动作返回None"""
        action_returns_none = Mock(return_value=None)
        rule_action_none = DecisionRule("action_none_rule", lambda e, es: True, action_returns_none)
        result = rule_action_none.execute(self.mock_entity)
        action_returns_none.assert_called_once_with(self.mock_entity)
        self.assertIsNone(result)
        
    def test_execute_action_with_exception(self):
        """测试执行动作时发生异常"""
        exception_action = Mock(side_effect=Exception("Test action error"))
        rule_with_exception = DecisionRule("exception_action_rule", lambda e, es: True, exception_action)
        result = rule_with_exception.execute(self.mock_entity)
        exception_action.assert_called_once_with(self.mock_entity)
        self.assertIsNone(result) # 发生异常时 execute 应返回 None


class TestDecision(unittest.TestCase):
    """测试决策"""
    
    def setUp(self):
        """每次测试前的准备工作"""
        # 创建一个简单的决策
        self.decision = Decision(
            behavior_id="test_behavior",
            params={"param1": "value1"},
            priority=10
        )
        
    def test_decision_initialization(self):
        """测试决策初始化"""
        self.assertEqual(self.decision.behavior_id, "test_behavior")
        self.assertEqual(self.decision.params, {"param1": "value1"})
        self.assertEqual(self.decision.priority, 10)
        
    def test_decision_equality(self):
        """测试决策相等性"""
        same_decision = Decision("test_behavior", {"param1": "value1"}, 10)
        self.assertEqual(self.decision, same_decision)
        
        different_behavior = Decision("other_behavior", {"param1": "value1"}, 10)
        self.assertNotEqual(self.decision, different_behavior)
        
    def test_decision_comparison(self):
        """测试决策比较（基于优先级）"""
        lower_priority = Decision("low_behavior", {}, 5)
        higher_priority = Decision("high_behavior", {}, 15)
        
        self.assertTrue(lower_priority < self.decision)
        self.assertTrue(self.decision < higher_priority)
        self.assertTrue(higher_priority > self.decision)
        self.assertTrue(self.decision > lower_priority)
        self.assertFalse(self.decision < lower_priority)
        self.assertFalse(self.decision > higher_priority)


class TestDecisionMaker(unittest.TestCase):
    """测试决策系统（重构后）"""
    
    def setUp(self):
        """每次测试前的准备工作"""
        self.mock_env_sensor_patcher = patch('status.behavior.decision_maker.EnvironmentSensor')
        self.MockEnvironmentSensor = self.mock_env_sensor_patcher.start()
        self.mock_env_sensor_instance = self.MockEnvironmentSensor.get_instance.return_value
        
        self.mock_entity = Mock()
        # self.mock_entity.behavior_manager = Mock(spec=BehaviorManager) # Not directly used by make_decision now
        
        self.decision_maker = DecisionMaker(self.mock_entity)
        
    def tearDown(self):
        self.mock_env_sensor_patcher.stop()

    def test_add_and_remove_rule(self):
        """测试添加和移除规则"""
        rule = DecisionRule("test_rule", Mock(), Mock(), 10)
        self.decision_maker.add_rule(rule)
        self.assertIn(rule, self.decision_maker.rules)
        self.assertTrue(self.decision_maker.remove_rule("test_rule"))
        self.assertNotIn(rule, self.decision_maker.rules)
        self.assertFalse(self.decision_maker.remove_rule("non_existent_rule"))

    def test_find_rule(self):
        """测试查找规则"""
        rule = DecisionRule("find_me", Mock(), Mock(), 10)
        self.decision_maker.add_rule(rule)
        self.assertEqual(self.decision_maker.find_rule("find_me"), rule)
        self.assertIsNone(self.decision_maker.find_rule("not_found"))

    def test_make_decision_no_rules(self):
        """测试没有规则时无法做出决策"""
        decision = self.decision_maker.make_decision()
        self.assertIsNone(decision)

    def test_make_decision_no_matching_rules(self):
        """测试没有规则条件满足时无法做出决策"""
        mock_condition = Mock(return_value=False)
        rule = DecisionRule("no_match_rule", mock_condition, Mock(), 10)
        self.decision_maker.add_rule(rule)
        
        decision = self.decision_maker.make_decision()
        self.assertIsNone(decision)
        mock_condition.assert_called_once_with(self.mock_entity, self.mock_env_sensor_instance)

    def test_make_decision_selects_highest_priority_rule(self):
        """测试选择最高优先级的规则并返回其决策"""
        action_result_high = ("high_behavior", {"p": 1}, 25) # Action provides priority
        action_result_low = ("low_behavior", {"p": 2}, None)  # Action uses rule's priority

        mock_action_high = Mock(return_value=action_result_high)
        mock_action_low = Mock(return_value=action_result_low)

        rule_high_priority = DecisionRule("high_rule", Mock(return_value=True), mock_action_high, 20)
        rule_low_priority = DecisionRule("low_rule", Mock(return_value=True), mock_action_low, 10)
        
        self.decision_maker.add_rule(rule_low_priority) # Add low first
        self.decision_maker.add_rule(rule_high_priority) # Add high second, sorting will be tested by selection
        
        decision = self.decision_maker.make_decision()
        
        self.assertIsNotNone(decision)
        if decision:
            self.assertEqual(decision.behavior_id, "high_behavior")
            self.assertEqual(decision.params, {"p": 1})
            self.assertEqual(decision.priority, 25) # Priority from action_result_high
        mock_action_high.assert_called_once_with(self.mock_entity)
        mock_action_low.assert_not_called() # Lower priority rule's action should not be called

    def test_make_decision_iterates_if_top_rule_action_returns_none_or_no_behavior(self):
        """测试如果高优先级规则的动作不返回行为，则评估下一个规则"""
        action_no_behavior = Mock(return_value=(None, {}, 10)) # Action returns no behavior_id
        action_valid = Mock(return_value=("valid_behavior", {}, 5))

        rule_top_no_behavior = DecisionRule("top_no_behavior", Mock(return_value=True), action_no_behavior, 20)
        rule_next_valid = DecisionRule("next_valid", Mock(return_value=True), action_valid, 10)

        self.decision_maker.add_rule(rule_top_no_behavior)
        self.decision_maker.add_rule(rule_next_valid)

        decision = self.decision_maker.make_decision()
        self.assertIsNotNone(decision)
        if decision:
            self.assertEqual(decision.behavior_id, "valid_behavior")
        action_no_behavior.assert_called_once_with(self.mock_entity)
        action_valid.assert_called_once_with(self.mock_entity)


    def test_make_decision_action_returns_none(self):
        """测试规则的动作返回None时，make_decision返回None"""
        mock_action_returns_none = Mock(return_value=None)
        rule = DecisionRule("action_none", Mock(return_value=True), mock_action_returns_none, 10)
        self.decision_maker.add_rule(rule)
        
        decision = self.decision_maker.make_decision()
        self.assertIsNone(decision)
        mock_action_returns_none.assert_called_once_with(self.mock_entity)
        
    def test_make_decision_uses_rule_priority_if_action_priority_is_none(self):
        """测试当动作返回的优先级为None时，使用规则自身的优先级"""
        action_result = ("behavior_id", {"p": "test"}, None) # Priority_override is None
        mock_action = Mock(return_value=action_result)
        rule = DecisionRule("rule_priority_test", Mock(return_value=True), mock_action, 77)
        self.decision_maker.add_rule(rule)

        decision = self.decision_maker.make_decision()
        self.assertIsNotNone(decision)
        if decision:
            self.assertEqual(decision.priority, 77) # Should use rule's priority

    def test_update_method_calls_make_decision(self):
        """测试 update 方法调用 make_decision"""
        # This test assumes update() is essentially an alias or simple wrapper for make_decision()
        # If update() has more logic, this test would need to be expanded.
        with patch.object(self.decision_maker, 'make_decision', return_value="mock_decision_result") as mock_make_decision:
            result = self.decision_maker.update()
            mock_make_decision.assert_called_once()
            self.assertEqual(result, "mock_decision_result")


if __name__ == '__main__':
    unittest.main() 