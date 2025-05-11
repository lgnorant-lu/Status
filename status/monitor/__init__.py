"""
---------------------------------------------------------------
File name:                  __init__.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                系统监控模块
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

# 导入主要组件
from .data_collector import SystemDataCollector
from .data_processor import DataProcessor
from .visualization import VisualMapper
from .scene_manager import SceneManager
from .monitor_manager import MonitorManager

# 导入工厂函数
from .factory import (
    create_monitor_system,
    create_custom_monitor_system,
    create_minimal_monitor_system,
    create_debug_monitor_system,
)

# 定义模块导出的内容
__all__ = [
    # 核心类
    'SystemDataCollector',
    'DataProcessor',
    'VisualMapper',
    'SceneManager',
    'MonitorManager',
    
    # 工厂函数
    'create_monitor_system',
    'create_custom_monitor_system',
    'create_minimal_monitor_system', 
    'create_debug_monitor_system',
] 