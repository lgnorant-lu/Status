"""
---------------------------------------------------------------
File name:                  weather_display.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                天气显示器，负责将天气数据可视化呈现
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""
import logging
import time
from typing import Dict, Any, Optional, List, Callable, Union, Tuple

class WeatherDisplay:
    """天气显示器类，负责将天气数据可视化呈现"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化天气显示器
        
        Args:
            config: 配置信息，包括显示样式、单位等
        """
        self.logger = logging.getLogger("WeatherDisplay")
        self.config = config or {}
        
        # 显示设置
        self.display_style = self.config.get('display_style', 'compact')  # compact, detailed
        self.use_icons = self.config.get('use_icons', True)
        self.use_animations = self.config.get('use_animations', True)
        self.show_forecast = self.config.get('show_forecast', False)
        self.time_format = self.config.get('time_format', '%H:%M:%S')
        self.date_format = self.config.get('date_format', '%Y-%m-%d')
        
        # 颜色方案
        self.color_scheme = self.config.get('color_scheme', 'default')
        self.color_schemes = {
            'default': {
                'background': '#FFFFFF',
                'text': '#333333',
                'highlight': '#4285F4',
                'temperature_cold': '#4285F4',  # 蓝色 - 冷
                'temperature_cool': '#72b8ff',  # 浅蓝 - 凉爽
                'temperature_mild': '#43a047',  # 绿色 - 温和
                'temperature_warm': '#FB8C00',  # 橙色 - 温暖
                'temperature_hot': '#E53935',   # 红色 - 热
            },
            'dark': {
                'background': '#333333',
                'text': '#FFFFFF',
                'highlight': '#4285F4',
                'temperature_cold': '#81D4FA',  # 浅蓝 - 冷
                'temperature_cool': '#4FC3F7',  # 中蓝 - 凉爽
                'temperature_mild': '#81C784',  # 浅绿 - 温和
                'temperature_warm': '#FFB74D',  # 浅橙 - 温暖
                'temperature_hot': '#FF8A65',   # 浅红 - 热
            }
        }
        
        # 图标设置
        self.icon_size = self.config.get('icon_size', 32)
        self.icon_set = self.config.get('icon_set', 'default')
        
        # 定义不同天气条件的图标和描述
        self.weather_icons = {
            'clear_day': {
                'icon': '☀️',
                'label': '晴朗',
                'description': '晴空万里，阳光明媚'
            },
            'clear_night': {
                'icon': '🌙',
                'label': '晴朗',
                'description': '晴朗的夜晚，繁星点点'
            },
            'partly_cloudy_day': {
                'icon': '🌤️',
                'label': '多云',
                'description': '部分多云，阳光时有穿透'
            },
            'partly_cloudy_night': {
                'icon': '🌜️',
                'label': '多云',
                'description': '部分多云，月光时有穿透'
            },
            'cloudy': {
                'icon': '☁️',
                'label': '阴天',
                'description': '云层厚重，阴天为主'
            },
            'rain': {
                'icon': '🌧️',
                'label': '雨',
                'description': '降雨，建议带伞出行'
            },
            'rain_day': {
                'icon': '🌦️',
                'label': '阵雨',
                'description': '阵雨，雨量不大'
            },
            'rain_night': {
                'icon': '🌧️',
                'label': '夜间雨',
                'description': '夜间降雨，建议带伞出行'
            },
            'thunderstorm': {
                'icon': '⛈️',
                'label': '雷雨',
                'description': '雷雨天气，请注意安全'
            },
            'snow': {
                'icon': '❄️',
                'label': '雪',
                'description': '降雪，注意保暖'
            },
            'fog': {
                'icon': '🌫️',
                'label': '雾',
                'description': '雾气较大，出行注意安全'
            },
            'unknown': {
                'icon': '❓',
                'label': '未知',
                'description': '未知天气状况'
            }
        }
        
        # 温度颜色映射
        self.temperature_thresholds = {
            'cold': -5,     # 冷
            'cool': 10,     # 凉爽
            'mild': 20,     # 温和
            'warm': 28,     # 温暖
            'hot': 35       # 热
        }
        
        # 动画设置
        self.animation_speed = self.config.get('animation_speed', 1.0)
        self.animation_enabled = self.config.get('animation_enabled', True)
        
        # 状态信息
        self.current_weather = None
        self.last_updated = None
        
        self.logger.info("天气显示器初始化完成")
    
    def update_display(self, weather_data: Dict[str, Any]) -> None:
        """
        更新显示的天气数据
        
        Args:
            weather_data: 天气数据
        """
        if not weather_data:
            self.logger.warning("尝试更新显示，但天气数据为空")
            return
        
        self.current_weather = weather_data
        self.last_updated = time.time()
        
        self.logger.debug(f"天气显示已更新: {weather_data.get('city')}, "
                         f"{weather_data.get('temperature')}°{weather_data.get('temperature_unit')}")
    
    def get_formatted_weather(self) -> Dict[str, Any]:
        """
        获取格式化的天气数据，用于显示
        
        Returns:
            Dict[str, Any]: 格式化的天气数据
        """
        if not self.current_weather:
            return {'error': '无天气数据可显示'}
        
        try:
            # 基本天气信息
            city = self.current_weather.get('city', '')
            country = self.current_weather.get('country', '')
            description = self.current_weather.get('description', '')
            temperature = self.current_weather.get('temperature', 0)
            temperature_unit = self.current_weather.get('temperature_unit', 'C')
            weather_icon = self.current_weather.get('weather_icon', 'unknown')
            
            # 获取图标和描述
            icon_info = self.weather_icons.get(weather_icon, self.weather_icons['unknown'])
            icon = icon_info['icon'] if self.use_icons else ''
            label = icon_info['label']
            detailed_description = icon_info['description']
            
            # 获取温度颜色
            temp_color = self._get_temperature_color(temperature)
            
            # 格式化时间
            timestamp = self.current_weather.get('timestamp', time.time())
            formatted_time = time.strftime(self.time_format, time.localtime(timestamp))
            formatted_date = time.strftime(self.date_format, time.localtime(timestamp))
            
            # 构建显示数据
            display_data = {
                'location': f"{city}, {country}" if country else city,
                'temperature': f"{temperature}°{temperature_unit}",
                'description': description,
                'icon': icon,
                'label': label,
                'detailed_description': detailed_description,
                'temperature_color': temp_color,
                'time': formatted_time,
                'date': formatted_date,
                'display_style': self.display_style,
                'raw_data': self.current_weather
            }
            
            # 添加详细信息（如果显示样式为详细）
            if self.display_style == 'detailed':
                display_data.update({
                    'humidity': f"{self.current_weather.get('humidity', 0)}%",
                    'wind_speed': self.current_weather.get('wind_speed', 0),
                    'wind_direction': self._format_wind_direction(self.current_weather.get('wind_direction', 0)),
                    'pressure': f"{self.current_weather.get('pressure', 0)} hPa",
                    'feels_like': f"{self.current_weather.get('feels_like', 0)}°{temperature_unit}",
                    'visibility': self._format_visibility(self.current_weather.get('visibility', 0)),
                    'cloudiness': f"{self.current_weather.get('cloudiness', 0)}%"
                })
            
            # 添加动画信息
            if self.use_animations:
                display_data['animation'] = self._get_weather_animation(weather_icon)
            
            return display_data
            
        except Exception as e:
            self.logger.error(f"格式化天气数据异常: {e}")
            return {
                'error': f'格式化天气数据失败: {str(e)}',
                'raw_data': self.current_weather
            }
    
    def get_weather_summary(self) -> str:
        """
        获取简短的天气摘要
        
        Returns:
            str: 天气摘要文本
        """
        if not self.current_weather:
            return "暂无天气数据"
        
        try:
            city = self.current_weather.get('city', '')
            temperature = self.current_weather.get('temperature', 0)
            temperature_unit = self.current_weather.get('temperature_unit', 'C')
            description = self.current_weather.get('description', '')
            
            return f"{city}: {temperature}°{temperature_unit}, {description}"
            
        except Exception as e:
            self.logger.error(f"获取天气摘要异常: {e}")
            return "获取天气摘要失败"
    
    def render_widget(self, size: Tuple[int, int] = (200, 100)) -> Dict[str, Any]:
        """
        渲染天气小部件
        
        Args:
            size: 小部件尺寸 (宽, 高)
            
        Returns:
            Dict[str, Any]: 小部件渲染数据
        """
        if not self.current_weather:
            return {
                'type': 'error',
                'message': '暂无天气数据',
                'size': size
            }
        
        try:
            weather_data = self.get_formatted_weather()
            
            # 根据尺寸选择合适的显示样式
            widget_style = 'compact' if size[0] < 300 or size[1] < 150 else self.display_style
            
            # 获取颜色方案
            colors = self.color_schemes.get(self.color_scheme, self.color_schemes['default'])
            
            # 构建小部件数据
            widget_data = {
                'type': 'weather_widget',
                'style': widget_style,
                'size': size,
                'colors': colors,
                'content': weather_data,
                'animation': weather_data.get('animation', None) if self.animation_enabled else None,
                'animation_speed': self.animation_speed
            }
            
            return widget_data
            
        except Exception as e:
            self.logger.error(f"渲染天气小部件异常: {e}")
            return {
                'type': 'error',
                'message': f'渲染天气小部件失败: {str(e)}',
                'size': size
            }
    
    def set_display_style(self, style: str) -> bool:
        """
        设置显示样式
        
        Args:
            style: 显示样式 ('compact' 或 'detailed')
            
        Returns:
            bool: 是否成功设置
        """
        if style not in ['compact', 'detailed']:
            self.logger.error(f"不支持的显示样式: {style}")
            return False
        
        self.display_style = style
        self.logger.info(f"已设置显示样式: {style}")
        return True
    
    def set_color_scheme(self, scheme: str) -> bool:
        """
        设置颜色方案
        
        Args:
            scheme: 颜色方案 ('default' 或 'dark')
            
        Returns:
            bool: 是否成功设置
        """
        if scheme not in self.color_schemes:
            self.logger.error(f"不支持的颜色方案: {scheme}")
            return False
        
        self.color_scheme = scheme
        self.logger.info(f"已设置颜色方案: {scheme}")
        return True
    
    def toggle_animations(self, enabled: bool) -> None:
        """
        开启或关闭动画
        
        Args:
            enabled: 是否启用动画
        """
        self.animation_enabled = enabled
        self.logger.info(f"{'启用' if enabled else '禁用'}天气动画")
    
    def set_icon_size(self, size: int) -> None:
        """
        设置图标大小
        
        Args:
            size: 图标大小（像素）
        """
        if size < 16:
            self.logger.warning(f"图标大小过小 ({size}px)，已自动调整为16px")
            size = 16
        elif size > 128:
            self.logger.warning(f"图标大小过大 ({size}px)，已自动调整为128px")
            size = 128
        
        self.icon_size = size
        self.logger.info(f"已设置图标大小: {size}px")
    
    def _get_temperature_color(self, temperature: float) -> str:
        """
        根据温度获取对应的颜色
        
        Args:
            temperature: 温度值
            
        Returns:
            str: 颜色代码
        """
        colors = self.color_schemes.get(self.color_scheme, self.color_schemes['default'])
        
        if temperature < self.temperature_thresholds['cold']:
            return colors['temperature_cold']
        elif temperature < self.temperature_thresholds['cool']:
            return colors['temperature_cool']
        elif temperature < self.temperature_thresholds['mild']:
            return colors['temperature_mild']
        elif temperature < self.temperature_thresholds['warm']:
            return colors['temperature_warm']
        else:
            return colors['temperature_hot']
    
    def _format_wind_direction(self, degrees: float) -> str:
        """
        将风向角度转换为文字描述
        
        Args:
            degrees: 风向角度
            
        Returns:
            str: 风向描述
        """
        directions = [
            '北', '东北偏北', '东北', '东北偏东', 
            '东', '东南偏东', '东南', '东南偏南', 
            '南', '西南偏南', '西南', '西南偏西', 
            '西', '西北偏西', '西北', '西北偏北'
        ]
        
        index = round(degrees / 22.5) % 16
        return directions[index]
    
    def _format_visibility(self, visibility: float) -> str:
        """
        格式化可见度
        
        Args:
            visibility: 可见度值
            
        Returns:
            str: 格式化的可见度
        """
        # OpenWeatherMap的可见度单位是米
        if visibility >= 1000:
            return f"{visibility/1000:.1f} km"
        else:
            return f"{visibility} m"
    
    def _get_weather_animation(self, weather_icon: str) -> Dict[str, Any]:
        """
        根据天气图标获取动画设置
        
        Args:
            weather_icon: 天气图标代码
            
        Returns:
            Dict[str, Any]: 动画设置
        """
        # 定义不同天气的动画效果
        animations = {
            'clear_day': {
                'type': 'sun_rays',
                'params': {'intensity': 0.8, 'speed': 1.0, 'color': '#FFD700'}
            },
            'clear_night': {
                'type': 'stars_twinkle',
                'params': {'intensity': 0.6, 'speed': 0.7, 'color': '#FFFFFF'}
            },
            'partly_cloudy_day': {
                'type': 'clouds_moving',
                'params': {'coverage': 0.4, 'speed': 0.8, 'color': '#FFFFFF'}
            },
            'partly_cloudy_night': {
                'type': 'clouds_moving',
                'params': {'coverage': 0.4, 'speed': 0.6, 'color': '#CCCCCC'}
            },
            'cloudy': {
                'type': 'clouds_moving',
                'params': {'coverage': 0.8, 'speed': 0.7, 'color': '#AAAAAA'}
            },
            'rain': {
                'type': 'rain_drops',
                'params': {'intensity': 0.7, 'speed': 1.2, 'color': '#5DADEC'}
            },
            'rain_day': {
                'type': 'rain_drops',
                'params': {'intensity': 0.5, 'speed': 1.0, 'color': '#5DADEC'}
            },
            'rain_night': {
                'type': 'rain_drops',
                'params': {'intensity': 0.6, 'speed': 1.1, 'color': '#5DADEC'}
            },
            'thunderstorm': {
                'type': 'lightning_flash',
                'params': {'intensity': 0.9, 'frequency': 0.4, 'color': '#FFFFFF'}
            },
            'snow': {
                'type': 'snow_fall',
                'params': {'intensity': 0.7, 'speed': 0.8, 'color': '#FFFFFF'}
            },
            'fog': {
                'type': 'fog_moving',
                'params': {'density': 0.8, 'speed': 0.3, 'color': '#CCCCCC'}
            }
        }
        
        return animations.get(weather_icon, {
            'type': 'none',
            'params': {}
        }) 