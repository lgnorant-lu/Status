"""
---------------------------------------------------------------
File name:                  test_events_manager.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                事件管理器测试，特别关注基本功能
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建;
----
"""

import pytest
from unittest.mock import MagicMock, patch, Mock

from status.core.events import EventManager, EventType, Event

class TestEventManager:
    """事件管理器测试用例"""

    def test_singleton_pattern(self):
        """测试单例模式实现"""
        manager1 = EventManager()
        manager2 = EventManager()
        assert manager1 is manager2, "EventManager should be a singleton"
    
    def test_register_and_dispatch(self):
        """测试注册处理器和分发事件"""
        # 创建EventManager实例
        manager = EventManager()
        
        # 清空现有处理器，确保测试环境干净
        if hasattr(manager, 'handlers'):
            manager.handlers = {}
        
        # 创建模拟处理器
        mock_handler = MagicMock()
        
        # 注册处理器
        manager.register_handler(EventType.SYSTEM_STATUS_UPDATE, mock_handler)
        
        # 分发事件
        test_data = {"message": "Hello"}
        manager.dispatch_event(EventType.SYSTEM_STATUS_UPDATE, None, test_data)
        
        # 验证处理器被调用
        mock_handler.assert_called_once()
        
        # 验证事件参数
        event_arg = mock_handler.call_args[0][0]
        assert event_arg.data == test_data
        
        # 测试取消订阅
        mock_handler.reset_mock()
        result = manager.unregister_handler(EventType.SYSTEM_STATUS_UPDATE, mock_handler)
        assert result is True
        
        # 再次分发事件
        manager.dispatch_event(EventType.SYSTEM_STATUS_UPDATE, None, test_data)
        
        # 验证处理器没有被调用，因为已经取消订阅
        mock_handler.assert_not_called()
    
    def test_event_instance_dispatch(self):
        """测试使用Event实例直接分发"""
        # 创建EventManager实例
        manager = EventManager()
        
        # 清空现有处理器，确保测试环境干净
        if hasattr(manager, 'handlers'):
            manager.handlers = {}
        
        # 创建模拟处理器
        mock_handler = MagicMock()
        
        # 注册处理器
        manager.register_handler(EventType.USER_INTERACTION, mock_handler)
        
        # 创建事件并分发
        test_data = {"message": "Hello User"}
        event = Event(EventType.USER_INTERACTION, None, test_data)
        manager.dispatch(event)
        
        # 验证处理器被调用
        mock_handler.assert_called_once()
        
        # 验证事件参数
        event_arg = mock_handler.call_args[0][0]
        assert event_arg.data == test_data 