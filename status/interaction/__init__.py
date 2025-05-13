"""
---------------------------------------------------------------
File name:                  __init__.py
Author:                     Ignorant-lu
Date created:               2023/02/10
Description:                interaction package initialization
----------------------------------------------------------------

Changed history:            
                            2023/02/10: 初始创建;
                            2023/02/14: 添加基础交互组件;
                            2025/05/13: 添加交互区域和交互跟踪相关类;
----
"""

from status.interaction.drag_manager import DragManager
from status.interaction.event_filter import EventFilter
from status.interaction.hotkey import HotkeyManager
from status.interaction.tray_icon import TrayIcon
from status.interaction.context_menu import ContextMenu
from status.interaction.interaction_area import InteractionArea, InteractionAreaManager, InteractionType
from status.interaction.interaction_tracker import InteractionTracker, InteractionRecord
from status.interaction.interaction_handler import InteractionHandler

__all__ = [
    "DragManager",
    "EventFilter",
    "HotkeyManager",
    "TrayIcon",
    "ContextMenu",
    "InteractionArea",
    "InteractionAreaManager",
    "InteractionType",
    "InteractionTracker",
    "InteractionRecord",
    "InteractionHandler",
]
