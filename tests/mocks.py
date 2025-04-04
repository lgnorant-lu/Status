"""
---------------------------------------------------------------
File name:                  mocks.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                用于测试的PyQt6模拟模块
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

# 模拟PyQt6相关的类和枚举，用于单元测试

import sys
from enum import Enum, auto

# 如果PyQt6不存在，就创建模拟类
try:
    from PyQt6.QtWidgets import QSystemTrayIcon
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

# 如果PyQt6不存在，就创建模拟QIcon类
try:
    from PyQt6.QtGui import QIcon
except ImportError:
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

# 如果PyQt6不存在，就创建模拟QMenu和QAction类
try:
    from PyQt6.QtWidgets import QMenu, QApplication
    from PyQt6.QtGui import QAction
except ImportError:
    # 模拟QMenu
    class QMenu:
        """模拟的QMenu类，用于测试"""
        
        def __init__(self, parent=None):
            """初始化"""
            self.parent = parent
            self.actions = []
            self.submenus = []
        
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

# 如果PyQt6不存在，就创建模拟QObject和信号
try:
    from PyQt6.QtCore import QObject, pyqtSignal
except ImportError:
    # 模拟QObject
    class QObject:
        """模拟的QObject类，用于测试"""
        
        def __init__(self):
            """初始化"""
            pass
    
    # 模拟pyqtSignal
    class pyqtSignal:
        """模拟的pyqtSignal类，用于测试"""
        
        def __init__(self, *args):
            """初始化"""
            self.args = args
            self.callbacks = []
        
        def connect(self, callback):
            """连接回调"""
            self.callbacks.append(callback)
        
        def disconnect(self, callback=None):
            """断开回调"""
            if callback:
                if callback in self.callbacks:
                    self.callbacks.remove(callback)
            else:
                self.callbacks.clear()
        
        def emit(self, *args):
            """发射信号"""
            for callback in self.callbacks:
                callback(*args)

# 将模拟模块添加到sys.modules中
if 'PyQt6' not in sys.modules:
    class QtWidgets:
        QSystemTrayIcon = QSystemTrayIcon
        QMenu = QMenu
        QApplication = QApplication
    
    class QtGui:
        QIcon = QIcon
        QAction = QAction
    
    class QtCore:
        QObject = QObject
        pyqtSignal = pyqtSignal
    
    class PyQt6:
        QtWidgets = QtWidgets
        QtGui = QtGui
        QtCore = QtCore
    
    # 添加到sys.modules中
    sys.modules['PyQt6'] = PyQt6
    sys.modules['PyQt6.QtWidgets'] = PyQt6.QtWidgets
    sys.modules['PyQt6.QtGui'] = PyQt6.QtGui
    sys.modules['PyQt6.QtCore'] = PyQt6.QtCore
    
    print("已成功设置PyQt6模拟模块") 