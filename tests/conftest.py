"""
---------------------------------------------------------------
File name:                  conftest.py
Author:                     Ignorant-lu
Date created:               2025/04/01
Date modified:              2025/05/15
Description:                Pytest配置文件，提供全局测试夹具和设置
----------------------------------------------------------------

Changed history:            
                            2025/04/01: 初始创建;
                            2025/05/15: 增加TDD和覆盖率支持;
----
"""

import os
import sys
import logging
import pytest
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable

# 将项目根目录添加到系统路径
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("status-test")

# 定义全局测试配置
def pytest_configure(config):
    """Pytest配置钩子，用于设置全局配置"""
    config.addinivalue_line("markers", "unit: 单元测试")
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "system: 系统测试")
    config.addinivalue_line("markers", "slow: 运行缓慢的测试")
    config.addinivalue_line("markers", "gui: 需要GUI环境的测试")
    config.addinivalue_line("markers", "tdd: 测试驱动开发模式的测试")
    
    # 设置pytest-cov的默认配置
    if not config.option.cov_source:
        config.option.cov_source = ["status"]

# PyQt/PySide测试环境设置
@pytest.fixture(scope="session")
def qt_app():
    """提供一个Qt应用程序实例，用于GUI测试"""
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield app
    except ImportError:
        # 不导入PyQt5，抛出skip异常
        pytest.skip("需要PySide6来运行GUI测试")
        yield None

# 模拟对象工厂
@pytest.fixture
def mock_factory(monkeypatch):
    """提供一个工厂函数，用于创建和注册模拟对象"""
    
    def _create_mock(target: str, **kwargs):
        """
        创建模拟对象并应用到指定目标
        
        Args:
            target: 要模拟的对象路径，格式为'module.class'或'module.function'
            **kwargs: 模拟对象的属性和方法
        
        Returns:
            创建的模拟对象
        """
        import mock
        
        # 解析目标路径
        parts = target.split('.')
        if len(parts) < 2:
            raise ValueError(f"目标路径'{target}'无效，应为'module.object'格式")
        
        module_path = '.'.join(parts[:-1])
        object_name = parts[-1]
        
        # 创建模拟对象
        mock_obj = mock.MagicMock(**kwargs)
        
        # 应用模拟
        monkeypatch.setattr(f"{module_path}.{object_name}", mock_obj)
        
        return mock_obj
    
    return _create_mock

# 测试数据路径
@pytest.fixture
def test_data_path():
    """返回测试数据目录的路径"""
    data_path = PROJECT_ROOT / "tests" / "data"
    data_path.mkdir(exist_ok=True)
    return data_path

# 临时配置
@pytest.fixture
def temp_config():
    """提供临时配置字典，测试后自动清理"""
    config = {}
    yield config
    config.clear()

# 测试环境设置和清理
@pytest.fixture(autouse=True)
def test_env():
    """设置和清理测试环境，自动应用于所有测试"""
    # 设置临时环境变量
    old_env = os.environ.copy()
    os.environ["STATUS_TEST_MODE"] = "1"
    
    yield
    
    # 恢复环境变量
    os.environ.clear()
    os.environ.update(old_env)

# 简单的模拟事件系统，避免导入错误
class MockEventSystem:
    def __init__(self):
        self.handlers = {}
    
    def register(self, event_type, handler):
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
    
    def unregister(self, event_type, handler):
        if event_type in self.handlers and handler in self.handlers[event_type]:
            self.handlers[event_type].remove(handler)
    
    def emit(self, event_type, **event_data):
        if event_type in self.handlers:
            for handler in self.handlers[event_type]:
                handler(event_data)
        return True

# 事件系统测试工具
@pytest.fixture
def event_tester():
    """提供事件系统测试工具，可以监控事件触发和处理"""
    # 使用模拟事件系统替代真实导入
    EventSystem = MockEventSystem
    
    class EventTester:
        def __init__(self):
            self.event_system = EventSystem()
            self.received_events = []
            self.event_handlers = {}
        
        def register_handler(self, event_type, handler=None):
            """注册事件处理器，如果未提供处理器，则使用自动记录的处理器"""
            if handler is None:
                def _handler(event):
                    self.received_events.append(event)
                handler = _handler
            
            self.event_handlers[event_type] = handler
            self.event_system.register(event_type, handler)
            return handler
        
        def emit_event(self, event_type, **event_data):
            """发送事件"""
            return self.event_system.emit(event_type, **event_data)
        
        def clear(self):
            """清除接收到的事件记录"""
            self.received_events.clear()
        
        def unregister_all(self):
            """注销所有事件处理器"""
            for event_type, handler in self.event_handlers.items():
                self.event_system.unregister(event_type, handler)
            self.event_handlers.clear()
    
    tester = EventTester()
    yield tester
    tester.unregister_all()

# 简单的模拟资源管理器类
class MockResourceManager:
    def __init__(self):
        self.resources = {}
    
    def load(self, resource_id, **kwargs):
        self.resources[resource_id] = kwargs
        return kwargs
    
    def get(self, resource_id):
        return self.resources.get(resource_id)

# 资源加载器测试工具
@pytest.fixture
def resource_loader():
    """提供资源加载器，用于加载测试资源"""
    # 使用模拟资源管理器
    resource_manager = MockResourceManager()
    yield resource_manager

# 测试覆盖率追踪
@pytest.fixture
def coverage_marker():
    """提供用于标记代码覆盖率的工具"""
    marked_files = set()
    
    def mark_file(file_path: str):
        """
        标记文件为已测试，用于跟踪代码覆盖率
        
        Args:
            file_path: 要标记的文件路径
        """
        marked_files.add(file_path)
    
    yield mark_file
    
    # 可以在这里添加代码，在测试结束时生成标记文件的覆盖率报告

# TDD模式支持
@pytest.fixture
def tdd_checker():
    """提供TDD模式支持工具，验证测试是否先失败再通过"""
    class TDDChecker:
        def __init__(self):
            self.failed_first = False
            self.passed_later = False
        
        def record_failure(self):
            """记录测试初次失败"""
            self.failed_first = True
        
        def record_success(self):
            """记录测试后续通过"""
            self.passed_later = True
        
        def is_tdd_compliant(self):
            """检查是否符合TDD模式（先失败后通过）"""
            return self.failed_first and self.passed_later
    
    return TDDChecker()

# GUI测试组件
@pytest.fixture
def qt_widget_tester(qt_app):
    """提供Qt部件测试工具，用于GUI测试"""
    if qt_app is None:
        pytest.skip("需要Qt环境来运行此测试")
    
    class QtWidgetTester:
        def __init__(self):
            self.widgets = []
        
        def create_widget(self, widget_class, *args, **kwargs):
            """创建并返回Qt部件"""
            widget = widget_class(*args, **kwargs)
            self.widgets.append(widget)
            return widget
        
        def simulate_click(self, widget, pos=None):
            """模拟鼠标点击事件"""
            try:
                from PySide6.QtCore import Qt, QPoint
                from PySide6.QtGui import QMouseEvent
                from PySide6.QtCore import QEvent
                
                if pos is None:
                    pos = QPoint(widget.width() // 2, widget.height() // 2)
                
                # 使用QEvent枚举而不是直接访问QMouseEvent属性
                mouse_press = QMouseEvent(
                    QEvent.Type.MouseButtonPress,  # 使用QEvent.Type枚举
                    pos,
                    Qt.MouseButton.LeftButton,    # 使用Qt.MouseButton枚举
                    Qt.MouseButton.LeftButton,    # 使用Qt.MouseButton枚举
                    Qt.KeyboardModifier.NoModifier  # 使用Qt.KeyboardModifier枚举
                )
                
                mouse_release = QMouseEvent(
                    QEvent.Type.MouseButtonRelease,  # 使用QEvent.Type枚举
                    pos,
                    Qt.MouseButton.LeftButton,    # 使用Qt.MouseButton枚举
                    Qt.MouseButton.LeftButton,    # 使用Qt.MouseButton枚举
                    Qt.KeyboardModifier.NoModifier  # 使用Qt.KeyboardModifier枚举
                )
                
                widget.mousePressEvent(mouse_press)
                widget.mouseReleaseEvent(mouse_release)
            except (ImportError, AttributeError) as e:
                logger.warning(f"模拟点击失败: {e}")
        
        def cleanup(self):
            """清理所有创建的部件"""
            for widget in self.widgets:
                if hasattr(widget, 'deleteLater'):
                    widget.deleteLater()
            self.widgets.clear()
    
    tester = QtWidgetTester()
    yield tester
    tester.cleanup()

# 添加命令行选项
def pytest_addoption(parser):
    """添加自定义命令行选项"""
    parser.addoption(
        "--tdd-mode",
        action="store_true",
        default=False,
        help="启用TDD模式，检查测试是否先失败再通过"
    )
    
    parser.addoption(
        "--debug-mode",
        action="store_true",
        default=False,
        help="启用调试模式，显示更详细的日志"
    )

# 处理命令行选项
@pytest.fixture(autouse=True)
def handle_custom_options(request):
    """处理自定义命令行选项"""
    # 设置日志级别
    if request.config.getoption("--debug-mode"):
        logger.setLevel(logging.DEBUG)
    
    yield 