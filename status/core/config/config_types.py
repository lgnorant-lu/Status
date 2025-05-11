"""
---------------------------------------------------------------
File name:                  config_types.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                配置相关的数据类型和常量
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

import os
import enum


class ConfigEventType(enum.Enum):
    """配置事件类型"""
    CONFIG_CHANGED = "config_changed"      # 配置项被修改
    CONFIG_LOADED = "config_loaded"        # 配置被加载
    CONFIG_SAVED = "config_saved"          # 配置被保存


# 默认配置文件路径
DEFAULT_CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".status", "config.json")

# 默认配置
DEFAULT_CONFIG = {
    "launcher": {
        "favorite_group_id": None,
        "recent_applications": [],
        "max_recent_count": 10,
        "default_icon_path": None,
        "grid_columns": 5,
        "show_tooltips": True,
        "icon_size": 48
    },
    "appearance": {
        "theme": "system",
        "font_size": "medium",
        "use_system_theme": True,
        "dark_mode": False,
        "accent_color": "#1E90FF"
    },
    "general": {
        "language": "zh_CN",
        "auto_start": False,
        "minimize_to_tray": True,
        "check_updates": True,
        "update_interval_days": 7
    },
    "performance": {
        "enable_animations": True,
        "preload_apps": True,
        "cache_enabled": True,
        "cache_size_mb": 100
    }
} 