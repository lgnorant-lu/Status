"""
---------------------------------------------------------------
File name:                  data_collector.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                系统数据采集器，获取系统性能指标
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import os
import platform
import psutil
import logging
import time
from typing import Dict, Any, List, Optional, Union


class SystemDataCollector:
    """系统数据采集器，负责收集系统性能数据"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化系统数据采集器
        
        Args:
            config: 采集器配置
        """
        self.config = config or {}
        self.logger = logging.getLogger("SystemDataCollector")
        
        # 设置默认配置值
        if "enable_advanced_metrics" not in self.config:
            self.config["enable_advanced_metrics"] = False
        if "enable_io_stats" not in self.config:
            self.config["enable_io_stats"] = True
        if "enable_network_stats" not in self.config:
            self.config["enable_network_stats"] = True
        if "enable_process_stats" not in self.config:
            self.config["enable_process_stats"] = False
        if "collection_interval" not in self.config:
            self.config["collection_interval"] = 1.0  # 秒
        if "alert_thresholds" not in self.config:
            self.config["alert_thresholds"] = {
                "cpu_usage": 90.0,
                "memory_usage": 85.0,
                "disk_usage": 90.0,
                "cpu_temperature": 85.0  # 摄氏度
            }
            
        # 初始化上次采集时间和历史数据
        self.last_collection_time = 0
        self.last_net_io_counters = None
        self.last_disk_io_counters = None
        
        self.logger.info("系统数据采集器初始化完成")
        
    def update_config(self, config: Dict[str, Any]) -> None:
        """
        更新采集器配置
        
        Args:
            config: 新配置
        """
        # 合并配置
        for key, value in config.items():
            if key == "alert_thresholds" and isinstance(value, dict) and "alert_thresholds" in self.config:
                # 合并告警阈值，不替换整个字典
                self.config["alert_thresholds"].update(value)
            else:
                self.config[key] = value
                
        self.logger.debug(f"更新采集器配置: {list(config.keys())}")
        
    def _collect_cpu_data(self) -> Dict[str, Any]:
        """
        采集CPU数据
        
        Returns:
            Dict: CPU性能数据
        """
        result = {
            'usage': psutil.cpu_percent(interval=0.1),
            'core_count': psutil.cpu_count(logical=True),
            'physical_core_count': psutil.cpu_count(logical=False),
        }
        
        # 如果启用高级指标，收集更多数据
        if self.config.get("enable_advanced_metrics", False):
            # 收集每个CPU核心的使用率
            per_cpu = psutil.cpu_percent(interval=0.1, percpu=True)
            result['per_core'] = per_cpu
            
            # CPU频率
            try:
                freq = psutil.cpu_freq()
                if freq:
                    result['freq_current'] = freq.current
                    if hasattr(freq, 'min'):
                        result['freq_min'] = freq.min
                    if hasattr(freq, 'max'):
                        result['freq_max'] = freq.max
            except Exception as e:
                self.logger.debug(f"无法获取CPU频率: {e}")
                
            # 负载平均值
            try:
                load_avg = psutil.getloadavg()
                result['load_avg_1min'] = load_avg[0]
                result['load_avg_5min'] = load_avg[1]
                result['load_avg_15min'] = load_avg[2]
            except Exception as e:
                self.logger.debug(f"无法获取负载平均值: {e}")
                
            # CPU温度 (如果可用)
            try:
                if hasattr(psutil, 'sensors_temperatures'):
                    temps = psutil.sensors_temperatures()
                    if temps:
                        cpu_temps = []
                        for name, entries in temps.items():
                            if any(x.lower() in name.lower() for x in ['cpu', 'core', 'package']):
                                for entry in entries:
                                    if hasattr(entry, 'current'):
                                        cpu_temps.append(entry.current)
                        if cpu_temps:
                            result['temperature'] = sum(cpu_temps) / len(cpu_temps)
                            result['temperature_max'] = max(cpu_temps)
            except Exception as e:
                self.logger.debug(f"无法获取CPU温度: {e}")
                
        return result
        
    def _collect_memory_data(self) -> Dict[str, Any]:
        """
        采集内存数据
        
        Returns:
            Dict: 内存性能数据
        """
        virtual_memory = psutil.virtual_memory()
        result = {
            'percent': virtual_memory.percent,
            'total': virtual_memory.total,
            'used': virtual_memory.used,
            'available': virtual_memory.available
        }
        
        # 交换内存信息
        try:
            swap = psutil.swap_memory()
            result['swap_percent'] = swap.percent
            result['swap_total'] = swap.total
            result['swap_used'] = swap.used
        except Exception as e:
            self.logger.debug(f"无法获取交换内存信息: {e}")
            
        # 如果启用高级指标，收集更多数据
        if self.config.get("enable_advanced_metrics", False):
            if hasattr(virtual_memory, 'buffers'):
                result['buffers'] = virtual_memory.buffers
            if hasattr(virtual_memory, 'cached'):
                result['cached'] = virtual_memory.cached
            if hasattr(virtual_memory, 'shared'):
                result['shared'] = virtual_memory.shared
                
        return result
        
    def _collect_disk_data(self) -> Dict[str, Any]:
        """
        采集磁盘数据
        
        Returns:
            Dict: 磁盘性能数据
        """
        result = {}
        
        # 磁盘使用情况
        try:
            # 获取根目录的使用情况
            root_usage = psutil.disk_usage('/')
            result['percent'] = root_usage.percent
            result['total'] = root_usage.total
            result['used'] = root_usage.used
            result['free'] = root_usage.free
        except Exception as e:
            self.logger.debug(f"无法获取根目录磁盘使用情况: {e}")
            
        # 如果启用IO统计，收集磁盘IO数据
        if self.config.get("enable_io_stats", True):
            try:
                io_counters = psutil.disk_io_counters()
                if io_counters:
                    # 计算IO速率
                    current_time = time.time()
                    if self.last_disk_io_counters and self.last_collection_time > 0:
                        time_diff = current_time - self.last_collection_time
                        if time_diff > 0:
                            read_bytes_diff = io_counters.read_bytes - self.last_disk_io_counters.read_bytes
                            write_bytes_diff = io_counters.write_bytes - self.last_disk_io_counters.write_bytes
                            
                            result['io_read'] = io_counters.read_bytes
                            result['io_write'] = io_counters.write_bytes
                            result['io_read_rate'] = read_bytes_diff / time_diff
                            result['io_write_rate'] = write_bytes_diff / time_diff
                    else:
                        result['io_read'] = io_counters.read_bytes
                        result['io_write'] = io_counters.write_bytes
                        
                    self.last_disk_io_counters = io_counters
            except Exception as e:
                self.logger.debug(f"无法获取磁盘IO统计: {e}")
                
        # 如果启用高级指标，收集详细的分区信息
        if self.config.get("enable_advanced_metrics", False):
            try:
                partitions = {}
                for part in psutil.disk_partitions(all=False):
                    if os.path.exists(part.mountpoint):
                        try:
                            usage = psutil.disk_usage(part.mountpoint)
                            partitions[part.mountpoint] = {
                                'device': part.device,
                                'fstype': part.fstype,
                                'total': usage.total,
                                'used': usage.used,
                                'free': usage.free,
                                'percent': usage.percent
                            }
                        except Exception as e:
                            self.logger.debug(f"无法获取分区 {part.mountpoint} 使用情况: {e}")
                            
                result['partitions'] = partitions
            except Exception as e:
                self.logger.debug(f"无法获取磁盘分区信息: {e}")
                
        return result
        
    def _collect_network_data(self) -> Dict[str, Any]:
        """
        采集网络数据
        
        Returns:
            Dict: 网络性能数据
        """
        result = {}
        
        # 基本网络IO信息
        try:
            net_io = psutil.net_io_counters()
            result['bytes_sent'] = net_io.bytes_sent
            result['bytes_recv'] = net_io.bytes_recv
            result['packets_sent'] = net_io.packets_sent
            result['packets_recv'] = net_io.packets_recv
            
            # 计算网络速率
            current_time = time.time()
            if self.last_net_io_counters and self.last_collection_time > 0:
                time_diff = current_time - self.last_collection_time
                if time_diff > 0:
                    sent_diff = net_io.bytes_sent - self.last_net_io_counters.bytes_sent
                    recv_diff = net_io.bytes_recv - self.last_net_io_counters.bytes_recv
                    
                    result['bytes_sent_rate'] = sent_diff / time_diff
                    result['bytes_recv_rate'] = recv_diff / time_diff
                    
            self.last_net_io_counters = net_io
            self.last_collection_time = current_time
        except Exception as e:
            self.logger.debug(f"无法获取网络IO信息: {e}")
            
        # 如果启用网络统计，收集网络连接信息
        if self.config.get("enable_network_stats", True):
            try:
                connections = psutil.net_connections(kind='inet')
                result['connections'] = len(connections)
                
                # 统计各状态的连接数
                if self.config.get("enable_advanced_metrics", False):
                    conn_status = {}
                    for conn in connections:
                        status = conn.status if hasattr(conn, 'status') else 'UNKNOWN'
                        conn_status[status] = conn_status.get(status, 0) + 1
                    result['connection_status'] = conn_status
            except Exception as e:
                self.logger.debug(f"无法获取网络连接信息: {e}")
                
        # 如果启用高级指标，收集详细的网络接口信息
        if self.config.get("enable_advanced_metrics", False):
            try:
                interfaces = {}
                for name, addrs in psutil.net_if_addrs().items():
                    interfaces[name] = {'addresses': []}
                    for addr in addrs:
                        if hasattr(addr, 'address') and hasattr(addr, 'family'):
                            addr_info = {'address': addr.address, 'family': str(addr.family)}
                            if hasattr(addr, 'netmask') and addr.netmask:
                                addr_info['netmask'] = addr.netmask
                            interfaces[name]['addresses'].append(addr_info)
                            
                # 添加接口统计信息
                stats = psutil.net_if_stats()
                for name, stat in stats.items():
                    if name in interfaces:
                        interfaces[name]['speed'] = stat.speed if hasattr(stat, 'speed') else 0
                        interfaces[name]['mtu'] = stat.mtu if hasattr(stat, 'mtu') else 0
                        interfaces[name]['up'] = stat.isup if hasattr(stat, 'isup') else False
                        
                result['interfaces'] = interfaces
            except Exception as e:
                self.logger.debug(f"无法获取网络接口信息: {e}")
                
        return result
        
    def _collect_process_data(self) -> Dict[str, Any]:
        """
        采集进程数据
        
        Returns:
            Dict: 进程性能数据
        """
        result = {}
        
        # 只有在启用进程统计时才收集
        if not self.config.get("enable_process_stats", False):
            return result
            
        try:
            # 获取进程总数
            result['count'] = len(psutil.pids())
            
            # 获取前N个CPU使用率最高的进程
            top_cpu_processes = []
            top_memory_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    process_data = {
                        'pid': pinfo['pid'],
                        'name': pinfo['name'],
                        'username': pinfo['username'],
                        'cpu_percent': pinfo['cpu_percent'] or proc.cpu_percent(interval=0.1),
                        'memory_percent': pinfo['memory_percent'] or proc.memory_percent()
                    }
                    
                    top_cpu_processes.append(process_data)
                    top_memory_processes.append(process_data)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
                    
            # 排序并截取前10个
            top_cpu_processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            top_memory_processes.sort(key=lambda x: x['memory_percent'], reverse=True)
            
            result['top_cpu_processes'] = top_cpu_processes[:10]
            result['top_memory_processes'] = top_memory_processes[:10]
        except Exception as e:
            self.logger.debug(f"无法获取进程信息: {e}")
            
        return result
        
    def _collect_system_info(self) -> Dict[str, Any]:
        """
        采集系统基本信息
        
        Returns:
            Dict: 系统信息数据
        """
        result = {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'hostname': platform.node(),
            'processor': platform.processor(),
            'boot_time': psutil.boot_time()
        }
        
        # 计算系统运行时间
        uptime = time.time() - psutil.boot_time()
        result['uptime'] = uptime
        
        return result
        
    def collect_data(self, metrics: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        采集系统数据
        
        Args:
            metrics: 要采集的指标列表，如果为None则采集所有指标
            
        Returns:
            Dict: 采集到的系统数据
        """
        if metrics is None:
            metrics = ["cpu", "memory", "disk", "network"]
            
            # 只有在启用进程统计时才添加进程指标
            if self.config.get("enable_process_stats", False):
                metrics.append("processes")
                
            # 添加系统信息指标
            metrics.append("system")
            
        result = {}
        
        # 采集指定的指标
        for metric in metrics:
            try:
                if metric == "cpu":
                    result["cpu"] = self._collect_cpu_data()
                elif metric == "memory":
                    result["memory"] = self._collect_memory_data()
                elif metric == "disk":
                    result["disk"] = self._collect_disk_data()
                elif metric == "network":
                    result["network"] = self._collect_network_data()
                elif metric == "processes":
                    result["processes"] = self._collect_process_data()
                elif metric == "system":
                    result["system"] = self._collect_system_info()
                else:
                    self.logger.warning(f"未知的指标类型: {metric}")
            except Exception as e:
                self.logger.error(f"采集 {metric} 数据时出错: {e}")
                
        return result
        
    def get_available_metrics(self) -> List[str]:
        """
        获取可用的指标列表
        
        Returns:
            List[str]: 可用指标列表
        """
        metrics = ["cpu", "memory", "disk", "network", "system"]
        
        # 只有在启用进程统计时才包含进程指标
        if self.config.get("enable_process_stats", False):
            metrics.append("processes")
            
        return metrics
        
    def check_system_alerts(self) -> List[Dict[str, Any]]:
        """
        检查系统告警
        
        Returns:
            List[Dict]: 告警列表
        """
        alerts = []
        thresholds = self.config.get("alert_thresholds", {})
        
        # 采集关键指标
        cpu_data = self._collect_cpu_data()
        memory_data = self._collect_memory_data()
        disk_data = self._collect_disk_data()
        
        # 检查CPU使用率
        cpu_threshold = thresholds.get("cpu_usage", 90.0)
        if cpu_data.get("usage", 0) > cpu_threshold:
            alerts.append({
                "type": "cpu",
                "severity": "warning",
                "message": f"CPU使用率过高: {cpu_data['usage']:.1f}% (阈值: {cpu_threshold:.1f}%)",
                "value": cpu_data["usage"],
                "threshold": cpu_threshold,
                "timestamp": time.time()
            })
            
        # 检查内存使用率
        memory_threshold = thresholds.get("memory_usage", 85.0)
        if memory_data.get("percent", 0) > memory_threshold:
            alerts.append({
                "type": "memory",
                "severity": "warning",
                "message": f"内存使用率过高: {memory_data['percent']:.1f}% (阈值: {memory_threshold:.1f}%)",
                "value": memory_data["percent"],
                "threshold": memory_threshold,
                "timestamp": time.time()
            })
            
        # 检查磁盘使用率
        disk_threshold = thresholds.get("disk_usage", 90.0)
        if disk_data.get("percent", 0) > disk_threshold:
            alerts.append({
                "type": "disk",
                "severity": "warning",
                "message": f"磁盘使用率过高: {disk_data['percent']:.1f}% (阈值: {disk_threshold:.1f}%)",
                "value": disk_data["percent"],
                "threshold": disk_threshold,
                "timestamp": time.time()
            })
            
        # 检查CPU温度
        temp_threshold = thresholds.get("cpu_temperature", 85.0)
        if "temperature" in cpu_data and cpu_data["temperature"] > temp_threshold:
            alerts.append({
                "type": "temperature",
                "severity": "danger",
                "message": f"CPU温度过高: {cpu_data['temperature']:.1f}°C (阈值: {temp_threshold:.1f}°C)",
                "value": cpu_data["temperature"],
                "threshold": temp_threshold,
                "timestamp": time.time()
            })
            
        return alerts 