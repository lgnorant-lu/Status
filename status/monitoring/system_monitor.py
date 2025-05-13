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