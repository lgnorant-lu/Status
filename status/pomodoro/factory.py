"""
---------------------------------------------------------------
File name:                  factory.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                番茄钟系统工厂，提供创建番茄钟系统的便捷方法
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

import logging
from typing import Dict, Any, Optional, Union

from status.pomodoro.pomodoro_timer import PomodoroTimer, PomodoroConfig
from status.pomodoro.pomodoro_manager import PomodoroManager

# 配置日志记录器
logger = logging.getLogger(__name__)

def create_pomodoro_system(config: Optional[Dict[str, Any]] = None) -> PomodoroManager:
    """创建默认的番茄钟系统
    
    使用默认配置创建番茄钟系统，包括计时器和管理器。
    
    Args:
        config: 可选的配置参数，用于覆盖默认配置
        
    Returns:
        PomodoroManager: 番茄钟管理器实例
    """
    # 获取默认配置
    default_config = _get_default_config()
    
    # 合并用户配置
    if config:
        merged_config = _merge_config(default_config, config)
    else:
        merged_config = default_config
    
    # 创建番茄钟管理器
    manager = PomodoroManager(merged_config)
    
    logger.info("已创建默认番茄钟系统")
    return manager

def create_custom_pomodoro_system(
    focus_duration: int = 25 * 60,
    short_break_duration: int = 5 * 60,
    long_break_duration: int = 15 * 60,
    cycles_before_long_break: int = 4,
    auto_start_breaks: bool = True,
    auto_start_focus: bool = False,
    sound_notification: bool = True,
    data_dir: str = "data",
    auto_save_interval: int = 300
) -> PomodoroManager:
    """创建自定义番茄钟系统
    
    根据提供的参数创建自定义番茄钟系统。
    
    Args:
        focus_duration: 专注时长，单位秒，默认25分钟
        short_break_duration: 短休息时长，单位秒，默认5分钟
        long_break_duration: 长休息时长，单位秒，默认15分钟
        cycles_before_long_break: 长休息前的专注循环次数，默认4次
        auto_start_breaks: 是否自动开始休息，默认True
        auto_start_focus: 是否自动开始专注，默认False
        sound_notification: 是否启用声音通知，默认True
        data_dir: 数据存储目录，默认为"data"
        auto_save_interval: 自动保存间隔，单位秒，默认300秒
        
    Returns:
        PomodoroManager: 番茄钟管理器实例
    """
    # 创建配置
    config = {
        "timer": {
            "focus_duration": focus_duration,
            "short_break_duration": short_break_duration,
            "long_break_duration": long_break_duration,
            "cycles_before_long_break": cycles_before_long_break,
            "auto_start_breaks": auto_start_breaks,
            "auto_start_focus": auto_start_focus,
        },
        "sound_notification": sound_notification,
        "data_dir": data_dir,
        "auto_save_interval": auto_save_interval
    }
    
    # 创建番茄钟管理器
    manager = PomodoroManager(config)
    
    logger.info("已创建自定义番茄钟系统")
    return manager

def _get_default_config() -> Dict[str, Any]:
    """获取默认配置
    
    Returns:
        Dict[str, Any]: 默认配置字典
    """
    return {
        "timer": {
            "focus_duration": 25 * 60,         # 专注时长 25分钟
            "short_break_duration": 5 * 60,    # 短休息 5分钟
            "long_break_duration": 15 * 60,    # 长休息 15分钟
            "cycles_before_long_break": 4,     # 长休息前的专注循环次数
            "auto_start_breaks": True,         # 自动开始休息
            "auto_start_focus": False,         # 不自动开始专注
            "tick_interval": 1,                # 计时器刻度间隔（秒）
        },
        "sound_notification": True,            # 启用声音通知
        "data_dir": "data",                    # 数据存储目录
        "auto_save_interval": 300,             # 自动保存间隔（秒）
        "current_task": ""                     # 当前任务
    }

def _merge_config(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """合并配置
    
    递归合并配置字典，override_config中的值会覆盖base_config中的值。
    
    Args:
        base_config: 基础配置
        override_config: 覆盖配置
        
    Returns:
        Dict[str, Any]: 合并后的配置
    """
    result = base_config.copy()
    
    for key, value in override_config.items():
        # 如果是字典，则递归合并
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_config(result[key], value)
        else:
            # 否则直接覆盖
            result[key] = value
    
    return result 