"""
---------------------------------------------------------------
File name:                  test_stats_panel_in_app.py
Author:                     Ignorant-lu
Date created:               2025/05/13  
Description:                测试StatsPanel在主应用中的集成表现
----------------------------------------------------------------

Changed history:            
                            2025/05/13: 初始创建;
----
"""

import sys
import os
import unittest
import logging
import time
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

# 将项目根目录添加到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# 导入被测组件
from status.main import StatusPet
from status.ui.stats_panel import StatsPanel

# 配置日志
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("TestStatsPanelInApp")

class TestStatsPanelInApp(unittest.TestCase):
    """测试StatsPanel在主应用中的集成行为"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化，创建QApplication实例"""
        # 创建QApplication（如果不存在）
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """每个测试前的准备工作"""
        # 创建StatusPet实例但不运行事件循环
        self.pet_app = StatusPet()
        # 初始化应用但不进入事件循环
        self.pet_app.initialize()
        
    def tearDown(self):
        """每个测试后的清理工作"""
        # 清理资源
        if hasattr(self, 'pet_app'):
            if hasattr(self.pet_app, 'exit_app'):
                self.pet_app.exit_app()
            self.pet_app = None
    
    def test_stats_panel_creation(self):
        """测试StatsPanel是否正确创建"""
        # 验证StatsPanel已在应用中创建
        self.assertIsNotNone(self.pet_app.stats_panel)
        self.assertIsInstance(self.pet_app.stats_panel, StatsPanel)
        
        # 默认应该是隐藏的
        self.assertFalse(self.pet_app.stats_panel.isVisible())
    
    def test_stats_panel_show_hide(self):
        """测试通过托盘菜单控制StatsPanel的显示和隐藏"""
        # 先确保主窗口显示
        if not self.pet_app.main_window.isVisible():
            self.pet_app.main_window.show()
            QApplication.processEvents()
        
        # 确保StatsPanel初始隐藏
        self.assertFalse(self.pet_app.stats_panel.isVisible())
        
        # 模拟托盘菜单的显示面板操作
        self.pet_app._handle_toggle_stats_panel(True)
        QApplication.processEvents()
        
        # 确保StatsPanel现在可见
        self.assertTrue(self.pet_app.stats_panel.isVisible(), "StatsPanel应该在显示操作后可见")
        
        # 检查面板位置是否合理
        self.assertIsNotNone(self.pet_app.stats_panel.pos())
        
        # 模拟托盘菜单的隐藏面板操作
        self.pet_app._handle_toggle_stats_panel(False)
        QApplication.processEvents()
        
        # 确保StatsPanel现在不可见
        self.assertFalse(self.pet_app.stats_panel.isVisible(), "StatsPanel应该在隐藏操作后不可见")
    
    def test_window_position_update(self):
        """测试当主窗口移动时StatsPanel位置是否正确更新"""
        # 先确保主窗口显示
        if not self.pet_app.main_window.isVisible():
            self.pet_app.main_window.show()
            QApplication.processEvents()
        
        # 显示StatsPanel
        self.pet_app._handle_toggle_stats_panel(True)
        QApplication.processEvents()
        
        # 记录初始位置
        initial_pos = self.pet_app.stats_panel.pos()
        
        # 移动主窗口
        new_pos = self.pet_app.main_window.pos()
        new_pos.setX(new_pos.x() + 100)
        new_pos.setY(new_pos.y() + 100)
        self.pet_app.main_window.move(new_pos)
        
        # 使用定时器等待一小段时间，让事件系统处理位置变化
        timer = QTimer()
        timer.singleShot(500, lambda: None)
        timer.start()
        QApplication.processEvents()
        
        # 确保StatsPanel位置已更新
        self.assertNotEqual(initial_pos, self.pet_app.stats_panel.pos(), 
                           "StatsPanel位置应该在主窗口移动后更新")
        
        # 隐藏StatsPanel
        self.pet_app._handle_toggle_stats_panel(False)

if __name__ == "__main__":
    unittest.main() 