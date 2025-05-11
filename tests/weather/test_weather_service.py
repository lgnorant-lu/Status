"""
---------------------------------------------------------------
File name:                  test_weather_service.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                天气服务组件单元测试
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""
import unittest
from unittest.mock import patch, MagicMock, call, ANY
import logging
import time
import requests
import json

from status.weather.weather_service import WeatherService

# 禁用日志输出，避免测试时的干扰
logging.disable(logging.CRITICAL)

class TestWeatherService(unittest.TestCase):
    """天气服务组件测试类"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 基本配置，用于测试
        self.config = {
            'api_service': 'openweathermap',
            'api_key': 'test_api_key',
            'city': 'Beijing',
            'units': 'metric',
            'lang': 'zh_cn',
            'auto_refresh': False,
            'refresh_interval': 3600
        }
        
        # 样本天气数据 - OpenWeatherMap格式
        self.sample_owm_data = {
            'name': 'Beijing',
            'sys': {'country': 'CN'},
            'main': {
                'temp': 22.5,
                'feels_like': 23.0,
                'humidity': 60,
                'pressure': 1012
            },
            'weather': [
                {'id': 800, 'main': 'Clear', 'description': '晴天', 'icon': '01d'}
            ],
            'wind': {'speed': 5.2, 'deg': 180},
            'clouds': {'all': 10},
            'visibility': 10000,
            'dt': 1617500000
        }
        
        # 样本天气数据 - WeatherAPI格式
        self.sample_weatherapi_data = {
            'location': {
                'name': 'Beijing',
                'country': 'China'
            },
            'current': {
                'temp_c': 22.5,
                'temp_f': 72.5,
                'feelslike_c': 23.0,
                'humidity': 60,
                'pressure_mb': 1012,
                'condition': {
                    'text': '晴天',
                    'icon': '//cdn.weatherapi.com/weather/64x64/day/113.png',
                    'code': 1000
                },
                'wind_kph': 18.7,
                'wind_degree': 180,
                'cloud': 10,
                'vis_km': 10,
                'last_updated_epoch': 1617500000
            },
            'forecast': {
                'forecastday': [
                    {
                        'date': '2021-04-04',
                        'day': {
                            'maxtemp_c': 25.0,
                            'mintemp_c': 15.0,
                            'condition': {
                                'text': '晴天',
                                'icon': '//cdn.weatherapi.com/weather/64x64/day/113.png',
                                'code': 1000
                            }
                        },
                        'hour': []
                    }
                ]
            }
        }
        
        # 创建服务实例
        with patch('requests.get'):
            self.weather_service = WeatherService(self.config)
    
    def test_init(self):
        """测试初始化"""
        # 验证基本属性设置
        self.assertEqual(self.weather_service.api_service, 'openweathermap')
        self.assertEqual(self.weather_service.api_key, 'test_api_key')
        self.assertEqual(self.weather_service.city, 'Beijing')
        self.assertEqual(self.weather_service.units, 'metric')
        self.assertEqual(self.weather_service.lang, 'zh_cn')
        self.assertFalse(self.weather_service.auto_refresh)
        self.assertEqual(self.weather_service.refresh_interval, 3600)
        
        # 验证回调列表初始化
        self.assertEqual(len(self.weather_service.callbacks['on_weather_updated']), 0)
        self.assertEqual(len(self.weather_service.callbacks['on_weather_error']), 0)
        
        # 验证API配置
        self.assertIn('openweathermap', self.weather_service.SUPPORTED_APIS)
        self.assertIn('weatherapi', self.weather_service.SUPPORTED_APIS)
        
        # 测试默认配置
        with patch('requests.get'):
            service = WeatherService()
            self.assertEqual(service.api_service, 'openweathermap')
            self.assertEqual(service.api_key, '')
            self.assertEqual(service.city, 'Beijing')
            self.assertEqual(service.units, 'metric')
            self.assertTrue(service.auto_refresh)
    
    def test_start_stop(self):
        """测试启动和停止服务"""
        # 使用自动刷新
        self.weather_service.auto_refresh = True
        self.weather_service.refresh_interval = 0.1
        
        with patch.object(self.weather_service, 'update_weather') as mock_update:
            # 启动服务
            self.weather_service.start()
            self.assertTrue(self.weather_service.running)
            time.sleep(0.2)  # 等待刷新线程执行
            
            # 停止服务
            self.weather_service.stop()
            self.assertFalse(self.weather_service.running)
            
            # 验证更新至少被调用一次
            mock_update.assert_called()
    
    def test_manual_update(self):
        """测试手动更新天气数据"""
        with patch('requests.get') as mock_get:
            # 模拟成功响应
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = self.sample_owm_data
            mock_get.return_value = mock_response
            
            # 注册更新回调
            callback = MagicMock()
            self.weather_service.register_callback('on_weather_updated', callback)
            
            # 执行更新
            result = self.weather_service.update_weather()
            
            # 验证结果
            self.assertTrue(result)
            self.assertIsNotNone(self.weather_service.weather_data)
            
            # 验证回调被调用
            callback.assert_called_once()
    
    def test_update_with_error(self):
        """测试更新时出错"""
        with patch('requests.get', side_effect=requests.exceptions.RequestException("Test error")):
            # 注册错误回调
            error_callback = MagicMock()
            self.weather_service.register_callback('on_weather_error', error_callback)
            
            # 执行更新
            result = self.weather_service.update_weather()
            
            # 验证结果
            self.assertFalse(result)
            self.assertIsNone(self.weather_service.weather_data)
            
            # 验证错误回调被调用
            error_callback.assert_called_once()
    
    def test_parse_openweathermap_data(self):
        """测试解析OpenWeatherMap响应"""
        # 直接使用样本数据调用解析方法
        parsed_data = self.weather_service._parse_openweathermap_data(self.sample_owm_data)
        
        # 验证解析结果
        self.assertIn('city', parsed_data)
        self.assertIn('country', parsed_data)
        self.assertIn('temperature', parsed_data)
        
        # 验证当前天气数据
        self.assertEqual(parsed_data['city'], 'Beijing')
        self.assertEqual(parsed_data['country'], 'CN')
        self.assertEqual(parsed_data['temperature'], 22.5)
        self.assertEqual(parsed_data['feels_like'], 23.0)
        self.assertEqual(parsed_data['humidity'], 60)
        self.assertEqual(parsed_data['pressure'], 1012)
        self.assertEqual(parsed_data['description'], '晴天')
        self.assertEqual(parsed_data['wind_speed'], 5.2)
    
    def test_parse_weatherapi_data(self):
        """测试解析WeatherAPI响应"""
        # 设置为WeatherAPI服务
        self.weather_service.api_service = 'weatherapi'
        
        # 直接使用样本数据调用解析方法
        parsed_data = self.weather_service._parse_weatherapi_data(self.sample_weatherapi_data)
        
        # 验证解析结果
        self.assertIn('city', parsed_data)
        self.assertIn('country', parsed_data)
        self.assertIn('temperature', parsed_data)
        
        # 验证当前天气数据
        self.assertEqual(parsed_data['city'], 'Beijing')
        self.assertEqual(parsed_data['country'], 'China')
        self.assertEqual(parsed_data['temperature'], 22.5)
        self.assertEqual(parsed_data['feels_like'], 23.0)
        self.assertEqual(parsed_data['humidity'], 60)
        self.assertEqual(parsed_data['pressure'], 1012)
        self.assertEqual(parsed_data['description'], '晴天')
    
    def test_update_city(self):
        """测试更新城市"""
        # 设置服务为运行状态，才会触发update_weather调用
        self.weather_service.running = True
        
        # 更新城市
        with patch.object(self.weather_service, 'update_weather') as mock_update:
            self.weather_service.set_city('Shanghai')
            
            # 验证城市已更新并触发了数据更新
            self.assertEqual(self.weather_service.city, 'Shanghai')
            mock_update.assert_called_once()
    
    def test_update_api_key(self):
        """测试更新API密钥"""
        # 设置服务为运行状态，才会触发start/stop调用
        self.weather_service.running = True
        
        # 更新API密钥
        with patch.object(self.weather_service, 'stop') as mock_stop:
            with patch.object(self.weather_service, 'start') as mock_start:
                self.weather_service.set_api_key('new_api_key')
                
                # 验证API密钥已更新
                self.assertEqual(self.weather_service.api_key, 'new_api_key')
                
                # 验证停止和重启服务
                mock_stop.assert_called_once()
                mock_start.assert_called_once()
    
    def test_update_units(self):
        """测试更新单位"""
        # 设置服务为运行状态，才会触发update_weather调用
        self.weather_service.running = True
        
        # 更新单位
        with patch.object(self.weather_service, 'update_weather') as mock_update:
            self.weather_service.set_units('imperial')
            
            # 验证单位已更新并触发了数据更新
            self.assertEqual(self.weather_service.units, 'imperial')
            mock_update.assert_called_once()
    
    def test_update_refresh_interval(self):
        """测试更新刷新间隔"""
        # 更新刷新间隔
        self.weather_service.set_refresh_interval(1800)
        
        # 验证刷新间隔已更新
        self.assertEqual(self.weather_service.refresh_interval, 1800)
    
    def test_callbacks(self):
        """测试回调注册和移除"""
        # 创建回调函数
        update_callback = MagicMock()
        error_callback = MagicMock()
        
        # 注册回调
        self.weather_service.register_callback('on_weather_updated', update_callback)
        self.weather_service.register_callback('on_weather_error', error_callback)
        
        # 验证回调已注册
        self.assertEqual(len(self.weather_service.callbacks['on_weather_updated']), 1)
        self.assertEqual(len(self.weather_service.callbacks['on_weather_error']), 1)
        
        # 移除回调
        self.weather_service.unregister_callback('on_weather_updated', update_callback)
        self.weather_service.unregister_callback('on_weather_error', error_callback)
        
        # 验证回调已移除
        self.assertEqual(len(self.weather_service.callbacks['on_weather_updated']), 0)
        self.assertEqual(len(self.weather_service.callbacks['on_weather_error']), 0)
    
    def test_is_running(self):
        """测试检查服务是否运行"""
        # 初始状态为未运行
        self.assertFalse(self.weather_service.is_running())
        
        # 设置为运行状态
        self.weather_service.running = True
        self.assertTrue(self.weather_service.is_running())

if __name__ == '__main__':
    unittest.main() 