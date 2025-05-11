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
----
"""

# 模拟Qt相关的类和枚举，用于单元测试

import sys
import types
from enum import Enum, auto

# 尝试导入PySide6类，失败时使用模拟类
try:
    from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
    from PySide6.QtGui import QIcon, QAction
    from PySide6.QtCore import QObject, Signal
    # 为保持兼容性，为Signal创建pyqtSignal别名
    pyqtSignal = Signal
    print("PySide6模块已正确加载（包含QApplication）")
except ImportError:
    # 模拟QSystemTrayIcon
    class QSystemTrayIcon:
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
        
        def __init__(self, parent=None):
            """初始化"""
            self.parent = parent
            self.visible = False
            self.icon = None
            self.tooltip = ""
            self.context_menu = None
        
        def show(self):
            """显示托盘图标"""
            self.visible = True
        
        def hide(self):
            """隐藏托盘图标"""
            self.visible = False
        
        def setIcon(self, icon):
            """设置图标"""
            self.icon = icon
        
        def setToolTip(self, tooltip):
            """设置工具提示"""
            self.tooltip = tooltip
        
        def setContextMenu(self, menu):
            """设置上下文菜单"""
            self.context_menu = menu
        
        def showMessage(self, title, message, icon=Information, duration=5000):
            """显示消息"""
            pass
        
        def activated(self, reason):
            """激活信号，模拟为方法"""
            pass

    # 模拟QIcon
    class QIcon:
        """模拟的QIcon类，用于测试"""
        
        def __init__(self, icon_path=None):
            """初始化"""
            self.path = icon_path
            self._null = icon_path is None
        
        def isNull(self):
            """检查图标是否为空"""
            return self._null
        
        @staticmethod
        def fromTheme(theme_name):
            """从主题创建图标"""
            return QIcon()

    # 模拟QMenu
    class QMenu:
        """模拟的QMenu类，用于测试"""
        
        def __init__(self, parent=None):
            """初始化"""
            self.parent = parent
            self.actions = []
            self.submenus = []
            self.title = ""  # 添加title属性
        
        def addAction(self, action):
            """添加动作"""
            self.actions.append(action)
            return action
        
        def addMenu(self, text):
            """添加子菜单"""
            submenu = QMenu()
            submenu.title = text
            self.submenus.append(submenu)
            return submenu
        
        def addSeparator(self):
            """添加分隔符"""
            pass
        
        def clear(self):
            """清空菜单"""
            self.actions.clear()
            self.submenus.clear()
    
    # 模拟QApplication
    class QApplication:
        """模拟的QApplication类，用于测试"""
        _instance = None
        
        def __init__(self, argv=None):
            """初始化"""
            self.argv = argv or []
            QApplication._instance = self
            self.display_name = ""
            self.quit_called = False
            self.window_icon = None
            self.style_sheet = ""
        
        @staticmethod
        def instance():
            """获取单例实例"""
            return QApplication._instance
        
        def setApplicationDisplayName(self, name):
            """设置应用程序显示名称"""
            self.display_name = name
        
        def applicationDisplayName(self):
            """获取应用程序显示名称"""
            return self.display_name
        
        def setWindowIcon(self, icon):
            """设置窗口图标"""
            self.window_icon = icon
        
        def setStyleSheet(self, style_sheet):
            """设置样式表"""
            self.style_sheet = style_sheet
        
        def exec(self):
            """执行应用程序事件循环"""
            return 0
        
        def quit(self):
            """退出应用程序"""
            self.quit_called = True
    
    # 模拟QAction
    class QAction:
        """模拟的QAction类，用于测试"""
        
        def __init__(self, text, parent=None):
            """初始化"""
            self.text = text
            self.parent = parent
            self.object_name = ""
            self._data = None
            self._enabled = True
            self._checkable = False
            self._checked = False
        
        def setObjectName(self, name):
            """设置对象名称"""
            self.object_name = name
        
        def setData(self, data):
            """设置数据"""
            self._data = data
        
        def data(self):
            """获取数据"""
            return self._data
        
        def setEnabled(self, enabled):
            """设置是否启用"""
            self._enabled = enabled
        
        def isEnabled(self):
            """检查是否启用"""
            return self._enabled
        
        def setCheckable(self, checkable):
            """设置是否可选中"""
            self._checkable = checkable
        
        def isCheckable(self):
            """检查是否可选中"""
            return self._checkable
        
        def setChecked(self, checked):
            """设置是否选中"""
            self._checked = checked
        
        def isChecked(self):
            """检查是否选中"""
            return self._checked
        
        def triggered(self, checked=False):
            """触发信号，模拟为方法"""
            pass

    # 模拟QObject
    class QObject:
        """模拟的QObject类，用于测试"""
        
        def __init__(self):
            """初始化"""
            pass
    
    # 模拟Signal/pyqtSignal
    class Signal:
        """模拟的Signal类，用于测试"""
        
        def __init__(self, *args):
            """初始化"""
            self.args = args
            self.callbacks = []
        
        def connect(self, callback):
            """连接回调函数"""
            self.callbacks.append(callback)
        
        def disconnect(self, callback=None):
            """断开回调函数"""
            if callback is None:
                self.callbacks.clear()
            elif callback in self.callbacks:
                self.callbacks.remove(callback)
        
        def emit(self, *args):
            """发送信号"""
            for callback in self.callbacks:
                callback(*args)
    
    # 为兼容性保留pyqtSignal别名
    pyqtSignal = Signal

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
    widgets_module.QSystemTrayIcon = QSystemTrayIcon
    widgets_module.QMenu = QMenu
    widgets_module.QApplication = QApplication
    
    gui_module.QIcon = QIcon
    gui_module.QAction = QAction
    
    core_module.QObject = QObject
    core_module.Signal = Signal
    
    # 注册模块
    sys.modules['PySide6.QtWidgets'] = widgets_module
    sys.modules['PySide6.QtGui'] = gui_module
    sys.modules['PySide6.QtCore'] = core_module
    sys.modules['PySide6.QtTest'] = test_module  # 注册测试模块
    
    # 将模块添加到PySide6包
    pyside6_module.QtWidgets = widgets_module
    pyside6_module.QtGui = gui_module
    pyside6_module.QtCore = core_module
    pyside6_module.QtTest = test_module  # 添加测试模块
    
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
            pyside6_module.QtWidgets = widgets_module
        
        if 'PySide6.QtGui' not in sys.modules:
            gui_module = types.ModuleType('PySide6.QtGui')
            sys.modules['PySide6.QtGui'] = gui_module
            pyside6_module.QtGui = gui_module
        
        if 'PySide6.QtCore' not in sys.modules:
            core_module = types.ModuleType('PySide6.QtCore')
            sys.modules['PySide6.QtCore'] = core_module
            pyside6_module.QtCore = core_module
        
        # 创建QtTest模块
        if 'PySide6.QtTest' not in sys.modules:
            test_module = types.ModuleType('PySide6.QtTest')
            sys.modules['PySide6.QtTest'] = test_module
            pyside6_module.QtTest = test_module
    
    # 创建子模块映射
    pyqt6_module.QtWidgets = sys.modules['PySide6.QtWidgets']
    pyqt6_module.QtGui = sys.modules['PySide6.QtGui']
    pyqt6_module.QtCore = sys.modules['PySide6.QtCore']
    pyqt6_module.QtTest = sys.modules['PySide6.QtTest']
    
    # 注册子模块
    sys.modules['PyQt6.QtWidgets'] = pyqt6_module.QtWidgets
    sys.modules['PyQt6.QtGui'] = pyqt6_module.QtGui
    sys.modules['PyQt6.QtCore'] = pyqt6_module.QtCore
    sys.modules['PyQt6.QtTest'] = pyqt6_module.QtTest
    
    # 为PyQt6.QtCore添加pyqtSignal作为PySide6.QtCore.Signal的别名
    if hasattr(sys.modules['PySide6.QtCore'], 'Signal'):
        sys.modules['PyQt6.QtCore'].pyqtSignal = sys.modules['PySide6.QtCore'].Signal
    
    print("PyQt6模拟模块已正确加载（包含QApplication）") 