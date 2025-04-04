"""
---------------------------------------------------------------
File name:                  system_info.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                系统信息收集，获取各项系统性能指标
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import os
import sys
import time
import logging
import datetime
import platform
import threading
import subprocess
from typing import Dict, List, Any, Tuple, Optional, Union, Callable

try:
    import psutil
except ImportError:
    logging.error("psutil库未安装，部分系统信息功能将不可用")
    psutil = None

from status.core.event_system import EventSystem, Event, EventType


class SystemInfo:
    """系统信息收集类，负责获取各项系统性能指标"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super(SystemInfo, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, update_interval: float = 1.0):
        """初始化系统信息收集器
        
        Args:
            update_interval: 自动更新间隔（秒）
        """
        # 单例模式只初始化一次
        if self._initialized:
            return
            
        self.logger = logging.getLogger(__name__)
        self.logger.info("初始化系统信息收集器")
        
        # 系统基本信息
        self.system_info = self._get_system_info()
        
        # 可更新的系统指标
        self.metrics = {}
        
        # 更新配置
        self.update_interval = update_interval
        self.auto_update_enabled = False
        self.update_thread = None
        self._stop_event = threading.Event()
        
        # 事件系统
        self.event_system = EventSystem()
        
        self._initialized = True
    
    def _get_system_info(self) -> Dict[str, Any]:
        """获取系统基本信息（不易变的信息）
        
        Returns:
            包含系统信息的字典
        """
        info = {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "architecture": platform.architecture(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        }
        
        # 添加CPU信息
        if psutil:
            try:
                info["cpu_count_physical"] = psutil.cpu_count(logical=False)
                info["cpu_count_logical"] = psutil.cpu_count(logical=True)
            except Exception as e:
                self.logger.error(f"获取CPU信息失败: {e}")
        
        # 获取主机名
        try:
            info["hostname"] = platform.node()
        except Exception as e:
            self.logger.error(f"获取主机名失败: {e}")
            info["hostname"] = "unknown"
        
        return info
    
    def get_basic_info(self) -> Dict[str, Any]:
        """获取系统基本信息
        
        Returns:
            包含系统基本信息的字典
        """
        return self.system_info
    
    def update_metrics(self) -> Dict[str, Any]:
        """更新所有系统指标
        
        Returns:
            包含所有最新系统指标的字典
        """
        self.metrics = {}
        
        # 获取CPU使用率
        try:
            if psutil:
                self.metrics["cpu"] = self.get_cpu_info()
        except Exception as e:
            self.logger.error(f"获取CPU信息失败: {e}")
            self.metrics["cpu"] = {"error": str(e)}
        
        # 获取内存使用情况
        try:
            if psutil:
                self.metrics["memory"] = self.get_memory_info()
        except Exception as e:
            self.logger.error(f"获取内存信息失败: {e}")
            self.metrics["memory"] = {"error": str(e)}
        
        # 获取磁盘使用情况
        try:
            if psutil:
                self.metrics["disk"] = self.get_disk_info()
        except Exception as e:
            self.logger.error(f"获取磁盘信息失败: {e}")
            self.metrics["disk"] = {"error": str(e)}
        
        # 获取网络使用情况
        try:
            if psutil:
                self.metrics["network"] = self.get_network_info()
        except Exception as e:
            self.logger.error(f"获取网络信息失败: {e}")
            self.metrics["network"] = {"error": str(e)}
        
        # 获取电池信息
        try:
            if psutil:
                battery = self.get_battery_info()
                if battery:
                    self.metrics["battery"] = battery
        except Exception as e:
            self.logger.error(f"获取电池信息失败: {e}")
            self.metrics["battery"] = {"error": str(e)}
        
        # 发送系统状态更新事件
        self._send_update_event()
        
        return self.metrics
    
    def get_cpu_info(self) -> Dict[str, Any]:
        """获取CPU使用率信息
        
        Returns:
            包含CPU使用率信息的字典
        """
        if not psutil:
            return {"error": "psutil未安装"}
        
        result = {
            "percent_overall": psutil.cpu_percent(interval=0.1),
            "percent_per_cpu": psutil.cpu_percent(interval=0.1, percpu=True),
            "times": dict(psutil.cpu_times()._asdict()),
            "stats": dict(psutil.cpu_stats()._asdict()),
            "freq": dict(psutil.cpu_freq()._asdict()) if psutil.cpu_freq() else {},
        }
        
        try:
            # 获取CPU负载（仅在Unix系统上可用）
            if hasattr(os, "getloadavg"):
                result["load_avg"] = os.getloadavg()
        except (AttributeError, OSError) as e:
            self.logger.debug(f"获取CPU负载失败: {e}")
        
        return result
    
    def get_memory_info(self) -> Dict[str, Any]:
        """获取内存使用情况
        
        Returns:
            包含内存使用情况的字典
        """
        if not psutil:
            return {"error": "psutil未安装"}
            
        virtual_memory = dict(psutil.virtual_memory()._asdict())
        swap_memory = dict(psutil.swap_memory()._asdict())
        
        result = {
            "virtual": virtual_memory,
            "swap": swap_memory,
            "percent": virtual_memory["percent"],
            "total_gb": round(virtual_memory["total"] / (1024 ** 3), 2),
            "available_gb": round(virtual_memory["available"] / (1024 ** 3), 2),
            "used_gb": round(virtual_memory["used"] / (1024 ** 3), 2),
        }
        
        return result
    
    def get_disk_info(self) -> Dict[str, Any]:
        """获取磁盘使用情况
        
        Returns:
            包含磁盘使用情况的字典
        """
        if not psutil:
            return {"error": "psutil未安装"}
            
        result = {
            "partitions": [],
            "io_counters": dict(psutil.disk_io_counters(perdisk=False)._asdict()) if psutil.disk_io_counters() else {},
            "io_counters_per_disk": {},
        }
        
        # 获取每个硬盘的IO计数器
        if psutil.disk_io_counters(perdisk=True):
            for disk, counters in psutil.disk_io_counters(perdisk=True).items():
                result["io_counters_per_disk"][disk] = dict(counters._asdict())
        
        # 获取分区信息
        for partition in psutil.disk_partitions():
            part_info = dict(partition._asdict())
            
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                part_info["usage"] = dict(usage._asdict())
                part_info["usage_gb"] = {
                    "total": round(usage.total / (1024 ** 3), 2),
                    "used": round(usage.used / (1024 ** 3), 2),
                    "free": round(usage.free / (1024 ** 3), 2),
                    "percent": usage.percent
                }
            except (PermissionError, OSError) as e:
                self.logger.debug(f"获取分区 {partition.mountpoint} 使用情况失败: {e}")
                part_info["usage"] = {"error": str(e)}
            
            result["partitions"].append(part_info)
        
        return result
    
    def get_network_info(self) -> Dict[str, Any]:
        """获取网络使用情况
        
        Returns:
            包含网络使用情况的字典
        """
        if not psutil:
            return {"error": "psutil未安装"}
            
        result = {
            "io_counters": dict(psutil.net_io_counters()._asdict()) if psutil.net_io_counters() else {},
            "io_counters_per_nic": {},
            "connections": [],
            "stats": {},
        }
        
        # 获取每个网卡的IO计数器
        if psutil.net_io_counters(pernic=True):
            for nic, counters in psutil.net_io_counters(pernic=True).items():
                result["io_counters_per_nic"][nic] = dict(counters._asdict())
        
        # 获取网络连接信息（最多显示10个）
        try:
            for i, conn in enumerate(psutil.net_connections()):
                if i >= 10:  # 限制连接数量，避免数据过大
                    break
                conn_dict = dict(conn._asdict())
                # 将地址信息转换为可序列化的格式
                if conn_dict.get("laddr"):
                    conn_dict["laddr"] = dict(zip(["ip", "port"], conn_dict["laddr"]))
                if conn_dict.get("raddr"):
                    conn_dict["raddr"] = dict(zip(["ip", "port"], conn_dict["raddr"]))
                result["connections"].append(conn_dict)
        except (psutil.AccessDenied, PermissionError) as e:
            self.logger.debug(f"获取网络连接信息失败（权限不足）: {e}")
        
        # 获取网络统计信息（仅在某些系统上可用）
        try:
            stats = psutil.net_if_stats()
            for nic, stat in stats.items():
                result["stats"][nic] = dict(stat._asdict())
        except Exception as e:
            self.logger.debug(f"获取网络统计信息失败: {e}")
        
        return result
    
    def get_battery_info(self) -> Optional[Dict[str, Any]]:
        """获取电池信息（如果可用）
        
        Returns:
            包含电池信息的字典，如果没有电池则返回None
        """
        if not psutil:
            return {"error": "psutil未安装"}
        
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return None
                
            result = {
                "percent": battery.percent,
                "power_plugged": battery.power_plugged,
                "seconds_left": battery.secsleft if battery.secsleft != -1 else None,
            }
            
            # 计算剩余时间的可读表示
            if result["seconds_left"] is not None:
                m, s = divmod(result["seconds_left"], 60)
                h, m = divmod(m, 60)
                result["time_left"] = f"{h:d}:{m:02d}:{s:02d}"
            
            return result
        except Exception as e:
            self.logger.debug(f"获取电池信息失败: {e}")
            return None
    
    def get_running_processes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取当前运行的进程信息
        
        Args:
            limit: 最多返回的进程数量
            
        Returns:
            包含进程信息的列表
        """
        if not psutil:
            return [{"error": "psutil未安装"}]
            
        result = []
        
        for proc in sorted(psutil.process_iter(['pid', 'name', 'username', 'memory_percent', 'cpu_percent', 'create_time']), 
                           key=lambda p: p.info['cpu_percent'] if p.info['cpu_percent'] is not None else 0, 
                           reverse=True)[:limit]:
            try:
                proc_info = proc.as_dict(['pid', 'name', 'username', 'memory_percent', 'cpu_percent', 'create_time'])
                # 将创建时间转换为可读格式
                if proc_info['create_time']:
                    proc_info['create_time'] = datetime.datetime.fromtimestamp(proc_info['create_time']).strftime('%Y-%m-%d %H:%M:%S')
                
                # 添加额外信息
                proc_info['status'] = proc.status()
                proc_info['num_threads'] = proc.num_threads()
                
                # 获取内存信息
                try:
                    mem_info = proc.memory_info()
                    proc_info['memory_mb'] = round(mem_info.rss / (1024 * 1024), 2)
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    proc_info['memory_mb'] = None
                
                result.append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                self.logger.debug(f"获取进程信息失败: {e}")
                continue
        
        return result
    
    def start_auto_update(self) -> bool:
        """启动自动更新线程
        
        Returns:
            是否成功启动
        """
        if self.auto_update_enabled:
            self.logger.warning("自动更新线程已在运行")
            return False
            
        self.auto_update_enabled = True
        self._stop_event.clear()
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        self.logger.info(f"系统信息自动更新已启动，更新间隔：{self.update_interval}秒")
        return True
    
    def stop_auto_update(self) -> bool:
        """停止自动更新线程
        
        Returns:
            是否成功停止
        """
        if not self.auto_update_enabled:
            self.logger.warning("自动更新线程未在运行")
            return False
            
        self.auto_update_enabled = False
        self._stop_event.set()
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=2)
        self.logger.info("系统信息自动更新已停止")
        return True
    
    def set_update_interval(self, interval: float) -> None:
        """设置更新间隔
        
        Args:
            interval: 更新间隔（秒）
        """
        if interval <= 0:
            self.logger.error("更新间隔必须大于0")
            return
            
        self.update_interval = interval
        self.logger.info(f"系统信息更新间隔已设置为 {interval} 秒")
    
    def _update_loop(self) -> None:
        """自动更新线程的主循环"""
        self.logger.debug("系统信息更新线程已启动")
        
        while self.auto_update_enabled and not self._stop_event.is_set():
            try:
                self.update_metrics()
            except Exception as e:
                self.logger.error(f"更新系统信息时发生错误: {e}")
            
            # 等待指定时间或直到收到停止信号
            self._stop_event.wait(self.update_interval)
        
        self.logger.debug("系统信息更新线程已停止")
    
    def _send_update_event(self) -> None:
        """发送系统状态更新事件"""
        try:
            event = Event(
                event_type=EventType.SYSTEM_STATUS_UPDATE,
                sender=self.__class__.__name__,
                data={"timestamp": time.time(), "metrics": self.metrics}
            )
            self.event_system.dispatch_event(event)
        except Exception as e:
            self.logger.error(f"发送系统状态更新事件失败: {e}") 