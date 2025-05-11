import os
import sys
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QPoint
import time

# pytest-qt为GUI测试提供QtBot
# pytest_plugins = ["pytestqt.plugin"]  # 已移除，避免插件冲突

import importlib.util
spec = importlib.util.spec_from_file_location("simple_knight_idle_demo", os.path.join(os.path.dirname(__file__), "../simple_knight_idle_demo.py"))
simple_knight_idle_demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(simple_knight_idle_demo)
KnightIdleWidget = simple_knight_idle_demo.KnightIdleWidget
IDLE_FRAME_COUNT = simple_knight_idle_demo.IDLE_FRAME_COUNT

@pytest.fixture(scope="session")
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

# 1. 测试窗口是否可见，初始位置和尺寸
def test_widget_visible_and_size(qtbot, app):
    widget = KnightIdleWidget()
    qtbot.addWidget(widget)
    widget.show()
    assert widget.isVisible()
    assert widget.width() == 64
    assert widget.height() == 64

# 2. 测试动画帧切换（定时器模拟）
def test_animation_frame_switch(qtbot, app):
    widget = KnightIdleWidget()
    qtbot.addWidget(widget)
    widget.show()
    orig_frame = widget.current_frame
    qtbot.wait(simple_knight_idle_demo.FRAME_INTERVAL_MS + 50)
    assert widget.current_frame != orig_frame

# 3. 测试鼠标拖动
def test_drag_move(qtbot, app):
    widget = KnightIdleWidget()
    qtbot.addWidget(widget)
    widget.show()
    orig_pos = widget.pos()
    # 模拟鼠标按下、移动、释放
    qtbot.mousePress(widget, Qt.MouseButton.LeftButton, pos=QPoint(10, 10))
    qtbot.mouseMove(widget, QPoint(30, 30))
    qtbot.mouseRelease(widget, Qt.MouseButton.LeftButton, pos=QPoint(30, 30))
    # 拖动后位置应变化
    assert widget.pos() != orig_pos

# 4. 测试双击闪烁反馈
def test_double_click_flash(qtbot, app):
    widget = KnightIdleWidget()
    qtbot.addWidget(widget)
    widget.show()
    orig_opacity = widget.windowOpacity()
    qtbot.mouseDClick(widget, Qt.MouseButton.LeftButton, pos=QPoint(20, 20))
    # 闪烁后应恢复原始透明度
    qtbot.wait(150)
    assert abs(widget.windowOpacity() - orig_opacity) < 0.01

# 5. 测试窗口边界检测（移动到极限位置）
def test_move_to_screen_edge(qtbot, app):
    widget = KnightIdleWidget()
    qtbot.addWidget(widget)
    widget.show()
    # 移动到极限位置
    widget.move(-1000, -1000)
    qtbot.wait(50)
    # 触发一次拖动逻辑
    qtbot.mousePress(widget, Qt.MouseButton.LeftButton, pos=QPoint(5, 5))
    qtbot.mouseMove(widget, QPoint(10, 10))
    qtbot.mouseRelease(widget, Qt.MouseButton.LeftButton, pos=QPoint(10, 10))
    # 应被拉回屏幕可见区域
    geo = widget.frameGeometry()
    screen = widget.screen().availableGeometry()
    assert geo.left() >= screen.left()
    assert geo.top() >= screen.top()
