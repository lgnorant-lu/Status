"""
---------------------------------------------------------------
File name:                  __init__.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                配置管理模块的入口
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
                            2025/04/04: 添加ConfigEnvironment枚举导出接口;
                            2025/04/04: 添加版本控制相关接口;
----
"""

from .config_manager import ConfigurationManager, ConfigChangeType, ConfigEnvironment, config_manager
from .utils import ConfigDiff
from .validators import ConfigValidator, ConfigValidationError

__all__ = [
    'ConfigurationManager',
    'ConfigChangeType',
    'ConfigEnvironment',
    'ConfigDiff',
    'ConfigValidator',
    'ConfigValidationError',
    'get_config_instance',
    'config_manager'
]

# 获取全局配置管理器实例
def get_config_instance() -> ConfigurationManager:
    """获取配置管理器的单例实例
    
    Returns:
        ConfigurationManager: 配置管理器实例
    """
    return ConfigurationManager()
