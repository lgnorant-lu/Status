"""
---------------------------------------------------------------
File name:                  note_store.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                笔记存储器，管理笔记的持久化存储
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""
import json
import os
import logging
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

class NoteStore:
    """笔记存储类，管理笔记的持久化及内存操作"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化笔记存储器
        
        Args:
            config: 配置信息，包含存储路径等
        """
        self.logger = logging.getLogger("NoteStore")
        self.config = config or {}
        
        # 存储路径
        self.storage_path = self.config.get("storage_path", "data/notes.json")
        
        # 确保存储目录存在
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        
        # 内存中的笔记数据
        self.notes: Dict[str, Dict[str, Any]] = {}
        
        # 笔记标签
        self.tags: Dict[str, List[str]] = {}
        
        # 加载已有笔记
        self._load_notes()
        
        self.logger.info("笔记存储器初始化完成")
    
    def _load_notes(self) -> None:
        """从文件加载笔记数据"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.notes = data.get('notes', {})
                    self.tags = data.get('tags', {})
                self.logger.info(f"已从 {self.storage_path} 加载 {len(self.notes)} 条笔记")
            else:
                self.logger.info("笔记存储文件不存在，将创建新文件")
        except Exception as e:
            self.logger.error(f"加载笔记数据失败: {e}")
            # 重置数据
            self.notes = {}
            self.tags = {}
    
    def _save_notes(self) -> bool:
        """保存笔记数据到文件
        
        Returns:
            bool: 是否成功保存
        """
        try:
            data = {
                'notes': self.notes,
                'tags': self.tags,
                'last_update': datetime.now().isoformat()
            }
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"已保存 {len(self.notes)} 条笔记到 {self.storage_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存笔记数据失败: {e}")
            return False
    
    def create_note(self, title: str, content: str, tags: List[str] = None) -> str:
        """
        创建新笔记
        
        Args:
            title: 笔记标题
            content: 笔记内容
            tags: 笔记标签列表
            
        Returns:
            str: 笔记ID
        """
        note_id = str(uuid.uuid4())
        created_time = datetime.now().isoformat()
        
        # 创建笔记对象
        note = {
            'id': note_id,
            'title': title,
            'content': content,
            'tags': tags or [],
            'created_time': created_time,
            'updated_time': created_time,
            'is_pinned': False,
            'is_archived': False
        }
        
        # 存储笔记
        self.notes[note_id] = note
        
        # 更新标签索引
        if tags:
            for tag in tags:
                if tag not in self.tags:
                    self.tags[tag] = []
                self.tags[tag].append(note_id)
        
        # 保存到文件
        self._save_notes()
        
        self.logger.info(f"已创建笔记 '{title}' (ID: {note_id})")
        return note_id
    
    def update_note(self, note_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新笔记
        
        Args:
            note_id: 笔记ID
            updates: 要更新的字段
            
        Returns:
            bool: 是否成功更新
        """
        if note_id not in self.notes:
            self.logger.warning(f"笔记 {note_id} 不存在")
            return False
        
        note = self.notes[note_id]
        
        # 记录旧标签，用于更新标签索引
        old_tags = note.get('tags', [])
        
        # 更新字段
        for key, value in updates.items():
            if key in ['title', 'content', 'is_pinned', 'is_archived', 'tags']:
                note[key] = value
        
        # 更新时间
        note['updated_time'] = datetime.now().isoformat()
        
        # 如果更新了标签，更新标签索引
        if 'tags' in updates:
            new_tags = updates['tags']
            
            # 从旧标签中移除
            for tag in old_tags:
                if tag in self.tags and note_id in self.tags[tag]:
                    self.tags[tag].remove(note_id)
                    # 如果标签没有关联的笔记，删除这个标签
                    if not self.tags[tag]:
                        del self.tags[tag]
            
            # 添加到新标签
            for tag in new_tags:
                if tag not in self.tags:
                    self.tags[tag] = []
                if note_id not in self.tags[tag]:
                    self.tags[tag].append(note_id)
        
        # 保存到文件
        self._save_notes()
        
        self.logger.info(f"已更新笔记 '{note['title']}' (ID: {note_id})")
        return True
    
    def delete_note(self, note_id: str) -> bool:
        """
        删除笔记
        
        Args:
            note_id: 笔记ID
            
        Returns:
            bool: 是否成功删除
        """
        if note_id not in self.notes:
            self.logger.warning(f"笔记 {note_id} 不存在")
            return False
        
        note = self.notes[note_id]
        
        # 从标签索引中移除
        for tag in note.get('tags', []):
            if tag in self.tags and note_id in self.tags[tag]:
                self.tags[tag].remove(note_id)
                # 如果标签没有关联的笔记，删除这个标签
                if not self.tags[tag]:
                    del self.tags[tag]
        
        # 删除笔记
        del self.notes[note_id]
        
        # 保存到文件
        self._save_notes()
        
        self.logger.info(f"已删除笔记 '{note['title']}' (ID: {note_id})")
        return True
    
    def get_note(self, note_id: str) -> Optional[Dict[str, Any]]:
        """
        获取笔记
        
        Args:
            note_id: 笔记ID
            
        Returns:
            Optional[Dict[str, Any]]: 笔记数据，不存在则返回None
        """
        if note_id not in self.notes:
            self.logger.warning(f"笔记 {note_id} 不存在")
            return None
        
        # 返回笔记副本
        return self.notes[note_id].copy()
    
    def get_all_notes(self, include_archived: bool = False) -> List[Dict[str, Any]]:
        """
        获取所有笔记
        
        Args:
            include_archived: 是否包含已归档的笔记
            
        Returns:
            List[Dict[str, Any]]: 笔记列表
        """
        if include_archived:
            notes = list(self.notes.values())
        else:
            notes = [note for note in self.notes.values() if not note.get('is_archived', False)]
        
        # 返回笔记副本
        return [note.copy() for note in notes]
    
    def get_notes_by_tag(self, tag: str, include_archived: bool = False) -> List[Dict[str, Any]]:
        """
        获取指定标签的笔记
        
        Args:
            tag: 标签
            include_archived: 是否包含已归档的笔记
            
        Returns:
            List[Dict[str, Any]]: 笔记列表
        """
        if tag not in self.tags:
            return []
        
        note_ids = self.tags[tag]
        notes = []
        
        for note_id in note_ids:
            if note_id in self.notes:
                note = self.notes[note_id]
                if include_archived or not note.get('is_archived', False):
                    notes.append(note.copy())
        
        return notes
    
    def get_all_tags(self) -> List[str]:
        """
        获取所有标签
        
        Returns:
            List[str]: 标签列表
        """
        return list(self.tags.keys())
    
    def search_notes(self, query: str, include_archived: bool = False) -> List[Dict[str, Any]]:
        """
        搜索笔记
        
        Args:
            query: 搜索关键词
            include_archived: 是否包含已归档的笔记
            
        Returns:
            List[Dict[str, Any]]: 匹配的笔记列表
        """
        query = query.lower()
        results = []
        
        for note in self.notes.values():
            if not include_archived and note.get('is_archived', False):
                continue
                
            # 搜索标题和内容
            if (query in note['title'].lower() or 
                query in note['content'].lower()):
                results.append(note.copy())
                continue
                
            # 搜索标签
            for tag in note.get('tags', []):
                if query in tag.lower():
                    results.append(note.copy())
                    break
        
        return results
    
    def get_pinned_notes(self) -> List[Dict[str, Any]]:
        """
        获取置顶笔记
        
        Returns:
            List[Dict[str, Any]]: 置顶笔记列表
        """
        pinned_notes = [
            note.copy() for note in self.notes.values() 
            if note.get('is_pinned', False) and not note.get('is_archived', False)
        ]
        return pinned_notes
    
    def get_recent_notes(self, limit: int = 10, include_archived: bool = False) -> List[Dict[str, Any]]:
        """
        获取最近更新的笔记
        
        Args:
            limit: 返回的笔记数量限制
            include_archived: 是否包含已归档的笔记
            
        Returns:
            List[Dict[str, Any]]: 最近更新的笔记列表
        """
        notes = self.get_all_notes(include_archived)
        
        # 按更新时间排序
        notes.sort(key=lambda x: x['updated_time'], reverse=True)
        
        # 限制数量
        return notes[:limit]
    
    def clear_all_notes(self) -> bool:
        """
        清空所有笔记
        
        Returns:
            bool: 是否成功清空
        """
        self.notes = {}
        self.tags = {}
        success = self._save_notes()
        
        if success:
            self.logger.info("已清空所有笔记")
        
        return success 