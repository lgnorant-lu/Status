"""
---------------------------------------------------------------
File name:                  note_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                笔记管理器，整合笔记系统的各个组件
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""
import logging
import threading
import time
from typing import Dict, List, Any, Optional, Callable, Union, Tuple

from .note_store import NoteStore
from .note_editor import NoteEditor

class NoteManager:
    """笔记管理器类，整合笔记系统的各个组件"""
    
    def __init__(self, config: Dict[str, Any] = None,
                store: NoteStore = None,
                editor: NoteEditor = None):
        """
        初始化笔记管理器
        
        Args:
            config: 配置信息
            store: 笔记存储器实例
            editor: 笔记编辑器实例
        """
        self.logger = logging.getLogger("NoteManager")
        self.config = config or {}
        
        # 初始化组件
        self.store = store or NoteStore(self.config.get('store_config', {}))
        self.editor = editor or NoteEditor(self.config.get('editor_config', {}))
        
        # 回调函数
        self.callbacks: Dict[str, List[Callable]] = {
            'on_note_created': [],
            'on_note_updated': [],
            'on_note_deleted': [],
            'on_note_opened': [],
            'on_note_closed': [],
            'on_search_complete': [],
            'on_error': []
        }
        
        # 注册编辑器回调
        self._register_editor_callbacks()
        
        # 缓存当前打开的笔记ID
        self.current_note_id: Optional[str] = None
        
        # 最后一次搜索结果
        self.last_search_results: List[Dict[str, Any]] = []
        
        # 是否已初始化
        self._is_initialized = True
        
        self.logger.info("笔记管理器初始化完成")
    
    def _register_editor_callbacks(self) -> None:
        """注册编辑器回调函数"""
        # 笔记保存回调
        self.editor.register_callback('on_note_saved', self._on_editor_save)
        
        # 自动保存回调
        self.editor.register_callback('on_auto_save', self._on_editor_auto_save)
        
        # 笔记打开回调
        self.editor.register_callback('on_note_opened', self._on_editor_note_opened)
        
        # 笔记关闭回调
        self.editor.register_callback('on_note_closed', self._on_editor_note_closed)
    
    def _on_editor_save(self, note: Dict[str, Any]) -> None:
        """
        处理编辑器保存事件
        
        Args:
            note: 笔记数据
        """
        # 更新存储
        if note and 'id' in note:
            success = self.store.update_note(note['id'], note)
            if success:
                # 触发更新回调
                self._trigger_callbacks('on_note_updated', note)
            else:
                self._trigger_callbacks('on_error', {
                    'action': 'update_note',
                    'note_id': note['id'],
                    'message': '存储失败'
                })
    
    def _on_editor_auto_save(self, note: Dict[str, Any]) -> None:
        """
        处理编辑器自动保存事件
        
        Args:
            note: 笔记数据
        """
        # 与普通保存相同处理
        self._on_editor_save(note)
    
    def _on_editor_note_opened(self, note: Dict[str, Any]) -> None:
        """
        处理编辑器笔记打开事件
        
        Args:
            note: 笔记数据
        """
        if note and 'id' in note:
            self.current_note_id = note['id']
            self._trigger_callbacks('on_note_opened', note)
    
    def _on_editor_note_closed(self, data: Dict[str, Any]) -> None:
        """
        处理编辑器笔记关闭事件
        
        Args:
            data: 事件数据，包含笔记和保存标志
        """
        note = data.get('note')
        save = data.get('save', True)
        
        if note and 'id' in note:
            if save:
                # 保存笔记
                self._on_editor_save(note)
            
            # 触发关闭回调
            self._trigger_callbacks('on_note_closed', note)
            
            # 清除当前笔记ID
            self.current_note_id = None
    
    def create_note(self, title: str, content: str = "", tags: List[str] = None) -> Optional[str]:
        """
        创建新笔记
        
        Args:
            title: 笔记标题
            content: 笔记内容
            tags: 笔记标签列表
            
        Returns:
            Optional[str]: 笔记ID，失败则返回None
        """
        try:
            # 创建笔记
            note_id = self.store.create_note(title, content, tags)
            
            if note_id:
                # 获取完整笔记数据
                note = self.store.get_note(note_id)
                
                # 触发创建回调
                self._trigger_callbacks('on_note_created', note)
                
                self.logger.info(f"已创建笔记 '{title}' (ID: {note_id})")
                return note_id
            else:
                self.logger.error(f"创建笔记 '{title}' 失败")
                self._trigger_callbacks('on_error', {
                    'action': 'create_note',
                    'title': title,
                    'message': '创建失败'
                })
                return None
        except Exception as e:
            self.logger.error(f"创建笔记异常: {e}")
            self._trigger_callbacks('on_error', {
                'action': 'create_note',
                'title': title,
                'message': str(e)
            })
            return None
    
    def delete_note(self, note_id: str) -> bool:
        """
        删除笔记
        
        Args:
            note_id: 笔记ID
            
        Returns:
            bool: 是否成功删除
        """
        try:
            # 如果当前正在编辑此笔记，先关闭它
            if self.current_note_id == note_id:
                self.close_current_note(save=False)
            
            # 获取笔记，用于回调
            note = self.store.get_note(note_id)
            
            # 删除笔记
            success = self.store.delete_note(note_id)
            
            if success and note:
                # 触发删除回调
                self._trigger_callbacks('on_note_deleted', note)
                
                self.logger.info(f"已删除笔记 (ID: {note_id})")
                return True
            else:
                self.logger.error(f"删除笔记 (ID: {note_id}) 失败")
                self._trigger_callbacks('on_error', {
                    'action': 'delete_note',
                    'note_id': note_id,
                    'message': '删除失败'
                })
                return False
        except Exception as e:
            self.logger.error(f"删除笔记异常: {e}")
            self._trigger_callbacks('on_error', {
                'action': 'delete_note',
                'note_id': note_id,
                'message': str(e)
            })
            return False
    
    def open_note(self, note_id: str) -> bool:
        """
        打开笔记进行编辑
        
        Args:
            note_id: 笔记ID
            
        Returns:
            bool: 是否成功打开
        """
        try:
            # 获取笔记
            note = self.store.get_note(note_id)
            
            if not note:
                self.logger.error(f"笔记 (ID: {note_id}) 不存在")
                self._trigger_callbacks('on_error', {
                    'action': 'open_note',
                    'note_id': note_id,
                    'message': '笔记不存在'
                })
                return False
            
            # 打开笔记
            success = self.editor.open_note(note)
            
            if success:
                self.current_note_id = note_id
                self.logger.info(f"已打开笔记 '{note['title']}' (ID: {note_id})")
                return True
            else:
                self.logger.error(f"打开笔记 (ID: {note_id}) 失败")
                self._trigger_callbacks('on_error', {
                    'action': 'open_note',
                    'note_id': note_id,
                    'message': '打开失败'
                })
                return False
        except Exception as e:
            self.logger.error(f"打开笔记异常: {e}")
            self._trigger_callbacks('on_error', {
                'action': 'open_note',
                'note_id': note_id,
                'message': str(e)
            })
            return False
    
    def close_current_note(self, save: bool = True) -> bool:
        """
        关闭当前笔记
        
        Args:
            save: 是否保存更改
            
        Returns:
            bool: 是否成功关闭
        """
        return self.editor.close_note(save)
    
    def get_current_note(self) -> Optional[Dict[str, Any]]:
        """
        获取当前编辑的笔记
        
        Returns:
            Optional[Dict[str, Any]]: 当前笔记，未打开则返回None
        """
        return self.editor.get_current_note()
    
    def update_current_note_content(self, content: str) -> bool:
        """
        更新当前笔记内容
        
        Args:
            content: 新内容
            
        Returns:
            bool: 是否成功更新
        """
        return self.editor.update_content(content)
    
    def update_current_note_title(self, title: str) -> bool:
        """
        更新当前笔记标题
        
        Args:
            title: 新标题
            
        Returns:
            bool: 是否成功更新
        """
        return self.editor.update_title(title)
    
    def force_save_current_note(self) -> bool:
        """
        强制保存当前笔记
        
        Returns:
            bool: 是否成功保存
        """
        return self.editor.force_save()
    
    def search_notes(self, query: str, include_archived: bool = False) -> List[Dict[str, Any]]:
        """
        搜索笔记
        
        Args:
            query: 搜索关键词
            include_archived: 是否包含已归档的笔记
            
        Returns:
            List[Dict[str, Any]]: 匹配的笔记列表
        """
        try:
            # 搜索笔记
            results = self.store.search_notes(query, include_archived)
            
            # 更新最后一次搜索结果
            self.last_search_results = results
            
            # 触发搜索完成回调
            self._trigger_callbacks('on_search_complete', {
                'query': query,
                'results': results,
                'count': len(results)
            })
            
            self.logger.info(f"搜索 '{query}' 找到 {len(results)} 条结果")
            return results
        except Exception as e:
            self.logger.error(f"搜索笔记异常: {e}")
            self._trigger_callbacks('on_error', {
                'action': 'search_notes',
                'query': query,
                'message': str(e)
            })
            return []
    
    def get_all_notes(self, include_archived: bool = False) -> List[Dict[str, Any]]:
        """
        获取所有笔记
        
        Args:
            include_archived: 是否包含已归档的笔记
            
        Returns:
            List[Dict[str, Any]]: 笔记列表
        """
        return self.store.get_all_notes(include_archived)
    
    def get_pinned_notes(self) -> List[Dict[str, Any]]:
        """
        获取置顶笔记
        
        Returns:
            List[Dict[str, Any]]: 置顶笔记列表
        """
        return self.store.get_pinned_notes()
    
    def get_recent_notes(self, limit: int = 10, include_archived: bool = False) -> List[Dict[str, Any]]:
        """
        获取最近更新的笔记
        
        Args:
            limit: 返回的笔记数量限制
            include_archived: 是否包含已归档的笔记
            
        Returns:
            List[Dict[str, Any]]: 最近更新的笔记列表
        """
        return self.store.get_recent_notes(limit, include_archived)
    
    def get_notes_by_tag(self, tag: str, include_archived: bool = False) -> List[Dict[str, Any]]:
        """
        获取指定标签的笔记
        
        Args:
            tag: 标签
            include_archived: 是否包含已归档的笔记
            
        Returns:
            List[Dict[str, Any]]: 笔记列表
        """
        return self.store.get_notes_by_tag(tag, include_archived)
    
    def get_all_tags(self) -> List[str]:
        """
        获取所有标签
        
        Returns:
            List[str]: 标签列表
        """
        return self.store.get_all_tags()
    
    def toggle_pin_current_note(self) -> bool:
        """
        切换当前笔记的置顶状态
        
        Returns:
            bool: 切换后的置顶状态
        """
        return self.editor.toggle_pin()
    
    def toggle_archive_current_note(self) -> bool:
        """
        切换当前笔记的归档状态
        
        Returns:
            bool: 切换后的归档状态
        """
        return self.editor.toggle_archive()
    
    def add_tag_to_current_note(self, tag: str) -> bool:
        """
        为当前笔记添加标签
        
        Args:
            tag: 标签
            
        Returns:
            bool: 是否成功添加
        """
        return self.editor.add_tag(tag)
    
    def remove_tag_from_current_note(self, tag: str) -> bool:
        """
        从当前笔记移除标签
        
        Args:
            tag: 标签
            
        Returns:
            bool: 是否成功移除
        """
        return self.editor.remove_tag(tag)
    
    def undo_current_note(self) -> bool:
        """
        撤销当前笔记的最后一次编辑
        
        Returns:
            bool: 是否成功撤销
        """
        return self.editor.undo()
    
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
    
    def export_notes(self, path: str, note_ids: List[str] = None) -> bool:
        """
        导出笔记
        
        Args:
            path: 导出路径
            note_ids: 要导出的笔记ID列表，为None则导出所有笔记
            
        Returns:
            bool: 是否成功导出
        """
        try:
            import json
            
            # 获取要导出的笔记
            if note_ids:
                notes = [self.store.get_note(note_id) for note_id in note_ids]
                notes = [note for note in notes if note]  # 过滤掉不存在的笔记
            else:
                notes = self.store.get_all_notes(include_archived=True)
            
            # 创建导出数据
            export_data = {
                'notes': notes,
                'export_time': datetime.now().isoformat(),
                'count': len(notes)
            }
            
            # 写入文件
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"已导出 {len(notes)} 条笔记到 {path}")
            return True
        except Exception as e:
            self.logger.error(f"导出笔记异常: {e}")
            self._trigger_callbacks('on_error', {
                'action': 'export_notes',
                'path': path,
                'message': str(e)
            })
            return False
    
    def import_notes(self, path: str) -> Tuple[int, int]:
        """
        导入笔记
        
        Args:
            path: 导入路径
            
        Returns:
            Tuple[int, int]: (成功导入数量, 总数量)
        """
        try:
            import json
            
            # 读取文件
            with open(path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            notes = import_data.get('notes', [])
            success_count = 0
            
            # 导入每个笔记
            for note in notes:
                # 移除ID，生成新ID
                if 'id' in note:
                    del note['id']
                
                # 创建笔记
                title = note.get('title', '导入的笔记')
                content = note.get('content', '')
                tags = note.get('tags', [])
                
                note_id = self.create_note(title, content, tags)
                
                if note_id:
                    # 更新其他字段
                    updates = {
                        'is_pinned': note.get('is_pinned', False),
                        'is_archived': note.get('is_archived', False)
                    }
                    self.store.update_note(note_id, updates)
                    success_count += 1
            
            self.logger.info(f"已导入 {success_count}/{len(notes)} 条笔记")
            return (success_count, len(notes))
        except Exception as e:
            self.logger.error(f"导入笔记异常: {e}")
            self._trigger_callbacks('on_error', {
                'action': 'import_notes',
                'path': path,
                'message': str(e)
            })
            return (0, 0) 