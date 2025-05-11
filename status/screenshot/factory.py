"""
---------------------------------------------------------------
File name:                  factory.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                截图系统工厂，创建和配置截图系统
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

import logging
import os
from typing import Dict, Any, Optional

from status.screenshot.screenshot_service import ScreenshotService
from status.screenshot.screenshot_manager import ScreenshotManager

# 配置日志记录器
logger = logging.getLogger(__name__)

def create_screenshot_system(config: Dict[str, Any] = None) -> ScreenshotManager:
    """创建截图系统
    
    根据配置创建默认的截图系统，包括截图服务和管理器。
    
    Args:
        config: 配置参数，包含服务和管理器的配置
        
    Returns:
        ScreenshotManager: 创建的截图管理器
    """
    # 使用默认配置
    default_config = _get_default_config()
    
    # 合并用户配置
    if config:
        _merge_config(default_config, config)
    
    # 创建截图管理器
    manager = ScreenshotManager(default_config)
    
    logger.info("默认截图系统已创建")
    return manager

def create_custom_screenshot_system(
    service_config: Dict[str, Any] = None,
    auto_copy: bool = True,
    show_notification: bool = True,
    max_recent_count: int = 10
) -> ScreenshotManager:
    """创建自定义截图系统
    
    使用自定义配置创建截图系统。
    
    Args:
        service_config: 截图服务的配置
        auto_copy: 是否自动复制到剪贴板
        show_notification: 是否显示通知
        max_recent_count: 最近截图记录的最大数量
        
    Returns:
        ScreenshotManager: 创建的截图管理器
    """
    # 创建配置
    config = {
        'service': service_config or {},
        'auto_copy': auto_copy,
        'show_notification': show_notification,
        'max_recent_count': max_recent_count,
        'full_screenshot_hotkey': 'F12',
        'region_screenshot_hotkey': 'Ctrl+Shift+F12',
        'window_screenshot_hotkey': 'Alt+F12'
    }
    
    # 创建截图管理器
    manager = ScreenshotManager(config)
    
    logger.info("自定义截图系统已创建")
    return manager

def _get_default_config() -> Dict[str, Any]:
    """获取默认配置
    
    Returns:
        Dict[str, Any]: 默认配置
    """
    # 默认保存路径
    default_save_dir = os.path.join(os.path.expanduser('~'), 'Pictures', 'Screenshots')
    
    # 创建配置
    config = {
        'service': {
            'save_dir': default_save_dir,
            'format': 'png',
            'include_cursor': False,
            'filename_pattern': 'screenshot_%Y%m%d_%H%M%S'
        },
        'auto_copy': True,
        'show_notification': True,
        'max_recent_count': 10,
        'full_screenshot_hotkey': 'F12',
        'region_screenshot_hotkey': 'Ctrl+Shift+F12',
        'window_screenshot_hotkey': 'Alt+F12'
    }
    
    return config

def _merge_config(base_config: Dict[str, Any], user_config: Dict[str, Any]) -> None:
    """合并配置
    
    将用户配置合并到基础配置中。
    
    Args:
        base_config: 基础配置
        user_config: 用户配置
    """
    for key, value in user_config.items():
        if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
            # 递归合并嵌套字典
            _merge_config(base_config[key], value)
        else:
            # 直接覆盖非字典值
            base_config[key] = value 