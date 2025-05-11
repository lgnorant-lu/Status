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
                            2025/05/15: 将PyQt6导入改为PySide6以统一项目Qt库使用;
                            2025/05/16: 修复PySide6导入和screens方法访问问题;
                            2025/05/16: 修复文件编码问题;
                            2025/05/16: 彻底重写，解决编码null字节问题;
----
"""

from PySide6.QtCore import QRect, QPoint, QSize
from PySide6.QtGui import QGuiApplication, QScreen
import logging
import platform
import sys

from status.core.events import EventManager, Event

logger = logging.getLogger(__name__)


class EnvironmentEvent(Event):
    """环境事件"""
    
    SCREEN_CHANGE = "environment.screen_change"
    WINDOW_MOVE = "environment.window_move"
    DESKTOP_OBJECTS_CHANGE = "environment.desktop_objects_change"
    
    def __init__(self, event_type, data=None):
        """
        初始化事件
        
        Args:
            event_type (str): 事件类型
            data (dict, optional): 事件相关数据
        """
        super().__init__(event_type)
        self.data = data or {}


class DesktopObject:
    """桌面对象，表示一个窗口或桌面区域"""
    
    def __init__(self, handle=None, title="", rect=None, process_name="", visible=True):
        """
        初始化桌面对象
        
        Args:
            handle: 窗口句柄或桌面区域标识
            title (str): 窗口或桌面区域的标题
            rect (QRect): 窗口或桌面区域的矩形范围
            process_name (str): 窗口或桌面区域的进程名
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
    环境传感器，负责感知桌面环境
    
    使用屏幕信息和窗口信息来检测环境变化，并通知事件。
    可以检测桌面上的所有窗口和桌面区域。
    """
    
    _instance = None
    _mock_mode = False
    _mock_screen_info = {}
    _mock_window_info = {}
    _mock_desktop_objects = []
    
    @classmethod
    def get_instance(cls):
        """
        获取环境传感器实例
        
        Returns:
            EnvironmentSensor: 环境传感器实例
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def enable_mock_mode(cls, enable=True):
        """
        启用模拟模式
        
        Args:
            enable (bool): 是否启用模拟模式
        """
        cls._mock_mode = enable
        if enable:
            # 初始化模拟屏幕信息
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
            screen_info (dict): 模拟屏幕信息
        """
        cls._mock_screen_info = screen_info
    
    @classmethod
    def set_mock_window_info(cls, window_info):
        """
        设置模拟窗口信息
        
        Args:
            window_info (dict): 模拟窗口信息
        """
        cls._mock_window_info = window_info
    
    @classmethod
    def set_mock_desktop_objects(cls, desktop_objects):
        """
        设置模拟桌面对象
        
        Args:
            desktop_objects (list): 模拟桌面对象列表
        """
        cls._mock_desktop_objects = desktop_objects
    
    def __init__(self):
        """初始化环境传感器"""
        if EnvironmentSensor._instance is not None:
            raise RuntimeError("EnvironmentSensor实例已存在，请使用get_instance()获取实例")
        
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
        初始化环境传感器
        
        Args:
            event_manager (EventManager, optional): 事件管理器
            active_window: 活动窗口或桌面区域
        """
        if self._initialized:
            return
        
        self._event_manager = event_manager
        self._active_window = active_window
        self._update_screen_info()
        self._update_window_info()
        self._update_desktop_objects()
        
        self._initialized = True
        logger.info("环境传感器初始化完成")
    
    def _update_screen_info(self):
        """更新屏幕信息"""
        if EnvironmentSensor._mock_mode:
            self._screen_info = EnvironmentSensor._mock_screen_info
            return
            
        self._screen_info = {}
        
        try:
            # 获取主屏幕
            primary_screen = QGuiApplication.primaryScreen()
            if primary_screen:
                # 添加主屏幕
                geometry = primary_screen.geometry()
                self._screen_info[0] = {
                    'geometry': geometry,
                    'width': geometry.width(),
                    'height': geometry.height(),
                    'x': geometry.x(),
                    'y': geometry.y(),
                    'name': primary_screen.name(),
                    'scale_factor': primary_screen.devicePixelRatio(),
                    'primary': True
                }
            logger.debug(f"已更新屏幕信息: {len(self._screen_info)}个屏幕")
        except Exception as e:
            logger.error(f"更新屏幕信息失败: {e}")
    
    def _update_window_info(self):
        """更新窗口信息"""
        if EnvironmentSensor._mock_mode:
            self._window_info = EnvironmentSensor._mock_window_info
            return
            
        if self._active_window is None:
            # 没有活动窗口，使用默认值
            self._window_info = {
                'geometry': QRect(0, 0, 800, 600),
                'width': 800,
                'height': 600,
                'x': 0,
                'y': 0
            }
        else:
            # 获取活动窗口的几何信息
            geometry = self._active_window.geometry()
            self._window_info = {
                'geometry': geometry,
                'width': geometry.width(),
                'height': geometry.height(),
                'x': geometry.x(),
                'y': geometry.y()
            }
        logger.debug(f"已更新窗口信息: {self._window_info}")
    
    def _update_desktop_objects(self):
        """更新桌面对象"""
        if EnvironmentSensor._mock_mode:
            self._desktop_objects = EnvironmentSensor._mock_desktop_objects
            return
            
        # 默认实现不检测任何对象，子类应重写此方法
        logger.debug("更新桌面对象 (默认实现)")
    
    def _notify_environment_change(self, event_type, data=None):
        """
        通知环境变化
        
        Args:
            event_type (str): 事件类型
            data (dict, optional): 事件相关数据
        """
        # 通知回调函数
        for callback in self._callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                logger.error(f"通知回调函数失败: {e}")
        
        # 通知事件管理器
        if self._event_manager:
            event = EnvironmentEvent(event_type, data)
            self._event_manager.dispatch(event)
        
        logger.debug(f"环境变化: {event_type}")
    
    def get_screen_boundaries(self, screen_index=0):
        """
        获取屏幕边界信息
        
        Args:
            screen_index (int): 屏幕索引，0表示主屏幕
        
        Returns:
            dict: 屏幕边界信息，包含x、y、width、height等
        """
        # 确保屏幕信息已更新
        if not self._screen_info:
            self._update_screen_info()
        
        # 没有指定索引的屏幕，返回第一个屏幕
        if screen_index not in self._screen_info:
            if self._screen_info:
                screen_index = list(self._screen_info.keys())[0]
            else:
                # 没有任何屏幕信息，返回默认值
                return {
                    'geometry': QRect(0, 0, 1920, 1080),
                    'width': 1920,
                    'height': 1080,
                    'x': 0,
                    'y': 0,
                    'name': 'Default Screen',
                    'scale_factor': 1.0,
                    'primary': True
                }
        
        return self._screen_info[screen_index]
    
    def get_all_screens(self):
        """
        获取所有屏幕信息
        
        Returns:
            dict: 所有屏幕信息的字典，键为屏幕索引
        """
        # 确保屏幕信息已更新
        if not self._screen_info:
            self._update_screen_info()
        
        return self._screen_info
    
    def get_primary_screen(self):
        """
        获取主屏幕信息
        
        Returns:
            dict: 主屏幕信息
        """
        # 确保屏幕信息已更新
        if not self._screen_info:
            self._update_screen_info()
        
        # 查找主屏幕
        for screen_info in self._screen_info.values():
            if screen_info.get('primary', False):
                return screen_info
        
        # 没有找到主屏幕，返回第一个屏幕
        if self._screen_info:
            return list(self._screen_info.values())[0]
        
        # 没有任何屏幕信息，返回默认值
        return {
            'geometry': QRect(0, 0, 1920, 1080),
            'width': 1920,
            'height': 1080,
            'x': 0,
            'y': 0,
            'name': 'Default Screen',
            'scale_factor': 1.0,
            'primary': True
        }
    
    def get_window_position(self, window=None):
        """
        获取窗口位置
        
        Args:
            window: 窗口对象，None表示活动窗口
        
        Returns:
            QRect: 窗口矩形区域
        """
        if window is not None:
            # 获取指定窗口的位置
            try:
                return window.geometry()
            except Exception as e:
                logger.error(f"获取窗口位置失败: {e}")
                return QRect(0, 0, 800, 600)
        
        # 确保窗口信息已更新
        if not self._window_info:
            self._update_window_info()
        
        return self._window_info.get('geometry', QRect(0, 0, 800, 600))
    
    def set_active_window(self, window):
        """
        设置活动窗口
        
        Args:
            window: 活动窗口对象
        """
        self._active_window = window
        self._update_window_info()
        logger.debug(f"设置活动窗口: {window}")
    
    def detect_desktop_objects(self, filter_func=None):
        """
        检测桌面对象
        
        Args:
            filter_func (callable, optional): 过滤函数，接受DesktopObject参数并返回布尔值
        
        Returns:
            list: 桌面对象列表
        """
        # 确保桌面对象已更新
        if not self._desktop_objects:
            self._update_desktop_objects()
        
        # 如果指定了过滤函数，则过滤对象
        if filter_func is not None:
            try:
                return [obj for obj in self._desktop_objects if filter_func(obj)]
            except Exception as e:
                logger.error(f"过滤桌面对象失败: {e}")
                return []
        
        return self._desktop_objects
    
    def is_window_visible(self, point_or_rect):
        """
        检查窗口是否在屏幕上可见
        
        Args:
            point_or_rect: 点或矩形区域
        
        Returns:
            bool: 是否可见
        """
        # 获取所有屏幕信息
        screens = self.get_all_screens()
        
        # 如果没有屏幕信息，返回False
        if not screens:
            return False
        
        # 检查点或矩形区域是否在任何屏幕上可见
        for screen_info in screens.values():
            screen_rect = screen_info['geometry']
            
            # 如果是点
            if isinstance(point_or_rect, QPoint):
                if screen_rect.contains(point_or_rect):
                    return True
            # 如果是矩形区域
            elif isinstance(point_or_rect, QRect):
                if screen_rect.intersects(point_or_rect):
                    return True
            else:
                logger.error(f"无效的参数类型: {type(point_or_rect)}")
                return False
        
        return False
    
    def get_screen_at_point(self, point):
        """
        获取包含指定点的屏幕信息
        
        Args:
            point (QPoint): 点坐标
        
        Returns:
            dict: 屏幕信息
        """
        # 获取所有屏幕信息
        screens = self.get_all_screens()
        
        # 如果没有屏幕信息，返回默认值
        if not screens:
            return self.get_primary_screen()
        
        # 查找包含指定点的屏幕
        for screen_info in screens.values():
            screen_rect = screen_info['geometry']
            if screen_rect.contains(point):
                return screen_info
        
        # 如果没有找到包含指定点的屏幕，返回主屏幕
        return self.get_primary_screen()
    
    def register_callback(self, callback):
        """
        注册环境变化回调函数
        
        Args:
            callback (callable): 回调函数，接受event_type和data参数
        
        Returns:
            bool: 是否注册成功
        """
        if not callable(callback):
            logger.error(f"无效的回调函数: {callback}")
            return False
        
        if callback not in self._callbacks:
            self._callbacks.append(callback)
            logger.debug(f"注册回调函数: {callback}")
            return True
        
        return False
    
    def unregister_callback(self, callback):
        """
        取消注册环境变化回调函数
        
        Args:
            callback (callable): 回调函数
        
        Returns:
            bool: 是否取消注册成功
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            logger.debug(f"取消注册回调函数: {callback}")
            return True
        
        return False
    
    def update(self):
        """
        更新环境信息
        
        检测环境变化并通知回调函数和事件管理器。
        """
        # 保存旧的环境信息
        old_screen_info = self._screen_info.copy()
        old_window_info = self._window_info.copy()
        old_desktop_objects = self._desktop_objects.copy()
        
        # 更新环境信息
        self._update_screen_info()
        self._update_window_info()
        self._update_desktop_objects()
        
        # 检测变化并通知
        if self._screen_info != old_screen_info:
            self._notify_environment_change(EnvironmentEvent.SCREEN_CHANGE, {
                'old_screen_info': old_screen_info,
                'new_screen_info': self._screen_info
            })
        
        if self._window_info != old_window_info:
            self._notify_environment_change(EnvironmentEvent.WINDOW_MOVE, {
                'old_window_info': old_window_info,
                'new_window_info': self._window_info
            })
        
        if self._desktop_objects != old_desktop_objects:
            self._notify_environment_change(EnvironmentEvent.DESKTOP_OBJECTS_CHANGE, {
                'old_desktop_objects': old_desktop_objects,
                'new_desktop_objects': self._desktop_objects
            })
        
        logger.debug("环境信息已更新")


# Windows平台特定优化
try:
    import ctypes
    from ctypes import windll, Structure, byref
    import win32gui
    import win32process
    import win32con
    import psutil
    
    # 定义Windows API使用的结构体
    class RECT(Structure):
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long)
        ]
    
    class MONITORINFO(Structure):
        _fields_ = [
            ("cbSize", ctypes.c_ulong),
            ("rcMonitor", RECT),
            ("rcWork", RECT),
            ("dwFlags", ctypes.c_ulong)
        ]
    
    class POINT(Structure):
        _fields_ = [
            ("x", ctypes.c_long),
            ("y", ctypes.c_long)
        ]
    
    class WindowsEnvironmentSensor(EnvironmentSensor):
        """Windows平台特定优化环境传感器"""
        
        def __init__(self):
            """初始化Windows环境传感器"""
            super().__init__()
            self._enum_windows_proc = None
        
        def _update_screen_info(self):
            """使用Windows API更新屏幕信息"""
            # 如果启用模拟模式，则使用模拟对象
            if EnvironmentSensor._mock_mode:
                self._screen_info = EnvironmentSensor._mock_screen_info
                return
                
            super()._update_screen_info()
            
            try:
                # 使用Windows API获取屏幕信息
                for idx, info in self._screen_info.items():
                    # 获取屏幕工作区域
                    monitor_info = MONITORINFO()
                    monitor_info.cbSize = ctypes.sizeof(MONITORINFO)
                    
                    # 创建POINT结构体
                    point = POINT()
                    point.x = info['x'] + info['width'] // 2
                    point.y = info['y'] + info['height'] // 2
                    
                    monitor = windll.user32.MonitorFromPoint(
                        point,
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
                    
                    # 获取DPI信息
                    try:
                        # Windows 10 1607及以上版本，获取进程DPI感知
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
                        # 如果无法获取DPI信息，则使用GDI获取默认DPI
                        hdc = windll.user32.GetDC(None)
                        info['dpi_x'] = windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
                        info['dpi_y'] = windll.gdi32.GetDeviceCaps(hdc, 90)  # LOGPIXELSY
                        windll.user32.ReleaseDC(None, hdc)
                
            except Exception as e:
                logger.error(f"获取Windows屏幕信息失败: {e}")
        
        def _update_window_info(self):
            """使用Windows API更新窗口信息"""
            # 如果启用模拟模式，则使用模拟对象
            if EnvironmentSensor._mock_mode:
                self._window_info = EnvironmentSensor._mock_window_info
                return
                
            super()._update_window_info()
            
            try:
                if self._active_window:
                    # 如果窗口是可见的，并且有句柄，则获取窗口信息
                    if hasattr(self._active_window, 'winId'):
                        hwnd = self._active_window.winId()
                        
                        # 获取窗口信息
                        rect = win32gui.GetWindowRect(hwnd)
                        title = win32gui.GetWindowText(hwnd)
                        
                        # 获取窗口样式信息
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
                    # 如果活动窗口不存在，则获取前台窗口信息
                    hwnd = win32gui.GetForegroundWindow()
                    if hwnd:
                        rect = win32gui.GetWindowRect(hwnd)
                        title = win32gui.GetWindowText(hwnd)
                        
                        # 获取前台窗口线程和进程ID
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
                logger.error(f"获取Windows窗口信息失败: {e}")
        
        def _enum_windows_callback(self, hwnd, results):
            """EnumWindows回调函数，用于检测所有窗口"""
            if not win32gui.IsWindowVisible(hwnd):
                return True
            
            # 过滤掉非顶级窗口和子窗口
            if win32gui.GetParent(hwnd) != 0:
                return True
                
            # 过滤掉没有标题的窗口
            title = win32gui.GetWindowText(hwnd)
            if not title:
                return True
            
            # 获取窗口位置和大小
            try:
                rect = win32gui.GetWindowRect(hwnd)
                
                # 过滤掉无效的窗口
                if rect[0] == -32000 or rect[1] == -32000:
                    return True
                
                # 过滤掉太小或太小的窗口
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
                if width < 50 or height < 50:
                    return True
                
                # 获取窗口线程和进程ID
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
                logger.error(f"获取窗口信息失败: {e}")
            
            return True
        
        def _update_desktop_objects(self):
            """使用Windows API更新桌面对象信息"""
            # 如果启用模拟模式，则使用模拟对象
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
                
                # 注册回调函数
                self._enum_windows_proc = callback_type(
                    lambda hwnd, results: self._enum_windows_callback(hwnd, results)
                )
                
                # 遍历所有窗口
                windll.user32.EnumWindows(self._enum_windows_proc, ctypes.py_object(objects))
                
                # 更新桌面对象信息
                self._desktop_objects = objects
                
                logger.debug(f"检测到 {len(self._desktop_objects)} 个桌面对象")
                
            except Exception as e:
                logger.error(f"更新Windows桌面对象信息失败: {e}")
                # 如果失败，则清空所有桌面对象
                self._desktop_objects = []
    
    # 如果环境传感器实例不存在，并且是Windows平台，则尝试初始化Windows环境传感器
    if EnvironmentSensor._instance is None and platform.system() == "Windows":
        try:
            EnvironmentSensor._instance = WindowsEnvironmentSensor()
            logger.info("启用Windows桌面对象检测")
        except Exception as e:
            logger.warning(f"无法初始化Windows环境传感器: {e}")
            # 如果失败，则清空所有环境传感器实例
            EnvironmentSensor._instance = None
        
except ImportError as e:
    # 如果无法导入Windows模块，则提示并忽略
    logger.info(f"无法初始化环境传感器: {e}")
    pass 
