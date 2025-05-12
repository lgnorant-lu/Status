"""
---------------------------------------------------------------
File name:                  data_process.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                数据处理模块，分析和转换系统数据
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
                            2025/05/15: 修复类型提示错误;
----
"""

import os
import time
import logging
import threading
from typing import Dict, List, Any, Optional, Callable, Tuple, Union, Deque, cast, TypeVar
import collections
from collections import deque

from status.core.event_system import EventSystem, Event, EventType

# 类型变量定义
T = TypeVar('T')

class DataProcessor:
    """数据处理类，负责处理和分析系统监控数据"""
    
    _instance = None
    _initialized: bool = False
    
    @classmethod
    def get_instance(cls) -> 'DataProcessor':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __new__(cls, *args, **kwargs):
        """创建单例实例"""
        if cls._instance is None:
            cls._instance = super(DataProcessor, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, max_history_size: int = 60):
        """初始化数据处理器
        
        Args:
            max_history_size: 历史数据保留的最大条目数（默认60条，对应1分钟）
        """
        # 单例模式只初始化一次
        if self._initialized:
            return
            
        self.logger = logging.getLogger(__name__)
        self.logger.info("初始化数据处理器")
        
        # 历史数据容器（使用双端队列）
        self.history: Dict[str, deque] = {
            "cpu": deque(maxlen=max_history_size),
            "memory": deque(maxlen=max_history_size),
            "disk": deque(maxlen=max_history_size),
            "network": deque(maxlen=max_history_size),
            "battery": deque(maxlen=max_history_size),
            "processes": deque(maxlen=max_history_size),
            "timestamps": deque(maxlen=max_history_size),
        }
        
        # 统计数据
        self.stats: Dict[str, Dict[str, Any]] = {
            "cpu": {},
            "memory": {},
            "disk": {},
            "network": {},
            "battery": {},
        }
        
        # 阈值配置（可由用户自定义）
        self.thresholds = {
            "cpu_high": 80.0,            # CPU使用率高阈值（百分比）
            "memory_high": 80.0,         # 内存使用率高阈值（百分比）
            "disk_space_low": 10.0,      # 磁盘空间低阈值（百分比）
            "battery_low": 20.0,         # 电池电量低阈值（百分比）
            "network_high": 80.0,        # 网络使用率高阈值（百分比）
        }
        
        # 事件系统
        self.event_system = EventSystem()
        
        # 注册系统状态更新事件处理器
        self.event_system.register_handler(
            EventType.SYSTEM_STATUS_UPDATE,
            self._handle_system_status_update
        )
        
        # 自定义处理回调函数
        self.custom_processors: Dict[str, Callable[[float, Dict[str, Any], Dict[str, deque], Dict[str, Any]], None]] = {}
        
        # 告警状态（避免重复告警）
        self.alert_status = {
            "cpu_high": False,
            "memory_high": False,
            "disk_space_low": False,
            "battery_low": False,
            "network_high": False,
        }
        
        # 线程锁（确保线程安全）
        self.lock = threading.RLock()
        
        self._initialized = True
    
    def _handle_system_status_update(self, event: Event) -> None:
        """处理系统状态更新事件
        
        Args:
            event: 系统状态更新事件
        """
        if event.type != EventType.SYSTEM_STATUS_UPDATE:
            return
            
        try:
            timestamp = event.data.get("timestamp", time.time())
            metrics = event.data.get("metrics", {})
            
            with self.lock:
                # 更新历史数据
                self._update_history(timestamp, metrics)
                
                # 计算统计数据
                self._calculate_stats()
                
                # 检查阈值并发送告警
                self._check_thresholds(metrics)
                
                # 应用自定义处理器
                self._apply_custom_processors(timestamp, metrics)
        except Exception as e:
            self.logger.error(f"处理系统状态更新事件失败: {e}")
    
    def _update_history(self, timestamp: float, metrics: Dict[str, Any]) -> None:
        """更新历史数据
        
        Args:
            timestamp: 时间戳
            metrics: 系统指标数据
        """
        self.history["timestamps"].append(timestamp)
        
        # 更新CPU历史数据
        cpu_data = metrics.get("cpu", {})
        if "percent_overall" in cpu_data:
            self.history["cpu"].append({
                "percent": cpu_data["percent_overall"],
                "per_cpu": cpu_data.get("percent_per_cpu", []),
            })
        
        # 更新内存历史数据
        memory_data = metrics.get("memory", {})
        if "percent" in memory_data:
            self.history["memory"].append({
                "percent": memory_data["percent"],
                "used_gb": memory_data.get("used_gb", 0),
                "total_gb": memory_data.get("total_gb", 0),
            })
        
        # 更新磁盘历史数据（仅保存总体使用情况）
        disk_data = metrics.get("disk", {})
        disk_summary = {}
        
        for partition in disk_data.get("partitions", []):
            usage = partition.get("usage", {})
            if usage and "percent" in usage:
                mount = partition.get("mountpoint", "unknown")
                disk_summary[mount] = {
                    "percent": usage["percent"],
                    "total_gb": partition.get("usage_gb", {}).get("total", 0),
                    "used_gb": partition.get("usage_gb", {}).get("used", 0),
                }
        
        self.history["disk"].append(disk_summary)
        
        # 更新网络历史数据
        network_data = metrics.get("network", {})
        if "io_counters" in network_data:
            io = network_data["io_counters"]
            self.history["network"].append({
                "bytes_sent": io.get("bytes_sent", 0),
                "bytes_recv": io.get("bytes_recv", 0),
                "packets_sent": io.get("packets_sent", 0),
                "packets_recv": io.get("packets_recv", 0),
            })
        
        # 更新电池历史数据
        battery_data = metrics.get("battery", {})
        if battery_data and "percent" in battery_data:
            self.history["battery"].append({
                "percent": battery_data["percent"],
                "plugged": battery_data.get("power_plugged", False),
                "time_left": battery_data.get("time_left"),
            })
    
    def _calculate_stats(self) -> None:
        """计算统计数据"""
        # 计算CPU统计数据
        if self.history["cpu"]:
            cpu_values = [entry["percent"] for entry in self.history["cpu"]]
            self.stats["cpu"] = {
                "current": cpu_values[-1] if cpu_values else 0,
                "min": min(cpu_values) if cpu_values else 0,
                "max": max(cpu_values) if cpu_values else 0,
                "avg": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
            }
        
        # 计算内存统计数据
        if self.history["memory"]:
            mem_values = [entry["percent"] for entry in self.history["memory"]]
            self.stats["memory"] = {
                "current": mem_values[-1] if mem_values else 0,
                "min": min(mem_values) if mem_values else 0,
                "max": max(mem_values) if mem_values else 0,
                "avg": sum(mem_values) / len(mem_values) if mem_values else 0,
            }
        
        # 计算磁盘统计数据（选择根分区或第一个分区）
        if self.history["disk"]:
            root_values = []
            for entry in self.history["disk"]:
                # 尝试获取根分区或第一个分区的使用率
                root_percent = None
                for mount, data in entry.items():
                    if mount == "/" or mount == "C:\\":  # 优先选择根分区
                        root_percent = data.get("percent", 0)
                        break
                
                # 如果没有找到根分区，使用第一个分区
                if root_percent is None and entry:
                    root_percent = next(iter(entry.values())).get("percent", 0)
                
                if root_percent is not None:
                    root_values.append(root_percent)
            
            self.stats["disk"] = {
                "current": root_values[-1] if root_values else 0,
                "min": min(root_values) if root_values else 0,
                "max": max(root_values) if root_values else 0,
                "avg": sum(root_values) / len(root_values) if root_values else 0,
            }
        
        # 计算网络统计数据（传输速率）
        if len(self.history["network"]) >= 2 and len(self.history["timestamps"]) >= 2:
            current = self.history["network"][-1]
            previous = self.history["network"][-2]
            current_time = self.history["timestamps"][-1]
            previous_time = self.history["timestamps"][-2]
            
            time_diff = current_time - previous_time
            if time_diff > 0:
                # 计算传输速率（字节/秒）
                bytes_sent_rate = (current.get("bytes_sent", 0) - previous.get("bytes_sent", 0)) / time_diff
                bytes_recv_rate = (current.get("bytes_recv", 0) - previous.get("bytes_recv", 0)) / time_diff
                
                self.stats["network"] = {
                    "bytes_sent_rate": bytes_sent_rate,
                    "bytes_recv_rate": bytes_recv_rate,
                    "kb_sent_rate": bytes_sent_rate / 1024,
                    "kb_recv_rate": bytes_recv_rate / 1024,
                    "mb_sent_rate": bytes_sent_rate / (1024 * 1024),
                    "mb_recv_rate": bytes_recv_rate / (1024 * 1024),
                }
        
        # 计算电池统计数据
        if self.history["battery"]:
            battery_values = [entry["percent"] for entry in self.history["battery"] if "percent" in entry]
            if battery_values:
                self.stats["battery"] = {
                    "current": battery_values[-1],
                    "min": min(battery_values),
                    "max": max(battery_values),
                    "avg": sum(battery_values) / len(battery_values),
                    "is_plugged": self.history["battery"][-1].get("plugged", False),
                    "time_left": self.history["battery"][-1].get("time_left"),
                }
    
    def _check_thresholds(self, metrics: Dict[str, Any]) -> None:
        """检查阈值并发送告警
        
        Args:
            metrics: 系统指标数据
        """
        # 检查CPU使用率
        if "cpu" in metrics and "percent_overall" in metrics["cpu"]:
            cpu_percent = metrics["cpu"]["percent_overall"]
            if cpu_percent >= self.thresholds["cpu_high"] and not self.alert_status["cpu_high"]:
                self._send_alert("cpu_high", f"CPU使用率过高: {cpu_percent:.1f}%", {
                    "value": cpu_percent,
                    "threshold": self.thresholds["cpu_high"],
                    "metrics": metrics["cpu"],
                })
                self.alert_status["cpu_high"] = True
            elif cpu_percent < self.thresholds["cpu_high"] * 0.9 and self.alert_status["cpu_high"]:
                # 恢复正常（使用缓冲区避免频繁告警）
                self.alert_status["cpu_high"] = False
        
        # 检查内存使用率
        if "memory" in metrics and "percent" in metrics["memory"]:
            memory_percent = metrics["memory"]["percent"]
            if memory_percent >= self.thresholds["memory_high"] and not self.alert_status["memory_high"]:
                self._send_alert("memory_high", f"内存使用率过高: {memory_percent:.1f}%", {
                    "value": memory_percent,
                    "threshold": self.thresholds["memory_high"],
                    "metrics": metrics["memory"],
                })
                self.alert_status["memory_high"] = True
            elif memory_percent < self.thresholds["memory_high"] * 0.9 and self.alert_status["memory_high"]:
                self.alert_status["memory_high"] = False
        
        # 检查磁盘空间
        if "disk" in metrics and "partitions" in metrics["disk"]:
            for partition in metrics["disk"]["partitions"]:
                if "usage" not in partition or "percent" not in partition["usage"]:
                    continue
                    
                # 计算剩余空间百分比
                free_percent = 100 - partition["usage"]["percent"]
                mount = partition.get("mountpoint", "unknown")
                
                if free_percent <= self.thresholds["disk_space_low"] and not self.alert_status["disk_space_low"]:
                    self._send_alert("disk_space_low", f"磁盘空间不足: {mount} 仅剩 {free_percent:.1f}%", {
                        "value": free_percent,
                        "threshold": self.thresholds["disk_space_low"],
                        "mount": mount,
                        "metrics": partition,
                    })
                    self.alert_status["disk_space_low"] = True
                elif free_percent > self.thresholds["disk_space_low"] * 1.1 and self.alert_status["disk_space_low"]:
                    self.alert_status["disk_space_low"] = False
        
        # 检查电池电量
        if "battery" in metrics and metrics["battery"] and "percent" in metrics["battery"]:
            battery_percent = metrics["battery"]["percent"]
            is_plugged = metrics["battery"].get("power_plugged", False)
            
            # 只在未接通电源时检查电池电量
            if not is_plugged and battery_percent <= self.thresholds["battery_low"] and not self.alert_status["battery_low"]:
                self._send_alert("battery_low", f"电池电量不足: {battery_percent:.1f}%", {
                    "value": battery_percent,
                    "threshold": self.thresholds["battery_low"],
                    "metrics": metrics["battery"],
                })
                self.alert_status["battery_low"] = True
            elif (battery_percent > self.thresholds["battery_low"] * 1.1 or is_plugged) and self.alert_status["battery_low"]:
                self.alert_status["battery_low"] = False
    
    def _apply_custom_processors(self, timestamp: float, metrics: Dict[str, Any]) -> None:
        """应用自定义处理器
        
        Args:
            timestamp: 时间戳
            metrics: 系统指标数据
        """
        for name, processor in self.custom_processors.items():
            try:
                processor(timestamp, metrics, self.history, self.stats)
            except Exception as e:
                self.logger.error(f"应用自定义处理器 '{name}' 失败: {e}")
    
    def _send_alert(self, alert_type: str, message: str, data: Dict[str, Any]) -> None:
        """发送系统告警事件
        
        Args:
            alert_type: 告警类型
            message: 告警消息
            data: 告警数据
        """
        try:
            alert_data = {
                "type": alert_type,
                    "message": message,
                "data": data,
                    "timestamp": time.time(),
            }
            
            # 使用枚举类型
            self.event_system.dispatch_event(
                event_type=EventType.SYSTEM_ALERT,
                sender=self,
                data=alert_data
            )
            
            self.logger.warning(f"发送系统告警: {alert_type} - {message}")
        except Exception as e:
            self.logger.error(f"发送告警事件失败: {e}")
    
    def register_custom_processor(self, name: str, processor: Callable[[float, Dict[str, Any], Dict[str, deque], Dict[str, Any]], None]) -> bool:
        """注册自定义数据处理器
        
        Args:
            name: 处理器名称
            processor: 处理器函数，接收四个参数：时间戳、指标数据、历史数据、统计数据
            
        Returns:
            是否注册成功
        """
        if name in self.custom_processors:
            self.logger.warning(f"自定义处理器 '{name}' 已存在，将被覆盖")
            
        self.custom_processors[name] = processor
        self.logger.info(f"已注册自定义处理器: {name}")
        return True
    
    def unregister_custom_processor(self, name: str) -> bool:
        """注销自定义数据处理器
        
        Args:
            name: 处理器名称
            
        Returns:
            是否注销成功
        """
        if name not in self.custom_processors:
            self.logger.warning(f"自定义处理器 '{name}' 不存在")
            return False
            
        del self.custom_processors[name]
        self.logger.info(f"已注销自定义处理器: {name}")
        return True
    
    def set_threshold(self, threshold_name: str, value: float) -> bool:
        """设置告警阈值
        
        Args:
            threshold_name: 阈值名称
            value: 阈值值
            
        Returns:
            是否设置成功
        """
        if threshold_name not in self.thresholds:
            self.logger.error(f"未知的阈值名称: {threshold_name}")
            return False
            
        self.thresholds[threshold_name] = value
        self.logger.info(f"已设置告警阈值 {threshold_name}: {value}")
        return True
    
    def get_threshold(self, threshold_name: str) -> Optional[float]:
        """获取告警阈值
        
        Args:
            threshold_name: 阈值名称
            
        Returns:
            阈值值，如果不存在则返回None
        """
        return self.thresholds.get(threshold_name)
    
    def get_all_thresholds(self) -> Dict[str, float]:
        """获取所有告警阈值
        
        Returns:
            包含所有告警阈值的字典
        """
        return self.thresholds.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计数据
        
        Returns:
            包含统计数据的字典
        """
        with self.lock:
            return self.stats.copy()
    
    def get_history(self, metric_type: str, count: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取指定类型的历史数据
        
        Args:
            metric_type: 指标类型（cpu, memory, disk, network, battery, timestamps）
            count: 返回的条目数量，None表示全部
            
        Returns:
            历史数据列表
        """
        with self.lock:
            if metric_type not in self.history:
                return []
                
            history_data = list(self.history[metric_type])
            
            if count is not None and count > 0:
                return history_data[-count:]
            return history_data
    
    def get_history_with_timestamps(self, metric_type: str, count: Optional[int] = None) -> List[Tuple[float, Dict[str, Any]]]:
        """获取带时间戳的历史数据
        
        Args:
            metric_type: 指标类型（cpu, memory, disk, network, battery）
            count: 返回的条目数量，None表示全部
            
        Returns:
            (时间戳, 数据)元组列表
        """
        with self.lock:
            if metric_type not in self.history or metric_type == "timestamps":
                return []
                
            # 组合时间戳和数据
            timestamps = list(self.history["timestamps"])
            data = list(self.history[metric_type])
            
            # 确保长度匹配
            min_length = min(len(timestamps), len(data))
            result = [(timestamps[i], data[i]) for i in range(min_length)]
            
            if count is not None and count > 0:
                return result[-count:]
            return result
    
    def clear_history(self) -> None:
        """清空历史数据"""
        with self.lock:
            for key in self.history:
                self.history[key].clear()
            self.logger.info("已清空历史数据") 
