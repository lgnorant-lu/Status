"""
---------------------------------------------------------------
File name:                  __init__.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                错误恢复系统模块初始化
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

from status.core.recovery.state_manager import StateManager, StateData
from status.core.recovery.recovery_manager import RecoveryManager, RecoveryMode
from status.core.recovery.exception_handler import ExceptionHandler, ErrorLevel

# 创建单例实例供全局使用
state_manager = StateManager()
recovery_manager = RecoveryManager()
exception_handler = ExceptionHandler()

__all__ = [
    'StateManager', 'StateData', 
    'RecoveryManager', 'RecoveryMode',
    'ExceptionHandler', 'ErrorLevel',
    'state_manager', 'recovery_manager', 'exception_handler'
] 