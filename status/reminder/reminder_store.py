"""
---------------------------------------------------------------
File name:                  reminder_store.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                提醒存储器，管理提醒的持久化存储
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""
import json
import os
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

class ReminderStore:
    """提醒存储类，管理提醒的持久化及内存操作"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化提醒存储器
        
        Args:
            config: 配置信息，包含存储路径等
        """
        self.logger = logging.getLogger("ReminderStore")
        self.config = config or {}
        # 存储路径
        self.storage_path = self.config.get("storage_path", "data/reminders.json")
        # 确保存储目录存在
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        # 内存中的提醒数据
        self.reminders: Dict[str, Dict[str, Any]] = {}
        # 加载已有提醒
        self._load_reminders()
        self.logger.info("提醒存储器初始化完成")
    
    def _load_reminders(self) -> None:
        """从文件加载提醒数据"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for reminder_id, reminder in data.items():
                        # 将字符串时间转换回datetime对象
                        if 'time' in reminder and isinstance(reminder['time'], str):
                            reminder['time'] = datetime.fromisoformat(reminder['time'])
                        self.reminders[reminder_id] = reminder
                self.logger.info(f"已加载 {len(self.reminders)} 个提醒")
            else:
                self.logger.info("提醒存储文件不存在，将创建新文件")
        except Exception as e:
            self.logger.error(f"加载提醒数据失败: {e}")
            self.reminders = {}
    
    def _save_reminders(self) -> None:
        """保存提醒数据到文件"""
        try:
            # 创建一个副本用于序列化，将datetime转为字符串
            serializable_reminders = {}
            for reminder_id, reminder in self.reminders.items():
                reminder_copy = reminder.copy()
                if 'time' in reminder_copy and isinstance(reminder_copy['time'], datetime):
                    reminder_copy['time'] = reminder_copy['time'].isoformat()
                serializable_reminders[reminder_id] = reminder_copy
                
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_reminders, f, ensure_ascii=False, indent=2)
            self.logger.debug(f"提醒数据已保存到 {self.storage_path}")
        except Exception as e:
            self.logger.error(f"保存提醒数据失败: {e}")
    
    def add_reminder(self, reminder_id: str, reminder: Dict[str, Any]) -> bool:
        """
        添加新的提醒
        
        Args:
            reminder_id: 提醒ID
            reminder: 提醒数据
            
        Returns:
            bool: 操作是否成功
        """
        try:
            if reminder_id in self.reminders:
                self.logger.warning(f"提醒ID {reminder_id} 已存在，将覆盖")
            self.reminders[reminder_id] = reminder
            self._save_reminders()
            self.logger.info(f"添加提醒 {reminder_id} 成功")
            return True
        except Exception as e:
            self.logger.error(f"添加提醒 {reminder_id} 失败: {e}")
            return False
    
    def update_reminder(self, reminder_id: str, reminder: Dict[str, Any]) -> bool:
        """
        更新提醒
        
        Args:
            reminder_id: 提醒ID
            reminder: 更新的提醒数据
            
        Returns:
            bool: 操作是否成功
        """
        if reminder_id not in self.reminders:
            self.logger.warning(f"提醒ID {reminder_id} 不存在，无法更新")
            return False
        try:
            self.reminders[reminder_id] = reminder
            self._save_reminders()
            self.logger.info(f"更新提醒 {reminder_id} 成功")
            return True
        except Exception as e:
            self.logger.error(f"更新提醒 {reminder_id} 失败: {e}")
            return False
    
    def delete_reminder(self, reminder_id: str) -> bool:
        """
        删除提醒
        
        Args:
            reminder_id: 提醒ID
            
        Returns:
            bool: 操作是否成功
        """
        if reminder_id not in self.reminders:
            self.logger.warning(f"提醒ID {reminder_id} 不存在，无法删除")
            return False
        try:
            del self.reminders[reminder_id]
            self._save_reminders()
            self.logger.info(f"删除提醒 {reminder_id} 成功")
            return True
        except Exception as e:
            self.logger.error(f"删除提醒 {reminder_id} 失败: {e}")
            return False
    
    def get_reminder(self, reminder_id: str) -> Optional[Dict[str, Any]]:
        """
        获取提醒
        
        Args:
            reminder_id: 提醒ID
            
        Returns:
            Optional[Dict[str, Any]]: 提醒数据，不存在则返回None
        """
        return self.reminders.get(reminder_id)
    
    def get_all_reminders(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有提醒
        
        Returns:
            Dict[str, Dict[str, Any]]: 所有提醒数据
        """
        return self.reminders.copy()
    
    def get_active_reminders(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有激活状态的提醒
        
        Returns:
            Dict[str, Dict[str, Any]]: 激活状态的提醒数据
        """
        now = datetime.now()
        return {
            reminder_id: reminder 
            for reminder_id, reminder in self.reminders.items() 
            if reminder.get('active', True) and reminder.get('time', now) > now
        }
    
    def get_expired_reminders(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有已过期的提醒
        
        Returns:
            Dict[str, Dict[str, Any]]: 已过期的提醒数据
        """
        now = datetime.now()
        return {
            reminder_id: reminder 
            for reminder_id, reminder in self.reminders.items() 
            if reminder.get('time', now) <= now
        }
    
    def clear_expired_reminders(self) -> int:
        """
        清除所有已过期的提醒
        
        Returns:
            int: 清除的提醒数量
        """
        expired = self.get_expired_reminders()
        for reminder_id in expired:
            del self.reminders[reminder_id]
        
        if expired:
            self._save_reminders()
            self.logger.info(f"已清除 {len(expired)} 个过期提醒")
        
        return len(expired)
    
    def clear_all_reminders(self) -> int:
        """
        清除所有提醒
        
        Returns:
            int: 清除的提醒数量
        """
        count = len(self.reminders)
        self.reminders = {}
        self._save_reminders()
        self.logger.info(f"已清除所有提醒，共 {count} 个")
        return count 