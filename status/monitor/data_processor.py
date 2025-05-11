"""
---------------------------------------------------------------
File name:                  data_processor.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                数据处理器，处理和分析系统性能数据
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import logging
import time
import math
from typing import Dict, Any, List, Optional, Union, Tuple


class DataProcessor:
    """数据处理器，负责处理和分析系统性能数据"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化数据处理器
        
        Args:
            config: 处理器配置
        """
        self.config = config or {}
        self.logger = logging.getLogger("DataProcessor")
        
        # 设置默认配置值
        if "enable_trends" not in self.config:
            self.config["enable_trends"] = True
        if "enable_predictions" not in self.config:
            self.config["enable_predictions"] = False
        if "smoothing_window" not in self.config:
            self.config["smoothing_window"] = 3
        if "max_history_size" not in self.config:
            self.config["max_history_size"] = 60
        if "threshold_values" not in self.config:
            self.config["threshold_values"] = {
                "cpu_warning": 70.0,
                "cpu_danger": 90.0,
                "memory_warning": 70.0,
                "memory_danger": 85.0,
                "disk_warning": 80.0,
                "disk_danger": 90.0
            }
            
        # 初始化历史数据
        self.history = {
            'cpu': {'usage': []},
            'memory': {'percent': []},
            'disk': {'percent': []},
            'network': {'bytes_sent_rate': [], 'bytes_recv_rate': []}
        }
        
        self.logger.info("数据处理器初始化完成")
        
    def update_config(self, config: Dict[str, Any]) -> None:
        """
        更新处理器配置
        
        Args:
            config: 新配置
        """
        # 合并配置
        for key, value in config.items():
            if key == "threshold_values" and isinstance(value, dict) and "threshold_values" in self.config:
                # 合并阈值，不替换整个字典
                self.config["threshold_values"].update(value)
            else:
                self.config[key] = value
                
        self.logger.debug(f"更新处理器配置: {list(config.keys())}")
        
    def _process_cpu_data(self, cpu_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理CPU数据
        
        Args:
            cpu_data: 原始CPU数据
            
        Returns:
            Dict: 处理后的CPU数据
        """
        if not cpu_data:
            return {'error': 'No CPU data available'}
            
        result = cpu_data.copy()
        
        # 计算CPU状态
        if 'usage' in result:
            thresholds = self.config.get("threshold_values", {})
            warning = thresholds.get("cpu_warning", 70.0)
            danger = thresholds.get("cpu_danger", 90.0)
            
            result['status'] = self._calculate_status(result['usage'], warning, danger)
            result['load_level'] = self._normalize_value(result['usage'], 0, 100)
            
            # 处理每个核心的数据
            if 'per_core' in result:
                core_statuses = []
                for core_usage in result['per_core']:
                    core_statuses.append(self._calculate_status(core_usage, warning, danger))
                result['core_statuses'] = core_statuses
                
            # 添加CPU负载指标
            if 'load_avg_1min' in result:
                core_count = result.get('physical_core_count', result.get('core_count', 1))
                load_percentage = (result['load_avg_1min'] / core_count) * 100
                result['load_percentage'] = load_percentage
                result['load_status'] = self._calculate_status(load_percentage, warning, danger)
                
        return result
        
    def _process_memory_data(self, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理内存数据
        
        Args:
            memory_data: 原始内存数据
            
        Returns:
            Dict: 处理后的内存数据
        """
        if not memory_data:
            return {'error': 'No memory data available'}
            
        result = {}
        
        # 处理虚拟内存
        result['virtual'] = {}
        if 'total' in memory_data:
            result['virtual']['total_gb'] = memory_data['total'] / (1024 ** 3)
        else:
            result['virtual']['total_gb'] = 0.0
            
        if 'used' in memory_data:
            result['virtual']['used_gb'] = memory_data['used'] / (1024 ** 3)
        else:
            result['virtual']['used_gb'] = 0.0
            
        if 'available' in memory_data:
            result['virtual']['available_gb'] = memory_data['available'] / (1024 ** 3)
        else:
            result['virtual']['available_gb'] = 0.0
            
        if 'percent' in memory_data:
            result['virtual']['percent'] = memory_data['percent']
        else:
            result['virtual']['percent'] = 0
            
        # 处理交换内存
        result['swap'] = {}
        if 'swap_total' in memory_data:
            result['swap']['total_gb'] = memory_data['swap_total'] / (1024 ** 3)
        else:
            result['swap']['total_gb'] = 0.0
            
        if 'swap_used' in memory_data:
            result['swap']['used_gb'] = memory_data['swap_used'] / (1024 ** 3)
        else:
            result['swap']['used_gb'] = 0.0
            
        if 'swap_percent' in memory_data:
            result['swap']['percent'] = memory_data['swap_percent']
        else:
            result['swap']['percent'] = 0
            
        # 计算内存状态
        if 'percent' in memory_data:
            thresholds = self.config.get("threshold_values", {})
            warning = thresholds.get("memory_warning", 70.0)
            danger = thresholds.get("memory_danger", 85.0)
            
            result['status'] = self._calculate_status(memory_data['percent'], warning, danger)
            result['usage_level'] = self._normalize_value(memory_data['percent'], 0, 100)
            result['percent'] = memory_data['percent']
            
            if 'total' in memory_data and 'used' in memory_data:
                result['total_gb'] = memory_data['total'] / (1024 ** 3)
                result['used_gb'] = memory_data['used'] / (1024 ** 3)
                result['free_gb'] = result['total_gb'] - result['used_gb']
                
        return result
        
    def _process_disk_data(self, disk_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理磁盘数据
        
        Args:
            disk_data: 原始磁盘数据
            
        Returns:
            Dict: 处理后的磁盘数据
        """
        if not disk_data:
            return {'error': 'No disk data available'}
            
        result = {}
        
        # 处理分区数据
        result['partitions'] = {}
        if 'partitions' in disk_data:
            for mount, data in disk_data['partitions'].items():
                result['partitions'][mount] = {
                    'total_gb': data['total'] / (1024 ** 3),
                    'used_gb': data['used'] / (1024 ** 3),
                    'free_gb': data['free'] / (1024 ** 3),
                    'percent': data['percent']
                }
                
                # 计算分区状态
                thresholds = self.config.get("threshold_values", {})
                warning = thresholds.get("disk_warning", 80.0)
                danger = thresholds.get("disk_danger", 90.0)
                
                result['partitions'][mount]['status'] = self._calculate_status(data['percent'], warning, danger)
                
        # 处理磁盘IO数据
        result['io'] = {}
        if 'io_read' in disk_data and 'io_write' in disk_data:
            result['io']['read_mb'] = disk_data['io_read'] / (1024 * 1024)
            result['io']['write_mb'] = disk_data['io_write'] / (1024 * 1024)
            
        if 'io_read_rate' in disk_data and 'io_write_rate' in disk_data:
            result['io']['read_mb_per_sec'] = disk_data['io_read_rate'] / (1024 * 1024)
            result['io']['write_mb_per_sec'] = disk_data['io_write_rate'] / (1024 * 1024)
        else:
            result['io']['read_mb_per_sec'] = 0.0
            result['io']['write_mb_per_sec'] = 0.0
            
        # 计算磁盘状态
        if 'percent' in disk_data:
            thresholds = self.config.get("threshold_values", {})
            warning = thresholds.get("disk_warning", 80.0)
            danger = thresholds.get("disk_danger", 90.0)
            
            result['status'] = self._calculate_status(disk_data['percent'], warning, danger)
            result['usage_level'] = self._normalize_value(disk_data['percent'], 0, 100)
            result['percent'] = disk_data['percent']
            
            if 'total' in disk_data and 'used' in disk_data:
                result['total_gb'] = disk_data['total'] / (1024 ** 3)
                result['used_gb'] = disk_data['used'] / (1024 ** 3)
                result['free_gb'] = result['total_gb'] - result['used_gb']
                
        # 找出使用率最高的分区
        max_usage = 0
        if 'partitions' in result:
            for mount, data in result['partitions'].items():
                if data['percent'] > max_usage:
                    max_usage = data['percent']
                    
        result['max_usage_percent'] = max_usage
        
        return result
        
    def _process_network_data(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理网络数据
        
        Args:
            network_data: 原始网络数据
            
        Returns:
            Dict: 处理后的网络数据
        """
        if not network_data:
            return {'error': 'No network data available'}
            
        result = {}
        
        # 计算网络流量
        upload_mb_per_sec = 0.0
        download_mb_per_sec = 0.0
        
        if 'bytes_sent_rate' in network_data:
            upload_mb_per_sec = network_data['bytes_sent_rate'] / (1024 * 1024)
            result['upload_mb_per_sec'] = upload_mb_per_sec
        else:
            result['upload_mb_per_sec'] = 0.0
            
        if 'bytes_recv_rate' in network_data:
            download_mb_per_sec = network_data['bytes_recv_rate'] / (1024 * 1024)
            result['download_mb_per_sec'] = download_mb_per_sec
        else:
            result['download_mb_per_sec'] = 0.0
            
        # 计算总体网络负载
        max_expected_throughput = 12.5  # 预期最大吞吐量，100Mbps = 12.5MB/s
        network_load = (upload_mb_per_sec + download_mb_per_sec) / max_expected_throughput
        network_load = min(1.0, network_load)  # 限制在0-1范围内
        
        result['network_load'] = network_load
        
        # 添加连接数
        if 'connections' in network_data:
            result['connections'] = network_data['connections']
            
        # 计算网络状态
        status = "normal"
        if network_load > 0.7:
            status = "warning"
        if network_load > 0.9:
            status = "danger"
            
        result['status'] = status
        
        # 添加接口数据
        if 'interfaces' in network_data:
            result['interfaces'] = {}
            for name, data in network_data['interfaces'].items():
                result['interfaces'][name] = {
                    'addresses': data.get('addresses', []),
                    'speed': data.get('speed', 0),
                    'up': data.get('up', False)
                }
                
        return result
        
    def _process_system_data(self, system_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理系统数据
        
        Args:
            system_data: 原始系统数据
            
        Returns:
            Dict: 处理后的系统数据
        """
        if not system_data:
            return {'error': 'No system data available'}
            
        result = system_data.copy()
        
        # 格式化运行时间
        if 'uptime' in result:
            uptime_seconds = result['uptime']
            
            # 计算天时分秒
            days = uptime_seconds // 86400
            uptime_seconds %= 86400
            hours = uptime_seconds // 3600
            uptime_seconds %= 3600
            minutes = uptime_seconds // 60
            seconds = uptime_seconds % 60
            
            result['uptime_formatted'] = f"{int(days)}天 {int(hours)}小时 {int(minutes)}分钟 {int(seconds)}秒"
            
        # 格式化启动时间
        if 'boot_time' in result:
            boot_time = result['boot_time']
            boot_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(boot_time))
            result['boot_time_formatted'] = boot_time_str
            
        return result
        
    def _calculate_system_status(self, data: Dict[str, Any]) -> Tuple[str, float]:
        """
        计算系统整体状态
        
        Args:
            data: 处理后的各项指标数据
            
        Returns:
            Tuple[str, float]: 状态和负载水平
        """
        # 获取各项指标的状态
        cpu_status = data.get('cpu', {}).get('status', 'unknown')
        memory_status = data.get('memory', {}).get('status', 'unknown')
        disk_status = data.get('disk', {}).get('status', 'unknown')
        network_status = data.get('network', {}).get('status', 'unknown')
        
        # 计算整体状态（取最严重的状态）
        status_priority = {
            'unknown': 0,
            'normal': 1,
            'warning': 2,
            'danger': 3
        }
        
        statuses = [cpu_status, memory_status, disk_status, network_status]
        max_priority = max([status_priority.get(status, 0) for status in statuses])
        
        overall_status = 'unknown'
        for status, priority in status_priority.items():
            if priority == max_priority:
                overall_status = status
                break
                
        # 计算整体负载（取加权平均值）
        cpu_load = data.get('cpu', {}).get('load_level', 0.0)
        memory_load = data.get('memory', {}).get('usage_level', 0.0)
        disk_load = data.get('disk', {}).get('usage_level', 0.0)
        network_load = data.get('network', {}).get('network_load', 0.0)
        
        # 权重
        weights = {
            'cpu': 0.35,
            'memory': 0.35,
            'disk': 0.2,
            'network': 0.1
        }
        
        overall_load = (
            cpu_load * weights['cpu'] +
            memory_load * weights['memory'] +
            disk_load * weights['disk'] +
            network_load * weights['network']
        )
        
        return overall_status, overall_load
        
    def _calculate_status(self, value: float, warning_threshold: float, danger_threshold: float) -> str:
        """
        根据阈值计算状态
        
        Args:
            value: 当前值
            warning_threshold: 警告阈值
            danger_threshold: 危险阈值
            
        Returns:
            str: 状态（normal, warning, danger）
        """
        if value >= danger_threshold:
            return "danger"
        elif value >= warning_threshold:
            return "warning"
        else:
            return "normal"
            
    def _normalize_value(self, value: float, min_value: float, max_value: float) -> float:
        """
        将值归一化到0-1范围
        
        Args:
            value: 要归一化的值
            min_value: 最小值
            max_value: 最大值
            
        Returns:
            float: 归一化后的值
        """
        if max_value == min_value:
            return 0.0
            
        normalized = (value - min_value) / (max_value - min_value)
        return max(0.0, min(1.0, normalized))
        
    def _update_history(self, data: Dict[str, Any]) -> None:
        """
        更新历史数据
        
        Args:
            data: 当前数据
        """
        max_size = self.config.get("max_history_size", 60)
        
        # 更新CPU历史
        if 'cpu' in data and 'usage' in data['cpu']:
            self.history['cpu']['usage'].append(data['cpu']['usage'])
            if len(self.history['cpu']['usage']) > max_size:
                self.history['cpu']['usage'] = self.history['cpu']['usage'][-max_size:]
                
        # 更新内存历史
        if 'memory' in data and 'percent' in data['memory']:
            self.history['memory']['percent'].append(data['memory']['percent'])
            if len(self.history['memory']['percent']) > max_size:
                self.history['memory']['percent'] = self.history['memory']['percent'][-max_size:]
                
        # 更新磁盘历史
        if 'disk' in data and 'percent' in data['disk']:
            self.history['disk']['percent'].append(data['disk']['percent'])
            if len(self.history['disk']['percent']) > max_size:
                self.history['disk']['percent'] = self.history['disk']['percent'][-max_size:]
                
        # 更新网络历史
        if 'network' in data:
            network_data = data['network']
            if 'upload_mb_per_sec' in network_data:
                self.history['network']['bytes_sent_rate'].append(network_data['upload_mb_per_sec'])
                if len(self.history['network']['bytes_sent_rate']) > max_size:
                    self.history['network']['bytes_sent_rate'] = self.history['network']['bytes_sent_rate'][-max_size:]
                    
            if 'download_mb_per_sec' in network_data:
                self.history['network']['bytes_recv_rate'].append(network_data['download_mb_per_sec'])
                if len(self.history['network']['bytes_recv_rate']) > max_size:
                    self.history['network']['bytes_recv_rate'] = self.history['network']['bytes_recv_rate'][-max_size:]
                    
    def _calculate_trends(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算趋势
        
        Args:
            data: 当前数据
            
        Returns:
            Dict: 添加了趋势的数据
        """
        result = data.copy()
        min_samples = 3
        
        # 计算CPU趋势
        if 'cpu' in result and len(self.history['cpu']['usage']) >= min_samples:
            # 最近几个值的平均增长率
            recent_values = self.history['cpu']['usage'][-min_samples:]
            trend = self._calculate_trend(recent_values)
            result['cpu']['trend'] = trend
            
            # 预测
            if self.config.get("enable_predictions", False) and len(recent_values) >= 5:
                next_value = self._predict_next_value(recent_values)
                result['cpu']['prediction'] = next_value
                
        # 计算内存趋势
        if 'memory' in result and len(self.history['memory']['percent']) >= min_samples:
            recent_values = self.history['memory']['percent'][-min_samples:]
            trend = self._calculate_trend(recent_values)
            result['memory']['trend'] = trend
            
            # 预测
            if self.config.get("enable_predictions", False) and len(recent_values) >= 5:
                next_value = self._predict_next_value(recent_values)
                result['memory']['prediction'] = next_value
                
        # 计算磁盘趋势
        if 'disk' in result and len(self.history['disk']['percent']) >= min_samples:
            recent_values = self.history['disk']['percent'][-min_samples:]
            trend = self._calculate_trend(recent_values)
            result['disk']['trend'] = trend
            
            # 预测
            if self.config.get("enable_predictions", False) and len(recent_values) >= 5:
                next_value = self._predict_next_value(recent_values)
                result['disk']['prediction'] = next_value
                
        # 计算网络趋势
        if 'network' in result:
            # 上传趋势
            if len(self.history['network']['bytes_sent_rate']) >= min_samples:
                recent_values = self.history['network']['bytes_sent_rate'][-min_samples:]
                trend = self._calculate_trend(recent_values)
                result['network']['upload_trend'] = trend
                
            # 下载趋势
            if len(self.history['network']['bytes_recv_rate']) >= min_samples:
                recent_values = self.history['network']['bytes_recv_rate'][-min_samples:]
                trend = self._calculate_trend(recent_values)
                result['network']['download_trend'] = trend
                
        return result
        
    def _calculate_trend(self, values: List[float]) -> str:
        """
        计算趋势
        
        Args:
            values: 历史值列表
            
        Returns:
            str: 趋势（increasing, decreasing, stable）
        """
        if len(values) < 2:
            return "stable"
            
        last = values[-1]
        prev = values[-2]
        
        change_percent = ((last - prev) / prev) * 100 if prev != 0 else 0
        
        if abs(change_percent) < 5:
            return "stable"
        elif change_percent > 0:
            return "increasing"
        else:
            return "decreasing"
            
    def _predict_next_value(self, values: List[float]) -> float:
        """
        预测下一个值
        
        Args:
            values: 历史值列表
            
        Returns:
            float: 预测的下一个值
        """
        if len(values) < 2:
            return values[-1] if values else 0.0
            
        # 简单线性回归
        n = len(values)
        x = list(range(n))
        y = values
        
        # 计算斜率和截距
        sum_x = sum(x)
        sum_y = sum(y)
        sum_x2 = sum(x_i ** 2 for x_i in x)
        sum_xy = sum(x_i * y_i for x_i, y_i in zip(x, y))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2) if (n * sum_x2 - sum_x ** 2) != 0 else 0
        intercept = (sum_y - slope * sum_x) / n
        
        # 预测下一个值
        next_x = n
        next_value = slope * next_x + intercept
        
        return max(0, next_value)
        
    def _smooth_data(self, values: List[float]) -> List[float]:
        """
        平滑数据（移动平均）
        
        Args:
            values: 原始数据
            
        Returns:
            List[float]: 平滑后的数据
        """
        window_size = self.config.get("smoothing_window", 3)
        if len(values) < window_size:
            return values
            
        result = values.copy()
        
        for i in range(window_size - 1, len(values)):
            window = values[i - (window_size - 1):i + 1]
            result[i] = sum(window) / len(window)
            
        return result
        
    def process_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理原始数据
        
        Args:
            raw_data: 原始性能数据
            
        Returns:
            Dict: 处理后的数据
        """
        if not raw_data:
            return {'error': 'No data to process'}
            
        result = {}
        
        # 处理各项指标
        if 'cpu' in raw_data:
            result['cpu'] = self._process_cpu_data(raw_data['cpu'])
            
        if 'memory' in raw_data:
            result['memory'] = self._process_memory_data(raw_data['memory'])
            
        if 'disk' in raw_data:
            result['disk'] = self._process_disk_data(raw_data['disk'])
            
        if 'network' in raw_data:
            result['network'] = self._process_network_data(raw_data['network'])
            
        if 'system' in raw_data:
            result['system'] = self._process_system_data(raw_data['system'])
            
        # 计算系统整体状态
        overall_status, overall_load = self._calculate_system_status(result)
        result['system'] = result.get('system', {})
        result['system']['overall_status'] = overall_status
        result['system']['overall_load'] = overall_load
        
        # 更新历史数据
        self._update_history(result)
        
        # 计算趋势
        if self.config.get("enable_trends", True):
            result = self._calculate_trends(result)
            
        # 添加时间戳
        result['timestamp'] = time.time()
        
        return result 