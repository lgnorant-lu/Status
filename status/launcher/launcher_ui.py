"""
---------------------------------------------------------------
File name:                  launcher_ui.py
Author:                     Ignorant-lu
Date created:               2023/11/28
Description:                快速启动器UI界面
----------------------------------------------------------------

Changed history:            
                            2023/11/28: 初始创建;
                            2023/11/29: 添加导入/导出功能与启动参数设置支持;
----
"""

import logging
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any, Set, Tuple

from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal, QObject, QEvent, QPoint
from PyQt6.QtGui import QIcon, QPixmap, QFont, QKeyEvent, QAction, QCursor
from PyQt6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea, QFrame,
    QApplication, QMenu, QSizePolicy, QToolButton, QGroupBox,
    QTabWidget, QListWidget, QListWidgetItem, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog, QInputDialog,
    QComboBox, QCheckBox, QSpinBox
)

from status.launcher.launcher_manager import LauncherManager
from status.launcher.launcher_types import LaunchedApplication, LauncherGroup, LaunchResult, LaunchMode

# 获取日志记录器
logger = logging.getLogger(__name__)


class LauncherUI(QDialog):
    """快捷启动器UI界面"""
    
    def __init__(self, launcher_manager=None, parent=None):
        """初始化启动器UI
        
        Args:
            launcher_manager: 启动器管理器实例
            parent: 父窗口
        """
        super().__init__(parent)
        
        # 启动器管理器
        if launcher_manager is None:
            self.launcher_manager = LauncherManager.get_instance()
        else:
            self.launcher_manager = launcher_manager
        
        # UI组件
        self.search_box = None
        self.app_grid = None
        self.group_buttons = {}  # 分组按钮 {group_id: button}
        self.app_widgets = {}  # 应用程序部件 {app_id: widget}
        self.current_group_id = None  # 当前选中的分组ID
        
        # 设置窗口属性
        self.setWindowTitle("快捷启动器")
        self.setMinimumSize(600, 400)
        
        # 初始化UI
        self._initialize_ui()
        
        # 连接事件
        self._connect_events()
        
        # 初始显示"全部"分组
        self._show_all_applications()
        
        # 设置窗口位置为屏幕中央
        self._center_on_screen()
        
        logger.debug("LauncherUI已初始化")
    
    def _initialize_ui(self):
        """初始化UI组件"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 顶部按钮区域
        top_button_layout = QHBoxLayout()
        
        # 设置按钮
        self.settings_button = QPushButton("设置")
        self.settings_button.setFixedWidth(80)
        self.settings_button.clicked.connect(self._show_settings)
        
        # 导入/导出按钮
        self.import_export_button = QPushButton("导入/导出")
        self.import_export_button.setFixedWidth(80)
        self.import_export_button.clicked.connect(self._show_import_export_menu)
        
        # 添加按钮
        self.add_app_button = QPushButton("添加应用")
        self.add_app_button.setFixedWidth(80)
        self.add_app_button.clicked.connect(self._add_application)
        
        # 添加到布局
        top_button_layout.addWidget(self.settings_button)
        top_button_layout.addWidget(self.import_export_button)
        top_button_layout.addWidget(self.add_app_button)
        top_button_layout.addStretch()
        
        main_layout.addLayout(top_button_layout)
        
        # 顶部搜索区域
        search_layout = QHBoxLayout()
        
        # 搜索框
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索应用...")
        self.search_box.setClearButtonEnabled(True)
        search_layout.addWidget(self.search_box)
        
        # 搜索按钮
        search_button = QPushButton("搜索")
        search_layout.addWidget(search_button)
        
        main_layout.addLayout(search_layout)
        
        # 分组区域
        group_scroll = QScrollArea()
        group_scroll.setWidgetResizable(True)
        group_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        group_scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        group_widget = QWidget()
        group_layout = QHBoxLayout(group_widget)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(5)
        
        # 添加"全部"分组按钮
        all_button = QPushButton("全部")
        all_button.setCheckable(True)
        all_button.setChecked(True)
        all_button.clicked.connect(self._show_all_applications)
        group_layout.addWidget(all_button)
        
        # 添加"收藏"分组按钮
        if self.launcher_manager.config["favorite_group_id"]:
            favorite_group_id = self.launcher_manager.config["favorite_group_id"]
            favorite_group = self.launcher_manager.get_group(favorite_group_id)
            if favorite_group:
                favorite_button = QPushButton(favorite_group.name)
                favorite_button.setCheckable(True)
                favorite_button.clicked.connect(
                    lambda checked, gid=favorite_group_id: self._show_group(gid)
                )
                group_layout.addWidget(favorite_button)
                self.group_buttons[favorite_group_id] = favorite_button
        
        # 添加其他分组按钮
        for group in self.launcher_manager.get_all_groups():
            # 跳过收藏分组，因为已经单独添加了
            if group.id == self.launcher_manager.config["favorite_group_id"]:
                continue
                
            group_button = QPushButton(group.name)
            group_button.setCheckable(True)
            group_button.clicked.connect(
                lambda checked, gid=group.id: self._show_group(gid)
            )
            group_layout.addWidget(group_button)
            self.group_buttons[group.id] = group_button
        
        # 添加"最近使用"按钮
        recent_button = QPushButton("最近使用")
        recent_button.setCheckable(True)
        recent_button.clicked.connect(self._show_recent_applications)
        group_layout.addWidget(recent_button)
        
        # 分组布局添加弹性空间
        group_layout.addStretch(1)
        
        group_scroll.setWidget(group_widget)
        main_layout.addWidget(group_scroll)
        
        # 应用程序网格区域
        app_scroll = QScrollArea()
        app_scroll.setWidgetResizable(True)
        app_scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        app_container = QWidget()
        self.app_grid = QGridLayout(app_container)
        self.app_grid.setContentsMargins(5, 5, 5, 5)
        self.app_grid.setSpacing(10)
        self.app_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        app_scroll.setWidget(app_container)
        main_layout.addWidget(app_scroll, 1)
        
        # 底部按钮区域
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        
        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        main_layout.addLayout(button_layout)
    
    def _connect_events(self):
        """连接事件信号和槽"""
        # 搜索框回车事件
        self.search_box.returnPressed.connect(self._search_applications)
    
    def _center_on_screen(self):
        """将窗口居中显示在屏幕上"""
        screen_geometry = QApplication.primaryScreen().geometry()
        window_geometry = self.frameGeometry()
        
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        
        self.move(window_geometry.topLeft())
    
    def _create_app_widget(self, application: LaunchedApplication) -> QWidget:
        """创建应用程序部件
        
        Args:
            application: 应用程序对象
            
        Returns:
            QWidget: 应用程序部件
        """
        # 创建应用部件
        app_widget = QWidget()
        app_widget.setProperty("app_id", application.id)
        
        # 应用布局
        app_layout = QVBoxLayout(app_widget)
        app_layout.setContentsMargins(5, 5, 5, 5)
        app_layout.setSpacing(5)
        
        # 应用图标
        icon_label = QLabel()
        icon_size = QSize(48, 48)
        
        # 设置图标
        if application.icon_path and os.path.exists(application.icon_path):
            icon = QIcon(application.icon_path)
            pixmap = icon.pixmap(icon_size)
            icon_label.setPixmap(pixmap)
        else:
            # 使用默认图标
            default_icon = self.launcher_manager.config["default_app_icon"]
            if default_icon and os.path.exists(default_icon):
                pixmap = QPixmap(default_icon).scaled(icon_size)
                icon_label.setPixmap(pixmap)
            else:
                # 默认图标不存在，使用文本代替
                icon_label.setText("App")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                icon_label.setStyleSheet("background-color: #f0f0f0; border-radius: 5px;")
        
        icon_label.setFixedSize(icon_size)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignCenter)
        
        # 应用名称
        name_label = QLabel(application.name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setMaximumWidth(100)
        app_layout.addWidget(name_label, 0, Qt.AlignmentFlag.AlignCenter)
        
        # 设置应用部件样式
        app_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f8f8;
                border-radius: 8px;
                padding: 5px;
            }
            QWidget:hover {
                background-color: #e0e0e0;
            }
        """)
        
        # 设置应用部件固定大小
        app_widget.setFixedSize(100, 100)
        
        # 设置应用部件的鼠标点击事件
        app_widget.mousePressEvent = lambda e, aid=application.id: self._handle_app_click(aid, e)
        
        return app_widget
    
    def _populate_grid(self, applications: List[LaunchedApplication]) -> None:
        """填充应用程序网格
        
        Args:
            applications: 应用程序列表
        """
        # 清空网格
        self._clear_grid()
        
        # 填充网格
        row, col = 0, 0
        max_columns = self.launcher_manager.config.get("grid_columns", 5)  # 从配置中获取列数，默认5列
        
        for app in applications:
            app_widget = self._create_app_widget(app)
            self.app_grid.addWidget(app_widget, row, col)
            self.app_widgets[app.id] = app_widget
            
            # 更新行列索引
            col += 1
            if col >= max_columns:
                col = 0
                row += 1
    
    def _clear_grid(self) -> None:
        """清空应用程序网格"""
        # 移除所有应用部件
        for app_widget in self.app_widgets.values():
            self.app_grid.removeWidget(app_widget)
            app_widget.deleteLater()
        
        # 清空应用部件字典
        self.app_widgets.clear()
    
    def _show_all_applications(self) -> None:
        """显示所有应用程序"""
        # 获取所有应用程序
        applications = self.launcher_manager.get_all_applications()
        
        # 按名称排序
        applications.sort(key=lambda app: app.name)
        
        # 填充网格
        self._populate_grid(applications)
        
        # 更新当前分组ID
        self.current_group_id = None
    
    def _show_group(self, group_id: str) -> None:
        """显示指定分组的应用程序
        
        Args:
            group_id: 分组ID
        """
        # 获取分组应用程序
        applications = self.launcher_manager.get_applications_by_group(group_id)
        
        # 按名称排序
        applications.sort(key=lambda app: app.name)
        
        # 填充网格
        self._populate_grid(applications)
        
        # 更新当前分组ID
        self.current_group_id = group_id
    
    def _show_recent_applications(self) -> None:
        """显示最近使用的应用程序"""
        # 获取最近使用的应用程序
        applications = self.launcher_manager.get_recent_applications()
        
        # 填充网格
        self._populate_grid(applications)
        
        # 更新当前分组ID
        self.current_group_id = None
    
    def _search_applications(self) -> None:
        """搜索应用程序"""
        # 获取搜索关键词
        query = self.search_box.text().strip()
        
        if not query:
            # 如果搜索框为空，显示当前分组或所有应用
            if self.current_group_id:
                self._show_group(self.current_group_id)
            else:
                self._show_all_applications()
            return
        
        # 搜索应用程序
        applications = self.launcher_manager.search_applications(query)
        
        # 填充网格
        self._populate_grid(applications)
    
    def _handle_app_click(self, app_id: str, event) -> None:
        """处理应用程序点击事件
        
        Args:
            app_id: 应用程序ID
            event: 鼠标事件
        """
        # 区分左键和右键点击
        if event.button() == Qt.MouseButton.LeftButton:
            # 左键点击启动应用
            self._launch_application(app_id)
        elif event.button() == Qt.MouseButton.RightButton:
            # 右键点击显示上下文菜单
            self._show_app_context_menu(app_id, event.globalPosition().toPoint())
    
    def _launch_application(self, app_id: str) -> None:
        """启动应用程序
        
        Args:
            app_id: 应用程序ID
        """
        # 获取应用程序
        application = self.launcher_manager.get_application(app_id)
        if not application:
            logger.warning(f"找不到ID为 '{app_id}' 的应用程序")
            return
        
        # 启动应用程序
        result = self.launcher_manager.launch_application(app_id)
        
        # 处理启动结果
        if result.success:
            logger.info(f"启动应用程序 '{application.name}' 成功")
            
            # 关闭启动器窗口
            self.accept()
        else:
            logger.error(f"启动应用程序 '{application.name}' 失败: {result.message}")
            
            # TODO: 显示错误消息
    
    def _show_app_context_menu(self, app_id, position):
        """显示应用程序上下文菜单"""
        app = self.launcher_manager.get_application(app_id)
        if not app:
            return
        
        menu = QMenu(self)
        
        # 基本操作
        launch_action = menu.addAction("启动")
        favorite_action = menu.addAction("✓ 收藏夹" if app.favorite else "收藏夹")
        settings_action = menu.addAction("应用设置")
        menu.addSeparator()
        
        # 添加导出选项
        export_action = menu.addAction("导出应用")
        
        # 分组子菜单
        groups_menu = QMenu("添加到分组", self)
        menu.addMenu(groups_menu)
        
        # 填充分组
        group_actions = {}
        for group_id, group in self.launcher_manager.groups.items():
            if group.id != self.launcher_manager.config["favorite_group_id"]:  # 排除收藏夹分组
                is_in_group = group.has_application(app_id)
                action = groups_menu.addAction("✓ " + group.name if is_in_group else group.name)
                group_actions[action] = (group.id, is_in_group)
        
        # 显示菜单并获取所选操作
        action = menu.exec(position)
        
        # 处理操作
        if action == launch_action:
            self._launch_application(app_id)
        elif action == favorite_action:
            self._toggle_favorite(app_id)
        elif action == settings_action:
            dialog = AppSettingsDialog(app, self.launcher_manager, self)
            if dialog.exec():
                # 更新应用和UI
                self._populate_current_view()
        elif action == export_action:
            self._export_application(app_id)
        else:
            # 处理分组操作
            for act, (group_id, is_in_group) in group_actions.items():
                if action == act:
                    self._toggle_in_group(app_id, group_id, is_in_group)
                    break
    
    def _show_import_export_menu(self):
        """显示导入/导出菜单"""
        menu = QMenu(self)
        
        # 应用操作
        import_apps_action = menu.addAction("导入应用")
        export_apps_action = menu.addAction("导出所有应用")
        export_selected_action = menu.addAction("导出当前显示的应用")
        menu.addSeparator()
        
        # 分组操作
        import_group_action = menu.addAction("导入分组")
        export_group_menu = QMenu("导出分组", self)
        menu.addMenu(export_group_menu)
        
        # 填充分组导出选项
        group_actions = {}
        for group_id, group in self.launcher_manager.groups.items():
            action = export_group_menu.addAction(group.name)
            group_actions[action] = group.id
        
        # 显示菜单
        pos = self.import_export_button.mapToGlobal(self.import_export_button.rect().bottomLeft())
        action = menu.exec(pos)
        
        # 处理操作
        if action == import_apps_action:
            self._import_applications()
        elif action == export_apps_action:
            self._export_all_applications()
        elif action == export_selected_action:
            self._export_displayed_applications()
        elif action == import_group_action:
            self._import_group()
        else:
            # 处理分组导出操作
            for act, group_id in group_actions.items():
                if action == act:
                    self._export_group(group_id)
                    break
    
    def _import_applications(self):
        """导入应用程序"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择导入文件", "", "JSON文件 (*.json);;所有文件 (*)"
        )
        
        if not file_path:
            return
            
        success_count, fail_count, error_messages = self.launcher_manager.import_applications(file_path)
        
        # 显示导入结果
        if success_count > 0 or fail_count > 0:
            message = f"导入结果:\n- 成功: {success_count}\n- 失败: {fail_count}"
            
            if error_messages and len(error_messages) > 0:
                message += "\n\n错误消息:"
                for i, msg in enumerate(error_messages[:5]):  # 仅显示前5个错误
                    message += f"\n{i+1}. {msg}"
                
                if len(error_messages) > 5:
                    message += f"\n... 共 {len(error_messages)} 个错误"
            
            QMessageBox.information(self, "导入完成", message)
            
            # 刷新UI
            self._populate_current_view()
        else:
            QMessageBox.warning(self, "导入失败", "导入过程中发生错误，未能导入任何应用程序。")
    
    def _export_application(self, app_id):
        """导出单个应用程序"""
        app = self.launcher_manager.get_application(app_id)
        if not app:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, f"导出应用 '{app.name}'", 
            f"{app.name}.json", 
            "JSON文件 (*.json);;所有文件 (*)"
        )
        
        if not file_path:
            return
            
        if self.launcher_manager.export_applications(file_path, [app_id]):
            QMessageBox.information(self, "导出成功", f"应用 '{app.name}' 已成功导出到:\n{file_path}")
        else:
            QMessageBox.warning(self, "导出失败", f"导出应用 '{app.name}' 时发生错误。")
    
    def _export_all_applications(self):
        """导出所有应用程序"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出所有应用", 
            "all_applications.json", 
            "JSON文件 (*.json);;所有文件 (*)"
        )
        
        if not file_path:
            return
            
        if self.launcher_manager.export_applications(file_path):
            QMessageBox.information(
                self, 
                "导出成功", 
                f"所有应用程序 ({len(self.launcher_manager.applications)}) 已成功导出到:\n{file_path}"
            )
        else:
            QMessageBox.warning(self, "导出失败", "导出应用程序时发生错误。")
    
    def _export_displayed_applications(self):
        """导出当前显示的应用程序"""
        displayed_app_ids = []
        
        # 收集当前显示的应用ID
        for i in range(self.app_grid.count()):
            widget = self.app_grid.itemAt(i).widget()
            if widget and hasattr(widget, 'app_id'):
                displayed_app_ids.append(widget.app_id)
        
        if not displayed_app_ids:
            QMessageBox.information(self, "没有应用", "当前没有显示的应用程序可以导出。")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            f"导出 {len(displayed_app_ids)} 个应用", 
            "selected_applications.json", 
            "JSON文件 (*.json);;所有文件 (*)"
        )
        
        if not file_path:
            return
            
        if self.launcher_manager.export_applications(file_path, displayed_app_ids):
            QMessageBox.information(
                self, 
                "导出成功", 
                f"已成功导出 {len(displayed_app_ids)} 个应用程序到:\n{file_path}"
            )
        else:
            QMessageBox.warning(self, "导出失败", "导出应用程序时发生错误。")
    
    def _import_group(self):
        """导入分组"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择分组导入文件", "", "JSON文件 (*.json);;所有文件 (*)"
        )
        
        if not file_path:
            return
            
        success, group_id, success_count, fail_count = self.launcher_manager.import_group(file_path)
        
        if success:
            group = self.launcher_manager.get_group(group_id)
            message = f"分组 '{group.name}' 导入成功:\n- 应用成功: {success_count}\n- 应用失败: {fail_count}"
            QMessageBox.information(self, "导入完成", message)
            
            # 刷新UI
            self._update_group_buttons()
            self._populate_current_view()
        else:
            QMessageBox.warning(self, "导入失败", "导入分组时发生错误。")
    
    def _export_group(self, group_id):
        """导出分组"""
        group = self.launcher_manager.get_group(group_id)
        if not group:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            f"导出分组 '{group.name}'", 
            f"{group.name}.json", 
            "JSON文件 (*.json);;所有文件 (*)"
        )
        
        if not file_path:
            return
            
        if self.launcher_manager.export_group(group_id, file_path):
            app_count = len(group.applications)
            QMessageBox.information(
                self, 
                "导出成功", 
                f"分组 '{group.name}' 及其 {app_count} 个应用已成功导出到:\n{file_path}"
            )
        else:
            QMessageBox.warning(self, "导出失败", f"导出分组 '{group.name}' 时发生错误。")
            
    def _add_application(self):
        """添加新应用程序"""
        # 创建一个空的应用对象
        app = LaunchedApplication(
            name="新应用",
            path=""
        )
        
        # 显示设置对话框
        dialog = AppSettingsDialog(app, self.launcher_manager, self, is_new=True)
        if dialog.exec():
            # 添加到管理器
            if app.path and os.path.exists(app.path):
                self.launcher_manager.add_application(app)
                self._populate_current_view()
            else:
                QMessageBox.warning(self, "路径无效", "应用程序路径无效或不存在。")
    
    def _toggle_favorite(self, app_id: str) -> None:
        """切换应用的收藏状态
        
        Args:
            app_id: 应用程序ID
        """
        new_state = self.launcher_manager.toggle_favorite(app_id)
        
        # 如果当前显示的是收藏分组，刷新显示
        if self.current_group_id == self.launcher_manager.config["favorite_group_id"]:
            self._show_group(self.current_group_id)
    
    def _toggle_in_group(self, app_id: str, group_id: str, is_in_group: bool) -> None:
        """切换应用在分组中的状态
        
        Args:
            app_id: 应用程序ID
            group_id: 分组ID
            is_in_group: 是否在分组中
        """
        if is_in_group:
            self.launcher_manager.add_to_group(app_id, group_id)
        else:
            self.launcher_manager.remove_from_group(app_id, group_id)
        
        # 如果当前显示的是该分组，刷新显示
        if self.current_group_id == group_id:
            self._show_group(group_id)
    
    def _show_settings(self) -> None:
        """显示设置对话框"""
        dialog = LauncherSettingsDialog(self.launcher_manager, self)
        if dialog.exec():
            # 刷新UI以应用新设置
            self._update_group_buttons()
            self._populate_current_view()
    
    def _show_app_settings(self, app_id):
        """显示应用设置对话框
        
        Args:
            app_id: 应用ID
        """
        app = self.launcher_manager.get_application(app_id)
        if not app:
            return
            
        dialog = AppSettingsDialog(app, self.launcher_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 更新应用
            self._populate_grid()  # 刷新网格
    
    def closeEvent(self, event) -> None:
        """关闭事件处理
        
        Args:
            event: 关闭事件
        """
        # 保存配置
        self.launcher_manager.save_configuration()
        
        # 接受事件，关闭窗口
        event.accept()


class AppSettingsDialog(QDialog):
    """应用程序设置对话框"""
    
    def __init__(self, application, launcher_manager, parent=None, is_new=False):
        super().__init__(parent)
        self.application = application
        self.launcher_manager = launcher_manager
        self.is_new = is_new
        self.original_app_data = application.to_dict() if not is_new else {}
        
        self.setWindowTitle("应用程序设置")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self.env_vars = application.environment_variables.copy() if hasattr(application, 'environment_variables') else {}
        
        self._init_ui()
        self._load_application_data()
        
    def _init_ui(self):
        """初始化用户界面"""
        main_layout = QVBoxLayout(self)
        
        # 创建标签页控件
        self.tab_widget = QTabWidget()
        
        # 基本信息标签页
        basic_tab = QWidget()
        self.tab_widget.addTab(basic_tab, "基本信息")
        
        # 启动参数标签页
        launch_tab = QWidget()
        self.tab_widget.addTab(launch_tab, "启动参数")
        
        # 环境变量标签页
        env_tab = QWidget()
        self.tab_widget.addTab(env_tab, "环境变量")
        
        # 标签标签页
        tags_tab = QWidget()
        self.tab_widget.addTab(tags_tab, "标签")
        
        # 设置基本信息标签页
        self._setup_basic_tab(basic_tab)
        
        # 设置启动参数标签页
        self._setup_launch_tab(launch_tab)
        
        # 设置环境变量标签页
        self._setup_env_tab(env_tab)
        
        # 设置标签标签页
        self._setup_tags_tab(tags_tab)
        
        main_layout.addWidget(self.tab_widget)
        
        # 添加按钮
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
        
    def _setup_basic_tab(self, tab):
        """设置基本信息标签页"""
        layout = QVBoxLayout(tab)
        
        # 名称
        name_layout = QHBoxLayout()
        name_label = QLabel("名称:")
        self.name_edit = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # 路径
        path_layout = QHBoxLayout()
        path_label = QLabel("路径:")
        self.path_edit = QLineEdit()
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self._browse_path)
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_button)
        layout.addLayout(path_layout)
        
        # 图标
        icon_layout = QHBoxLayout()
        icon_label = QLabel("图标:")
        self.icon_edit = QLineEdit()
        icon_browse_button = QPushButton("浏览...")
        icon_browse_button.clicked.connect(self._browse_icon)
        icon_layout.addWidget(icon_label)
        icon_layout.addWidget(self.icon_edit)
        icon_layout.addWidget(icon_browse_button)
        layout.addLayout(icon_layout)
        
        # 描述
        desc_layout = QVBoxLayout()
        desc_label = QLabel("描述:")
        self.desc_edit = QLineEdit()
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.desc_edit)
        layout.addLayout(desc_layout)
        
        # 工作目录
        work_dir_layout = QHBoxLayout()
        work_dir_label = QLabel("工作目录:")
        self.work_dir_edit = QLineEdit()
        work_dir_browse_button = QPushButton("浏览...")
        work_dir_browse_button.clicked.connect(self._browse_work_dir)
        work_dir_layout.addWidget(work_dir_label)
        work_dir_layout.addWidget(self.work_dir_edit)
        work_dir_layout.addWidget(work_dir_browse_button)
        layout.addLayout(work_dir_layout)
        
        # 收藏复选框
        self.favorite_check = QCheckBox("添加到收藏夹")
        layout.addWidget(self.favorite_check)
        
        layout.addStretch()
        
    def _setup_launch_tab(self, tab):
        """设置启动参数标签页"""
        layout = QVBoxLayout(tab)
        
        # 启动模式
        mode_layout = QHBoxLayout()
        mode_label = QLabel("启动模式:")
        self.mode_combo = QComboBox()
        
        # 添加启动模式选项
        for mode in LaunchMode:
            self.mode_combo.addItem(mode.name, mode)
            
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_combo)
        layout.addLayout(mode_layout)
        
        # 命令行参数
        args_layout = QVBoxLayout()
        args_label = QLabel("命令行参数:")
        self.args_edit = QLineEdit()
        args_layout.addWidget(args_label)
        args_layout.addWidget(self.args_edit)
        layout.addLayout(args_layout)
        
        # 管理员权限
        self.admin_check = QCheckBox("以管理员权限运行")
        layout.addWidget(self.admin_check)
        
        layout.addStretch()
        
    def _setup_env_tab(self, tab):
        """设置环境变量标签页"""
        layout = QVBoxLayout(tab)
        
        # 创建表格
        self.env_table = QTableWidget(0, 2)
        self.env_table.setHorizontalHeaderLabels(["变量名", "值"])
        self.env_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.env_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.env_table)
        
        # 按钮布局
        buttons_layout = QHBoxLayout()
        add_button = QPushButton("添加")
        add_button.clicked.connect(self._add_env_var)
        edit_button = QPushButton("编辑")
        edit_button.clicked.connect(self._edit_env_var)
        remove_button = QPushButton("删除")
        remove_button.clicked.connect(self._remove_env_var)
        
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(edit_button)
        buttons_layout.addWidget(remove_button)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
    def _setup_tags_tab(self, tab):
        """设置标签标签页"""
        layout = QVBoxLayout(tab)
        
        # 标签列表
        self.tags_list = QListWidget()
        layout.addWidget(self.tags_list)
        
        # 按钮布局
        buttons_layout = QHBoxLayout()
        add_button = QPushButton("添加")
        add_button.clicked.connect(self._add_tag)
        remove_button = QPushButton("删除")
        remove_button.clicked.connect(self._remove_tag)
        
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(remove_button)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
    def _load_application_data(self):
        """加载应用程序数据到控件"""
        # 基本信息
        self.name_edit.setText(self.application.name)
        self.path_edit.setText(self.application.path)
        self.icon_edit.setText(self.application.icon_path if self.application.icon_path else "")
        self.desc_edit.setText(self.application.description if self.application.description else "")
        self.work_dir_edit.setText(self.application.working_directory if self.application.working_directory else "")
        self.favorite_check.setChecked(self.application.favorite)
        
        # 启动参数
        self.args_edit.setText(" ".join(self.application.arguments) if self.application.arguments else "")
        
        # 查找启动模式
        for i in range(self.mode_combo.count()):
            mode = self.mode_combo.itemData(i)
            if hasattr(self.application, 'launch_mode') and mode == self.application.launch_mode:
                self.mode_combo.setCurrentIndex(i)
                break
        
        # 管理员权限
        if hasattr(self.application, 'launch_mode'):
            self.admin_check.setChecked(self.application.launch_mode == LaunchMode.ADMIN)
        
        # 环境变量
        self._populate_env_vars()
        
        # 标签
        self._populate_tags()
        
    def _populate_env_vars(self):
        """填充环境变量表格"""
        self.env_table.setRowCount(0)
        
        if not hasattr(self.application, 'environment_variables') or not self.application.environment_variables:
            return
            
        for i, (key, value) in enumerate(self.env_vars.items()):
            self.env_table.insertRow(i)
            self.env_table.setItem(i, 0, QTableWidgetItem(key))
            self.env_table.setItem(i, 1, QTableWidgetItem(value))
            
    def _populate_tags(self):
        """填充标签列表"""
        self.tags_list.clear()
        
        if not self.application.tags:
            return
            
        for tag in self.application.tags:
            self.tags_list.addItem(tag)
            
    def _browse_path(self):
        """浏览应用程序路径"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择应用程序", 
            "", 
            "可执行文件 (*.exe);;所有文件 (*)"
        )
        
        if file_path:
            self.path_edit.setText(file_path)
            
            # 如果名称为空或是默认值，自动设置为文件名
            if not self.name_edit.text() or self.name_edit.text() == "新应用":
                self.name_edit.setText(os.path.basename(file_path).split('.')[0])
            
            # 自动设置工作目录
            if not self.work_dir_edit.text():
                self.work_dir_edit.setText(os.path.dirname(file_path))
                
    def _browse_icon(self):
        """浏览图标路径"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择图标", 
            "", 
            "图标文件 (*.ico *.png *.jpg);;所有文件 (*)"
        )
        
        if file_path:
            self.icon_edit.setText(file_path)
            
    def _browse_work_dir(self):
        """浏览工作目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, 
            "选择工作目录", 
            ""
        )
        
        if dir_path:
            self.work_dir_edit.setText(dir_path)
            
    def _add_env_var(self):
        """添加环境变量"""
        key, ok = QInputDialog.getText(self, "添加环境变量", "变量名:")
        if ok and key:
            value, ok = QInputDialog.getText(self, "添加环境变量", "变量值:")
            if ok:
                # 添加到内部字典
                self.env_vars[key] = value
                
                # 更新表格
                row = self.env_table.rowCount()
                self.env_table.insertRow(row)
                self.env_table.setItem(row, 0, QTableWidgetItem(key))
                self.env_table.setItem(row, 1, QTableWidgetItem(value))
                
    def _edit_env_var(self):
        """编辑环境变量"""
        selected_rows = self.env_table.selectedItems()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        key_item = self.env_table.item(row, 0)
        value_item = self.env_table.item(row, 1)
        
        if not key_item or not value_item:
            return
            
        old_key = key_item.text()
        old_value = value_item.text()
        
        # 获取新键
        new_key, ok = QInputDialog.getText(
            self, "编辑环境变量", "变量名:", 
            text=old_key
        )
        if ok and new_key:
            # 获取新值
            new_value, ok = QInputDialog.getText(
                self, "编辑环境变量", "变量值:", 
                text=old_value
            )
            if ok:
                # 从字典中删除旧键
                if old_key in self.env_vars:
                    del self.env_vars[old_key]
                    
                # 添加新键值对
                self.env_vars[new_key] = new_value
                
                # 更新表格
                key_item.setText(new_key)
                value_item.setText(new_value)
                
    def _remove_env_var(self):
        """删除环境变量"""
        selected_rows = self.env_table.selectedItems()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        key_item = self.env_table.item(row, 0)
        
        if not key_item:
            return
            
        key = key_item.text()
        
        # 从字典中删除
        if key in self.env_vars:
            del self.env_vars[key]
            
        # 从表格中删除
        self.env_table.removeRow(row)
        
    def _add_tag(self):
        """添加标签"""
        tag, ok = QInputDialog.getText(self, "添加标签", "标签名:")
        if ok and tag:
            # 检查是否已存在
            for i in range(self.tags_list.count()):
                if self.tags_list.item(i).text() == tag:
                    return
                    
            # 添加到列表
            self.tags_list.addItem(tag)
            
    def _remove_tag(self):
        """删除标签"""
        selected_items = self.tags_list.selectedItems()
        if not selected_items:
            return
            
        for item in selected_items:
            row = self.tags_list.row(item)
            self.tags_list.takeItem(row)
            
    def accept(self):
        """接受对话框"""
        # 获取基本信息
        self.application.name = self.name_edit.text()
        self.application.path = self.path_edit.text()
        self.application.icon_path = self.icon_edit.text() or None
        self.application.description = self.desc_edit.text() or None
        self.application.working_directory = self.work_dir_edit.text() or None
        self.application.favorite = self.favorite_check.isChecked()
        
        # 获取命令行参数
        args_text = self.args_edit.text().strip()
        self.application.arguments = args_text.split() if args_text else []
        
        # 获取启动模式
        mode_index = self.mode_combo.currentIndex()
        if mode_index >= 0:
            self.application.launch_mode = self.mode_combo.itemData(mode_index)
            
            # 如果选择了管理员权限，覆盖启动模式
            if self.admin_check.isChecked():
                self.application.launch_mode = LaunchMode.ADMIN
                
        # 获取环境变量
        self.application.environment_variables = self.env_vars.copy()
        
        # 获取标签
        tags = []
        for i in range(self.tags_list.count()):
            tags.append(self.tags_list.item(i).text())
        self.application.tags = tags
        
        super().accept()


class LauncherSettingsDialog(QDialog):
    """启动器设置对话框"""
    
    def __init__(self, launcher_manager, parent=None):
        super().__init__(parent)
        self.launcher_manager = launcher_manager
        self.original_config = launcher_manager.config.copy()
        
        self.setWindowTitle("启动器设置")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self._init_ui()
        self._load_settings()
        
    def _init_ui(self):
        """初始化用户界面"""
        main_layout = QVBoxLayout(self)
        
        # 创建标签页控件
        self.tab_widget = QTabWidget()
        
        # 常规设置标签页
        general_tab = QWidget()
        self.tab_widget.addTab(general_tab, "常规设置")
        
        # 界面设置标签页
        ui_tab = QWidget()
        self.tab_widget.addTab(ui_tab, "界面设置")
        
        # 高级设置标签页
        advanced_tab = QWidget()
        self.tab_widget.addTab(advanced_tab, "高级设置")
        
        # 设置常规设置标签页
        self._setup_general_tab(general_tab)
        
        # 设置界面设置标签页
        self._setup_ui_tab(ui_tab)
        
        # 设置高级设置标签页
        self._setup_advanced_tab(advanced_tab)
        
        main_layout.addWidget(self.tab_widget)
        
        # 添加按钮
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
        
    def _setup_general_tab(self, tab):
        """设置常规设置标签页"""
        layout = QVBoxLayout(tab)
        
        # 默认应用图标
        icon_layout = QHBoxLayout()
        icon_label = QLabel("默认应用图标:")
        self.icon_edit = QLineEdit()
        icon_browse_button = QPushButton("浏览...")
        icon_browse_button.clicked.connect(self._browse_app_icon)
        icon_layout.addWidget(icon_label)
        icon_layout.addWidget(self.icon_edit)
        icon_layout.addWidget(icon_browse_button)
        layout.addLayout(icon_layout)
        
        # 默认分组图标
        group_icon_layout = QHBoxLayout()
        group_icon_label = QLabel("默认分组图标:")
        self.group_icon_edit = QLineEdit()
        group_icon_browse_button = QPushButton("浏览...")
        group_icon_browse_button.clicked.connect(self._browse_group_icon)
        group_icon_layout.addWidget(group_icon_label)
        group_icon_layout.addWidget(self.group_icon_edit)
        group_icon_layout.addWidget(group_icon_browse_button)
        layout.addLayout(group_icon_layout)
        
        # 自动加载系统应用
        self.auto_load_check = QCheckBox("自动加载系统应用")
        layout.addWidget(self.auto_load_check)
        
        layout.addStretch()
        
    def _setup_ui_tab(self, tab):
        """设置界面设置标签页"""
        layout = QVBoxLayout(tab)
        
        # 最近使用的应用数量上限
        recent_layout = QHBoxLayout()
        recent_label = QLabel("最近使用的应用数量上限:")
        self.recent_spin = QSpinBox()
        self.recent_spin.setMinimum(1)
        self.recent_spin.setMaximum(50)
        recent_layout.addWidget(recent_label)
        recent_layout.addWidget(self.recent_spin)
        layout.addLayout(recent_layout)
        
        # 网格列数
        grid_layout = QHBoxLayout()
        grid_label = QLabel("应用网格列数:")
        self.grid_spin = QSpinBox()
        self.grid_spin.setMinimum(3)
        self.grid_spin.setMaximum(10)
        grid_layout.addWidget(grid_label)
        grid_layout.addWidget(self.grid_spin)
        layout.addLayout(grid_layout)
        
        layout.addStretch()
        
    def _setup_advanced_tab(self, tab):
        """设置高级设置标签页"""
        layout = QVBoxLayout(tab)
        
        # 管理分组
        manage_groups_button = QPushButton("管理分组")
        manage_groups_button.clicked.connect(self._manage_groups)
        layout.addWidget(manage_groups_button)
        
        # 导入/导出设置
        import_export_layout = QHBoxLayout()
        import_button = QPushButton("导入设置")
        import_button.clicked.connect(self._import_settings)
        export_button = QPushButton("导出设置")
        export_button.clicked.connect(self._export_settings)
        import_export_layout.addWidget(import_button)
        import_export_layout.addWidget(export_button)
        layout.addLayout(import_export_layout)
        
        # 重置设置
        reset_button = QPushButton("重置所有设置")
        reset_button.clicked.connect(self._reset_settings)
        layout.addWidget(reset_button)
        
        layout.addStretch()
        
    def _load_settings(self):
        """加载设置到控件"""
        # 常规设置
        self.icon_edit.setText(self.launcher_manager.config["default_app_icon"] or "")
        self.group_icon_edit.setText(self.launcher_manager.config["default_group_icon"] or "")
        self.auto_load_check.setChecked(self.launcher_manager.config["auto_load_system_apps"])
        
        # 界面设置
        self.recent_spin.setValue(self.launcher_manager.config["max_recent_apps"])
        
        # 如果存在grid_columns配置项，设置网格列数
        if "grid_columns" in self.launcher_manager.config:
            self.grid_spin.setValue(self.launcher_manager.config["grid_columns"])
        else:
            self.grid_spin.setValue(5)  # 默认值
            
    def _browse_app_icon(self):
        """浏览默认应用图标"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择默认应用图标", 
            "", 
            "图标文件 (*.ico *.png *.jpg);;所有文件 (*)"
        )
        
        if file_path:
            self.icon_edit.setText(file_path)
            
    def _browse_group_icon(self):
        """浏览默认分组图标"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择默认分组图标", 
            "", 
            "图标文件 (*.ico *.png *.jpg);;所有文件 (*)"
        )
        
        if file_path:
            self.group_icon_edit.setText(file_path)
            
    def _manage_groups(self):
        """管理分组"""
        # 此功能待实现
        QMessageBox.information(self, "提示", "分组管理功能将在未来版本中实现")
        
    def _import_settings(self):
        """导入设置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "导入设置", 
            "", 
            "JSON文件 (*.json);;所有文件 (*)"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                
            if "config" in settings:
                # 更新配置，保留原有值
                for key, value in settings["config"].items():
                    if key in self.launcher_manager.config:
                        self.launcher_manager.config[key] = value
                
                # 重新加载设置
                self._load_settings()
                
                QMessageBox.information(self, "成功", "设置已导入")
        except Exception as e:
            QMessageBox.warning(self, "导入失败", f"导入设置时发生错误: {str(e)}")
            
    def _export_settings(self):
        """导出设置"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "导出设置", 
            "launcher_settings.json", 
            "JSON文件 (*.json);;所有文件 (*)"
        )
        
        if not file_path:
            return
            
        try:
            # 准备导出数据
            export_data = {
                "config": self.launcher_manager.config,
                "export_time": datetime.now().isoformat()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                
            QMessageBox.information(self, "成功", f"设置已导出到: {file_path}")
        except Exception as e:
            QMessageBox.warning(self, "导出失败", f"导出设置时发生错误: {str(e)}")
            
    def _reset_settings(self):
        """重置所有设置"""
        reply = QMessageBox.question(
            self, 
            "确认重置", 
            "确定要重置所有设置吗？这将恢复默认值。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 恢复默认配置
            self.launcher_manager.config = {
                "auto_load_system_apps": True,
                "max_recent_apps": 10,
                "default_app_icon": None,
                "default_group_icon": None,
                "favorite_group_id": self.launcher_manager.config.get("favorite_group_id"),
                "grid_columns": 5
            }
            
            # 重新加载设置
            self._load_settings()
            
    def accept(self):
        """接受对话框"""
        # 保存常规设置
        self.launcher_manager.config["default_app_icon"] = self.icon_edit.text() or None
        self.launcher_manager.config["default_group_icon"] = self.group_icon_edit.text() or None
        self.launcher_manager.config["auto_load_system_apps"] = self.auto_load_check.isChecked()
        
        # 保存界面设置
        self.launcher_manager.config["max_recent_apps"] = self.recent_spin.value()
        self.launcher_manager.config["grid_columns"] = self.grid_spin.value()
        
        # 保存配置
        self.launcher_manager.save_configuration()
        
        super().accept() 