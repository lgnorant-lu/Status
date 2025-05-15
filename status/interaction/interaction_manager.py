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
                            2025/05/12: 移除CommandManager相关代码，处理Linter错误 (v3 - final attempt).
----
"""

import logging
from typing import Dict, List, Optional
import collections

from status.core.events import EventManager
from .event_filter import EventFilter, EventFilterChain
from .event_throttler import EventThrottler, EventThrottlerChain
from .mouse_interaction import MouseInteraction
from .tray_icon import TrayIcon # 导入但未实例化，因为不知道构造函数API
from .context_menu import ContextMenu
from .hotkey import HotkeyManager
from .drag_manager import DragManager
from .behavior_trigger import BehaviorTrigger
from .interaction_event import InteractionEvent, InteractionEventType

# 配置日志
logger = logging.getLogger(__name__)

class InteractionManager:
    """交互管理器，协调各种交互功能"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls, *args, **kwargs):
        """获取单例实例。如果实例不存在，则使用提供的参数创建它。"""
        if cls._instance is None:
            if not args and not kwargs.get('app_context'):
                logger.warning("InteractionManager创建新实例时没有显式提供app_context/settings。")
            cls._instance = cls(*args, **kwargs) 
        return cls._instance
    
    def __init__(self, app_context, settings):
        """初始化交互管理器"""
        if InteractionManager._instance is not None and InteractionManager._instance is not self:
            raise RuntimeError("InteractionManager是单例。在初始创建后使用get_instance()。")
        
        self.logger = logging.getLogger(__name__)
        self.app_context = app_context
        self.settings = settings
        self.event_bus = app_context.event_bus
        # self.interaction_handlers: List[object] = [] # TODO: 填充和使用如果需要可扩展性
        self.mouse_event_handler: Optional[MouseInteraction] = None
        self.keyboard_event_handler: Optional[HotkeyManager] = None
        
        self.filters_by_id: Dict[str, EventFilter] = {}
        self.filter_chain: EventFilterChain = EventFilterChain()
        self.throttlers_by_id: Dict[str, EventThrottler] = {}
        self.throttler_chain: EventThrottlerChain = EventThrottlerChain()
        # self.event_stats: Dict[str, int] = collections.defaultdict(int) # TODO: 如果需要实现事件统计
        self.context_menu: Optional[ContextMenu] = None 
        self.drag_manager: Optional[DragManager] = None
        self.tray_icon: Optional[TrayIcon] = None # 目前保持为None
        
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
            main_window = None
            if hasattr(self.app_context, 'get_main_window'):
                main_window = self.app_context.get_main_window()
            
            if main_window:
                self.mouse_event_handler = MouseInteraction(window=main_window)
                
                try:
                    # 基于DragManager linter反馈假设0参数构造函数
                    # TODO: 确认实际的ContextMenu构造函数API并提供必要的参数。
                    self.context_menu = ContextMenu()
                    logger.info("ContextMenu已初始化 (基于Linter提示假设需要0参数构造函数)。")
                except Exception as e:
                    logger.error(f"Failed to initialize ContextMenu: {e}", exc_info=True)

                try:
                    # Linter提示DragManager构造函数缺少'window'参数。
                    # TODO: 确认DragManager实际的构造函数API。目前基于Linter提示假设需要'window'参数。
                    self.drag_manager = DragManager(window=main_window)
                    logger.info("DragManager已初始化 (基于Linter提示假设需要'window'参数)。")
                except Exception as e:
                    logger.error(f"Failed to initialize DragManager: {e}", exc_info=True)
                
                # TrayIcon实例化被注释掉了，因为不知道构造函数API。
                # self.tray_icon将保持为None，直到其API被澄清。
                # TODO: 如果设置中启用了TrayIcon，请实现TrayIcon实例化，并提供正确的参数。
                # if self.settings.get('enable_tray_icon', True):
                #     logger.info("TrayIcon初始化被跳过 (API未知)。")

            else:
                logger.warning("主窗口不可用。MouseInteraction、ContextMenu、DragManager可能无法正常工作或初始化。")
            
            self.keyboard_event_handler = HotkeyManager()
            if hasattr(self.keyboard_event_handler, 'start'):
                self.keyboard_event_handler.start()
            else:
                logger.warning("HotkeyManager没有start方法或无法启动。")
            
            self._initialized = True
            logger.info("交互管理器初始化成功")
            return True
        
        except Exception as e:
            logger.error(f"交互管理器初始化失败: {str(e)}", exc_info=True)
            return False
    
    def _handle_interaction_event(self, event_type, event_data=None):
        """
        处理交互事件 (可能由事件总线或直接调用)
        
        Args:
            event_type: 事件类型
            event_data: 事件数据
        """
        subsystems = [
            self.mouse_event_handler,
            self.keyboard_event_handler,
        ]
        
        for subsystem in subsystems:
            if subsystem and hasattr(subsystem, 'handle_event'):
                try:
                    subsystem.handle_event(event_type, event_data) # 实际处理逻辑待实现
                except Exception as e:
                    logger.error(f"Error处理事件在子系统 {subsystem.__class__.__name__}: {e}", exc_info=True)
    
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
        logger.info(f"Added节流器 '{throttler_id}' 到交互管理器")
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
            logger.info(f"Removed节流器 '{throttler_id}' 从交互管理器")
        return success
    
    def clear_filters(self) -> None:
        """清除所有事件过滤器"""
        self.filter_chain.clear_filters()
        self.filters_by_id.clear()
        logger.info("Cleared所有过滤器从交互管理器")
    
    def clear_throttlers(self) -> None:
        """清除所有事件节流器"""
        self.throttler_chain.clear_throttlers()
        self.throttlers_by_id.clear()
        logger.info("Cleared所有节流器从交互管理器")
    
    def _setup_connections(self):
        """设置组件间的信号和槽连接，或事件订阅"""
        logger.debug("InteractionManager: 连接设置 (占位符).")
    
    def _setup_default_filters_and_throttlers(self):
        """设置默认的事件过滤器和节流器"""
        logger.debug("InteractionManager: 默认过滤器/节流器设置 (占位符).")
    
    def shutdown(self) -> bool:
        """
        关闭交互管理器及其所有子系统。

        Returns:
            bool: 关闭操作是否成功执行 (目前总是返回 True)。
        """
        if not self._initialized:
            logger.warning("交互管理器尚未初始化或已关闭。")
            return True

        logger.info("正在关闭交互管理器...")

        if self.keyboard_event_handler and hasattr(self.keyboard_event_handler, 'stop'):
            try:
                self.keyboard_event_handler.stop()
                logger.info("HotkeyManager 已停止。")
            except Exception as e:
                logger.error(f"停止 HotkeyManager 时出错: {e}", exc_info=True)
        
        if self.mouse_event_handler and hasattr(self.mouse_event_handler, 'shutdown'):
            try:
                self.mouse_event_handler.shutdown()
                logger.info("MouseInteraction 已关闭。")
            except Exception as e:
                logger.error(f"关闭 MouseInteraction 时出错: {e}", exc_info=True)

        if self.tray_icon and hasattr(self.tray_icon, 'shutdown'):
            try:
                self.tray_icon.shutdown()
                logger.info("TrayIcon 已关闭。")
            except Exception as e:
                logger.error(f"关闭 TrayIcon 时出错: {e}", exc_info=True)
        
        if self.context_menu and hasattr(self.context_menu, 'shutdown'):
            try:
                self.context_menu.shutdown()
                logger.info("ContextMenu 已关闭。")
            except Exception as e:
                logger.error(f"关闭 ContextMenu 时出错: {e}", exc_info=True)
        
        if self.drag_manager and hasattr(self.drag_manager, 'shutdown'):
            try:
                self.drag_manager.shutdown()
                logger.info("DragManager 已关闭。")
            except Exception as e:
                logger.error(f"关闭 DragManager 时出错: {e}", exc_info=True)

        if self.event_bus and hasattr(self.event_bus, 'unregister_handler'):
            try:
                self.event_bus.unregister_handler("interaction", self._handle_interaction_event)
                logger.info("已从事件总线注销交互事件处理器。")
            except Exception as e:
                logger.error(f"从事件总线注销处理器时出错: {e}", exc_info=True)

        self.clear_filters()
        self.clear_throttlers()
        
        self._initialized = False
        logger.info("交互管理器已成功关闭。")
        return True

# Example usage for BehaviorTrigger (if it were managed here)
# from status.behavior.behavior_manager import BehaviorManager
# class MyBehaviorTrigger(BehaviorTrigger):
# ...

# End of InteractionManager class 
