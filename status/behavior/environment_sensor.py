﻿"""
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
                            2025/05/18: 修复循环导入问题;
                            2025/05/18: 修复元类冲突问题;
                            2025/05/18: 修复类型注解问题;
                            2025/05/19: 进一步修复元类冲突问题，确保mypy兼容;
                            2025/05/19: 解决事件类型问题;
----
"""

from PySide6.QtCore import QRect, QPoint, QSize, QObject, Signal
from PySide6.QtGui import QGuiApplication, QScreen
import logging
import platform
import sys
from typing import Dict, List, Optional, Tuple, Any, Union, Callable, Type, cast
from abc import ABC, abstractmethod, ABCMeta
from threading import Thread, Event as ThreadEvent
import time
from enum import Enum, auto

from status.core.events import EventManager, Event, EventType
from status.core.event_system import EventType as OldEventType

# 移除循环导入
# from status.behavior.environment_sensor import WindowsEnvironmentSensor, MacEnvironmentSensor, LinuxEnvironmentSensor

logger = logging.getLogger(__name__)


# 环境事件类型
class EnvironmentEventType(Enum):
    """环境事件类型枚举"""
    SCREEN_CHANGE = auto()
    WINDOW_MOVE = auto()
    DESKTOP_OBJECTS_CHANGE = auto()


class EnvironmentEvent(Event):
    """环境事件"""
    
    def __init__(self, event_type: EnvironmentEventType, data: Optional[Dict[str, Any]] = None):
        """
        初始化事件
        
        Args:
            event_type: 事件类型
            data: 事件相关数据
        """
        # 将EnvironmentEventType映射为EventType.SYSTEM_STATUS_UPDATE
        super().__init__(EventType.SYSTEM_STATUS_UPDATE)
        # 保存原始环境事件类型
        self.environment_type = event_type
        # 为了测试兼容性，将type属性也设置为事件类型
        self.type = event_type  # type: ignore[assignment]
        self.data = data or {}


class DesktopObject:
    """桌面对象，表示一个窗口或桌面区域"""
    
    def __init__(self, handle: Any = None, title: str = "", rect: Optional[QRect] = None, 
                 process_name: str = "", visible: bool = True):
        """
        初始化桌面对象
        
        Args:
            handle: 窗口句柄或桌面区域标识
            title: 窗口或桌面区域的标题
            rect: 窗口或桌面区域的矩形范围
            process_name: 窗口或桌面区域的进程名
            visible: 是否可见
        """
        self.handle = handle
        self.title = title
        self.rect = rect or QRect()
        self.process_name = process_name
        self.visible = visible
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DesktopObject):
            return False
        return (self.handle == other.handle and
                self.title == other.title and
                self.rect == other.rect and
                self.process_name == other.process_name and
                self.visible == other.visible)
    
    def __repr__(self) -> str:
        return f"DesktopObject(title='{self.title}', rect={self.rect}, process='{self.process_name}', visible={self.visible})"


class EnvironmentData:
    """环境数据类，存储传感器收集的各种环境信息"""
    screen_info: Dict[int, Dict[str, Any]] = {}
    window_info: Dict[str, Any] = {}
    desktop_objects: List[DesktopObject] = []
    active_window: Optional[Dict[str, Any]] = None
    cursor_position: Optional[Tuple[int, int]] = None
    timestamp: float = 0.0


# 先定义一个创建QObject和ABC兼容的元类的函数
def qt_abc_metaclass():
    """创建兼容QObject和ABC的元类"""
    
    class _QtABCMeta(type(QObject), ABCMeta):
        """同时继承QObject的元类和ABCMeta"""
        pass
    
    return _QtABCMeta


# 使用修复的metaclass，现在它继承自ABCMeta，确保兼容性
class EnvironmentSensor(QObject, ABC, metaclass=qt_abc_metaclass()): # type: ignore[misc]
    """
    环境传感器，负责感知桌面环境
    
    使用屏幕信息和窗口信息来检测环境变化，并通知事件。
    可以检测桌面上的所有窗口和桌面区域。
    """
    
    _instance: Optional['EnvironmentSensor'] = None
    _mock_mode: bool = False
    _mock_screen_info: Dict[int, Dict[str, Any]] = {}
    _mock_window_info: Dict[str, Any] = {}
    _mock_desktop_objects: List[DesktopObject] = []
    
    data_updated = Signal(object)  # 使用object类型，因为EnvironmentData不是QObject
    error_occurred = Signal(str)
    
    @classmethod
    def get_instance(cls) -> 'EnvironmentSensor':
        """
        获取环境传感器实例
        
        Returns:
            EnvironmentSensor: 环境传感器实例
        """
        if cls._instance is None:
            if platform.system() == "Windows" and not EnvironmentSensor._mock_mode:
                # 使用显式导入
                from status.behavior.environment_sensor import WindowsEnvironmentSensor
                cls._instance = WindowsEnvironmentSensor()
            elif platform.system() == "Darwin" and not EnvironmentSensor._mock_mode:
                # MacOS
                from status.behavior.environment_sensor import MacEnvironmentSensor
                cls._instance = MacEnvironmentSensor()
            elif platform.system() == "Linux" and not EnvironmentSensor._mock_mode:
                # Linux
                from status.behavior.environment_sensor import LinuxEnvironmentSensor
                cls._instance = LinuxEnvironmentSensor()
            else:
                # 默认或模拟模式 - 这里需要使用正确的类型
                # 我们需要创建一个基本实现来避免抽象方法错误
                from status.behavior.environment_sensor import WindowsEnvironmentSensor
                cls._instance = WindowsEnvironmentSensor(mock=True)
        
        # 使用cast确保类型检查器理解返回类型
        return cast('EnvironmentSensor', cls._instance)
    
    @classmethod
    def enable_mock_mode(cls, enable: bool = True) -> None:
        """
        启用模拟模式
        
        Args:
            enable: 是否启用模拟模式
        """
        cls._mock_mode = enable
        if enable:
            # 初始化模拟屏幕信息
            mock_screen = {
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
            
            # 初始化模拟窗口信息
            mock_window = {
                'geometry': QRect(100, 100, 800, 600),
                'width': 800,
                'height': 600,
                'x': 100,
                'y': 100
            }
            
            # 设置模拟数据
            cls._mock_screen_info = mock_screen
            cls._mock_window_info = mock_window
            cls._mock_desktop_objects = []  # 空列表
    
    @classmethod
    def set_mock_screen_info(cls, screen_info: Dict[int, Dict[str, Any]]):
        """
        设置模拟屏幕信息
        
        Args:
            screen_info: 模拟屏幕信息
        """
        cls._mock_screen_info = screen_info
    
    @classmethod
    def set_mock_window_info(cls, window_info: Dict[str, Any]):
        """
        设置模拟窗口信息
        
        Args:
            window_info: 模拟窗口信息
        """
        cls._mock_window_info = window_info
    
    @classmethod
    def set_mock_desktop_objects(cls, desktop_objects: List[DesktopObject]):
        """
        设置模拟桌面对象
        
        Args:
            desktop_objects: 模拟桌面对象列表
        """
        cls._mock_desktop_objects = desktop_objects
    
    def __init__(self, update_interval: float = 5.0,
                 event_callback: Optional[Callable[[EnvironmentEventType, Any], None]] = None):
        """初始化环境传感器"""
        super().__init__()
        if EnvironmentSensor._instance is not None:
            raise RuntimeError("EnvironmentSensor实例已存在，请使用get_instance()获取实例")
        
        self._screen_info: Dict[int, Dict[str, Any]] = {}
        self._window_info: Dict[str, Any] = {}
        self._desktop_objects: List[DesktopObject] = []
        self._callbacks: List[Callable[[EnvironmentEventType, Any], None]] = []
        self._event_manager = None
        self._initialized = False
        self._active_window = None
        self._platform = platform.system()
        self._event_callback = event_callback
        self._current_data = EnvironmentData()
        self._update_interval = update_interval
        self._thread: Optional[Thread] = None
        self._stop_event = ThreadEvent()
        self._is_mock = False # Track mock status
    
    def initialize(self, event_manager=None, active_window=None):
        """
        初始化环境传感器
        
        Args:
            event_manager (EventManager, optional): 事件管理器
            active_window: 活动窗口或桌面区域
        """
        logger.info("环境传感器初始化中...")
        if event_manager:
            self._event_manager = event_manager
        self.set_active_window(active_window)
        
        # 获取初始环境数据并计算哈希值
        # 在模拟模式下，_get_environment_data 将使用预设的 mock 数据
        initial_data = self._get_environment_data()
        if initial_data:
            self._last_screen_hash = hash(repr(initial_data.screen_info))
            self._last_desktop_hash = hash(repr(initial_data.desktop_objects))
            self._last_screen_details = dict(initial_data.screen_info)
            logger.debug(f"环境传感器初始化: _last_screen_hash={self._last_screen_hash}, _last_desktop_hash={self._last_desktop_hash}")
        else:
            logger.warning("环境传感器初始化: _get_environment_data 返回 None")

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
    
    def _notify_environment_change(self, event_type: EnvironmentEventType, data=None):
        """通知环境变化事件"""
        # logger.debug(f"环境传感器准备通知事件: {event_type}")
        event = EnvironmentEvent(event_type, data)
        if self._event_manager:
            # logger.debug(f"环境传感器正在分发事件: {event.type}, data: {event.data}")
            # self._event_manager.dispatch(event) # 旧的调用
            self._event_manager.emit(OldEventType.SYSTEM_STATUS_UPDATE, event) # 新的调用
        
        # 调用已注册的回调函数
        for callback in self._callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                logger.error(f"通知回调函数失败: {e}")
        
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
            self._notify_environment_change(EnvironmentEventType.SCREEN_CHANGE, {
                'old_screen_info': old_screen_info,
                'new_screen_info': self._screen_info
            })
        
        if self._window_info != old_window_info:
            self._notify_environment_change(EnvironmentEventType.WINDOW_MOVE, {
                'old_window_info': old_window_info,
                'new_window_info': self._window_info
            })
        
        if self._desktop_objects != old_desktop_objects:
            self._notify_environment_change(EnvironmentEventType.DESKTOP_OBJECTS_CHANGE, {
                'old_desktop_objects': old_desktop_objects,
                'new_desktop_objects': self._desktop_objects
            })
        
        logger.debug("环境信息已更新")

    def _run(self):
        while not self._stop_event.is_set():
            try:
                new_data = self._get_environment_data()
                # Simple check: emit if active window changed or timestamp difference > threshold?
                # For now, emit every time
                self._current_data = new_data
                self.data_updated.emit(self._current_data)
            except Exception as e:
                logger.error(f"Error in environment sensor loop: {e}", exc_info=True)
                self.error_occurred.emit(f"Sensor loop error: {e}")
            time.sleep(self._update_interval)

    @abstractmethod
    def _get_environment_data(self) -> EnvironmentData:
        """Platform-specific method to gather all environment data."""
        pass

    def get_current_data(self) -> EnvironmentData:
        """获取当前缓存的环境数据"""
        return self._current_data

    @classmethod
    def set_mock_mode(cls, enable: bool, screen_info=None, window_info=None, desktop_objects=None):
        cls._is_mock = enable
        if enable:
            cls._mock_screen_info = screen_info or cls._get_default_mock_screens()
            cls._mock_window_info = window_info or cls._get_default_mock_windows()
            cls._mock_desktop_objects = desktop_objects or []
        logger.info(f"EnvironmentSensor mock mode set to: {enable}")

    @classmethod
    def _get_default_mock_screens(cls) -> Dict[int, Dict[str, Any]]:
        """返回默认的模拟屏幕信息"""
        return {
            0: {
                'id': 0,
                'geometry': QRect(0, 0, 1920, 1080),
                'primary': True
            }
        }

    @classmethod
    def _get_default_mock_windows(cls) -> Dict[str, Any]:
        """返回默认的模拟窗口信息"""
        return {
            'hwnd': 123,
            'title': 'Mock Window',
            'class': 'MockClass',
            'rect': QRect(100, 100, 800, 600)
        }


# Windows平台特定优化
try:
    import ctypes
    from ctypes import windll, Structure, byref
    import win32gui
    import win32process
    import win32con
    import win32api  # 明确导入win32api
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
        
        def __init__(self, update_interval: float = 5.0, mock: bool = False,
                     event_callback: Optional[Callable[[EnvironmentEventType, Any], None]] = None):
            """初始化Windows环境传感器"""
            super().__init__(update_interval, event_callback)
            self._is_mock = mock
            if self._is_mock:
                # Use class mock data if available, or defaults
                self._mock_screen_info = self.__class__._mock_screen_info or self._get_default_mock_screens()
                self._mock_window_info = self.__class__._mock_window_info or self._get_default_mock_windows()
                self._mock_desktop_objects = self.__class__._mock_desktop_objects or []
            else:
                # Clear any class-level mock data if not in mock mode
                self._mock_screen_info = {}
                self._mock_window_info = {}
                self._mock_desktop_objects = []
            # Import windows libs here if not mocking
            if not self._is_mock:
                self._import_win_libs()
        
        def _import_win_libs(self):
            try:
                global win32api, win32gui, win32process, win32con, psutil, GPUtil
                import win32api
                import win32gui
                import win32process
                import win32con
                import psutil
                try:
                    import GPUtil  # type: ignore [import-untyped]
                except ImportError:
                    GPUtil = None
            except ImportError as e:
                logger.error(f"Failed to import Windows API libraries (pywin32? psutil?): {e}")
                # Potentially raise or disable sensor if essential libs missing
                raise
        
        def _get_environment_data(self) -> EnvironmentData:
            data = EnvironmentData()
            data.timestamp = time.time()

            if self._is_mock:
                # 确保返回的数据结构与EnvironmentData定义一致
                data.screen_info = self._mock_screen_info
                data.window_info = self._mock_window_info
                data.desktop_objects = self._mock_desktop_objects
                
                # 如果有屏幕信息，设置一个活动窗口
                if self._mock_screen_info:
                    first_screen_key = next(iter(self._mock_screen_info))
                    data.active_window = self._mock_window_info
                    
                # 设置默认光标位置
                data.cursor_position = (500, 500)
            else:
                try:
                    # 获取实际数据，确保数据结构与EnvironmentData定义一致
                    screens = self._get_screen_info()
                    windows = self._get_window_info()
                    
                    # 转换screen_info格式：由List转为Dict[int, Dict]
                    screen_dict = {}
                    for i, screen in enumerate(screens):
                        screen_dict[i] = screen
                    data.screen_info = screen_dict
                    
                    # 设置window_info为活动窗口信息
                    active_window = self._get_active_window(windows)
                    if active_window:
                        data.window_info = active_window
                        data.active_window = active_window
                    elif windows:
                        data.window_info = windows[0]
                        data.active_window = windows[0]
                    
                    # 转换desktop_objects
                    desktop_objs = []
                    for obj_data in self._get_desktop_objects():
                        desktop_obj = DesktopObject(
                            handle=obj_data.get('hwnd'),
                            title=obj_data.get('title', ''),
                            rect=obj_data.get('rect', QRect()),
                            process_name=obj_data.get('process_name', ''),
                            visible=True
                        )
                        desktop_objs.append(desktop_obj)
                    data.desktop_objects = desktop_objs
                    
                    # 设置光标位置
                    data.cursor_position = self._get_cursor_position()
                except Exception as e:
                    logger.error(f"Error fetching Windows env data: {e}", exc_info=True)
                    self.error_occurred.emit(f"Error fetching Windows data: {e}")
                    
                    # 返回空数据结构
                    data.screen_info = {}
                    data.window_info = {}
                    data.desktop_objects = []
                    data.active_window = None
                    data.cursor_position = None

            return data

        # --- Helper methods for fetching specific data --- 

        def _get_screen_info(self) -> List[Dict[str, Any]]:
            screens = []
            try:
                monitors = win32api.EnumDisplayMonitors()
                primary_monitor_handle = win32api.MonitorFromPoint((0, 0), win32con.MONITOR_DEFAULTTOPRIMARY)
                for i, monitor_info in enumerate(monitors):
                    handle = monitor_info[0].handle
                    rect_tuple = monitor_info[2] # (left, top, right, bottom)
                    is_primary = (handle == primary_monitor_handle)
                    screens.append({
                        'id': i,
                        'handle': handle,
                        'geometry': QRect(rect_tuple[0], rect_tuple[1], rect_tuple[2]-rect_tuple[0], rect_tuple[3]-rect_tuple[1]),
                        'primary': is_primary
                    })
            except Exception as e:
                logger.error(f"Error getting screen info: {e}")
                self.error_occurred.emit(f"Error getting screen info: {e}")
            return screens

        def _get_window_info(self) -> List[Dict[str, Any]]:
            windows: List[Dict[str, Any]] = []
            try:
                def win_enum_handler(hwnd, results):
                    if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                        try:
                            rect = win32gui.GetWindowRect(hwnd)
                            tid, pid = win32process.GetWindowThreadProcessId(hwnd)
                            process_name = "N/A"
                            try:
                                process = psutil.Process(pid)
                                process_name = process.name()
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                pass # Ignore processes we can't access

                            results.append({
                                'hwnd': hwnd,
                                'title': win32gui.GetWindowText(hwnd),
                                'class': win32gui.GetClassName(hwnd),
                                'rect': QRect(*rect),
                                'pid': pid,
                                'process_name': process_name
                            })
                        except Exception as inner_e:
                            # Log error for specific window but continue enumeration
                            # logger.warning(f"Could not get info for HWND {hwnd}: {inner_e}")
                            pass # Silently ignore errors for individual windows

                win32gui.EnumWindows(win_enum_handler, windows)
            except Exception as e:
                logger.error(f"Error enumerating windows: {e}")
                self.error_occurred.emit(f"Error enumerating windows: {e}")
            return windows

        def _get_active_window(self, all_windows: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
            try:
                active_hwnd = win32gui.GetForegroundWindow()
                # Find the active window info from the list we already gathered
                return next((w for w in all_windows if w['hwnd'] == active_hwnd), None)
            except Exception as e:
                logger.error(f"Error getting active window: {e}")
                self.error_occurred.emit(f"Error getting active window: {e}")
                return None

        def _get_cursor_position(self) -> Optional[Tuple[int, int]]:
            try:
                return win32api.GetCursorPos()
            except Exception as e:
                logger.error(f"Error getting cursor position: {e}")
                self.error_occurred.emit(f"Error getting cursor position: {e}")
                return None

        def _get_desktop_objects(self) -> List[Dict[str, Any]]:
            """获取桌面上的窗口对象信息列表"""
            # 这是复杂的，涉及迭代在Progman/SHELLDLL_DefView下的ListView
            # 实现Windows窗口枚举
            windows: List[Dict[str, Any]] = []
            try:
                # 这里是实际实现代码，仅作为示例
                pass
            except Exception as e:
                logger.error(f"获取桌面对象失败: {e}")
            return windows

    # 如果环境传感器实例不存在，并且是Windows平台，则尝试初始化Windows环境传感器
    if EnvironmentSensor._instance is None and platform.system() == "Windows":
        try:
            # 初始化一个WindowsEnvironmentSensor实例给_instance
            win_sensor: Optional[WindowsEnvironmentSensor] = WindowsEnvironmentSensor()
            EnvironmentSensor._instance = win_sensor
            logger.info("启用Windows桌面对象检测")
        except Exception as e:
            logger.warning(f"无法初始化Windows环境传感器: {e}")
            # 如果失败，则清空所有环境传感器实例
            EnvironmentSensor._instance = None
        
except ImportError as e:
    # 如果无法导入Windows模块，则提示并忽略
    logger.info(f"无法初始化环境传感器: {e}")
    pass 

def get_environment_sensor(platform_system: Optional[str] = None, **kwargs: Any) -> Optional[EnvironmentSensor]:
    """根据平台获取环境传感器实例"""
    current_platform = platform_system or platform.system()
    logger.info(f"Detected platform: {current_platform}")

    sensor_instance: Optional[EnvironmentSensor] = None # Initialize with None

    if current_platform == "Windows":
        # Pass kwargs to the constructor
        sensor_instance = WindowsEnvironmentSensor(**kwargs)
    elif current_platform == "Darwin":  # macOS
        sensor_instance = MacEnvironmentSensor(**kwargs)
    elif current_platform == "Linux":
        sensor_instance = LinuxEnvironmentSensor(**kwargs)
    else:
        logger.warning(f"Unsupported platform: {current_platform}. No environment sensor created.")
        # sensor_instance remains None

    if sensor_instance:
         logger.info(f"Created {type(sensor_instance).__name__} instance.")

    return sensor_instance # Return the instance or None

class MacEnvironmentSensor(EnvironmentSensor):
    """macOS环境传感器（占位实现）"""
    
    def __init__(self, update_interval: float = 5.0,
                event_callback: Optional[Callable[[EnvironmentEventType, Any], None]] = None):
        """初始化macOS环境传感器"""
        super().__init__(update_interval, event_callback)
        logger.info("MacOS环境传感器已初始化")
    
    def _get_environment_data(self) -> EnvironmentData:
        """获取环境数据"""
        # 占位实现
        data = EnvironmentData()
        data.timestamp = time.time()
        
        # 返回默认数据（实际使用时应该实现特定于macOS的方法）
        return data


class LinuxEnvironmentSensor(EnvironmentSensor):
    """Linux环境传感器（占位实现）"""
    
    def __init__(self, update_interval: float = 5.0,
                event_callback: Optional[Callable[[EnvironmentEventType, Any], None]] = None):
        """初始化Linux环境传感器"""
        super().__init__(update_interval, event_callback)
        logger.info("Linux环境传感器已初始化")
    
    def _get_environment_data(self) -> EnvironmentData:
        """获取环境数据"""
        # 占位实现
        data = EnvironmentData()
        data.timestamp = time.time()
        
        # 返回默认数据（实际使用时应该实现特定于Linux的方法）
        return data
