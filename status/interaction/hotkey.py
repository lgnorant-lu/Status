"""
---------------------------------------------------------------
File name:                  hotkey.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                桌宠全局热键管理模块
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import logging
import sys
import threading
from PySide6.QtCore import QObject, Signal, Qt
from status.core.events import EventManager
from status.interaction.interaction_event import InteractionEvent, InteractionEventType
from typing import Callable, Optional, Dict, List, Any, TYPE_CHECKING

# 配置日志
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from status.interaction.hotkey_mac import register_hotkey as register_hotkey_mac, unregister_hotkey as unregister_hotkey_mac, listen as listen_mac # type: ignore [import-not-found]
    from status.interaction.hotkey_linux import register_hotkey as register_hotkey_linux, unregister_hotkey as unregister_hotkey_linux, listen as listen_linux # type: ignore [import-not-found]


class HotkeyManager(QObject):
    """全局热键管理类
    
    管理桌宠应用的全局热键，支持注册和触发热键。
    根据不同操作系统使用不同的全局热键实现。
    """
    
    # 定义信号
    hotkey_triggered_signal = Signal(str)
    
    def __init__(self):
        """初始化热键管理器
        """
        super().__init__()
        self.event_manager = EventManager.get_instance()
        
        # 热键字典，键是热键组合，值是回调函数
        self.hotkeys = {}
        
        # 标记后台线程是否应该继续运行
        self.running = False
        
        # 后台监听线程
        self.listener_thread = None
        
        # 热键监听器
        self.listener = None
        
        # 平台特定的热键处理器
        self.platform_handler = None
        
        # 初始化平台特定的处理器
        self._init_platform_handler()
        
        logger.info("HotkeyManager initialized")
    
    def _init_platform_handler(self):
        """初始化平台特定的热键处理器
        
        根据不同操作系统初始化相应的热键处理器。
        """
        platform = sys.platform
        
        if platform.startswith('win'):
            # Windows平台
            try:
                # 尝试导入Windows平台所需的库
                # 注意：这需要安装pywin32库
                from status.interaction.hotkey_win import WindowsHotkeyHandler
                
                self.platform_handler = WindowsHotkeyHandler()
                logger.info("Initialized Windows hotkey handler")
                
            except ImportError as e:
                logger.error(f"Failed to import Windows libraries for hotkey: {str(e)}")
                logger.warning("Global hotkeys will not be available")
                
        elif platform.startswith('darwin'):
            # macOS平台
            try:
                # 这需要安装PyObjC库
                from status.interaction.hotkey_mac import MacHotkeyHandler
                
                self.platform_handler = MacHotkeyHandler()
                logger.info("Initialized macOS hotkey handler")
                
            except ImportError as e:
                logger.error(f"Failed to import macOS libraries for hotkey: {str(e)}")
                logger.warning("Global hotkeys will not be available")
                
        elif platform.startswith('linux'):
            # Linux平台
            try:
                # 这需要安装python-xlib库
                from status.interaction.hotkey_linux import LinuxHotkeyHandler
                
                self.platform_handler = LinuxHotkeyHandler()
                logger.info("Initialized Linux hotkey handler")
                
            except ImportError as e:
                logger.error(f"Failed to import Linux libraries for hotkey: {str(e)}")
                logger.warning("Global hotkeys will not be available")
        
        else:
            logger.warning(f"Unsupported platform for global hotkeys: {platform}")
            logger.warning("Global hotkeys will not be available")
    
    def start(self):
        """启动热键监听
        
        开始监听全局热键。
        
        Returns:
            bool: 是否成功启动
        """
        if not self.platform_handler:
            logger.error("No platform handler available, cannot start hotkey listening")
            return False
        
        if self.running:
            logger.warning("Hotkey listener already running")
            return True
        
        try:
            self.running = True
            
            # 创建并启动监听线程
            self.listener_thread = threading.Thread(
                target=self._listener_thread_func,
                daemon=True
            )
            self.listener_thread.start()
            
            logger.info("Hotkey listener started")
            return True
            
        except Exception as e:
            self.running = False
            logger.error(f"Failed to start hotkey listener: {str(e)}")
            return False
    
    def stop(self):
        """停止热键监听
        
        停止监听全局热键。
        
        Returns:
            bool: 是否成功停止
        """
        if not self.running:
            logger.warning("Hotkey listener not running")
            return True
        
        try:
            self.running = False
            
            # 如果有线程在运行，等待它结束
            if self.listener_thread and self.listener_thread.is_alive():
                self.listener_thread.join(timeout=1.0)
            
            # 调用平台处理器的停止方法
            if self.platform_handler:
                self.platform_handler.stop()
            
            logger.info("Hotkey listener stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop hotkey listener: {str(e)}")
            return False
    
    def _listener_thread_func(self):
        """热键监听线程函数
        
        在后台线程中监听全局热键。
        """
        logger.debug("Hotkey listener thread started")
        
        try:
            # 开始平台特定的热键监听
            self.platform_handler.start(self._on_hotkey_callback)
            
            # 持续监听，直到被停止
            while self.running:
                # 使用平台处理器的轮询方法
                self.platform_handler.poll()
                
        except Exception as e:
            logger.error(f"Error in hotkey listener thread: {str(e)}")
            self.running = False
        
        logger.debug("Hotkey listener thread ended")
    
    def _on_hotkey_callback(self, key_combination):
        """热键回调函数
        
        当热键被触发时调用此函数。
        
        Args:
            key_combination (str): 热键组合字符串
        """
        logger.debug(f"Hotkey triggered: {key_combination}")
        
        # 发出信号
        self.hotkey_triggered_signal.emit(key_combination)
        
        # 创建并发布热键事件
        ev = InteractionEvent.create_hotkey_event(key_combination)
        self.event_manager.post_event(ev)
        
        # 如果有注册的回调函数，调用它
        if key_combination in self.hotkeys:
            callback = self.hotkeys[key_combination]
            try:
                callback(key_combination)
            except Exception as e:
                logger.error(f"Error calling hotkey callback for {key_combination}: {str(e)}")
    
    def register_hotkey(self, key_combination, callback):
        """注册热键
        
        Args:
            key_combination (str): 热键组合字符串，例如"Ctrl+Alt+P"
            callback (function): 热键触发时的回调函数
            
        Returns:
            bool: 是否成功注册
        """
        if not self.platform_handler:
            logger.error("No platform handler available, cannot register hotkey")
            return False
        
        try:
            # 检查热键是否已经注册
            if key_combination in self.hotkeys:
                logger.warning(f"Hotkey {key_combination} already registered, updating callback")
                
                # 更新回调函数
                self.hotkeys[key_combination] = callback
                return True
            
            # 使用平台处理器注册热键
            if self.platform_handler.register_hotkey(key_combination):
                # 存储回调函数
                self.hotkeys[key_combination] = callback
                logger.info(f"Registered hotkey: {key_combination}")
                return True
            else:
                logger.error(f"Failed to register hotkey: {key_combination}")
                return False
            
        except Exception as e:
            logger.error(f"Error registering hotkey {key_combination}: {str(e)}")
            return False
    
    def unregister_hotkey(self, key_combination):
        """注销热键
        
        Args:
            key_combination (str): 热键组合字符串
            
        Returns:
            bool: 是否成功注销
        """
        if not self.platform_handler:
            logger.error("No platform handler available, cannot unregister hotkey")
            return False
        
        try:
            # 检查热键是否已经注册
            if key_combination not in self.hotkeys:
                logger.warning(f"Hotkey {key_combination} not registered")
                return False
            
            # 使用平台处理器注销热键
            if self.platform_handler.unregister_hotkey(key_combination):
                # 移除回调函数
                del self.hotkeys[key_combination]
                logger.info(f"Unregistered hotkey: {key_combination}")
                return True
            else:
                logger.error(f"Failed to unregister hotkey: {key_combination}")
                return False
            
        except Exception as e:
            logger.error(f"Error unregistering hotkey {key_combination}: {str(e)}")
            return False
    
    def is_hotkey_registered(self, key_combination):
        """检查热键是否已注册
        
        Args:
            key_combination (str): 热键组合字符串
            
        Returns:
            bool: 热键是否已注册
        """
        return key_combination in self.hotkeys
    
    def handle_event(self, event):
        """处理交互事件
        
        这个方法用于处理从交互管理器传来的事件。
        
        Args:
            event: 要处理的事件
        """
        # 只处理与热键相关的事件
        if (hasattr(event, 'interaction_type') and 
            event.interaction_type == InteractionEventType.HOTKEY_TRIGGERED):
            logger.debug(f"HotkeyManager handling event: {event}")
            # 此处可以根据需要添加对特定事件的处理
    
    def shutdown(self):
        """关闭热键管理器
        
        清理资源，注销所有热键。
        
        Returns:
            bool: 是否成功关闭
        """
        logger.info("Shutting down HotkeyManager")
        
        # 停止监听
        success = self.stop()
        
        # 注销所有热键
        if self.platform_handler:
            # 复制键列表，因为在循环中会修改字典
            key_combinations = list(self.hotkeys.keys())
            
            for key_combination in key_combinations:
                self.unregister_hotkey(key_combination)
        
        return success