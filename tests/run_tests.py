"""
---------------------------------------------------------------
File name:                  run_tests.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                测试运行脚本
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

# 在运行任何其他代码前，设置模拟模块
import sys
import os

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# 设置模拟模块
if 'PyQt6' not in sys.modules:
    from enum import Enum, auto
    
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
            
    # 模拟信号
    class pyqtSignal:
        """模拟的pyqtSignal类，用于测试"""
        
        def __init__(self, *args):
            """初始化"""
            self.callbacks = []
            
        def connect(self, callback):
            """连接回调"""
            self.callbacks.append(callback)
            
        def disconnect(self, callback=None):
            """断开回调"""
            if callback is None:
                self.callbacks.clear()
            elif callback in self.callbacks:
                self.callbacks.remove(callback)
                
        def emit(self, *args):
            """触发信号"""
            for callback in self.callbacks:
                callback(*args)
    
    # 模拟定时器
    class QTimer(QObject):
        """模拟的QTimer类，用于测试"""
        
        def __init__(self, parent=None):
            """初始化"""
            super().__init__()
            self.parent = parent
            self._interval = 0
            self._single_shot = False
            self._active = False
            self._callback = None
            
        def start(self, interval=None):
            """启动定时器"""
            if interval is not None:
                self._interval = interval
            self._active = True
            
        def stop(self):
            """停止定时器"""
            self._active = False
            
        def isActive(self):
            """检查定时器是否激活"""
            return self._active
            
        def setInterval(self, msec):
            """设置定时器间隔"""
            self._interval = msec
            
        def interval(self):
            """获取定时器间隔"""
            return self._interval
            
        def setSingleShot(self, single_shot):
            """设置是否单次触发"""
            self._single_shot = single_shot
            
        def isSingleShot(self):
            """检查是否单次触发"""
            return self._single_shot
            
        def timeout(self):
            """超时信号，模拟为方法"""
            pass
            
        @staticmethod
        def singleShot(msec, callback):
            """静态方法，创建单次定时器"""
            timer = QTimer()
            timer.setSingleShot(True)
            timer.setInterval(msec)
            timer._callback = callback
            timer.start()
            return timer
    
    # 模拟Qt
    class Qt:
        """模拟的Qt类，用于测试"""
        class PenCapStyle(Enum):
            RoundCap = auto()
            FlatCap = auto()
            SquareCap = auto()
            
        class BrushStyle(Enum):
            NoBrush = auto()
            SolidPattern = auto()
            
        class AlignmentFlag(Enum):
            AlignLeft = auto()
            AlignRight = auto()
            AlignCenter = auto()
            AlignTop = auto()
            AlignBottom = auto()
            
        # 常量
        LeftButton = 1
        RightButton = 2
        MiddleButton = 3
        
        # 将枚举通过类属性暴露
        RoundCap = PenCapStyle.RoundCap
        FlatCap = PenCapStyle.FlatCap
        SquareCap = PenCapStyle.SquareCap
        NoBrush = BrushStyle.NoBrush
        SolidPattern = BrushStyle.SolidPattern
        AlignLeft = AlignmentFlag.AlignLeft
        AlignRight = AlignmentFlag.AlignRight
        AlignCenter = AlignmentFlag.AlignCenter
        AlignTop = AlignmentFlag.AlignTop
        AlignBottom = AlignmentFlag.AlignBottom
    
    # 模拟几何类
    class QPoint:
        """模拟的QPoint类，用于测试"""
        def __init__(self, x=0, y=0):
            self.x = x
            self.y = y
            
        def __eq__(self, other):
            return isinstance(other, QPoint) and self.x == other.x and self.y == other.y
            
    class QPointF:
        """模拟的QPointF类，用于测试"""
        def __init__(self, x=0.0, y=0.0):
            self.x = float(x)
            self.y = float(y)
            
        def __eq__(self, other):
            return isinstance(other, QPointF) and self.x == other.x and self.y == other.y
            
    class QSize:
        """模拟的QSize类，用于测试"""
        def __init__(self, width=0, height=0):
            self.width = width
            self.height = height
            
        def __eq__(self, other):
            return isinstance(other, QSize) and self.width == other.width and self.height == other.height
            
    class QSizeF:
        """模拟的QSizeF类，用于测试"""
        def __init__(self, width=0.0, height=0.0):
            self.width = float(width)
            self.height = float(height)
            
        def __eq__(self, other):
            return isinstance(other, QSizeF) and self.width == other.width and self.height == other.height
            
    class QRect:
        """模拟的QRect类，用于测试"""
        def __init__(self, x=0, y=0, width=0, height=0):
            self.x = x
            self.y = y
            self.width = width
            self.height = height
            
        def __eq__(self, other):
            return isinstance(other, QRect) and self.x == other.x and self.y == other.y and \
                   self.width == other.width and self.height == other.height
                   
        def contains(self, point):
            """检查矩形是否包含点"""
            if isinstance(point, (QPoint, QPointF)):
                return (self.x <= point.x <= self.x + self.width and 
                        self.y <= point.y <= self.y + self.height)
            return False
            
        def intersects(self, rect):
            """检查矩形是否与另一个矩形相交"""
            return not (self.x + self.width < rect.x or 
                       rect.x + rect.width < self.x or 
                       self.y + self.height < rect.y or 
                       rect.y + rect.height < self.y)
                       
    class QRectF:
        """模拟的QRectF类，用于测试"""
        def __init__(self, x=0.0, y=0.0, width=0.0, height=0.0):
            self.x = float(x)
            self.y = float(y)
            self.width = float(width)
            self.height = float(height)
            
        def __eq__(self, other):
            return isinstance(other, QRectF) and self.x == other.x and self.y == other.y and \
                   self.width == other.width and self.height == other.height
                   
        def contains(self, point):
            """检查矩形是否包含点"""
            if isinstance(point, (QPoint, QPointF)):
                return (self.x <= point.x <= self.x + self.width and 
                        self.y <= point.y <= self.y + self.height)
            return False
            
        def intersects(self, rect):
            """检查矩形是否与另一个矩形相交"""
            return not (self.x + self.width < rect.x or 
                       rect.x + rect.width < self.x or 
                       self.y + self.height < rect.y or 
                       rect.y + rect.height < self.y)
                       
    class QLineF:
        """模拟的QLineF类，用于测试"""
        def __init__(self, x1=0.0, y1=0.0, x2=0.0, y2=0.0):
            self.x1 = float(x1)
            self.y1 = float(y1)
            self.x2 = float(x2)
            self.y2 = float(y2)
            
        def __eq__(self, other):
            return isinstance(other, QLineF) and self.x1 == other.x1 and self.y1 == other.y1 and \
                   self.x2 == other.x2 and self.y2 == other.y2

    # 模拟事件类
    class QMouseEvent:
        """模拟的QMouseEvent类，用于测试"""
        
        def __init__(self, event_type, pos, button=None, buttons=None, modifiers=None, source=None):
            """初始化鼠标事件
            
            Args:
                event_type: 事件类型
                pos: 鼠标位置（QPoint或QPointF）
                button: 按下的按钮
                buttons: 当前按下的所有按钮
                modifiers: 修饰键状态
                source: 事件源设备
            """
            self.type = event_type
            self.pos_value = pos
            self.button_value = button or Qt.LeftButton
            self.buttons_value = buttons or Qt.LeftButton
            self.modifiers_value = modifiers
            self.accepted = False
            self.source_value = source
        
        def pos(self):
            """获取鼠标位置"""
            return self.pos_value
        
        def button(self):
            """获取按下的按钮"""
            return self.button_value
        
        def buttons(self):
            """获取当前按下的所有按钮"""
            return self.buttons_value
        
        def modifiers(self):
            """获取修饰键状态"""
            return self.modifiers_value
        
        def x(self):
            """获取X坐标"""
            return self.pos_value.x if hasattr(self.pos_value, 'x') else 0
        
        def y(self):
            """获取Y坐标"""
            return self.pos_value.y if hasattr(self.pos_value, 'y') else 0
        
        def globalPos(self):
            """获取全局坐标，在模拟中与局部坐标相同"""
            return self.pos_value
        
        def accept(self):
            """接受事件"""
            self.accepted = True
        
        def ignore(self):
            """忽略事件"""
            self.accepted = False
        
        def isAccepted(self):
            """检查事件是否被接受"""
            return self.accepted
        
        def source(self):
            """获取事件源设备"""
            return self.source_value

    # 将模拟的类组织成类似PyQt6的结构
    class QtWidgets:
        QSystemTrayIcon = QSystemTrayIcon
        QMenu = QMenu
        QAction = QAction  # 在QtWidgets中也提供QAction，以兼容从QtWidgets导入的代码
        
    class QtGui:
        QIcon = QIcon
        QAction = QAction
        QMouseEvent = QMouseEvent
        
    class QtCore:
        QObject = QObject
        pyqtSignal = pyqtSignal
        Qt = Qt
        QPoint = QPoint
        QPointF = QPointF
        QSize = QSize
        QSizeF = QSizeF
        QRect = QRect
        QRectF = QRectF
        QLineF = QLineF
        QTimer = QTimer
        
    class PyQt6:
        QtWidgets = QtWidgets
        QtGui = QtGui
        QtCore = QtCore
        
    # 将模拟模块添加到sys.modules中
    sys.modules['PyQt6'] = PyQt6
    sys.modules['PyQt6.QtWidgets'] = QtWidgets
    sys.modules['PyQt6.QtGui'] = QtGui
    sys.modules['PyQt6.QtCore'] = QtCore
    
    print("已成功设置PyQt6模拟模块")

# 在设置完模拟模块后，导入和运行测试
import unittest

# 运行指定的测试文件
def run_test(test_path):
    """运行指定的测试文件
    
    Args:
        test_path (str): 测试文件路径
    """
    print(f"运行测试: {test_path}")
    
    # 构建测试套件
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=os.path.dirname(test_path), 
                           pattern=os.path.basename(test_path))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回测试结果
    return result.wasSuccessful()

if __name__ == "__main__":
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="运行测试")
    parser.add_argument("test_path", nargs="?", default="tests",
                       help="要运行的测试文件或目录路径")
    args = parser.parse_args()
    
    # 运行测试
    success = run_test(args.test_path)
    
    # 根据测试结果设置退出码
    sys.exit(0 if success else 1) 