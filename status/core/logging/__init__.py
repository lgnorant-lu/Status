"""
---------------------------------------------------------------
File name:                  __init__.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                日志系统模块初始化
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

from status.core.logging.log_manager import LogManager, get_logger

# 创建单例日志实例供全局使用
log = get_logger()

__all__ = ['LogManager', 'get_logger', 'log'] 