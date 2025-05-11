"""
---------------------------------------------------------------
File name:                  test_weather_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                天气管理器单元测试
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""
import unittest
from unittest.mock import patch, MagicMock, call
import time
import logging
import threading

from status.weather.weather_manager import WeatherManager
from status.weather.weather_service import WeatherService
from status.weather.weather_display import WeatherDisplay

# 禁用日志输出，避免测试时的干扰
logging.disable(logging.CRITICAL)

class TestWeatherManager(unittest.TestCase):
    """天气管理器测试类"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 创建测试配置
        self.test_config = {
            'service': {
                'api_service': 'openweathermap',
                'api_key': 'test_api_key',
                'city': 'TestCity',
                'units': 'metric',
                'auto_refresh': False
            },
            'display': {
                'display_style': 'compact',
                'color_scheme': 'default',
                'use_icons': True
            }
        }
        
        # 准备补丁
        self.service_patch = patch('status.weather.weather_manager.WeatherService')
        self.display_patch = patch('status.weather.weather_manager.WeatherDisplay')
        
        # 启动补丁
        self.mock_service_class = self.service_patch.start()
        self.mock_display_class = self.display_patch.start()
        
        # 创建模拟服务和显示实例
        self.mock_service = MagicMock(spec=WeatherService)
        self.mock_display = MagicMock(spec=WeatherDisplay)
        
        # 设置模拟类返回模拟实例
        self.mock_service_class.return_value = self.mock_service
        self.mock_display_class.return_value = self.mock_display
        
        # 创建天气管理器实例
        self.weather_manager = WeatherManager(self.test_config)
        
        # 准备模拟的天气数据
        self.mock_weather_data = {
            'city': 'TestCity',
            'temperature': 25.5,
            'description': '晴朗'
        }
    
    def tearDown(self):
        """测试后的清理工作"""
        # 停止所有补丁
        self.service_patch.stop()
        self.display_patch.stop()
    
    def test_init(self):
        """测试初始化配置"""
        # 验证服务和显示实例创建
        self.mock_service_class.assert_called_once_with(self.test_config['service'])
        self.mock_display_class.assert_called_once_with(self.test_config['display'])
        
        # 验证回调注册
        self.mock_service.register_callback.assert_any_call('on_weather_updated', self.weather_manager._on_weather_updated)
        self.mock_service.register_callback.assert_any_call('on_weather_error', self.weather_manager._on_weather_error)
        
        # 验证初始状态
        self.assertFalse(self.weather_manager.running)
        self.assertIsNotNone(self.weather_manager.lock)
        self.assertIsNotNone(self.weather_manager.callbacks)
    
    def test_on_weather_updated(self):
        """测试天气更新回调"""
        # 创建回调数据
        callback_data = {'weather': self.mock_weather_data}
        
        # 添加模拟回调
        mock_callback = MagicMock()
        self.weather_manager.callbacks['on_weather_updated'].append(mock_callback)
        
        # 调用回调
        self.weather_manager._on_weather_updated(callback_data)
        
        # 验证显示更新
        self.mock_display.update_display.assert_called_once_with(self.mock_weather_data)
        
        # 验证回调触发
        mock_callback.assert_called_once()
        args, kwargs = mock_callback.call_args
        self.assertEqual(args[0]['weather'], self.mock_weather_data)
    
    def test_on_weather_error(self):
        """测试天气错误回调"""
        # 创建错误数据
        error_data = {'error': 'Test error'}
        
        # 添加模拟回调
        mock_callback = MagicMock()
        self.weather_manager.callbacks['on_error'].append(mock_callback)
        
        # 调用回调
        self.weather_manager._on_weather_error(error_data)
        
        # 验证回调触发
        mock_callback.assert_called_once()
        args, kwargs = mock_callback.call_args
        self.assertEqual(args[0]['error'], 'Test error')
        self.assertEqual(args[0]['source'], 'weather_service')
    
    def test_start(self):
        """测试启动管理器"""
        # 设置服务启动返回值
        self.mock_service.start.return_value = True
        
        # 启动管理器
        result = self.weather_manager.start()
        
        # 验证结果
        self.assertTrue(result)
        self.assertTrue(self.weather_manager.running)
        
        # 验证服务启动
        self.mock_service.start.assert_called_once()
        
        # 测试已运行情况
        self.mock_service.reset_mock()
        result = self.weather_manager.start()
        self.assertFalse(result)
        self.mock_service.start.assert_not_called()
        
        # 测试服务启动失败
        self.weather_manager.running = False
        self.mock_service.start.return_value = False
        
        # 添加模拟回调
        mock_callback = MagicMock()
        self.weather_manager.callbacks['on_error'].append(mock_callback)
        
        result = self.weather_manager.start()
        self.assertFalse(result)
        self.assertFalse(self.weather_manager.running)
        
        # 验证错误回调
        mock_callback.assert_called_once()
        args, kwargs = mock_callback.call_args
        self.assertIn('error', args[0])
        self.assertEqual(args[0]['source'], 'weather_manager')
    
    def test_stop(self):
        """测试停止管理器"""
        # 设置运行状态
        self.weather_manager.running = True
        
        # 设置服务停止返回值
        self.mock_service.stop.return_value = True
        
        # 停止管理器
        result = self.weather_manager.stop()
        
        # 验证结果
        self.assertTrue(result)
        self.assertFalse(self.weather_manager.running)
        
        # 验证服务停止
        self.mock_service.stop.assert_called_once()
        
        # 测试未运行情况
        self.mock_service.reset_mock()
        result = self.weather_manager.stop()
        self.assertFalse(result)
        self.mock_service.stop.assert_not_called()
        
        # 测试服务停止警告
        self.weather_manager.running = True
        self.mock_service.stop.return_value = False
        
        result = self.weather_manager.stop()
        self.assertTrue(result)  # 虽有警告，但停止成功
        self.assertFalse(self.weather_manager.running)
    
    def test_is_running(self):
        """测试运行状态检查"""
        self.weather_manager.running = False
        self.assertFalse(self.weather_manager.is_running())
        
        self.weather_manager.running = True
        self.assertTrue(self.weather_manager.is_running())
    
    def test_update_weather(self):
        """测试手动更新天气"""
        # 设置运行状态
        self.weather_manager.running = True
        
        # 设置服务更新返回值
        self.mock_service.update_weather.return_value = True
        
        # 更新天气
        result = self.weather_manager.update_weather()
        
        # 验证结果
        self.assertTrue(result)
        
        # 验证服务调用
        self.mock_service.update_weather.assert_called_once()
        
        # 测试未运行情况
        self.mock_service.reset_mock()
        self.weather_manager.running = False
        
        result = self.weather_manager.update_weather()
        self.assertFalse(result)
        self.mock_service.update_weather.assert_not_called()
    
    def test_get_weather(self):
        """测试获取天气数据"""
        # 设置服务返回值
        self.mock_service.get_weather.return_value = self.mock_weather_data
        
        # 获取天气数据
        result = self.weather_manager.get_weather()
        
        # 验证结果
        self.assertEqual(result, self.mock_weather_data)
        
        # 验证服务调用
        self.mock_service.get_weather.assert_called_once()
    
    def test_get_formatted_weather(self):
        """测试获取格式化天气数据"""
        # 设置显示返回值
        mock_formatted = {'location': 'TestCity', 'temperature': '25.5°C'}
        self.mock_display.get_formatted_weather.return_value = mock_formatted
        
        # 获取格式化天气
        result = self.weather_manager.get_formatted_weather()
        
        # 验证结果
        self.assertEqual(result, mock_formatted)
        
        # 验证显示调用
        self.mock_display.get_formatted_weather.assert_called_once()
    
    def test_get_weather_summary(self):
        """测试获取天气摘要"""
        # 设置显示返回值
        self.mock_display.get_weather_summary.return_value = 'TestCity: 25.5°C, 晴朗'
        
        # 获取摘要
        result = self.weather_manager.get_weather_summary()
        
        # 验证结果
        self.assertEqual(result, 'TestCity: 25.5°C, 晴朗')
        
        # 验证显示调用
        self.mock_display.get_weather_summary.assert_called_once()
    
    def test_render_widget(self):
        """测试渲染小部件"""
        # 设置显示返回值
        mock_widget = {'type': 'weather_widget', 'content': {}}
        self.mock_display.render_widget.return_value = mock_widget
        
        # 默认尺寸
        result = self.weather_manager.render_widget()
        
        # 验证显示调用
        self.mock_display.render_widget.assert_called_once_with((200, 100))
        
        # 验证结果
        self.assertEqual(result, mock_widget)
        
        # 使用自定义尺寸
        self.mock_display.reset_mock()
        size = (300, 150)
        
        result = self.weather_manager.render_widget(size)
        
        # 验证显示调用
        self.mock_display.render_widget.assert_called_once_with(size)
    
    def test_set_city(self):
        """测试设置城市"""
        # 设置服务返回值
        self.mock_service.set_city.return_value = True
        
        # 设置城市
        result = self.weather_manager.set_city('NewCity')
        
        # 验证结果
        self.assertTrue(result)
        
        # 验证服务调用
        self.mock_service.set_city.assert_called_once_with('NewCity')
        
        # 测试失败情况
        self.mock_service.reset_mock()
        self.mock_service.set_city.return_value = False
        
        result = self.weather_manager.set_city('')
        self.assertFalse(result)
    
    def test_set_units(self):
        """测试设置温度单位"""
        # 设置服务返回值
        self.mock_service.set_units.return_value = True
        
        # 设置单位
        result = self.weather_manager.set_units('imperial')
        
        # 验证结果
        self.assertTrue(result)
        
        # 验证服务调用
        self.mock_service.set_units.assert_called_once_with('imperial')
        
        # 测试失败情况
        self.mock_service.reset_mock()
        self.mock_service.set_units.return_value = False
        
        result = self.weather_manager.set_units('invalid')
        self.assertFalse(result)
    
    def test_set_api_key(self):
        """测试设置API密钥"""
        # 设置服务返回值
        self.mock_service.set_api_key.return_value = True
        
        # 设置API密钥
        result = self.weather_manager.set_api_key('new_api_key')
        
        # 验证结果
        self.assertTrue(result)
        
        # 验证服务调用
        self.mock_service.set_api_key.assert_called_once_with('new_api_key')
    
    def test_set_refresh_interval(self):
        """测试设置刷新间隔"""
        # 设置服务返回值
        self.mock_service.set_refresh_interval.return_value = True
        
        # 设置刷新间隔
        result = self.weather_manager.set_refresh_interval(7200)
        
        # 验证结果
        self.assertTrue(result)
        
        # 验证服务调用
        self.mock_service.set_refresh_interval.assert_called_once_with(7200)
    
    def test_set_display_style(self):
        """测试设置显示样式"""
        # 设置显示返回值
        self.mock_display.set_display_style.return_value = True
        
        # 设置样式
        result = self.weather_manager.set_display_style('detailed')
        
        # 验证结果
        self.assertTrue(result)
        
        # 验证显示调用
        self.mock_display.set_display_style.assert_called_once_with('detailed')
        
        # 测试失败情况
        self.mock_display.reset_mock()
        self.mock_display.set_display_style.return_value = False
        
        result = self.weather_manager.set_display_style('invalid')
        self.assertFalse(result)
    
    def test_set_color_scheme(self):
        """测试设置颜色方案"""
        # 设置显示返回值
        self.mock_display.set_color_scheme.return_value = True
        
        # 设置方案
        result = self.weather_manager.set_color_scheme('dark')
        
        # 验证结果
        self.assertTrue(result)
        
        # 验证显示调用
        self.mock_display.set_color_scheme.assert_called_once_with('dark')
        
        # 测试失败情况
        self.mock_display.reset_mock()
        self.mock_display.set_color_scheme.return_value = False
        
        result = self.weather_manager.set_color_scheme('invalid')
        self.assertFalse(result)
    
    def test_toggle_animations(self):
        """测试切换动画"""
        # 设置动画
        self.weather_manager.toggle_animations(False)
        
        # 验证显示调用
        self.mock_display.toggle_animations.assert_called_once_with(False)
        
        # 再次切换
        self.mock_display.reset_mock()
        self.weather_manager.toggle_animations(True)
        
        # 验证显示调用
        self.mock_display.toggle_animations.assert_called_once_with(True)
    
    def test_register_callback(self):
        """测试注册回调"""
        # 创建测试回调
        mock_callback = MagicMock()
        
        # 注册有效事件类型
        result = self.weather_manager.register_callback('on_weather_updated', mock_callback)
        
        # 验证结果
        self.assertTrue(result)
        self.assertIn(mock_callback, self.weather_manager.callbacks['on_weather_updated'])
        
        # 测试无效事件类型
        result = self.weather_manager.register_callback('invalid_event', mock_callback)
        
        # 验证结果
        self.assertFalse(result)
    
    def test_unregister_callback(self):
        """测试取消注册回调"""
        # 创建测试回调
        mock_callback = MagicMock()
        
        # 注册回调
        self.weather_manager.callbacks['on_weather_updated'].append(mock_callback)
        
        # 取消注册
        result = self.weather_manager.unregister_callback('on_weather_updated', mock_callback)
        
        # 验证结果
        self.assertTrue(result)
        self.assertNotIn(mock_callback, self.weather_manager.callbacks['on_weather_updated'])
        
        # 测试无效事件类型
        result = self.weather_manager.unregister_callback('invalid_event', mock_callback)
        self.assertFalse(result)
        
        # 测试未注册的回调
        result = self.weather_manager.unregister_callback('on_weather_updated', mock_callback)
        self.assertFalse(result)
    
    def test_trigger_callbacks(self):
        """测试触发回调"""
        # 创建多个测试回调
        mock_callback1 = MagicMock()
        mock_callback2 = MagicMock()
        
        # 添加异常抛出回调
        mock_exception = MagicMock(side_effect=Exception('测试异常'))
        
        # 注册回调
        self.weather_manager.callbacks['on_weather_updated'].extend([mock_callback1, mock_exception, mock_callback2])
        
        # 触发回调
        test_data = {'weather': self.mock_weather_data}
        self.weather_manager._trigger_callbacks('on_weather_updated', test_data)
        
        # 验证回调调用
        mock_callback1.assert_called_once_with(test_data)
        mock_callback2.assert_called_once_with(test_data)
        
        # 验证异常回调仍允许其他回调执行
        mock_exception.assert_called_once_with(test_data)
    
    def test_get_last_updated(self):
        """测试获取最后更新时间"""
        # 设置服务返回值
        test_time = time.time()
        self.mock_service.get_last_updated.return_value = test_time
        
        # 获取时间
        result = self.weather_manager.get_last_updated()
        
        # 验证结果
        self.assertEqual(result, test_time)
        
        # 验证服务调用
        self.mock_service.get_last_updated.assert_called_once()
    
    def test_update_config_no_restart(self):
        """测试更新不需要重启的配置"""
        # 准备测试配置
        new_config = {
            'service': {
                'city': 'NewCity',
                'units': 'imperial',
                'refresh_interval': 7200
            },
            'display': {
                'display_style': 'detailed',
                'color_scheme': 'dark',
                'animation_enabled': False
            }
        }
        
        # 模拟方法调用
        with patch.multiple(self.weather_manager, 
                           set_city=MagicMock(return_value=True),
                           set_units=MagicMock(return_value=True),
                           set_refresh_interval=MagicMock(return_value=True),
                           set_display_style=MagicMock(return_value=True),
                           set_color_scheme=MagicMock(return_value=True),
                           toggle_animations=MagicMock()):
            
            # 更新配置
            result = self.weather_manager.update_config(new_config)
            
            # 验证结果
            self.assertFalse(result)  # 不需要重启
            
            # 验证方法调用
            self.weather_manager.set_city.assert_called_once_with('NewCity')
            self.weather_manager.set_units.assert_called_once_with('imperial')
            self.weather_manager.set_refresh_interval.assert_called_once_with(7200)
            self.weather_manager.set_display_style.assert_called_once_with('detailed')
            self.weather_manager.set_color_scheme.assert_called_once_with('dark')
            self.weather_manager.toggle_animations.assert_called_once_with(False)
    
    def test_update_config_restart(self):
        """测试更新需要重启的配置"""
        # 准备测试配置
        new_config = {
            'service': {
                'api_service': 'weatherapi',
                'api_key': 'new_api_key'
            }
        }
        
        # 设置运行状态
        self.weather_manager.running = True
        
        # 模拟方法调用
        with patch.multiple(self.weather_manager, 
                           stop=MagicMock(return_value=True),
                           start=MagicMock(return_value=True),
                           _connect_service_display=MagicMock()):
            
            # 更新配置
            result = self.weather_manager.update_config(new_config)
            
            # 验证结果
            self.assertTrue(result)  # 需要重启
            
            # 验证方法调用
            self.weather_manager.stop.assert_called_once()
            self.mock_service_class.assert_called_with(self.weather_manager.config.get('service', {}))
            self.weather_manager._connect_service_display.assert_called_once()
            self.weather_manager.start.assert_called_once()

if __name__ == '__main__':
    unittest.main() 