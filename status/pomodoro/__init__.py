"""
---------------------------------------------------------------
File name:                  __init__.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                番茄钟模块，提供专注/休息时间管理功能
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

# 从模块中导入类和函数
from status.pomodoro.pomodoro_timer import PomodoroTimer, PomodoroState, PomodoroConfig
from status.pomodoro.pomodoro_manager import PomodoroManager, PomodoroEventType
from status.pomodoro.factory import create_pomodoro_system, create_custom_pomodoro_system

# 定义公开的API
__all__ = [
    'PomodoroTimer',
    'PomodoroState',
    'PomodoroConfig',
    'PomodoroManager',
    'PomodoroEventType',
    'create_pomodoro_system',
    'create_custom_pomodoro_system'
] 