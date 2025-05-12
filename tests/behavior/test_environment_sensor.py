"""
---------------------------------------------------------------
File name:                  test_environment_sensor.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                环境感知器测试
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
                            2025/04/04: 更新使用mock模式进行测试;
                            2025/04/04: 修复测试错误;
                            2025/04/04: 修复单例模式测试;
                            2025/05/15: 将PyQt6导入改为PySide6以统一项目Qt库使用;
----
"""

import unittest
from unittest.mock import MagicMock, patch, call
import sys
import platform
import pytest

from PySide6.QtCore import QRect, QPoint
from PySide6.QtGui import QGuiApplication

from status.behavior.environment_sensor import EnvironmentSensor, EnvironmentEventType, EnvironmentEvent, DesktopObject
from status.behavior.environment_sensor import WindowsEnvironmentSensor
from status.core.events import EventManager

@pytest.mark.usefixtures("qapp")
class TestEnvironmentSensor(unittest.TestCase):
    """环境感知器测试类"""
    
    def setUp(self):
        """每个测试方法前执行"""
        # 先禁用mock模式确保环境干净
        EnvironmentSensor.enable_mock_mode(False)
        
        # 重置单例实例
        EnvironmentSensor._instance = None
        
        # 启用模拟模式进行测试
        EnvironmentSensor.enable_mock_mode(True)
        
        # 设置模拟数据
        EnvironmentSensor.set_mock_screen_info({
            0: {
                'geometry': QRect(0, 0, 1920, 1080),
                'width': 1920,
                'height': 1080,
                'x': 0,
                'y': 0,
                'name': 'Test Screen',
                'scale_factor': 1.0,
                'primary': True
            },
            1: {
                'geometry': QRect(1920, 0, 1920, 1080),
                'width': 1920,
                'height': 1080,
                'x': 1920,
                'y': 0,
                'name': 'Test Screen 2',
                'scale_factor': 1.0,
                'primary': False
            }
        })
        
        EnvironmentSensor.set_mock_window_info({
            'geometry': QRect(100, 100, 800, 600),
            'width': 800,
            'height': 600,
            'x': 100,
            'y': 100
        })
        
        test_objects = [
            DesktopObject(title="Test Window 1", rect=QRect(0, 0, 100, 100)),
            DesktopObject(title="Test Window 2", rect=QRect(200, 200, 300, 200))
        ]
        EnvironmentSensor.set_mock_desktop_objects(test_objects)
        
        # 创建环境感知器实例
        self.sensor = EnvironmentSensor.get_instance()
        self.event_manager = MagicMock(spec=EventManager)
        self.sensor.initialize(self.event_manager)
    
    def tearDown(self):
        """每个测试方法后执行"""
        # 重置环境感知器单例
        EnvironmentSensor._instance = None
        
        # 禁用模拟模式
        EnvironmentSensor.enable_mock_mode(False)
    
    def test_singleton(self):
        """测试单例模式"""
        # 获取当前实例的引用
        instance1 = self.sensor
        
        # 获取单例实例（应该是与instance1相同的实例）
        instance2 = EnvironmentSensor.get_instance()
        self.assertIs(instance2, instance1)
        
        # 尝试创建第二个实例应该引发异常
        with self.assertRaises(RuntimeError):
            instance3 = EnvironmentSensor()
    
    def test_get_screen_boundaries(self):
        """测试获取屏幕边界信息"""
        # 测试默认参数（获取主屏幕）
        screen_info = self.sensor.get_screen_boundaries()
        self.assertIsInstance(screen_info, dict)
        self.assertIn('width', screen_info)
        self.assertIn('height', screen_info)
        self.assertIn('x', screen_info)
        self.assertIn('y', screen_info)
        self.assertIn('geometry', screen_info)
        
        # 宽度和高度应该为正数
        self.assertGreater(screen_info['width'], 0)
        self.assertGreater(screen_info['height'], 0)
    
    def test_get_all_screens(self):
        """测试获取所有屏幕信息"""
        screens = self.sensor.get_all_screens()
        self.assertIsInstance(screens, dict)
        
        # 应有两个屏幕（模拟数据）
        self.assertEqual(len(screens), 2)
        
        # 检查第一个屏幕的信息
        self.assertIn(0, screens)
        first_screen = screens[0]
        self.assertEqual(first_screen['width'], 1920)
        self.assertEqual(first_screen['height'], 1080)
    
    def test_get_primary_screen(self):
        """测试获取主屏幕信息"""
        primary_screen = self.sensor.get_primary_screen()
        self.assertIsInstance(primary_screen, dict)
        
        # 检查基本属性
        self.assertIn('width', primary_screen)
        self.assertIn('height', primary_screen)
        
        # 主屏幕的primary属性应为True
        self.assertTrue(primary_screen['primary'])
        
        # 应该是我们设置的测试屏幕
        self.assertEqual(primary_screen['name'], 'Test Screen')
    
    def test_get_window_position(self):
        """测试获取窗口位置"""
        # 创建一个模拟窗口对象
        mock_window = MagicMock()
        mock_window.geometry.return_value = QRect(100, 100, 800, 600)
        
        # 测试获取指定窗口的位置
        position = self.sensor.get_window_position(mock_window)
        self.assertEqual(position, QRect(100, 100, 800, 600))
        
        # 测试获取活动窗口位置（未设置活动窗口时应返回 setUp 中 set_mock_window_info 设置的默认值）
        position = self.sensor.get_window_position()
        self.assertEqual(position, QRect(100, 100, 800, 600))
        
        # 设置活动窗口后测试
        self.sensor.set_active_window(mock_window)
    
    def test_detect_desktop_objects(self):
        """测试检测桌面对象"""
        # 使用模拟模式，应返回我们设置的测试对象
        objects = self.sensor.detect_desktop_objects()
        self.assertIsInstance(objects, list)
        self.assertEqual(len(objects), 2)
        
        # 验证对象内容
        self.assertEqual(objects[0].title, "Test Window 1")
        self.assertEqual(objects[1].title, "Test Window 2")
        
        # 测试使用过滤器
        objects = self.sensor.detect_desktop_objects(
            filter_func=lambda obj: "Window 1" in obj.title
        )
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0].title, "Test Window 1")
    
    def test_is_window_visible(self):
        """测试窗口可见性检查"""
        # 使用模拟屏幕数据
        # 屏幕1: (0, 0, 1920, 1080)
        # 屏幕2: (1920, 0, 1920, 1080)
        
        # 测试点在第一个屏幕内
        self.assertTrue(self.sensor.is_window_visible(QPoint(500, 500)))
        
        # 测试点在第二个屏幕内
        self.assertTrue(self.sensor.is_window_visible(QPoint(2500, 500)))
        
        # 测试点在屏幕外
        self.assertFalse(self.sensor.is_window_visible(QPoint(4000, 2000)))
        
        # 测试矩形完全在第一个屏幕内
        self.assertTrue(self.sensor.is_window_visible(QRect(100, 100, 800, 600)))
        
        # 测试矩形跨越两个屏幕
        self.assertTrue(self.sensor.is_window_visible(QRect(1800, 100, 300, 300)))
        
        # 测试矩形完全在屏幕外
        self.assertFalse(self.sensor.is_window_visible(QRect(4000, 2000, 300, 300)))
    
    def test_get_screen_at_point(self):
        """测试获取包含指定点的屏幕信息"""
        # 使用模拟屏幕数据
        # 屏幕1: (0, 0, 1920, 1080)
        # 屏幕2: (1920, 0, 1920, 1080)
        
        # 测试点在第一个屏幕内
        result = self.sensor.get_screen_at_point(QPoint(500, 500))
        self.assertEqual(result['name'], 'Test Screen')
        
        # 测试点在第二个屏幕内
        result = self.sensor.get_screen_at_point(QPoint(2500, 500))
        self.assertEqual(result['name'], 'Test Screen 2')
        
        # 测试点不在任何屏幕内，应返回主屏幕
        result = self.sensor.get_screen_at_point(QPoint(5000, 5000))
        self.assertEqual(result['name'], 'Test Screen')
    
    def test_register_callback(self):
        """测试注册环境变化回调函数"""
        # 创建一个简单的回调函数
        callback = MagicMock()
        
        # 注册回调
        result = self.sensor.register_callback(callback)
        self.assertTrue(result)
        
        # 重复注册应返回False
        result = self.sensor.register_callback(callback)
        self.assertFalse(result)
        
        # 非可调用对象应返回False
        result = self.sensor.register_callback("not a callable")
        self.assertFalse(result)
        
        # 触发事件通知，回调应被调用
        self.sensor._notify_environment_change(EnvironmentEventType.SCREEN_CHANGE, {'test': True})
        callback.assert_called_once()
    
    def test_unregister_callback(self):
        """测试取消注册环境变化回调函数"""
        # 创建一个简单的回调函数
        callback = MagicMock()
        
        # 注册回调
        self.sensor.register_callback(callback)
        
        # 取消注册
        result = self.sensor.unregister_callback(callback)
        self.assertTrue(result)
        
        # 再次取消注册应返回False
        result = self.sensor.unregister_callback(callback)
        self.assertFalse(result)
        
        # 触发事件通知，回调不应被调用
        self.sensor._notify_environment_change(EnvironmentEventType.SCREEN_CHANGE, {'test': True})
        callback.assert_not_called()
    
    def test_environment_events(self):
        """测试环境事件"""
        # 触发屏幕变化事件
        self.sensor._notify_environment_change(EnvironmentEventType.SCREEN_CHANGE, {'screen_info': {}})
        
        # 验证事件管理器的dispatch方法被调用
        self.event_manager.dispatch.assert_called_once()
        
        # 获取传递给dispatch的事件对象
        event = self.event_manager.dispatch.call_args[0][0]
        
        # 验证事件类型
        self.assertEqual(event.type, EnvironmentEventType.SCREEN_CHANGE)
        
        # 验证事件数据
        self.assertEqual(event.data, {'screen_info': {}})
    
    def test_update(self):
        """测试更新环境信息"""
        # 初始化后模拟状态变化
        old_screen_info = self.sensor._screen_info.copy()
        old_window_info = self.sensor._window_info.copy()
        old_desktop_objects = self.sensor._desktop_objects.copy()
        
        # 修改模拟数据
        new_screen_info = {
            0: {
                'geometry': QRect(0, 0, 1280, 720),
                'width': 1280,
                'height': 720,
                'x': 0,
                'y': 0,
                'name': 'Changed Screen',
                'scale_factor': 1.0,
                'primary': True
            }
        }
        EnvironmentSensor.set_mock_screen_info(new_screen_info)
        
        new_window_info = {
            'geometry': QRect(200, 200, 800, 600),
            'width': 800,
            'height': 600,
            'x': 200,
            'y': 200
        }
        EnvironmentSensor.set_mock_window_info(new_window_info)
        
        new_desktop_objects = [
            DesktopObject(title="New Window", rect=QRect(300, 300, 400, 300))
        ]
        EnvironmentSensor.set_mock_desktop_objects(new_desktop_objects)
        
        # 调用更新方法
        self.sensor.update()
        
        # 验证事件管理器的dispatch方法被调用三次（屏幕、窗口、桌面对象各一次）
        self.assertEqual(self.event_manager.dispatch.call_count, 3)
        
        # 验证新的状态
        self.assertEqual(self.sensor._screen_info, new_screen_info)
        self.assertEqual(self.sensor._window_info, new_window_info)
        self.assertEqual(self.sensor._desktop_objects, new_desktop_objects)
        
        # 验证每个事件类型（使用正确的事件类型列表提取方式）
        event_types = []
        for call_obj in self.event_manager.dispatch.call_args_list:
            event = call_obj[0][0]  # 获取第一个位置参数，即事件对象
            event_types.append(event.type)
            
        self.assertIn(EnvironmentEventType.SCREEN_CHANGE, event_types)
        self.assertIn(EnvironmentEventType.WINDOW_MOVE, event_types)
        self.assertIn(EnvironmentEventType.DESKTOP_OBJECTS_CHANGE, event_types)


class TestDesktopObject(unittest.TestCase):
    """桌面对象测试类"""
    
    def test_desktop_object_creation(self):
        """测试桌面对象创建"""
        # 测试默认参数
        obj = DesktopObject()
        self.assertEqual(obj.handle, None)
        self.assertEqual(obj.title, "")
        self.assertEqual(obj.rect, QRect())
        self.assertEqual(obj.process_name, "")
        self.assertTrue(obj.visible)
        
        # 测试自定义参数
        rect = QRect(10, 20, 300, 200)
        obj = DesktopObject(
            handle=123,
            title="Test Object",
            rect=rect,
            process_name="test.exe",
            visible=False
        )
        self.assertEqual(obj.handle, 123)
        self.assertEqual(obj.title, "Test Object")
        self.assertEqual(obj.rect, rect)
        self.assertEqual(obj.process_name, "test.exe")
        self.assertFalse(obj.visible)
    
    def test_desktop_object_equality(self):
        """测试桌面对象相等性比较"""
        # 创建两个相同的对象
        rect1 = QRect(10, 20, 300, 200)
        obj1 = DesktopObject(
            handle=123,
            title="Test Object",
            rect=rect1,
            process_name="test.exe",
            visible=True
        )
        
        rect2 = QRect(10, 20, 300, 200)
        obj2 = DesktopObject(
            handle=123,
            title="Test Object",
            rect=rect2,
            process_name="test.exe",
            visible=True
        )
        
        # 测试相等性
        self.assertEqual(obj1, obj2)
        
        # 修改一个属性后测试不相等
        obj2.title = "Different Title"
        self.assertNotEqual(obj1, obj2)
        
        # 测试与非DesktopObject对象的比较
        self.assertNotEqual(obj1, "not an object")
        self.assertNotEqual(obj1, 123)
        self.assertNotEqual(obj1, None)


# Windows平台特定测试（使用模拟模式）
@unittest.skipIf(platform.system() != "Windows", "Windows平台特定测试")
@pytest.mark.usefixtures("qapp")
class TestWindowsEnvironmentSensor(unittest.TestCase):
    """Windows环境感知器测试类"""
    
    def setUp(self):
        """每个测试方法前执行"""
        # 先禁用mock模式确保环境干净
        EnvironmentSensor.enable_mock_mode(False)
        
        # 重置单例实例
        EnvironmentSensor._instance = None
        
        # 创建环境感知器实例 (在 TestWindowsEnvironmentSensor 中，这会是 WindowsEnvironmentSensor)
        self.sensor = EnvironmentSensor.get_instance()
        
        # 确保它是Windows传感器（如果适用）
        if platform.system() == "Windows":
            from status.behavior.environment_sensor import WindowsEnvironmentSensor
            # self.assertIsInstance(self.sensor, WindowsEnvironmentSensor)

        self.event_manager = MagicMock(spec=EventManager)
        # 确保这里没有 self.sensor._update_desktop_objects() 调用
    
    def tearDown(self):
        """每个测试方法后执行"""
        # 重置环境感知器单例
        EnvironmentSensor._instance = None
        
        # 禁用模拟模式
        EnvironmentSensor.enable_mock_mode(False)
    
    def test_windows_specific_features(self):
        """测试Windows特定的环境感知功能（例如，不依赖全局mock模式）"""
        EnvironmentSensor.enable_mock_mode(False)
        EnvironmentSensor._instance = None

        sensor = EnvironmentSensor.get_instance()
        # 在访问特定于子类的属性之前，进行实例检查是好的
        self.assertIsInstance(sensor, WindowsEnvironmentSensor, "Sensor instance should be WindowsEnvironmentSensor on Windows.")

        # 检查 user32 是否成功加载
        # hasattr 是动态检查，Linter 可能仍然无法静态确认类型，但这是安全的
        if not hasattr(sensor, 'user32') or sensor.user32 is None: # type: ignore
            self.skipTest("user32.dll 未能加载，跳过依赖真实Windows API的特性测试。")
            return

        sensor.initialize(self.event_manager)

        # 1. 测试屏幕信息 (实际 API 调用)
        screen_info = sensor.get_screen_boundaries()
        self.assertIsInstance(screen_info, dict)
        
        # 2. 测试窗口位置
        window_rect = sensor.get_window_position()
        self.assertIsInstance(window_rect, QRect)
        
        # 3. 测试检测桌面对象
        objects = sensor.detect_desktop_objects()
        self.assertIsInstance(objects, list)
        
        # 在模拟模式下，应该返回我们设置的测试对象
        self.assertEqual(len(objects), 2)
        self.assertEqual(objects[0].title, "Test Window 1")
        self.assertEqual(objects[1].title, "Test Window 2")
    
    def test_windows_mock_desktop_objects(self):
        """测试Windows环境下的模拟桌面对象"""
        # 启用全局模拟模式
        EnvironmentSensor.enable_mock_mode(True)
        EnvironmentSensor._mock_desktop_objects = [] # 确保在 set_mock_desktop_objects 之前是干净的
        
        # 设置模拟数据
        mock_objects = [
            DesktopObject(
                handle=1001,
                title="Windows Test App",
                rect=QRect(50, 50, 500, 400),
                process_name="test_app.exe",
                visible=True
            ),
            DesktopObject(
                handle=1002,
                title="Windows Test App 2",
                rect=QRect(600, 50, 500, 400),
                process_name="test_app2.exe",
                visible=True
            )
        ]
        EnvironmentSensor.set_mock_desktop_objects(mock_objects)
        
        # 检测桌面对象
        objects = self.sensor.detect_desktop_objects()
        
        # 验证返回的对象列表
        self.assertEqual(len(objects), 2)
        self.assertEqual(objects[0].handle, 1001)
        self.assertEqual(objects[0].title, "Windows Test App")
        self.assertEqual(objects[1].handle, 1002)
        self.assertEqual(objects[1].title, "Windows Test App 2")
    
    def test_windows_object_filtering(self):
        """测试Windows环境下的对象过滤功能"""
        EnvironmentSensor.enable_mock_mode(True)
        EnvironmentSensor._mock_desktop_objects = []

        # 原始的 mock_objects
        mock_objects = [
            DesktopObject(title="Filter Test App 1", rect=QRect(10, 10, 100, 100), process_name="app1.exe"),
            DesktopObject(title="Filter Test App 2", rect=QRect(150, 150, 200, 200), process_name="app2.exe"),
            DesktopObject(title="Another Window", rect=QRect(300, 300, 150, 150), process_name="other.exe")
        ]
        EnvironmentSensor.set_mock_desktop_objects(mock_objects)

        EnvironmentSensor._instance = None 
        sensor_for_test = EnvironmentSensor.get_instance()
        sensor_for_test.initialize(self.event_manager)
        sensor_for_test._update_desktop_objects() # 保留这一行

        # 按标题过滤 - 恢复原始 lambda 和断言
        filtered_by_title = sensor_for_test.detect_desktop_objects(
            filter_func=lambda obj: "App 1" in obj.title
        )
        self.assertEqual(len(filtered_by_title), 1)
        if filtered_by_title:
            self.assertEqual(filtered_by_title[0].title, "Filter Test App 1")

        # 按进程名过滤 - 恢复原始 lambda 和断言
        filtered_by_process = sensor_for_test.detect_desktop_objects(
            filter_func=lambda obj: obj.process_name == "app2.exe"
        )
        self.assertEqual(len(filtered_by_process), 1)
        if filtered_by_process:
            self.assertEqual(filtered_by_process[0].process_name, "app2.exe")
            
        # 无匹配的过滤 - 恢复原始 lambda 和断言
        filtered_no_match = sensor_for_test.detect_desktop_objects(
            filter_func=lambda obj: "NonExistent" in obj.title
        )
        self.assertEqual(len(filtered_no_match), 0)

        EnvironmentSensor.enable_mock_mode(False)


if __name__ == '__main__':
    unittest.main() 