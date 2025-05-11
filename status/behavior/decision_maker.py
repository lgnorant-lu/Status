"""
---------------------------------------------------------------
File name:                  decision_maker.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                决策系统，负责做出桌宠行为决策
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
                            2025/04/04: 修复测试问题;
----
"""

import logging
from typing import List, Callable, Dict, Any, Optional, Union

from status.behavior.environment_sensor import EnvironmentSensor


# 配置日志
logger = logging.getLogger(__name__)


class Decision:
    """
    决策类，表示一个行为决策结果
    
    决策包含行为ID、参数和优先级。
    """
    
    def __init__(self, behavior_id: str, params: Dict[str, Any] = None, priority: int = 0):
        """
        初始化决策
        
        Args:
            behavior_id (str): 行为ID
            params (dict, optional): 行为参数. 默认为None
            priority (int, optional): 决策优先级. 默认为0
        """
        self.behavior_id = behavior_id
        self.params = params or {}
        self.priority = priority
    
    def __eq__(self, other):
        """
        比较两个决策是否相等
        
        Args:
            other (Decision): 另一个决策对象
            
        Returns:
            bool: 是否相等
        """
        if not isinstance(other, Decision):
            return False
        return (self.behavior_id == other.behavior_id and
                self.params == other.params and
                self.priority == other.priority)
    
    def __lt__(self, other):
        """
        小于比较操作符，用于优先级排序
        
        Args:
            other (Decision): 另一个决策对象
            
        Returns:
            bool: 是否小于另一个决策
        """
        if not isinstance(other, Decision):
            return NotImplemented
        return self.priority < other.priority
    
    def __gt__(self, other):
        """
        大于比较操作符，用于优先级排序
        
        Args:
            other (Decision): 另一个决策对象
            
        Returns:
            bool: 是否大于另一个决策
        """
        if not isinstance(other, Decision):
            return NotImplemented
        return self.priority > other.priority


class DecisionRule:
    """
    决策规则类
    
    定义一个决策规则，包含条件、动作和优先级。
    """
    
    def __init__(self, name: str, condition: Callable, action: Callable, priority: int = 0):
        """
        初始化决策规则
        
        Args:
            name (str): 规则名称
            condition (callable): 条件函数，接收entity和env_sensor参数，返回bool
            action (callable): 动作函数，接收entity参数，执行决策动作
            priority (int, optional): 规则优先级. 默认为0
        """
        self.name = name
        self.condition = condition
        self.action = action
        self.priority = priority
    
    def evaluate(self, entity, env_sensor: EnvironmentSensor) -> bool:
        """
        评估规则条件是否满足
        
        Args:
            entity: 实体对象
            env_sensor (EnvironmentSensor): 环境感知器
            
        Returns:
            bool: 条件是否满足
        """
        try:
            return self.condition(entity, env_sensor)
        except Exception as e:
            logger.error(f"评估规则 '{self.name}' 条件时出错: {str(e)}")
            return False
    
    def execute(self, entity) -> None:
        """
        执行规则动作
        
        Args:
            entity: 实体对象
        """
        try:
            return self.action(entity)
        except Exception as e:
            logger.error(f"执行规则 '{self.name}' 动作时出错: {str(e)}")


class DecisionMaker:
    """
    决策系统
    
    负责根据环境和状态做出行为决策。
    """
    
    def __init__(self, entity):
        """
        初始化决策系统
        
        Args:
            entity: 拥有此决策系统的实体
        """
        self.entity = entity
        self.rules: List[DecisionRule] = []
        self.last_decision: Optional[Decision] = None
        logger.debug("决策系统已初始化")
    
    def add_rule(self, rule: DecisionRule) -> None:
        """
        添加决策规则
        
        Args:
            rule (DecisionRule): 决策规则
        """
        self.rules.append(rule)
        logger.debug(f"规则 '{rule.name}' 已添加到决策系统")
    
    def remove_rule(self, rule_name: str) -> bool:
        """
        移除决策规则
        
        Args:
            rule_name (str): 规则名称
            
        Returns:
            bool: 是否成功移除
        """
        initial_count = len(self.rules)
        self.rules = [rule for rule in self.rules if rule.name != rule_name]
        removed = len(self.rules) < initial_count
        
        if removed:
            logger.debug(f"规则 '{rule_name}' 已从决策系统移除")
        else:
            logger.warning(f"规则 '{rule_name}' 不存在，无法移除")
        
        return removed
    
    def find_rule(self, rule_name: str) -> Optional[DecisionRule]:
        """
        根据名称查找规则
        
        Args:
            rule_name (str): 规则名称
            
        Returns:
            DecisionRule or None: 找到的规则，如果不存在则返回None
        """
        for rule in self.rules:
            if rule.name == rule_name:
                return rule
        return None
    
    def make_decision(self) -> Optional[Decision]:
        """
        制定决策
        
        基于当前环境和状态评估所有规则，选择最高优先级的满足条件的规则，
        并执行相应动作。
        
        Returns:
            Decision or None: 决策结果，如果没有规则满足条件则返回None
        """
        # 获取环境感知器实例
        env_sensor = EnvironmentSensor.get_instance()
        
        # 找出所有满足条件的规则
        matching_rules = []
        for rule in self.rules:
            if rule.evaluate(self.entity, env_sensor):
                matching_rules.append(rule)
        
        if not matching_rules:
            logger.debug("没有规则满足条件，无法做出决策")
            return None
        
        # 按优先级排序
        matching_rules.sort(key=lambda r: r.priority, reverse=True)
        
        # 选择最高优先级的规则
        top_rule = matching_rules[0]
        logger.debug(f"选择规则 '{top_rule.name}' (优先级: {top_rule.priority})")
        
        # 执行规则动作并捕获返回的行为ID和参数
        behavior_id = None
        params = None
        
        # 创建一个mock对象来捕获execute_behavior的调用
        original_execute_behavior = self.entity.behavior_manager.execute_behavior
        
        def mock_execute_behavior(behavior_id_arg, params_arg=None):
            nonlocal behavior_id, params
            behavior_id = behavior_id_arg
            params = params_arg
            return original_execute_behavior(behavior_id_arg, params=params_arg)
        
        # 替换方法
        self.entity.behavior_manager.execute_behavior = mock_execute_behavior
        
        # 执行规则
        top_rule.execute(self.entity)
        
        # 恢复原方法
        self.entity.behavior_manager.execute_behavior = original_execute_behavior
        
        if behavior_id:
            # 创建决策对象
            decision = Decision(behavior_id, params, top_rule.priority)
            self.last_decision = decision
            logger.debug(f"已做出决策: 行为='{behavior_id}', 优先级={top_rule.priority}")
            return decision
        
        logger.warning(f"规则 '{top_rule.name}' 未能产生有效的行为决策")
        return None
    
    def get_last_decision(self) -> Optional[Decision]:
        """
        获取最近一次决策结果
        
        Returns:
            Decision or None: 最近的决策结果，如果没有则返回None
        """
        return self.last_decision
    
    def clear_rules(self) -> None:
        """
        清除所有规则
        """
        self.rules.clear()
        logger.debug("所有规则已清除")
    
    def update(self) -> Optional[Decision]:
        """
        更新决策系统
        
        评估规则并做出决策，但不执行动作。
        这对于预测性决策很有用。
        
        Returns:
            Decision or None: 决策结果，如果没有规则满足条件则返回None
        """
        return self.make_decision() 