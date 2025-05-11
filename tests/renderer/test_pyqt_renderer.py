"""
测试：桌宠主窗口（KnightIdleWidget）基础属性与交互
"""
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QPoint
from renderer.pyqt_renderer import KnightIdleWidget

@pytest.fixture(scope="module")
def app():
    import sys
    app = QApplication.instance() or QApplication(sys.argv)
    yield app

@pytest.fixture
def widget(app):
    w = KnightIdleWidget()
    yield w
    w.close()

def test_window_flags(widget):
    # 无边框/置顶/工具窗口
    flags = widget.windowFlags()
    assert flags & Qt.WindowType.FramelessWindowHint
    assert flags & Qt.WindowType.WindowStaysOnTopHint
    assert flags & Qt.WindowType.Tool

def test_window_transparent(widget):
    # 透明窗口（背景透明）
    assert widget.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

def test_window_draggable(widget, qtbot):
    # 拖动窗口模拟：按下->移动->松开
    old_pos = widget.pos()
    qtbot.mousePress(widget, Qt.MouseButton.LeftButton, pos=QPoint(10, 10))
    qtbot.mouseMove(widget, QPoint(30, 30))
    qtbot.mouseRelease(widget, Qt.MouseButton.LeftButton, pos=QPoint(30, 30))
    # 检查窗口位置发生变化
    assert widget.pos() != old_pos

def test_tray_icon_and_quit(app, qtbot):
    """测试：主窗口托盘菜单存在且可触发退出"""
    from renderer.pyqt_renderer import KnightIdleWidget
    w = KnightIdleWidget()
    w.show()
    # 检查托盘图标存在
    assert hasattr(w, "tray") and w.tray is not None
    # 检查托盘菜单存在且含有退出项
    menu = getattr(w.tray, "contextMenu", lambda: None)()
    assert menu is not None
    action_texts = [a.text().lower() for a in menu.actions()]
    assert any("退" in t or "exit" in t for t in action_texts)
    # 模拟点击退出（不直接关闭app，防止测试环境退出）
    # 可选：action = next(a for a in menu.actions() if "退" in a.text() or "exit" in a.text().lower())
    # action.trigger()
    w.close()

# 可根据需要继续补充双击、边界检测等测试
