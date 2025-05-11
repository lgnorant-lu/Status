# mypy: disable-error-code="attr-defined,unused-ignore,no-redef,unreachable"
"""
---------------------------------------------------------------
File name:                  mocks.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                用于测试的Qt模拟模块
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
                            2025/05/16: 添加对PySide6的支持;
                            2025/05/16: 专注于PySide6支持，移除PyQt6依赖;
                            2025/05/16: 改进PyQt6->PySide6映射，解决DLL加载错误;
                            2025/05/17: 添加mypy类型注释;
                            2025/05/17: 修复类型兼容性问题;
----
"""

# 模拟Qt相关的类和枚举，用于单元测试

import sys
import types
from enum import Enum, auto
from typing import Any, List, Optional, Dict, Union, Type, Callable, cast, TypeVar, ClassVar

# 定义类型变量用于类型化Signal
T = TypeVar('T')

# 尝试导入PySide6类，失败时使用模拟类
try:
    # 允许导入时可能的名称重定义
    from PySide6.QtWidgets import QSystemTrayIcon as PySide6_QSystemTrayIcon  # 使用别名避免类型冲突
    from PySide6.QtWidgets import QMenu as PySide6_QMenu
    from PySide6.QtWidgets import QApplication as PySide6_QApplication
    from PySide6.QtGui import QIcon as PySide6_QIcon
    from PySide6.QtGui import QAction as PySide6_QAction
    from PySide6.QtCore import QObject as PySide6_QObject
    from PySide6.QtCore import Signal as PySide6_Signal
    
    # 为兼容性创建本地别名
    QSystemTrayIcon = PySide6_QSystemTrayIcon
    QMenu = PySide6_QMenu
    QApplication = PySide6_QApplication
    QIcon = PySide6_QIcon
    QAction = PySide6_QAction
    QObject = PySide6_QObject
    Signal = PySide6_Signal
    
    # 为保持兼容性，为Signal创建pyqtSignal别名
    pyqtSignal = Signal
    print("PySide6模块已正确加载（包含QApplication）")
except ImportError:
    # 模拟QSystemTrayIcon
    class QSystemTrayIcon:  # type: ignore[no-redef]
        """模拟的QSystemTrayIcon类，用于测试"""
        
        class ActivationReason(Enum):
            """模拟ActivationReason枚举"""
            Trigger = auto()
            DoubleClick = auto()
            MiddleClick = auto()
            Context = auto()
            Unknown = auto()
        
        # 定义消息图标枚举
        Information = 1
        Warning = 2
        Critical = 3
        NoIcon = 4
        
        # 将类枚举通过类属性暴露，以保持与原始API的兼容性
        Trigger = ActivationReason.Trigger
        DoubleClick = ActivationReason.DoubleClick
        MiddleClick = ActivationReason.MiddleClick
        Context = ActivationReason.Context
        Unknown = ActivationReason.Unknown
        
        def __init__(self, parent: Any = None) -> None:
            """初始化"""
            self.parent = parent
            self.visible = False
            self.icon = None
            self.tooltip = ""
            self.context_menu = None
        
        def show(self) -> None:
            """显示托盘图标"""
            self.visible = True
        
        def hide(self) -> None:
            """隐藏托盘图标"""
            self.visible = False
        
        def setIcon(self, icon: Any) -> None:
            """设置图标"""
            self.icon = icon
        
        def setToolTip(self, tooltip: str) -> None:
            """设置工具提示"""
            self.tooltip = tooltip
        
        def setContextMenu(self, menu: Any) -> None:
            """设置上下文菜单"""
            self.context_menu = menu
        
        def showMessage(self, title: str, message: str, icon: Any = Information, duration: int = 5000) -> None:
            """显示消息"""
            pass
        
        def activated(self, reason: Any) -> None:
            """激活信号，模拟为方法"""
            pass

    # 模拟QIcon
    class QIcon:  # type: ignore[no-redef]
        """模拟的QIcon类，用于测试"""
        
        def __init__(self, icon_path: Optional[str] = None) -> None:
            """初始化"""
            self.path = icon_path
            self._null = icon_path is None
        
        def isNull(self) -> bool:
            """检查图标是否为空"""
            return self._null
        
        @staticmethod
        def fromTheme(theme_name: str) -> 'QIcon':
            """从主题创建图标"""
            return QIcon()

    # 模拟QMenu
    class QMenu:  # type: ignore[no-redef]
        """模拟的QMenu类，用于测试"""
        
        def __init__(self, parent: Any = None) -> None:
            """初始化"""
            self.parent = parent
            self.actions: List[Any] = []
            self.submenus: List['QMenu'] = []
            self._title_str = ""  # 重命名以避免与方法冲突
        
        def addAction(self, action: Any) -> Any:
            """添加动作"""
            self.actions.append(action)
            return action
        
        def addMenu(self, text: str) -> 'QMenu':
            """添加子菜单"""
            submenu = QMenu()
            # 使用setter函数而不是直接访问属性
            submenu.setTitle(text)
            self.submenus.append(submenu)
            return submenu
        
        def addSeparator(self) -> None:
            """添加分隔符"""
            pass
        
        def clear(self) -> None:
            """清空菜单"""
            self.actions.clear()
            self.submenus.clear()
            
        def title(self) -> str:
            """获取标题"""
            return self._title_str
            
        def setTitle(self, title: str) -> None:
            """设置标题"""
            self._title_str = title
    
    # 模拟QApplication
    class QApplication:  # type: ignore[no-redef]
        """模拟的QApplication类，用于测试"""
        # 使用ClassVar声明类变量
        _instance: ClassVar[Optional['QApplication']] = None
        
        def __init__(self, argv: Optional[List[str]] = None) -> None:
            """初始化"""
            self.argv = argv or []
            # 存储实例
            QApplication._instance = self
            self.display_name = ""
            self.quit_called = False
            self.window_icon = None
            self.style_sheet = ""
        
        @staticmethod
        def instance() -> Optional['QApplication']:
            """获取单例实例"""
            return QApplication._instance
        
        def setApplicationDisplayName(self, name: str) -> None:
            """设置应用程序显示名称"""
            self.display_name = name
        
        def applicationDisplayName(self) -> str:
            """获取应用程序显示名称"""
            return self.display_name
        
        def setWindowIcon(self, icon: Any) -> None:
            """设置窗口图标"""
            self.window_icon = icon
        
        def setStyleSheet(self, style_sheet: str) -> None:
            """设置样式表"""
            self.style_sheet = style_sheet
        
        def exec(self) -> int:
            """执行应用程序事件循环"""
            return 0
        
        def quit(self) -> None:
            """退出应用程序"""
            self.quit_called = True
    
    # 模拟QAction
    class QAction:  # type: ignore[no-redef]
        """模拟的QAction类，用于测试"""
        
        def __init__(self, text: str, parent: Any = None) -> None:
            """初始化"""
            self.text_str = text  # 重命名以避免与方法冲突
            self.parent_obj = parent  # 重命名以避免与方法冲突
            self.object_name = ""
            self._data = None
            self._enabled = True
            self._checkable = False
            self._checked = False
            # 定义触发回调列表
            self._triggered_callbacks: List[Callable[..., Any]] = []
        
        def text(self) -> str:
            """获取文本"""
            return self.text_str
            
        def setText(self, text: str) -> None:
            """设置文本"""
            self.text_str = text
            
        def parent(self) -> Any:
            """获取父对象"""
            return self.parent_obj
        
        def setObjectName(self, name: str) -> None:
            """设置对象名称"""
            self.object_name = name
        
        def setData(self, data: Any) -> None:
            """设置数据"""
            self._data = data
        
        def data(self) -> Any:
            """获取数据"""
            return self._data
        
        def setEnabled(self, enabled: bool) -> None:
            """设置是否启用"""
            self._enabled = enabled
        
        def isEnabled(self) -> bool:
            """检查是否启用"""
            return self._enabled
        
        def setCheckable(self, checkable: bool) -> None:
            """设置是否可选中"""
            self._checkable = checkable
        
        def isCheckable(self) -> bool:
            """检查是否可选中"""
            return self._checkable
        
        def setChecked(self, checked: bool) -> None:
            """设置是否选中"""
            self._checked = checked
        
        def isChecked(self) -> bool:
            """检查是否选中"""
            return self._checked
            
        # 信号模拟方法
        def triggered(self, checked: bool = False) -> None:
            """触发信号，模拟为方法"""
            for callback in self._triggered_callbacks:
                callback()
                
        # 连接方法（模拟Signal的connect方法）
        def connect_triggered(self, callback: Callable[..., Any]) -> None:
            """连接触发信号的回调"""
            if callback not in self._triggered_callbacks:
                self._triggered_callbacks.append(callback)

    # 模拟QObject
    class QObject:  # type: ignore[no-redef]
        """模拟的QObject类，用于测试"""
        
        def __init__(self) -> None:
            """初始化"""
            pass
    
    # 模拟Signal/pyqtSignal
    class Signal:  # type: ignore[no-redef]
        """模拟的Signal类，用于测试"""
        
        def __init__(self, *args: Any) -> None:
            """初始化"""
            self.args = args
            self.callbacks: List[Any] = []
        
        def connect(self, callback: Any) -> None:
            """连接回调函数"""
            self.callbacks.append(callback)
        
        def disconnect(self, callback: Any = None) -> None:
            """断开回调函数"""
            if callback is None:
                self.callbacks.clear()
            elif callback in self.callbacks:
                self.callbacks.remove(callback)
        
        def emit(self, *args: Any) -> None:
            """发送信号"""
            for callback in self.callbacks:
                callback(*args)
    
    # 为兼容性保留pyqtSignal别名
    # 使用类型注解来解决"Cannot assign multiple types to name pyqtSignal"错误
    pyqtSignal: Type[Signal] = Signal

# 创建模拟的PySide6模块，如果真实模块不存在或不完整
if 'PySide6' not in sys.modules:
    # 创建模拟的PySide6模块结构
    pyside6_module = types.ModuleType('PySide6')
    sys.modules['PySide6'] = pyside6_module
    
    # 创建子模块
    widgets_module = types.ModuleType('PySide6.QtWidgets')
    gui_module = types.ModuleType('PySide6.QtGui')
    core_module = types.ModuleType('PySide6.QtCore')
    test_module = types.ModuleType('PySide6.QtTest')  # 添加测试模块
    
    # 将类添加到各个模块
    widgets_module.QSystemTrayIcon = QSystemTrayIcon  # type: ignore[attr-defined]
    widgets_module.QMenu = QMenu  # type: ignore[attr-defined]
    widgets_module.QApplication = QApplication  # type: ignore[attr-defined]
    
    gui_module.QIcon = QIcon  # type: ignore[attr-defined]
    gui_module.QAction = QAction  # type: ignore[attr-defined]
    
    core_module.QObject = QObject  # type: ignore[attr-defined]
    core_module.Signal = Signal  # type: ignore[attr-defined]
    
    # 注册模块
    sys.modules['PySide6.QtWidgets'] = widgets_module
    sys.modules['PySide6.QtGui'] = gui_module
    sys.modules['PySide6.QtCore'] = core_module
    sys.modules['PySide6.QtTest'] = test_module  # 注册测试模块
    
    # 将模块添加到PySide6包
    # 使用setattr而不是直接赋值，避免attr-defined错误
    setattr(pyside6_module, 'QtWidgets', widgets_module)
    setattr(pyside6_module, 'QtGui', gui_module)
    setattr(pyside6_module, 'QtCore', core_module)
    setattr(pyside6_module, 'QtTest', test_module)
    
    print("已创建PySide6模拟模块（包含QtTest）")

# 为兼容现有代码，创建PyQt6->PySide6的映射
if 'PyQt6' not in sys.modules:
    # 创建PyQt6模块作为PySide6的别名
    pyqt6_module = types.ModuleType('PyQt6')
    sys.modules['PyQt6'] = pyqt6_module
    
    # 先确保PySide6模块存在
    if 'PySide6' not in sys.modules or 'PySide6.QtTest' not in sys.modules:
        # 如果没有完整的PySide6，创建模拟模块
        if 'PySide6' not in sys.modules:
            pyside6_module = types.ModuleType('PySide6')
            sys.modules['PySide6'] = pyside6_module
        else:
            pyside6_module = sys.modules['PySide6']
        
        # 确保子模块存在
        if 'PySide6.QtWidgets' not in sys.modules:
            widgets_module = types.ModuleType('PySide6.QtWidgets')
            sys.modules['PySide6.QtWidgets'] = widgets_module
            setattr(pyside6_module, 'QtWidgets', widgets_module)
        
        if 'PySide6.QtGui' not in sys.modules:
            gui_module = types.ModuleType('PySide6.QtGui')
            sys.modules['PySide6.QtGui'] = gui_module
            setattr(pyside6_module, 'QtGui', gui_module)
        
        if 'PySide6.QtCore' not in sys.modules:
            core_module = types.ModuleType('PySide6.QtCore')
            sys.modules['PySide6.QtCore'] = core_module
            setattr(pyside6_module, 'QtCore', core_module)
        
        # 创建QtTest模块
        if 'PySide6.QtTest' not in sys.modules:
            test_module = types.ModuleType('PySide6.QtTest')
            sys.modules['PySide6.QtTest'] = test_module
            setattr(pyside6_module, 'QtTest', test_module)
    
    # 创建子模块映射，使用setattr替代直接属性赋值
    setattr(pyqt6_module, 'QtWidgets', sys.modules['PySide6.QtWidgets'])
    setattr(pyqt6_module, 'QtGui', sys.modules['PySide6.QtGui'])
    setattr(pyqt6_module, 'QtCore', sys.modules['PySide6.QtCore'])
    setattr(pyqt6_module, 'QtTest', sys.modules['PySide6.QtTest'])
    
    # 注册子模块
    sys.modules['PyQt6.QtWidgets'] = getattr(pyqt6_module, 'QtWidgets')
    sys.modules['PyQt6.QtGui'] = getattr(pyqt6_module, 'QtGui')
    sys.modules['PyQt6.QtCore'] = getattr(pyqt6_module, 'QtCore')
    sys.modules['PyQt6.QtTest'] = getattr(pyqt6_module, 'QtTest')
    
    # 为PyQt6.QtCore添加pyqtSignal作为PySide6.QtCore.Signal的别名
    if hasattr(sys.modules['PySide6.QtCore'], 'Signal'):
        setattr(sys.modules['PyQt6.QtCore'], 'pyqtSignal', getattr(sys.modules['PySide6.QtCore'], 'Signal'))
    
    print("PyQt6模拟模块已正确加载（包含QApplication）") 