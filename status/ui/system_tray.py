"""
---------------------------------------------------------------
File name:                  system_tray.py
Author:                     Ignorant-lu
Date created:               2025/04/16
Description:                系统托盘组件，为应用提供系统托盘功能
----------------------------------------------------------------

Changed history:            
                            2025/04/16: 初始创建;
                            2025/05/20: 添加拖动模式选项;
----
"""

import logging
import os
from typing import Callable, Optional

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction, QActionGroup
from PySide6.QtCore import QPoint, Signal

logger = logging.getLogger(__name__)

class SystemTrayManager:
    """系统托盘管理器，负责系统托盘的创建和管理"""
    
    def __init__(self, app: QApplication, icon_path: Optional[str] = None):
        """初始化系统托盘管理器
        
        Args:
            app: QApplication实例
            icon_path: 系统托盘图标路径
        """
        self.app = app
        
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon()
        
        # 设置图标
        if icon_path and os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
            logger.info(f"使用指定图标创建系统托盘: {icon_path}")
        else:
            # 创建一个临时图标文件
            temp_icon_path = self._create_temp_icon()
            if temp_icon_path:
                self.tray_icon.setIcon(QIcon(temp_icon_path))
                logger.info(f"系统托盘已使用临时图标创建: {temp_icon_path}")
            else:
                logger.warning("无法创建系统托盘图标，将使用默认图标")
        
        # 创建托盘菜单
        self.tray_menu = QMenu()
        
        # 常见操作回调
        self.on_show_hide = None
        self.on_exit = None
        self.on_drag_mode_changed = None
        
        # 菜单项
        self.action_show_hide = None
        self.action_exit = None
        self.window_is_visible = True
        
        # 拖动模式菜单项
        self.drag_mode_menu = None
        self.drag_mode_actions = {}
        
        # 显示系统托盘
        self.tray_icon.show()
        
        logger.debug("系统托盘管理器初始化完成")
    
    def _create_temp_icon(self) -> Optional[str]:
        """创建一个临时图标文件
        
        Returns:
            str: 临时图标文件路径
        """
        try:
            from PySide6.QtGui import QPixmap, QPainter, QColor
            from PySide6.QtCore import Qt, QSize
            
            # 创建一个简单的图标
            size = 32
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # 绘制一个简单的图形作为临时图标
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(60, 150, 255))
            painter.drawEllipse(4, 4, 24, 24)
            
            # 绘制猫咪耳朵
            painter.setBrush(QColor(40, 120, 220))
            painter.drawPolygon([
                QPoint(8, 8),
                QPoint(14, 14),
                QPoint(8, 14)
            ])
            painter.drawPolygon([
                QPoint(24, 8),
                QPoint(18, 14),
                QPoint(24, 14)
            ])
            
            painter.end()
            
            # 保存到临时文件
            temp_path = "status/temp_icon.png"
            pixmap.save(temp_path)
            
            return temp_path
        
        except Exception as e:
            logger.error(f"创建临时图标失败: {str(e)}")
            return None
    
    def setup_menu(
        self,
        show_hide_callback: Callable[[], None],
        exit_callback: Callable[[], None],
        drag_mode_callback: Callable[[str], None],
        toggle_interaction_callback: Callable[[], None]
    ) -> None:
        """设置系统托盘菜单

        Args:
            show_hide_callback: 当"显示/隐藏"菜单项被点击时调用的函数
            exit_callback: 当"退出"菜单项被点击时调用的函数
            drag_mode_callback: 当拖动模式子菜单项被点击时调用的函数，参数为模式字符串
            toggle_interaction_callback: 当"切换交互"菜单项被点击时调用的函数
        """
        # 保存回调
        self.on_show_hide = show_hide_callback
        self.on_exit = exit_callback
        self.on_drag_mode_changed = drag_mode_callback
        
        # 清空菜单
        self.tray_menu.clear()
        
        # 添加显示/隐藏菜单项
        self.action_show_hide = QAction("隐藏", self.tray_menu)
        self.action_show_hide.triggered.connect(show_hide_callback)
        self.tray_menu.addAction(self.action_show_hide)
        
        # 添加切换交互菜单项
        self.toggle_interaction_action = QAction("允许鼠标穿透", self.tray_menu)
        self.toggle_interaction_action.setCheckable(True)
        self.toggle_interaction_action.setChecked(False)
        self.toggle_interaction_action.triggered.connect(toggle_interaction_callback)
        self.toggle_interaction_action.triggered.connect(self._update_toggle_interaction_text)
        self.tray_menu.addAction(self.toggle_interaction_action)
        self._update_toggle_interaction_text()
        
        # 添加分隔线
        self.tray_menu.addSeparator()
        
        # 创建拖动模式子菜单
        self.drag_mode_menu = QMenu("拖动模式", self.tray_menu)
        
        # 创建动作组以实现单选效果
        drag_mode_group = QActionGroup(self.tray_menu)
        
        # 创建三种拖动模式选项
        modes = [
            ("智能模式", "smart", "根据拖动速度自动调整平滑度"),
            ("精确模式", "precise", "精确跟随鼠标位置"),
            ("平滑模式", "smooth", "最大程度平滑拖动效果")
        ]
        
        for name, mode, tooltip in modes:
            action = QAction(name, self.drag_mode_menu)
            action.setToolTip(tooltip)
            action.setCheckable(True)
            action.setData(mode)
            
            # 默认选中智能模式
            if mode == "smart":
                action.setChecked(True)
            
            action.triggered.connect(
                lambda checked, m=mode: self._on_drag_mode_triggered(m)
            )
            
            # 添加到动作组以实现单选
            drag_mode_group.addAction(action)
            self.drag_mode_menu.addAction(action)
            self.drag_mode_actions[mode] = action
        
        # 添加拖动模式子菜单到主菜单
        self.tray_menu.addMenu(self.drag_mode_menu)
        
        # 添加分隔线
        self.tray_menu.addSeparator()
        
        # 添加退出菜单项
        self.action_exit = QAction("退出", self.tray_menu)
        self.action_exit.triggered.connect(exit_callback)
        self.tray_menu.addAction(self.action_exit)
        
        # 设置托盘菜单
        self.tray_icon.setContextMenu(self.tray_menu)
        
        logger.debug("系统托盘菜单设置完成")
    
    def _update_toggle_interaction_text(self):
        """根据当前选中状态更新'切换交互'菜单项的文本"""
        if self.toggle_interaction_action.isChecked():
            self.toggle_interaction_action.setText("禁止鼠标穿透 (可交互)")
        else:
            self.toggle_interaction_action.setText("允许鼠标穿透 (不可交互)")
    
    def set_window_visibility(self, visible: bool) -> None:
        """设置窗口可见性状态，用于更新菜单项文本
        
        Args:
            visible: 窗口是否可见
        """
        self.window_is_visible = visible
        if self.action_show_hide:
            self.action_show_hide.setText("隐藏" if visible else "显示")
    
    def set_current_drag_mode(self, mode: str) -> None:
        """设置当前选中的拖动模式
        
        Args:
            mode: 拖动模式 - "smart", "precise", "smooth"
        """
        if mode in self.drag_mode_actions:
            self.drag_mode_actions[mode].setChecked(True)
    
    def _on_show_hide_triggered(self) -> None:
        """显示/隐藏菜单项被触发"""
        if self.on_show_hide:
            self.on_show_hide()
            logger.info(f"用户通过托盘菜单请求{'隐藏' if self.window_is_visible else '显示'}窗口")
    
    def _on_exit_triggered(self) -> None:
        """退出菜单项被触发"""
        if self.on_exit:
            self.on_exit()
            logger.info("用户通过托盘菜单请求退出应用")
    
    def _on_drag_mode_triggered(self, mode: str) -> None:
        """拖动模式菜单项被触发
        
        Args:
            mode: 选择的拖动模式
        """
        if self.on_drag_mode_changed:
            self.on_drag_mode_changed(mode)
            logger.info(f"用户将拖动模式切换为: {mode}")
    
    def show_message(self, title: str, message: str) -> None:
        """显示托盘消息
        
        Args:
            title: 消息标题
            message: 消息内容
        """
        self.tray_icon.showMessage(
            title, 
            message, 
            QSystemTrayIcon.MessageIcon.Information, 
            5000  # 显示5秒
        ) 