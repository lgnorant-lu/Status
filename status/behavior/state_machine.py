"""
---------------------------------------------------------------
File name:                  state_machine.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                状态机核心实现
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import logging
from abc import ABC, abstractmethod


# 配置日志
logger = logging.getLogger(__name__)


class State(ABC):
    """状态基类
    
    定义状态接口，所有具体状态必须继承此类并实现所需方法。
    """
    
    @abstractmethod
    def enter(self, entity):
        """进入状态时调用
        
        当实体进入此状态时调用此方法。
        
        Args:
            entity: 拥有此状态的实体
        """
        pass
        
    @abstractmethod
    def exit(self, entity):
        """退出状态时调用
        
        当实体离开此状态时调用此方法。
        
        Args:
            entity: 拥有此状态的实体
        """
        pass
        
    @abstractmethod
    def update(self, entity, delta_time):
        """状态更新时调用
        
        当实体处于此状态时，每帧调用此方法。
        
        Args:
            entity: 拥有此状态的实体
            delta_time (float): 自上次更新以来的时间（秒）
        """
        pass
        
    def check_transitions(self, entity):
        """检查是否应该转换到其他状态
        
        检查是否满足转换条件，如果满足则返回下一个状态的ID。
        
        Args:
            entity: 拥有此状态的实体
            
        Returns:
            str: 下一个状态的ID，如果不需要转换则为None
        """
        return None


class StateMachine:
    """状态机
    
    管理实体的状态和状态转换。
    """
    
    def __init__(self, entity):
        """初始化状态机
        
        Args:
            entity: 拥有此状态机的实体
        """
        self.entity = entity
        self.states = {}  # 状态字典，key是状态ID，value是状态对象
        self.current_state = None  # 当前状态
        self.previous_state = None  # 上一个状态
        self.global_state = None  # 全局状态，每次更新都会调用
        
        logger.debug(f"状态机已初始化")

    def add_state(self, state_id, state):
        """添加状态到状态机
        
        Args:
            state_id (str): 状态ID
            state (State): 状态对象
            
        Returns:
            bool: 添加是否成功
        """
        if state_id in self.states:
            logger.warning(f"状态 {state_id} 已存在，将被覆盖")
            
        self.states[state_id] = state
        logger.debug(f"状态 {state_id} 已添加到状态机")
        return True
        
    def set_current_state(self, state_id):
        """设置当前状态
        
        设置当前状态并调用enter方法。
        
        Args:
            state_id (str): 状态ID
            
        Returns:
            bool: 设置是否成功
        """
        if state_id not in self.states:
            logger.error(f"状态 {state_id} 不存在")
            return False
            
        self.current_state = self.states[state_id]
        self.current_state.enter(self.entity)
        logger.debug(f"当前状态已设置为 {state_id}")
        return True
        
    def set_global_state(self, state_id):
        """设置全局状态
        
        设置全局状态并调用enter方法。
        
        Args:
            state_id (str): 状态ID
            
        Returns:
            bool: 设置是否成功
        """
        if state_id not in self.states:
            logger.error(f"状态 {state_id} 不存在")
            return False
            
        self.global_state = self.states[state_id]
        self.global_state.enter(self.entity)
        logger.debug(f"全局状态已设置为 {state_id}")
        return True
        
    def update(self, delta_time):
        """更新状态机
        
        更新全局状态和当前状态，检查状态转换。
        
        Args:
            delta_time (float): 自上次更新以来的时间（秒）
        """
        # 更新全局状态
        if self.global_state:
            self.global_state.update(self.entity, delta_time)
            
            # 检查全局状态是否触发转换
            next_state_id = self.global_state.check_transitions(self.entity)
            if next_state_id:
                self.change_state(next_state_id)
                return
        
        # 如果当前状态存在，更新当前状态
        if self.current_state:
            self.current_state.update(self.entity, delta_time)
            
            # 检查当前状态是否触发转换
            next_state_id = self.current_state.check_transitions(self.entity)
            if next_state_id:
                self.change_state(next_state_id)
        
    def change_state(self, new_state_id):
        """改变当前状态
        
        退出当前状态，进入新状态。
        
        Args:
            new_state_id (str): 新状态的ID
            
        Returns:
            bool: 改变是否成功
        """
        if new_state_id not in self.states:
            logger.error(f"状态 {new_state_id} 不存在")
            return False
            
        if not self.current_state:
            logger.warning("当前没有状态，直接设置新状态")
            return self.set_current_state(new_state_id)
            
        # 保存前一个状态
        self.previous_state = self.current_state
        
        # 退出当前状态
        self.current_state.exit(self.entity)
        
        # 进入新状态
        self.current_state = self.states[new_state_id]
        self.current_state.enter(self.entity)
        
        logger.debug(f"状态已从旧状态切换到 {new_state_id}")
        return True
        
    def revert_to_previous_state(self):
        """回到前一个状态
        
        退出当前状态，进入前一个状态。
        
        Returns:
            bool: 回退是否成功
        """
        if not self.previous_state:
            logger.warning("没有前一个状态，无法回退")
            return False
            
        # 交换当前状态和前一个状态
        current_state = self.current_state
        self.current_state = self.previous_state
        self.previous_state = current_state
        
        # 退出旧状态，进入新状态
        self.previous_state.exit(self.entity)
        self.current_state.enter(self.entity)
        
        logger.debug("已回退到前一个状态")
        return True
        
    def is_in_state(self, state_id):
        """检查是否处于指定状态
        
        Args:
            state_id (str): 状态ID
            
        Returns:
            bool: 是否处于指定状态
        """
        if not self.current_state:
            return False
            
        return self.current_state == self.states.get(state_id)


class Condition(ABC):
    """状态转换条件接口
    
    定义状态转换条件接口，所有具体条件必须继承此类并实现所需方法。
    """
    
    @abstractmethod
    def evaluate(self, entity):
        """评估条件是否满足
        
        Args:
            entity: 要评估条件的实体
            
        Returns:
            bool: 条件是否满足
        """
        pass


class AndCondition(Condition):
    """组合条件(AND)
    
    当所有子条件都满足时，此条件满足。
    """
    
    def __init__(self, conditions):
        """初始化AND条件
        
        Args:
            conditions (list): 条件列表
        """
        self.conditions = conditions
        
    def evaluate(self, entity):
        """评估条件是否满足
        
        当所有子条件都满足时返回True，否则返回False。
        
        Args:
            entity: 要评估条件的实体
            
        Returns:
            bool: 条件是否满足
        """
        return all(condition.evaluate(entity) for condition in self.conditions)
    
    
class OrCondition(Condition):
    """组合条件(OR)
    
    当任一子条件满足时，此条件满足。
    """
    
    def __init__(self, conditions):
        """初始化OR条件
        
        Args:
            conditions (list): 条件列表
        """
        self.conditions = conditions
        
    def evaluate(self, entity):
        """评估条件是否满足
        
        当任一子条件满足时返回True，否则返回False。
        
        Args:
            entity: 要评估条件的实体
            
        Returns:
            bool: 条件是否满足
        """
        return any(condition.evaluate(entity) for condition in self.conditions)


class Transition:
    """状态转换定义
    
    定义从一个状态到另一个状态的转换条件。
    """
    
    def __init__(self, target_state_id, condition):
        """初始化转换
        
        Args:
            target_state_id (str): 目标状态ID
            condition (Condition): 触发此转换的条件
        """
        self.target_state_id = target_state_id
        self.condition = condition
        
    def should_transition(self, entity):
        """检查是否应该转换
        
        评估条件是否满足，决定是否应该转换到目标状态。
        
        Args:
            entity: 要评估条件的实体
            
        Returns:
            bool: 是否应该转换
        """
        return self.condition.evaluate(entity) 