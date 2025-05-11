"""
---------------------------------------------------------------
File name:                  __init__.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                笔记模块，提供简易笔记创建和管理功能
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

from .note_store import NoteStore
from .note_editor import NoteEditor
from .note_manager import NoteManager
from .factory import create_note_system, create_minimal_note_system, create_custom_note_system

# 导出的API
__all__ = [
    # 笔记存储器
    'NoteStore',
    
    # 笔记编辑器
    'NoteEditor',
    
    # 笔记管理器
    'NoteManager',
    
    # 工厂函数
    'create_note_system',
    'create_minimal_note_system',
    'create_custom_note_system'
] 