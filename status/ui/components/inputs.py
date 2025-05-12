"""
---------------------------------------------------------------
File name:                  inputs.py
Author:                     Ignorant-lu
Date created:               2025/04/10
Description:                UI输入组件
----------------------------------------------------------------

Changed history:            
                            2025/04/10: 初始创建;
                            2025/05/16: 修复参数类型注解;
                            2025/05/19: 修复信号定义，从pyqtSignal改为Signal;
----
"""

import logging
from typing import Optional, List, Union, Dict, Any, Callable, Tuple, cast

from PySide6.QtCore import Qt, Signal, QSize, QMargins, QTimer, QEvent, QRegularExpression
from PySide6.QtGui import (
    QColor, QIcon, QFont, QFontMetrics, QCursor, QValidator, 
    QAction, QRegularExpressionValidator, QIntValidator, QDoubleValidator
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTextEdit, QPushButton, QToolButton, QMenu, QStyle,
    QCompleter, QComboBox, QScrollArea, QFrame, QCheckBox, QRadioButton
)

logger = logging.getLogger(__name__)

# 输入框样式定义
INPUT_STYLE = """
/* 基本输入框样式 */
QLineEdit {
    background-color: #1D1D1D;
    color: #E6E6E6;
    border: 1px solid #3D3D3D;
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 14px;
}

QLineEdit:hover {
    border: 1px solid #5D5D5D;
}

QLineEdit:focus {
    border: 1px solid #1A6E8E;
}

QLineEdit:disabled {
    background-color: #252525;
    color: #808080;
    border: 1px solid #3D3D3D;
}

QLineEdit[error="true"] {
    border: 1px solid #9E2B25;
}

/* 搜索框样式 */
QLineEdit.search {
    padding-left: 30px;
    background-position: 8px center;
    background-repeat: no-repeat;
}
"""

class BaseInputField(QWidget):
    """基础输入字段组件，为所有输入类型提供共享功能"""
    
    valueChanged = Signal(str)  # 值变化信号 (Reverted to str)
    
    def __init__(self, 
                 label: str = "", 
                 placeholder: str = "",
                 parent: Optional[QWidget] = None,
                 on_change: Optional[Callable[[str], None]] = None, # Reverted to str
                 required: bool = False,
                 helper_text: str = "",
                 error_text: str = "",
                 initial_value: str = ""): # Reverted to str
        """
        初始化输入字段
        
        Args:
            label: 输入框标签
            placeholder: 输入框占位符
            parent: 父组件
            on_change: 值变化回调
            required: 是否必填
            helper_text: 帮助文本
            error_text: 错误文本
            initial_value: 初始值
        """
        super().__init__(parent)
        
        self._label_text = label # Store label text
        self._show_label = bool(label)
        self._placeholder = placeholder
        self._required = required
        self._helper_text = helper_text
        self._error_text = error_text
        self._has_error = False
        self._input: Optional[Union[QLineEdit, QTextEdit]] = None # 明确指定输入控件类型
        self._layout: Optional[Union[QVBoxLayout, QHBoxLayout]] = None # Layout type can vary

        self._setup_ui() # Call UI setup

        # Set initial value after UI setup
        if initial_value:
            self.setValue(initial_value)

        # Connect signals
        # Connections need to be done in subclasses based on _input type
        if on_change:
            self.valueChanged.connect(on_change)
    
    def _setup_ui(self):
        """Setup the basic UI structure (Label, Input placeholder, Message)."""
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)

        self.label: Optional[QLabel] = None
        if self._show_label:
            self.label = QLabel(self._label_text)
            if self._required:
                self.label.setText(f"{self._label_text} *")
            self._layout.addWidget(self.label)

        # Subclasses MUST create self._input here
        self._setup_input_widget() # Call subclass implementation

        self._message_label = QLabel(self._helper_text, self)
        self._message_label.setStyleSheet("color: #808080; font-size: 12px;")
        self._layout.addWidget(self._message_label)
        self._message_label.setVisible(bool(self._helper_text) and not self._has_error)

    def _setup_input_widget(self):
        """Subclasses must implement this to create self._input."""
        # Example: self._input = QLineEdit(self)
        #          self._input.setPlaceholderText(self._placeholder)
        #          self._input.textChanged.connect(self._on_text_changed)
        #          self._layout.insertWidget(1, self._input) # Insert after label
        raise NotImplementedError("_setup_input_widget must be implemented by subclasses")

    def _on_text_changed(self, text: str):
        """当文本变化时处理"""
        if self._has_error:
            self.clearError()
        self.valueChanged.emit(text)

    def value(self) -> str:
        """获取字段值 (基类期望子类实现)"""
        if self._input is not None and hasattr(self._input, 'text'):
            # This is potentially unsafe, relies on subclass setting QLineEdit
            if isinstance(self._input, QLineEdit):
                return self._input.text()
        elif self._input is not None and hasattr(self._input, 'toPlainText'):
            if isinstance(self._input, QTextEdit):
                return self._input.toPlainText()
        logger.warning("BaseInputField.value() called but _input type is unknown or lacks text retrieval method.")
        return ""

    def setValue(self, value: str) -> None:
        """设置字段值 (基类期望子类实现)"""
        if self._input is not None:
            # 先检查是否是QLineEdit类型
            if isinstance(self._input, QLineEdit):
                self._input.setText(value)
                return
            # 再检查是否是QTextEdit类型
            elif isinstance(self._input, QTextEdit):
                self._input.setPlainText(value)
                return
        logger.warning("BaseInputField.setValue() called but _input type is unknown or lacks text setting method.")

    def setError(self, error_text: str = "") -> None:
        """设置错误状态"""
        self._has_error = True
        text = error_text if error_text else self._error_text or "输入无效"

        if self._input is not None:
            self._input.setProperty("error", "true")
            style = self._input.style()
            if style is not None:
                style.unpolish(self._input)
                style.polish(self._input)

        self._message_label.setText(text)
        self._message_label.setStyleSheet("color: #9E2B25; font-size: 12px;")
        self._message_label.setVisible(True)

    def clearError(self) -> None:
        """清除错误状态"""
        if not self._has_error: return # Avoid unnecessary repolishing
        self._has_error = False

        if self._input is not None:
            self._input.setProperty("error", "false")
            style = self._input.style()
            if style is not None:
                style.unpolish(self._input)
                style.polish(self._input)

        if self._helper_text:
            self._message_label.setText(self._helper_text)
            self._message_label.setStyleSheet("color: #808080; font-size: 12px;")
            self._message_label.setVisible(True)
        else:
            self._message_label.setVisible(False)

    def hasError(self) -> bool:
        """检查是否有错误"""
        return self._has_error

    def setPlaceholder(self, text: str) -> None:
        """设置占位符文本"""
        self._placeholder = text # Store it
        if self._input is not None and hasattr(self._input, 'setPlaceholderText'):
            self._input.setPlaceholderText(text)

    def setRequired(self, required: bool) -> None:
        """设置是否必填"""
        self._required = required
        if self.label: # Check if label exists
            text = self._label_text # Use stored text
            self.label.setText(f"{text} *" if required else text)

    def isRequired(self) -> bool:
        """检查是否必填"""
        return self._required

    def isValid(self) -> bool:
        """验证输入是否有效 (基类只检查必填)"""
        if self._required and not self.value().strip():
            self.setError("此字段为必填项")
            return False
        # Subclasses should override for more specific validation
        # If no error set previously, assume valid for base class
        if not self._has_error:
            self.clearError() # Ensure helper text is shown if valid
            return True
        return False # Invalid if error was set previously

    def setEnabled(self, enabled: bool) -> None:
        """设置启用状态"""
        super().setEnabled(enabled)
        if self._input:
            self._input.setEnabled(enabled)
        if self.label:
            self.label.setEnabled(enabled)
        if self._message_label:
            # Keep message visible but maybe dimmed if needed?
            self._message_label.setEnabled(enabled)

    def setHelper(self, text: str) -> None:
        """设置帮助文本"""
        self._helper_text = text
        if not self._has_error:
            self._message_label.setText(text)
            self._message_label.setVisible(bool(text))

    def setStyle(self, style: Optional[QStyle]) -> None:
        """设置控件样式 (Reverted logic)"""
        current_style = self.style()
        if current_style is not None:
            current_style.unpolish(self)
            # Added check before unpolishing _input
            if self._input is not None:
                current_style.unpolish(self._input)

        # Check style is not None before passing to base class
        if style is not None:
            super().setStyle(style)
            style.polish(self)
            # Added check before polishing _input
            if self._input is not None:
                style.polish(self._input)
        else:
            # When style is None, don't call superclass method
            pass  # Skip calling super().setStyle(None)

class TextField(BaseInputField):
    """文本输入字段"""
    
    def __init__(self, 
                 label: str = "", 
                 placeholder: str = "",
                 parent: Optional[QWidget] = None,
                 on_change: Optional[Callable[[str], None]] = None,
                 required: bool = False,
                 helper_text: str = "",
                 error_text: str = "",
                 initial_value: str = "",
                 max_length: int = 0,
                 password: bool = False):
        """
        初始化文本输入字段
        
        Args:
            label: 输入框标签
            placeholder: 输入框占位符
            parent: 父组件
            on_change: 值变化回调
            required: 是否必填
            helper_text: 帮助文本
            error_text: 错误文本
            initial_value: 初始值
            max_length: 最大字符数（0表示无限制）
            password: 是否为密码输入
        """
        super().__init__(
            label, placeholder, parent, on_change, 
            required, helper_text, error_text, initial_value
        )
        
        # 设置最大长度（如果指定）
        if max_length > 0 and self._input is not None and isinstance(self._input, QLineEdit):
            self._input.setMaxLength(max_length)
            
        # 设置密码模式（如果指定）
        if password and self._input is not None and isinstance(self._input, QLineEdit):
            self._input.setEchoMode(QLineEdit.EchoMode.Password)
        
    def _setup_input_widget(self) -> None:
        """创建输入控件"""
        self._input = QLineEdit(self)
        
        if self._input is not None:
            # 设置占位符和连接信号
            self._input.setPlaceholderText(self._placeholder)
            self._input.textChanged.connect(self._on_text_changed)
            
            # 将输入框添加到布局中
            if self._layout is not None:
                self._layout.insertWidget(1, self._input)
        
    def value(self) -> str:
        """获取当前值"""
        if self._input is not None and isinstance(self._input, QLineEdit):
            return self._input.text()
        return ""
    
    def setValue(self, value: str) -> None:
        """设置当前值"""
        if self._input is not None and isinstance(self._input, QLineEdit):
            self._input.setText(value)
    
    def setError(self, error_text: str = "") -> None:
        """设置错误状态"""
        self._has_error = True
        
        # 使用提供的错误文本或默认错误文本
        text = error_text if error_text else self._error_text or "输入无效"
        
        # 更新样式和消息
        if self._input is not None:
            self._input.setProperty("error", "true")
            style = self._input.style()
            if style is not None:
                style.unpolish(self._input)
                style.polish(self._input)
        
        if self._message_label:
            self._message_label.setText(text)
            self._message_label.setStyleSheet("color: #9E2B25; font-size: 12px;")
            self._message_label.setVisible(True)
        
    def clearError(self) -> None:
        """清除错误状态"""
        if not self._has_error:
            return
            
        self._has_error = False
        
        # 恢复正常样式
        if self._input is not None:
            self._input.setProperty("error", "false")
            style = self._input.style()
            if style is not None:
                style.unpolish(self._input)
                style.polish(self._input)
        
        # 恢复帮助文本（如果有）
        if self._message_label:
            if self._helper_text:
                self._message_label.setText(self._helper_text)
                self._message_label.setStyleSheet("color: #808080; font-size: 12px;")
                self._message_label.setVisible(True)
            else:
                self._message_label.setVisible(False)
                
    def setReadOnly(self, read_only: bool) -> None:
        """设置只读状态"""
        if self._input is not None and isinstance(self._input, QLineEdit):
            self._input.setReadOnly(read_only)

class SearchField(BaseInputField):
    """搜索输入字段"""
    
    def __init__(self, 
                 placeholder: str = "搜索...",
                 parent: Optional[QWidget] = None,
                 on_change: Optional[Callable[[str], None]] = None,
                 on_search: Optional[Callable[[str], None]] = None,
                 suggestions: Optional[List[str]] = None):
        """
        初始化搜索输入字段
        
        Args:
            placeholder: 输入框占位符
            parent: 父组件
            on_change: 值变化回调
            on_search: 搜索提交回调
            suggestions: 搜索建议列表
        """
        super().__init__("", placeholder, parent, on_change, initial_value="")
        
        # 添加搜索图标
        if self._input is not None and isinstance(self._input, QLineEdit):
            self._input.setProperty("class", "search")
            self._input.returnPressed.connect(self._on_search)
            if suggestions:
                self.setSuggestions(suggestions)
        
        self._on_search_callback = on_search
    
    def _setup_input_widget(self) -> None:
        """创建输入控件"""
        self._input = QLineEdit(self)
        
        if self._input is not None:
            # 设置占位符和连接信号
            self._input.setPlaceholderText(self._placeholder)
            self._input.textChanged.connect(self._on_text_changed)
            
            # 将输入框添加到布局中
            if self._layout is not None:
                self._layout.insertWidget(1, self._input)
    
    def _on_search(self) -> None:
        """搜索提交处理"""
        if self._on_search_callback:
            self._on_search_callback(self.value())
            
    def setSuggestions(self, suggestions: List[str]) -> None:
        """设置搜索建议"""
        if self._input is not None and isinstance(self._input, QLineEdit):
            completer = QCompleter(suggestions, self)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self._input.setCompleter(completer)

class NumberField(BaseInputField):
    """数字输入字段"""
    
    valueChanged = Signal(float)  # 重新定义为数值类型信号
    
    def __init__(self, 
                 label: str = "", 
                 placeholder: str = "",
                 parent: Optional[QWidget] = None,
                 on_change: Optional[Callable[[float], None]] = None,
                 required: bool = False,
                 helper_text: str = "",
                 error_text: str = "",
                 initial_value: Union[int, float, str] = "",
                 min_value: Optional[float] = None,
                 max_value: Optional[float] = None,
                 decimals: int = 0):
        """
        初始化数字输入字段
        
        Args:
            label: 输入框标签
            placeholder: 输入框占位符
            parent: 父组件
            on_change: 值变化回调
            required: 是否必填
            helper_text: 帮助文本
            error_text: 错误文本
            initial_value: 初始值
            min_value: 最小值
            max_value: 最大值
            decimals: 小数位数（0表示整数）
        """
        # 预先声明验证器类型
        self._validator: Union[QDoubleValidator, QIntValidator]
        
        # 将数值转换为字符串作为初始值
        if isinstance(initial_value, (int, float)):
            initial_value = str(initial_value)
            
        super().__init__(
            label, placeholder, parent, None,  # 不传递on_change，我们将单独处理
            required, helper_text, error_text, initial_value
        )
        
        # 设置验证器
        if decimals > 0:
            # 浮点数验证器
            self._validator = QDoubleValidator()
            min_val = min_value if min_value is not None else -2147483647.0
            max_val = max_value if max_value is not None else 2147483647.0
            self._validator.setRange(min_val, max_val, decimals)
        else:
            # 整数验证器
            self._validator = QIntValidator()
            min_val = int(min_value) if min_value is not None else -2147483647
            max_val = int(max_value) if max_value is not None else 2147483647
            self._validator.setRange(min_val, max_val)
            
        # 确保_input是QLineEdit类型才设置验证器
        if isinstance(self._input, QLineEdit):
            self._input.setValidator(self._validator)
        
        # 保存范围信息用于验证
        self._min_value = min_value
        self._max_value = max_value
        self._decimals = decimals
        
        # 连接信号
        if isinstance(self._input, QLineEdit):
            self._input.textChanged.connect(self._on_numeric_changed)
        if on_change:
            self.valueChanged.connect(on_change)
            
    def _on_numeric_changed(self, text: str):
        """处理数值变化"""
        # 调用基类方法处理基本文本变化逻辑
        super()._on_text_changed(text)
        
        # 转换为数值并发射数值信号
        if text and text not in ['-', '.', '-.']:
            try:
                value = float(text)
                if self._decimals == 0:
                    value = int(value)
                self.valueChanged.emit(value)
            except ValueError:
                pass  # 忽略无效输入
                
    def value(self) -> str:
        """获取当前数值（作为字符串返回，以符合基类接口）"""
        if self._input is not None and isinstance(self._input, QLineEdit):
            return self._input.text()
        return ""
            
    def get_numeric_value(self) -> Union[int, float, None]:
        """获取当前数值（作为数值类型返回）"""
        if self._input is not None and isinstance(self._input, QLineEdit):
            text = self._input.text()
            if not text:
                return None
                
            try:
                value = float(text)
                return int(value) if self._decimals == 0 else value
            except ValueError:
                return None
        return None
            
    def setValue(self, value: str) -> None:
        """设置当前值（接受字符串，符合基类接口）"""
        if self._input is not None and isinstance(self._input, QLineEdit):
            self._input.setText(value)

    def set_numeric_value(self, value: Union[int, float]) -> None:
        """设置当前数值（接受数值类型）"""
        if self._input is not None and isinstance(self._input, QLineEdit):
            self._input.setText(str(value))

    def isValid(self) -> bool:
        """验证输入是否有效"""
        # 首先调用基类验证
        if not super().isValid():
            return False
            
        # 如果为空且非必填，则有效
        if self._input is None:
            return not self._required
            
        text = ""
        if isinstance(self._input, QLineEdit):
            text = self._input.text()
        elif isinstance(self._input, QTextEdit):
            text = self._input.toPlainText()
            
        if not text:
            return not self._required
            
        # 检查是否为有效数字
        try:
            value = float(text)
            
            # 检查范围
            if self._min_value is not None and value < self._min_value:
                self.setError(f"值不能小于 {self._min_value}")
                return False
                
            if self._max_value is not None and value > self._max_value:
                self.setError(f"值不能大于 {self._max_value}")
                return False
                
            # 检查小数位数
            if self._decimals == 0 and value != int(value):
                self.setError("请输入整数")
                return False
                
            return True
        except ValueError:
            self.setError("请输入有效数字")
            return False

class PasswordField(BaseInputField):
    """密码输入字段"""
    
    # 添加_toggle_button属性声明
    _toggle_button: Optional[QToolButton] = None
    
    def __init__(self, 
                 label: str = "", 
                 placeholder: str = "请输入密码",
                 parent: Optional[QWidget] = None,
                 on_change: Optional[Callable[[str], None]] = None,
                 required: bool = False,
                 helper_text: str = "",
                 error_text: str = "",
                 initial_value: str = "",
                 max_length: int = 0,
                 show_toggle: bool = True):
        """
        初始化密码输入字段
        
        Args:
            label: 输入框标签
            placeholder: 输入框占位符
            parent: 父组件
            on_change: 值变化回调
            required: 是否必填
            helper_text: 帮助文本
            error_text: 错误文本
            initial_value: 初始值
            max_length: 最大长度（0表示无限制）
            show_toggle: 是否显示密码显示切换按钮
        """
        super().__init__(label, placeholder, parent, on_change, 
                         required, helper_text, error_text, initial_value)
        
        # 设置密码模式和最大长度（仅当_input是QLineEdit时）
        if isinstance(self._input, QLineEdit):
            self._input.setEchoMode(QLineEdit.EchoMode.Password)
            
            # 设置最大长度
            if max_length > 0:
                self._input.setMaxLength(max_length)
            
            # 实现密码显示切换
            if show_toggle:
                self._add_toggle_button()
    
    def _add_toggle_button(self):
        """Helper to add the toggle button"""
        if not isinstance(self._input, QLineEdit): 
            return
        
        if self._layout is None:
            return
            
        # 确保_layout是有效的，并且可以找到_input
        if isinstance(self._layout, QVBoxLayout) or isinstance(self._layout, QHBoxLayout):
            original_index = self._layout.indexOf(self._input)
            if original_index != -1:
                self._layout.removeWidget(self._input)

                input_layout = QHBoxLayout()
                input_layout.setContentsMargins(0, 0, 0, 0)
                input_layout.setSpacing(0)

                input_layout.addWidget(self._input)

                self._toggle_button = QToolButton(self)
                self._toggle_button.setText("👁")
                self._toggle_button.setFixedSize(30, 30)
                self._toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
                self._toggle_button.clicked.connect(self._toggle_password_visibility)

                input_layout.addWidget(self._toggle_button)

                self._layout.insertLayout(original_index, input_layout)
            else:
                logger.warning("Could not find QLineEdit in PasswordField layout to add toggle button.")
        else:
            logger.warning("Invalid layout type in PasswordField")

    def _toggle_password_visibility(self):
        """切换密码显示/隐藏"""
        if isinstance(self._input, QLineEdit) and self._toggle_button is not None:
            if self._input.echoMode() == QLineEdit.EchoMode.Password:
                self._input.setEchoMode(QLineEdit.EchoMode.Normal)
                self._toggle_button.setText("❌")
            else:
                self._input.setEchoMode(QLineEdit.EchoMode.Password)
                self._toggle_button.setText("👁")

class TextArea(QWidget):
    """多行文本输入区域"""
    
    valueChanged = Signal(str)  # 值变化信号
    
    def __init__(self, 
                 label: str = "", 
                 placeholder: str = "",
                 parent: Optional[QWidget] = None,
                 on_change: Optional[Callable[[str], None]] = None,
                 required: bool = False,
                 helper_text: str = "",
                 error_text: str = "",
                 initial_value: str = "",
                 min_height: int = 100,
                 max_height: int = 0,
                 read_only: bool = False):
        """
        初始化多行文本区域
        
        Args:
            label: 输入框标签
            placeholder: 输入框占位符
            parent: 父组件
            on_change: 值变化回调
            required: 是否必填
            helper_text: 帮助文本
            error_text: 错误文本
            initial_value: 初始值
            min_height: 最小高度
            max_height: 最大高度（0表示无限制）
            read_only: 是否只读
        """
        super().__init__(parent)
        
        # 保存属性
        self._required = required
        self._helper_text = helper_text
        self._error_text = error_text
        self._has_error = False
        
        # 预先声明输入控件变量
        self._input: Optional[Union[QTextEdit, QLineEdit]] = None
        self._label: Optional[QLabel] = None
        self._message_label: Optional[QLabel] = None
        
        # 创建布局
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        
        # 添加标签（如果提供）
        if label:
            self._label = QLabel(label, self)
            if required:
                self._label.setText(f"{label} *")
            self._layout.addWidget(self._label)
        
        # 创建文本区域
        try:
            # 不需要再次导入，使用外部导入的QTextEdit
            self._input = QTextEdit(self)
            self._input.setPlaceholderText(placeholder)
            self._input.setPlainText(initial_value)
            self._input.setReadOnly(read_only)
            
            # 设置样式
            self._input.setStyleSheet("""
                QTextEdit {
                    background-color: #1D1D1D;
                    color: #E6E6E6;
                    border: 1px solid #3D3D3D;
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 14px;
                }
                
                QTextEdit:hover {
                    border: 1px solid #5D5D5D;
                }
                
                QTextEdit:focus {
                    border: 1px solid #1A6E8E;
                }
                
                QTextEdit:disabled {
                    background-color: #252525;
                    color: #808080;
                    border: 1px solid #3D3D3D;
                }
                
                QTextEdit[error="true"] {
                    border: 1px solid #9E2B25;
                }
            """)
            
            # 设置尺寸
            if min_height > 0:
                self._input.setMinimumHeight(min_height)
            if max_height > 0:
                self._input.setMaximumHeight(max_height)
                
            self._layout.addWidget(self._input)
            
            # 添加辅助/错误文本标签
            self._message_label = QLabel(helper_text, self)
            self._message_label.setStyleSheet("color: #808080; font-size: 12px;")
            self._layout.addWidget(self._message_label)
            
            # 设置初始可见性
            self._message_label.setVisible(bool(helper_text))
            
            # 连接信号
            if isinstance(self._input, QTextEdit):
                self._input.textChanged.connect(self._on_text_changed)
            if on_change:
                self.valueChanged.connect(on_change)
                
        except Exception as e:
            logger.error(f"无法创建QTextEdit组件: {str(e)}")
            # 回退到单行输入
            self._input = QLineEdit(self)
            self._input.setPlaceholderText(placeholder)
            self._input.setText(initial_value)
            self._input.setReadOnly(read_only)
            self._layout.addWidget(self._input)
            
            # 添加辅助/错误文本标签
            self._message_label = QLabel(helper_text, self)
            self._message_label.setStyleSheet("color: #808080; font-size: 12px;")
            self._layout.addWidget(self._message_label)
    
    def _on_text_changed(self) -> None:
        """当文本变化时处理"""
        # 清除错误状态（如果有）
        if self._has_error:
            self.clearError()
            
        # 获取当前文本并发射信号
        text = self.value()
        self.valueChanged.emit(text)
        
    def value(self) -> str:
        """获取当前值"""
        if self._input is None:
            return ""
            
        if isinstance(self._input, QTextEdit):
            return self._input.toPlainText()
        elif isinstance(self._input, QLineEdit):
            return self._input.text()
        return ""
    
    def setValue(self, value: str) -> None:
        """设置当前值"""
        if self._input is None:
            return
            
        if isinstance(self._input, QTextEdit):
            self._input.setPlainText(value)
        elif isinstance(self._input, QLineEdit):
            self._input.setText(value)
            
    def setError(self, error_text: str = "") -> None:
        """设置错误状态"""
        self._has_error = True
        
        # 使用提供的错误文本或默认错误文本
        text = error_text if error_text else self._error_text or "输入无效"
        
        # 更新样式和消息
        if self._input is not None:
            self._input.setProperty("error", "true")
            style = self._input.style()
            if style is not None:
                style.unpolish(self._input)
                style.polish(self._input)
        
        if self._message_label is not None:
            self._message_label.setText(text)
            self._message_label.setStyleSheet("color: #9E2B25; font-size: 12px;")
            self._message_label.setVisible(True)
        
    def clearError(self) -> None:
        """清除错误状态"""
        self._has_error = False
        
        # 恢复正常样式
        if self._input is not None:
            self._input.setProperty("error", "false")
            style = self._input.style()
            if style is not None:
                style.unpolish(self._input)
                style.polish(self._input)
        
        # 恢复帮助文本（如果有）
        if self._message_label is not None:
            if self._helper_text:
                self._message_label.setText(self._helper_text)
                self._message_label.setStyleSheet("color: #808080; font-size: 12px;")
                self._message_label.setVisible(True)
            else:
                self._message_label.setVisible(False)
            
    def setReadOnly(self, read_only: bool):
        """设置只读状态"""
        if self._input is not None:
            self._input.setReadOnly(read_only)
    
    def setStyle(self, style: Optional[QStyle]) -> None:
        """设置样式"""
        if self._input is None:
            return
            
        current_style = self.style()
        if current_style is not None:
            current_style.unpolish(self)
            # 确保类型兼容
            if isinstance(self._input, QWidget):
                current_style.unpolish(self._input)
        
        if style is not None:
            super().setStyle(style)
            style.polish(self)
            # 确保类型兼容
            if isinstance(self._input, QWidget):
                style.polish(self._input)
        # 不要调用super().setStyle(None)

class FormField(QWidget):
    """表单字段组合器，用于将多个输入字段组合成一个表单"""
    
    submitted = Signal(dict)  # 表单提交信号，传递字段值字典
    
    def __init__(self, 
                 parent: Optional[QWidget] = None,
                 fields: Optional[List[Tuple[str, QWidget]]] = None):
        """
        初始化表单字段
        
        Args:
            parent: 父组件
            fields: 字段列表，每个元素为 (字段名, 字段组件) 元组
        """
        super().__init__(parent)
        
        # 创建布局
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(16)
        
        # 保存字段字典
        self._fields: Dict[str, Any] = {}
        
        # 添加字段（如果提供）
        if fields:
            for name, field in fields:
                self.addField(name, field)
    
    def addField(self, name: str, field: QWidget):
        """添加字段"""
        self._fields[name] = field
        self._layout.addWidget(field)
        
    def getField(self, name: str) -> Optional[QWidget]:
        """获取字段"""
        return self._fields.get(name)
        
    def removeField(self, name: str):
        """移除字段"""
        field = self._fields.pop(name, None)
        if field:
            self._layout.removeWidget(field)
            field.setParent(None)
    
    def getValues(self) -> dict:
        """获取所有字段的值"""
        values = {}
        for name, field in self._fields.items():
            if isinstance(field, BaseInputField) or hasattr(field, 'value'):
                try:
                    values[name] = field.value()
                except Exception as e:
                    logger.warning(f"Could not get value for field '{name}': {e}")
                    values[name] = None
            else:
                logger.warning(f"Field '{name}' of type {type(field).__name__} does not have a 'value' method.")
                values[name] = None
        return values
    
    def validate(self) -> bool:
        """验证所有字段"""
        is_valid = True
        for field_name, field in self._fields.items():
            if isinstance(field, BaseInputField) or hasattr(field, 'isValid'):
                try:
                    if not field.isValid():
                        is_valid = False
                except Exception as e:
                    logger.warning(f"Could not validate field '{field_name}': {e}")
                    is_valid = False
        return is_valid
    
    def submit(self) -> bool:
        """验证并提交表单"""
        if self.validate():
            values = self.getValues()
            self.submitted.emit(values)
            return True
        return False 