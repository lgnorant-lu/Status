"""
配置管理模块
"""

from status.core.config.config_manager import ConfigManager
from status.core.config.config_types import ConfigEventType, DEFAULT_CONFIG, DEFAULT_CONFIG_FILE

# 创建全局配置管理器实例
config_manager = ConfigManager.get_instance()

__all__ = [
    'ConfigManager',
    'ConfigEventType',
    'DEFAULT_CONFIG',
    'DEFAULT_CONFIG_FILE',
    'config_manager'
]
