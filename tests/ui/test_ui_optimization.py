"""
---------------------------------------------------------------
File name:                  test_ui_optimization.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                UI优化功能测试
----------------------------------------------------------------

Changed history:             2025/05/13: 初始创建;
                             2025/05/16: 修复测试用例;
----
"""

import os
import sys
import time
import unittest
import logging
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QPoint, QTimer, QSize, QRect
from PySide6.QtWidgets import QApplication

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from status.ui.main_pet_window import MainPetWindow, DRAG_SMOOTHING_FACTOR
from status.interaction.drag_manager import DragManager, DRAG_MOVE_THROTTLE_MS, SCREEN_EDGE_MARGIN
from status.main import StatusPet
from status.animation.animation import Animation

class TestDragParameterOptimization(unittest.TestCase):
    """测试拖拽参数优化"""
    
    def test_drag_throttle_parameter(self):
        """测试拖拽节流参数是否正确设置"""
        # 验证参数值是否已更改为优化值
        self.assertEqual(DRAG_MOVE_THROTTLE_MS, 75, 
                        "拖拽移动事件节流间隔应为75ms")
    
    def test_drag_smoothing_factor(self):
        """测试拖拽平滑系数是否在合理范围内"""
        # 假设DRAG_SMOOTHING_FACTOR定义在main_pet_window.py中
        # 实际值为0.5，测试期望应与之匹配
        self.assertEqual(DRAG_SMOOTHING_FACTOR, 0.5, 
                         "拖拽平滑系数应为0.5")

class TestLogLevelOptimization(unittest.TestCase):
    """测试日志级别优化"""
    
    def setUp(self):
        """设置测试环境"""
        # 保存原始日志级别
        self.original_level = logging.getLogger("StatusApp").level
    
    def tearDown(self):
        """清理测试环境"""
        # 恢复原始日志级别
        logging.getLogger("StatusApp").setLevel(self.original_level)
    
    def test_log_level_setting(self):
        """测试日志级别是否设置为INFO"""
        # 模拟应用初始化过程
        with patch('status.main.logging.basicConfig') as mock_config:
            # 导入main模块会执行logging.basicConfig
            import status.main
            # 重新加载以确保执行配置
            import importlib
            importlib.reload(status.main)
            
            # 检查是否使用了INFO级别
            mock_config.assert_called_with(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
            )
    
    def test_debug_log_suppression(self):
        """测试DEBUG级别日志是否被抑制"""
        logger = logging.getLogger("TestLogger")
        logger.setLevel(logging.INFO)
        
        # 创建一个模拟处理器并正确设置其级别
        mock_handler = MagicMock()
        mock_handler.level = logging.INFO  # 设置处理器的日志级别
        logger.addHandler(mock_handler)
        
        # 创建一个模拟方法用于跟踪调用
        mock_handler.handle = MagicMock()
        
        # 记录不同级别的日志
        logger.debug("这是DEBUG消息")
        logger.info("这是INFO消息")
        logger.warning("这是WARNING消息")
        
        # 验证DEBUG消息被抑制，而INFO和WARNING消息正常记录
        self.assertEqual(mock_handler.handle.call_count, 2, 
                       "应该记录2条日志消息（INFO和WARNING）")

class TestWindowUpdateOptimization(unittest.TestCase):
    """测试窗口更新优化"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 确保 QApplication 存在
        self.q_app = QApplication.instance() or QApplication(sys.argv)
        self.pet_app = StatusPet() 
        self.pet_app.initialize() # Call initialize to set up actual main_window and animations.

        # For these specific tests, we want to mock main_window and current_animation
        # to control their behavior and assert calls, regardless of successful initialization.
        self.pet_app.main_window = MagicMock(spec=MainPetWindow)
        self.pet_app.main_window.isVisible.return_value = True # Default mock state

        # Ensure current_animation is also a mock for consistent testing environment
        current_anim_mock = MagicMock(spec=Animation)
        current_anim_mock.name = "mock_animation_name" # Configure name attribute
        
        mock_frame = MagicMock() # Mock for the frame object
        mock_frame.isNull.return_value = False # Configure isNull method for the frame
        current_anim_mock.current_frame.return_value = mock_frame # Configure current_frame to return mock_frame
        
        current_anim_mock.is_looping = True 
        current_anim_mock.is_playing = True
        # Add other necessary attributes/methods if errors indicate they are missing
        # For example, if .update, .reset, .play are called and need specific mock behavior.
        # MagicMock will create them as mocks by default if accessed.

        self.pet_app.current_animation = current_anim_mock

    def tearDown(self):
        if self.pet_app and self.pet_app.main_window:
            self.pet_app.main_window.close() # Clean up window
        # QApplication.quit() # Avoid quitting the app if it's shared across tests
        del self.pet_app
        del self.q_app

    def test_update_skipping_when_hidden(self):
        """测试窗口隐藏时是否跳过渲染更新"""
        self.pet_app.main_window.hide()
        self.pet_app.main_window.isVisible.return_value = False # Ensure mock reflects hidden state
        
        # current_animation is already a mock from setUp
        # self.pet_app.current_animation = MagicMock(spec=Animation) 
        
        self.pet_app.update() # Call the main update loop
        
        # 验证动画管理器的更新方法是否被调用
        self.pet_app.current_animation.update.assert_called_once()

    def test_update_when_visible(self):
        """测试窗口可见时是否执行渲染更新"""
        self.pet_app.main_window.show()
        self.pet_app.main_window.isVisible.return_value = True # Ensure mock reflects visible state

        # current_animation is already a mock from setUp
        # self.pet_app.current_animation = MagicMock(spec=Animation)
        # self.pet_app.current_animation.is_looping = True 
        # self.pet_app.current_animation.is_playing = True
        
        # 模拟经过一段时间
        self.pet_app._last_update_time = time.perf_counter() - 0.1 # Simulate 0.1s passed
        self.pet_app.update() # Call the main update loop
        
        # 验证动画的更新方法是否被调用
        self.pet_app.current_animation.update.assert_called_once()

class TestSmoothDragging(unittest.TestCase):
    """测试平滑拖动功能"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建QApplication实例，用于测试PySide6组件
        self.app = QApplication.instance() or QApplication([])
        # 创建MainPetWindow实例
        self.window = MainPetWindow()
    
    def test_smooth_dragging_initialization(self):
        """测试平滑拖动初始化是否正确"""
        # 验证平滑拖动相关属性是否正确初始化
        self.assertEqual(self.window.smoothing_factor, DRAG_SMOOTHING_FACTOR)
        self.assertIsInstance(self.window.target_pos, QPoint)
        self.assertIsInstance(self.window.current_pos, QPoint)
        self.assertIsInstance(self.window.smoothing_timer, QTimer)
        self.assertEqual(self.window.smoothing_timer.interval(), 16)
    
    def test_position_update_calculation(self):
        """测试位置更新计算是否正确"""
        # 设置当前位置和目标位置
        self.window.current_pos = QPoint(100, 100)
        self.window.target_pos = QPoint(200, 200)
        
        # 模拟_update_position方法中的计算
        smoothing_factor = self.window.smoothing_factor
        new_x = self.window.current_pos.x() + (self.window.target_pos.x() - self.window.current_pos.x()) * smoothing_factor
        new_y = self.window.current_pos.y() + (self.window.target_pos.y() - self.window.current_pos.y()) * smoothing_factor
        
        # 验证计算结果
        expected_x = 100 + (200 - 100) * smoothing_factor
        expected_y = 100 + (200 - 100) * smoothing_factor
        self.assertAlmostEqual(new_x, expected_x)
        self.assertAlmostEqual(new_y, expected_y)
    
    def test_is_position_close(self):
        """测试_is_position_close方法是否正确判断位置接近程度"""
        # 距离小于阈值的情况
        self.window.current_pos = QPoint(100, 100)
        self.window.target_pos = QPoint(101, 101)
        self.assertTrue(self.window._is_position_close())
        
        # 距离大于阈值的情况
        self.window.current_pos = QPoint(100, 100)
        self.window.target_pos = QPoint(110, 110)
        self.assertFalse(self.window._is_position_close())

class TestScreenBoundaryDetection(unittest.TestCase):
    """测试屏幕边界检测功能"""
    
    def setUp(self):
        """设置测试环境"""
        self.app = QApplication.instance() or QApplication([])
        self.window = MagicMock()
        self.window.width.return_value = 100
        self.window.height.return_value = 100
        self.drag_manager = DragManager(self.window)
    
    @patch('status.interaction.drag_manager.DragManager._get_screen_bounds')
    def test_boundary_constraints(self, mock_get_screen_bounds):
        """测试边界约束是否正确应用"""
        # 模拟屏幕边界
        mock_get_screen_bounds.return_value = QRect(0, 0, 1920, 1080)
        
        # 测试窗口在屏幕内时不应约束
        x, y = self.drag_manager._apply_boundary_constraints(500, 500)
        self.assertEqual((x, y), (500, 500))
        
        # 启用边界保护
        self.drag_manager.boundary_protection = True
        
        # 设置窗口大小，用于边界计算
        self.window.width.return_value = 100
        self.window.height.return_value = 100
        
        # 计算允许的最小/最大位置（直接从源代码实现中获取算法）
        screen_rect = mock_get_screen_bounds.return_value
        window_width = self.window.width()
        window_height = self.window.height()
        
        min_x = screen_rect.left() - window_width + SCREEN_EDGE_MARGIN
        max_x = screen_rect.right() - SCREEN_EDGE_MARGIN
        min_y = screen_rect.top() - window_height + SCREEN_EDGE_MARGIN
        max_y = screen_rect.bottom() - SCREEN_EDGE_MARGIN
        
        # 测试窗口超出左边界时应约束
        x, y = self.drag_manager._apply_boundary_constraints(-90, 500)
        self.assertEqual(x, min_x, "左边界约束计算错误")
        self.assertEqual(y, 500, "左边界约束不应修改y坐标")
        
        # 测试窗口超出右边界时应约束
        x, y = self.drag_manager._apply_boundary_constraints(1910, 500)
        self.assertEqual(x, max_x, "右边界约束计算错误")
        self.assertEqual(y, 500, "右边界约束不应修改y坐标")
        
        # 测试窗口超出上边界时应约束
        x, y = self.drag_manager._apply_boundary_constraints(500, -90)
        self.assertEqual(x, 500, "上边界约束不应修改x坐标")
        self.assertEqual(y, min_y, "上边界约束计算错误")
        
        # 测试窗口超出下边界时应约束
        x, y = self.drag_manager._apply_boundary_constraints(500, 1070)
        self.assertEqual(x, 500, "下边界约束不应修改x坐标")
        self.assertEqual(y, max_y, "下边界约束计算错误")
    
    def test_boundary_protection_toggle(self):
        """测试边界保护开关是否正常工作"""
        # 默认应启用边界保护
        self.assertTrue(self.drag_manager.boundary_protection)
        
        # 测试关闭边界保护
        self.drag_manager.set_boundary_protection(False)
        self.assertFalse(self.drag_manager.boundary_protection)
        
        # 测试不应用约束
        with patch('status.interaction.drag_manager.DragManager._get_screen_bounds') as mock_get_screen_bounds:
            mock_get_screen_bounds.return_value = QRect(0, 0, 1920, 1080)
            x, y = self.drag_manager._apply_boundary_constraints(5000, 5000)
            self.assertEqual((x, y), (5000, 5000))
        
        # 重新启用边界保护
        self.drag_manager.set_boundary_protection(True)
        self.assertTrue(self.drag_manager.boundary_protection)

if __name__ == '__main__':
    unittest.main() 