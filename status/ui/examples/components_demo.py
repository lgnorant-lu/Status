"""
---------------------------------------------------------------
File name:                  components_demo.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                UI组件库演示程序
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

import sys
import os
import logging
from pathlib import Path

try:
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtGui import QIcon, QColor
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                QHBoxLayout, QTabWidget, QLabel, QScrollArea,
                                QSizePolicy, QSpacerItem)
    HAS_PYQT = True
except ImportError:
    HAS_PYQT = False
    logging.error("PyQt6未安装，无法运行UI组件演示程序")
    sys.exit(1)

# 确保能够导入status包
parent_dir = str(Path(__file__).resolve().parent.parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 导入自定义组件
from status.ui.components import (
    # 按钮组件
    PrimaryButton, SecondaryButton, TextButton, IconButton,
    # 输入组件
    TextField, SearchField, NumberField,
    # 卡片组件
    Card, ExpandableCard,
    # 进度指示器组件
    ProgressStatus, ProgressBar, ProgressIndicator, LoadingWidget,
    # 通知组件
    NotificationType, NotificationManager, show_info, show_success, show_warning, show_error
)

# 设置日志记录
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComponentsDemo(QMainWindow):
    """UI组件库演示程序主窗口"""
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        # 设置窗口属性
        self.setWindowTitle("UI组件库演示")
        self.setMinimumSize(900, 700)
        
        # 创建中央部件和主布局
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 创建标题
        title_label = QLabel("Hollow-ming UI组件库", self)
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #E6E6E6;
            margin: 20px 0;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(title_label)
        
        # 创建标签页
        self.tabs = QTabWidget(self)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #323232;
                background-color: #252525;
                border-radius: 6px;
            }
            QTabBar::tab {
                background-color: #1D1D1D;
                color: #AAAAAA;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 100px;
                padding: 8px 16px;
            }
            QTabBar::tab:selected {
                background-color: #252525;
                color: #E6E6E6;
                border-top: 2px solid #1A6E8E;
            }
            QTabBar::tab:hover:!selected {
                background-color: #2A2A2A;
            }
        """)
        
        # 创建各组件演示页
        self.create_buttons_tab()
        self.create_inputs_tab()
        self.create_cards_tab()
        self.create_progress_tab()
        self.create_notifications_tab()
        
        self.main_layout.addWidget(self.tabs)
        
        # 初始化通知管理器
        self.notification_manager = NotificationManager.instance()
        
        # 应用全局样式
        self.apply_global_style()
        
    def apply_global_style(self):
        """应用全局样式"""
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1D1D1D;
                color: #E6E6E6;
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #252525;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #404040;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #505050;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background-color: transparent;
            }
            QLabel {
                color: #E6E6E6;
            }
        """)
        
    def create_scrollable_content(self, widget):
        """创建可滚动内容区域"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(widget)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        return scroll_area
    
    def create_section(self, title):
        """创建带标题的章节"""
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # 添加标题
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #E6E6E6;
            margin-top: 10px;
            margin-bottom: 5px;
        """)
        layout.addWidget(title_label)
        
        # 添加分隔线
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        separator.setStyleSheet("background-color: #323232;")
        layout.addWidget(separator)
        
        # 添加内容容器
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 10, 10, 20)
        layout.addWidget(content)
        
        return container, content_layout
    
    def create_buttons_tab(self):
        """创建按钮组件演示标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建标准按钮章节
        container, section_layout = self.create_section("标准按钮")
        
        # 创建按钮行
        button_row = QWidget()
        button_layout = QHBoxLayout(button_row)
        button_layout.setSpacing(20)
        
        # 添加各类按钮
        primary_btn = PrimaryButton("主按钮", on_click=lambda: show_info("按钮点击", "主按钮被点击"))
        secondary_btn = SecondaryButton("次要按钮", on_click=lambda: show_info("按钮点击", "次要按钮被点击"))
        text_btn = TextButton("文本按钮", on_click=lambda: show_info("按钮点击", "文本按钮被点击"))
        
        button_layout.addWidget(primary_btn)
        button_layout.addWidget(secondary_btn)
        button_layout.addWidget(text_btn)
        button_layout.addStretch(1)
        
        section_layout.addWidget(button_row)
        layout.addWidget(container)
        
        # 创建图标按钮章节
        container, section_layout = self.create_section("图标按钮")
        
        # 创建按钮行
        button_row = QWidget()
        button_layout = QHBoxLayout(button_row)
        button_layout.setSpacing(20)
        
        # 创建图标按钮（使用文本作为临时图标）
        icon_btn1 = IconButton("▶", tooltip="播放")
        icon_btn2 = IconButton("⏸", tooltip="暂停")
        icon_btn3 = IconButton("⏹", tooltip="停止")
        
        icon_btn1.clicked.connect(lambda: show_info("图标按钮", "播放按钮被点击"))
        icon_btn2.clicked.connect(lambda: show_info("图标按钮", "暂停按钮被点击"))
        icon_btn3.clicked.connect(lambda: show_info("图标按钮", "停止按钮被点击"))
        
        button_layout.addWidget(icon_btn1)
        button_layout.addWidget(icon_btn2)
        button_layout.addWidget(icon_btn3)
        button_layout.addStretch(1)
        
        section_layout.addWidget(button_row)
        layout.addWidget(container)
        
        # 添加禁用按钮章节
        container, section_layout = self.create_section("禁用状态按钮")
        
        # 创建按钮行
        button_row = QWidget()
        button_layout = QHBoxLayout(button_row)
        button_layout.setSpacing(20)
        
        # 添加禁用状态的按钮
        disabled_primary = PrimaryButton("禁用主按钮")
        disabled_primary.setEnabled(False)
        
        disabled_secondary = SecondaryButton("禁用次要按钮")
        disabled_secondary.setEnabled(False)
        
        disabled_text = TextButton("禁用文本按钮")
        disabled_text.setEnabled(False)
        
        button_layout.addWidget(disabled_primary)
        button_layout.addWidget(disabled_secondary)
        button_layout.addWidget(disabled_text)
        button_layout.addStretch(1)
        
        section_layout.addWidget(button_row)
        layout.addWidget(container)
        
        # 添加伸缩空间
        layout.addStretch(1)
        
        # 创建可滚动区域并添加到标签页
        scroll_area = self.create_scrollable_content(tab)
        self.tabs.addTab(scroll_area, "按钮")
        
    def create_inputs_tab(self):
        """创建输入组件演示标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建文本输入章节
        container, section_layout = self.create_section("文本输入")
        
        # 创建普通文本输入
        text_field = TextField(
            label="用户名",
            placeholder="请输入用户名",
            helper_text="用户名长度不少于3个字符",
            required=True
        )
        text_field.valueChanged.connect(lambda val: self.validate_username(text_field, val))
        section_layout.addWidget(text_field)
        
        # 创建密码输入
        password_field = TextField(
            label="密码",
            placeholder="请输入密码",
            helper_text="密码长度不少于6个字符",
            password=True,
            required=True
        )
        section_layout.addWidget(password_field)
        
        layout.addWidget(container)
        
        # 创建搜索输入章节
        container, section_layout = self.create_section("搜索输入")
        
        # 创建搜索输入
        search_field = SearchField(
            placeholder="搜索内容...",
            suggestions=["Hollow Knight", "Silksong", "Hornet", "Knight", "Quirrel"]
        )
        section_layout.addWidget(search_field)
        
        layout.addWidget(container)
        
        # 创建数字输入章节
        container, section_layout = self.create_section("数字输入")
        
        # 创建整数输入
        int_field = NumberField(
            label="年龄",
            placeholder="请输入年龄",
            min_value=1,
            max_value=120,
            helper_text="有效年龄范围: 1-120"
        )
        section_layout.addWidget(int_field)
        
        # 创建浮点数输入
        float_field = NumberField(
            label="身高 (m)",
            placeholder="请输入身高",
            min_value=0.5,
            max_value=2.5,
            decimals=2,
            helper_text="有效身高范围: 0.50-2.50 m"
        )
        section_layout.addWidget(float_field)
        
        layout.addWidget(container)
        
        # 添加伸缩空间
        layout.addStretch(1)
        
        # 创建可滚动区域并添加到标签页
        scroll_area = self.create_scrollable_content(tab)
        self.tabs.addTab(scroll_area, "输入")
        
    def validate_username(self, field, value):
        """验证用户名"""
        if value and len(value) < 3:
            field.setError("用户名长度不能少于3个字符")
        else:
            field.clearError()
    
    def create_cards_tab(self):
        """创建卡片组件演示标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建标准卡片章节
        container, section_layout = self.create_section("标准卡片")
        
        # 创建标准卡片
        card = Card(title="系统状态", subtitle="当前系统资源使用情况")
        
        # 添加卡片内容
        status_label = QLabel("CPU使用率: 25%\n内存使用率: 40%\n磁盘空间: 150GB可用")
        status_label.setStyleSheet("font-size: 14px;")
        card.addWidget(status_label)
        
        # 添加操作按钮
        action_layout = QHBoxLayout()
        action_layout.addStretch(1)
        refresh_btn = SecondaryButton("刷新")
        refresh_btn.clicked.connect(lambda: show_info("刷新", "刷新系统状态"))
        action_layout.addWidget(refresh_btn)
        card.addLayout(action_layout)
        
        section_layout.addWidget(card)
        layout.addWidget(container)
        
        # 创建可展开卡片章节
        container, section_layout = self.create_section("可展开卡片")
        
        # 创建可展开卡片
        expandable_card = ExpandableCard(
            title="高级设置",
            subtitle="这些设置仅推荐高级用户修改"
        )
        
        # 添加卡片内容
        settings_label = QLabel("这里是一些高级设置选项，可以通过展开/折叠按钮控制显示。\n\n" +
                             "性能模式: 高性能\n防火墙: 已启用\n自动更新: 每周")
        settings_label.setStyleSheet("font-size: 14px;")
        expandable_card.addWidget(settings_label)
        
        section_layout.addWidget(expandable_card)
        layout.addWidget(container)
        
        # 添加伸缩空间
        layout.addStretch(1)
        
        # 创建可滚动区域并添加到标签页
        scroll_area = self.create_scrollable_content(tab)
        self.tabs.addTab(scroll_area, "卡片")
    
    def create_progress_tab(self):
        """创建进度指示器组件演示标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建进度条章节
        container, section_layout = self.create_section("进度条")
        
        # 创建不同状态的进度条
        progress_default = ProgressBar(label="默认进度条", value=45)
        progress_success = ProgressBar(label="成功进度条", value=80, status=ProgressStatus.SUCCESS)
        progress_warning = ProgressBar(label="警告进度条", value=60, status=ProgressStatus.WARNING)
        progress_error = ProgressBar(label="错误进度条", value=20, status=ProgressStatus.ERROR)
        
        # 添加进度条控制按钮
        control_layout = QHBoxLayout()
        
        # 进度递增按钮
        increase_btn = PrimaryButton("增加进度", on_click=lambda: self.update_progress(progress_default, 10))
        reset_btn = SecondaryButton("重置", on_click=lambda: progress_default.setValue(0))
        
        control_layout.addWidget(increase_btn)
        control_layout.addWidget(reset_btn)
        control_layout.addStretch(1)
        
        # 添加组件到布局
        section_layout.addWidget(progress_default)
        section_layout.addLayout(control_layout)
        section_layout.addWidget(progress_success)
        section_layout.addWidget(progress_warning)
        section_layout.addWidget(progress_error)
        
        layout.addWidget(container)
        
        # 创建加载指示器章节
        container, section_layout = self.create_section("加载指示器")
        
        # 创建加载指示器行
        indicators_layout = QHBoxLayout()
        
        # 创建不同颜色的加载指示器
        indicator1 = ProgressIndicator(color=QColor(26, 110, 142))  # 蓝色
        indicator1.start()
        indicators_layout.addWidget(indicator1)
        
        indicator2 = ProgressIndicator(color=QColor(45, 140, 70))  # 绿色
        indicator2.start()
        indicators_layout.addWidget(indicator2)
        
        indicator3 = ProgressIndicator(color=QColor(216, 156, 0))  # 黄色
        indicator3.start()
        indicators_layout.addWidget(indicator3)
        
        indicator4 = ProgressIndicator(color=QColor(158, 43, 37))  # 红色
        indicator4.start()
        indicators_layout.addWidget(indicator4)
        
        indicators_layout.addStretch(1)
        section_layout.addLayout(indicators_layout)
        
        # 创建带文本的加载组件
        loading_widget = LoadingWidget(text="正在加载数据，请稍候...")
        section_layout.addWidget(loading_widget)
        
        layout.addWidget(container)
        
        # 添加伸缩空间
        layout.addStretch(1)
        
        # 创建可滚动区域并添加到标签页
        scroll_area = self.create_scrollable_content(tab)
        self.tabs.addTab(scroll_area, "进度指示器")
    
    def update_progress(self, progress_bar, increment):
        """更新进度条值"""
        current = progress_bar.value()
        new_value = min(current + increment, progress_bar.maximum())
        progress_bar.setValue(new_value)
    
    def create_notifications_tab(self):
        """创建通知组件演示标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建通知章节
        container, section_layout = self.create_section("通知类型")
        
        # 创建通知演示按钮
        info_button = PrimaryButton("信息通知", on_click=lambda: show_info(
            "信息", "这是一条信息通知，用于显示一般性信息。"
        ))
        
        success_button = PrimaryButton("成功通知", on_click=lambda: show_success(
            "成功", "操作已成功完成！所有更改已保存。"
        ))
        
        warning_button = PrimaryButton("警告通知", on_click=lambda: show_warning(
            "警告", "检测到潜在问题，建议您尽快处理。"
        ))
        
        error_button = PrimaryButton("错误通知", on_click=lambda: show_error(
            "错误", "操作失败！无法完成请求的操作。"
        ))
        
        # 创建按钮行
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(info_button)
        buttons_layout.addWidget(success_button)
        buttons_layout.addWidget(warning_button)
        buttons_layout.addWidget(error_button)
        buttons_layout.addStretch(1)
        
        section_layout.addLayout(buttons_layout)
        layout.addWidget(container)
        
        # 创建通知选项章节
        container, section_layout = self.create_section("通知选项")
        
        # 创建持续时间演示按钮
        duration_layout = QHBoxLayout()
        
        short_button = PrimaryButton("短时通知 (2秒)", on_click=lambda: show_info(
            "短时通知", "这条通知会在2秒后自动关闭。", 2000
        ))
        
        long_button = PrimaryButton("长时通知 (10秒)", on_click=lambda: show_info(
            "长时通知", "这条通知会在10秒后自动关闭。", 10000
        ))
        
        persistent_button = PrimaryButton("持久通知", on_click=lambda: show_info(
            "持久通知", "这条通知不会自动关闭，需要手动关闭。", 0
        ))
        
        duration_layout.addWidget(short_button)
        duration_layout.addWidget(long_button)
        duration_layout.addWidget(persistent_button)
        duration_layout.addStretch(1)
        
        section_layout.addLayout(duration_layout)
        layout.addWidget(container)
        
        # 添加伸缩空间
        layout.addStretch(1)
        
        # 创建可滚动区域并添加到标签页
        scroll_area = self.create_scrollable_content(tab)
        self.tabs.addTab(scroll_area, "通知")

def run_demo():
    """运行组件演示程序"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # 使用Fusion风格以获得更一致的外观
    
    # 设置应用程序全局样式
    app.setStyleSheet("""
        QToolTip {
            background-color: #252525;
            color: #E6E6E6;
            border: 1px solid #323232;
            padding: 4px;
        }
    """)
    
    window = ComponentsDemo()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    run_demo() 