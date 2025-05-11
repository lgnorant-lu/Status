"""
---------------------------------------------------------------
File name:                  factory.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                天气系统工厂，提供创建天气系统的便捷方法
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""
import logging
from typing import Dict, Any, Optional

from .weather_service import WeatherService
from .weather_display import WeatherDisplay
from .weather_manager import WeatherManager

def create_weather_system(config: Dict[str, Any] = None) -> WeatherManager:
    """
    创建天气系统
    
    Args:
        config: 配置信息，包括服务和显示配置
        
    Returns:
        WeatherManager: 天气管理器实例
    """
    logger = logging.getLogger("WeatherFactory")
    logger.info("创建天气系统")
    
    # 使用提供的配置或默认配置
    config = config or {}
    
    # 创建天气管理器
    manager = WeatherManager(config)
    
    # 如果配置了自动启动，则启动管理器
    if config.get('auto_start', True):
        manager.start()
        logger.info("天气系统已自动启动")
    
    return manager

def create_default_weather_system(
    city: str = 'Beijing',
    api_key: str = '',
    api_service: str = 'openweathermap',
    units: str = 'metric',
    display_style: str = 'compact',
    color_scheme: str = 'default',
    auto_refresh: bool = True,
    auto_start: bool = True
) -> WeatherManager:
    """
    创建具有默认配置的天气系统
    
    Args:
        city: 城市名称
        api_key: API密钥
        api_service: API服务 ('openweathermap' 或 'weatherapi')
        units: 温度单位 ('metric' 或 'imperial')
        display_style: 显示样式 ('compact' 或 'detailed')
        color_scheme: 颜色方案 ('default' 或 'dark')
        auto_refresh: 是否自动刷新天气
        auto_start: 是否自动启动系统
        
    Returns:
        WeatherManager: 天气管理器实例
    """
    logger = logging.getLogger("WeatherFactory")
    logger.info(f"创建默认天气系统，城市：{city}，API服务：{api_service}")
    
    # 构建配置
    config = {
        'service': {
            'api_service': api_service,
            'api_key': api_key,
            'city': city,
            'units': units,
            'auto_refresh': auto_refresh,
            'refresh_interval': 3600  # 默认1小时刷新一次
        },
        'display': {
            'display_style': display_style,
            'color_scheme': color_scheme,
            'use_icons': True,
            'use_animations': True
        },
        'auto_start': auto_start
    }
    
    # 创建天气系统
    return create_weather_system(config)

def create_custom_weather_system(
    service_config: Dict[str, Any] = None,
    display_config: Dict[str, Any] = None,
    auto_start: bool = True
) -> WeatherManager:
    """
    创建自定义配置的天气系统
    
    Args:
        service_config: 天气服务配置
        display_config: 显示配置
        auto_start: 是否自动启动系统
        
    Returns:
        WeatherManager: 天气管理器实例
    """
    logger = logging.getLogger("WeatherFactory")
    logger.info("创建自定义天气系统")
    
    # 构建配置
    config = {
        'service': service_config or {},
        'display': display_config or {},
        'auto_start': auto_start
    }
    
    # 创建天气系统
    return create_weather_system(config)

def create_lightweight_weather_system(
    city: str = 'Beijing',
    api_key: str = '',
    auto_refresh: bool = False
) -> WeatherManager:
    """
    创建轻量级天气系统，适用于资源有限的环境
    
    Args:
        city: 城市名称
        api_key: API密钥
        auto_refresh: 是否自动刷新天气
        
    Returns:
        WeatherManager: 天气管理器实例
    """
    logger = logging.getLogger("WeatherFactory")
    logger.info(f"创建轻量级天气系统，城市：{city}")
    
    # 构建轻量级配置
    config = {
        'service': {
            'api_service': 'openweathermap',
            'api_key': api_key,
            'city': city,
            'units': 'metric',
            'auto_refresh': auto_refresh,
            'refresh_interval': 7200  # 2小时刷新一次
        },
        'display': {
            'display_style': 'compact',
            'color_scheme': 'default',
            'use_icons': True,
            'use_animations': False  # 禁用动画以节省资源
        },
        'auto_start': True
    }
    
    # 创建天气系统
    return create_weather_system(config)

def create_detailed_weather_system(
    city: str = 'Beijing',
    api_key: str = '',
    api_service: str = 'weatherapi',  # 使用功能更丰富的API
    auto_refresh: bool = True
) -> WeatherManager:
    """
    创建详细天气系统，包含更多天气信息
    
    Args:
        city: 城市名称
        api_key: API密钥
        api_service: API服务 ('openweathermap' 或 'weatherapi')
        auto_refresh: 是否自动刷新天气
        
    Returns:
        WeatherManager: 天气管理器实例
    """
    logger = logging.getLogger("WeatherFactory")
    logger.info(f"创建详细天气系统，城市：{city}，API服务：{api_service}")
    
    # 构建详细配置
    config = {
        'service': {
            'api_service': api_service,
            'api_key': api_key,
            'city': city,
            'units': 'metric',
            'auto_refresh': auto_refresh,
            'refresh_interval': 1800  # 30分钟刷新一次
        },
        'display': {
            'display_style': 'detailed',
            'color_scheme': 'default',
            'use_icons': True,
            'use_animations': True,
            'show_forecast': True
        },
        'auto_start': True
    }
    
    # 创建天气系统
    return create_weather_system(config)

def create_dark_theme_weather_system(
    city: str = 'Beijing',
    api_key: str = '',
    auto_refresh: bool = True
) -> WeatherManager:
    """
    创建深色主题天气系统
    
    Args:
        city: 城市名称
        api_key: API密钥
        auto_refresh: 是否自动刷新天气
        
    Returns:
        WeatherManager: 天气管理器实例
    """
    logger = logging.getLogger("WeatherFactory")
    logger.info(f"创建深色主题天气系统，城市：{city}")
    
    # 构建深色主题配置
    config = {
        'service': {
            'api_service': 'openweathermap',
            'api_key': api_key,
            'city': city,
            'units': 'metric',
            'auto_refresh': auto_refresh,
            'refresh_interval': 3600  # 1小时刷新一次
        },
        'display': {
            'display_style': 'compact',
            'color_scheme': 'dark',
            'use_icons': True,
            'use_animations': True
        },
        'auto_start': True
    }
    
    # 创建天气系统
    return create_weather_system(config) 