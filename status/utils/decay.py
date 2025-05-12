"""
---------------------------------------------------------------
File name:                  decay.py
Author:                     Ignorant-lu
Date created:               2025/05/18
Description:                衰减函数工具，提供各种衰减计算方法
----------------------------------------------------------------

Changed history:            
                            2025/05/18: 初始创建;
----
"""

import math
from typing import Callable, Optional, Tuple, List, Union


def exponential_decay(value: float, decay_rate: float, dt: float) -> float:
    """指数衰减函数
    
    计算公式: value * e^(-decay_rate * dt)
    
    Args:
        value: 初始值
        decay_rate: 衰减率，值越大衰减越快
        dt: 时间增量（秒）
        
    Returns:
        float: 衰减后的值
    """
    return value * math.exp(-decay_rate * dt)


def linear_decay(value: float, decay_rate: float, dt: float, min_value: float = 0.0) -> float:
    """线性衰减函数
    
    计算公式: max(value - decay_rate * dt, min_value)
    
    Args:
        value: 初始值
        decay_rate: 衰减率，每秒减少的值
        dt: 时间增量（秒）
        min_value: 最小值
        
    Returns:
        float: 衰减后的值
    """
    return max(value - decay_rate * dt, min_value)


def quadratic_decay(value: float, decay_rate: float, dt: float, min_value: float = 0.0) -> float:
    """二次衰减函数
    
    计算公式: max(value - decay_rate * dt^2, min_value)
    
    Args:
        value: 初始值
        decay_rate: 衰减率
        dt: 时间增量（秒）
        min_value: 最小值
        
    Returns:
        float: 衰减后的值
    """
    return max(value - decay_rate * (dt * dt), min_value)


def logarithmic_decay(value: float, decay_rate: float, dt: float, 
                     min_value: float = 0.0, base: float = math.e) -> float:
    """对数衰减函数
    
    计算公式: max(value - decay_rate * log(dt + 1, base), min_value)
    
    Args:
        value: 初始值
        decay_rate: 衰减率
        dt: 时间增量（秒）
        min_value: 最小值
        base: 对数的底数
        
    Returns:
        float: 衰减后的值
    """
    if dt <= 0:
        return value
    return max(value - decay_rate * math.log(dt + 1, base), min_value)


def cosine_decay(value: float, decay_rate: float, dt: float, 
                period: float = 1.0, min_value: float = 0.0) -> float:
    """余弦衰减函数
    
    计算公式: max(value * (1 + cos(π * dt / period)) / 2 * e^(-decay_rate * dt), min_value)
    
    Args:
        value: 初始值
        decay_rate: 衰减率
        dt: 时间增量（秒）
        period: 振荡周期
        min_value: 最小值
        
    Returns:
        float: 衰减后的值
    """
    if dt <= 0:
        return value
    cosine_factor = (1 + math.cos(math.pi * dt / period)) / 2
    exp_factor = math.exp(-decay_rate * dt)
    return max(value * cosine_factor * exp_factor, min_value)


def stepped_decay(value: float, decay_steps: List[Tuple[float, float]], 
                 dt: float, min_value: float = 0.0) -> float:
    """阶梯式衰减函数
    
    Args:
        value: 初始值
        decay_steps: 衰减步骤列表，每个元素为(时间阈值, 衰减百分比)
        dt: 时间增量（秒）
        min_value: 最小值
        
    Returns:
        float: 衰减后的值
    """
    if dt <= 0 or not decay_steps:
        return value
        
    # 按时间阈值排序
    sorted_steps = sorted(decay_steps, key=lambda x: x[0])
    
    result = value
    for time_threshold, decay_percent in sorted_steps:
        if dt >= time_threshold:
            result *= (1.0 - decay_percent)
    
    return max(result, min_value)


def create_custom_decay(decay_function: Callable[[float, float, float], float]) -> Callable[[float, float, float], float]:
    """创建自定义衰减函数
    
    Args:
        decay_function: 衰减函数，接受(value, decay_rate, dt)参数
        
    Returns:
        Callable: 自定义衰减函数
    """
    def custom_decay(value: float, decay_rate: float, dt: float) -> float:
        return decay_function(value, decay_rate, dt)
    
    return custom_decay 