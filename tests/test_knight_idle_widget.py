import os
import sys
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

# 保证PyQt应用单例
@pytest.fixture(scope="session")
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

# 导入正式模块
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
from renderer.pyqt_renderer import KnightIdleWidget, FRAME_SIZE, IDLE_FRAME_COUNT
from resources.asset_manager import AssetManager

# 1. 测试Idle动画帧加载
def test_idle_frames_loaded():
    am = AssetManager()
    frames = am.load_idle_frames(IDLE_FRAME_COUNT)
    assert len(frames) == IDLE_FRAME_COUNT
    for frame in frames:
        assert isinstance(frame, QPixmap)
        assert frame.width() == FRAME_SIZE[0]
        assert frame.height() == FRAME_SIZE[1]

# 2. 测试窗口属性
@pytest.mark.parametrize("flag", [Qt.WindowType.FramelessWindowHint, Qt.WindowType.WindowStaysOnTopHint, Qt.WindowType.Tool])
def test_window_flags(app, flag):
    widget = KnightIdleWidget()
    assert widget.windowFlags() & flag
    assert widget.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    assert widget.width() == FRAME_SIZE[0]
    assert widget.height() == FRAME_SIZE[1]

# 3. 测试动画循环
def test_frame_cycling(app):
    widget = KnightIdleWidget()
    orig = widget.current_frame
    widget.next_frame()
    assert widget.current_frame == (orig + 1) % IDLE_FRAME_COUNT
    widget.current_frame = IDLE_FRAME_COUNT - 1
    widget.next_frame()
    assert widget.current_frame == 0

# 4. 测试资源缺失容错
def test_missing_frame_tolerant(app):
    am = AssetManager()
    frames = am.load_idle_frames(10)
    assert len(frames) == 10

# 5. 交互相关测试建议用pytest-qt扩展
