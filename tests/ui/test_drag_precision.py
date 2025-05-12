"""
---------------------------------------------------------------
File name:                  test_drag_precision.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                精确拖动功能和精度测试
----------------------------------------------------------------
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QPoint, QTimer, QElapsedTimer, QEvent, Qt, QRect
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from status.ui.main_pet_window import MainPetWindow, DRAG_MAX_SMOOTHING, DRAG_MIN_SMOOTHING, DRAG_SMOOTHING_FACTOR

class TestDragPrecision(unittest.TestCase):
    """测试拖动精确度"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建QApplication实例，用于测试PySide6组件
        self.app = QApplication.instance() or QApplication([])
        # 创建MainPetWindow实例
        self.window = MainPetWindow()
        # 设置初始位置
        self.window.move(100, 100)
        # 模拟_get_screen_geometry和_constrain_to_screen_boundary方法以简化测试
        self.window._get_screen_geometry = MagicMock(return_value=QRect(0, 0, 1920, 1080))
        self.original_constrain = self.window._constrain_to_screen_boundary
        self.window._constrain_to_screen_boundary = lambda pos, screen_geometry: pos
    
    def tearDown(self):
        """清理测试环境"""
        # 恢复原始方法
        self.window._constrain_to_screen_boundary = self.original_constrain
    
    def simulate_mouse_move(self, dx, dy, elapsed=20):
        """模拟鼠标移动事件
        
        Args:
            dx: X轴移动距离
            dy: Y轴移动距离
            elapsed: 模拟的时间间隔（毫秒）
        """
        # 设置起始条件
        if not hasattr(self.window, 'is_dragging') or not self.window.is_dragging:
            self.window.is_dragging = True
            self.window.drag_start_pos = QPoint(10, 10)
            self.window.window_start_pos = self.window.pos()
            self.window.last_mouse_pos = QPoint(10, 10)
            self.window.last_mouse_time = QElapsedTimer()
            self.window.last_mouse_time.start()
        
        # 计算新的鼠标位置
        new_mouse_x = self.window.last_mouse_pos.x() + dx
        new_mouse_y = self.window.last_mouse_pos.y() + dy
        
        # 创建鼠标移动事件
        event = QMouseEvent(
            QEvent.Type.MouseMove,
            QPoint(new_mouse_x, new_mouse_y),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        
        # 模拟时间经过
        self.window.last_mouse_time = MagicMock()
        self.window.last_mouse_time.elapsed.return_value = elapsed
        
        # 触发鼠标移动事件
        self.window.mouseMoveEvent(event)
        
        # 更新最后的鼠标位置
        self.window.last_mouse_pos = QPoint(new_mouse_x, new_mouse_y)
    
    def test_precise_mode_smoothing_factor(self):
        """测试精确模式的平滑系数"""
        # 设置精确模式
        self.window.set_drag_mode("precise")
        # 模拟鼠标移动事件计算平滑系数
        
        # 创建一个MouseEvent模拟鼠标按下
        mouse_press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPoint(10, 10),  # 本地坐标
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        
        # 设置拖拽状态
        self.window.is_dragging = True
        self.window.drag_start_pos = QPoint(10, 10)
        self.window.window_start_pos = QPoint(100, 100)
        self.window.last_mouse_pos = QPoint(10, 10)
        
        # 模拟last_mouse_time已经启动
        self.window.last_mouse_time = QElapsedTimer()
        self.window.last_mouse_time.start()
        
        # 创建一个MouseEvent模拟鼠标移动
        mouse_move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            QPoint(20, 20),  # 本地坐标，移动了10像素
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        
        # 触发mouseMoveEvent方法
        self.window.mouseMoveEvent(mouse_move_event)
        
        # 验证精确模式下平滑系数是否设置为DRAG_MAX_SMOOTHING
        self.assertEqual(self.window.smoothing_factor, DRAG_MAX_SMOOTHING)
    
    def test_direct_position_tracking(self):
        """测试在精确模式下是否能够直接跟踪鼠标位置"""
        # 设置测试环境
        self.window.set_drag_mode("precise")
        self.window.is_dragging = True
        self.window.drag_start_pos = QPoint(10, 10)
        self.window.window_start_pos = QPoint(100, 100)
        self.window.current_pos = QPoint(100, 100)
        self.window.target_pos = QPoint(100, 100)
        
        # 模拟鼠标移动10个像素
        mouse_move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            QPoint(20, 20),  # 本地坐标，移动了10像素
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        
        # 模拟last_mouse_time已经启动
        self.window.last_mouse_time = QElapsedTimer()
        self.window.last_mouse_time.start()
        self.window.last_mouse_pos = QPoint(10, 10)
        
        # 触发mouseMoveEvent方法
        self.window.mouseMoveEvent(mouse_move_event)
        
        # 验证target_pos是否正确设置
        expected_position = QPoint(110, 110)  # 初始位置(100,100) + 移动(10,10)
        self.assertEqual(self.window.target_pos, expected_position)
    
    def test_smooth_mode_vs_precise_mode(self):
        """测试平滑模式和精确模式下的移动差异"""
        # 验证平滑模式有较低的平滑系数
        self.window.set_drag_mode("smooth")
        self.assertEqual(self.window.smoothing_factor, DRAG_MIN_SMOOTHING)
        
        # 验证精确模式有较高的平滑系数
        self.window.set_drag_mode("precise")
        self.assertEqual(self.window.smoothing_factor, DRAG_MAX_SMOOTHING)
    
    def test_position_updates_in_precise_mode(self):
        """测试精确模式下的位置更新频率"""
        # 设置精确模式
        self.window.set_drag_mode("precise")
        
        # 模拟拖动操作
        self.window.is_dragging = True
        self.window.drag_start_pos = QPoint(10, 10)
        self.window.window_start_pos = QPoint(100, 100)
        self.window.target_pos = QPoint(110, 110)
        self.window.current_pos = QPoint(100, 100)
        
        # 手动调用_update_position方法
        self.window._update_position()
        
        # 由于smoothing_factor在精确模式下设为DRAG_MAX_SMOOTHING(0.85)
        # 期望的新位置应该是: current + (target - current) * factor
        expected_x = 100 + (110 - 100) * DRAG_MAX_SMOOTHING
        expected_y = 100 + (110 - 100) * DRAG_MAX_SMOOTHING
        expected_pos = QPoint(int(expected_x), int(expected_y))
        
        # 验证current_pos是否更新为期望值
        self.assertEqual(self.window.current_pos, expected_pos)
    
    def test_smoothing_factors_for_all_modes(self):
        """测试所有拖动模式下的平滑因子设置"""
        # 测试精确模式
        self.window.set_drag_mode("precise")
        self.simulate_mouse_move(10, 10)
        self.assertAlmostEqual(self.window.smoothing_factor, DRAG_MAX_SMOOTHING)
        
        # 测试平滑模式
        self.window.set_drag_mode("smooth")
        self.simulate_mouse_move(10, 10)
        self.assertAlmostEqual(self.window.smoothing_factor, DRAG_MIN_SMOOTHING)
        
        # 测试智能模式在不同速度下的平滑因子变化
        self.window.set_drag_mode("smart")
        
        # 低速移动 - 应该使用较低的平滑因子
        self.simulate_mouse_move(1, 1, elapsed=100)  # 慢速移动
        self.assertLess(self.window.smoothing_factor, (DRAG_MIN_SMOOTHING + DRAG_MAX_SMOOTHING) / 2)
        
        # 高速移动 - 应该使用较高的平滑因子
        # 使用更高的速度测试，确保超过阈值
        self.simulate_mouse_move(50, 50, elapsed=5)  # 非常快速的移动
        self.assertGreater(self.window.smoothing_factor, 0.5)  # 使用较低的阈值
    
    def test_precise_mode_tracking_accuracy(self):
        """测试精确模式下的位置跟踪精确度"""
        self.window.set_drag_mode("precise")
        initial_pos = QPoint(100, 100)
        self.window.move(initial_pos)
        self.window.current_pos = initial_pos
        self.window.target_pos = initial_pos
        
        # 模拟一系列鼠标移动
        movements = [
            (10, 10),   # 右下移动
            (0, 10),    # 向下移动
            (10, 0),    # 向右移动
            (-5, -5),   # 左上移动
        ]
        
        # 跟踪总移动距离
        expected_x, expected_y = initial_pos.x(), initial_pos.y()
        
        for dx, dy in movements:
            # 模拟鼠标移动
            self.simulate_mouse_move(dx, dy)
            expected_x += dx
            expected_y += dy
            
            # 执行一次位置更新
            self.window._update_position()
            
            # 计算当前位置与期望位置的差距
            x_diff = abs(self.window.current_pos.x() - expected_x)
            y_diff = abs(self.window.current_pos.y() - expected_y)
            
            # 精确模式下，差距应该小于或等于某个阈值（例如2像素）
            self.assertLessEqual(x_diff, 2, f"X轴跟踪精度不足: {x_diff}px")
            self.assertLessEqual(y_diff, 2, f"Y轴跟踪精度不足: {y_diff}px")
    
    def test_mouse_speed_calculation(self):
        """测试鼠标速度的计算和平滑"""
        self.window.set_drag_mode("smart")
        
        # 模拟一连串不同速度的鼠标移动
        speeds = [
            (5, 5, 100),   # 慢速 (5,5像素/100ms)
            (10, 10, 50),  # 中速 (10,10像素/50ms)
            (20, 20, 10),  # 快速 (20,20像素/10ms)
        ]
        
        for dx, dy, elapsed in speeds:
            # 重置速度历史
            self.window.speed_history = []
            
            # 模拟特定速度的鼠标移动
            self.simulate_mouse_move(dx, dy, elapsed)
            
            # 计算期望的速度（像素/毫秒）
            distance = ((dx**2 + dy**2)**0.5)
            expected_speed = distance / elapsed
            
            # 验证计算的鼠标速度接近期望值
            self.assertAlmostEqual(
                self.window.mouse_speed, 
                expected_speed,
                delta=0.1,  # 允许0.1的误差
                msg=f"速度计算不准确: 期望{expected_speed}, 实际{self.window.mouse_speed}"
            )
    
    def test_position_update_calculation(self):
        """测试位置更新的计算准确性"""
        # 设置初始状态
        self.window.current_pos = QPoint(100, 100)
        self.window.target_pos = QPoint(200, 200)
        
        # 测试不同平滑因子下的位置更新
        for factor in [0.3, 0.5, 0.8, 0.9]:
            # 设置平滑因子
            self.window.smoothing_factor = factor
            
            # 执行一次位置更新
            self.window._update_position()
            
            # 计算期望位置
            expected_x = 100 + (200 - 100) * factor
            expected_y = 100 + (200 - 100) * factor
            expected_pos = QPoint(int(expected_x), int(expected_y))
            
            # 验证位置更新的准确性
            self.assertEqual(
                self.window.current_pos, 
                expected_pos,
                f"位置更新计算错误: 平滑因子{factor}, 期望{expected_pos}, 实际{self.window.current_pos}"
            )
            
            # 重置当前位置继续下一次测试
            self.window.current_pos = QPoint(100, 100)
    
    def test_rapid_movement_precision(self):
        """测试快速移动时的精确度"""
        self.window.set_drag_mode("precise")
        initial_pos = QPoint(100, 100)
        self.window.move(initial_pos)
        self.window.current_pos = initial_pos
        self.window.target_pos = initial_pos
        
        # 模拟快速移动（大幅度、短时间）
        dx, dy = 100, 100
        elapsed = 5  # 毫秒
        
        # 计算快速移动的鼠标速度
        self.simulate_mouse_move(dx, dy, elapsed)
        
        # 执行多次位置更新，模拟连续帧更新
        for _ in range(5):
            self.window._update_position()
        
        # 验证经过多次更新后，位置是否接近目标位置
        # 在精确模式下，应该迅速接近目标位置
        target_pos = QPoint(initial_pos.x() + dx, initial_pos.y() + dy)
        x_diff = abs(self.window.current_pos.x() - target_pos.x())
        y_diff = abs(self.window.current_pos.y() - target_pos.y())
        
        # 精确模式下快速移动后，差距应该很小
        self.assertLess(x_diff, 5, f"快速移动X轴精度不足: 差距{x_diff}px")
        self.assertLess(y_diff, 5, f"快速移动Y轴精度不足: 差距{y_diff}px")
    
    def test_update_interval_effect(self):
        """测试不同更新间隔对跟踪精确度的影响"""
        original_interval = self.window.smoothing_timer.interval()
        
        test_intervals = [8, 16, 30]  # 毫秒
        results = {}
        
        for interval in test_intervals:
            # 设置更新间隔
            self.window.smoothing_timer.setInterval(interval)
            
            # 重置位置
            initial_pos = QPoint(100, 100)
            self.window.move(initial_pos)
            self.window.current_pos = initial_pos
            self.window.target_pos = initial_pos
            
            # 设置精确模式
            self.window.set_drag_mode("precise")
            
            # 模拟鼠标移动
            dx, dy = 50, 50
            self.simulate_mouse_move(dx, dy)
            
            # 模拟5次连续更新
            for _ in range(5):
                self.window._update_position()
            
            # 记录结果
            target_pos = QPoint(initial_pos.x() + dx, initial_pos.y() + dy)
            x_diff = abs(self.window.current_pos.x() - target_pos.x())
            y_diff = abs(self.window.current_pos.y() - target_pos.y())
            results[interval] = (x_diff, y_diff)
        
        # 恢复原始间隔
        self.window.smoothing_timer.setInterval(original_interval)
        
        # 验证更新间隔越小，跟踪精度越高
        for i in range(len(test_intervals) - 1):
            current_interval = test_intervals[i]
            next_interval = test_intervals[i + 1]
            
            # 获取当前和下一个间隔的误差
            current_error = results[current_interval][0] + results[current_interval][1]
            next_error = results[next_interval][0] + results[next_interval][1]
            
            # 较小间隔的误差应该小于或等于较大间隔的误差
            self.assertLessEqual(
                current_error, 
                next_error, 
                f"更新间隔{current_interval}ms的精度低于{next_interval}ms: {current_error} > {next_error}"
            )

if __name__ == '__main__':
    unittest.main()