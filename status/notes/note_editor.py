"""
---------------------------------------------------------------
File name:                  note_editor.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                笔记编辑器，提供笔记的创建和编辑功能
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""
import logging
from typing import Dict, Any, List, Optional, Callable, Union
import re
import time
from datetime import datetime

class NoteEditor:
    """笔记编辑器类，提供笔记的创建和编辑功能"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化笔记编辑器
        
        Args:
            config: 配置信息
        """
        self.logger = logging.getLogger("NoteEditor")
        self.config = config or {}
        
        # 编辑历史
        self.history_enabled = self.config.get('history_enabled', True)
        self.max_history_steps = self.config.get('max_history_steps', 20)
        self.history: Dict[str, List[Dict[str, Any]]] = {}
        
        # 当前编辑的笔记
        self.current_note_id: Optional[str] = None
        self.current_note: Optional[Dict[str, Any]] = None
        
        # 自动保存
        self.auto_save_enabled = self.config.get('auto_save_enabled', True)
        self.auto_save_interval = self.config.get('auto_save_interval', 30)  # 秒
        self.last_auto_save_time = 0
        
        # 编辑回调函数
        self.callbacks: Dict[str, List[Callable]] = {
            'on_note_opened': [],
            'on_note_closed': [],
            'on_note_saved': [],
            'on_auto_save': [],
            'on_content_changed': []
        }
        
        # 内容分析
        self.auto_tags_enabled = self.config.get('auto_tags_enabled', True)
        
        self.logger.info("笔记编辑器初始化完成")
    
    def open_note(self, note: Dict[str, Any]) -> bool:
        """
        打开笔记进行编辑
        
        Args:
            note: 笔记数据
            
        Returns:
            bool: 是否成功打开
        """
        # 确保先关闭当前笔记
        if self.current_note_id:
            self.close_note(save=True)
        
        note_id = note.get('id')
        if not note_id:
            self.logger.error("无效的笔记，缺少ID")
            return False
        
        # 创建笔记副本
        self.current_note = note.copy()
        self.current_note_id = note_id
        
        # 初始化历史记录
        if self.history_enabled and note_id not in self.history:
            self.history[note_id] = [self.current_note.copy()]
        
        # 重置自动保存时间
        self.last_auto_save_time = time.time()
        
        # 触发回调
        self._trigger_callbacks('on_note_opened', self.current_note)
        
        self.logger.info(f"已打开笔记 '{note['title']}' (ID: {note_id})")
        return True
    
    def close_note(self, save: bool = True) -> bool:
        """
        关闭当前笔记
        
        Args:
            save: 是否保存更改
            
        Returns:
            bool: 是否成功关闭
        """
        if not self.current_note_id:
            return False
        
        # 如需保存，返回当前笔记副本
        result = self.current_note.copy() if save else None
        
        # 触发回调
        self._trigger_callbacks('on_note_closed', {
            'note': self.current_note,
            'save': save
        })
        
        note_id = self.current_note_id
        
        # 清除当前笔记
        self.current_note = None
        self.current_note_id = None
        
        self.logger.info(f"已关闭笔记 (ID: {note_id}), 保存: {save}")
        return True
    
    def update_content(self, content: str) -> bool:
        """
        更新笔记内容
        
        Args:
            content: 新内容
            
        Returns:
            bool: 是否成功更新
        """
        if not self.current_note:
            self.logger.warning("没有打开的笔记")
            return False
        
        # 更新内容
        self.current_note['content'] = content
        self.current_note['updated_time'] = datetime.now().isoformat()
        
        # 添加到历史记录
        self._add_to_history()
        
        # 触发内容变更回调
        self._trigger_callbacks('on_content_changed', self.current_note)
        
        # 检查自动保存
        self._check_auto_save()
        
        # 如果启用了自动标签，分析内容
        if self.auto_tags_enabled:
            self._analyze_content()
        
        return True
    
    def update_title(self, title: str) -> bool:
        """
        更新笔记标题
        
        Args:
            title: 新标题
            
        Returns:
            bool: 是否成功更新
        """
        if not self.current_note:
            self.logger.warning("没有打开的笔记")
            return False
        
        # 更新标题
        self.current_note['title'] = title
        self.current_note['updated_time'] = datetime.now().isoformat()
        
        # 添加到历史记录
        self._add_to_history()
        
        # 检查自动保存
        self._check_auto_save()
        
        return True
    
    def add_tag(self, tag: str) -> bool:
        """
        添加标签
        
        Args:
            tag: 标签
            
        Returns:
            bool: 是否成功添加
        """
        if not self.current_note:
            self.logger.warning("没有打开的笔记")
            return False
        
        if 'tags' not in self.current_note:
            self.current_note['tags'] = []
        
        if tag not in self.current_note['tags']:
            self.current_note['tags'].append(tag)
            self.current_note['updated_time'] = datetime.now().isoformat()
            
            # 添加到历史记录
            self._add_to_history()
            
            # 检查自动保存
            self._check_auto_save()
            
            return True
        
        return False
    
    def remove_tag(self, tag: str) -> bool:
        """
        移除标签
        
        Args:
            tag: 标签
            
        Returns:
            bool: 是否成功移除
        """
        if not self.current_note or 'tags' not in self.current_note:
            self.logger.warning("没有打开的笔记或笔记没有标签")
            return False
        
        if tag in self.current_note['tags']:
            self.current_note['tags'].remove(tag)
            self.current_note['updated_time'] = datetime.now().isoformat()
            
            # 添加到历史记录
            self._add_to_history()
            
            # 检查自动保存
            self._check_auto_save()
            
            return True
        
        return False
    
    def toggle_pin(self) -> bool:
        """
        切换置顶状态
        
        Returns:
            bool: 切换后的置顶状态
        """
        if not self.current_note:
            self.logger.warning("没有打开的笔记")
            return False
        
        # 切换状态
        is_pinned = not self.current_note.get('is_pinned', False)
        self.current_note['is_pinned'] = is_pinned
        self.current_note['updated_time'] = datetime.now().isoformat()
        
        # 添加到历史记录
        self._add_to_history()
        
        # 检查自动保存
        self._check_auto_save()
        
        return is_pinned
    
    def toggle_archive(self) -> bool:
        """
        切换归档状态
        
        Returns:
            bool: 切换后的归档状态
        """
        if not self.current_note:
            self.logger.warning("没有打开的笔记")
            return False
        
        # 切换状态
        is_archived = not self.current_note.get('is_archived', False)
        self.current_note['is_archived'] = is_archived
        self.current_note['updated_time'] = datetime.now().isoformat()
        
        # 添加到历史记录
        self._add_to_history()
        
        # 检查自动保存
        self._check_auto_save()
        
        return is_archived
    
    def get_current_note(self) -> Optional[Dict[str, Any]]:
        """
        获取当前编辑的笔记
        
        Returns:
            Optional[Dict[str, Any]]: 当前笔记副本，未打开则返回None
        """
        if not self.current_note:
            return None
        
        return self.current_note.copy()
    
    def undo(self) -> bool:
        """
        撤销操作
        
        Returns:
            bool: 是否成功撤销
        """
        if not self.history_enabled or not self.current_note_id:
            return False
        
        history_list = self.history.get(self.current_note_id, [])
        if len(history_list) < 2:
            # 没有可撤销的历史记录
            return False
        
        # 移除当前状态
        history_list.pop()
        
        # 恢复到上一个状态
        self.current_note = history_list[-1].copy()
        
        # 重置自动保存时间
        self.last_auto_save_time = time.time()
        
        self.logger.debug(f"已撤销操作，剩余历史步骤: {len(history_list)}")
        return True
    
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
            self.logger.warning(f"无效的事件类型: {event_type}")
            return False
        
        if callback not in self.callbacks[event_type]:
            self.callbacks[event_type].append(callback)
            return True
        
        return False
    
    def unregister_callback(self, event_type: str, callback: Callable) -> bool:
        """
        注销回调函数
        
        Args:
            event_type: 事件类型
            callback: 回调函数
            
        Returns:
            bool: 是否成功注销
        """
        if event_type not in self.callbacks:
            return False
        
        if callback in self.callbacks[event_type]:
            self.callbacks[event_type].remove(callback)
            return True
        
        return False
    
    def force_save(self) -> bool:
        """
        强制保存
        
        Returns:
            bool: 是否成功保存
        """
        if not self.current_note:
            self.logger.warning("没有打开的笔记")
            return False
        
        # 触发保存回调
        self._trigger_callbacks('on_note_saved', self.current_note)
        
        # 更新保存时间
        self.last_auto_save_time = time.time()
        
        self.logger.info(f"强制保存笔记 '{self.current_note['title']}'")
        return True
    
    def _trigger_callbacks(self, event_type: str, data: Any) -> None:
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
                self.logger.error(f"回调函数执行失败: {e}")
    
    def _add_to_history(self) -> None:
        """添加当前状态到历史记录"""
        if not self.history_enabled or not self.current_note_id:
            return
        
        history_list = self.history.get(self.current_note_id, [])
        
        # 添加当前状态的副本
        history_list.append(self.current_note.copy())
        
        # 限制历史记录长度
        if len(history_list) > self.max_history_steps:
            history_list.pop(0)
        
        # 更新历史记录
        self.history[self.current_note_id] = history_list
    
    def _check_auto_save(self) -> None:
        """检查是否需要自动保存"""
        if not self.auto_save_enabled or not self.current_note:
            return
        
        current_time = time.time()
        if current_time - self.last_auto_save_time >= self.auto_save_interval:
            # 触发自动保存回调
            self._trigger_callbacks('on_auto_save', self.current_note)
            
            # 更新保存时间
            self.last_auto_save_time = current_time
            
            self.logger.debug(f"自动保存笔记 '{self.current_note['title']}'")
    
    def _analyze_content(self) -> None:
        """分析笔记内容，提取标签"""
        if not self.current_note:
            return
        
        content = self.current_note['content']
        
        # 查找内容中的标签，格式为 #标签名
        tag_pattern = r'#(\w+)'
        tags = re.findall(tag_pattern, content)
        
        # 添加找到的标签
        for tag in tags:
            if tag and 'tags' in self.current_note and tag not in self.current_note['tags']:
                self.current_note['tags'].append(tag)
                self.logger.debug(f"从内容中提取标签: {tag}") 