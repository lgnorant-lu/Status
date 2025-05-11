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
                            2025/05/12: 修正导入路径和不存在的模块;
----
"""

# 交互管理类
from status.interaction.interaction_manager import InteractionManager
from status.interaction.mouse_interaction import MouseInteraction
from status.interaction.tray_icon import TrayIcon
from status.interaction.context_menu import ContextMenu
from status.interaction.hotkey import HotkeyManager
from status.interaction.behavior_trigger import BehaviorTrigger
from status.interaction.drag_manager import DragManager
from status.interaction.interaction_event import InteractionEvent, InteractionEventType

# 命令系统类 (Commented out as a_s_command directory does not exist)
# from status.interaction.a_s_command.command_types import (
#     Command, 
#     CommandType, 
#     CommandStatus, 
#     CommandContext,
#     CommandRegistry
# )
# from status.interaction.a_s_command.command_parser import CommandParser
# from status.interaction.a_s_command.command_manager import CommandManager

# 根据操作系统选择性导入
import platform
if platform.system() == "Windows":
    from status.interaction.hotkey_win import WindowsHotkeyHandler
    # 可以将 WindowsHotkeyHandler 赋值给通用的 HotkeyManager 名称，如果它是默认实现
    # HotkeyManager = WindowsHotkeyHandler 
    # 或者在 InteractionManager 中根据平台选择性实例化
# elif platform.system() == "Linux":
#     from .hotkey_linux import HotkeyManagerLinux
# elif platform.system() == "Darwin": # macOS
#     from .hotkey_mac import HotkeyManagerMac

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
    # 'Command',
    # 'CommandType',
    # 'CommandStatus',
    # 'CommandContext',
    # 'CommandRegistry',
    # 'CommandParser',
    # 'CommandManager'
]

# Conditionally add platform-specific handlers to __all__ if needed
if platform.system() == "Windows":
    if 'WindowsHotkeyHandler' not in __all__:
        __all__.append('WindowsHotkeyHandler')
