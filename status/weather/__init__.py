"""
---------------------------------------------------------------
File name:                  __init__.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                天气集成模块，提供天气信息获取和展示
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

from .weather_service import WeatherService
from .weather_display import WeatherDisplay
from .weather_manager import WeatherManager
from .factory import create_weather_system, create_default_weather_system, create_custom_weather_system

__all__ = [
    'WeatherService',
    'WeatherDisplay',
    'WeatherManager',
    'create_weather_system',
    'create_default_weather_system',
    'create_custom_weather_system'
] 