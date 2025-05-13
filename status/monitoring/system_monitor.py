"""
---------------------------------------------------------------
File name:                  system_monitor.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                提供获取系统监控信息的功能
----------------------------------------------------------------
"""

import psutil
import logging

logger = logging.getLogger(__name__)

def get_cpu_usage() -> float:
    """获取当前的CPU平均使用率

    Returns:
        float: CPU使用率 (0.0 到 100.0)
    """
    try:
        # interval=None 获取自上次调用或模块初始化以来的平均CPU使用率
        # 这通常比 interval=0.1 或更高更适合快速、低开销的读取
        usage = psutil.cpu_percent(interval=None)
        logger.debug(f"psutil.cpu_percent returned: {usage}")
        return usage if usage is not None else 0.0
    except Exception as e:
        logger.error(f"获取CPU使用率时发生错误: {e}")
        return 0.0 # 发生错误时返回0.0，确保函数总有float返回 

def get_memory_usage() -> float:
    """获取当前内存使用率百分比"""
    try:
        memory_info = psutil.virtual_memory()
        logger.debug(f"内存信息: {memory_info}") # 记录原始信息以供调试
        return memory_info.percent
    except Exception as e:
        logger.error(f"获取内存使用率时出错: {e}")
        return 0.0 # 发生错误时返回 0

# 可以在这里添加其他系统监控函数
# 例如：获取磁盘使用率、网络速度等 