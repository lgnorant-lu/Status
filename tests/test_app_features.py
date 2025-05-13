"""
---------------------------------------------------------------
File name:                  test_app_features.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                测试 StatusPet 应用层面的特性集成
----------------------------------------------------------------
"""

import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入Qt以确保QApplication初始化
from PySide6.QtWidgets import QApplication
app = QApplication.instance() if QApplication.instance() else QApplication(sys.argv)

# --- 模拟 Qt 类 --- 
# 不再模拟整个 QtCore 或 QtWidgets，只模拟测试中直接交互或实例化的类
# 假设 StatusPet 会实例化 QApplication, MainPetWindow, SystemTrayManager, StatsPanel, PetStateMachine, Animation
MockQApplication = MagicMock()
MockQObject = MagicMock()
MockQWidget = MagicMock()
# MockQPoint = MagicMock(return_value=(0, 0)) # 移除或注释掉这行 - 它导致了混淆
# MockQSize = MagicMock(return_value=(64, 64)) # 移除或注释掉这行 - 它导致了类似的问题
MockSignal = MagicMock()
MockQScreen = MagicMock()
# MockQRect = MagicMock(return_value=(0, 0, 1920, 1080)) # 移除或注释掉这行 - 它导致了类似的问题

# --- 模拟项目内部 UI 和核心类 --- 
MockMainPetWindow = MagicMock()
MockSystemTrayManager = MagicMock()
MockStatsPanel = MagicMock()
MockPetStateMachine = MagicMock() 
MockAnimation = MagicMock()

# 在应用 Patch 之前导入被测试的类
from status.main import StatusPet 

# 移除类级别的 Patch 装饰器
class TestAppFeatures(unittest.TestCase):
    """测试应用级特性交互"""

    def setUp(self):
        """设置测试环境，使用 patch 上下文管理器"""
        self.patchers = []
        
        patcher = patch('status.main.QApplication', MockQApplication)
        self.mock_app_cls_ref = patcher.start() # 保存对模拟类的引用，以防需要
        self.patchers.append(patcher)
        # 关键更改：模拟 QApplication.instance() 返回一个模拟的 QApplication 实例
        self.mock_qapp_instance = MagicMock() # 移除 spec
        MockQApplication.instance.return_value = self.mock_qapp_instance
        MockQApplication.primaryScreen.return_value = MockQScreen # 保持屏幕模拟
        
        # 配置 screen_geometry (QRect) 对象
        mock_rect_obj = MagicMock()
        mock_rect_obj.right.return_value = 1920
        mock_rect_obj.bottom.return_value = 1080
        mock_rect_obj.top.return_value = 0
        mock_rect_obj.left.return_value = 0
        # 使用这个模拟对象
        MockQScreen.availableGeometry.return_value = mock_rect_obj
        
        # Patch MainPetWindow
        patcher = patch('status.main.MainPetWindow', MockMainPetWindow)
        self.mock_window_cls = patcher.start()
        self.patchers.append(patcher)
        
        # Patch SystemTrayManager
        patcher = patch('status.main.SystemTrayManager', MockSystemTrayManager)
        self.mock_tray_cls = patcher.start()
        self.patchers.append(patcher)
        
        # Patch StatsPanel
        patcher = patch('status.main.StatsPanel', MockStatsPanel)
        self.mock_stats_panel_cls = patcher.start()
        self.patchers.append(patcher)
        
        # Patch PetStateMachine
        patcher = patch('status.main.PetStateMachine', MockPetStateMachine)
        self.mock_state_machine_cls = patcher.start()
        self.patchers.append(patcher)
        
        # Patch Animation
        patcher = patch('status.main.Animation', MockAnimation)
        self.mock_animation_cls = patcher.start()
        self.patchers.append(patcher)
        
        # Patch publish_stats
        patcher = patch('status.main.publish_stats')
        self.mock_publish_stats = patcher.start()
        self.patchers.append(patcher)

        self.status_pet = StatusPet()
        self.status_pet.initialize()
        
        self.mock_main_window = self.status_pet.main_window 
        self.mock_system_tray = self.status_pet.system_tray
        self.mock_stats_panel = self.status_pet.stats_panel
        self.mock_state_machine = self.status_pet.state_machine

        if not isinstance(self.mock_main_window, MagicMock):
            self.mock_main_window = self.mock_window_cls()
            self.status_pet.main_window = self.mock_main_window
        if not isinstance(self.mock_stats_panel, MagicMock):
            self.mock_stats_panel = self.mock_stats_panel_cls()
            self.status_pet.stats_panel = self.mock_stats_panel
            
        if self.mock_main_window: # 再次检查，因为上面可能重新赋值
            # self.mock_main_window.pos.return_value = MockQPoint(0,0) # 旧的错误代码
            # 新代码：创建并配置模拟的 QPoint 对象
            mock_pos_obj = MagicMock()
            mock_pos_obj.x.return_value = 0 
            mock_pos_obj.y.return_value = 0
            self.mock_main_window.pos.return_value = mock_pos_obj # 让 pos() 返回这个配置好的 mock
            
            # self.mock_main_window.size.return_value = MockQSize(64,64) # 旧的错误代码
            # 新代码：创建并配置模拟的 QSize 对象
            mock_size_obj = MagicMock()
            mock_size_obj.width.return_value = 64
            mock_size_obj.height.return_value = 64
            self.mock_main_window.size.return_value = mock_size_obj
            
        if self.mock_stats_panel:
            # self.mock_stats_panel.sizeHint.return_value = MockQSize(100,50) # 旧的错误代码
            # 新代码：创建并配置模拟的 QSize 对象
            mock_sizehint_obj = MagicMock()
            mock_sizehint_obj.width.return_value = 100
            mock_sizehint_obj.height.return_value = 50
            self.mock_stats_panel.sizeHint.return_value = mock_sizehint_obj

    def tearDown(self):
        """停止所有 patchers"""
        for patcher in self.patchers:
            patcher.stop()

    # def test_toggle_interaction(self):
    #     """测试切换交互状态是否正确调用窗口方法 (暂时注释)"""
    #     # ... (保持注释) ...

    # --- StatsPanel 测试 --- 
    def test_toggle_stats_panel_show(self):
        """测试通过托盘请求显示统计面板"""
        if not self.mock_stats_panel or not self.mock_main_window:
             self.skipTest("Mock objects not created correctly in setUp")
        
        # 重置 mock 对象的调用计数
        self.mock_stats_panel.show_panel.reset_mock()
        self.mock_stats_panel.hide_panel.reset_mock()
             
        # 直接调用处理函数，模拟信号触发
        self.status_pet._handle_toggle_stats_panel(True)
        
        # 验证 StatsPanel 的 show_panel 被调用
        self.mock_stats_panel.show_panel.assert_called_once()
        call_args = self.mock_stats_panel.show_panel.call_args
        self.assertEqual(len(call_args[0]), 1) 
        self.assertIsNotNone(call_args[0][0]) 
        
        self.mock_stats_panel.hide_panel.assert_not_called()

    def test_toggle_stats_panel_hide(self):
        """测试通过托盘请求隐藏统计面板"""
        if not self.mock_stats_panel or not self.mock_main_window:
             self.skipTest("Mock objects not created correctly in setUp")
        
        # 重置 mock 对象的调用计数
        self.mock_stats_panel.show_panel.reset_mock()
        self.mock_stats_panel.hide_panel.reset_mock()
             
        # 直接调用处理函数，模拟信号触发隐藏
        self.status_pet._handle_toggle_stats_panel(False)
        
        # 验证 StatsPanel 的 hide_panel 被调用
        self.mock_stats_panel.hide_panel.assert_called_once()
        self.mock_stats_panel.show_panel.assert_not_called()

if __name__ == '__main__':
    unittest.main()