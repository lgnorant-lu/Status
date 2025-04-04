"""
---------------------------------------------------------------
File name:                  conftest.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                测试配置和钩子
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

# 在测试开始前加载模拟模块，确保它们在其他模块导入之前就已经准备好
import sys
import os

# 导入模拟模块
from tests.mocks import *

# 添加项目根目录到sys.path，确保可以导入项目模块
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# 确保PyQt6的模拟模块已经在sys.modules中
if 'PyQt6' in sys.modules and 'PyQt6.QtWidgets' in sys.modules:
    # 确保QApplication在模拟模块中
    if hasattr(sys.modules['PyQt6.QtWidgets'], 'QApplication'):
        print("PyQt6模拟模块已正确加载（包含QApplication）")
    else:
        print("警告：PyQt6.QtWidgets模块中缺少QApplication类")
else:
    print("警告：PyQt6模拟模块未完全加载")
    
    # 强制重新加载模拟模块
    from tests.mocks import QApplication, QSystemTrayIcon, QMenu, QIcon, QAction, QObject, pyqtSignal
    
    # 创建模拟模块
    class QtWidgets:
        QSystemTrayIcon = QSystemTrayIcon
        QMenu = QMenu
        QApplication = QApplication
    
    class QtGui:
        QIcon = QIcon
        QAction = QAction
    
    class QtCore:
        QObject = QObject
        pyqtSignal = pyqtSignal
    
    class PyQt6:
        QtWidgets = QtWidgets
        QtGui = QtGui
        QtCore = QtCore
    
    # 添加到sys.modules中
    sys.modules['PyQt6'] = PyQt6
    sys.modules['PyQt6.QtWidgets'] = PyQt6.QtWidgets
    sys.modules['PyQt6.QtGui'] = PyQt6.QtGui
    sys.modules['PyQt6.QtCore'] = PyQt6.QtCore
    
    print("已手动重新加载PyQt6模拟模块")

import logging
import pytest
from pathlib import Path

# 获取项目根目录
project_root = Path(__file__).parent.parent

# 将项目根目录添加到Python路径
sys.path.insert(0, str(project_root))

# 禁用日志输出，避免测试日志污染
@pytest.fixture(scope="session", autouse=True)
def disable_logging():
    """在测试期间禁用日志输出"""
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)

# 创建测试目录的固定装置
@pytest.fixture(scope="session")
def test_dir():
    """返回测试目录的路径"""
    return os.path.dirname(os.path.abspath(__file__))

# 创建测试资源目录的固定装置
@pytest.fixture(scope="session")
def test_resources_dir(test_dir):
    """返回测试资源目录的路径"""
    resources_dir = os.path.join(test_dir, 'resources')
    os.makedirs(resources_dir, exist_ok=True)
    return resources_dir

# 模拟资源的创建和清理
@pytest.fixture
def mock_resource(test_resources_dir):
    """创建一个模拟资源文件并在测试后清理"""
    resource_path = os.path.join(test_resources_dir, 'mock_resource.txt')
    
    # 创建测试资源
    with open(resource_path, 'w', encoding='utf-8') as f:
        f.write('This is a mock resource for testing.')
    
    yield resource_path
    
    # 清理测试资源
    if os.path.exists(resource_path):
        os.remove(resource_path)

# 默认模拟配置
@pytest.fixture
def mock_config():
    """返回模拟配置字典"""
    return {
        "app_name": "Hollow-ming-test",
        "version": "0.1.0-test",
        "default_scene": "test_scene",
        "update_interval": 0.1,
        "window_size": (300, 400),
        "always_on_top": False,
        "start_minimized": False
    } 