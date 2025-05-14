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
from typing import Callable, Optional, Dict

# 将 logger 定义移到最前面
logger = logging.getLogger(__name__)

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox, QWidget
from PySide6.QtGui import QIcon, QAction, QActionGroup, QPixmap, QPainter, QColor, QBrush, QPen
from PySide6.QtCore import QPoint, Signal, QObject

# 移除 try-except，直接使用下面的函数定义
def get_resource_path(relative_path: str) -> str: # 添加类型提示
    base_path = os.path.dirname(__file__)
    # 路径调整：假设 resources 目录在项目根目录下
    # __file__ 是 status/ui/system_tray.py
    # os.path.dirname(__file__) 是 status/ui
    # os.path.join(base_path, '..', '..', 'resources', relative_path) -> status/ui/../../resources/relative_path -> resources/relative_path
    resource_path = os.path.abspath(os.path.join(base_path, '..', '..', 'resources', relative_path))
    logger.debug(f"get_resource_path for '{relative_path}': '{resource_path}'")
    return resource_path

class SystemTrayManager(QObject):
    """管理系统托盘图标和菜单"""
    
    toggle_stats_panel_visibility_requested = Signal(bool)
    
    def __init__(self, app: QApplication, parent: QObject | None = None):
        super().__init__(parent)
        self.app = app
        self.tray_icon = QSystemTrayIcon(parent=None) # 父对象设为 None 避免随父窗口关闭
        
        # 直接构建到 assets/placeholders/app_icon.png 的路径
        # __file__ 是 status/ui/system_tray.py
        base_dir = os.path.dirname(__file__)
        icon_path = os.path.abspath(os.path.join(base_dir, '..', '..', 'assets', 'placeholders', 'app_icon.png'))
        
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
            logger.info(f"成功加载托盘图标: {icon_path}")
        else:
            logger.warning(f"托盘图标文件未找到: {icon_path}，将创建默认图标")
            # 创建一个简单的默认图标
            pixmap = QPixmap(16, 16)
            pixmap.fill(QColor(0, 0, 0, 0))  # 透明背景
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # 绘制一个简单的圆形图标
            painter.setBrush(QBrush(QColor(90, 200, 190)))  # 填充颜色
            painter.setPen(QPen(QColor(60, 60, 60), 1))  # 边框颜色和宽度
            painter.drawEllipse(2, 2, 12, 12)  # 在 16x16 的图像上绘制一个 12x12 的圆
            
            # 添加一个简单的标识
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.drawLine(6, 8, 10, 8)  # 绘制一个简单的符号
            
            painter.end()
            
            # 设置自定义图标
            self.tray_icon.setIcon(QIcon(pixmap))
            logger.info("已创建并设置默认托盘图标")
            
        self.tray_icon.setToolTip("Status-Ming")
        
        self._callbacks: Dict[str, Optional[Callable]] = {} # 初始化回调字典
        # 初始化动作属性
        self.show_hide_action: Optional[QAction] = None
        self.drag_mode_actions: Dict[str, QAction] = {}
        self.toggle_interaction_action: Optional[QAction] = None
        self.toggle_stats_action: Optional[QAction] = None

        self.tray_icon.activated.connect(self.on_tray_activated) # 连接激活事件
        self.tray_icon.show()
        logger.info("系统托盘管理器初始化")

    def setup_menu(self, 
                   show_hide_callback: Optional[Callable] = None, 
                   exit_callback: Optional[Callable] = None,
                   drag_mode_callback: Optional[Callable[[str], None]] = None,
                   toggle_interaction_callback: Optional[Callable] = None):
        """设置托盘菜单项和回调"""
        self._callbacks = {
            'show_hide': show_hide_callback,
            'exit': exit_callback,
            'drag_mode': drag_mode_callback,
            'toggle_interaction': toggle_interaction_callback
        }
        
        menu = QMenu() # 创建菜单
        
        # 显示/隐藏 动作
        self.show_hide_action = QAction("显示桌宠", menu)
        show_hide_cb = self._callbacks.get('show_hide')
        if show_hide_cb:
            self.show_hide_action.triggered.connect(show_hide_cb)
        menu.addAction(self.show_hide_action)
        
        menu.addSeparator()

        # 拖动模式组
        drag_mode_group = QActionGroup(menu) # 父对象为 menu
        drag_mode_group.setExclusive(True)
        modes = [("智能模式", "smart"), ("精确模式", "precise"), ("平滑模式", "smooth")]
        self.drag_mode_actions = {}
        drag_mode_submenu = QMenu("拖动模式", menu) # 创建子菜单
        drag_mode_cb = self._callbacks.get('drag_mode')
        for text, mode_id in modes:
            action = QAction(text, drag_mode_submenu)
            action.setCheckable(True)
            # 安全调用回调
            if drag_mode_cb:
                action.triggered.connect(lambda checked, m=mode_id, cb=drag_mode_cb: cb(m) if checked else None)
            drag_mode_group.addAction(action)
            drag_mode_submenu.addAction(action) # 添加到子菜单
            self.drag_mode_actions[mode_id] = action
            if mode_id == "smart": # 默认选中智能模式
                action.setChecked(True)
        menu.addMenu(drag_mode_submenu) # 添加子菜单到主菜单
        
        menu.addSeparator()
        
        # 鼠标交互切换
        self.toggle_interaction_action = QAction("启用交互 (可拖动)", menu)
        self.toggle_interaction_action.setCheckable(True)
        self.toggle_interaction_action.setChecked(True) # 默认可交互
        toggle_interaction_cb = self._callbacks.get('toggle_interaction')
        if toggle_interaction_cb:
            self.toggle_interaction_action.triggered.connect(toggle_interaction_cb)
        menu.addAction(self.toggle_interaction_action)
        
        # 统计面板切换
        menu.addSeparator()
        self.toggle_stats_action = QAction("显示统计面板", menu)
        self.toggle_stats_action.setCheckable(True)
        self.toggle_stats_action.setChecked(False) # 初始隐藏
        self.toggle_stats_action.triggered.connect(self.on_toggle_stats_panel)
        menu.addAction(self.toggle_stats_action)

        menu.addSeparator()

        # 退出动作
        exit_action = QAction("退出", menu)
        exit_cb = self._callbacks.get('exit')
        if exit_cb:
            exit_action.triggered.connect(exit_cb)
        menu.addAction(exit_action)

        self.tray_icon.setContextMenu(menu)
        logger.debug("系统托盘菜单设置完成")
        
    def set_window_visibility(self, is_visible: bool):
        if self.show_hide_action:
            self.show_hide_action.setText("隐藏桌宠" if is_visible else "显示桌宠")
        
    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            show_hide_cb = self._callbacks.get('show_hide')
            if show_hide_cb:
                show_hide_cb()
            else:
                logger.warning("托盘左键单击，但未设置 show_hide_callback")
    
    def set_interaction_state(self, is_interactive: bool):
        if self.toggle_interaction_action:
            self.toggle_interaction_action.setChecked(is_interactive)
            self.toggle_interaction_action.setText("禁用交互 (鼠标穿透)" if is_interactive else "启用交互 (可拖动)")

    def set_drag_mode_action(self, mode: str):
        if mode in self.drag_mode_actions:
            self.drag_mode_actions[mode].setChecked(True)
        else:
            logger.warning(f"尝试设置未知的拖动模式动作: {mode}")
            
    def on_toggle_stats_panel(self):
        if self.toggle_stats_action:
            show = self.toggle_stats_action.isChecked()
            self.toggle_stats_panel_visibility_requested.emit(show)
            self.toggle_stats_action.setText("隐藏统计面板" if show else "显示统计面板")
            logger.debug(f"请求切换统计面板可见性: {show}")
        else:
            logger.error("on_toggle_stats_panel called but toggle_stats_action does not exist")
        
    def show_message(self, title: str, message: str, 
                     icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information, 
                     timeout: int = 3000):
        self.tray_icon.showMessage(title, message, icon, timeout) 