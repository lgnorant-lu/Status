"""
---------------------------------------------------------------
File name:                  tray_icon.py
Author:                     Ignorant-lu
Date created:               2025/04/04  
Description:                系统托盘图标管理
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
                            2025/04/04: 添加菜单项管理功能;
                            2025/04/17: 从PyQt6迁移到PySide6;
----
"""

import logging
import os
from typing import Dict, Any, Optional, Callable, Union

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QSystemTrayIcon, QMenu

from status.core.events import InteractionEvent, InteractionEventType, EventManager

# 设置日志记录
logger = logging.getLogger(__name__)

class TrayIcon(QObject):
    """系统托盘图标类
    
    管理桌宠应用的系统托盘图标和菜单。
    """
    
    # 定义信号
    tray_activated_signal = Signal(str)
    menu_action_signal = Signal(str)

    def __init__(self, app, icon_path=None):
        """初始化系统托盘图标
        
        Args:
            app: 应用程序实例，用于退出应用
            icon_path (str, optional): 图标文件路径. 默认为None
        """
        super().__init__()
        
        # 保存应用程序实例
        self.app = app
        
        # 实例化事件管理器
        self.event_manager = EventManager.get_instance()
        
        # 创建托盘图标和菜单
        self.tray_icon = None
        self.menu = None
        self.menu_actions = {}
        
        # 初始化托盘图标
        self.setup_icon(icon_path)
        
        # 初始化菜单
        self.setup_menu()
        
        # 显示托盘图标
        if self.tray_icon:
            self.tray_icon.show()
            logger.info("TrayIcon initialized")
        else:
            logger.error("Failed to initialize TrayIcon: tray_icon is None")
    
    def setup_icon(self, icon_path=None):
        """设置托盘图标
        
        Args:
            icon_path (str, optional): 图标文件路径. 默认为None，使用默认图标
            
        Returns:
            bool: 设置是否成功
        """
        try:
            # 创建系统托盘图标
            if self.tray_icon is None:
                self.tray_icon = QSystemTrayIcon()
                
            # 选择图标
            if icon_path and os.path.exists(icon_path):
                icon = QIcon(icon_path)
            else:
                # 使用默认图标
                icon = QIcon.fromTheme("user-desktop")
                if icon.isNull():
                    # 如果系统主题没有图标，尝试使用PySide自带的图标
                    icon = QIcon()  # 使用一个空图标作为后备选项
            
            if self.tray_icon:
                self.tray_icon.setIcon(icon)
                self.tray_icon.setToolTip("Status Pet 桌宠应用")
                
                # 连接托盘激活信号
                self.tray_icon.activated.connect(self.on_tray_activated)
                
                logger.debug(f"Tray icon set to {icon_path if icon_path else 'default'}")
                return True
            else:
                logger.error("Failed to set tray icon: tray_icon is None")
                return False
            
        except Exception as e:
            logger.error(f"Failed to set tray icon: {str(e)}")
            return False
    
    def setup_menu(self):
        """设置托盘图标菜单
        
        创建并配置托盘图标的上下文菜单。
        """
        # 创建菜单（如果尚未创建）
        if self.menu is None:
            self.menu = QMenu()
            
        # 确保有可用的托盘图标
        if self.tray_icon is None:
            self.setup_icon()
            
        # 清空菜单
        if self.menu:
            self.menu.clear()
            
            # 添加菜单项
            self.add_menu_action("show", "显示", self.on_show_action)
            self.add_menu_action("hide", "隐藏", self.on_hide_action)
            self.add_menu_action("settings", "设置", self.on_settings_action)
            
            # 添加分隔符
            self.menu.addSeparator()
            
            # 添加二级菜单
            mode_menu = self.menu.addMenu("模式")
            self.add_menu_action("mode_normal", "普通", self.on_mode_action, mode_menu, "normal")
            self.add_menu_action("mode_sleep", "睡眠", self.on_mode_action, mode_menu, "sleep")
            self.add_menu_action("mode_active", "活跃", self.on_mode_action, mode_menu, "active")
            
            # 添加分隔符
            self.menu.addSeparator()
            
            # 添加退出菜单项
            self.add_menu_action("exit", "退出", self.on_exit_action)
            
            # 设置托盘图标菜单
            if self.tray_icon:
                self.tray_icon.setContextMenu(self.menu)
            
            logger.debug("Tray menu set up")
        else:
            logger.error("Failed to set up tray menu: menu is None")
    
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
        elif self.menu:
            self.menu.addAction(action)
        
        return action
    
    def on_tray_activated(self, reason):
        """处理托盘图标激活事件
        
        Args:
            reason (QSystemTrayIcon.ActivationReason): 激活原因
        """
        reason_str = "unknown"
        
        # 映射激活原因到字符串
        # 在PySide6中，QSystemTrayIcon.ActivationReason是整数常量
        if reason == QSystemTrayIcon.Trigger:  # 单击
            reason_str = "click"
        elif reason == QSystemTrayIcon.DoubleClick:  # 双击
            reason_str = "double_click"
        elif reason == QSystemTrayIcon.MiddleClick:  # 中键单击
            reason_str = "middle_click"
        elif reason == QSystemTrayIcon.Context:  # 右键单击
            reason_str = "context"
        
        logger.debug(f"Tray icon activated: {reason_str}")
        self.tray_activated_signal.emit(reason_str)
        
        # 创建并发布事件
        if self.event_manager:
            ev = InteractionEvent.create_tray_event(
                InteractionEventType.TRAY_ICON_ACTIVATED, reason_str
            )
            self.event_manager.post_event(ev)
        
        # 如果是左键单击或双击，显示窗口
        if reason in [QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick]:
            self.on_show_action(None)
    
    def on_show_action(self, action):
        """处理"显示"菜单项点击事件
        
        Args:
            action: 触发的动作
        """
        logger.debug("Tray menu: Show action triggered")
        
        # 创建并发布事件
        if self.event_manager:
            ev = InteractionEvent.create_tray_event(
                InteractionEventType.TRAY_MENU_COMMAND, action_id="show"
            )
            self.event_manager.post_event(ev)
        self.menu_action_signal.emit("show")
    
    def on_hide_action(self, action):
        """处理"隐藏"菜单项点击事件
        
        Args:
            action: 触发的动作
        """
        logger.debug("Tray menu: Hide action triggered")
        
        # 创建并发布事件
        if self.event_manager:
            ev = InteractionEvent.create_tray_event(
                InteractionEventType.TRAY_MENU_COMMAND, action_id="hide"
            )
            self.event_manager.post_event(ev)
        self.menu_action_signal.emit("hide")
    
    def on_settings_action(self, action):
        """处理"设置"菜单项点击事件
        
        Args:
            action: 触发的动作
        """
        logger.debug("Tray menu: Settings action triggered")
        
        # 创建并发布事件
        if self.event_manager:
            ev = InteractionEvent.create_tray_event(
                InteractionEventType.TRAY_MENU_COMMAND, action_id="settings"
            )
            self.event_manager.post_event(ev)
        self.menu_action_signal.emit("settings")
    
    def on_mode_action(self, action):
        """处理"模式"菜单项点击事件
        
        Args:
            action: 触发的动作
        """
        # 获取选择的模式
        mode = action.data()
        logger.debug(f"Tray menu: Mode action triggered - {mode}")
        
        # 创建并发布事件
        if self.event_manager:
            ev = InteractionEvent.create_tray_event(
                InteractionEventType.TRAY_MENU_COMMAND, 
                action_id="mode", 
                data={"mode": mode}
            )
            self.event_manager.post_event(ev)
        self.menu_action_signal.emit(f"mode:{mode}")
    
    def on_exit_action(self, action):
        """处理"退出"菜单项点击事件
        
        Args:
            action: 触发的动作
        """
        logger.debug("Tray menu: Exit action triggered")
        
        # 创建并发布事件
        if self.event_manager:
            ev = InteractionEvent.create_tray_event(
                InteractionEventType.TRAY_MENU_COMMAND, action_id="exit"
            )
            self.event_manager.post_event(ev)
        self.menu_action_signal.emit("exit")
        
        # 关闭托盘图标
        self.shutdown()
        
        # 退出应用
        if self.app:
            self.app.quit()
    
    def show_message(self, title, message, icon=None, duration=5000):
        """显示托盘气泡消息
        
        Args:
            title (str): 消息标题
            message (str): 消息内容
            icon (QSystemTrayIcon.MessageIcon, optional): 消息图标. 默认为None
            duration (int, optional): 显示时长（毫秒）. 默认为5000
        """
        if not self.tray_icon:
            logger.error("Cannot show message: tray_icon is None")
            return
            
        if icon is None:
            icon = QSystemTrayIcon.Information
            
        self.tray_icon.showMessage(title, message, icon, duration)
        logger.debug(f"Tray message displayed: {title}")
    
    def handle_event(self, event):
        """处理事件
        
        Args:
            event: 事件对象
        """
        # 根据事件类型处理
        if event.type == InteractionEventType.TRAY_MESSAGE:
            # 显示托盘气泡消息
            title = event.data.get("title", "")
            message = event.data.get("message", "")
            icon = event.data.get("icon", QSystemTrayIcon.Information)
            duration = event.data.get("duration", 5000)
            
            self.show_message(title, message, icon, duration)
    
    def shutdown(self):
        """关闭托盘图标"""
        if self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon = None
        
        logger.info("TrayIcon shutdown") 