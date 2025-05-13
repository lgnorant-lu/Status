"""
---------------------------------------------------------------
File name:                  decay.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                定义各种衰减函数，用于模拟数值随时间的衰减
----------------------------------------------------------------

Changed history:            
                            2025/05/13: 初始创建;
----
"""

import math
from typing import Callable, Optional
from abc import ABC, abstractmethod


class DecayFunction(ABC):
    """衰减函数基类"""
    
    @abstractmethod
    def compute(self, value: float, elapsed_time: float) -> float:
        """计算衰减后的值
        
        Args:
            value: 原始值
            elapsed_time: 经过的时间（秒）
            
        Returns:
            float: 衰减后的值
        """
        pass


class ExponentialDecay(DecayFunction):
    """指数衰减
    
    formula: value * exp(-decay_factor * elapsed_time)
    """
    
    def __init__(self, decay_factor: float = 0.1):
        """初始化指数衰减函数
        
        Args:
            decay_factor: 衰减因子，值越大衰减越快
        """
        self.decay_factor = decay_factor
    
    def compute(self, value: float, elapsed_time: float) -> float:
        """计算指数衰减
        
        Args:
            value: 原始值
            elapsed_time: 经过的时间（秒）
            
        Returns:
            float: 衰减后的值
        """
        return value * math.exp(-self.decay_factor * elapsed_time)
    
    def get_half_life(self) -> float:
        """获取半衰期（值减半所需的时间）
        
        Returns:
            float: 半衰期（秒）
        """
        return math.log(2) / self.decay_factor


class LinearDecay(DecayFunction):
    """线性衰减
    
    formula: value * (1 - decay_factor * elapsed_time)
    如果结果小于0，则返回0
    """
    
    def __init__(self, decay_factor: float = 0.1):
        """初始化线性衰减函数
        
        Args:
            decay_factor: 衰减因子，表示每单位时间衰减的比例
        """
        self.decay_factor = decay_factor
    
    def compute(self, value: float, elapsed_time: float) -> float:
        """计算线性衰减
        
        Args:
            value: 原始值
            elapsed_time: 经过的时间（秒）
            
        Returns:
            float: 衰减后的值
        """
        result = value * (1 - self.decay_factor * elapsed_time)
        return max(0.0, result)
    
    def get_zero_time(self, value: float = 1.0) -> float:
        """获取值衰减到0所需的时间
        
        Args:
            value: 初始值，默认为1.0
            
        Returns:
            float: 衰减到0所需的时间（秒）
        """
        return 1.0 / self.decay_factor


class StepDecay(DecayFunction):
    """阶梯衰减
    
    在特定时间点有固定的衰减率
    """
    
    def __init__(self, steps: list, decay_rates: list):
        """初始化阶梯衰减函数
        
        Args:
            steps: 时间点列表，必须升序排列
            decay_rates: 每个时间点的累积衰减率，例如[0.5, 0.25]表示第一步衰减到原值的50%，第二步衰减到原值的25%
        """
        if len(steps) != len(decay_rates):
            raise ValueError("steps和decay_rates长度必须相同")
        
        self.steps = steps
        self.decay_rates = decay_rates
    
    def compute(self, value: float, elapsed_time: float) -> float:
        """计算阶梯衰减
        
        Args:
            value: 原始值
            elapsed_time: 经过的时间（秒）
            
        Returns:
            float: 衰减后的值
        """
        for i, step in enumerate(self.steps):
            if elapsed_time < step:
                if i == 0:
                    return value  # 还未到第一个衰减点
                else:
                    return value * self.decay_rates[i-1]
        
        # 超过所有时间点，使用最后一个衰减率
        if self.steps:
            return value * self.decay_rates[-1]
        return value


class CustomDecay(DecayFunction):
    """自定义衰减函数"""
    
    def __init__(self, decay_function: Callable[[float, float], float]):
        """初始化自定义衰减函数
        
        Args:
            decay_function: 自定义衰减计算函数，接受原始值和经过时间，返回衰减后的值
        """
        self.decay_function = decay_function
    
    def compute(self, value: float, elapsed_time: float) -> float:
        """计算自定义衰减
        
        Args:
            value: 原始值
            elapsed_time: 经过的时间（秒）
            
        Returns:
            float: 衰减后的值
        """
        return self.decay_function(value, elapsed_time)


def create_decay_function(decay_type: str, **params) -> DecayFunction:
    """创建衰减函数
    
    Args:
        decay_type: 衰减类型，可选值: 'exponential', 'linear', 'step', 'custom'
        **params: 各衰减函数特定的参数
        
    Returns:
        DecayFunction: 衰减函数对象
        
    Raises:
        ValueError: 不支持的衰减类型
    """
    if decay_type == 'exponential':
        decay_factor = params.get('decay_factor', 0.1)
        return ExponentialDecay(decay_factor)
    elif decay_type == 'linear':
        decay_factor = params.get('decay_factor', 0.1)
        return LinearDecay(decay_factor)
    elif decay_type == 'step':
        steps = params.get('steps', [])
        decay_rates = params.get('decay_rates', [])
        return StepDecay(steps, decay_rates)
    elif decay_type == 'custom':
        decay_function = params.get('decay_function')
        if not decay_function:
            raise ValueError("必须提供decay_function参数")
        return CustomDecay(decay_function)
    else:
        raise ValueError(f"不支持的衰减类型: {decay_type}") 