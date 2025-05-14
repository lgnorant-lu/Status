"""
---------------------------------------------------------------
File name:                  test_hover_interaction.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                测试桌宠的悬停(hover)交互功能
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# 添加项目根目录到系统路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from PySide6.QtCore import QPoint, Qt, QEvent
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication

# 导入被测试的模块
from status.interaction.interaction_handler import InteractionHandler
from status.interaction.interaction_zones import InteractionType
from status.core.event_system import EventSystem, EventType
from status.behavior.pet_state import PetState
from status.behavior.interaction_state_adapter import InteractionStateAdapter

# 确保有Qt应用程序实例
app = None
if not QApplication.instance():
    app = QApplication(sys.argv)

class TestHoverInteraction(unittest.TestCase):
    """测试悬停交互功能"""
    
    def setUp(self):
        """每个测试前的设置"""
        # 模拟事件系统
        self.event_system_patcher = patch('status.core.event_system.EventSystem')
        self.mock_event_system = self.event_system_patcher.start()
        self.mock_event_system_instance = MagicMock()
        self.mock_event_system.get_instance.return_value = self.mock_event_system_instance
        
        # 创建交互处理器和模拟主窗口
        self.mock_window = MagicMock()
        self.interaction_handler = InteractionHandler(parent_window=self.mock_window)
        
        # 手动添加event_system属性
        self.interaction_handler.event_system = self.mock_event_system_instance
        
        # 添加mock方法
        self.interaction_handler._publish_interaction_event = MagicMock()
        
        # 初始化交互处理器
        with patch.object(self.interaction_handler, 'zone_manager'):
            self.interaction_handler._initialize()
            
        # 模拟状态机
        self.mock_state_machine = MagicMock()
        
        # 创建交互状态适配器
        self.interaction_adapter = InteractionStateAdapter(self.mock_state_machine)
        
        # 设置交互状态适配器属性
        self.interaction_adapter.event_system = self.mock_event_system_instance
        self.interaction_adapter._pet_state_machine = self.mock_state_machine
        
        # 模拟交互区域管理器
        self.interaction_handler.zone_manager = MagicMock()
        
        # 模拟区域和支持的交互类型
        self.mock_zone = MagicMock()
        self.mock_zone.zone_id = "test_zone"
        self.mock_zone.supported_interactions = {InteractionType.HOVER}
        
        # 设置模拟区域管理器的get_zones_at_point方法返回我们的模拟区域
        self.interaction_handler.zone_manager.get_zones_at_point.return_value = [self.mock_zone]
        
    def tearDown(self):
        """每个测试后的清理"""
        self.event_system_patcher.stop()
        
    def test_hover_event_detected(self):
        """测试是否能正确检测到hover事件"""
        # 创建鼠标移动事件
        pos = (100, 100)
        
        # 创建QMouseEvent - 使用非弃用的构造函数
        qt_event = QMouseEvent(
            QEvent.Type.MouseMove,  
            QPoint(pos[0], pos[1]),  # 本地位置
            QPoint(pos[0], pos[1]),  # 场景位置
            QPoint(pos[0], pos[1]),  # 全局位置
            Qt.MouseButton.NoButton,  # 按钮
            Qt.MouseButton.NoButton,  # 按钮状态
            Qt.KeyboardModifier.NoModifier  # 键盘修饰符
        )
        
        # 调用鼠标移动处理方法
        result = self.interaction_handler._handle_mouse_move(pos, qt_event)
        
        # 验证结果
        self.assertTrue(result, "悬停事件应该被检测到")
        self.assertEqual(self.interaction_handler.current_hover_zone, "test_zone", "当前悬停区域应该更新")
        
        # 验证是否发布了正确的交互事件
        self.interaction_handler._publish_interaction_event.assert_called_with(
            InteractionType.HOVER, 
            "test_zone", 
            {'x': pos[0], 'y': pos[1], 'original_qt_event_type': 'move'}
        )
        
    def test_hover_state_change(self):
        """测试hover事件是否能触发状态变化"""
        # 创建事件数据
        event_data = {
            'interaction_type': InteractionType.HOVER.name,
            'zone_id': 'test_zone',
            'data': {'x': 100, 'y': 100}
        }
        
        # 模拟交互状态适配器
        self.interaction_adapter._initialize()
            
        # 模拟事件监听器回调，使用正确的方法名
        mock_event = MagicMock()
        mock_event.data = event_data
        
        # 修改交互到状态的映射
        self.interaction_adapter.interaction_to_state = {
            InteractionType.HOVER.name: PetState.HOVER
        }
        
        # 调用方法
        self.interaction_adapter._on_user_interaction(mock_event)
            
        # 验证状态更新调用
        self.mock_state_machine.set_interaction_state.assert_called_with(PetState.HOVER)
        
    def test_hover_state_reset_on_mouse_leave(self):
        """测试鼠标离开时hover状态是否重置"""
        # 首先设置当前悬停区域
        self.interaction_handler.current_hover_zone = "test_zone"
        
        # 让get_zones_at_point返回空列表，模拟鼠标离开区域
        self.interaction_handler.zone_manager.get_zones_at_point.return_value = []
        
        # 创建鼠标移动事件
        pos = (200, 200)  # 位置在区域外
        qt_event = QMouseEvent(
            QEvent.Type.MouseMove,
            QPoint(pos[0], pos[1]),
            QPoint(pos[0], pos[1]),
            QPoint(pos[0], pos[1]),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier
        )
        
        # 调用鼠标移动处理方法
        self.interaction_handler._handle_mouse_move(pos, qt_event)
        
        # 验证当前悬停区域被清除
        self.assertIsNone(self.interaction_handler.current_hover_zone, "当前悬停区域应该被清除")
        
    def test_integration_with_main_window(self):
        """测试与主窗口的集成"""
        # 创建模拟的mouseEvent方法，该方法将测试鼠标悬停在窗口上的行为
        def mock_main_window_mouse_move(pos, button_type):
            local_pos = (pos.x(), pos.y())
            qt_event = QMouseEvent(
                QEvent.Type.MouseMove,
                pos,
                pos,
                pos,
                button_type,
                button_type,
                Qt.KeyboardModifier.NoModifier
            )
            return qt_event
            
        # 测试从主窗口的鼠标移动到交互处理器的完整流程
        with patch('status.main.StatusPet._create_mouse_event', side_effect=mock_main_window_mouse_move):
            # 模拟主窗口发送鼠标移动信号
            pos = QPoint(100, 100)
            
            # 手动调用交互处理器的鼠标事件处理方法
            self.interaction_handler.handle_mouse_event(
                mock_main_window_mouse_move(pos, Qt.MouseButton.NoButton),
                'move'
            )
            
            # 验证悬停区域是否更新
            self.assertEqual(self.interaction_handler.current_hover_zone, "test_zone",
                           "通过主窗口触发的悬停事件应该更新当前悬停区域")

if __name__ == '__main__':
    unittest.main() 