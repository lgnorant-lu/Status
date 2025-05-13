"""
---------------------------------------------------------------
File name:                  test_main_pet_window.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                主窗口拖拽功能测试
----------------------------------------------------------------

Changed history:
                            2025/05/13: 初始化;
                            2025/05/13: 添加拖拽功能测试;
----
"""

import unittest
import sys
import os
from unittest.mock import MagicMock, patch

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

from PySide6.QtCore import Qt, QPoint, QSize, QTimer
from PySide6.QtGui import QMouseEvent, QPixmap
from PySide6.QtWidgets import QApplication
from status.ui.main_pet_window import MainPetWindow

# 需要有一个QApplication实例
app = QApplication.instance()
if not app:
    app = QApplication([])

class TestMainPetWindow(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.window = MainPetWindow()
        
        # 创建一个测试用的QPixmap
        self.test_pixmap = QPixmap(100, 100)
        self.test_pixmap.fill(Qt.GlobalColor.red)
        
        # 设置窗口图像
        self.window.set_image(self.test_pixmap)
        
        # 记录原始位置
        self.original_pos = self.window.pos()

    def tearDown(self):
        """Tear down test fixtures"""
        self.window.close()
        self.window.deleteLater()

    def test_initialization(self):
        """Test the initialization of the MainPetWindow"""
        self.assertIsNotNone(self.window)
        self.assertEqual(self.window.windowTitle(), "Status Pet")
        self.assertTrue(self.window.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground))
        
        # 验证窗口大小与图像一致
        self.assertEqual(self.window.size(), QSize(100, 100))

    def test_set_image(self):
        """Test setting image to the window"""
        # 创建一个新的测试图像
        new_pixmap = QPixmap(200, 150)
        new_pixmap.fill(Qt.GlobalColor.blue)
        
        # 设置新图像
        self.window.set_image(new_pixmap)
        
        # 验证图像和窗口大小
        self.assertIsNotNone(self.window.image)
        if self.window.image:
            self.assertEqual(self.window.image.size(), QSize(200, 150))
        self.assertEqual(self.window.size(), QSize(200, 150))

    def test_drag_mode_setting(self):
        """Test setting drag modes"""
        # 测试设置有效的拖动模式
        self.window.set_drag_mode("precise")
        self.assertEqual(self.window.drag_mode, "precise")
        
        self.window.set_drag_mode("smooth")
        self.assertEqual(self.window.drag_mode, "smooth")
        
        self.window.set_drag_mode("smart")
        self.assertEqual(self.window.drag_mode, "smart")
        
        # 测试无效模式不会改变当前模式
        current_mode = self.window.drag_mode
        self.window.set_drag_mode("invalid_mode")
        self.assertEqual(self.window.drag_mode, current_mode)

    def test_mouse_press_event(self):
        """Test mouse press event handling"""
        # 模拟鼠标点击
        event = MagicMock()
        event.button.return_value = Qt.MouseButton.LeftButton
        event.position.return_value.toPoint.return_value = QPoint(50, 50)
        
        # 创建一个信号捕获器
        clicked_signal_received = False
        def on_clicked(position):
            nonlocal clicked_signal_received
            clicked_signal_received = True
            self.assertEqual(position, QPoint(50, 50))
        
        # 连接信号
        self.window.clicked.connect(on_clicked)
        
        # 触发事件
        self.window.mousePressEvent(event)
        
        # 验证结果
        self.assertTrue(self.window.is_dragging)
        self.assertFalse(self.window.drag_activated)  # 应该还未激活
        self.assertTrue(clicked_signal_received)

    def test_small_movement_does_not_activate_drag(self):
        """Test that small movements don't activate dragging"""
        # 设置拖动模式
        self.window.set_drag_mode("smart")
        
        # 模拟鼠标按下
        press_event = MagicMock()
        press_event.button.return_value = Qt.MouseButton.LeftButton
        press_event.position.return_value.toPoint.return_value = QPoint(50, 50)
        self.window.mousePressEvent(press_event)
        
        # 模拟很小的移动（小于DRAG_THRESHOLD）
        move_event = MagicMock()
        move_event.position.return_value.toPoint.return_value = QPoint(51, 51)  # 只移动1个像素
        self.window.mouseMoveEvent(move_event)
        
        # 验证拖动未激活
        self.assertFalse(self.window.drag_activated)

    def test_movement_activates_drag(self):
        """Test that movement beyond threshold activates dragging"""
        # 设置拖动模式
        self.window.set_drag_mode("smart")
        
        # 模拟鼠标按下
        press_event = MagicMock()
        press_event.button.return_value = Qt.MouseButton.LeftButton
        press_event.position.return_value.toPoint.return_value = QPoint(50, 50)
        self.window.mousePressEvent(press_event)
        
        # 模拟足够大的移动（大于DRAG_THRESHOLD）
        move_event = MagicMock()
        move_event.position.return_value.toPoint.return_value = QPoint(55, 55)  # 移动5个像素
        
        # 捕获拖动信号
        drag_signal_received = False
        def on_dragged(position):
            nonlocal drag_signal_received
            drag_signal_received = True
        
        self.window.dragged.connect(on_dragged)
        
        # 触发移动
        self.window.mouseMoveEvent(move_event)
        
        # 验证拖动已激活
        self.assertTrue(self.window.drag_activated)
        self.assertTrue(drag_signal_received)

    def test_drag_and_release(self):
        """Test complete drag and release cycle"""
        # 设置拖动模式为精确模式，以便测试立即响应
        self.window.set_drag_mode("precise")
        
        # 记录原始位置
        original_pos = self.window.pos()
        
        # 模拟鼠标按下
        press_event = MagicMock()
        press_event.button.return_value = Qt.MouseButton.LeftButton
        press_event.position.return_value.toPoint.return_value = QPoint(50, 50)
        self.window.mousePressEvent(press_event)
        
        # 模拟拖动
        move_event = MagicMock()
        move_event.position.return_value.toPoint.return_value = QPoint(70, 70)  # 移动20像素
        self.window.mouseMoveEvent(move_event)
        
        # 验证拖动已激活
        self.assertTrue(self.window.drag_activated)
        
        # 捕获释放信号
        drop_signal_received = False
        def on_dropped(position):
            nonlocal drop_signal_received
            drop_signal_received = True
            self.assertEqual(position, QPoint(70, 70))
        
        self.window.dropped.connect(on_dropped)
        
        # 模拟鼠标释放
        release_event = MagicMock()
        release_event.button.return_value = Qt.MouseButton.LeftButton
        release_event.position.return_value.toPoint.return_value = QPoint(70, 70)
        self.window.mouseReleaseEvent(release_event)
        
        # 验证结果
        self.assertFalse(self.window.is_dragging)
        self.assertFalse(self.window.drag_activated)
        self.assertTrue(drop_signal_received)
        
        # 等待平滑移动完成 - 使用timer而不是阻塞操作
        def check_position():
            # 计算预期的位置偏移
            expected_delta = QPoint(20, 20)  # 鼠标移动了(70,70)-(50,50)=(20,20)
            
            # 假设窗口已经移动到目标位置
            # 注意：在实际测试中可能需要考虑屏幕边界
            # 但对于此测试我们简单验证窗口已移动
            current_pos = self.window.pos()
            self.assertNotEqual(current_pos, original_pos)
            
            # 由于QTimer可能是None，安全处理
            if QTimer is not None:
                QTimer.singleShot(100, lambda: app.exit() if app else None)
        
        # 在短暂延迟后检查位置变化
        if QTimer is not None and app is not None:
            QTimer.singleShot(500, check_position)
            app.exec()

    def test_watchdog_timer(self):
        """Test that watchdog timer prevents stuck dragging state"""
        # 设置拖动模式
        self.window.set_drag_mode("smart")
        
        # 模拟鼠标按下
        press_event = MagicMock()
        press_event.button.return_value = Qt.MouseButton.LeftButton
        press_event.position.return_value.toPoint.return_value = QPoint(50, 50)
        self.window.mousePressEvent(press_event)
        
        # 验证拖动状态和看门狗定时器
        self.assertTrue(self.window.is_dragging)
        self.assertTrue(self.window.watchdog_timer.isActive())
        
        # 模拟情况：鼠标按钮被释放，但没有触发mouseReleaseEvent
        # (例如由于失去焦点或其他窗口事件干扰)
        with patch('PySide6.QtWidgets.QApplication.mouseButtons', 
                   return_value=Qt.MouseButton.NoButton):  # 模拟鼠标按钮已释放
            
            # 直接调用看门狗检查
            self.window._check_drag_state()
            
            # 验证拖动状态已重置
            self.assertFalse(self.window.is_dragging)
            self.assertFalse(self.window.drag_activated)
            self.assertFalse(self.window.watchdog_timer.isActive())

    def test_double_click_cancels_drag(self):
        """Test that double click cancels any ongoing drag operation"""
        # 设置拖动模式
        self.window.set_drag_mode("smart")
        
        # 模拟拖动开始
        self.window.is_dragging = True
        self.window.drag_activated = True
        self.window.watchdog_timer.start()
        
        # 捕获双击信号
        double_click_received = False
        def on_double_clicked(position):
            nonlocal double_click_received
            double_click_received = True
        
        self.window.double_clicked.connect(on_double_clicked)
        
        # 模拟双击事件
        event = MagicMock()
        event.button.return_value = Qt.MouseButton.LeftButton
        event.position.return_value.toPoint.return_value = QPoint(50, 50)
        
        self.window.mouseDoubleClickEvent(event)
        
        # 验证结果
        self.assertFalse(self.window.is_dragging)
        self.assertFalse(self.window.drag_activated)
        self.assertFalse(self.window.watchdog_timer.isActive())
        self.assertTrue(double_click_received)

if __name__ == '__main__':
    unittest.main() 