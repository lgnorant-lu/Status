"""
---------------------------------------------------------------
File name:                  notification.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                通知渲染器，管理提醒通知的展示
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""
import logging
import time
import threading
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime

class NotificationRenderer:
    """通知渲染器类，管理提醒通知的展示"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化通知渲染器
        
        Args:
            config: 配置信息
        """
        self.logger = logging.getLogger("NotificationRenderer")
        self.config = config or {}
        
        # 默认样式
        self.default_styles = {
            'info': {
                'color': '#2ECC40',
                'icon': 'info-circle',
                'duration': 5  # 秒
            },
            'warning': {
                'color': '#FF851B',
                'icon': 'exclamation-triangle',
                'duration': 8  # 秒
            },
            'error': {
                'color': '#FF4136',
                'icon': 'exclamation-circle',
                'duration': 10  # 秒
            },
            'success': {
                'color': '#2ECC40',
                'icon': 'check-circle',
                'duration': 5  # 秒
            }
        }
        
        # 用户配置的样式
        user_styles = self.config.get('styles', {})
        for style_name, style_config in user_styles.items():
            if style_name in self.default_styles:
                self.default_styles[style_name].update(style_config)
            else:
                self.default_styles[style_name] = style_config
        
        # 活动通知列表
        self.active_notifications: List[Dict[str, Any]] = []
        
        # 最大同时显示通知数
        self.max_notifications = self.config.get('max_notifications', 5)
        
        # 通知回调
        self.callbacks: Dict[str, List[Callable]] = {
            'on_notification_show': [],
            'on_notification_click': [],
            'on_notification_close': [],
            'on_notification_error': []
        }
        
        # 系统通知功能是否可用
        self.system_notification_available = False
        try:
            # 这里根据平台尝试初始化系统通知
            # 例如，在Windows上可以使用win10toast，在MacOS上可以使用pync
            # 简化起见，这里不做实际实现
            self.logger.info("系统通知功能可用")
            self.system_notification_available = True
        except Exception as e:
            self.logger.warning(f"系统通知功能不可用: {e}")
        
        self.logger.info("通知渲染器初始化完成")
    
    def show_notification(self, 
                        title: str, 
                        message: str, 
                        notification_type: str = 'info', 
                        data: Dict[str, Any] = None, 
                        callback: Callable = None) -> str:
        """
        显示通知
        
        Args:
            title: 通知标题
            message: 通知内容
            notification_type: 通知类型 (info, warning, error, success)
            data: 附加数据
            callback: 点击回调
            
        Returns:
            str: 通知ID
        """
        try:
            notification_id = f"notification_{int(time.time() * 1000)}"
            style = self.default_styles.get(notification_type, self.default_styles['info'])
            
            notification = {
                'id': notification_id,
                'title': title,
                'message': message,
                'type': notification_type,
                'style': style,
                'data': data or {},
                'create_time': datetime.now(),
                'read': False
            }
            
            # 系统通知
            if self.system_notification_available:
                self._show_system_notification(notification)
            
            # 应用内通知
            self._show_app_notification(notification)
            
            # 添加到活动通知列表
            self.active_notifications.append(notification)
            
            # 限制列表长度
            if len(self.active_notifications) > self.max_notifications:
                oldest = self.active_notifications.pop(0)
                self.logger.debug(f"移除最早的通知 {oldest['id']}")
            
            # 如果提供了回调，注册为点击事件
            if callback:
                def click_handler(data):
                    if data.get('id') == notification_id:
                        callback(data)
                
                self.register_callback('on_notification_click', click_handler)
            
            # 触发显示回调
            self._trigger_callbacks('on_notification_show', notification)
            
            # 启动自动关闭定时器
            duration = style.get('duration', 5)
            if duration > 0:
                def close_notification():
                    time.sleep(duration)
                    self.close_notification(notification_id)
                
                thread = threading.Thread(target=close_notification)
                thread.daemon = True
                thread.start()
            
            self.logger.info(f"已显示通知 {notification_id}，类型：{notification_type}")
            return notification_id
        
        except Exception as e:
            self.logger.error(f"显示通知失败: {e}")
            self._trigger_callbacks('on_notification_error', {
                'error': str(e),
                'title': title,
                'message': message
            })
            return ""
    
    def _show_system_notification(self, notification: Dict[str, Any]) -> None:
        """
        显示系统通知
        
        Args:
            notification: 通知信息
        """
        # 这里根据平台调用系统通知API
        # 简化起见，这里不做实际实现
        self.logger.debug(f"系统通知: {notification['title']}")
    
    def _show_app_notification(self, notification: Dict[str, Any]) -> None:
        """
        显示应用内通知
        
        Args:
            notification: 通知信息
        """
        # 这里与应用UI交互，显示通知
        # 简化起见，这里不做实际实现
        self.logger.debug(f"应用内通知: {notification['title']}")
    
    def close_notification(self, notification_id: str) -> bool:
        """
        关闭通知
        
        Args:
            notification_id: 通知ID
            
        Returns:
            bool: 是否成功关闭
        """
        for i, notification in enumerate(self.active_notifications):
            if notification['id'] == notification_id:
                notification = self.active_notifications.pop(i)
                self._trigger_callbacks('on_notification_close', notification)
                self.logger.debug(f"已关闭通知 {notification_id}")
                return True
        
        self.logger.warning(f"通知 {notification_id} 不存在或已关闭")
        return False
    
    def close_all_notifications(self) -> int:
        """
        关闭所有通知
        
        Returns:
            int: 关闭的通知数量
        """
        count = len(self.active_notifications)
        for notification in list(self.active_notifications):
            self._trigger_callbacks('on_notification_close', notification)
        
        self.active_notifications = []
        self.logger.info(f"已关闭所有通知，共 {count} 个")
        return count
    
    def update_notification(self, notification_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新通知内容
        
        Args:
            notification_id: 通知ID
            updates: 更新的字段
            
        Returns:
            bool: 是否成功更新
        """
        for notification in self.active_notifications:
            if notification['id'] == notification_id:
                for key, value in updates.items():
                    if key in notification and key not in ['id', 'create_time']:
                        notification[key] = value
                
                self.logger.debug(f"已更新通知 {notification_id}")
                return True
        
        self.logger.warning(f"通知 {notification_id} 不存在，无法更新")
        return False
    
    def get_notification(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """
        获取通知信息
        
        Args:
            notification_id: 通知ID
            
        Returns:
            Optional[Dict[str, Any]]: 通知信息，不存在则返回None
        """
        for notification in self.active_notifications:
            if notification['id'] == notification_id:
                return notification.copy()
        
        return None
    
    def get_all_notifications(self) -> List[Dict[str, Any]]:
        """
        获取所有活动通知
        
        Returns:
            List[Dict[str, Any]]: 通知列表
        """
        return [notification.copy() for notification in self.active_notifications]
    
    def register_callback(self, event_type: str, callback: Callable) -> bool:
        """
        注册回调函数
        
        Args:
            event_type: 事件类型
            callback: 回调函数
            
        Returns:
            bool: 是否成功注册
        """
        if event_type not in self.callbacks:
            self.logger.warning(f"未知的事件类型: {event_type}")
            return False
        
        self.callbacks[event_type].append(callback)
        return True
    
    def unregister_callback(self, event_type: str, callback: Callable) -> bool:
        """
        取消注册回调函数
        
        Args:
            event_type: 事件类型
            callback: 回调函数
            
        Returns:
            bool: 是否成功取消注册
        """
        if event_type not in self.callbacks:
            self.logger.warning(f"未知的事件类型: {event_type}")
            return False
        
        if callback in self.callbacks[event_type]:
            self.callbacks[event_type].remove(callback)
            return True
        
        return False
    
    def _trigger_callbacks(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        触发回调函数
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        if event_type not in self.callbacks:
            return
        
        for callback in self.callbacks[event_type]:
            try:
                callback(data)
            except Exception as e:
                self.logger.error(f"执行事件 {event_type} 的回调函数失败: {e}")
                self._trigger_callbacks('on_notification_error', {
                    'error': str(e),
                    'event_type': event_type
                }) 