"""
---------------------------------------------------------------
File name:                  screenshot_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                截图管理器，协调截图服务和系统集成
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, Callable, Tuple, List, Union
import os

from status.core.events import EventManager, Event, EventType, InteractionEvent, InteractionEventType
from status.screenshot.screenshot_service import ScreenshotService, ScreenshotError

# 配置日志记录器
logger = logging.getLogger(__name__)

class ScreenshotEventType:
    """截图相关的事件类型常量"""
    SCREENSHOT_TAKEN = "screenshot_taken"       # 截图已完成
    SCREENSHOT_FAILED = "screenshot_failed"     # 截图失败
    SCREENSHOT_COPIED = "screenshot_copied"     # 截图已复制到剪贴板
    REGION_SELECTION_START = "region_selection_start"   # 开始区域选择
    REGION_SELECTION_END = "region_selection_end"       # 结束区域选择

class ScreenshotManager:
    """截图管理器
    
    协调截图服务与系统其他组件的交互，
    处理热键触发、事件分发等功能。
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化截图管理器
        
        Args:
            config: 配置参数
        """
        # 基础配置
        self.config = config or {}
        
        # 创建截图服务
        service_config = self.config.get('service', {})
        self.screenshot_service = ScreenshotService(service_config)
        
        # 获取事件管理器
        self.event_manager = EventManager.get_instance()
        
        # 是否正在捕获区域
        self.selecting_region = False
        self.selection_start = None
        self.selection_end = None
        
        # 最近的截图记录
        self.recent_screenshots = []
        self.max_recent_count = self.config.get('max_recent_count', 10)
        
        # 是否自动复制到剪贴板
        self.auto_copy = self.config.get('auto_copy', True)
        
        # 是否显示通知
        self.show_notification = self.config.get('show_notification', True)
        
        # 截图计数（本次启动后）
        self.screenshot_count = 0
        
        # 注册事件回调
        self._register_event_handlers()
        
        # 注册服务回调
        self._register_service_callbacks()
        
        logger.info("截图管理器已初始化")
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        # 注册热键事件处理
        self.event_manager.register_handler(EventType.USER_INTERACTION, self._handle_interaction_event)
        
        logger.debug("已注册事件处理器")
    
    def _register_service_callbacks(self):
        """注册截图服务回调"""
        # 注册截图完成回调
        self.screenshot_service.register_screenshot_callback(self._on_screenshot_taken)
        
        # 注册错误回调
        self.screenshot_service.register_error_callback(self._on_screenshot_error)
        
        logger.debug("已注册服务回调")
    
    def _handle_interaction_event(self, event: Event):
        """处理交互事件
        
        Args:
            event: 交互事件
        """
        # 只处理用户交互类型的事件
        if event.type != EventType.USER_INTERACTION:
            return
            
        # 转换为交互事件
        if not isinstance(event, InteractionEvent):
            return
            
        interaction_event = event
        
        # 处理热键事件
        if interaction_event.interaction_type == InteractionEventType.HOTKEY_PRESSED:
            hotkey = interaction_event.data
            
            # 处理截图相关的热键
            if hotkey == self.config.get('full_screenshot_hotkey', 'F12'):
                logger.debug(f"触发全屏截图热键: {hotkey}")
                self.take_full_screenshot()
                event.handled = True
                
            elif hotkey == self.config.get('region_screenshot_hotkey', 'Ctrl+Shift+F12'):
                logger.debug(f"触发区域截图热键: {hotkey}")
                self.start_region_selection()
                event.handled = True
                
            elif hotkey == self.config.get('window_screenshot_hotkey', 'Alt+F12'):
                logger.debug(f"触发窗口截图热键: {hotkey}")
                self.take_window_screenshot()
                event.handled = True
        
        # 处理鼠标事件（用于区域选择）
        if self.selecting_region:
            if interaction_event.interaction_type == InteractionEventType.MOUSE_CLICK:
                # 记录选择起点
                if self.selection_start is None:
                    self.selection_start = interaction_event.position
                    logger.debug(f"区域选择起点: {self.selection_start}")
                    event.handled = True
                    
                # 记录选择终点并完成选择
                elif self.selection_end is None:
                    self.selection_end = interaction_event.position
                    logger.debug(f"区域选择终点: {self.selection_end}")
                    self.complete_region_selection()
                    event.handled = True
    
    def _on_screenshot_taken(self, filepath: str):
        """截图完成回调
        
        Args:
            filepath: 截图文件路径
        """
        # 记录截图
        self.screenshot_count += 1
        
        # 添加到最近记录
        self.recent_screenshots.append(filepath)
        if len(self.recent_screenshots) > self.max_recent_count:
            self.recent_screenshots.pop(0)
        
        # 发布事件
        self.event_manager.dispatch_event(
            EventType.USER_INTERACTION,
            self,
            {"type": ScreenshotEventType.SCREENSHOT_TAKEN, "filepath": filepath}
        )
        
        logger.info(f"截图已完成: {filepath}")
        
        # 自动复制到剪贴板
        if self.auto_copy:
            self.copy_to_clipboard(filepath)
    
    def _on_screenshot_error(self, error_message: str):
        """截图错误回调
        
        Args:
            error_message: 错误消息
        """
        # 发布事件
        self.event_manager.dispatch_event(
            EventType.ERROR,
            self,
            {"type": ScreenshotEventType.SCREENSHOT_FAILED, "message": error_message}
        )
        
        logger.error(f"截图失败: {error_message}")
    
    def take_full_screenshot(self) -> Optional[str]:
        """获取全屏截图
        
        Returns:
            str: 截图文件路径，失败时返回None
        """
        try:
            return self.screenshot_service.take_full_screenshot()
        except ScreenshotError as e:
            logger.error(f"全屏截图失败: {str(e)}")
            return None
    
    def take_region_screenshot(self, region: Tuple[int, int, int, int]) -> Optional[str]:
        """获取区域截图
        
        Args:
            region: 区域坐标和大小 (x, y, width, height)
            
        Returns:
            str: 截图文件路径，失败时返回None
        """
        try:
            return self.screenshot_service.take_region_screenshot(region)
        except ScreenshotError as e:
            logger.error(f"区域截图失败: {str(e)}")
            return None
    
    def take_window_screenshot(self, window_title: str = None) -> Optional[str]:
        """获取窗口截图
        
        Args:
            window_title: 窗口标题，为None时捕获活动窗口
            
        Returns:
            str: 截图文件路径，失败时返回None
        """
        try:
            return self.screenshot_service.take_window_screenshot(window_title)
        except ScreenshotError as e:
            logger.error(f"窗口截图失败: {str(e)}")
            return None
    
    def start_region_selection(self):
        """开始区域选择"""
        self.selecting_region = True
        self.selection_start = None
        self.selection_end = None
        
        # 发布区域选择开始事件
        self.event_manager.dispatch_event(
            EventType.USER_INTERACTION,
            self,
            {"type": ScreenshotEventType.REGION_SELECTION_START}
        )
        
        logger.debug("开始区域选择")
    
    def complete_region_selection(self):
        """完成区域选择并获取区域截图"""
        if not self.selecting_region or self.selection_start is None or self.selection_end is None:
            logger.warning("区域选择不完整，无法完成")
            return None
        
        # 计算区域坐标和大小
        x1, y1 = self.selection_start
        x2, y2 = self.selection_end
        
        # 确保x1 <= x2且y1 <= y2
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        
        width = x2 - x1
        height = y2 - y1
        
        # 发布区域选择结束事件
        self.event_manager.dispatch_event(
            EventType.USER_INTERACTION,
            self,
            {
                "type": ScreenshotEventType.REGION_SELECTION_END,
                "region": (x1, y1, width, height)
            }
        )
        
        # 重置选择状态
        self.selecting_region = False
        
        # 获取区域截图
        return self.take_region_screenshot((x1, y1, width, height))
    
    def cancel_region_selection(self):
        """取消区域选择"""
        self.selecting_region = False
        self.selection_start = None
        self.selection_end = None
        
        logger.debug("区域选择已取消")
    
    def is_selecting_region(self) -> bool:
        """是否正在选择区域
        
        Returns:
            bool: 是否正在选择区域
        """
        return self.selecting_region
    
    def get_recent_screenshots(self) -> List[str]:
        """获取最近的截图列表
        
        Returns:
            List[str]: 截图文件路径列表
        """
        return self.recent_screenshots.copy()
    
    def clear_recent_screenshots(self):
        """清空最近的截图记录"""
        self.recent_screenshots.clear()
        logger.debug("已清空最近截图记录")
    
    def copy_to_clipboard(self, filepath: Optional[str] = None) -> bool:
        """将截图复制到剪贴板
        
        Args:
            filepath: 截图文件路径，为None时使用最后一次的截图
            
        Returns:
            bool: 是否成功复制
        """
        try:
            result = self.screenshot_service.copy_to_clipboard(filepath)
            
            if result:
                # 发布事件
                self.event_manager.dispatch_event(
                    EventType.USER_INTERACTION,
                    self,
                    {
                        "type": ScreenshotEventType.SCREENSHOT_COPIED,
                        "filepath": filepath or self.screenshot_service.get_last_screenshot()
                    }
                )
            
            return result
        except Exception as e:
            logger.error(f"复制到剪贴板失败: {str(e)}")
            return False
    
    def set_auto_copy(self, enabled: bool):
        """设置是否自动复制到剪贴板
        
        Args:
            enabled: 是否启用
        """
        self.auto_copy = enabled
        logger.debug(f"自动复制到剪贴板已{'启用' if enabled else '禁用'}")
    
    def set_show_notification(self, enabled: bool):
        """设置是否显示通知
        
        Args:
            enabled: 是否启用
        """
        self.show_notification = enabled
        logger.debug(f"截图通知已{'启用' if enabled else '禁用'}")
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """更新配置
        
        Args:
            new_config: 新的配置参数
            
        Returns:
            bool: 是否成功更新
        """
        try:
            # 更新管理器配置
            for key, value in new_config.items():
                if key != 'service':  # 服务配置单独处理
                    self.config[key] = value
            
            # 更新自动复制设置
            if 'auto_copy' in new_config:
                self.auto_copy = new_config['auto_copy']
            
            # 更新通知设置
            if 'show_notification' in new_config:
                self.show_notification = new_config['show_notification']
            
            # 更新最近记录数量
            if 'max_recent_count' in new_config:
                self.max_recent_count = new_config['max_recent_count']
                # 裁剪列表到新的最大大小
                if len(self.recent_screenshots) > self.max_recent_count:
                    self.recent_screenshots = self.recent_screenshots[-self.max_recent_count:]
            
            # 更新服务配置
            if 'service' in new_config:
                service_config = new_config['service']
                
                # 设置保存目录
                if 'save_dir' in service_config:
                    self.screenshot_service.set_save_directory(service_config['save_dir'])
                
                # 设置格式
                if 'format' in service_config:
                    self.screenshot_service.set_format(service_config['format'])
                
                # 设置文件名模式
                if 'filename_pattern' in service_config:
                    self.screenshot_service.set_filename_pattern(service_config['filename_pattern'])
                
                # 设置是否包含光标
                if 'include_cursor' in service_config:
                    self.screenshot_service.include_cursor = service_config['include_cursor']
            
            logger.info("截图管理器配置已更新")
            return True
            
        except Exception as e:
            logger.error(f"更新配置失败: {str(e)}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置
        
        Returns:
            Dict[str, Any]: 当前配置
        """
        return self.config
    
    def get_screenshot_count(self) -> int:
        """获取截图计数
        
        Returns:
            int: 本次启动后的截图数量
        """
        return self.screenshot_count
    
    def open_save_directory(self) -> bool:
        """打开保存目录
        
        Returns:
            bool: 是否成功打开
        """
        return self.screenshot_service.open_save_directory()
    
    def shutdown(self):
        """关闭截图管理器"""
        # 注销事件处理器
        self.event_manager.unregister_handler(EventType.USER_INTERACTION, self._handle_interaction_event)
        
        # 清理资源
        self.selecting_region = False
        
        logger.info("截图管理器已关闭") 