"""
---------------------------------------------------------------
File name:                  inputs.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                UI输入组件
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

import logging
from typing import Optional, Callable, Union, List, Tuple, Any

try:
    from PyQt6.QtCore import Qt, pyqtSignal, QSize, QEvent
    from PyQt6.QtGui import QIcon, QKeyEvent, QValidator, QIntValidator, QDoubleValidator
    from PyQt6.QtWidgets import (QLineEdit, QWidget, QHBoxLayout, QLabel, 
                                 QCompleter, QVBoxLayout, QSizePolicy)
    HAS_PYQT = True
except ImportError:
    HAS_PYQT = False
    # 创建占位类以避免导入错误
    class QLineEdit:
        pass
    class QWidget:
        pass
    class QValidator:
        pass

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
    
    valueChanged = pyqtSignal(str)  # 值变化信号
    
    def __init__(self, 
                 label: str = "", 
                 placeholder: str = "",
                 parent: Optional[QWidget] = None,
                 on_change: Optional[Callable[[str], None]] = None,
                 required: bool = False,
                 helper_text: str = "",
                 error_text: str = "",
                 initial_value: str = ""):
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
        if not HAS_PYQT:
            logger.error("PyQt6未安装，无法创建UI组件")
            return
            
        super().__init__(parent)
        
        # 保存属性
        self._required = required
        self._helper_text = helper_text
        self._error_text = error_text
        self._has_error = False
        
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
        else:
            self._label = None
        
        # 创建输入框
        self._input = QLineEdit(self)
        self._input.setPlaceholderText(placeholder)
        self._input.setText(initial_value)
        self._input.setStyleSheet(INPUT_STYLE)
        self._layout.addWidget(self._input)
        
        # 添加辅助/错误文本标签
        self._message_label = QLabel(helper_text, self)
        self._message_label.setStyleSheet("color: #808080; font-size: 12px;")
        self._layout.addWidget(self._message_label)
        
        # 设置初始可见性
        self._message_label.setVisible(bool(helper_text))
        
        # 连接信号
        self._input.textChanged.connect(self._on_text_changed)
        if on_change:
            self.valueChanged.connect(on_change)
    
    def _on_text_changed(self, text: str):
        """当文本变化时处理"""
        # 清除错误状态（如果有）
        if self._has_error:
            self.clearError()
            
        # 发射信号
        self.valueChanged.emit(text)
        
    def value(self) -> str:
        """获取当前值"""
        return self._input.text()
    
    def setValue(self, value: str):
        """设置当前值"""
        self._input.setText(value)
        
    def setError(self, error_text: str = ""):
        """设置错误状态"""
        self._has_error = True
        
        # 使用提供的错误文本或默认错误文本
        text = error_text if error_text else self._error_text or "输入无效"
        
        # 更新样式和消息
        self._input.setProperty("error", "true")
        self._input.style().unpolish(self._input)
        self._input.style().polish(self._input)
        
        self._message_label.setText(text)
        self._message_label.setStyleSheet("color: #9E2B25; font-size: 12px;")
        self._message_label.setVisible(True)
        
    def clearError(self):
        """清除错误状态"""
        self._has_error = False
        
        # 恢复正常样式
        self._input.setProperty("error", "false")
        self._input.style().unpolish(self._input)
        self._input.style().polish(self._input)
        
        # 恢复帮助文本（如果有）
        if self._helper_text:
            self._message_label.setText(self._helper_text)
            self._message_label.setStyleSheet("color: #808080; font-size: 12px;")
            self._message_label.setVisible(True)
        else:
            self._message_label.setVisible(False)
    
    def hasError(self) -> bool:
        """检查是否有错误"""
        return self._has_error
    
    def setPlaceholder(self, text: str):
        """设置占位符文本"""
        self._input.setPlaceholderText(text)
        
    def setRequired(self, required: bool):
        """设置是否必填"""
        self._required = required
        if self._label:
            text = self._label.text().rstrip(" *")
            self._label.setText(f"{text} *" if required else text)
    
    def isRequired(self) -> bool:
        """检查是否必填"""
        return self._required
    
    def isValid(self) -> bool:
        """验证输入是否有效"""
        # 基本验证：必填字段不能为空
        if self._required and not self.value().strip():
            self.setError("此字段为必填项")
            return False
        return True
        
    def setEnabled(self, enabled: bool):
        """设置启用状态"""
        super().setEnabled(enabled)
        if self._input:
            self._input.setEnabled(enabled)
        if self._label:
            self._label.setEnabled(enabled)
        if self._message_label:
            self._message_label.setEnabled(enabled)
            
    def setHelper(self, text: str):
        """设置帮助文本"""
        self._helper_text = text
        if not self._has_error:
            self._message_label.setText(text)
            self._message_label.setVisible(bool(text))

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
        if max_length > 0:
            self._input.setMaxLength(max_length)
            
        # 设置密码模式（如果指定）
        if password:
            self._input.setEchoMode(QLineEdit.EchoMode.Password)

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
        super().__init__("", placeholder, parent, on_change)
        
        # 添加搜索图标
        self._input.setProperty("class", "search")
        
        # 设置搜索提交处理
        self._input.returnPressed.connect(self._on_search)
        self._on_search_callback = on_search
        
        # 添加自动完成功能（如果提供建议）
        if suggestions:
            self.setSuggestions(suggestions)
            
    def _on_search(self):
        """搜索提交处理"""
        if self._on_search_callback:
            self._on_search_callback(self.value())
            
    def setSuggestions(self, suggestions: List[str]):
        """设置搜索建议"""
        completer = QCompleter(suggestions, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._input.setCompleter(completer)

class NumberField(BaseInputField):
    """数字输入字段"""
    
    valueChanged = pyqtSignal(float)  # 重新定义为数值类型信号
    
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
            validator = QDoubleValidator(self)
            validator.setDecimals(decimals)
            if min_value is not None:
                validator.setBottom(min_value)
            if max_value is not None:
                validator.setTop(max_value)
        else:
            # 整数验证器
            validator = QIntValidator(self)
            if min_value is not None:
                validator.setBottom(int(min_value))
            if max_value is not None:
                validator.setTop(int(max_value))
                
        self._input.setValidator(validator)
        
        # 保存范围信息用于验证
        self._min_value = min_value
        self._max_value = max_value
        self._decimals = decimals
        
        # 连接信号
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
                
    def value(self) -> Union[int, float, None]:
        """获取当前数值"""
        text = self._input.text()
        if not text:
            return None
            
        try:
            value = float(text)
            return int(value) if self._decimals == 0 else value
        except ValueError:
            return None
            
    def setValue(self, value: Union[int, float]):
        """设置当前数值"""
        if self._decimals == 0:
            self._input.setText(str(int(value)))
        else:
            format_str = f"{{:.{self._decimals}f}}"
            self._input.setText(format_str.format(value))
            
    def isValid(self) -> bool:
        """验证输入是否有效"""
        # 首先调用基类验证
        if not super().isValid():
            return False
            
        # 如果为空且非必填，则有效
        text = self._input.text()
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
        if not HAS_PYQT:
            logger.error("PyQt6未安装，无法创建UI组件")
            return
            
        super().__init__(label, placeholder, parent, on_change, 
                         required, helper_text, error_text, initial_value)
        
        # 设置密码模式
        self._input.setEchoMode(QLineEdit.EchoMode.Password)
        
        # 设置最大长度
        if max_length > 0:
            self._input.setMaxLength(max_length)
            
        # 实现密码显示切换
        if show_toggle and HAS_PYQT:
            try:
                from PyQt6.QtWidgets import QToolButton
                
                # 移除并重新创建布局
                self._layout.removeWidget(self._input)
                
                # 创建包含输入框和切换按钮的水平布局
                input_layout = QHBoxLayout()
                input_layout.setContentsMargins(0, 0, 0, 0)
                input_layout.setSpacing(0)
                
                # 添加输入框
                input_layout.addWidget(self._input)
                
                # 创建切换按钮
                self._toggle_button = QToolButton(self)
                self._toggle_button.setText("👁")
                self._toggle_button.setFixedSize(30, 30)
                self._toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
                self._toggle_button.clicked.connect(self._toggle_password_visibility)
                
                # 添加按钮
                input_layout.addWidget(self._toggle_button)
                
                # 将水平布局添加到主布局
                self._layout.insertLayout(1, input_layout)
                
            except ImportError:
                logger.warning("无法导入QToolButton，密码切换按钮不可用")
    
    def _toggle_password_visibility(self):
        """切换密码显示/隐藏"""
        if self._input.echoMode() == QLineEdit.EchoMode.Password:
            self._input.setEchoMode(QLineEdit.EchoMode.Normal)
            self._toggle_button.setText("❌")
        else:
            self._input.setEchoMode(QLineEdit.EchoMode.Password)
            self._toggle_button.setText("👁")

class TextArea(QWidget):
    """多行文本输入区域"""
    
    valueChanged = pyqtSignal(str)  # 值变化信号
    
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
        if not HAS_PYQT:
            logger.error("PyQt6未安装，无法创建UI组件")
            return
            
        super().__init__(parent)
        
        # 保存属性
        self._required = required
        self._helper_text = helper_text
        self._error_text = error_text
        self._has_error = False
        
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
            from PyQt6.QtWidgets import QTextEdit
            
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
            self._input.textChanged.connect(self._on_text_changed)
            if on_change:
                self.valueChanged.connect(on_change)
                
        except ImportError:
            logger.error("无法导入QTextEdit，使用QLineEdit替代")
            # 回退到单行输入
            self._input = QLineEdit(self)
            self._input.setPlaceholderText(placeholder)
            self._input.setText(initial_value)
            self._input.setReadOnly(read_only)
            self._layout.addWidget(self._input)
    
    def _on_text_changed(self):
        """当文本变化时处理"""
        # 清除错误状态（如果有）
        if self._has_error:
            self.clearError()
            
        # 获取当前文本并发射信号
        text = self.value()
        self.valueChanged.emit(text)
        
    def value(self) -> str:
        """获取当前值"""
        try:
            return self._input.toPlainText()
        except:
            return self._input.text()
    
    def setValue(self, value: str):
        """设置当前值"""
        try:
            self._input.setPlainText(value)
        except:
            self._input.setText(value)
            
    def setError(self, error_text: str = ""):
        """设置错误状态"""
        self._has_error = True
        
        # 使用提供的错误文本或默认错误文本
        text = error_text if error_text else self._error_text or "输入无效"
        
        # 更新样式和消息
        self._input.setProperty("error", "true")
        self._input.style().unpolish(self._input)
        self._input.style().polish(self._input)
        
        self._message_label.setText(text)
        self._message_label.setStyleSheet("color: #9E2B25; font-size: 12px;")
        self._message_label.setVisible(True)
        
    def clearError(self):
        """清除错误状态"""
        self._has_error = False
        
        # 恢复正常样式
        self._input.setProperty("error", "false")
        self._input.style().unpolish(self._input)
        self._input.style().polish(self._input)
        
        # 恢复帮助文本（如果有）
        if self._helper_text:
            self._message_label.setText(self._helper_text)
            self._message_label.setStyleSheet("color: #808080; font-size: 12px;")
            self._message_label.setVisible(True)
        else:
            self._message_label.setVisible(False)
            
    def setReadOnly(self, read_only: bool):
        """设置只读状态"""
        self._input.setReadOnly(read_only)

class FormField(QWidget):
    """表单字段组合器，用于将多个输入字段组合成一个表单"""
    
    submitted = pyqtSignal(dict)  # 表单提交信号，传递字段值字典
    
    def __init__(self, 
                 parent: Optional[QWidget] = None,
                 fields: Optional[List[Tuple[str, QWidget]]] = None):
        """
        初始化表单字段
        
        Args:
            parent: 父组件
            fields: 字段列表，每个元素为 (字段名, 字段组件) 元组
        """
        if not HAS_PYQT:
            logger.error("PyQt6未安装，无法创建UI组件")
            return
            
        super().__init__(parent)
        
        # 创建布局
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(16)
        
        # 保存字段字典
        self._fields = {}
        
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
            if hasattr(field, 'value') and callable(field.value):
                values[name] = field.value()
        return values
    
    def validate(self) -> bool:
        """验证所有字段"""
        is_valid = True
        for field in self._fields.values():
            if hasattr(field, 'isValid') and callable(field.isValid):
                if not field.isValid():
                    is_valid = False
        return is_valid
    
    def submit(self) -> bool:
        """验证并提交表单"""
        if self.validate():
            values = self.getValues()
            self.submitted.emit(values)
            return True
        return False 