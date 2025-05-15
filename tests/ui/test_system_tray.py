"""
---------------------------------------------------------------
File name:                  test_system_tray.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                系统托盘功能测试
----------------------------------------------------------------

Changed history:            
                            2025/05/13: 初始创建;
                            2025/05/16: 修复退出功能;
----
"""

import sys
import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication

# 确保测试环境中有QApplication实例
@pytest.fixture
def app():
    """创建Qt应用程序实例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # 不在这里调用app.quit()，避免提前结束测试

@pytest.fixture
def mock_image():
    """模拟图像资源"""
    with patch('PySide6.QtGui.QIcon') as mock_icon:
        mock_icon_instance = MagicMock()
        mock_icon.return_value = mock_icon_instance
        yield mock_icon

# 导入系统托盘管理器
from status.ui.system_tray import SystemTrayManager

def test_system_tray_init(app, mock_image):
    """测试系统托盘初始化"""
    # 创建模拟的退出回调函数
    mock_quit_callback = MagicMock()
    mock_show_hide_callback = MagicMock()
    mock_drag_mode_callback = MagicMock()
    mock_toggle_interaction_callback = MagicMock()
    
    # 初始化系统托盘管理器
    tray_manager = SystemTrayManager(app=app) # Pass the app fixture
    tray_manager.setup_menu(
        show_hide_callback=mock_show_hide_callback,
        exit_callback=mock_quit_callback,
        drag_mode_callback=mock_drag_mode_callback,
        toggle_interaction_callback=mock_toggle_interaction_callback
    )
    
    # 验证托盘是否被创建
    assert tray_manager.tray_icon is not None
    # 验证托盘菜单是否被创建和设置
    assert tray_manager.tray_icon.contextMenu() is not None
    # 验证菜单中有动作 (基本检查)
    assert len(tray_manager.tray_icon.contextMenu().actions()) > 0

def test_system_tray_quit(app, mock_image):
    """测试系统托盘退出功能"""
    # 创建模拟的退出回调函数
    mock_quit_callback = MagicMock()
    
    # 初始化系统托盘管理器
    tray_manager = SystemTrayManager(app=app) # Pass the app fixture
    tray_manager.setup_menu(exit_callback=mock_quit_callback)
    
    # 模拟触发退出动作
    exit_action = None
    if tray_manager.tray_icon.contextMenu():
        for action in tray_manager.tray_icon.contextMenu().actions():
            # The text for quit action is "退出"
            if action.text() == "退出":
                exit_action = action
                break
    
    assert exit_action is not None, "未找到'退出'菜单项"
    exit_action.triggered.emit()
    
    # 验证退出回调是否被调用
    mock_quit_callback.assert_called_once() 