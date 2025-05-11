"""
---------------------------------------------------------------
File name:                  test_factory.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                天气系统工厂单元测试
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""
import unittest
from unittest.mock import patch, MagicMock, call
import logging

from status.weather.factory import (
    create_weather_system,
    create_default_weather_system,
    create_custom_weather_system,
    create_lightweight_weather_system,
    create_detailed_weather_system,
    create_dark_theme_weather_system
)
from status.weather.weather_manager import WeatherManager

# 禁用日志输出，避免测试时的干扰
logging.disable(logging.CRITICAL)

class TestWeatherFactory(unittest.TestCase):
    """天气系统工厂测试类"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 准备补丁
        self.manager_patch = patch('status.weather.factory.WeatherManager')
        self.logger_patch = patch('status.weather.factory.logging.getLogger')
        
        # 启动补丁
        self.mock_manager_class = self.manager_patch.start()
        self.mock_logger = self.logger_patch.start()
        
        # 创建模拟管理器实例
        self.mock_manager = MagicMock(spec=WeatherManager)
        
        # 设置模拟管理器类返回模拟实例
        self.mock_manager_class.return_value = self.mock_manager
    
    def tearDown(self):
        """测试后的清理工作"""
        # 停止所有补丁
        self.manager_patch.stop()
        self.logger_patch.stop()
    
    def test_create_weather_system(self):
        """测试创建天气系统"""
        # 测试默认配置
        manager = create_weather_system()
        
        # 验证管理器创建
        self.mock_manager_class.assert_called_once_with({})
        
        # 验证管理器启动
        self.mock_manager.start.assert_called_once()
        
        # 验证返回值
        self.assertEqual(manager, self.mock_manager)
        
        # 测试提供配置
        self.mock_manager_class.reset_mock()
        self.mock_manager.reset_mock()
        
        test_config = {'service': {'city': 'TestCity'}, 'auto_start': False}
        manager = create_weather_system(test_config)
        
        # 验证配置传递
        self.mock_manager_class.assert_called_once_with(test_config)
        
        # 验证不自动启动
        self.mock_manager.start.assert_not_called()
    
    def test_create_default_weather_system(self):
        """测试创建默认天气系统"""
        # 测试默认参数
        with patch('status.weather.factory.create_weather_system') as mock_create:
            manager = create_default_weather_system()
            
            # 验证基础创建函数调用
            mock_create.assert_called_once()
            args, kwargs = mock_create.call_args
            config = args[0]
            
            # 验证配置内容
            self.assertEqual(config['service']['api_service'], 'openweathermap')
            self.assertEqual(config['service']['city'], 'Beijing')
            self.assertEqual(config['service']['units'], 'metric')
            self.assertTrue(config['service']['auto_refresh'])
            self.assertEqual(config['display']['display_style'], 'compact')
            self.assertEqual(config['display']['color_scheme'], 'default')
            self.assertTrue(config['auto_start'])
        
        # 测试自定义参数
        with patch('status.weather.factory.create_weather_system') as mock_create:
            manager = create_default_weather_system(
                city='Shanghai',
                api_key='custom_key',
                api_service='weatherapi',
                units='imperial',
                display_style='detailed',
                color_scheme='dark',
                auto_refresh=False,
                auto_start=False
            )
            
            # 验证配置内容
            args, kwargs = mock_create.call_args
            config = args[0]
            
            self.assertEqual(config['service']['api_service'], 'weatherapi')
            self.assertEqual(config['service']['api_key'], 'custom_key')
            self.assertEqual(config['service']['city'], 'Shanghai')
            self.assertEqual(config['service']['units'], 'imperial')
            self.assertFalse(config['service']['auto_refresh'])
            self.assertEqual(config['display']['display_style'], 'detailed')
            self.assertEqual(config['display']['color_scheme'], 'dark')
            self.assertFalse(config['auto_start'])
    
    def test_create_custom_weather_system(self):
        """测试创建自定义天气系统"""
        # 测试自定义配置
        service_config = {'api_service': 'weatherapi', 'city': 'TestCity'}
        display_config = {'display_style': 'detailed', 'color_scheme': 'dark'}
        
        with patch('status.weather.factory.create_weather_system') as mock_create:
            manager = create_custom_weather_system(service_config, display_config, False)
            
            # 验证基础创建函数调用
            mock_create.assert_called_once()
            args, kwargs = mock_create.call_args
            config = args[0]
            
            # 验证配置内容
            self.assertEqual(config['service'], service_config)
            self.assertEqual(config['display'], display_config)
            self.assertFalse(config['auto_start'])
        
        # 测试空配置
        with patch('status.weather.factory.create_weather_system') as mock_create:
            manager = create_custom_weather_system()
            
            # 验证配置内容
            args, kwargs = mock_create.call_args
            config = args[0]
            
            self.assertEqual(config['service'], {})
            self.assertEqual(config['display'], {})
            self.assertTrue(config['auto_start'])
    
    def test_create_lightweight_weather_system(self):
        """测试创建轻量级天气系统"""
        with patch('status.weather.factory.create_weather_system') as mock_create:
            manager = create_lightweight_weather_system(
                city='TestCity',
                api_key='test_key',
                auto_refresh=True
            )
            
            # 验证基础创建函数调用
            mock_create.assert_called_once()
            args, kwargs = mock_create.call_args
            config = args[0]
            
            # 验证配置内容
            self.assertEqual(config['service']['api_service'], 'openweathermap')
            self.assertEqual(config['service']['api_key'], 'test_key')
            self.assertEqual(config['service']['city'], 'TestCity')
            self.assertTrue(config['service']['auto_refresh'])
            self.assertEqual(config['service']['refresh_interval'], 7200)  # 2小时
            self.assertFalse(config['display']['use_animations'])  # 禁用动画
            self.assertTrue(config['auto_start'])
    
    def test_create_detailed_weather_system(self):
        """测试创建详细天气系统"""
        with patch('status.weather.factory.create_weather_system') as mock_create:
            manager = create_detailed_weather_system(
                city='TestCity',
                api_key='test_key',
                api_service='weatherapi',
                auto_refresh=True
            )
            
            # 验证基础创建函数调用
            mock_create.assert_called_once()
            args, kwargs = mock_create.call_args
            config = args[0]
            
            # 验证配置内容
            self.assertEqual(config['service']['api_service'], 'weatherapi')
            self.assertEqual(config['service']['api_key'], 'test_key')
            self.assertEqual(config['service']['city'], 'TestCity')
            self.assertTrue(config['service']['auto_refresh'])
            self.assertEqual(config['service']['refresh_interval'], 1800)  # 30分钟
            self.assertEqual(config['display']['display_style'], 'detailed')
            self.assertTrue(config['display']['show_forecast'])
            self.assertTrue(config['auto_start'])
    
    def test_create_dark_theme_weather_system(self):
        """测试创建深色主题天气系统"""
        with patch('status.weather.factory.create_weather_system') as mock_create:
            manager = create_dark_theme_weather_system(
                city='TestCity',
                api_key='test_key',
                auto_refresh=True
            )
            
            # 验证基础创建函数调用
            mock_create.assert_called_once()
            args, kwargs = mock_create.call_args
            config = args[0]
            
            # 验证配置内容
            self.assertEqual(config['service']['api_service'], 'openweathermap')
            self.assertEqual(config['service']['api_key'], 'test_key')
            self.assertEqual(config['service']['city'], 'TestCity')
            self.assertTrue(config['service']['auto_refresh'])
            self.assertEqual(config['display']['color_scheme'], 'dark')
            self.assertTrue(config['auto_start'])

if __name__ == '__main__':
    unittest.main() 