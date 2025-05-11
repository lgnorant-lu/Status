"""
---------------------------------------------------------------
File name:                  weather_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                天气管理器，整合天气服务和显示组件
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""
import logging
import threading
import time
from typing import Dict, Any, Optional, List, Callable, Union, Tuple

from .weather_service import WeatherService
from .weather_display import WeatherDisplay

class WeatherManager:
    """天气管理器类，整合天气服务和显示组件"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化天气管理器
        
        Args:
            config: 配置信息，包括服务和显示配置
        """
        self.logger = logging.getLogger("WeatherManager")
        self.config = config or {}
        
        # 从配置中提取服务和显示配置
        service_config = self.config.get('service', {})
        display_config = self.config.get('display', {})
        
        # 创建天气服务和显示组件
        self.weather_service = WeatherService(service_config)
        self.weather_display = WeatherDisplay(display_config)
        
        # 管理器状态
        self.running = False
        self.lock = threading.Lock()
        
        # 注册回调
        self.callbacks: Dict[str, List[Callable]] = {
            'on_weather_updated': [],
            'on_display_updated': [],
            'on_error': []
        }
        
        # 自动连接服务和显示器
        self._connect_service_display()
        
        self.logger.info("天气管理器初始化完成")
    
    def _connect_service_display(self) -> None:
        """连接天气服务和显示器的回调"""
        # 注册天气服务的回调
        self.weather_service.register_callback('on_weather_updated', self._on_weather_updated)
        self.weather_service.register_callback('on_weather_error', self._on_weather_error)
    
    def _on_weather_updated(self, data: Dict[str, Any]) -> None:
        """
        天气数据更新回调
        
        Args:
            data: 包含天气数据的字典
        """
        weather = data.get('weather')
        if weather:
            # 更新显示
            self.weather_display.update_display(weather)
            
            # 触发回调
            self._trigger_callbacks('on_weather_updated', {'weather': weather})
    
    def _on_weather_error(self, data: Dict[str, Any]) -> None:
        """
        天气错误回调
        
        Args:
            data: 包含错误信息的字典
        """
        error = data.get('error', '未知错误')
        self.logger.error(f"天气服务错误: {error}")
        
        # 触发回调
        self._trigger_callbacks('on_error', {'error': error, 'source': 'weather_service'})
    
    def start(self) -> bool:
        """
        启动天气管理器
        
        Returns:
            bool: 是否成功启动
        """
        with self.lock:
            if self.running:
                self.logger.warning("天气管理器已在运行中")
                return False
            
            # 启动天气服务
            if not self.weather_service.start():
                self.logger.error("启动天气服务失败")
                self._trigger_callbacks('on_error', {'error': '启动天气服务失败', 'source': 'weather_manager'})
                return False
            
            self.running = True
            self.logger.info("天气管理器已启动")
            return True
    
    def stop(self) -> bool:
        """
        停止天气管理器
        
        Returns:
            bool: 是否成功停止
        """
        with self.lock:
            if not self.running:
                self.logger.warning("天气管理器未在运行")
                return False
            
            # 停止天气服务
            if not self.weather_service.stop():
                self.logger.warning("停止天气服务时出现警告")
            
            self.running = False
            self.logger.info("天气管理器已停止")
            return True
    
    def is_running(self) -> bool:
        """
        检查天气管理器是否在运行
        
        Returns:
            bool: 运行状态
        """
        return self.running
    
    def update_weather(self) -> bool:
        """
        手动更新天气数据
        
        Returns:
            bool: 是否成功更新
        """
        if not self.running:
            self.logger.warning("天气管理器未运行，无法更新天气")
            return False
        
        return self.weather_service.update_weather()
    
    def get_weather(self) -> Optional[Dict[str, Any]]:
        """
        获取当前天气数据
        
        Returns:
            Optional[Dict[str, Any]]: 天气数据，如果没有数据则返回None
        """
        return self.weather_service.get_weather()
    
    def get_formatted_weather(self) -> Dict[str, Any]:
        """
        获取格式化的天气数据，用于显示
        
        Returns:
            Dict[str, Any]: 格式化的天气数据
        """
        return self.weather_display.get_formatted_weather()
    
    def get_weather_summary(self) -> str:
        """
        获取简短的天气摘要
        
        Returns:
            str: 天气摘要文本
        """
        return self.weather_display.get_weather_summary()
    
    def render_widget(self, size: Tuple[int, int] = (200, 100)) -> Dict[str, Any]:
        """
        渲染天气小部件
        
        Args:
            size: 小部件尺寸 (宽, 高)
            
        Returns:
            Dict[str, Any]: 小部件渲染数据
        """
        return self.weather_display.render_widget(size)
    
    def set_city(self, city: str) -> bool:
        """
        设置城市
        
        Args:
            city: 城市名称
            
        Returns:
            bool: 是否成功设置
        """
        return self.weather_service.set_city(city)
    
    def set_units(self, units: str) -> bool:
        """
        设置温度单位
        
        Args:
            units: 温度单位 ('metric' 或 'imperial')
            
        Returns:
            bool: 是否成功设置
        """
        return self.weather_service.set_units(units)
    
    def set_api_key(self, api_key: str) -> bool:
        """
        设置API密钥
        
        Args:
            api_key: API密钥
            
        Returns:
            bool: 是否成功设置
        """
        return self.weather_service.set_api_key(api_key)
    
    def set_refresh_interval(self, interval: int) -> bool:
        """
        设置刷新间隔
        
        Args:
            interval: 刷新间隔（秒）
            
        Returns:
            bool: 是否成功设置
        """
        return self.weather_service.set_refresh_interval(interval)
    
    def set_display_style(self, style: str) -> bool:
        """
        设置显示样式
        
        Args:
            style: 显示样式 ('compact' 或 'detailed')
            
        Returns:
            bool: 是否成功设置
        """
        return self.weather_display.set_display_style(style)
    
    def set_color_scheme(self, scheme: str) -> bool:
        """
        设置颜色方案
        
        Args:
            scheme: 颜色方案 ('default' 或 'dark')
            
        Returns:
            bool: 是否成功设置
        """
        return self.weather_display.set_color_scheme(scheme)
    
    def toggle_animations(self, enabled: bool) -> None:
        """
        开启或关闭动画
        
        Args:
            enabled: 是否启用动画
        """
        self.weather_display.toggle_animations(enabled)
    
    def register_callback(self, event_type: str, callback: Callable) -> bool:
        """
        注册回调函数
        
        Args:
            event_type: 事件类型
            callback: 回调函数
            
        Returns:
            bool: 是否成功注册
        """
        if event_type not in self.callbacks:
            self.logger.warning(f"未知的事件类型: {event_type}")
            return False
        
        self.callbacks[event_type].append(callback)
        self.logger.debug(f"已注册事件 {event_type} 的回调函数")
        return True
    
    def unregister_callback(self, event_type: str, callback: Callable) -> bool:
        """
        取消注册回调函数
        
        Args:
            event_type: 事件类型
            callback: 回调函数
            
        Returns:
            bool: 是否成功取消注册
        """
        if event_type not in self.callbacks:
            self.logger.warning(f"未知的事件类型: {event_type}")
            return False
        
        if callback not in self.callbacks[event_type]:
            self.logger.warning(f"回调函数未注册在事件 {event_type} 中")
            return False
        
        self.callbacks[event_type].remove(callback)
        self.logger.debug(f"已取消注册事件 {event_type} 的回调函数")
        return True
    
    def _trigger_callbacks(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        触发回调函数
        
        Args:
            event_type: 事件类型
            data: 回调数据
        """
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    self.logger.error(f"执行回调函数异常: {e}")
    
    def get_last_updated(self) -> Optional[float]:
        """
        获取最后更新时间戳
        
        Returns:
            Optional[float]: 时间戳，如果没有更新过则返回None
        """
        return self.weather_service.get_last_updated()
    
    def update_config(self, config: Dict[str, Any]) -> bool:
        """
        更新配置
        
        Args:
            config: 新的配置信息
            
        Returns:
            bool: 是否需要重启服务
        """
        # 更新全局配置
        self.config.update(config)
        
        need_restart = False
        
        # 更新服务配置
        if 'service' in config:
            service_config = config['service']
            
            # 检查是否有需要重启服务的配置项
            if any(key in service_config for key in ['api_service', 'api_key']):
                need_restart = True
            
            # 如果管理器正在运行且需要重启
            if self.running and need_restart:
                self.stop()
                # 重新创建服务实例
                self.weather_service = WeatherService(self.config.get('service', {}))
                self._connect_service_display()
                self.start()
            else:
                # 更新不需要重启的配置项
                if 'city' in service_config:
                    self.set_city(service_config['city'])
                if 'units' in service_config:
                    self.set_units(service_config['units'])
                if 'refresh_interval' in service_config:
                    self.set_refresh_interval(service_config['refresh_interval'])
        
        # 更新显示配置
        if 'display' in config:
            display_config = config['display']
            
            # 不需要重启服务的显示配置更新
            if 'display_style' in display_config:
                self.set_display_style(display_config['display_style'])
            if 'color_scheme' in display_config:
                self.set_color_scheme(display_config['color_scheme'])
            if 'animation_enabled' in display_config:
                self.toggle_animations(display_config['animation_enabled'])
        
        self.logger.info("配置已更新" + (" 并重启服务" if need_restart else ""))
        return need_restart 