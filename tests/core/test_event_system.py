"""
---------------------------------------------------------------
File name:                  test_event_system.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                事件系统测试
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import pytest
from unittest.mock import MagicMock, patch, Mock

from core.event_system import EventSystem, Event, EventType

class TestEventSystem:
    """事件系统测试用例"""

    def test_singleton_pattern(self):
        """测试单例模式实现"""
        system1 = EventSystem()
        system2 = EventSystem()
        assert system1 is system2, "EventSystem should be a singleton"

    def test_register_unregister_handler(self):
        """测试注册和注销事件处理器"""
        system = EventSystem()
        
        # 清空现有处理器，确保测试环境干净
        system.handlers = {}
        
        # 创建模拟处理器
        mock_handler = MagicMock()
        
        # 注册处理器
        system.register_handler(EventType.SYSTEM_STATUS_UPDATE, mock_handler)
        
        # 验证注册成功
        assert EventType.SYSTEM_STATUS_UPDATE in system.handlers
        assert mock_handler in system.handlers[EventType.SYSTEM_STATUS_UPDATE]
        
        # 注销处理器
        result = system.unregister_handler(EventType.SYSTEM_STATUS_UPDATE, mock_handler)
        
        # 验证注销成功
        assert result is True
        assert mock_handler not in system.handlers[EventType.SYSTEM_STATUS_UPDATE]
        
        # 测试注销不存在的处理器
        result = system.unregister_handler(EventType.SYSTEM_STATUS_UPDATE, mock_handler)
        assert result is False
        
        # 测试注销不存在的事件类型
        result = system.unregister_handler(EventType.ERROR, mock_handler)
        assert result is False

    def test_dispatch_event(self):
        """测试事件分发"""
        system = EventSystem()
        
        # 清空现有处理器，确保测试环境干净
        system.handlers = {}
        
        # 创建模拟处理器
        mock_handler1 = MagicMock()
        mock_handler2 = MagicMock()
        
        # 注册处理器
        system.register_handler(EventType.SYSTEM_STATUS_UPDATE, mock_handler1)
        system.register_handler(EventType.SYSTEM_STATUS_UPDATE, mock_handler2)
        
        # 创建事件数据
        test_data = {"cpu": 50, "memory": 1024}
        
        # 分发事件
        system.dispatch_event(EventType.SYSTEM_STATUS_UPDATE, "test_sender", test_data)
        
        # 验证处理器被调用
        mock_handler1.assert_called_once()
        mock_handler2.assert_called_once()
        
        # 验证事件参数
        event_arg = mock_handler1.call_args[0][0]
        assert isinstance(event_arg, Event)
        assert event_arg.type == EventType.SYSTEM_STATUS_UPDATE
        assert event_arg.sender == "test_sender"
        assert event_arg.data == test_data

    def test_handler_exception(self):
        """测试处理器异常处理"""
        system = EventSystem()
        
        # 清空现有处理器，确保测试环境干净
        system.handlers = {}
        
        # 创建异常处理器和正常处理器
        def exception_handler(event):
            raise Exception("Test exception")
        
        normal_handler = MagicMock()
        
        # 注册处理器
        system.register_handler(EventType.ERROR, exception_handler)
        system.register_handler(EventType.ERROR, normal_handler)
        
        # 直接替换logger以验证调用
        real_logger = Mock()
        real_logger.error = Mock()
        system.logger = real_logger
        
        # 分发事件
        system.dispatch_event(EventType.ERROR, "test_sender", "test_data")
        
        # 验证异常被记录
        assert real_logger.error.called
        
        # 验证第二个处理器被调用，说明系统捕获异常后继续工作
        assert normal_handler.called

    def test_event_handling(self):
        """测试事件处理标记功能"""
        system = EventSystem()
        
        # 清空现有处理器，确保测试环境干净
        system.handlers = {}
        
        # 创建标记事件为已处理的处理器和不标记的处理器
        def marking_handler(event):
            event.handled = True
        
        mock_handler = MagicMock()
        
        # 注册处理器
        system.register_handler(EventType.USER_INTERACTION, marking_handler)
        system.register_handler(EventType.USER_INTERACTION, mock_handler)
        
        # 分发事件
        system.dispatch_event(EventType.USER_INTERACTION, "test_sender", "test_data")
        
        # 验证第二个处理器没有被调用，因为事件被标记为已处理
        mock_handler.assert_not_called()

    def test_get_handlers_count(self):
        """测试获取处理器数量"""
        system = EventSystem()
        
        # 清空现有处理器，确保测试环境干净
        system.handlers = {}
        
        # 创建模拟处理器
        mock_handler1 = MagicMock()
        mock_handler2 = MagicMock()
        mock_handler3 = MagicMock()
        
        # 注册处理器
        system.register_handler(EventType.SYSTEM_STATUS_UPDATE, mock_handler1)
        system.register_handler(EventType.SYSTEM_STATUS_UPDATE, mock_handler2)
        system.register_handler(EventType.APPLICATION_START, mock_handler3)
        
        # 验证处理器数量
        assert system.get_handlers_count() == 3
        assert system.get_handlers_count(EventType.SYSTEM_STATUS_UPDATE) == 2
        assert system.get_handlers_count(EventType.APPLICATION_START) == 1
        assert system.get_handlers_count(EventType.APPLICATION_EXIT) == 0

    def test_clear_handlers(self):
        """测试清除处理器"""
        system = EventSystem()
        
        # 清空现有处理器，确保测试环境干净
        system.handlers = {}
        
        # 创建模拟处理器
        mock_handler1 = MagicMock()
        mock_handler2 = MagicMock()
        mock_handler3 = MagicMock()
        
        # 注册处理器
        system.register_handler(EventType.SYSTEM_STATUS_UPDATE, mock_handler1)
        system.register_handler(EventType.SYSTEM_STATUS_UPDATE, mock_handler2)
        system.register_handler(EventType.APPLICATION_START, mock_handler3)
        
        # 清除特定类型的处理器
        system.clear_handlers(EventType.SYSTEM_STATUS_UPDATE)
        
        # 验证清除结果
        assert system.get_handlers_count(EventType.SYSTEM_STATUS_UPDATE) == 0
        assert system.get_handlers_count(EventType.APPLICATION_START) == 1
        
        # 清除所有处理器
        system.clear_handlers()
        
        # 验证清除结果
        assert system.get_handlers_count() == 0 