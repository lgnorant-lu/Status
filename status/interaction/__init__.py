"""
---------------------------------------------------------------
File name:                  __init__.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                交互系统初始化文件，提供用户交互相关功能
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
                            2025/04/05: 添加命令系统类;
----
"""

# 交互管理类
from status.interaction.interaction_manager import InteractionManager
from status.interaction.mouse_interaction import MouseInteraction
from status.interaction.trayicon import TrayIcon
from status.interaction.context_menu import ContextMenu
from status.interaction.hotkey_manager import HotkeyManager
from status.interaction.behavior_trigger import BehaviorTrigger
from status.interaction.drag_manager import DragManager
from status.interaction.interaction_event import InteractionEvent, InteractionEventType

# 命令系统类
from status.interaction.command.command_types import (
    Command, 
    CommandType, 
    CommandStatus, 
    CommandContext,
    CommandRegistry
)
from status.interaction.command.command_parser import CommandParser
from status.interaction.command.command_manager import CommandManager

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
    'Command',
    'CommandType',
    'CommandStatus',
    'CommandContext',
    'CommandRegistry',
    'CommandParser',
    'CommandManager'
]
