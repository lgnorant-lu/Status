"""
---------------------------------------------------------------
File name:                  factory.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                笔记系统工厂，提供创建笔记系统的便捷方法
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""
import logging
from typing import Dict, Any, Optional

from .note_manager import NoteManager
from .note_store import NoteStore
from .note_editor import NoteEditor

logger = logging.getLogger("NoteFactory")

def create_note_system(config: Dict[str, Any] = None) -> NoteManager:
    """
    创建标准笔记系统
    
    Args:
        config: 配置信息
        
    Returns:
        NoteManager: 笔记管理器实例
    """
    config = config or {}
    logger.info("创建标准笔记系统")
    
    # 创建存储器
    logger.info("创建笔记存储器")
    store = NoteStore(config.get('store_config', {}))
    
    # 创建编辑器
    logger.info("创建笔记编辑器")
    editor = NoteEditor(config.get('editor_config', {}))
    
    # 创建管理器
    logger.info("创建笔记管理器")
    manager = NoteManager(config, store, editor)
    
    logger.info("笔记系统创建完成")
    return manager

def create_minimal_note_system() -> NoteManager:
    """
    创建最小化笔记系统
    
    Returns:
        NoteManager: 笔记管理器实例
    """
    logger.info("创建最小化笔记系统")
    config = {
        'store_config': {
            'storage_path': 'data/minimal_notes.json'
        },
        'editor_config': {
            'history_enabled': False,
            'auto_save_enabled': False,
            'auto_tags_enabled': False
        }
    }
    
    return create_note_system(config)

def create_custom_note_system(store_path: Optional[str] = None,
                             history_size: int = 20,
                             auto_save_interval: int = 30,
                             auto_tags_enabled: bool = True) -> NoteManager:
    """
    创建自定义笔记系统
    
    Args:
        store_path: 存储路径
        history_size: 历史记录大小
        auto_save_interval: 自动保存间隔（秒）
        auto_tags_enabled: 是否启用自动标签
        
    Returns:
        NoteManager: 笔记管理器实例
    """
    logger.info("创建自定义笔记系统")
    
    config = {
        'store_config': {
            'storage_path': store_path or 'data/notes.json'
        },
        'editor_config': {
            'history_enabled': True,
            'max_history_steps': history_size,
            'auto_save_enabled': True,
            'auto_save_interval': auto_save_interval,
            'auto_tags_enabled': auto_tags_enabled
        }
    }
    
    return create_note_system(config) 