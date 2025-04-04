"""
---------------------------------------------------------------
File name:                  interaction_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                桌宠交互管理器，协调各类交互
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
                            2025/04/04: 添加事件过滤和节流功能;
----
"""

import logging
from typing import Dict, List, Optional, Set, Type

from status.core.events import EventManager
from .event_filter import EventFilter, EventFilterChain
from .event_throttler import EventThrottler, EventThrottlerChain

# 配置日志
logger = logging.getLogger(__name__)

class InteractionManager:
    """交互管理器
    
    管理所有桌宠交互子系统，协调它们之间的交互。
    提供了一个单例实例，确保全局只有一个交互管理器。
    """
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """获取交互管理器的单例实例
        
        如果实例不存在，则创建一个新实例。
        
        Returns:
            InteractionManager: 交互管理器的单例实例
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """初始化交互管理器
        
        初始化各个交互子系统的引用和事件管理器。
        注意：应该使用get_instance()获取实例，而不是直接创建。
        """
        if InteractionManager._instance is not None:
            raise RuntimeError("InteractionManager is a singleton, use get_instance() instead")
        
        # 设置交互子系统引用
        self.mouse_interaction = None
        self.tray_icon = None
        self.context_menu = None
        self.hotkey_manager = None
        self.behavior_trigger = None
        self.drag_manager = None
        
        # 获取事件管理器
        self.event_manager = EventManager.get_instance()
        
        # 初始化事件过滤和节流系统
        self.filter_chain = EventFilterChain("InteractionFilterChain")
        self.throttler_chain = EventThrottlerChain("InteractionThrottlerChain")
        
        # 维护过滤器和节流器的映射，便于管理
        self.filters_by_id = {}  # 通过ID查找过滤器
        self.throttlers_by_id = {}  # 通过ID查找节流器
        
        # 性能统计
        self.event_stats = {
            'total_events': 0,
            'filtered_events': 0,
            'throttled_events': 0,
            'processed_events': 0
        }
        
        # 初始化标志
        self.initialized = False
        
        logger.info("InteractionManager created")
    
    def initialize(self, app_instance, main_window):
        """初始化交互管理器和所有交互子系统
        
        Args:
            app_instance: 应用程序实例，通常是QApplication
            main_window: 主窗口实例，通常是桌宠的主窗口
            
        Returns:
            bool: 初始化是否成功
        """
        if self.initialized:
            logger.warning("InteractionManager already initialized")
            return False
        
        try:
            logger.info("Initializing InteractionManager")
            
            # 导入交互子系统
            # 延迟导入以避免循环依赖
            from status.interaction.mouse_interaction import MouseInteraction
            from status.interaction.tray_icon import TrayIcon
            from status.interaction.context_menu import ContextMenu
            from status.interaction.hotkey import HotkeyManager
            from status.interaction.behavior_trigger import BehaviorTrigger
            from status.interaction.drag_manager import DragManager
            
            # 初始化各交互子系统
            self.mouse_interaction = MouseInteraction(main_window)
            self.tray_icon = TrayIcon(app_instance)
            self.context_menu = ContextMenu()
            self.hotkey_manager = HotkeyManager()
            self.behavior_trigger = BehaviorTrigger()
            self.drag_manager = DragManager(main_window)
            
            # 设置必要的连接
            self._setup_connections()
            
            # 设置默认的过滤器和节流器
            self._setup_default_filters_and_throttlers()
            
            self.initialized = True
            logger.info("InteractionManager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize InteractionManager: {str(e)}")
            return False
    
    def _setup_connections(self):
        """设置交互子系统之间的连接
        
        连接各个交互子系统，使它们能够相互协作。
        """
        # 将右键点击连接到上下文菜单
        self.mouse_interaction.right_click_signal.connect(self.context_menu.show_menu)
        
        # 连接拖拽管理器和鼠标交互
        self.mouse_interaction.register_drag_manager(self.drag_manager)
        
        # 注册各子系统的事件处理器
        self.event_manager.register_handler("interaction", self._handle_interaction_event)
        
        logger.debug("InteractionManager connections set up")
    
    def _setup_default_filters_and_throttlers(self):
        """设置默认的事件过滤器和节流器
        
        初始化一些常用的事件过滤和节流配置
        """
        # 这里可以添加一些默认配置
        # 例如为鼠标移动事件添加节流器等
        logger.debug("Default filters and throttlers set up")
    
    def _handle_interaction_event(self, event):
        """处理交互事件
        
        处理从各个交互子系统发出的事件。
        应用过滤和节流逻辑，决定是否继续处理。
        
        Args:
            event: 要处理的交互事件
        """
        # 更新统计信息
        self.event_stats['total_events'] += 1
        
        # 应用过滤器
        if not self.filter_chain.should_process(event):
            self.event_stats['filtered_events'] += 1
            logger.debug(f"Event filtered: {event.event_type}")
            return
        
        # 应用节流器
        if not self.throttler_chain.throttle(event):
            self.event_stats['throttled_events'] += 1
            logger.debug(f"Event throttled: {event.event_type}")
            return
        
        # 更新处理统计
        self.event_stats['processed_events'] += 1
        
        logger.debug(f"Handling interaction event: {event.event_type}")
        
        # 通知所有的子系统关于这个事件
        # 使用策略模式，允许每个子系统决定是否处理该事件
        subsystems = [
            self.mouse_interaction,
            self.tray_icon,
            self.context_menu,
            self.hotkey_manager,
            self.behavior_trigger,
            self.drag_manager
        ]
        
        for subsystem in subsystems:
            if subsystem and hasattr(subsystem, 'handle_event'):
                subsystem.handle_event(event)
    
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
    
    def shutdown(self):
        """关闭交互管理器和所有交互子系统
        
        清理资源，关闭所有交互子系统。
        
        Returns:
            bool: 关闭是否成功
        """
        if not self.initialized:
            logger.warning("InteractionManager not initialized, nothing to shutdown")
            return False
        
        try:
            logger.info("Shutting down InteractionManager")
            
            # 关闭各交互子系统
            subsystems = [
                self.mouse_interaction,
                self.tray_icon,
                self.context_menu,
                self.hotkey_manager,
                self.behavior_trigger,
                self.drag_manager
            ]
            
            for subsystem in subsystems:
                if subsystem and hasattr(subsystem, 'shutdown'):
                    subsystem.shutdown()
            
            # 注销事件处理器
            self.event_manager.unregister_handler("interaction", self._handle_interaction_event)
            
            # 清空过滤器和节流器
            self.clear_filters()
            self.clear_throttlers()
            
            # 重置状态
            self.initialized = False
            
            logger.info("InteractionManager shutdown successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to shutdown InteractionManager: {str(e)}")
            return False 