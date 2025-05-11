"""
---------------------------------------------------------------
File name:                  __init__.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                快捷启动器模块初始化文件
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

# 导出类型定义
from status.launcher.launcher_types import (
    LaunchedApplication,
    LauncherGroup,
    LaunchResult,
    LaunchStatus
)

# 导出管理器
from status.launcher.launcher_manager import LauncherManager

# 导出UI组件
from status.launcher.launcher_ui import LauncherUI

# 导出所有公共组件
__all__ = [
    # 类型
    'LaunchedApplication',
    'LauncherGroup',
    'LaunchResult',
    'LaunchStatus',
    
    # 管理器
    'LauncherManager',
    
    # UI组件
    'LauncherUI'
] 