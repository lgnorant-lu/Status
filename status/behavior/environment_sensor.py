"""
---------------------------------------------------------------
File name:                  environment_sensor.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                环境感知器，负责感知桌面环境
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
                            2025/04/04: 增强Windows平台特定优化;
                            2025/04/04: 修复Windows特定实现问题;
                            2025/04/04: 添加mock机制支持单元测试;
----
"""

from PyQt6.QtCore import QRect, QPoint, QSize
from PyQt6.QtGui import QGuiApplication, QScreen
import logging
import platform
import sys

from status.core.events import EventManager, Event

logger = logging.getLogger(__name__)


class EnvironmentEvent(Event):
    """环境变化事件类型"""
    
    SCREEN_CHANGE = "environment.screen_change"
    WINDOW_MOVE = "environment.window_move"
    DESKTOP_OBJECTS_CHANGE = "environment.desktop_objects_change"
    
    def __init__(self, event_type, data=None):
        """
        初始化环境事件
        
        Args:
            event_type (str): 事件类型
            data (dict, optional): 事件相关数据
        """
        super().__init__(event_type)
        self.data = data or {}


class DesktopObject:
    """桌面对象类，表示桌面上的窗口或其他对象"""
    
    def __init__(self, handle=None, title="", rect=None, process_name="", visible=True):
        """
        初始化桌面对象
        
        Args:
            handle: 窗口句柄或对象标识
            title (str): 窗口标题或对象名称
            rect (QRect): 对象的位置和大小
            process_name (str): 所属进程名称
            visible (bool): 是否可见
        """
        self.handle = handle
        self.title = title
        self.rect = rect or QRect()
        self.process_name = process_name
        self.visible = visible
    
    def __eq__(self, other):
        if not isinstance(other, DesktopObject):
            return False
        return (self.handle == other.handle and
                self.title == other.title and
                self.rect == other.rect and
                self.process_name == other.process_name and
                self.visible == other.visible)
    
    def __repr__(self):
        return f"DesktopObject(title='{self.title}', rect={self.rect}, process='{self.process_name}', visible={self.visible})"


class EnvironmentSensor:
    """
    环境感知器，负责感知桌面环境
    
    该类使用单例模式，提供对桌面环境的感知能力，包括屏幕边界、
    窗口位置和桌面物体检测等功能。
    """
    
    _instance = None
    _mock_mode = False
    _mock_screen_info = {}
    _mock_window_info = {}
    _mock_desktop_objects = []
    
    @classmethod
    def get_instance(cls):
        """
        获取环境感知器实例
        
        Returns:
            EnvironmentSensor: 环境感知器单例实例
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def enable_mock_mode(cls, enable=True):
        """
        启用或禁用模拟模式（用于测试）
        
        Args:
            enable (bool): 是否启用模拟模式
        """
        cls._mock_mode = enable
        if enable:
            # 设置默认模拟数据
            cls._mock_screen_info = {
                0: {
                    'geometry': QRect(0, 0, 1920, 1080),
                    'width': 1920,
                    'height': 1080,
                    'x': 0,
                    'y': 0,
                    'name': 'Mock Screen',
                    'scale_factor': 1.0,
                    'primary': True
                }
            }
            cls._mock_window_info = {
                'geometry': QRect(100, 100, 800, 600),
                'width': 800,
                'height': 600,
                'x': 100,
                'y': 100
            }
            cls._mock_desktop_objects = []
    
    @classmethod
    def set_mock_screen_info(cls, screen_info):
        """
        设置模拟屏幕信息
        
        Args:
            screen_info (dict): 模拟的屏幕信息
        """
        cls._mock_screen_info = screen_info
    
    @classmethod
    def set_mock_window_info(cls, window_info):
        """
        设置模拟窗口信息
        
        Args:
            window_info (dict): 模拟的窗口信息
        """
        cls._mock_window_info = window_info
    
    @classmethod
    def set_mock_desktop_objects(cls, desktop_objects):
        """
        设置模拟桌面对象
        
        Args:
            desktop_objects (list): 模拟的桌面对象列表
        """
        cls._mock_desktop_objects = desktop_objects
    
    def __init__(self):
        """初始化环境感知器"""
        if EnvironmentSensor._instance is not None:
            raise RuntimeError("EnvironmentSensor已存在，请使用get_instance()获取实例")
        
        self._screen_info = {}
        self._window_info = {}
        self._desktop_objects = []
        self._callbacks = []
        self._event_manager = None
        self._initialized = False
        self._active_window = None
        self._platform = platform.system()
    
    def initialize(self, event_manager=None, active_window=None):
        """
        初始化环境感知器
        
        Args:
            event_manager (EventManager, optional): 事件管理器
            active_window: 当前活动窗口对象
        """
        if self._initialized:
            return
        
        self._event_manager = event_manager
        self._active_window = active_window
        self._update_screen_info()
        self._update_window_info()
        self._update_desktop_objects()
        
        # 注册屏幕变化事件处理
        if self._event_manager:
            # 这里可以注册对应的系统事件，如屏幕分辨率变化等
            pass
        
        self._initialized = True
        logger.info(f"环境感知器初始化完成 (平台: {self._platform})")
    
    def _update_screen_info(self):
        """更新屏幕信息"""
        if EnvironmentSensor._mock_mode:
            self._screen_info = EnvironmentSensor._mock_screen_info
            return
            
        self._screen_info = {}
        
        app = QGuiApplication.instance()
        if app:
            for i, screen in enumerate(app.screens()):
                geometry = screen.geometry()
                self._screen_info[i] = {
                    'geometry': geometry,
                    'width': geometry.width(),
                    'height': geometry.height(),
                    'x': geometry.x(),
                    'y': geometry.y(),
                    'name': screen.name(),
                    'scale_factor': screen.devicePixelRatio(),
                    'primary': screen.virtualGeometry() == QGuiApplication.primaryScreen().virtualGeometry()
                }
                
        logger.debug(f"更新屏幕信息: {len(self._screen_info)}个屏幕")
    
    def _update_window_info(self):
        """更新窗口信息"""
        if EnvironmentSensor._mock_mode:
            self._window_info = EnvironmentSensor._mock_window_info
            return
            
        self._window_info = {}
        
        if self._active_window:
            if hasattr(self._active_window, 'geometry'):
                geometry = self._active_window.geometry()
                self._window_info = {
                    'geometry': geometry,
                    'width': geometry.width(),
                    'height': geometry.height(),
                    'x': geometry.x(),
                    'y': geometry.y()
                }
            
        logger.debug(f"更新窗口信息: {self._window_info}")
    
    def _update_desktop_objects(self):
        """更新桌面对象信息"""
        # 如果是模拟模式，使用模拟数据
        if EnvironmentSensor._mock_mode:
            self._desktop_objects = EnvironmentSensor._mock_desktop_objects
            return
            
        # 基类中仅提供一个空实现，由平台特定实现覆盖
        self._desktop_objects = []
    
    def _notify_environment_change(self, event_type, data=None):
        """
        通知环境变化
        
        Args:
            event_type (str): 事件类型
            data (dict, optional): 事件数据
        """
        # 调用注册的回调函数
        for callback in self._callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                logger.error(f"调用环境变化回调函数出错: {e}")
        
        # 发送事件
        if self._event_manager:
            event = EnvironmentEvent(event_type, data)
            self._event_manager.dispatch(event)
    
    def get_screen_boundaries(self, screen_index=0):
        """
        获取屏幕边界信息
        
        Args:
            screen_index (int, optional): 屏幕索引，默认为主屏幕
            
        Returns:
            dict: 包含屏幕边界信息的字典
        """
        if not self._initialized:
            self.initialize()
            
        if screen_index in self._screen_info:
            return self._screen_info[screen_index]
        elif len(self._screen_info) > 0:
            # 尝试找主屏幕
            for idx, info in self._screen_info.items():
                if info.get('primary', False):
                    return info
            # 否则返回第一个
            return next(iter(self._screen_info.values()))
        else:
            logger.warning("无法获取屏幕信息")
            return {'width': 1920, 'height': 1080, 'x': 0, 'y': 0}
    
    def get_all_screens(self):
        """
        获取所有屏幕信息
        
        Returns:
            dict: 包含所有屏幕信息的字典
        """
        if not self._initialized:
            self.initialize()
            
        return self._screen_info
    
    def get_primary_screen(self):
        """
        获取主屏幕信息
        
        Returns:
            dict: 包含主屏幕信息的字典
        """
        if not self._initialized:
            self.initialize()
            
        for idx, info in self._screen_info.items():
            if info.get('primary', False):
                return info
                
        # 如果没有找到主屏幕，返回第一个屏幕
        if len(self._screen_info) > 0:
            return next(iter(self._screen_info.values()))
            
        logger.warning("无法获取主屏幕信息")
        return {'width': 1920, 'height': 1080, 'x': 0, 'y': 0}
    
    def get_window_position(self, window=None):
        """
        获取窗口位置
        
        Args:
            window (object, optional): 窗口对象，如果为None则获取当前应用窗口
            
        Returns:
            QRect: 窗口位置和大小
        """
        if not self._initialized:
            self.initialize()
            
        target_window = window or self._active_window
        
        if target_window and hasattr(target_window, 'geometry'):
            return target_window.geometry()
            
        return QRect(0, 0, 800, 600)  # 默认值
    
    def set_active_window(self, window):
        """
        设置当前活动窗口
        
        Args:
            window: 窗口对象
        """
        if self._active_window != window:
            self._active_window = window
            self._update_window_info()
    
    def detect_desktop_objects(self, filter_func=None):
        """
        检测桌面上的其他窗口或对象
        
        Args:
            filter_func (callable, optional): 过滤函数，接收DesktopObject参数，返回布尔值
            
        Returns:
            list: 桌面对象列表
        """
        if not self._initialized:
            self.initialize()
            
        # 确保对象列表是最新的
        self._update_desktop_objects()
        
        if filter_func:
            return [obj for obj in self._desktop_objects if filter_func(obj)]
        
        return self._desktop_objects
    
    def is_window_visible(self, point_or_rect):
        """
        检查指定点或区域是否在任何屏幕内
        
        Args:
            point_or_rect: QPoint或QRect对象，表示要检查的点或区域
            
        Returns:
            bool: 如果点或区域至少部分在任何屏幕内，则为True
        """
        if not self._initialized:
            self.initialize()
            
        # 确保屏幕信息是最新的
        self._update_screen_info()
        
        # 检查每个屏幕
        for info in self._screen_info.values():
            screen_rect = info['geometry']
            
            if isinstance(point_or_rect, QPoint):
                if screen_rect.contains(point_or_rect):
                    return True
            elif isinstance(point_or_rect, QRect):
                if screen_rect.intersects(point_or_rect):
                    return True
        
        return False
    
    def get_screen_at_point(self, point):
        """
        获取包含指定点的屏幕信息
        
        Args:
            point (QPoint): 要检查的点
            
        Returns:
            dict: 包含点的屏幕信息，如果没有则返回主屏幕
        """
        if not self._initialized:
            self.initialize()
            
        # 确保屏幕信息是最新的
        self._update_screen_info()
        
        # 检查每个屏幕
        for idx, info in self._screen_info.items():
            if info['geometry'].contains(point):
                return info
        
        # 如果没有找到，返回主屏幕
        return self.get_primary_screen()
    
    def register_callback(self, callback):
        """
        注册环境变化回调函数
        
        Args:
            callback (callable): 回调函数，接收事件类型和数据作为参数
            
        Returns:
            bool: 注册是否成功
        """
        if callable(callback) and callback not in self._callbacks:
            self._callbacks.append(callback)
            return True
        return False
    
    def unregister_callback(self, callback):
        """
        取消注册环境变化回调函数
        
        Args:
            callback (callable): 之前注册的回调函数
            
        Returns:
            bool: 取消注册是否成功
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            return True
        return False
    
    def update(self):
        """
        更新环境信息
        
        该方法应定期调用以更新环境状态
        """
        if not self._initialized:
            self.initialize()
            
        # 保存旧状态用于比较
        old_screen_info = {k: v.copy() for k, v in self._screen_info.items()} if self._screen_info else {}
        old_window_info = self._window_info.copy() if self._window_info else {}
        old_desktop_objects = self._desktop_objects.copy() if self._desktop_objects else []
        
        # 更新状态
        self._update_screen_info()
        self._update_window_info()
        self._update_desktop_objects()
        
        # 检测变化并通知
        if old_screen_info != self._screen_info:
            self._notify_environment_change(EnvironmentEvent.SCREEN_CHANGE, {'screen_info': self._screen_info})
            
        if old_window_info != self._window_info:
            self._notify_environment_change(EnvironmentEvent.WINDOW_MOVE, {'window_info': self._window_info})
            
        if old_desktop_objects != self._desktop_objects:
            self._notify_environment_change(EnvironmentEvent.DESKTOP_OBJECTS_CHANGE, 
                                          {'desktop_objects': self._desktop_objects})


# Windows平台特定优化
try:
    import ctypes
    from ctypes import windll, Structure, wintypes, POINTER, byref
    import win32gui
    import win32process
    import win32con
    import psutil
    
    # 定义Windows API需要的结构体
    class RECT(Structure):
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long)
        ]
    
    class MONITORINFO(Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("rcMonitor", RECT),
            ("rcWork", RECT),
            ("dwFlags", wintypes.DWORD)
        ]
    
    class WindowsEnvironmentSensor(EnvironmentSensor):
        """Windows平台特定的环境感知器实现"""
        
        def __init__(self):
            """初始化Windows环境感知器"""
            super().__init__()
            self._enum_windows_proc = None
        
        def _update_screen_info(self):
            """使用Windows API更新屏幕信息"""
            # 如果是模拟模式，使用模拟数据
            if EnvironmentSensor._mock_mode:
                self._screen_info = EnvironmentSensor._mock_screen_info
                return
                
            super()._update_screen_info()
            
            try:
                # 获取额外的Windows特定屏幕信息
                for idx, info in self._screen_info.items():
                    # 获取工作区域（排除任务栏等）
                    monitor_info = MONITORINFO()
                    monitor_info.cbSize = ctypes.sizeof(MONITORINFO)
                    
                    monitor = windll.user32.MonitorFromPoint(
                        wintypes.POINT(info['x'] + info['width'] // 2, info['y'] + info['height'] // 2),
                        win32con.MONITOR_DEFAULTTONEAREST
                    )
                    
                    if windll.user32.GetMonitorInfoW(monitor, byref(monitor_info)):
                        work_rect = monitor_info.rcWork
                        info['work_area'] = {
                            'x': work_rect.left,
                            'y': work_rect.top,
                            'width': work_rect.right - work_rect.left,
                            'height': work_rect.bottom - work_rect.top
                        }
                    
                    # 添加DPI信息
                    try:
                        # Windows 10 1607及以上版本
                        awareness = ctypes.c_int()
                        windll.shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness))
                        info['dpi_awareness'] = awareness.value
                        
                        dpi_x = ctypes.c_uint()
                        dpi_y = ctypes.c_uint()
                        windll.shcore.GetDpiForMonitor(
                            monitor, 
                            0,  # MDT_EFFECTIVE_DPI
                            ctypes.byref(dpi_x),
                            ctypes.byref(dpi_y)
                        )
                        info['dpi_x'] = dpi_x.value
                        info['dpi_y'] = dpi_y.value
                    except (AttributeError, OSError):
                        # 旧版Windows或API调用失败
                        hdc = windll.user32.GetDC(None)
                        info['dpi_x'] = windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
                        info['dpi_y'] = windll.gdi32.GetDeviceCaps(hdc, 90)  # LOGPIXELSY
                        windll.user32.ReleaseDC(None, hdc)
                
            except Exception as e:
                logger.error(f"获取Windows屏幕信息出错: {e}")
        
        def _update_window_info(self):
            """使用Windows API更新窗口信息"""
            # 如果是模拟模式，使用模拟数据
            if EnvironmentSensor._mock_mode:
                self._window_info = EnvironmentSensor._mock_window_info
                return
                
            super()._update_window_info()
            
            try:
                if self._active_window:
                    # 如果有活动窗口对象，尝试获取其HWND
                    if hasattr(self._active_window, 'winId'):
                        hwnd = self._active_window.winId()
                        
                        # 获取窗口信息
                        rect = win32gui.GetWindowRect(hwnd)
                        title = win32gui.GetWindowText(hwnd)
                        
                        # 获取窗口样式
                        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                        
                        # 更新窗口信息
                        self._window_info.update({
                            'hwnd': hwnd,
                            'title': title,
                            'rect': rect,
                            'x': rect[0],
                            'y': rect[1],
                            'width': rect[2] - rect[0],
                            'height': rect[3] - rect[1],
                            'style': style,
                            'ex_style': ex_style,
                            'visible': bool(style & win32con.WS_VISIBLE),
                            'maximized': bool(style & win32con.WS_MAXIMIZE),
                            'minimized': bool(style & win32con.WS_MINIMIZE)
                        })
                else:
                    # 如果没有活动窗口对象，尝试获取当前前台窗口
                    hwnd = win32gui.GetForegroundWindow()
                    if hwnd:
                        rect = win32gui.GetWindowRect(hwnd)
                        title = win32gui.GetWindowText(hwnd)
                        
                        # 获取进程信息
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        try:
                            process = psutil.Process(pid)
                            process_name = process.name()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            process_name = "unknown"
                        
                        # 更新窗口信息
                        self._window_info = {
                            'hwnd': hwnd,
                            'title': title,
                            'rect': rect,
                            'x': rect[0],
                            'y': rect[1],
                            'width': rect[2] - rect[0],
                            'height': rect[3] - rect[1],
                            'process_name': process_name,
                            'pid': pid
                        }
            
            except Exception as e:
                logger.error(f"获取Windows窗口信息出错: {e}")
        
        def _enum_windows_callback(self, hwnd, results):
            """EnumWindows回调函数，用于收集窗口信息"""
            if not win32gui.IsWindowVisible(hwnd):
                return True
            
            # 排除一些系统窗口
            if win32gui.GetParent(hwnd) != 0:
                return True
                
            # 排除没有标题的窗口
            title = win32gui.GetWindowText(hwnd)
            if not title:
                return True
            
            # 获取窗口位置和大小
            try:
                rect = win32gui.GetWindowRect(hwnd)
                
                # 排除最小化的窗口
                if rect[0] == -32000 or rect[1] == -32000:
                    return True
                
                # 排除太小的窗口（可能是系统托盘图标等）
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
                if width < 50 or height < 50:
                    return True
                
                # 获取进程信息
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    process = psutil.Process(pid)
                    process_name = process.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    process_name = "unknown"
                
                # 创建桌面对象
                desktop_obj = DesktopObject(
                    handle=hwnd,
                    title=title,
                    rect=QRect(rect[0], rect[1], width, height),
                    process_name=process_name,
                    visible=True
                )
                
                results.append(desktop_obj)
            
            except Exception as e:
                logger.error(f"枚举窗口信息出错: {e}")
            
            return True
        
        def _update_desktop_objects(self):
            """使用Windows API更新桌面对象信息"""
            # 如果是模拟模式，使用模拟数据
            if EnvironmentSensor._mock_mode:
                self._desktop_objects = EnvironmentSensor._mock_desktop_objects
                return
                
            try:
                objects = []
                callback_type = ctypes.WINFUNCTYPE(
                    ctypes.c_bool, 
                    ctypes.c_int, 
                    ctypes.py_object
                )
                
                # 保存回调引用，防止垃圾回收
                self._enum_windows_proc = callback_type(
                    lambda hwnd, results: self._enum_windows_callback(hwnd, results)
                )
                
                # 枚举所有顶级窗口
                windll.user32.EnumWindows(self._enum_windows_proc, ctypes.py_object(objects))
                
                # 更新桌面对象列表
                self._desktop_objects = objects
                
                logger.debug(f"检测到 {len(self._desktop_objects)} 个桌面对象")
                
            except Exception as e:
                logger.error(f"更新Windows桌面对象信息出错: {e}")
                # 确保即使出错也有一个有效的对象列表
                self._desktop_objects = []
    
    # 如果是Windows平台，使用Windows特定实现替换默认实现
    if EnvironmentSensor._instance is None and platform.system() == "Windows":
        try:
            EnvironmentSensor._instance = WindowsEnvironmentSensor()
            logger.info("使用Windows特定的环境感知器实现")
        except Exception as e:
            logger.warning(f"无法创建Windows特定环境感知器: {e}")
            # 出错时回退到基础实现
            EnvironmentSensor._instance = None
        
except ImportError as e:
    # 不是Windows平台或缺少必要库，使用默认实现
    logger.info(f"使用通用环境感知器实现 (导入错误: {e})")
    pass 