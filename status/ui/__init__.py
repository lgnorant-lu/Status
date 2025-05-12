"""
---------------------------------------------------------------
File name:                  __init__.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                UI模块初始化
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
                            2025/04/05: 添加主题系统导出;
----
"""

# 从监控UI导出
# from .monitor_ui import MonitorUIWindow
# from .monitor_app import run_app

# 从UI组件导出
from status.ui.components import (
    # 按钮组件
    PrimaryButton,
    SecondaryButton,
    IconButton,
    TextButton,
    
    # 输入组件
    TextField,
    SearchField,
    PasswordField, 
    TextArea,
    FormField,
    
    # 卡片组件
    Card,
    CardHeader,
    CardContent,
    CardFooter,
    
    # 进度指示器
    ProgressBar,
    CircularProgress,
    ProgressIndicator,
    ProgressType,
    
    # 通知组件
    Notification,
    NotificationType,
    NotificationManager,
    
    # 主题系统
    Theme,
    ThemeType,
    ColorRole,
    ThemeManager,
    apply_stylesheet,
    apply_theme_to_widget
)

# 导出所有接口
__all__ = [
    # 监控UI
    # 'MonitorUIWindow',
    # 'run_app',
    
    # 按钮组件
    'PrimaryButton',
    'SecondaryButton',
    'IconButton',
    'TextButton',
    
    # 输入组件
    'TextField',
    'SearchField',
    'PasswordField', 
    'TextArea',
    'FormField',
    
    # 卡片组件
    'Card',
    'CardHeader',
    'CardContent',
    'CardFooter',
    
    # 进度指示器
    'ProgressBar',
    'CircularProgress',
    'ProgressIndicator',
    'ProgressType',
    
    # 通知组件
    'Notification',
    'NotificationType',
    'NotificationManager',
    
    # 主题系统
    'Theme',
    'ThemeType',
    'ColorRole',
    'ThemeManager',
    'apply_stylesheet',
    'apply_theme_to_widget'
]
