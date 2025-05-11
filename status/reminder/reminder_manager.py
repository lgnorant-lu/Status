"""
---------------------------------------------------------------
File name:                  reminder_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                提醒管理器，整合提醒系统的各个组件
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""
import logging
import uuid
import threading
import time
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from datetime import datetime, timedelta

from .reminder_store import ReminderStore
from .scheduler import ReminderScheduler
from .notification import NotificationRenderer

class ReminderManager:
    """提醒管理器类，整合提醒系统的各个组件"""
    
    def __init__(self, config: Dict[str, Any] = None,
                store: ReminderStore = None,
                scheduler: ReminderScheduler = None,
                notification_renderer: NotificationRenderer = None):
        """
        初始化提醒管理器
        
        Args:
            config: 配置信息
            store: 提醒存储器实例
            scheduler: 提醒调度器实例
            notification_renderer: 通知渲染器实例
        """
        self.logger = logging.getLogger("ReminderManager")
        self.config = config or {}
        
        # 初始化组件
        self.store = store or ReminderStore(self.config.get('store_config', {}))
        self.scheduler = scheduler or ReminderScheduler(self.config.get('scheduler_config', {}))
        self.notification_renderer = notification_renderer or NotificationRenderer(
            self.config.get('notification_config', {})
        )
        
        # 回调函数
        self.callbacks: Dict[str, List[Callable]] = {
            'on_reminder_created': [],
            'on_reminder_updated': [],
            'on_reminder_deleted': [],
            'on_reminder_triggered': [],
            'on_error': []
        }
        
        # 加载现有提醒
        self._is_initialized = False
        self._load_and_schedule_reminders()
        self._is_initialized = True
        
        # 注册调度器回调
        self._register_scheduler_callbacks()
        
        self.logger.info("提醒管理器初始化完成")
    
    def _load_and_schedule_reminders(self) -> None:
        """加载并调度已存在的提醒"""
        try:
            reminders = self.store.get_active_reminders()
            self.logger.info(f"加载了 {len(reminders)} 个活动提醒")
            
            for reminder_id, reminder in reminders.items():
                reminder_time = reminder.get('time')
                if reminder_time and isinstance(reminder_time, datetime):
                    self.scheduler.schedule_reminder(reminder_id, reminder_time, reminder)
        except Exception as e:
            self.logger.error(f"加载并调度提醒失败: {e}")
            self._trigger_callbacks('on_error', {'error': str(e)})
    
    def _register_scheduler_callbacks(self) -> None:
        """注册调度器回调函数"""
        # 提醒触发回调
        self.scheduler.register_callback('on_reminder_triggered', self._on_reminder_triggered)
        # 调度器错误回调
        self.scheduler.register_callback('on_scheduler_error', self._on_scheduler_error)
    
    def _on_reminder_triggered(self, data: Dict[str, Any]) -> None:
        """
        提醒触发回调
        
        Args:
            data: 事件数据
        """
        reminder_id = data.get('reminder_id')
        reminder_data = data.get('data', {})
        
        if not reminder_id or not reminder_data:
            self.logger.warning("触发的提醒数据不完整")
            return
        
        try:
            # 显示通知
            title = reminder_data.get('title', '提醒')
            message = reminder_data.get('message', '您有一个提醒')
            notification_type = reminder_data.get('notification_type', 'info')
            
            notification_id = self.notification_renderer.show_notification(
                title=title,
                message=message,
                notification_type=notification_type,
                data={'reminder_id': reminder_id}
            )
            
            # 处理提醒（如标记为已触发）
            reminder = self.store.get_reminder(reminder_id)
            if reminder:
                reminder['triggered'] = True
                reminder['notification_id'] = notification_id
                reminder['trigger_time'] = datetime.now()
                self.store.update_reminder(reminder_id, reminder)
            
            # 触发回调
            self._trigger_callbacks('on_reminder_triggered', {
                'reminder_id': reminder_id,
                'data': reminder_data,
                'notification_id': notification_id
            })
            
            self.logger.info(f"提醒 {reminder_id} 已触发并显示通知")
        except Exception as e:
            self.logger.error(f"处理提醒触发失败: {e}")
            self._trigger_callbacks('on_error', {
                'error': str(e),
                'reminder_id': reminder_id
            })
    
    def _on_scheduler_error(self, data: Dict[str, Any]) -> None:
        """
        调度器错误回调
        
        Args:
            data: 错误数据
        """
        error = data.get('error', '未知错误')
        self.logger.error(f"调度器错误: {error}")
        self._trigger_callbacks('on_error', {'error': error})
    
    def start(self) -> bool:
        """
        启动提醒管理器
        
        Returns:
            bool: 是否成功启动
        """
        try:
            result = self.scheduler.start()
            if result:
                self.logger.info("提醒管理器已启动")
            else:
                self.logger.warning("提醒管理器启动失败")
            return result
        except Exception as e:
            self.logger.error(f"启动提醒管理器失败: {e}")
            self._trigger_callbacks('on_error', {'error': str(e)})
            return False
    
    def stop(self) -> bool:
        """
        停止提醒管理器
        
        Returns:
            bool: 是否成功停止
        """
        try:
            result = self.scheduler.stop()
            if result:
                self.logger.info("提醒管理器已停止")
            else:
                self.logger.warning("提醒管理器停止失败")
            return result
        except Exception as e:
            self.logger.error(f"停止提醒管理器失败: {e}")
            self._trigger_callbacks('on_error', {'error': str(e)})
            return False
    
    def is_running(self) -> bool:
        """
        检查提醒管理器是否在运行
        
        Returns:
            bool: 提醒管理器运行状态
        """
        return self.scheduler.is_running()
    
    def create_reminder(self, 
                       title: str, 
                       message: str, 
                       reminder_time: datetime,
                       notification_type: str = 'info',
                       repeat: Optional[Dict[str, Any]] = None,
                       data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        创建新提醒
        
        Args:
            title: 提醒标题
            message: 提醒内容
            reminder_time: 提醒时间
            notification_type: 通知类型
            repeat: 重复设置，如 {'type': 'daily', 'interval': 1}
            data: 附加数据
            
        Returns:
            Optional[str]: 提醒ID，失败则返回None
        """
        try:
            # 生成唯一ID
            reminder_id = str(uuid.uuid4())
            
            # 创建提醒数据
            reminder_data = {
                'title': title,
                'message': message,
                'time': reminder_time,
                'notification_type': notification_type,
                'repeat': repeat,
                'data': data or {},
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'active': True,
                'triggered': False
            }
            
            # 存储提醒
            store_result = self.store.add_reminder(reminder_id, reminder_data)
            if not store_result:
                self.logger.error(f"存储提醒 {reminder_id} 失败")
                return None
            
            # 调度提醒
            schedule_result = self.scheduler.schedule_reminder(
                reminder_id, reminder_time, reminder_data
            )
            
            if not schedule_result:
                self.logger.warning(f"调度提醒 {reminder_id} 失败")
            
            # 触发回调
            self._trigger_callbacks('on_reminder_created', {
                'reminder_id': reminder_id,
                'data': reminder_data
            })
            
            self.logger.info(f"创建提醒 {reminder_id}，将在 {reminder_time} 触发")
            return reminder_id
        
        except Exception as e:
            self.logger.error(f"创建提醒失败: {e}")
            self._trigger_callbacks('on_error', {'error': str(e)})
            return None
    
    def update_reminder(self, 
                       reminder_id: str, 
                       title: Optional[str] = None,
                       message: Optional[str] = None,
                       reminder_time: Optional[datetime] = None,
                       notification_type: Optional[str] = None,
                       repeat: Optional[Dict[str, Any]] = None,
                       data: Optional[Dict[str, Any]] = None,
                       active: Optional[bool] = None) -> bool:
        """
        更新提醒
        
        Args:
            reminder_id: 提醒ID
            title: 提醒标题
            message: 提醒内容
            reminder_time: 提醒时间
            notification_type: 通知类型
            repeat: 重复设置
            data: 附加数据
            active: 是否激活
            
        Returns:
            bool: 是否成功更新
        """
        try:
            # 获取原提醒
            reminder = self.store.get_reminder(reminder_id)
            if not reminder:
                self.logger.warning(f"提醒 {reminder_id} 不存在，无法更新")
                return False
            
            # 更新字段
            updates = {}
            if title is not None:
                updates['title'] = title
            if message is not None:
                updates['message'] = message
            if reminder_time is not None:
                updates['time'] = reminder_time
            if notification_type is not None:
                updates['notification_type'] = notification_type
            if repeat is not None:
                updates['repeat'] = repeat
            if data is not None:
                updates['data'] = {**reminder.get('data', {}), **data}
            if active is not None:
                updates['active'] = active
            
            updates['updated_at'] = datetime.now()
            
            # 合并更新
            updated_reminder = {**reminder, **updates}
            
            # 存储更新
            result = self.store.update_reminder(reminder_id, updated_reminder)
            if not result:
                self.logger.error(f"更新提醒 {reminder_id} 存储失败")
                return False
            
            # 如果时间变更，重新调度
            if reminder_time is not None or active is not None:
                # 取消旧调度
                self.scheduler.cancel_reminder(reminder_id)
                
                # 如果激活状态为True且时间在未来，重新调度
                if updated_reminder.get('active', True) and updated_reminder['time'] > datetime.now():
                    self.scheduler.schedule_reminder(
                        reminder_id, 
                        updated_reminder['time'], 
                        updated_reminder
                    )
            
            # 触发回调
            self._trigger_callbacks('on_reminder_updated', {
                'reminder_id': reminder_id,
                'data': updated_reminder,
                'updates': updates
            })
            
            self.logger.info(f"更新提醒 {reminder_id} 成功")
            return True
        
        except Exception as e:
            self.logger.error(f"更新提醒 {reminder_id} 失败: {e}")
            self._trigger_callbacks('on_error', {
                'error': str(e),
                'reminder_id': reminder_id
            })
            return False
    
    def delete_reminder(self, reminder_id: str) -> bool:
        """
        删除提醒
        
        Args:
            reminder_id: 提醒ID
            
        Returns:
            bool: 是否成功删除
        """
        try:
            # 取消调度
            self.scheduler.cancel_reminder(reminder_id)
            
            # 删除存储
            result = self.store.delete_reminder(reminder_id)
            if not result:
                self.logger.warning(f"删除提醒 {reminder_id} 存储失败")
                return False
            
            # 触发回调
            self._trigger_callbacks('on_reminder_deleted', {'reminder_id': reminder_id})
            
            self.logger.info(f"删除提醒 {reminder_id} 成功")
            return True
        
        except Exception as e:
            self.logger.error(f"删除提醒 {reminder_id} 失败: {e}")
            self._trigger_callbacks('on_error', {
                'error': str(e),
                'reminder_id': reminder_id
            })
            return False
    
    def get_reminder(self, reminder_id: str) -> Optional[Dict[str, Any]]:
        """
        获取提醒
        
        Args:
            reminder_id: 提醒ID
            
        Returns:
            Optional[Dict[str, Any]]: 提醒数据，不存在则返回None
        """
        return self.store.get_reminder(reminder_id)
    
    def get_all_reminders(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有提醒
        
        Returns:
            Dict[str, Dict[str, Any]]: 所有提醒数据
        """
        return self.store.get_all_reminders()
    
    def get_active_reminders(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有激活状态的提醒
        
        Returns:
            Dict[str, Dict[str, Any]]: 激活状态的提醒数据
        """
        return self.store.get_active_reminders()
    
    def clear_expired_reminders(self) -> int:
        """
        清除已过期的提醒
        
        Returns:
            int: 清除的提醒数量
        """
        return self.store.clear_expired_reminders()
    
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
        self.logger.debug(f"已注册事件 {event_type} 的回调函数")
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
            self.logger.debug(f"已取消注册事件 {event_type} 的回调函数")
            return True
        else:
            self.logger.warning(f"回调函数未注册在事件 {event_type} 中")
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