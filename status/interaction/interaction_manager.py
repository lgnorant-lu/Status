"""
---------------------------------------------------------------
File name:                  interaction_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                交互管理器模块，负责协调各种交互功能
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
                            2025/04/05: 添加命令系统的初始化;
----
"""

import logging
from typing import Dict, List, Optional, Set, Type

from status.core.events import EventManager
from .event_filter import EventFilter, EventFilterChain
from .event_throttler import EventThrottler, EventThrottlerChain
from status.interaction.mouse_interaction import MouseInteraction
from status.interaction.trayicon import TrayIcon
from status.interaction.context_menu import ContextMenu
from status.interaction.hotkey_manager import HotkeyManager
from status.interaction.drag_manager import DragManager
from status.interaction.behavior_trigger import BehaviorTrigger
from status.interaction.interaction_event import InteractionEvent, InteractionEventType
from status.interaction.base_interaction_handler import BaseInteractionHandler

# 配置日志
logger = logging.getLogger(__name__)

class InteractionManager:
    """交互管理器，协调各种交互功能"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = InteractionManager()
        return cls._instance
    
    def __init__(self, app_context, settings):
        """初始化交互管理器"""
        if InteractionManager._instance is not None:
            raise RuntimeError("InteractionManager是单例，请使用get_instance()获取实例")
        
        self.logger = logging.getLogger(__name__)
        self.app_context = app_context
        self.settings = settings
        self.event_bus = app_context.event_bus
        self.interaction_handlers: List[BaseInteractionHandler] = []
        self.mouse_event_handler = None
        self.keyboard_event_handler = None
        
        # 初始化标记
        self._initialized = False
        
        logger.debug("交互管理器已创建")
    
    def initialize(self) -> bool:
        """
        初始化交互管理器及其管理的子系统
        
        Returns:
            初始化是否成功
        """
        if self._initialized:
            logger.warning("交互管理器已经初始化")
            return True
        
        try:
            # Initialize CommandManager if enabled
            # if self.settings.get('enable_command_processing', False):
            #     try:
            #         self.command_manager = CommandManager(self.app_context)
            #         self.command_manager.initialize()
            #         self.logger.info("CommandManager initialized.")
            #     except Exception as e:
            #         self.logger.error(f"Failed to initialize CommandManager: {e}", exc_info=True)
            # else:
            #     self.logger.info("Command processing is disabled.")

            # Initialize other interaction handlers
            self.mouse_event_handler = MouseInteraction()
            self.mouse_event_handler.initialize()
            
            self.keyboard_event_handler = HotkeyManager()
            self.keyboard_event_handler.initialize()
            
            # 注册事件监听
            self.event_bus.add_listener(
                InteractionEventType.ANY,
                self._handle_interaction_event
            )
            
            self._initialized = True
            logger.info("交互管理器初始化成功")
            return True
        
        except Exception as e:
            logger.error(f"交互管理器初始化失败: {str(e)}")
            return False
    
    def _handle_interaction_event(self, event_type, event_data=None):
        """
        处理交互事件
        
        Args:
            event_type: 事件类型
            event_data: 事件数据
        """
        subsystems = [
            self.mouse_event_handler,
            self.keyboard_event_handler,
            # self.command_manager
        ]
        
        for subsystem in subsystems:
            if subsystem and hasattr(subsystem, 'handle_event'):
                subsystem.handle_event(event_type, event_data)
    
    def shutdown(self):
        """关闭交互管理器及其管理的子系统"""
        logger.info("正在关闭交互管理器")
        
        # 关闭事件监听
        self.event_bus.remove_listener(
            InteractionEventType.ANY,
            self._handle_interaction_event
        )
        
        # 关闭各个子系统
        if self.mouse_event_handler:
            self.mouse_event_handler.shutdown()
        
        if self.keyboard_event_handler:
            self.keyboard_event_handler.shutdown()
        
        # if self.command_manager:
        #     try:
        #         self.command_manager.shutdown()
        #         self.logger.info("CommandManager shut down.")
        #     except Exception as e:
        #         self.logger.error(f"Error shutting down CommandManager: {e}", exc_info=True)
        
        self._initialized = False
        logger.info("交互管理器已关闭")
    
    def add_filter(self, filter_id: str, event_filter: EventFilter) -> bool:
        """添加事件过滤器
        
        Args:
            filter_id: 过滤器的唯一标识符
            event_filter: 要添加的过滤器实例
            
        Returns:
            bool: 添加是否成功
        """
        if filter_id in self.filters_by_id:
            logger.warning(f"Filter with ID '{filter_id}' already exists")
            return False
        
        self.filter_chain.add_filter(event_filter)
        self.filters_by_id[filter_id] = event_filter
        logger.info(f"Added filter '{filter_id}' to interaction manager")
        return True
    
    def remove_filter(self, filter_id: str) -> bool:
        """移除事件过滤器
        
        Args:
            filter_id: 要移除的过滤器ID
            
        Returns:
            bool: 移除是否成功
        """
        if filter_id not in self.filters_by_id:
            logger.warning(f"Filter with ID '{filter_id}' not found")
            return False
        
        event_filter = self.filters_by_id[filter_id]
        success = self.filter_chain.remove_filter(event_filter)
        if success:
            del self.filters_by_id[filter_id]
            logger.info(f"Removed filter '{filter_id}' from interaction manager")
        return success
    
    def add_throttler(self, throttler_id: str, event_throttler: EventThrottler) -> bool:
        """添加事件节流器
        
        Args:
            throttler_id: 节流器的唯一标识符
            event_throttler: 要添加的节流器实例
            
        Returns:
            bool: 添加是否成功
        """
        if throttler_id in self.throttlers_by_id:
            logger.warning(f"Throttler with ID '{throttler_id}' already exists")
            return False
        
        self.throttler_chain.add_throttler(event_throttler)
        self.throttlers_by_id[throttler_id] = event_throttler
        logger.info(f"Added throttler '{throttler_id}' to interaction manager")
        return True
    
    def remove_throttler(self, throttler_id: str) -> bool:
        """移除事件节流器
        
        Args:
            throttler_id: 要移除的节流器ID
            
        Returns:
            bool: 移除是否成功
        """
        if throttler_id not in self.throttlers_by_id:
            logger.warning(f"Throttler with ID '{throttler_id}' not found")
            return False
        
        event_throttler = self.throttlers_by_id[throttler_id]
        success = self.throttler_chain.remove_throttler(event_throttler)
        if success:
            del self.throttlers_by_id[throttler_id]
            logger.info(f"Removed throttler '{throttler_id}' from interaction manager")
        return success
    
    def clear_filters(self) -> None:
        """清除所有事件过滤器"""
        self.filter_chain.clear_filters()
        self.filters_by_id.clear()
        logger.info("Cleared all filters from interaction manager")
    
    def clear_throttlers(self) -> None:
        """清除所有事件节流器"""
        self.throttler_chain.clear_throttlers()
        self.throttlers_by_id.clear()
        logger.info("Cleared all throttlers from interaction manager")
    
    def get_event_stats(self) -> Dict:
        """获取事件处理统计信息
        
        Returns:
            Dict: 事件统计信息
        """
        return self.event_stats.copy()
    
    def reset_event_stats(self) -> None:
        """重置事件统计信息"""
        for key in self.event_stats:
            self.event_stats[key] = 0
        logger.info("Reset event statistics")
    
    def _setup_connections(self):
        """设置交互子系统之间的连接
        
        连接各个交互子系统，使它们能够相互协作。
        """
        # 将右键点击连接到上下文菜单
        self.mouse_event_handler.right_click_signal.connect(self.context_menu.show_menu)
        
        # 连接拖拽管理器和鼠标交互
        self.mouse_event_handler.register_drag_manager(self.drag_manager)
        
        # 注册各子系统的事件处理器
        self.event_bus.register_handler("interaction", self._handle_interaction_event)
        
        logger.debug("InteractionManager connections set up")
    
    def _setup_default_filters_and_throttlers(self):
        """设置默认的事件过滤器和节流器
        
        初始化一些常用的事件过滤和节流配置
        """
        # 这里可以添加一些默认配置
        # 例如为鼠标移动事件添加节流器等
        logger.debug("Default filters and throttlers set up")
    
    def _show_launcher(self):
        """显示快捷启动器"""
        if not self.launcher_manager:
            logger.warning("启动器管理器未初始化")
            return
        
        try:
            # 导入UI组件
            from status.launcher import LauncherUI
            
            # 创建并显示启动器UI
            launcher_ui = LauncherUI()
            launcher_ui.exec()
            
            logger.info("显示快捷启动器")
        except Exception as e:
            logger.error(f"显示快捷启动器失败: {str(e)}")
    
    def shutdown(self):
        """关闭交互管理器
        
        清理资源并关闭所有交互子系统。
        """
        if not self._initialized:
            logger.warning("InteractionManager not initialized")
            return
        
        logger.info("Shutting down InteractionManager")
        
        # 关闭各交互子系统
        subsystems = [
            self.mouse_event_handler,
            self.keyboard_event_handler,
            # self.command_manager
        ]
        
        for subsystem in subsystems:
            if subsystem and hasattr(subsystem, 'shutdown'):
                try:
                    subsystem.shutdown()
                except Exception as e:
                    logger.error(f"Error shutting down subsystem: {str(e)}")
        
        # 清空过滤器和节流器
        self.clear_filters()
        self.clear_throttlers()
        
        # 重置统计信息
        self.reset_event_stats()
        
        # 重置初始化标志
        self._initialized = False
        
        logger.info("InteractionManager shut down") 