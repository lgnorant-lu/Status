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
from .mouse_interaction import MouseInteraction
from .tray_icon import TrayIcon
from .context_menu import ContextMenu
from .hotkey import HotkeyManager
from .drag_manager import DragManager
from .behavior_trigger import BehaviorTrigger
from .interaction_event import InteractionEvent, InteractionEventType
import collections

# 配置日志
logger = logging.getLogger(__name__)

class InteractionManager:
    """交互管理器，协调各种交互功能"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls, *args, **kwargs):
        """获取单例实例。如果实例不存在，则使用提供的参数创建它。"""
        if cls._instance is None:
            # 如果没有提供 app_context 和 settings，尝试从 kwargs 获取，或者记录错误
            # 这是为了确保 __init__ 有必要的参数
            if not args and not kwargs.get('app_context'):
                # 在实际应用中，这里可能需要更复杂的逻辑来获取默认的 app_context 和 settings
                # 或者强制调用者提供它们。
                # 为了测试，我们允许它在没有这些参数的情况下继续，但 __init__ 可能会失败或行为不当。
                logger.warning("InteractionManager creating new instance without explicit app_context/settings via get_instance.")
            cls._instance = cls(*args, **kwargs) # 调用 __init__
        return cls._instance
    
    def __init__(self, app_context, settings):
        """初始化交互管理器"""
        if InteractionManager._instance is not None and InteractionManager._instance is not self:
            raise RuntimeError("InteractionManager is a singleton. Use get_instance() after initial creation.")
        
        self.logger = logging.getLogger(__name__)
        self.app_context = app_context
        self.settings = settings
        self.event_bus = app_context.event_bus
        self.interaction_handlers: List[object] = []
        self.mouse_event_handler = None
        self.keyboard_event_handler = None
        
        # Initialize missing attributes
        self.filters_by_id: Dict[str, EventFilter] = {}
        self.filter_chain: EventFilterChain = EventFilterChain()
        self.throttlers_by_id: Dict[str, EventThrottler] = {}
        self.throttler_chain: EventThrottlerChain = EventThrottlerChain()
        self.event_stats: Dict[str, int] = collections.defaultdict(int)
        self.context_menu = None 
        self.drag_manager = None
        
        self._initialized = False
        InteractionManager._instance = self
        
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
            main_window = None
            if hasattr(self.app_context, 'get_main_window'):
                main_window = self.app_context.get_main_window()
            
            if main_window:
                self.mouse_event_handler = MouseInteraction(window=main_window)
            else:
                logger.warning("Main window not available for MouseInteraction, mouse events might not work.")
            
            self.keyboard_event_handler = HotkeyManager()
            if hasattr(self.keyboard_event_handler, 'start'):
                 self.keyboard_event_handler.start()
            else:
                 logger.warning("HotkeyManager does not have a start method.")
            
            # 注册事件监听
            # if hasattr(InteractionEventType, 'ANY'):
            #     self.event_bus.add_listener(
            #         InteractionEventType.ANY,
            #         self._handle_interaction_event
            #     )
            # else:
            #     logger.warning("InteractionEventType.ANY not found, listener for ANY not registered.")
            
            self._initialized = True
            logger.info("交互管理器初始化成功")
            return True
        
        except Exception as e:
            logger.error(f"交互管理器初始化失败: {str(e)}", exc_info=True)
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
        for key in list(self.event_stats.keys()):
            self.event_stats[key] = 0
        logger.info("Reset event statistics")
    
    def _setup_connections(self):
        """设置交互子系统之间的连接
        
        连接各个交互子系统，使它们能够相互协作。
        """
        if self.mouse_event_handler and self.context_menu and hasattr(self.mouse_event_handler, 'right_click_signal'):
            self.mouse_event_handler.right_click_signal.connect(self.context_menu.show_menu)
        
        if self.mouse_event_handler and self.drag_manager and hasattr(self.mouse_event_handler, 'register_drag_manager'):
            self.mouse_event_handler.register_drag_manager(self.drag_manager)
        
        self.event_bus.register_handler("interaction", self._handle_interaction_event)
        
        logger.debug("InteractionManager connections set up")
    
    def _setup_default_filters_and_throttlers(self):
        """设置默认的事件过滤器和节流器
        
        初始化一些常用的事件过滤和节流配置
        """
        logger.debug("Default filters and throttlers set up")
    
    def shutdown(self):
        """关闭交互管理器
        
        清理资源并关闭所有交互子系统。
        """
        if not self._initialized:
            logger.warning("InteractionManager not initialized or already shut down")
            return False #明确返回False如果未初始化
        
        logger.info("Shutting down InteractionManager")
        
        # 注销事件总线处理器，如果它曾被注册
        if hasattr(self.event_bus, 'unregister_handler'):
             try:
                 self.event_bus.unregister_handler("interaction", self._handle_interaction_event)
                 logger.debug("Unregistered interaction event handler from event bus.")
             except Exception as e:
                 logger.error(f"Error unregistering event handler from event bus: {e}", exc_info=True)
        
        # 关闭各个子系统
        subsystems_to_shutdown = [
            self.mouse_event_handler,
            self.keyboard_event_handler,
            self.context_menu, # If created and assigned to self.context_menu
            self.drag_manager, # If created and assigned to self.drag_manager
            # self.tray_icon # Removed, as InteractionManager may not own it directly
        ]
        
        for subsystem in subsystems_to_shutdown:
            if subsystem:
                # HotkeyManager uses stop(), others might use shutdown()
                if isinstance(subsystem, HotkeyManager) and hasattr(subsystem, 'stop'):
                    try:
                        logger.debug(f"Stopping subsystem {subsystem.__class__.__name__}")
                        subsystem.stop()
                    except Exception as e:
                        logger.error(f"Error stopping subsystem {subsystem.__class__.__name__}: {str(e)}", exc_info=True)
                elif hasattr(subsystem, 'shutdown'):
                    try:
                        logger.debug(f"Shutting down subsystem {subsystem.__class__.__name__}")
                        subsystem.shutdown()
                    except Exception as e:
                        logger.error(f"Error shutting down subsystem {subsystem.__class__.__name__}: {str(e)}", exc_info=True)
                # Add specific shutdown methods if a general 'shutdown' or 'stop' is not applicable

        self.clear_filters()
        self.clear_throttlers()
        self.reset_event_stats()
        
        self._initialized = False
        logger.info("InteractionManager shut down successfully")
        return True # 明确返回True表示成功 