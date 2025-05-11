"""
---------------------------------------------------------------
File name:                  scheduler.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                提醒调度器，管理提醒的定时触发
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""
import logging
import threading
import time
from typing import Dict, Any, List, Callable, Union, Optional
from datetime import datetime, timedelta

class ReminderScheduler:
    """提醒调度器类，管理提醒的定时触发"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化提醒调度器
        
        Args:
            config: 配置信息
        """
        self.logger = logging.getLogger("ReminderScheduler")
        self.config = config or {}
        # 扫描间隔（秒）
        self.scan_interval = self.config.get("scan_interval", 15)
        # 存储定时任务
        self.timers: Dict[str, threading.Timer] = {}
        # 回调函数字典
        self.callbacks: Dict[str, List[Callable]] = {
            "on_reminder_triggered": [], # 提醒触发时的回调
            "on_reminder_added": [],     # 添加提醒时的回调
            "on_reminder_removed": [],   # 移除提醒时的回调
            "on_scheduler_error": []     # 调度器错误时的回调
        }
        # 运行状态
        self.running = False
        # 主线程
        self.thread = None
        self.logger.info("提醒调度器初始化完成")
    
    def start(self) -> bool:
        """
        启动调度器
        
        Returns:
            bool: 是否成功启动
        """
        if self.running:
            self.logger.warning("调度器已经在运行中")
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.thread.start()
        self.logger.info("提醒调度器已启动")
        return True
    
    def stop(self) -> bool:
        """
        停止调度器
        
        Returns:
            bool: 是否成功停止
        """
        if not self.running:
            self.logger.warning("调度器未在运行")
            return False
        
        self.running = False
        # 清理所有定时器
        for timer_id, timer in list(self.timers.items()):
            self._cancel_timer(timer_id)
        
        # 等待主线程结束
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        
        self.logger.info("提醒调度器已停止")
        return True
    
    def is_running(self) -> bool:
        """
        检查调度器是否在运行
        
        Returns:
            bool: 调度器运行状态
        """
        return self.running
    
    def _scheduler_loop(self) -> None:
        """调度器主循环"""
        while self.running:
            try:
                # 执行定时检查
                self.logger.debug("执行提醒扫描")
                time.sleep(self.scan_interval)
            except Exception as e:
                self.logger.error(f"调度器循环发生错误: {e}")
                self._trigger_callbacks("on_scheduler_error", {"error": str(e)})
                # 短暂休息后继续
                time.sleep(1)
    
    def schedule_reminder(self, reminder_id: str, reminder_time: datetime, 
                         reminder_data: Dict[str, Any]) -> bool:
        """
        调度一个提醒
        
        Args:
            reminder_id: 提醒ID
            reminder_time: 提醒时间
            reminder_data: 提醒数据
            
        Returns:
            bool: 是否成功调度
        """
        try:
            # 取消已存在的同ID定时器
            if reminder_id in self.timers:
                self._cancel_timer(reminder_id)
            
            # 计算定时器延迟（秒）
            now = datetime.now()
            if reminder_time <= now:
                self.logger.warning(f"提醒 {reminder_id} 时间已过期，将立即触发")
                self._trigger_reminder(reminder_id, reminder_data)
                return True
            
            delay = (reminder_time - now).total_seconds()
            
            # 创建新定时器
            timer = threading.Timer(
                delay,
                self._trigger_reminder, 
                args=[reminder_id, reminder_data]
            )
            timer.daemon = True
            timer.start()
            
            self.timers[reminder_id] = timer
            self.logger.info(f"已调度提醒 {reminder_id}，将在 {delay:.2f} 秒后触发")
            self._trigger_callbacks("on_reminder_added", {
                "reminder_id": reminder_id,
                "time": reminder_time,
                "data": reminder_data
            })
            return True
        except Exception as e:
            self.logger.error(f"调度提醒 {reminder_id} 失败: {e}")
            self._trigger_callbacks("on_scheduler_error", {
                "reminder_id": reminder_id,
                "error": str(e)
            })
            return False
    
    def cancel_reminder(self, reminder_id: str) -> bool:
        """
        取消一个提醒
        
        Args:
            reminder_id: 提醒ID
            
        Returns:
            bool: 是否成功取消
        """
        return self._cancel_timer(reminder_id)
    
    def _cancel_timer(self, timer_id: str) -> bool:
        """
        取消定时器
        
        Args:
            timer_id: 定时器ID
            
        Returns:
            bool: 是否成功取消
        """
        if timer_id not in self.timers:
            self.logger.warning(f"定时器 {timer_id} 不存在，无法取消")
            return False
        
        try:
            timer = self.timers[timer_id]
            timer.cancel()
            del self.timers[timer_id]
            self.logger.info(f"已取消定时器 {timer_id}")
            self._trigger_callbacks("on_reminder_removed", {"reminder_id": timer_id})
            return True
        except Exception as e:
            self.logger.error(f"取消定时器 {timer_id} 失败: {e}")
            return False
    
    def _trigger_reminder(self, reminder_id: str, reminder_data: Dict[str, Any]) -> None:
        """
        触发提醒
        
        Args:
            reminder_id: 提醒ID
            reminder_data: 提醒数据
        """
        try:
            self.logger.info(f"触发提醒 {reminder_id}")
            # 从定时器列表中移除
            if reminder_id in self.timers:
                del self.timers[reminder_id]
            
            # 触发回调
            self._trigger_callbacks("on_reminder_triggered", {
                "reminder_id": reminder_id,
                "data": reminder_data,
                "trigger_time": datetime.now()
            })
        except Exception as e:
            self.logger.error(f"触发提醒 {reminder_id} 时发生错误: {e}")
            self._trigger_callbacks("on_scheduler_error", {
                "reminder_id": reminder_id,
                "error": str(e)
            })
    
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
                self._trigger_callbacks("on_scheduler_error", {"error": str(e)}) 