"""
---------------------------------------------------------------
File name:                  __init__.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                桌宠交互系统模块初始化文件
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

# 导出主要类

from status.interaction.interaction_manager import InteractionManager
from status.interaction.mouse_interaction import MouseInteraction
from status.interaction.tray_icon import TrayIcon
from status.interaction.context_menu import ContextMenu
from status.interaction.hotkey import HotkeyManager
from status.interaction.behavior_trigger import BehaviorTrigger
from status.interaction.drag_manager import DragManager
from status.interaction.interaction_event import InteractionEvent, InteractionEventType

__all__ = [
    'InteractionManager',
    'MouseInteraction',
    'TrayIcon',
    'ContextMenu',
    'HotkeyManager',
    'BehaviorTrigger',
    'DragManager',
    'InteractionEvent',
    'InteractionEventType',
]
