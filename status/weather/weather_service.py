"""
---------------------------------------------------------------
File name:                  weather_service.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                天气服务，负责获取天气数据
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""
import logging
import time
import threading
import requests
from typing import Dict, Any, Optional, List, Callable, Union

class WeatherService:
    """天气服务类，负责从API获取天气数据"""
    
    # 默认支持的天气API服务
    SUPPORTED_APIS = {
        'openweathermap': {
            'url': 'https://api.openweathermap.org/data/2.5/weather',
            'params': {
                'q': '{city}',
                'appid': '{api_key}',
                'units': '{units}',
                'lang': '{lang}'
            }
        },
        'weatherapi': {
            'url': 'https://api.weatherapi.com/v1/current.json',
            'params': {
                'q': '{city}',
                'key': '{api_key}',
                'lang': '{lang}'
            }
        }
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化天气服务
        
        Args:
            config: 配置信息，包括API密钥、城市、刷新间隔等
        """
        self.logger = logging.getLogger("WeatherService")
        self.config = config or {}
        
        # 天气API配置
        self.api_service = self.config.get('api_service', 'openweathermap')
        self.api_key = self.config.get('api_key', '')
        self.city = self.config.get('city', 'Beijing')
        self.units = self.config.get('units', 'metric')  # metric 或 imperial
        self.lang = self.config.get('lang', 'zh_cn')
        
        # 自动刷新配置
        self.auto_refresh = self.config.get('auto_refresh', True)
        self.refresh_interval = self.config.get('refresh_interval', 3600)  # 默认1小时刷新一次
        
        # 天气数据缓存
        self.weather_data = None
        self.last_updated = None
        self.is_updating = False
        self.update_lock = threading.Lock()
        
        # 回调函数
        self.callbacks: Dict[str, List[Callable]] = {
            'on_weather_updated': [],
            'on_weather_error': []
        }
        
        # 自动刷新线程
        self.refresh_thread = None
        self.running = False
        
        # 天气图标映射
        self.icon_mapping = {
            # OpenWeatherMap图标映射
            '01d': 'clear_day',
            '01n': 'clear_night',
            '02d': 'partly_cloudy_day',
            '02n': 'partly_cloudy_night',
            '03d': 'cloudy',
            '03n': 'cloudy',
            '04d': 'cloudy',
            '04n': 'cloudy',
            '09d': 'rain',
            '09n': 'rain',
            '10d': 'rain_day',
            '10n': 'rain_night',
            '11d': 'thunderstorm',
            '11n': 'thunderstorm',
            '13d': 'snow',
            '13n': 'snow',
            '50d': 'fog',
            '50n': 'fog',
            
            # WeatherAPI图标映射
            'sunny': 'clear_day',
            'clear': 'clear_night',
            'partly-cloudy': 'partly_cloudy_day',
            'partly-cloudy-night': 'partly_cloudy_night',
            'cloudy': 'cloudy',
            'overcast': 'cloudy',
            'mist': 'fog',
            'fog': 'fog',
            'rain': 'rain',
            'snow': 'snow',
            'sleet': 'snow',
            'thunderstorm': 'thunderstorm'
        }
        
        self.logger.info(f"天气服务初始化完成，城市：{self.city}，API服务：{self.api_service}")
    
    def start(self) -> bool:
        """
        启动天气服务
        
        Returns:
            bool: 是否成功启动
        """
        if self.running:
            self.logger.warning("天气服务已在运行中")
            return False
        
        if not self.api_key:
            self.logger.error("未配置API密钥，无法启动天气服务")
            self._trigger_callbacks('on_weather_error', {'error': '未配置API密钥'})
            return False
        
        self.running = True
        
        # 立即更新一次天气
        self.update_weather()
        
        # 如果启用自动刷新，启动刷新线程
        if self.auto_refresh:
            self.refresh_thread = threading.Thread(target=self._refresh_loop, daemon=True)
            self.refresh_thread.start()
            self.logger.info(f"天气服务自动刷新已启动，间隔：{self.refresh_interval}秒")
        
        self.logger.info("天气服务已启动")
        return True
    
    def stop(self) -> bool:
        """
        停止天气服务
        
        Returns:
            bool: 是否成功停止
        """
        if not self.running:
            self.logger.warning("天气服务未在运行")
            return False
        
        self.running = False
        
        # 等待刷新线程结束
        if self.refresh_thread and self.refresh_thread.is_alive():
            self.refresh_thread.join(timeout=2)
            self.refresh_thread = None
        
        self.logger.info("天气服务已停止")
        return True
    
    def is_running(self) -> bool:
        """
        检查天气服务是否在运行
        
        Returns:
            bool: 服务运行状态
        """
        return self.running
    
    def _refresh_loop(self) -> None:
        """天气自动刷新循环"""
        while self.running:
            try:
                # 计算下次更新时间
                if self.last_updated:
                    elapsed = time.time() - self.last_updated
                    if elapsed < self.refresh_interval:
                        # 等待剩余时间
                        wait_time = max(1, self.refresh_interval - elapsed)
                        time.sleep(wait_time)
                
                # 更新天气
                if self.running:  # 再次检查，防止在等待期间服务被停止
                    self.update_weather()
                    
            except Exception as e:
                self.logger.error(f"天气刷新循环异常: {e}")
                self._trigger_callbacks('on_weather_error', {'error': str(e)})
                time.sleep(60)  # 发生异常，等待一分钟后重试
    
    def update_weather(self) -> bool:
        """
        更新天气数据
        
        Returns:
            bool: 是否成功更新
        """
        with self.update_lock:
            if self.is_updating:
                self.logger.debug("已有更新操作在进行中")
                return False
            
            self.is_updating = True
        
        try:
            self.logger.debug(f"开始更新天气数据，城市：{self.city}")
            
            # 根据配置的API服务构建请求
            if self.api_service in self.SUPPORTED_APIS:
                api_config = self.SUPPORTED_APIS[self.api_service]
                url = api_config['url']
                
                # 构建参数
                params = {}
                for key, value in api_config['params'].items():
                    if '{api_key}' in value:
                        params[key] = value.replace('{api_key}', self.api_key)
                    elif '{city}' in value:
                        params[key] = value.replace('{city}', self.city)
                    elif '{units}' in value:
                        params[key] = value.replace('{units}', self.units)
                    elif '{lang}' in value:
                        params[key] = value.replace('{lang}', self.lang)
                    else:
                        params[key] = value
                
                # 发送请求
                self.logger.debug(f"发送天气API请求：{url}")
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    # 解析响应数据
                    raw_data = response.json()
                    
                    # 根据API服务解析数据
                    if self.api_service == 'openweathermap':
                        weather_data = self._parse_openweathermap_data(raw_data)
                    elif self.api_service == 'weatherapi':
                        weather_data = self._parse_weatherapi_data(raw_data)
                    else:
                        weather_data = raw_data  # 未知API服务，直接返回原始数据
                    
                    # 更新缓存数据
                    self.weather_data = weather_data
                    self.last_updated = time.time()
                    
                    self.logger.info(f"天气数据更新成功：{self.city}, "
                                    f"{weather_data.get('temperature')}°{weather_data.get('temperature_unit')}, "
                                    f"{weather_data.get('description')}")
                    
                    # 触发回调
                    self._trigger_callbacks('on_weather_updated', {'weather': weather_data})
                    return True
                else:
                    error_msg = f"天气API请求失败，状态码：{response.status_code}，错误：{response.text}"
                    self.logger.error(error_msg)
                    self._trigger_callbacks('on_weather_error', {'error': error_msg})
                    return False
            else:
                error_msg = f"不支持的API服务：{self.api_service}"
                self.logger.error(error_msg)
                self._trigger_callbacks('on_weather_error', {'error': error_msg})
                return False
            
        except Exception as e:
            error_msg = f"更新天气数据异常：{str(e)}"
            self.logger.error(error_msg)
            self._trigger_callbacks('on_weather_error', {'error': error_msg})
            return False
        
        finally:
            with self.update_lock:
                self.is_updating = False
    
    def _parse_openweathermap_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析OpenWeatherMap API的数据
        
        Args:
            data: API返回的原始数据
            
        Returns:
            Dict[str, Any]: 格式化的天气数据
        """
        try:
            weather = data.get('weather', [{}])[0]
            main = data.get('main', {})
            wind = data.get('wind', {})
            sys = data.get('sys', {})
            
            # 获取天气图标
            icon_code = weather.get('icon', '')
            icon = self.icon_mapping.get(icon_code, 'unknown')
            
            # 构建统一格式的天气数据
            weather_data = {
                'city': data.get('name', self.city),
                'country': sys.get('country', ''),
                'description': weather.get('description', ''),
                'temperature': main.get('temp', 0),
                'temperature_unit': 'C' if self.units == 'metric' else 'F',
                'feels_like': main.get('feels_like', 0),
                'humidity': main.get('humidity', 0),
                'pressure': main.get('pressure', 0),
                'wind_speed': wind.get('speed', 0),
                'wind_direction': wind.get('deg', 0),
                'cloudiness': data.get('clouds', {}).get('all', 0),
                'visibility': data.get('visibility', 0),
                'sunrise': sys.get('sunrise', 0),
                'sunset': sys.get('sunset', 0),
                'weather_code': weather.get('id', 0),
                'weather_icon': icon,
                'weather_main': weather.get('main', ''),
                'raw_data': data,
                'source': 'openweathermap',
                'timestamp': time.time()
            }
            
            return weather_data
            
        except Exception as e:
            self.logger.error(f"解析OpenWeatherMap数据异常：{e}")
            return {
                'error': str(e),
                'source': 'openweathermap',
                'timestamp': time.time(),
                'raw_data': data
            }
    
    def _parse_weatherapi_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析WeatherAPI的数据
        
        Args:
            data: API返回的原始数据
            
        Returns:
            Dict[str, Any]: 格式化的天气数据
        """
        try:
            location = data.get('location', {})
            current = data.get('current', {})
            condition = current.get('condition', {})
            
            # 获取天气图标
            icon_code = condition.get('code', '')
            icon_text = condition.get('text', '').lower().replace(' ', '-')
            icon = self.icon_mapping.get(icon_text, 'unknown')
            
            # 构建统一格式的天气数据
            weather_data = {
                'city': location.get('name', self.city),
                'country': location.get('country', ''),
                'description': condition.get('text', ''),
                'temperature': current.get('temp_c' if self.units == 'metric' else 'temp_f', 0),
                'temperature_unit': 'C' if self.units == 'metric' else 'F',
                'feels_like': current.get('feelslike_c' if self.units == 'metric' else 'feelslike_f', 0),
                'humidity': current.get('humidity', 0),
                'pressure': current.get('pressure_mb', 0),
                'wind_speed': current.get('wind_kph' if self.units == 'metric' else 'wind_mph', 0),
                'wind_direction': current.get('wind_degree', 0),
                'cloudiness': current.get('cloud', 0),
                'visibility': current.get('vis_km' if self.units == 'metric' else 'vis_miles', 0),
                'weather_code': condition.get('code', 0),
                'weather_icon': icon,
                'weather_main': condition.get('text', ''),
                'is_day': current.get('is_day', 1) == 1,
                'raw_data': data,
                'source': 'weatherapi',
                'timestamp': time.time()
            }
            
            return weather_data
            
        except Exception as e:
            self.logger.error(f"解析WeatherAPI数据异常：{e}")
            return {
                'error': str(e),
                'source': 'weatherapi',
                'timestamp': time.time(),
                'raw_data': data
            }
    
    def get_weather(self) -> Optional[Dict[str, Any]]:
        """
        获取当前天气数据
        
        Returns:
            Optional[Dict[str, Any]]: 天气数据，如果没有数据则返回None
        """
        return self.weather_data
    
    def get_last_updated(self) -> Optional[float]:
        """
        获取最后更新时间戳
        
        Returns:
            Optional[float]: 时间戳，如果没有更新过则返回None
        """
        return self.last_updated
    
    def set_city(self, city: str) -> bool:
        """
        设置城市
        
        Args:
            city: 城市名称
            
        Returns:
            bool: 是否成功设置
        """
        if not city:
            self.logger.error("城市名称不能为空")
            return False
        
        self.city = city
        self.logger.info(f"已设置城市：{city}")
        
        # 立即更新天气
        if self.running:
            return self.update_weather()
        
        return True
    
    def set_units(self, units: str) -> bool:
        """
        设置温度单位
        
        Args:
            units: 温度单位 ('metric' 或 'imperial')
            
        Returns:
            bool: 是否成功设置
        """
        if units not in ['metric', 'imperial']:
            self.logger.error(f"不支持的温度单位：{units}，应为 'metric' 或 'imperial'")
            return False
        
        self.units = units
        self.logger.info(f"已设置温度单位：{units}")
        
        # 立即更新天气
        if self.running:
            return self.update_weather()
        
        return True
    
    def set_api_key(self, api_key: str) -> bool:
        """
        设置API密钥
        
        Args:
            api_key: API密钥
            
        Returns:
            bool: 是否成功设置
        """
        if not api_key:
            self.logger.error("API密钥不能为空")
            return False
        
        self.api_key = api_key
        self.logger.info("已设置API密钥")
        
        # 如果服务已运行，重启服务
        was_running = self.running
        if was_running:
            self.stop()
        
        if was_running:
            return self.start()
        
        return True
    
    def set_refresh_interval(self, interval: int) -> bool:
        """
        设置刷新间隔
        
        Args:
            interval: 刷新间隔（秒）
            
        Returns:
            bool: 是否成功设置
        """
        if interval < 60:
            self.logger.warning(f"刷新间隔过短 ({interval}秒)，已自动调整为60秒")
            interval = 60
        
        self.refresh_interval = interval
        self.logger.info(f"已设置刷新间隔：{interval}秒")
        
        return True
    
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