"""
---------------------------------------------------------------
File name:                  test_weather_display.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                天气显示组件单元测试
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""
import unittest
from unittest.mock import patch, MagicMock, call
import logging
import time

from status.weather.weather_display import WeatherDisplay

# 禁用日志输出，避免测试时的干扰
logging.disable(logging.CRITICAL)

class TestWeatherDisplay(unittest.TestCase):
    """天气显示组件测试类"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 基本测试天气数据
        self.test_weather_data = {
            'city': 'Beijing',
            'country': 'CN',
            'temperature': 22.5,
            'temperature_unit': 'C',
            'feels_like': 23.0,
            'humidity': 60,
            'pressure': 1012,
            'description': '晴天',
            'weather_icon': 'clear_day',
            'wind_speed': 5.2,
            'wind_direction': 180,
            'cloudiness': 10,
            'visibility': 10000,
            'timestamp': 1617500000  # 2021-04-04 10:40:00 UTC
        }
        
        # 默认配置
        self.default_config = {
            'display_style': 'compact',
            'color_scheme': 'default',
            'use_icons': True,
            'use_animations': True,
            'time_format': '%H:%M:%S',
            'date_format': '%Y-%m-%d',
            'show_forecast': True
        }
        
        # 创建天气显示实例
        self.display = WeatherDisplay(self.default_config)
    
    def test_init(self):
        """测试初始化"""
        # 测试默认配置
        self.assertEqual(self.display.display_style, 'compact')
        self.assertEqual(self.display.color_scheme, 'default')
        self.assertTrue(self.display.use_icons)
        self.assertTrue(self.display.use_animations)
        self.assertEqual(self.display.time_format, '%H:%M:%S')
        self.assertEqual(self.display.date_format, '%Y-%m-%d')
        
        # 测试无配置初始化
        display = WeatherDisplay()
        self.assertIsNotNone(display.display_style)
        self.assertIsNotNone(display.color_scheme)
        
        # 测试自定义配置
        custom_config = {
            'display_style': 'detailed',
            'color_scheme': 'dark',
            'use_animations': False
        }
        display = WeatherDisplay(custom_config)
        self.assertEqual(display.display_style, 'detailed')
        self.assertEqual(display.color_scheme, 'dark')
        self.assertFalse(display.use_animations)
        # 默认值仍应存在
        self.assertTrue(display.use_icons)
        self.assertFalse(display.show_forecast)  # 默认应该是False
    
    def test_update_display(self):
        """测试更新天气数据"""
        # 更新天气数据
        self.display.update_display(self.test_weather_data)
        
        # 验证数据已更新
        self.assertEqual(self.display.current_weather, self.test_weather_data)
        self.assertIsNotNone(self.display.last_updated)
        
        # 测试更新空数据
        original_data = self.display.current_weather
        original_time = self.display.last_updated
        
        self.display.update_display(None)
        
        # 验证没有变化
        self.assertEqual(self.display.current_weather, original_data)
        self.assertEqual(self.display.last_updated, original_time)
    
    def test_get_formatted_weather(self):
        """测试获取格式化的天气数据"""
        # 更新天气数据
        self.display.update_display(self.test_weather_data)
        
        # 获取格式化数据
        result = self.display.get_formatted_weather()
        
        # 验证格式化结果
        self.assertIsInstance(result, dict)
        self.assertEqual(result['location'], 'Beijing, CN')
        self.assertEqual(result['temperature'], '22.5°C')
        self.assertEqual(result['description'], '晴天')
        self.assertEqual(result['label'], '晴朗')
        self.assertIn('icon', result)
        self.assertIn('temperature_color', result)
        self.assertIn('time', result)
        self.assertIn('date', result)
        
        # 测试无天气数据
        self.display.current_weather = None
        result = self.display.get_formatted_weather()
        self.assertEqual(result['error'], '无天气数据可显示')
    
    def test_get_weather_summary(self):
        """测试获取天气摘要"""
        # 更新天气数据
        self.display.update_display(self.test_weather_data)
        
        # 获取摘要
        result = self.display.get_weather_summary()
        
        # 验证摘要内容
        self.assertEqual(result, 'Beijing: 22.5°C, 晴天')
        
        # 测试无天气数据
        self.display.current_weather = None
        result = self.display.get_weather_summary()
        self.assertEqual(result, '暂无天气数据')
    
    def test_render_widget(self):
        """测试渲染天气小部件"""
        # 更新天气数据
        self.display.update_display(self.test_weather_data)
        
        # 渲染小部件
        result = self.display.render_widget()
        
        # 验证渲染结果
        self.assertIsInstance(result, dict)
        self.assertEqual(result['type'], 'weather_widget')
        self.assertEqual(result['style'], 'compact')
        self.assertIn('content', result)
        self.assertIn('colors', result)
        
        # 测试自定义尺寸
        result = self.display.render_widget((400, 300))
        self.assertEqual(result['size'], (400, 300))
        
        # 测试无天气数据
        self.display.current_weather = None
        result = self.display.render_widget()
        self.assertEqual(result['type'], 'error')
        self.assertIn('message', result)
    
    def test_set_display_style(self):
        """测试设置显示样式"""
        # 设置有效样式
        self.assertTrue(self.display.set_display_style('detailed'))
        self.assertEqual(self.display.display_style, 'detailed')
        
        # 设置无效样式
        self.assertFalse(self.display.set_display_style('invalid'))
        self.assertEqual(self.display.display_style, 'detailed')  # 保持不变
    
    def test_set_color_scheme(self):
        """测试设置颜色方案"""
        # 设置有效方案
        self.assertTrue(self.display.set_color_scheme('dark'))
        self.assertEqual(self.display.color_scheme, 'dark')
        
        # 设置无效方案
        self.assertFalse(self.display.set_color_scheme('invalid'))
        self.assertEqual(self.display.color_scheme, 'dark')  # 保持不变
    
    def test_toggle_animations(self):
        """测试切换动画"""
        # 初始为启用
        self.assertTrue(self.display.animation_enabled)
        
        # 禁用动画
        self.display.toggle_animations(False)
        self.assertFalse(self.display.animation_enabled)
        
        # 启用动画
        self.display.toggle_animations(True)
        self.assertTrue(self.display.animation_enabled)
    
    def test_set_icon_size(self):
        """测试设置图标大小"""
        # 设置有效大小
        self.display.set_icon_size(64)
        self.assertEqual(self.display.icon_size, 64)
        
        # 设置过小的大小
        self.display.set_icon_size(8)
        self.assertEqual(self.display.icon_size, 16)  # 应自动调整为最小值
        
        # 设置过大的大小
        self.display.set_icon_size(256)
        self.assertEqual(self.display.icon_size, 128)  # 应自动调整为最大值
    
    def test_temperature_color(self):
        """测试获取温度颜色"""
        # 测试不同温度范围
        color_cold = self.display._get_temperature_color(-10)
        color_cool = self.display._get_temperature_color(5)
        color_mild = self.display._get_temperature_color(15)
        color_warm = self.display._get_temperature_color(25)
        color_hot = self.display._get_temperature_color(40)
        
        # 确保返回的是字符串
        self.assertIsInstance(color_cold, str)
        self.assertIsInstance(color_cool, str)
        self.assertIsInstance(color_mild, str)
        self.assertIsInstance(color_warm, str)
        self.assertIsInstance(color_hot, str)
        
        # 检查颜色是否与配置匹配
        colors = self.display.color_schemes[self.display.color_scheme]
        self.assertEqual(color_cold, colors['temperature_cold'])
        self.assertEqual(color_cool, colors['temperature_cool'])
        self.assertEqual(color_mild, colors['temperature_mild'])
        self.assertEqual(color_warm, colors['temperature_warm'])
        self.assertEqual(color_hot, colors['temperature_hot'])
    
    def test_format_wind_direction(self):
        """测试格式化风向"""
        # 测试不同角度
        self.assertEqual(self.display._format_wind_direction(0), '北')
        self.assertEqual(self.display._format_wind_direction(90), '东')
        self.assertEqual(self.display._format_wind_direction(180), '南')
        self.assertEqual(self.display._format_wind_direction(270), '西')
        self.assertEqual(self.display._format_wind_direction(45), '东北')
    
    def test_format_visibility(self):
        """测试格式化可见度"""
        # 测试不同单位
        self.assertEqual(self.display._format_visibility(500), '500 m')
        self.assertEqual(self.display._format_visibility(1000), '1.0 km')
        self.assertEqual(self.display._format_visibility(10000), '10.0 km')
    
    def test_get_weather_animation(self):
        """测试获取天气动画"""
        # 测试不同天气类型的动画
        result_clear = self.display._get_weather_animation('clear_day')
        result_rain = self.display._get_weather_animation('rain')
        result_snow = self.display._get_weather_animation('snow')
        result_unknown = self.display._get_weather_animation('unknown')
        
        # 验证动画格式
        self.assertIn('type', result_clear)
        self.assertIn('params', result_clear)
        self.assertIn('type', result_rain)
        self.assertIn('params', result_rain)
        self.assertIn('type', result_snow)
        self.assertIn('params', result_snow)
        
        # 验证未知天气类型
        self.assertEqual(result_unknown['type'], 'none')
        self.assertEqual(result_unknown['params'], {})

if __name__ == '__main__':
    unittest.main() 