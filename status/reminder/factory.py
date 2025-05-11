"""
---------------------------------------------------------------
File name:                  factory.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                提醒系统工厂，提供创建提醒系统的便捷方法
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""
import logging
from typing import Dict, Any, Optional

from .reminder_manager import ReminderManager
from .reminder_store import ReminderStore
from .scheduler import ReminderScheduler
from .notification import NotificationRenderer

logger = logging.getLogger("ReminderFactory")

def create_reminder_system(config: Dict[str, Any] = None) -> ReminderManager:
    """
    创建标准提醒系统
    
    Args:
        config: 配置信息
        
    Returns:
        ReminderManager: 提醒管理器实例
    """
    config = config or {}
    logger.info("创建标准提醒系统")
    
    # 创建存储器
    logger.info("创建提醒存储器")
    store = ReminderStore(config.get('store_config', {}))
    
    # 创建调度器
    logger.info("创建提醒调度器")
    scheduler = ReminderScheduler(config.get('scheduler_config', {}))
    
    # 创建通知渲染器
    logger.info("创建通知渲染器")
    notification_renderer = NotificationRenderer(config.get('notification_config', {}))
    
    # 创建管理器
    logger.info("创建提醒管理器")
    manager = ReminderManager(
        config, 
        store, 
        scheduler, 
        notification_renderer
    )
    
    # 自动启动
    if config.get('auto_start', True):
        logger.info("自动启动提醒系统")
        manager.start()
    
    logger.info("提醒系统创建完成")
    return manager

def create_minimal_reminder_system() -> ReminderManager:
    """
    创建最小化提醒系统
    
    Returns:
        ReminderManager: 提醒管理器实例
    """
    logger.info("创建最小化提醒系统")
    config = {
        'store_config': {
            'storage_path': 'data/minimal_reminders.json'
        },
        'scheduler_config': {
            'scan_interval': 30  # 降低扫描频率
        },
        'notification_config': {
            'max_notifications': 3
        },
        'auto_start': False
    }
    
    return create_reminder_system(config)

def create_debug_reminder_system() -> ReminderManager:
    """
    创建调试提醒系统
    
    Returns:
        ReminderManager: 提醒管理器实例
    """
    logger.debug("创建调试提醒系统")
    config = {
        'store_config': {
            'storage_path': 'data/debug_reminders.json'
        },
        'scheduler_config': {
            'scan_interval': 5  # 提高扫描频率
        },
        'notification_config': {
            'max_notifications': 10
        },
        'auto_start': True
    }
    
    manager = create_reminder_system(config)
    logger.debug("调试提醒系统创建完成")
    return manager

def create_custom_reminder_system(
    store: Optional[ReminderStore] = None,
    scheduler: Optional[ReminderScheduler] = None,
    notification_renderer: Optional[NotificationRenderer] = None,
    config: Dict[str, Any] = None
) -> ReminderManager:
    """
    创建自定义提醒系统
    
    Args:
        store: 自定义存储器
        scheduler: 自定义调度器
        notification_renderer: 自定义通知渲染器
        config: 配置信息
        
    Returns:
        ReminderManager: 提醒管理器实例
    """
    logger.info("创建自定义提醒系统")
    config = config or {}
    
    # 创建管理器
    manager = ReminderManager(
        config, 
        store, 
        scheduler, 
        notification_renderer
    )
    
    # 自动启动
    if config.get('auto_start', False):
        logger.info("自动启动自定义提醒系统")
        manager.start()
    
    logger.info("自定义提醒系统创建完成")
    return manager 