"""
---------------------------------------------------------------
File name:                  theme_demo.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                UI主题演示程序
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

import sys
import os
import logging
import traceback

# 确保可以导入上层包
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print("="*50)
print("主题演示程序启动")
print("="*50)

# 检查PyQt6是否安装
HAS_PYQT = False
try:
    print("尝试导入PyQt6...")
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit,
        QCheckBox, QRadioButton, QTabWidget, QSlider, QProgressBar,
        QGroupBox, QFrame, QSpacerItem, QSizePolicy, QGridLayout
    )
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtGui import QIcon, QPixmap
    
    HAS_PYQT = True
    print("PyQt6成功导入")
except ImportError as e:
    logger.error(f"导入PyQt6失败: {e}")
    print(f"导入PyQt6失败: {e}")
    traceback.print_exc()
    HAS_PYQT = False

print("-"*50)

# 只有PyQt6导入成功时才尝试导入自定义组件
if HAS_PYQT:
    try:
        print("尝试导入自定义UI组件...")
        # 导入UI组件
        from status.ui.components import (
            PrimaryButton, SecondaryButton, TextButton, Card, CardHeader, CardContent,
            ProgressBar, ProgressType, Notification, NotificationType, NotificationManager,
            Theme, ThemeType, ColorRole, ThemeManager
        )
        print("UI组件导入成功")
    except ImportError as e:
        logger.error(f"导入UI组件失败: {e}")
        print(f"导入UI组件失败: {e}")
        traceback.print_exc()
        HAS_PYQT = False

class ThemeDemo(QMainWindow):
    """主题演示窗口"""
    
    def __init__(self):
        """初始化主题演示窗口"""
        # 必须有PyQt6才能继续
        if not HAS_PYQT:
            logger.error("PyQt6未安装，无法创建演示窗口")
            raise ImportError("PyQt6未安装，无法创建UI组件")
            
        # 调用父类初始化
        super().__init__()
        
        # 初始化成员变量
        self.theme_manager = None
        self.theme_selector = None
        
        # 初始化UI
        self.init_ui()
        
        # 初始化主题管理器
        try:
            self.theme_manager = ThemeManager.instance()
            print(f"在ThemeDemo中成功获取ThemeManager实例: {self.theme_manager}")
        except Exception as e:
            logger.error(f"在ThemeDemo中获取ThemeManager实例失败: {e}")
            print(f"在ThemeDemo中获取ThemeManager实例失败: {e}")
            raise
        
        # 更新主题选择器
        self.update_theme_selector()
        
        # 注册主题变更监听器
        self.theme_manager.add_theme_listener(self.on_theme_changed)
        
    def init_ui(self):
        """初始化UI"""
        # 设置窗口属性
        self.setWindowTitle("Hollow-ming UI主题演示")
        self.setMinimumSize(1000, 800)
        
        # 创建中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 标题区域
        title_layout = QHBoxLayout()
        title = QLabel("Hollow-ming UI主题演示")
        title.setProperty("heading", "true")
        title.setFixedHeight(50)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(title)
        
        # 主题选择器
        theme_layout = QHBoxLayout()
        theme_label = QLabel("选择主题:")
        self.theme_selector = QComboBox()
        self.theme_selector.currentTextChanged.connect(self.on_theme_selected)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_selector)
        theme_layout.addStretch()
        
        # 添加到主布局
        main_layout.addLayout(title_layout)
        main_layout.addLayout(theme_layout)
        
        # 创建内容区域
        content_layout = QHBoxLayout()
        
        # 左侧区域：基础控件
        left_panel = self.create_basic_widgets_panel()
        
        # 右侧区域：自定义组件
        right_panel = self.create_custom_widgets_panel()
        
        # 添加到内容布局
        content_layout.addWidget(left_panel)
        content_layout.addWidget(right_panel)
        
        # 添加到主布局
        main_layout.addLayout(content_layout)
        
        # 状态栏
        self.statusBar().showMessage("主题演示程序已启动")
        
    def create_basic_widgets_panel(self):
        """创建基础控件面板"""
        # 创建分组框
        group_box = QGroupBox("基础控件")
        layout = QVBoxLayout(group_box)
        
        # 按钮部分
        buttons_group = QGroupBox("按钮")
        buttons_layout = QVBoxLayout(buttons_group)
        
        # 普通按钮
        buttons_row1 = QHBoxLayout()
        normal_button = QPushButton("普通按钮")
        disabled_button = QPushButton("禁用按钮")
        disabled_button.setEnabled(False)
        
        buttons_row1.addWidget(normal_button)
        buttons_row1.addWidget(disabled_button)
        buttons_layout.addLayout(buttons_row1)
        
        # 次要按钮
        buttons_row2 = QHBoxLayout()
        secondary_button = QPushButton("次要按钮")
        secondary_button.setProperty("class", "secondary")
        flat_button = QPushButton("扁平按钮")
        flat_button.setFlat(True)
        
        buttons_row2.addWidget(secondary_button)
        buttons_row2.addWidget(flat_button)
        buttons_layout.addLayout(buttons_row2)
        
        # 输入部分
        inputs_group = QGroupBox("输入控件")
        inputs_layout = QVBoxLayout(inputs_group)
        
        # 文本输入框
        text_input = QLineEdit()
        text_input.setPlaceholderText("请输入文本...")
        inputs_layout.addWidget(text_input)
        
        # 禁用的输入框
        disabled_input = QLineEdit()
        disabled_input.setPlaceholderText("禁用的输入框")
        disabled_input.setEnabled(False)
        inputs_layout.addWidget(disabled_input)
        
        # 文本区域
        text_area = QTextEdit()
        text_area.setPlaceholderText("多行文本区域...")
        text_area.setMaximumHeight(100)
        inputs_layout.addWidget(text_area)
        
        # 选择器部分
        selectors_group = QGroupBox("选择器")
        selectors_layout = QVBoxLayout(selectors_group)
        
        # 复选框
        checkboxes_layout = QHBoxLayout()
        checkbox1 = QCheckBox("选项一")
        checkbox2 = QCheckBox("选项二")
        checkbox2.setChecked(True)
        checkboxes_layout.addWidget(checkbox1)
        checkboxes_layout.addWidget(checkbox2)
        selectors_layout.addLayout(checkboxes_layout)
        
        # 单选按钮
        radio_layout = QHBoxLayout()
        radio1 = QRadioButton("单选项一")
        radio2 = QRadioButton("单选项二")
        radio1.setChecked(True)
        radio_layout.addWidget(radio1)
        radio_layout.addWidget(radio2)
        selectors_layout.addLayout(radio_layout)
        
        # 下拉框
        combo = QComboBox()
        combo.addItems(["选项 1", "选项 2", "选项 3"])
        selectors_layout.addWidget(combo)
        
        # 滑块和进度条
        indicators_group = QGroupBox("指示器")
        indicators_layout = QVBoxLayout(indicators_group)
        
        # 滑块
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(40)
        indicators_layout.addWidget(slider)
        
        # 进度条
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(70)
        indicators_layout.addWidget(progress)
        
        # 添加所有部分到布局
        layout.addWidget(buttons_group)
        layout.addWidget(inputs_group)
        layout.addWidget(selectors_group)
        layout.addWidget(indicators_group)
        layout.addStretch()
        
        return group_box
        
    def create_custom_widgets_panel(self):
        """创建自定义组件面板"""
        # 创建分组框
        group_box = QGroupBox("自定义组件")
        layout = QVBoxLayout(group_box)
        
        # 自定义按钮部分
        custom_buttons_group = QGroupBox("自定义按钮")
        custom_buttons_layout = QVBoxLayout(custom_buttons_group)
        
        # 主要按钮和次要按钮
        buttons_row = QHBoxLayout()
        primary_btn = PrimaryButton("主要按钮")
        secondary_btn = SecondaryButton("次要按钮")
        buttons_row.addWidget(primary_btn)
        buttons_row.addWidget(secondary_btn)
        custom_buttons_layout.addLayout(buttons_row)
        
        # 卡片部分
        cards_group = QGroupBox("卡片组件")
        cards_layout = QVBoxLayout(cards_group)
        
        # 创建卡片1
        card1 = Card()
        card1_layout = QVBoxLayout(card1)
        card1_header = CardHeader("信息卡片")
        card1_content = CardContent()
        card1_content_layout = QVBoxLayout(card1_content)
        card1_text = QLabel("这是一个信息卡片的内容示例，展示了卡片组件的基本用法。")
        card1_text.setWordWrap(True)
        card1_content_layout.addWidget(card1_text)
        card1_layout.addWidget(card1_header)
        card1_layout.addWidget(card1_content)
        cards_layout.addWidget(card1)
        
        # 创建卡片2
        card2 = Card()
        card2_layout = QVBoxLayout(card2)
        card2_header = CardHeader("操作卡片")
        card2_content = CardContent()
        card2_content_layout = QVBoxLayout(card2_content)
        card2_text = QLabel("这是一个带有操作按钮的卡片示例。")
        card2_text.setWordWrap(True)
        card2_button = PrimaryButton("执行操作")
        card2_content_layout.addWidget(card2_text)
        card2_content_layout.addWidget(card2_button)
        card2_layout.addWidget(card2_header)
        card2_layout.addWidget(card2_content)
        cards_layout.addWidget(card2)
        
        # 进度指示器部分
        progress_group = QGroupBox("进度指示器")
        progress_layout = QVBoxLayout(progress_group)
        
        # 标准进度条
        std_progress = ProgressBar()
        std_progress.setValue(60)
        progress_layout.addWidget(std_progress)
        
        # 进行中的进度条
        indeterminate_progress = ProgressBar()
        indeterminate_progress.setType(ProgressType.INDETERMINATE)
        progress_layout.addWidget(indeterminate_progress)
        
        # 通知部分
        notifications_group = QGroupBox("通知")
        notifications_layout = QVBoxLayout(notifications_group)
        
        # 通知按钮
        notify_layout = QHBoxLayout()
        info_btn = QPushButton("信息通知")
        info_btn.clicked.connect(lambda: self.show_notification(NotificationType.INFO))
        success_btn = QPushButton("成功通知")
        success_btn.clicked.connect(lambda: self.show_notification(NotificationType.SUCCESS))
        notify_layout.addWidget(info_btn)
        notify_layout.addWidget(success_btn)
        
        notify_layout2 = QHBoxLayout()
        warning_btn = QPushButton("警告通知")
        warning_btn.clicked.connect(lambda: self.show_notification(NotificationType.WARNING))
        error_btn = QPushButton("错误通知")
        error_btn.clicked.connect(lambda: self.show_notification(NotificationType.ERROR))
        notify_layout2.addWidget(warning_btn)
        notify_layout2.addWidget(error_btn)
        
        notifications_layout.addLayout(notify_layout)
        notifications_layout.addLayout(notify_layout2)
        
        # 添加所有部分到布局
        layout.addWidget(custom_buttons_group)
        layout.addWidget(cards_group)
        layout.addWidget(progress_group)
        layout.addWidget(notifications_group)
        layout.addStretch()
        
        return group_box
    
    def update_theme_selector(self):
        """更新主题选择器"""
        if not self.theme_manager:
            return
            
        # 获取可用主题
        themes = self.theme_manager.get_available_themes()
        
        # 清空并添加主题
        self.theme_selector.clear()
        self.theme_selector.addItems(themes)
        
        # 选择当前主题
        current_theme = self.theme_manager.get_current_theme()
        if current_theme:
            self.theme_selector.setCurrentText(current_theme.name)
    
    def on_theme_selected(self, theme_name):
        """主题选择响应"""
        if not self.theme_manager:
            return
            
        # 设置所选主题
        self.theme_manager.set_theme(theme_name)
    
    def on_theme_changed(self, theme):
        """主题变更响应"""
        # 显示主题变更通知
        self.statusBar().showMessage(f"已切换到主题: {theme.name}")
    
    def show_notification(self, notification_type):
        """显示通知"""
        title_map = {
            NotificationType.INFO: "信息通知",
            NotificationType.SUCCESS: "成功通知",
            NotificationType.WARNING: "警告通知",
            NotificationType.ERROR: "错误通知"
        }
        
        message_map = {
            NotificationType.INFO: "这是一条信息通知，提供一般性信息。",
            NotificationType.SUCCESS: "操作已成功完成！",
            NotificationType.WARNING: "请注意，这是一个警告提示。",
            NotificationType.ERROR: "发生错误，无法完成操作。"
        }
        
        # 创建并显示通知
        notification = Notification(
            title=title_map.get(notification_type, "通知"),
            message=message_map.get(notification_type, "通知内容"),
            notification_type=notification_type
        )
        
        # 获取通知管理器并显示通知
        NotificationManager.instance().show(notification)

def main():
    """程序入口"""
    print("="*50)
    print("进入main函数")
    print("="*50)
    
    # 检查PyQt6是否可用
    if not HAS_PYQT:
        logger.error("PyQt6未安装或导入组件失败，无法运行演示程序")
        print("错误: 请确保PyQt6库已正确安装，且所有必要的UI组件都已实现")
        return 1
    
    # 详细的调试输出
    print("导入调试信息:")
    print(f"PyQt6已成功导入: {HAS_PYQT}")
    
    # 单独调试每个重要模块
    try:
        import status.ui.components
        print("成功导入status.ui.components模块")
    except ImportError as e:
        print(f"导入status.ui.components模块失败: {e}")
        traceback.print_exc()
        return 1
    
    try:
        from status.ui.components.theme import ThemeManager
        print("成功导入ThemeManager类")
    except ImportError as e:
        print(f"导入ThemeManager类失败: {e}")
        traceback.print_exc()
        return 1
    
    # 检查theme.py是否存在
    theme_path = os.path.join(os.path.dirname(__file__), "../components/theme.py")
    if os.path.exists(theme_path):
        print(f"theme.py文件存在于: {theme_path}")
    else:
        print(f"theme.py文件不存在: {theme_path}")
        
    # 创建应用程序
    print("-"*50)
    print("创建QApplication实例")
    try:
        app = QApplication(sys.argv)
        print("QApplication创建成功")
    except Exception as e:
        print(f"创建QApplication失败: {e}")
        traceback.print_exc()
        return 1
    
    # 初始化主题管理器
    print("尝试创建ThemeManager实例")
    try:
        theme_manager = ThemeManager.instance()
        print(f"成功创建ThemeManager实例: {theme_manager}")
    except Exception as e:
        print(f"创建ThemeManager实例失败: {e}")
        traceback.print_exc()
        return 1
    
    # 创建并显示主窗口
    print("尝试创建ThemeDemo实例")
    try:
        window = ThemeDemo()
        print("成功创建ThemeDemo实例，准备显示窗口")
        window.show()
    except Exception as e:
        print(f"创建或显示ThemeDemo实例失败: {e}")
        traceback.print_exc()
        return 1
    
    print("启动应用程序主循环")
    try:
        return app.exec()
    except Exception as e:
        print(f"执行应用程序主循环时发生错误: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        print(f"程序退出，退出码: {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        print(f"主程序发生错误: {e}")
        traceback.print_exc()
        sys.exit(1) 