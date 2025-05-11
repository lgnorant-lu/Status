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
from PyQt6.QtCore import QRect, QPoint

# 导入被测试的模块
from status.behavior.decision_maker import (
    DecisionMaker, Decision, DecisionRule
)
from status.behavior.environment_sensor import EnvironmentSensor, DesktopObject
from status.behavior.behavior_manager import BehaviorManager
from status.behavior.state_machine import StateMachine


class TestDecisionRule(unittest.TestCase):
    """测试决策规则"""

    def setUp(self):
        """每次测试前的准备工作"""
        # 创建模拟的环境感知器
        self.mock_env_sensor = Mock(spec=EnvironmentSensor)
        
        # 创建模拟的行为管理器
        self.mock_behavior_manager = Mock(spec=BehaviorManager)
        
        # 创建模拟的状态机
        self.mock_state_machine = Mock(spec=StateMachine)
        
        # 创建模拟的实体
        self.mock_entity = Mock()
        self.mock_entity.behavior_manager = self.mock_behavior_manager
        self.mock_entity.state_machine = self.mock_state_machine
        
        # 创建一个简单的决策规则
        self.condition = lambda entity, env_sensor: True  # 总是返回True的条件
        self.action = lambda entity: entity.behavior_manager.execute_behavior("test_behavior")
        self.rule = DecisionRule(
            name="test_rule", 
            condition=self.condition,
            action=self.action,
            priority=10
        )
        
    def test_rule_initialization(self):
        """测试规则初始化"""
        self.assertEqual(self.rule.name, "test_rule")
        self.assertEqual(self.rule.priority, 10)
        self.assertEqual(self.rule.condition, self.condition)
        self.assertEqual(self.rule.action, self.action)
        
    def test_evaluate_condition(self):
        """测试条件评估"""
        # 测试条件返回True的情况
        self.assertTrue(self.rule.evaluate(self.mock_entity, self.mock_env_sensor))
        
        # 创建一个返回False的条件
        false_condition = lambda entity, env_sensor: False
        false_rule = DecisionRule(
            name="false_rule",
            condition=false_condition,
            action=self.action,
            priority=5
        )
        self.assertFalse(false_rule.evaluate(self.mock_entity, self.mock_env_sensor))
        
    def test_execute_action(self):
        """测试执行动作"""
        self.rule.execute(self.mock_entity)
        self.mock_behavior_manager.execute_behavior.assert_called_once_with("test_behavior")
        
    def test_screen_position_rule(self):
        """测试基于屏幕位置的规则"""
        # 设置模拟环境感知器的行为
        self.mock_env_sensor.get_window_position.return_value = QRect(10, 20, 100, 100)
        
        # 创建一个检查窗口位置的条件
        position_condition = lambda entity, env_sensor: env_sensor.get_window_position().x() < 50
        
        rule = DecisionRule(
            name="position_rule",
            condition=position_condition,
            action=self.action,
            priority=20
        )
        
        # 应该返回True，因为x=10 < 50
        self.assertTrue(rule.evaluate(self.mock_entity, self.mock_env_sensor))
        
        # 改变窗口位置
        self.mock_env_sensor.get_window_position.return_value = QRect(100, 20, 100, 100)
        
        # 应该返回False，因为x=100 > 50
        self.assertFalse(rule.evaluate(self.mock_entity, self.mock_env_sensor))


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
        # 创建相同的决策
        same_decision = Decision(
            behavior_id="test_behavior",
            params={"param1": "value1"},
            priority=10
        )
        self.assertEqual(self.decision, same_decision)
        
        # 创建不同行为的决策
        different_behavior = Decision(
            behavior_id="other_behavior",
            params={"param1": "value1"},
            priority=10
        )
        self.assertNotEqual(self.decision, different_behavior)
        
        # 创建不同参数的决策
        different_params = Decision(
            behavior_id="test_behavior",
            params={"param2": "value2"},
            priority=10
        )
        self.assertNotEqual(self.decision, different_params)
        
        # 创建不同优先级的决策
        different_priority = Decision(
            behavior_id="test_behavior",
            params={"param1": "value1"},
            priority=20
        )
        self.assertNotEqual(self.decision, different_priority)
        
    def test_decision_comparison(self):
        """测试决策比较（基于优先级）"""
        # 创建较低优先级的决策
        lower_priority = Decision(
            behavior_id="low_behavior",
            params={},
            priority=5
        )
        
        # 创建较高优先级的决策
        higher_priority = Decision(
            behavior_id="high_behavior",
            params={},
            priority=15
        )
        
        # 测试比较操作符
        self.assertTrue(lower_priority < self.decision)
        self.assertTrue(self.decision < higher_priority)
        self.assertTrue(higher_priority > self.decision)
        self.assertTrue(self.decision > lower_priority)


class TestDecisionMaker(unittest.TestCase):
    """测试决策系统"""
    
    def setUp(self):
        """每次测试前的准备工作"""
        # 创建模拟的环境感知器
        self.mock_env_sensor = Mock(spec=EnvironmentSensor)
        
        # 创建模拟的实体
        self.mock_entity = Mock()
        self.mock_behavior_manager = Mock(spec=BehaviorManager)
        self.mock_state_machine = Mock(spec=StateMachine)
        self.mock_entity.behavior_manager = self.mock_behavior_manager
        self.mock_entity.state_machine = self.mock_state_machine
        
        # 创建决策系统
        self.decision_maker = DecisionMaker(self.mock_entity)
        
        # 添加一些测试规则
        self.rule1 = DecisionRule(
            name="rule1",
            condition=lambda entity, env_sensor: True,  # 始终为真
            action=lambda entity: entity.behavior_manager.execute_behavior("behavior1"),
            priority=10
        )
        
        self.rule2 = DecisionRule(
            name="rule2",
            condition=lambda entity, env_sensor: False,  # 始终为假
            action=lambda entity: entity.behavior_manager.execute_behavior("behavior2"),
            priority=20
        )
        
        self.rule3 = DecisionRule(
            name="rule3",
            condition=lambda entity, env_sensor: True,  # 始终为真
            action=lambda entity: entity.behavior_manager.execute_behavior("behavior3"),
            priority=5
        )
        
        # 将规则添加到决策系统
        self.decision_maker.add_rule(self.rule1)
        self.decision_maker.add_rule(self.rule2)
        self.decision_maker.add_rule(self.rule3)
        
    def test_add_rule(self):
        """测试添加规则"""
        # 创建新规则
        new_rule = DecisionRule(
            name="new_rule",
            condition=lambda entity, env_sensor: True,
            action=lambda entity: None,
            priority=15
        )
        
        # 添加规则
        self.decision_maker.add_rule(new_rule)
        
        # 验证规则已添加
        self.assertIn(new_rule, self.decision_maker.rules)
        
    def test_remove_rule(self):
        """测试移除规则"""
        # 移除规则
        self.decision_maker.remove_rule("rule1")
        
        # 验证规则已移除
        rule_names = [rule.name for rule in self.decision_maker.rules]
        self.assertNotIn("rule1", rule_names)
        
    def test_find_rule_by_name(self):
        """测试通过名称查找规则"""
        # 查找存在的规则
        found_rule = self.decision_maker.find_rule("rule1")
        self.assertEqual(found_rule, self.rule1)
        
        # 查找不存在的规则
        not_found = self.decision_maker.find_rule("non_existent")
        self.assertIsNone(not_found)
        
    def test_make_decision(self):
        """测试做出决策"""
        # 设置环境感知器
        patch_env_sensor = patch.object(
            EnvironmentSensor, 'get_instance', 
            return_value=self.mock_env_sensor
        )
        
        with patch_env_sensor:
            # 调用决策方法
            result = self.decision_maker.make_decision()
            
            # 验证结果包含满足条件的最高优先级规则
            self.assertEqual(result.behavior_id, "behavior1")
            
            # 验证执行了决策
            self.mock_behavior_manager.execute_behavior.assert_called_once_with(
                "behavior1", 
                params=None
            )
        
    def test_no_decision_when_no_rules_match(self):
        """测试没有规则匹配时的情况"""
        # 清除所有规则
        self.decision_maker.rules.clear()
        
        # 添加一个永远不匹配的规则
        never_match_rule = DecisionRule(
            name="never_match",
            condition=lambda entity, env_sensor: False,
            action=lambda entity: entity.behavior_manager.execute_behavior("never_executed"),
            priority=100
        )
        self.decision_maker.add_rule(never_match_rule)
        
        # 设置环境感知器
        patch_env_sensor = patch.object(
            EnvironmentSensor, 'get_instance', 
            return_value=self.mock_env_sensor
        )
        
        with patch_env_sensor:
            # 调用决策方法
            result = self.decision_maker.make_decision()
            
            # 验证没有做出决策
            self.assertIsNone(result)
            self.mock_behavior_manager.execute_behavior.assert_not_called()
    
    def test_decision_with_parameters(self):
        """测试带参数的决策"""
        # 创建一个返回参数的规则
        params_rule = DecisionRule(
            name="params_rule",
            condition=lambda entity, env_sensor: True,
            action=lambda entity: entity.behavior_manager.execute_behavior(
                "parameterized_behavior", 
                {"speed": 10, "direction": "left"}
            ),
            priority=30
        )
        self.decision_maker.add_rule(params_rule)
        
        # 设置环境感知器
        patch_env_sensor = patch.object(
            EnvironmentSensor, 'get_instance', 
            return_value=self.mock_env_sensor
        )
        
        with patch_env_sensor:
            # 调用决策方法
            result = self.decision_maker.make_decision()
            
            # 验证决策包含参数
            self.assertEqual(result.behavior_id, "parameterized_behavior")
            self.assertEqual(result.params, {"speed": 10, "direction": "left"})
            
            # 验证执行了决策
            self.mock_behavior_manager.execute_behavior.assert_called_once_with(
                "parameterized_behavior", 
                params={"speed": 10, "direction": "left"}
            )
    
    def test_environment_based_decisions(self):
        """测试基于环境的决策"""
        # 设置环境感知器的模拟返回值
        self.mock_env_sensor.get_window_position.return_value = QRect(10, 20, 100, 100)
        self.mock_env_sensor.get_screen_boundaries.return_value = {
            'width': 1920, 'height': 1080, 'x': 0, 'y': 0
        }
        self.mock_env_sensor.detect_desktop_objects.return_value = [
            DesktopObject(title="Test Window", rect=QRect(200, 200, 300, 300))
        ]
        
        # 创建基于环境的规则
        edge_rule = DecisionRule(
            name="edge_rule",
            condition=lambda entity, env_sensor: (
                env_sensor.get_window_position().x() < 50  # 靠近左边缘
            ),
            action=lambda entity: entity.behavior_manager.execute_behavior(
                "move_right", {"speed": 5}
            ),
            priority=50
        )
        self.decision_maker.add_rule(edge_rule)
        
        # 设置环境感知器
        patch_env_sensor = patch.object(
            EnvironmentSensor, 'get_instance', 
            return_value=self.mock_env_sensor
        )
        
        with patch_env_sensor:
            # 调用决策方法
            result = self.decision_maker.make_decision()
            
            # 验证基于环境的决策
            self.assertEqual(result.behavior_id, "move_right")
            self.assertEqual(result.params, {"speed": 5})
            
            # 改变环境条件
            self.mock_env_sensor.get_window_position.return_value = QRect(100, 20, 100, 100)
            
            # 重新调用决策方法，这次应该选择次高优先级规则
            self.mock_behavior_manager.execute_behavior.reset_mock()
            result = self.decision_maker.make_decision()
            
            # 在排除了edge_rule后，rule1是优先级最高的规则(优先级为10)
            self.assertEqual(result.behavior_id, "behavior1")
    
    def test_state_based_decisions(self):
        """测试基于状态的决策"""
        # 设置状态机的模拟返回值
        self.mock_state_machine.is_in_state.return_value = True
        
        # 创建基于状态的规则
        state_rule = DecisionRule(
            name="state_rule",
            condition=lambda entity, env_sensor: entity.state_machine.is_in_state("idle"),
            action=lambda entity: entity.behavior_manager.execute_behavior("play_animation"),
            priority=60
        )
        self.decision_maker.add_rule(state_rule)
        
        # 设置环境感知器
        patch_env_sensor = patch.object(
            EnvironmentSensor, 'get_instance', 
            return_value=self.mock_env_sensor
        )
        
        with patch_env_sensor:
            # 调用决策方法
            result = self.decision_maker.make_decision()
            
            # 验证基于状态的决策
            self.assertEqual(result.behavior_id, "play_animation")
            
            # 改变状态条件
            self.mock_state_machine.is_in_state.return_value = False
            
            # 重新调用决策方法，这次应该选择另一个规则
            self.mock_behavior_manager.execute_behavior.reset_mock()
            result = self.decision_maker.make_decision()
            
            # 验证选择了不同的规则（因为state_rule不再匹配）
            self.assertNotEqual(result.behavior_id, "play_animation")


if __name__ == '__main__':
    unittest.main() 