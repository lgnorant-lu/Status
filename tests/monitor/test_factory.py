"""
---------------------------------------------------------------
File name:                  test_factory.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                监控系统工厂测试
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
                            2025/04/07: 更新以匹配当前factory实现;
----
"""

import unittest
from unittest.mock import patch, MagicMock, call, ANY
import logging

from status.monitor.factory import (
    create_monitor_system, 
    create_custom_monitor_system,
    create_minimal_monitor_system,
    create_debug_monitor_system
)
from status.monitor.monitor_manager import MonitorManager
from status.monitor.data_collector import SystemDataCollector
from status.monitor.data_processor import DataProcessor
from status.monitor.visualization import VisualMapper
from status.monitor.scene_manager import SceneManager


class TestFactory(unittest.TestCase):
    """测试监控系统工厂"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 配置日志
        logging.basicConfig(level=logging.CRITICAL)
            
    @patch('status.monitor.factory.MonitorManager')
    @patch('status.monitor.factory.SceneManager')
    @patch('status.monitor.factory.VisualMapper')
    @patch('status.monitor.factory.DataProcessor')
    @patch('status.monitor.factory.SystemDataCollector')
    def test_create_monitor_system_basic(self, 
                                       mock_collector_class, 
                                       mock_processor_class, 
                                       mock_mapper_class, 
                                       mock_scene_class, 
                                       mock_manager_class):
        """测试基本监控系统创建功能"""
        # 设置模拟对象
        mock_collector = MagicMock()
        mock_processor = MagicMock()
        mock_mapper = MagicMock()
        mock_scene = MagicMock()
        mock_manager = MagicMock()
        
        mock_collector_class.return_value = mock_collector
        mock_processor_class.return_value = mock_processor
        mock_mapper_class.return_value = mock_mapper
        mock_scene_class.return_value = mock_scene
        mock_manager_class.return_value = mock_manager
        
        # 调用工厂函数
        result = create_monitor_system()
        
        # 验证结果
        self.assertEqual(result, mock_manager)
        
        # 验证组件创建
        mock_collector_class.assert_called_once_with({})
        mock_processor_class.assert_called_once_with({})
        mock_mapper_class.assert_called_once_with({})
        mock_scene_class.assert_called_once_with({})
        
        # 验证创建了默认场景
        mock_scene.create_default_scenes.assert_called_once()
        
        # 验证监控管理器创建
        mock_manager_class.assert_called_once_with(
            data_collector=mock_collector,
            data_processor=mock_processor,
            visual_mapper=mock_mapper,
            scene_manager=mock_scene,
            config={}
        )
        
        # 验证没有自动启动
        mock_manager.start.assert_not_called()
        
    @patch('status.monitor.factory.MonitorManager')
    @patch('status.monitor.factory.SceneManager')
    @patch('status.monitor.factory.VisualMapper')
    @patch('status.monitor.factory.DataProcessor')
    @patch('status.monitor.factory.SystemDataCollector')
    def test_create_monitor_system_with_config(self, 
                                             mock_collector_class, 
                                             mock_processor_class, 
                                             mock_mapper_class, 
                                             mock_scene_class, 
                                             mock_manager_class):
        """测试带配置的监控系统创建"""
        # 设置模拟对象
        mock_collector = MagicMock()
        mock_processor = MagicMock()
        mock_mapper = MagicMock()
        mock_scene = MagicMock()
        mock_manager = MagicMock()
        
        mock_collector_class.return_value = mock_collector
        mock_processor_class.return_value = mock_processor
        mock_mapper_class.return_value = mock_mapper
        mock_scene_class.return_value = mock_scene
        mock_manager_class.return_value = mock_manager
        
        # 创建配置
        config = {
            "create_default_scenes": True,
            "auto_start": True,
            "data_collector": {
                "advanced_metrics": True
            },
            "data_processor": {
                "enable_trends": True
            },
            "visual_mapper": {
                "color_scheme": "dark"
            },
            "scene_manager": {
                "default_scene": "overview"
            },
            "monitor_manager": {
                "update_interval": 2.0
            }
        }
        
        # 调用工厂函数
        result = create_monitor_system(config)
        
        # 验证结果
        self.assertEqual(result, mock_manager)
        
        # 验证组件创建和配置传递
        mock_collector_class.assert_called_once_with(config["data_collector"])
        mock_processor_class.assert_called_once_with(config["data_processor"])
        mock_mapper_class.assert_called_once_with(config["visual_mapper"])
        mock_scene_class.assert_called_once_with(config["scene_manager"])
        
        # 验证监控管理器创建
        mock_manager_class.assert_called_once_with(
            data_collector=mock_collector,
            data_processor=mock_processor,
            visual_mapper=mock_mapper,
            scene_manager=mock_scene,
            config=config["monitor_manager"]
        )
        
        # 验证自动启动
        mock_manager.start.assert_called_once()
        
    @patch('status.monitor.factory.MonitorManager')
    @patch('status.monitor.factory.SceneManager')
    @patch('status.monitor.factory.VisualMapper')
    @patch('status.monitor.factory.DataProcessor')
    @patch('status.monitor.factory.SystemDataCollector')
    def test_create_monitor_system_with_partial_config(self, 
                                                    mock_collector_class, 
                                                    mock_processor_class, 
                                                    mock_mapper_class, 
                                                    mock_scene_class, 
                                                    mock_manager_class):
        """测试部分配置的监控系统创建"""
        # 设置模拟对象
        mock_collector = MagicMock()
        mock_processor = MagicMock()
        mock_mapper = MagicMock()
        mock_scene = MagicMock()
        mock_manager = MagicMock()
        
        mock_collector_class.return_value = mock_collector
        mock_processor_class.return_value = mock_processor
        mock_mapper_class.return_value = mock_mapper
        mock_scene_class.return_value = mock_scene
        mock_manager_class.return_value = mock_manager
        
        # 创建部分配置
        config = {
            "create_default_scenes": False,
            "auto_start": False,
            "data_collector": {
                "advanced_metrics": False
            }
        }
        
        # 调用工厂函数
        result = create_monitor_system(config)
        
        # 验证结果
        self.assertEqual(result, mock_manager)
        
        # 验证只有指定的配置被使用
        mock_collector_class.assert_called_once_with(config["data_collector"])
        mock_processor_class.assert_called_once_with({})
        mock_mapper_class.assert_called_once_with({})
        mock_scene_class.assert_called_once_with({})
        
        # 验证没有创建默认场景
        mock_scene.create_default_scenes.assert_not_called()
        
        # 验证没有自动启动
        mock_manager.start.assert_not_called()
        
    @patch('status.monitor.factory.MonitorManager')
    def test_create_custom_monitor_system(self, mock_manager_class):
        """测试创建自定义监控系统"""
        # 创建模拟组件
        mock_collector = MagicMock(spec=SystemDataCollector)
        mock_processor = MagicMock(spec=DataProcessor)
        mock_mapper = MagicMock(spec=VisualMapper)
        mock_scene = MagicMock(spec=SceneManager)
        mock_manager = MagicMock(spec=MonitorManager)
        
        # 设置返回值
        mock_manager_class.return_value = mock_manager
        
        # 设置自定义配置
        custom_config = {
            "data_collector": {"metrics": ["cpu", "memory", "network"]},
            "scene_manager": {"enable_caching": True}
        }
        
        # 调用工厂函数
        result = create_custom_monitor_system(
            data_collector=mock_collector,
            data_processor=mock_processor,
            visual_mapper=mock_mapper,
            scene_manager=mock_scene,
            config=custom_config,
            auto_start=True
        )
        
        # 验证结果
        self.assertEqual(result, mock_manager)
        
        # 验证使用了传入的组件和配置
        mock_manager_class.assert_called_once_with(
            data_collector=mock_collector,
            data_processor=mock_processor,
            visual_mapper=mock_mapper,
            scene_manager=mock_scene,
            config=custom_config
        )
        
        # 验证监控系统已启动
        mock_manager.start.assert_called_once()
        
    @patch('status.monitor.factory.MonitorManager')
    @patch('status.monitor.factory.SceneManager')
    @patch('status.monitor.factory.VisualMapper')
    @patch('status.monitor.factory.DataProcessor')
    @patch('status.monitor.factory.SystemDataCollector')
    def test_create_minimal_monitor_system(self, 
                                         mock_collector_class, 
                                         mock_processor_class, 
                                         mock_mapper_class, 
                                         mock_scene_class, 
                                         mock_manager_class):
        """测试创建最小化监控系统"""
        # 设置模拟对象
        mock_collector = MagicMock()
        mock_processor = MagicMock()
        mock_mapper = MagicMock()
        mock_scene = MagicMock()
        mock_manager = MagicMock()
        
        mock_collector_class.return_value = mock_collector
        mock_processor_class.return_value = mock_processor
        mock_mapper_class.return_value = mock_mapper
        mock_scene_class.return_value = mock_scene
        mock_manager_class.return_value = mock_manager
        
        # 调用工厂函数
        result = create_minimal_monitor_system()
        
        # 验证结果
        self.assertEqual(result, mock_manager)
        
        # 验证使用了最小化配置
        mock_collector_class.assert_called_once()
        mock_processor_class.assert_called_once()
        mock_mapper_class.assert_called_once()
        mock_scene_class.assert_called_once()
        
        # 验证创建了特定场景
        mock_scene.create_scene.assert_called_once_with("minimal", ANY)
        mock_scene.set_active_scene.assert_called_once_with("minimal")
        
        # 验证启动了系统
        mock_manager.start.assert_not_called()
        
    @patch('status.monitor.factory.create_monitor_system')
    def test_create_debug_monitor_system(self, mock_create_monitor):
        """测试创建调试监控系统"""
        # 创建模拟对象
        mock_manager = MagicMock(spec=MonitorManager)
        mock_create_monitor.return_value = mock_manager
        
        # 调用工厂函数
        result = create_debug_monitor_system()
        
        # 验证结果
        self.assertEqual(result, mock_manager)
        
        # 验证基础监控系统被创建
        mock_create_monitor.assert_called_once_with(None)
        
        # 验证注册了回调函数
        mock_manager.register_update_callback.assert_called_once()


if __name__ == '__main__':
    unittest.main() 