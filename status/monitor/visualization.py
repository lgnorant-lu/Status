"""
---------------------------------------------------------------
File name:                  visualization.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                可视化映射器，将系统数据映射为视觉元素
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import logging
import time
from typing import Dict, Any, List, Optional, Union, Tuple


class VisualMapper:
    """可视化映射器，负责将处理后的性能数据映射为视觉元素"""
    
    # 默认颜色方案
    DEFAULT_COLOR_SCHEMES = {
        "normal": {
            "primary": "#2ECC40",  # 绿色
            "secondary": "#0074D9",  # 蓝色
            "accent": "#FFDC00",  # 黄色
            "background": "#001f3f",  # 深蓝色
            "text": "#FFFFFF"  # 白色
        },
        "warning": {
            "primary": "#FF851B",  # 橙色
            "secondary": "#FFDC00",  # 黄色
            "accent": "#0074D9",  # 蓝色
            "background": "#FF4136",  # 红色
            "text": "#FFFFFF"  # 白色
        },
        "danger": {
            "primary": "#FF4136",  # 红色
            "secondary": "#FF851B",  # 橙色
            "accent": "#FFDC00",  # 黄色
            "background": "#85144b",  # 深红色
            "text": "#FFFFFF"  # 白色
        }
    }
    
    # 默认动画效果
    DEFAULT_ANIMATIONS = {
        "normal": {
            "speed": 1.0,
            "scale": 1.0,
            "effects": []
        },
        "warning": {
            "speed": 1.2,
            "scale": 1.1,
            "effects": ["pulse"]
        },
        "danger": {
            "speed": 1.5,
            "scale": 1.2,
            "effects": ["pulse", "shake"]
        }
    }
    
    # 默认指示器样式
    DEFAULT_INDICATORS = {
        "cpu": {
            "icon": "cpu",
            "color_map": lambda value: {
                "color": "#2ECC40" if value < 0.7 else "#FF851B" if value < 0.9 else "#FF4136",
                "opacity": 0.7 + value * 0.3
            }
        },
        "memory": {
            "icon": "memory",
            "color_map": lambda value: {
                "color": "#2ECC40" if value < 0.7 else "#FF851B" if value < 0.9 else "#FF4136",
                "opacity": 0.7 + value * 0.3
            }
        },
        "disk": {
            "icon": "hdd",
            "color_map": lambda value: {
                "color": "#2ECC40" if value < 0.8 else "#FF851B" if value < 0.9 else "#FF4136",
                "opacity": 0.7 + value * 0.3
            }
        },
        "network": {
            "icon": "network",
            "color_map": lambda value: {
                "color": "#2ECC40" if value < 0.7 else "#FF851B" if value < 0.9 else "#FF4136",
                "opacity": 0.7 + value * 0.3
            }
        },
        "temperature": {
            "icon": "thermometer",
            "color_map": lambda value: {
                "color": "#2ECC40" if value < 0.6 else "#FF851B" if value < 0.8 else "#FF4136",
                "opacity": 0.7 + value * 0.3
            }
        },
        "battery": {
            "icon": "battery",
            "color_map": lambda value: {
                "color": "#FF4136" if value < 0.2 else "#FF851B" if value < 0.4 else "#2ECC40",
                "opacity": 0.7 + (1 - value) * 0.3
            }
        }
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化可视化映射器
        
        Args:
            config: 映射器配置
        """
        self.config = config or {}
        self.logger = logging.getLogger("VisualMapper")
        
        # 加载颜色方案
        self.color_schemes = self._merge_config(
            self.DEFAULT_COLOR_SCHEMES, 
            self.config.get("color_schemes", {})
        )
        
        # 加载动画配置
        self.animations = self._merge_config(
            self.DEFAULT_ANIMATIONS, 
            self.config.get("animations", {})
        )
        
        # 加载指示器配置
        self.indicators = self.DEFAULT_INDICATORS.copy()
        user_indicators = self.config.get("indicators", {})
        for key, value in user_indicators.items():
            if key in self.indicators:
                # 合并而不是替换
                for inner_key, inner_value in value.items():
                    # 不要替换color_map函数
                    if inner_key != "color_map" or "color_map" not in self.indicators[key]:
                        self.indicators[key][inner_key] = inner_value
            else:
                # 新增指示器
                self.indicators[key] = value
                
        self.logger.info("可视化映射器初始化完成")
        
    def update_config(self, config: Dict[str, Any]) -> None:
        """
        更新映射器配置
        
        Args:
            config: 新配置
        """
        # 更新配置
        self.config.update(config)
        
        # 重新加载颜色方案
        if "color_schemes" in config:
            self.color_schemes = self._merge_config(
                self.DEFAULT_COLOR_SCHEMES, 
                self.config.get("color_schemes", {})
            )
            
        # 重新加载动画配置
        if "animations" in config:
            self.animations = self._merge_config(
                self.DEFAULT_ANIMATIONS, 
                self.config.get("animations", {})
            )
            
        # 重新加载指示器配置
        if "indicators" in config:
            user_indicators = self.config.get("indicators", {})
            for key, value in user_indicators.items():
                if key in self.indicators:
                    # 合并而不是替换
                    for inner_key, inner_value in value.items():
                        # 不要替换color_map函数
                        if inner_key != "color_map" or "color_map" not in self.indicators[key]:
                            self.indicators[key][inner_key] = inner_value
                else:
                    # 新增指示器
                    self.indicators[key] = value
                    
        self.logger.debug(f"更新映射器配置: {list(config.keys())}")
        
    def _merge_config(self, default: Dict, user: Dict) -> Dict:
        """
        合并配置

        Args:
            default: 默认配置
            user: 用户配置

        Returns:
            Dict: 合并后的配置
        """
        result = default.copy()
        
        # 递归合并
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
                
        return result
        
    def map_data(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将处理后的数据映射为视觉元素
        
        Args:
            processed_data: 已处理的数据
            
        Returns:
            Dict: 视觉映射参数
        """
        if not processed_data:
            return {'error': 'No data to map'}
            
        visual_params = {}
        
        # 获取系统整体状态
        overall_status = processed_data.get('system', {}).get('overall_status', 'normal')
        overall_load = processed_data.get('system', {}).get('overall_load', 0.0)
        
        # 基本视觉参数
        visual_params['color_scheme'] = self._get_color_scheme(overall_status)
        visual_params['animation'] = self._get_animation(overall_status, overall_load)
        visual_params['indicators'] = self._get_indicators(processed_data)
        visual_params['effects'] = self._get_effects(processed_data)
        visual_params['tooltips'] = self._get_tooltips(processed_data)
        visual_params['alerts'] = self._get_alerts(processed_data)
        visual_params['timestamp'] = time.time()
        
        # 添加系统状态摘要
        visual_params['summary'] = {
            'status': overall_status,
            'load': overall_load,
            'label': self._get_status_label(overall_status)
        }
        
        return visual_params
        
    def _get_color_scheme(self, status: str) -> Dict[str, str]:
        """
        获取对应状态的颜色方案
        
        Args:
            status: 状态 (normal, warning, danger)
            
        Returns:
            Dict: 颜色方案
        """
        # 获取对应状态的颜色方案，如果不存在则使用normal
        if status in self.color_schemes:
            return self.color_schemes[status]
        else:
            return self.color_schemes["normal"]
            
    def _get_animation(self, status: str, load: float) -> Dict[str, Any]:
        """
        获取动画参数
        
        Args:
            status: 状态 (normal, warning, danger)
            load: 负载水平 (0.0-1.0)
            
        Returns:
            Dict: 动画参数
        """
        if status not in self.animations:
            status = "normal"
            
        # 获取基础动画配置
        animation = self.animations[status].copy()
        
        # 根据负载调整速度
        animation["speed"] *= (0.8 + load * 0.4)
        
        # 根据负载调整缩放
        animation["scale"] *= (0.9 + load * 0.2)
        
        return animation
        
    def _get_indicators(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取指示器参数
        
        Args:
            data: 处理后的数据
            
        Returns:
            Dict: 指示器参数
        """
        result = {}
        
        # CPU指示器
        if 'cpu' in data:
            cpu_data = data['cpu']
            cpu_usage = cpu_data.get('usage', 0) / 100.0 if 'usage' in cpu_data else 0
            
            result['cpu'] = {
                'value': cpu_usage,
                'icon': self.indicators['cpu']['icon'],
                'visual': self.indicators['cpu']['color_map'](cpu_usage),
                'trend': cpu_data.get('trend', 'stable')
            }
            
        # 内存指示器
        if 'memory' in data:
            memory_data = data['memory']
            memory_usage = memory_data.get('percent', 0) / 100.0 if 'percent' in memory_data else 0
            
            result['memory'] = {
                'value': memory_usage,
                'icon': self.indicators['memory']['icon'],
                'visual': self.indicators['memory']['color_map'](memory_usage),
                'trend': memory_data.get('trend', 'stable')
            }
            
        # 磁盘指示器
        if 'disk' in data:
            disk_data = data['disk']
            disk_usage = disk_data.get('percent', 0) / 100.0 if 'percent' in disk_data else 0
            
            result['disk'] = {
                'value': disk_usage,
                'icon': self.indicators['disk']['icon'],
                'visual': self.indicators['disk']['color_map'](disk_usage),
                'trend': disk_data.get('trend', 'stable')
            }
            
            # 添加磁盘IO指示器
            io_data = disk_data.get('io', {})
            if io_data:
                read_speed = io_data.get('read_mb_per_sec', 0)
                write_speed = io_data.get('write_mb_per_sec', 0)
                io_activity = min(1.0, (read_speed + write_speed) / 20.0)  # 假设20MB/s是满活动
                
                result['disk_io'] = {
                    'value': io_activity,
                    'read': read_speed,
                    'write': write_speed,
                    'visual': {
                        'color': '#0074D9',
                        'opacity': 0.7 + io_activity * 0.3
                    }
                }
                
        # 网络指示器
        if 'network' in data:
            network_data = data['network']
            upload = network_data.get('upload_mb_per_sec', 0)
            download = network_data.get('download_mb_per_sec', 0)
            network_load = network_data.get('network_load', 0)
            
            result['network'] = {
                'value': network_load,
                'icon': self.indicators['network']['icon'],
                'visual': self.indicators['network']['color_map'](network_load),
                'upload': upload,
                'download': download,
                'upload_trend': network_data.get('upload_trend', 'stable'),
                'download_trend': network_data.get('download_trend', 'stable')
            }
            
        return result
        
    def _get_effects(self, data: Dict[str, Any]) -> List[str]:
        """
        获取特效列表
        
        Args:
            data: 处理后的数据
            
        Returns:
            List[str]: 特效列表
        """
        effects = []
        
        # CPU高负载特效
        if 'cpu' in data and 'usage' in data['cpu']:
            cpu_usage = data['cpu']['usage']
            if cpu_usage > 90:
                effects.append('cpu_critical')
            elif cpu_usage > 75:
                effects.append('cpu_high')
                
        # 磁盘IO特效
        if 'disk' in data and 'io' in data['disk']:
            io_data = data['disk']['io']
            read_speed = io_data.get('read_mb_per_sec', 0)
            write_speed = io_data.get('write_mb_per_sec', 0)
            
            if read_speed > 10 or write_speed > 10:
                effects.append('disk_active')
                
        # 网络活动特效
        if 'network' in data:
            network_data = data['network']
            upload = network_data.get('upload_mb_per_sec', 0)
            download = network_data.get('download_mb_per_sec', 0)
            
            if upload > 2:
                effects.append('network_upload')
            if download > 2:
                effects.append('network_download')
                
        # 系统状态特效
        overall_status = data.get('system', {}).get('overall_status', 'normal')
        if overall_status == 'warning':
            effects.append('system_warning')
        elif overall_status == 'danger':
            effects.append('system_danger')
            
        return effects
        
    def _get_tooltips(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        生成提示文本
        
        Args:
            data: 处理后的数据
            
        Returns:
            Dict[str, str]: 提示文本
        """
        tooltips = {}
        
        # CPU提示
        if 'cpu' in data:
            cpu_data = data['cpu']
            if 'usage' in cpu_data:
                tooltips['cpu'] = f"CPU使用率: {cpu_data['usage']:.1f}%"
                
                if 'load_avg_1min' in cpu_data:
                    tooltips['cpu'] += f"\n负载: {cpu_data['load_avg_1min']:.2f}"
                    
        # 内存提示
        if 'memory' in data:
            memory_data = data['memory']
            if 'percent' in memory_data:
                if 'total_gb' in memory_data and 'used_gb' in memory_data:
                    tooltips['memory'] = f"内存使用率: {memory_data['percent']:.1f}%\n已用: {memory_data['used_gb']:.1f}GB / 总共: {memory_data['total_gb']:.1f}GB"
                else:
                    tooltips['memory'] = f"内存使用率: {memory_data['percent']:.1f}%"
                    
        # 磁盘提示
        if 'disk' in data:
            disk_data = data['disk']
            if 'percent' in disk_data:
                if 'total_gb' in disk_data and 'used_gb' in disk_data:
                    tooltips['disk'] = f"磁盘使用率: {disk_data['percent']:.1f}%\n已用: {disk_data['used_gb']:.1f}GB / 总共: {disk_data['total_gb']:.1f}GB"
                else:
                    tooltips['disk'] = f"磁盘使用率: {disk_data['percent']:.1f}%"
                    
            # 磁盘IO提示
            io_data = disk_data.get('io', {})
            if io_data:
                read_speed = io_data.get('read_mb_per_sec', 0)
                write_speed = io_data.get('write_mb_per_sec', 0)
                tooltips['disk_io'] = f"读取: {read_speed:.2f}MB/s\n写入: {write_speed:.2f}MB/s"
                
        # 网络提示
        if 'network' in data:
            network_data = data['network']
            upload = network_data.get('upload_mb_per_sec', 0)
            download = network_data.get('download_mb_per_sec', 0)
            tooltips['network'] = f"上传: {upload:.2f}MB/s\n下载: {download:.2f}MB/s"
            
            if 'connections' in network_data:
                tooltips['network'] += f"\n连接数: {network_data['connections']}"
                
        # 系统提示
        if 'system' in data:
            system_data = data['system']
            if 'overall_status' in system_data:
                status_label = self._get_status_label(system_data['overall_status'])
                tooltips['system'] = f"系统状态: {status_label}"
                
                if 'uptime_formatted' in system_data:
                    tooltips['system'] += f"\n运行时间: {system_data['uptime_formatted']}"
                    
        return tooltips
        
    def _get_alerts(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成告警信息
        
        Args:
            data: 处理后的数据
            
        Returns:
            List[Dict[str, Any]]: 告警信息列表
        """
        alerts = []
        
        # CPU告警
        if 'cpu' in data:
            cpu_data = data['cpu']
            if 'status' in cpu_data and cpu_data['status'] in ('warning', 'danger'):
                alert = {
                    'type': 'cpu',
                    'level': cpu_data['status'],
                    'message': f"CPU使用率 ({cpu_data.get('usage', 0):.1f}%) 过高",
                    'timestamp': time.time()
                }
                alerts.append(alert)
                
        # 内存告警
        if 'memory' in data:
            memory_data = data['memory']
            if 'status' in memory_data and memory_data['status'] in ('warning', 'danger'):
                alert = {
                    'type': 'memory',
                    'level': memory_data['status'],
                    'message': f"内存使用率 ({memory_data.get('percent', 0):.1f}%) 过高",
                    'timestamp': time.time()
                }
                alerts.append(alert)
                
        # 磁盘告警
        if 'disk' in data:
            disk_data = data['disk']
            if 'status' in disk_data and disk_data['status'] in ('warning', 'danger'):
                alert = {
                    'type': 'disk',
                    'level': disk_data['status'],
                    'message': f"磁盘使用率 ({disk_data.get('percent', 0):.1f}%) 过高",
                    'timestamp': time.time()
                }
                alerts.append(alert)
                
            # 检查分区
            partitions = disk_data.get('partitions', {})
            for mount, partition_data in partitions.items():
                if 'status' in partition_data and partition_data['status'] in ('warning', 'danger'):
                    alert = {
                        'type': 'disk_partition',
                        'level': partition_data['status'],
                        'message': f"分区 {mount} 使用率 ({partition_data.get('percent', 0):.1f}%) 过高",
                        'timestamp': time.time()
                    }
                    alerts.append(alert)
                    
        # 网络告警
        if 'network' in data:
            network_data = data['network']
            if 'status' in network_data and network_data['status'] in ('warning', 'danger'):
                alert = {
                    'type': 'network',
                    'level': network_data['status'],
                    'message': "网络流量过高",
                    'timestamp': time.time()
                }
                alerts.append(alert)
                
        return alerts
        
    def _get_status_label(self, status: str) -> str:
        """
        获取状态的文本标签
        
        Args:
            status: 状态 (normal, warning, danger)
            
        Returns:
            str: 状态文本
        """
        status_labels = {
            'normal': '正常',
            'warning': '警告',
            'danger': '危险',
            'unknown': '未知'
        }
        
        return status_labels.get(status, '未知')
        
    def get_color_for_metric(self, metric_name: str, value: float) -> str:
        """
        获取指标对应的颜色
        
        Args:
            metric_name: 指标名称
            value: 指标值 (0.0-1.0)
            
        Returns:
            str: 十六进制颜色代码
        """
        if metric_name in self.indicators:
            return self.indicators[metric_name]['color_map'](value)['color']
        else:
            # 默认颜色映射
            return "#2ECC40" if value < 0.7 else "#FF851B" if value < 0.9 else "#FF4136"
            
    def get_animation_for_status(self, status: str) -> Dict[str, Any]:
        """
        获取状态对应的动画配置
        
        Args:
            status: 状态 (normal, warning, danger)
            
        Returns:
            Dict: 动画配置
        """
        if status in self.animations:
            return self.animations[status].copy()
        else:
            return self.animations["normal"].copy()
            
    def get_color_scheme(self, status: str) -> Dict[str, str]:
        """
        获取状态对应的颜色方案
        
        Args:
            status: 状态 (normal, warning, danger)
            
        Returns:
            Dict: 颜色方案
        """
        if status in self.color_schemes:
            return self.color_schemes[status].copy()
        else:
            return self.color_schemes["normal"].copy() 