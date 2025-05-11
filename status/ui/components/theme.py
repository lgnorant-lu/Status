"""
---------------------------------------------------------------
File name:                  theme.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                UI主题管理系统
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

import logging
import json
import os
from typing import Dict, Any, Optional, List, Callable
from enum import Enum

from PySide6.QtCore import Qt, QObject, Signal, QFile, QTextStream
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QWidget

logger = logging.getLogger(__name__)

class ThemeType(str, Enum):
    """主题类型枚举"""
    DARK = "dark"      # 深色主题（默认）
    LIGHT = "light"    # 浅色主题

class ColorRole(str, Enum):
    """颜色角色枚举"""
    # 基础颜色
    BACKGROUND = "background"                # 背景色
    SURFACE = "surface"                      # 表面色
    PRIMARY = "primary"                      # 主要强调色
    SECONDARY = "secondary"                  # 次要强调色
    TEXT_PRIMARY = "text_primary"            # 主要文本色
    TEXT_SECONDARY = "text_secondary"        # 次要文本色
    BORDER = "border"                        # 边框色
    
    # 状态颜色
    SUCCESS = "success"                      # 成功色
    WARNING = "warning"                      # 警告色
    ERROR = "error"                          # 错误色
    INFO = "info"                            # 信息色
    
    # 特殊颜色
    SHADOW = "shadow"                        # 阴影色
    OVERLAY = "overlay"                      # 遮罩色

class Theme:
    """主题定义类"""
    
    def __init__(self, 
                 name: str,
                 type: ThemeType,
                 colors: Dict[str, str],
                 description: str = ""):
        """
        初始化主题
        
        Args:
            name: 主题名称
            type: 主题类型
            colors: 颜色定义字典
            description: 主题描述
        """
        self.name = name
        self.type = type
        self.colors = colors
        self.description = description
        
    def get_color(self, role: ColorRole) -> str:
        """获取特定角色的颜色"""
        return self.colors.get(role, "#000000")
    
    def get_qcolor(self, role: ColorRole) -> QColor:
        """获取特定角色的QColor对象"""
        return QColor(self.get_color(role))
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Theme':
        """从字典创建主题"""
        return cls(
            name=data.get("name", "Custom Theme"),
            type=ThemeType(data.get("type", ThemeType.DARK)),
            colors=data.get("colors", {}),
            description=data.get("description", "")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "type": self.type,
            "colors": self.colors,
            "description": self.description
        }
    
    @classmethod
    def from_json(cls, json_data: str) -> 'Theme':
        """从JSON字符串创建主题"""
        try:
            data = json.loads(json_data)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            logger.error(f"解析JSON失败: {e}")
            return cls.dark_theme()  # 返回默认深色主题
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    @classmethod
    def dark_theme(cls) -> 'Theme':
        """创建默认深色主题"""
        return cls(
            name="Hollow Dark",
            type=ThemeType.DARK,
            colors={
                ColorRole.BACKGROUND: "#121212",
                ColorRole.SURFACE: "#1E1E1E",
                ColorRole.PRIMARY: "#1A6E8E",
                ColorRole.SECONDARY: "#F1CA74",
                ColorRole.TEXT_PRIMARY: "#E6E6E6",
                ColorRole.TEXT_SECONDARY: "#AAAAAA",
                ColorRole.BORDER: "#333333",
                ColorRole.SUCCESS: "#2D8C46",
                ColorRole.WARNING: "#D89C00",
                ColorRole.ERROR: "#9E2B25",
                ColorRole.INFO: "#1A6E8E",
                ColorRole.SHADOW: "rgba(0, 0, 0, 0.5)",
                ColorRole.OVERLAY: "rgba(18, 18, 18, 0.8)"
            },
            description="默认深色主题，基于Status桌面宠物应用设计风格"
        )
    
    @classmethod
    def light_theme(cls) -> 'Theme':
        """创建默认浅色主题"""
        return cls(
            name="Hollow Light",
            type=ThemeType.LIGHT,
            colors={
                ColorRole.BACKGROUND: "#F5F5F5",
                ColorRole.SURFACE: "#FFFFFF",
                ColorRole.PRIMARY: "#0F5A75",
                ColorRole.SECONDARY: "#D5A930",
                ColorRole.TEXT_PRIMARY: "#202020",
                ColorRole.TEXT_SECONDARY: "#606060",
                ColorRole.BORDER: "#DDDDDD",
                ColorRole.SUCCESS: "#1E7837",
                ColorRole.WARNING: "#C27D00",
                ColorRole.ERROR: "#C1261E",
                ColorRole.INFO: "#0F5A75",
                ColorRole.SHADOW: "rgba(0, 0, 0, 0.2)",
                ColorRole.OVERLAY: "rgba(245, 245, 245, 0.8)"
            },
            description="浅色主题，基于Status桌面宠物应用设计风格的明亮版本"
        )

class ThemeManager(QObject):
    """主题管理器，管理主题切换和应用"""
    
    theme_changed = Signal(Theme)  # 主题变更信号
    
    _instance = None  # 单例实例
    
    @classmethod
    def instance(cls) -> 'ThemeManager':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """初始化主题管理器"""
        # 只在有PySide6时调用super().__init__()
        super().__init__()
        
        # 检查是否已有实例
        if ThemeManager._instance is not None:
            logger.warning("ThemeManager是单例类，应使用instance()方法获取实例")
            return
            
        # 保存为单例实例
        ThemeManager._instance = self
        
        # 初始化主题
        self._themes: Dict[str, Theme] = {}
        self._current_theme: Optional[Theme] = None
        self._theme_listeners: List[Callable[[Theme], None]] = []
        
        # 添加默认主题
        try:
            self.register_theme(Theme.dark_theme())
            self.register_theme(Theme.light_theme())
            
            # 设置默认主题
            self.set_theme("Hollow Dark")
        except Exception as e:
            logger.error(f"初始化主题失败: {e}")
            import traceback
            traceback.print_exc()
    
    def register_theme(self, theme: Theme) -> bool:
        """注册主题"""
        if theme.name in self._themes:
            logger.warning(f"主题'{theme.name}'已存在，将被覆盖")
            
        self._themes[theme.name] = theme
        return True
    
    def get_theme(self, name: str) -> Optional[Theme]:
        """获取主题"""
        return self._themes.get(name)
    
    def get_current_theme(self) -> Optional[Theme]:
        """获取当前主题"""
        return self._current_theme
    
    def get_available_themes(self) -> List[str]:
        """获取所有可用主题名称"""
        return list(self._themes.keys())
    
    def set_theme(self, name: str) -> bool:
        """设置当前主题"""
        if name not in self._themes:
            logger.error(f"主题'{name}'不存在")
            return False
            
        self._current_theme = self._themes[name]
        
        # 生成并应用样式表
        self._apply_theme_to_application()
        
        # 发射主题变更信号
        self.theme_changed.emit(self._current_theme)
        
        # 通知所有监听器
        for listener in self._theme_listeners:
            listener(self._current_theme)
            
        return True
    
    def add_theme_listener(self, listener: Callable[[Theme], None]):
        """添加主题变更监听器"""
        if listener not in self._theme_listeners:
            self._theme_listeners.append(listener)
    
    def remove_theme_listener(self, listener: Callable[[Theme], None]):
        """移除主题变更监听器"""
        if listener in self._theme_listeners:
            self._theme_listeners.remove(listener)
    
    def _apply_theme_to_application(self):
        """将当前主题应用到应用程序的样式和调色板"""
        app = QApplication.instance()
        if not isinstance(app, QApplication):
            logger.warning("QApplication 实例无效或非 QApplication 类型，无法应用主题。")
            return

        # 生成并应用样式表
        stylesheet = self._generate_stylesheet()
        app.setStyleSheet(stylesheet)
        
        # 生成并应用调色板
        palette = self._generate_palette()
        app.setPalette(palette)
    
    def _generate_stylesheet(self) -> str:
        """生成样式表"""
        current_theme = self.get_current_theme()
        
        if not current_theme:
            logger.warning("当前主题未设置，无法生成样式表，将返回默认样式表。")
            return self._generate_default_stylesheet()

        # 基础 CSS
        base_css = f"""
        /* 生成的默认样式表 */
        QWidget {{
            background-color: {current_theme.get_color(ColorRole.BACKGROUND)};
            color: {current_theme.get_color(ColorRole.TEXT_PRIMARY)};
        }}
        
        QPushButton {{
            background-color: {current_theme.get_color(ColorRole.PRIMARY)};
            color: {current_theme.get_color(ColorRole.TEXT_PRIMARY)};
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
        }}
        
        QPushButton:hover {{
            background-color: {self._adjust_color(current_theme.get_color(ColorRole.PRIMARY), 15)};
        }}
        
        QPushButton:pressed {{
            background-color: {self._adjust_color(current_theme.get_color(ColorRole.PRIMARY), -15)};
        }}
        
        QLineEdit {{
            background-color: {current_theme.get_color(ColorRole.SURFACE)};
            color: {current_theme.get_color(ColorRole.TEXT_PRIMARY)};
            border: 1px solid {current_theme.get_color(ColorRole.BORDER)};
            border-radius: 4px;
            padding: 4px 8px;
        }}
        
        QLabel {{
            color: {current_theme.get_color(ColorRole.TEXT_PRIMARY)};
        }}
        """
        
        qss_file_path = ""
        # 尝试加载特定主题的QSS文件
        try:
            css_path = self._get_theme_css_path(current_theme.type)
            if css_path and os.path.exists(css_path):
                qss_file_path = css_path
        except Exception as e:
            logger.warning(f"获取主题 specific QSS路径失败: {e}, 将使用默认样式")

        if qss_file_path:
            # 读取主题CSS模板
            try:
                with open(qss_file_path, 'r', encoding='utf-8') as f:
                    css_template = f.read()
                    
                # 替换颜色变量
                for role in ColorRole:
                    placeholder = f"${{color.{role}}}"
                    css_template = css_template.replace(placeholder, current_theme.get_color(role))
                    
                return css_template
            except Exception as e:
                logger.error(f"读取主题CSS模板失败: {e}")
                return self._generate_default_stylesheet()
        else:
            return self._generate_default_stylesheet()
    
    def _get_theme_css_path(self, theme_type: ThemeType) -> str:
        """获取主题CSS模板路径"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        css_dir = os.path.join(base_dir, "styles")
        
        if theme_type == ThemeType.DARK:
            return os.path.join(css_dir, "dark_theme.css")
        else:
            return os.path.join(css_dir, "light_theme.css")
    
    def _generate_default_stylesheet(self) -> str:
        """生成一个非常基础的默认QSS样式表，不依赖当前主题对象"""
        # 定义一些绝对的默认颜色值，以防万一主题加载完全失败
        default_bg_color = "#2B2B2B"       # 深灰背景
        default_text_color = "#D3D3D3"    # 浅灰文本
        default_primary_color = "#007ACC" # 蓝色强调
        default_surface_color = "#3C3C3C"
        default_border_color = "#555555"

        return f"""
        QWidget {{
            background-color: {default_bg_color};
            color: {default_text_color};
        }}
        
        QPushButton {{
            background-color: {default_primary_color};
            color: {default_text_color};
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
        }}
        
        QPushButton:hover {{
            background-color: #4A90E2; /* 比 primary 亮一点 */
        }}
        
        QPushButton:pressed {{
            background-color: #005C99; /* 比 primary 暗一点 */
        }}
        
        QLineEdit {{
            background-color: {default_surface_color};
            color: {default_text_color};
            border: 1px solid {default_border_color};
            border-radius: 4px;
            padding: 4px 8px;
        }}
        
        QLabel {{
            color: {default_text_color};
        }}
        """
    
    _qt_color_role_map: Dict[ColorRole, QPalette.ColorRole] = {
        ColorRole.BACKGROUND: QPalette.ColorRole.Window,
        ColorRole.SURFACE: QPalette.ColorRole.Base,
        ColorRole.PRIMARY: QPalette.ColorRole.Highlight,
        ColorRole.SECONDARY: QPalette.ColorRole.ToolTipBase, # 只是一个近似值
        ColorRole.TEXT_PRIMARY: QPalette.ColorRole.WindowText,
        ColorRole.TEXT_SECONDARY: QPalette.ColorRole.ToolTipText, # 只是一个近似值
        ColorRole.BORDER: QPalette.ColorRole.Shadow, # 近似值
        ColorRole.SUCCESS: QPalette.ColorRole.Highlight, # 可能需要更具体的，但用Highlight暂代
        ColorRole.WARNING: QPalette.ColorRole.HighlightedText, # Warning 通常是亮色背景上的暗色文字
        ColorRole.ERROR: QPalette.ColorRole.Dark, # Error 通常是深色，或用红色强调
        ColorRole.INFO: QPalette.ColorRole.Link, # Info 可以用Link颜色
        # SHADOW 和 OVERLAY 没有直接的 QPalette.ColorRole 对应, 通常通过样式表处理
    }

    def _generate_palette(self) -> QPalette:
        """生成调色板"""
        palette = QPalette()
        theme = self.get_current_theme()
        
        if not theme: # 如果主题为 None，返回默认调色板
            logger.warning("当前主题未设置，返回默认QPalette。")
            return palette # 返回一个空的或者预设的默认QPalette

        assert isinstance(theme, Theme), "Theme object should not be None here"

        for app_role, qt_role in self._qt_color_role_map.items():
            qcolor = theme.get_qcolor(app_role) # theme 在这里已经被确认不是 None
            if qcolor: # 确保 qcolor 也不是 None (虽然 get_qcolor 正常应返回有效 QColor)
                palette.setColor(qt_role, qcolor)
            else:
                logger.debug(f"角色 {app_role.value} 的 QColor 未能生成，跳过设置此调色板颜色。")
        
        # 例如，确保按钮等控件的颜色与主题协调
        if theme.colors.get(ColorRole.PRIMARY.value) is not None:
            palette.setColor(QPalette.ColorRole.Button, theme.get_qcolor(ColorRole.PRIMARY))
        if theme.colors.get(ColorRole.TEXT_PRIMARY.value) is not None:
            palette.setColor(QPalette.ColorRole.ButtonText, theme.get_qcolor(ColorRole.TEXT_PRIMARY))
            palette.setColor(QPalette.ColorRole.Text, theme.get_qcolor(ColorRole.TEXT_PRIMARY))

        return palette
    
    def _adjust_color(self, color: str, amount: int) -> str:
        """调整颜色亮度"""
        # 创建QColor
        qcolor = QColor(color)
        return self._adjust_qcolor(qcolor, amount).name()
    
    def _adjust_qcolor(self, color: QColor, amount: int) -> QColor:
        """调整QColor亮度"""
        h, s, l, a = color.getHsl()
        
        # 调整亮度
        l = max(0, min(255, l + amount))
        
        # 创建新颜色
        new_color = QColor()
        new_color.setHsl(h, s, l, a)
        return new_color
    
    def load_theme_from_file(self, filepath: str) -> bool:
        """从文件加载主题"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                theme_data = f.read()
                
            theme = Theme.from_json(theme_data)
            self.register_theme(theme)
            return True
        except Exception as e:
            logger.error(f"从文件加载主题失败: {e}")
            return False
    
    def save_theme_to_file(self, theme_name: str, filepath: str) -> bool:
        """将主题保存到文件"""
        theme = self.get_theme(theme_name)
        if not theme:
            logger.error(f"主题'{theme_name}'不存在")
            return False
            
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(theme.to_json())
            return True
        except Exception as e:
            logger.error(f"保存主题到文件失败: {e}")
            return False

def apply_stylesheet(widget: QWidget, stylesheet: str):
    """应用样式表到单个组件"""
    widget.setStyleSheet(stylesheet)

def apply_theme_to_widget(widget: QWidget, theme: Optional[Theme] = None):
    """将当前主题应用到组件"""
    # 获取主题
    if theme is None:
        theme_manager = ThemeManager.instance()
        theme = theme_manager.get_current_theme()
        
    if not theme:
        logger.error("无法获取当前主题")
        return
        
    # 创建组件样式表
    stylesheet = f"""
    QWidget {{
        background-color: {theme.get_color(ColorRole.BACKGROUND)};
        color: {theme.get_color(ColorRole.TEXT_PRIMARY)};
    }}
    
    QPushButton {{
        background-color: {theme.get_color(ColorRole.PRIMARY)};
        color: {theme.get_color(ColorRole.TEXT_PRIMARY)};
    }}
    
    QLabel {{
        color: {theme.get_color(ColorRole.TEXT_PRIMARY)};
    }}
    """
    
    # 应用样式表
    widget.setStyleSheet(stylesheet) 