"""
---------------------------------------------------------------
File name:                  context_menu.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                桌宠上下文菜单管理模块
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
                            2025/04/05: 修复QAction导入路径;
----
"""

import logging
from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QAction
from PyQt6.QtCore import pyqtSignal, QObject
from status.core.events import EventManager
from status.interaction.interaction_event import InteractionEvent, InteractionEventType

# 配置日志
logger = logging.getLogger(__name__)


class ContextMenu(QObject):
    """上下文菜单类
    
    管理桌宠的右键上下文菜单，提供各种交互选项。
    """
    
    # 定义信号
    menu_shown_signal = pyqtSignal()
    menu_hidden_signal = pyqtSignal()
    menu_action_signal = pyqtSignal(str)
    
    def __init__(self):
        """初始化上下文菜单
        """
        super().__init__()
        self.event_manager = EventManager.get_instance()
        
        # 创建菜单
        self.menu = QMenu()
        
        # 设置菜单样式
        self.menu.setStyleSheet("""
            QMenu {
                background-color: #F5F5F5;
                border: 1px solid #C0C0C0;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 25px 5px 25px;
                border: 1px solid transparent;
            }
            QMenu::item:selected {
                background-color: #E0E0E0;
                border: 1px solid #C0C0C0;
            }
        """)
        
        # 菜单动作列表
        self.actions = {}
        
        # 设置菜单项
        self.setup_menu()
        
        # 连接菜单信号
        self.menu.aboutToShow.connect(self.on_menu_about_to_show)
        self.menu.aboutToHide.connect(self.on_menu_about_to_hide)
        
        logger.info("ContextMenu initialized")
    
    def setup_menu(self):
        """设置上下文菜单
        
        创建并配置上下文菜单的菜单项。
        """
        # 清空菜单
        self.menu.clear()
        self.actions.clear()
        
        # 添加与桌宠交互的菜单项
        self.add_menu_action("pet", "抚摸", self.on_pet_action)
        self.add_menu_action("feed", "喂食", self.on_feed_action)
        self.add_menu_action("play", "玩耍", self.on_play_action)
        
        # 添加分隔符
        self.menu.addSeparator()
        
        # 添加二级菜单 - 状态
        state_menu = self.menu.addMenu("状态")
        self.add_menu_action("state_normal", "普通", self.on_state_action, state_menu, "normal")
        self.add_menu_action("state_happy", "开心", self.on_state_action, state_menu, "happy")
        self.add_menu_action("state_sad", "难过", self.on_state_action, state_menu, "sad")
        self.add_menu_action("state_angry", "生气", self.on_state_action, state_menu, "angry")
        self.add_menu_action("state_sleepy", "困倦", self.on_state_action, state_menu, "sleepy")
        
        # 添加二级菜单 - 动作
        action_menu = self.menu.addMenu("动作")
        self.add_menu_action("action_sit", "坐下", self.on_action_action, action_menu, "sit")
        self.add_menu_action("action_run", "跑步", self.on_action_action, action_menu, "run")
        self.add_menu_action("action_jump", "跳跃", self.on_action_action, action_menu, "jump")
        self.add_menu_action("action_dance", "跳舞", self.on_action_action, action_menu, "dance")
        self.add_menu_action("action_sleep", "睡觉", self.on_action_action, action_menu, "sleep")
        
        # 添加分隔符
        self.menu.addSeparator()
        
        # 添加设置和关于菜单项
        self.add_menu_action("settings", "设置", self.on_settings_action)
        self.add_menu_action("about", "关于", self.on_about_action)
        
        logger.debug("Context menu set up")
    
    def add_menu_action(self, action_id, text, slot, parent_menu=None, data=None):
        """添加菜单动作
        
        Args:
            action_id (str): 动作ID
            text (str): 菜单项文本
            slot (function): 点击时的回调函数
            parent_menu (QMenu, optional): 父菜单. 默认为None，使用主菜单
            data (any, optional): 要传递给回调函数的数据. 默认为None
            
        Returns:
            QAction: 创建的菜单动作
        """
        action = QAction(text, self)
        
        # 如果有数据，设置为用户数据
        if data:
            action.setData(data)
        
        # 设置动作ID作为属性
        action.setObjectName(action_id)
        
        # 连接槽函数
        action.triggered.connect(lambda: slot(action))
        
        # 添加到菜单
        if parent_menu:
            parent_menu.addAction(action)
        else:
            self.menu.addAction(action)
        
        # 存储动作以便后续使用
        self.actions[action_id] = action
        
        return action
    
    def show_menu(self, x, y):
        """显示上下文菜单
        
        Args:
            x (int): 菜单显示的x坐标
            y (int): 菜单显示的y坐标
        """
        logger.debug(f"Showing context menu at ({x}, {y})")
        
        # 创建并发布菜单显示事件
        ev = InteractionEvent.create_menu_event(
            InteractionEventType.MENU_SHOW, "context_menu"
        )
        self.event_manager.post_event(ev)
        
        # 显示菜单
        self.menu.popup(x, y)
    
    def on_menu_about_to_show(self):
        """菜单即将显示的处理函数
        """
        logger.debug("Context menu about to show")
        self.menu_shown_signal.emit()
    
    def on_menu_about_to_hide(self):
        """菜单即将隐藏的处理函数
        """
        logger.debug("Context menu about to hide")
        
        # 创建并发布菜单隐藏事件
        ev = InteractionEvent.create_menu_event(
            InteractionEventType.MENU_HIDE, "context_menu"
        )
        self.event_manager.post_event(ev)
        
        self.menu_hidden_signal.emit()
    
    def on_pet_action(self, action):
        """处理"抚摸"菜单项点击事件
        
        Args:
            action: 触发的动作
        """
        logger.debug("Context menu: Pet action triggered")
        
        # 创建并发布菜单命令事件
        ev = InteractionEvent.create_menu_event(
            InteractionEventType.MENU_COMMAND, "context_menu", "pet"
        )
        self.event_manager.post_event(ev)
        
        self.menu_action_signal.emit("pet")
    
    def on_feed_action(self, action):
        """处理"喂食"菜单项点击事件
        
        Args:
            action: 触发的动作
        """
        logger.debug("Context menu: Feed action triggered")
        
        # 创建并发布菜单命令事件
        ev = InteractionEvent.create_menu_event(
            InteractionEventType.MENU_COMMAND, "context_menu", "feed"
        )
        self.event_manager.post_event(ev)
        
        self.menu_action_signal.emit("feed")
    
    def on_play_action(self, action):
        """处理"玩耍"菜单项点击事件
        
        Args:
            action: 触发的动作
        """
        logger.debug("Context menu: Play action triggered")
        
        # 创建并发布菜单命令事件
        ev = InteractionEvent.create_menu_event(
            InteractionEventType.MENU_COMMAND, "context_menu", "play"
        )
        self.event_manager.post_event(ev)
        
        self.menu_action_signal.emit("play")
    
    def on_state_action(self, action):
        """处理状态菜单项点击事件
        
        Args:
            action: 触发的动作
        """
        state = action.data()
        logger.debug(f"Context menu: State action triggered - {state}")
        
        # 创建并发布菜单命令事件
        ev = InteractionEvent.create_menu_event(
            InteractionEventType.MENU_COMMAND, "context_menu", f"state_{state}"
        )
        self.event_manager.post_event(ev)
        
        self.menu_action_signal.emit(f"state_{state}")
    
    def on_action_action(self, action):
        """处理动作菜单项点击事件
        
        Args:
            action: 触发的动作
        """
        action_type = action.data()
        logger.debug(f"Context menu: Action action triggered - {action_type}")
        
        # 创建并发布菜单命令事件
        ev = InteractionEvent.create_menu_event(
            InteractionEventType.MENU_COMMAND, "context_menu", f"action_{action_type}"
        )
        self.event_manager.post_event(ev)
        
        self.menu_action_signal.emit(f"action_{action_type}")
    
    def on_settings_action(self, action):
        """处理"设置"菜单项点击事件
        
        Args:
            action: 触发的动作
        """
        logger.debug("Context menu: Settings action triggered")
        
        # 创建并发布菜单命令事件
        ev = InteractionEvent.create_menu_event(
            InteractionEventType.MENU_COMMAND, "context_menu", "settings"
        )
        self.event_manager.post_event(ev)
        
        self.menu_action_signal.emit("settings")
    
    def on_about_action(self, action):
        """处理"关于"菜单项点击事件
        
        Args:
            action: 触发的动作
        """
        logger.debug("Context menu: About action triggered")
        
        # 创建并发布菜单命令事件
        ev = InteractionEvent.create_menu_event(
            InteractionEventType.MENU_COMMAND, "context_menu", "about"
        )
        self.event_manager.post_event(ev)
        
        self.menu_action_signal.emit("about")
    
    def enable_action(self, action_id, enabled=True):
        """启用或禁用菜单项
        
        Args:
            action_id (str): 动作ID
            enabled (bool, optional): 是否启用. 默认为True
            
        Returns:
            bool: 操作是否成功
        """
        if action_id in self.actions:
            self.actions[action_id].setEnabled(enabled)
            logger.debug(f"Action {action_id} {'enabled' if enabled else 'disabled'}")
            return True
        
        logger.warning(f"Action {action_id} not found")
        return False
    
    def handle_event(self, event):
        """处理交互事件
        
        这个方法用于处理从交互管理器传来的事件。
        
        Args:
            event: 要处理的事件
        """
        # 只处理与菜单相关的事件
        if hasattr(event, 'interaction_type') and event.source == "menu":
            logger.debug(f"ContextMenu handling event: {event}")
            # 此处可以根据需要添加对特定事件的处理
    
    def shutdown(self):
        """关闭上下文菜单
        
        清理资源。
        """
        logger.info("Shutting down ContextMenu")
        
        # 清空菜单
        if self.menu:
            self.menu.clear()
        
        # 清空动作字典
        self.actions.clear() 