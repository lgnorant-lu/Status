"""
---------------------------------------------------------------
File name:                  system_info.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                系统信息收集模块，获取系统性能指标
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
                            2025/05/12: 修复类型提示;
                            2025/05/15: 修复Collection[Any]类型索引错误;
----
"""

import os
import sys
import time
import platform
import datetime
import logging
import threading
import typing
from typing import Dict, List, Optional, Any, Tuple, Union, cast, Type, TYPE_CHECKING
from types import ModuleType

# 尝试导入psutil库
try:
    import psutil
except ImportError:
    psutil = None  # type: ignore[assignment]

# 尝试导入GPUtil库（用于获取GPU信息）
try:
    import GPUtil # type: ignore [import-untyped]
except ImportError:
    GPUtil = None

from status.core.event_system import EventSystem, Event, EventType

# 确保psutil总是可导入的，即使变量为None
if psutil is None:
    # 创建一个模拟模块，避免None类型错误
    class MockNamedTuple:
        def _asdict(self):
            return vars(self)
            
    class VirtualMemory(MockNamedTuple):
        def __init__(self):
            self.total = 8 * (1024 ** 3)  # 8GB
            self.used = 4 * (1024 ** 3)   # 4GB
            self.free = 4 * (1024 ** 3)   # 4GB
            self.available = 4 * (1024 ** 3)  # 4GB
            self.percent = 50.0  # 50%
            
    class SwapMemory(MockNamedTuple):
        def __init__(self):
            self.total = 2 * (1024 ** 3)  # 2GB
            self.used = 0.5 * (1024 ** 3)  # 0.5GB
            self.free = 1.5 * (1024 ** 3)  # 1.5GB
            self.percent = 25.0  # 25%
            
    class DiskPartition(MockNamedTuple):
        def __init__(self, device="/dev/sda1", mountpoint="/", fstype="ext4"):
            self.device = device
            self.mountpoint = mountpoint
            self.fstype = fstype
            self.opts = "rw,relatime"
            
    class DiskUsage(MockNamedTuple):
        def __init__(self):
            self.total = 250 * (1024 ** 3)  # 250GB
            self.used = 100 * (1024 ** 3)   # 100GB
            self.free = 150 * (1024 ** 3)   # 150GB
            self.percent = 40.0  # 40%
            
    class CpuFreq(MockNamedTuple):
        def __init__(self):
            self.current = 2500  # 2.5GHz
            self.min = 800       # 0.8GHz
            self.max = 3200      # 3.2GHz
            
    class SensorTemp(MockNamedTuple):
        def __init__(self):
            self.label = "Core 0"
            self.current = 45.0  # 45°C
            self.high = 80.0     # 80°C
            self.critical = 95.0  # 95°C
    
    class PsutilMock:
        @staticmethod
        def cpu_count(logical=True):
            return 4 if logical else 2  # 返回默认值
        
        @staticmethod
        def getloadavg():
            return [0.5, 0.7, 0.9]  # 返回默认负载值
        
        @staticmethod
        def boot_time():
            return time.time() - 3600  # 模拟系统启动于1小时前
            
        @staticmethod
        def cpu_percent(interval=0.1, percpu=False):
            if percpu:
                return [25.0, 30.0, 15.0, 10.0]  # 4核心CPU使用率
            return 20.0  # 总体CPU使用率
            
        @staticmethod
        def sensors_temperatures():
            return {
                "coretemp": [SensorTemp(), SensorTemp(), SensorTemp(), SensorTemp()]
            }
            
        @staticmethod
        def cpu_freq(percpu=False):
            return CpuFreq()
            
        @staticmethod
        def virtual_memory():
            return VirtualMemory()
            
        @staticmethod
        def swap_memory():
            return SwapMemory()
            
        @staticmethod
        def disk_partitions():
            return [
                DiskPartition(),
                DiskPartition("/dev/sdb1", "/mnt/data", "ntfs")
            ]
            
        @staticmethod
        def disk_usage(path):
            return DiskUsage()
            
        @staticmethod
        def disk_io_counters(perdisk=False):
            return {}
            
        @staticmethod
        def net_io_counters(pernic=False):
            return {}
            
        @staticmethod
        def net_if_addrs():
            return {}
            
        @staticmethod
        def net_if_stats():
            return {}
            
        @staticmethod
        def net_connections():
            return []
    
    psutil = PsutilMock()  # type: ignore

class SystemInfo:
    """系统信息收集类，负责获取各项系统性能指标"""
    
    _instance = None
    _initialized: bool = False
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __new__(cls, *args, **kwargs):
        """创建单例实例"""
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
        
        # 缓存的系统指标数据
        self.metrics: Dict[str, Any] = {}
        
        # 更新间隔（秒）
        self.update_interval = update_interval
        
        # 自动更新控制
        self.auto_update_enabled = False
        self._stop_event = threading.Event()
        self.update_thread: Optional[threading.Thread] = None
        
        # 事件系统
        self.event_system = EventSystem()
        
        self._initialized = True
    
    def _get_system_info(self) -> Dict[str, Any]:
        """获取系统基本信息
        
        Returns:
            包含系统信息的字典
        """
        if not psutil:
            return {"error": "psutil未安装"}
            
        try:
            # 获取开机时间
            boot_time = time.time() - psutil.boot_time()
            
            info = {
                "os": {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "platform": platform.platform(),
                    "machine": platform.machine(),
                    "architecture": platform.architecture()[0],
                    "node": platform.node(),
                },
                "python": {
                    "version": platform.python_version(),
                    "implementation": platform.python_implementation(),
                    "compiler": platform.python_compiler(),
                },
                "processor": {
                    "name": platform.processor(),
                    "cores_physical": psutil.cpu_count(logical=False) or 1,  # 防止None
                    "cores_logical": psutil.cpu_count(logical=True) or 1,    # 防止None
                },
                "boot_time": datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
                "uptime_seconds": boot_time,
            }
            
            # 格式化正常运行时间为可读格式
            # 确保uptime是float类型
            uptime_val = info["uptime_seconds"]
            if isinstance(uptime_val, (int, float)):
                uptime = float(uptime_val) 
            else:
                # 如果不是数字类型，设置一个默认值
                uptime = 0.0
                self.logger.warning(f"uptime_seconds不是数字类型: {type(uptime_val)}")
                
            days, remainder = divmod(uptime, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            info["uptime"] = f"{int(days)}天 {int(hours)}小时 {int(minutes)}分钟 {int(seconds)}秒"
            
            return info
        except Exception as e:
            self.logger.error(f"获取系统信息失败: {e}")
            return {"error": str(e)}
    
    def get_basic_info(self) -> Dict[str, Any]:
        """获取系统基本信息，该信息通常不会变化，因此不缓存
        
        Returns:
            系统基本信息
        """
        return self._get_system_info()
    
    def update_metrics(self) -> Dict[str, Any]:
        """更新所有系统指标数据
        
        Returns:
            包含所有系统指标的字典
        """
        # 获取当前时间戳
        timestamp = time.time()
        
        # 更新各项指标
        self.metrics = {
            "timestamp": timestamp,
            "datetime": datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S"),
            "cpu": self.get_cpu_info(),
            "memory": self.get_memory_info(),
            "disk": self.get_disk_info(),
            "network": self.get_network_info(),
        }
        
        # 获取电池信息（如果可用）
        battery_info = self.get_battery_info()
        if battery_info:
            self.metrics["battery"] = battery_info
        
        # 获取GPU信息（如果可用）
        if GPUtil:
            try:
                gpus = GPUtil.getGPUs()
                gpu_info = []
                
                for gpu in gpus:
                    gpu_info.append({
                        "id": gpu.id,
                        "name": gpu.name,
                        "load": round(gpu.load * 100, 1),
                        "memory": {
                            "total": round(gpu.memoryTotal / 1024, 2),  # 转换为GB
                            "used": round(gpu.memoryUsed / 1024, 2),    # 转换为GB
                            "free": round(gpu.memoryFree / 1024, 2),    # 转换为GB
                            "percent": round(gpu.memoryUtil * 100, 1),
                        },
                        "temperature": gpu.temperature,
                    })
                
                if gpu_info:
                    self.metrics["gpu"] = gpu_info
            except Exception as e:
                self.logger.debug(f"获取GPU信息失败: {e}")
        
        # 获取进程信息
        self.metrics["processes"] = self.get_running_processes(limit=10)
        
        # 发送系统状态更新事件
        self._send_update_event()
        
        return self.metrics
    
    def get_cpu_info(self) -> Dict[str, Any]:
        """获取CPU信息
        
        Returns:
            CPU信息字典
        """
        if not psutil:
            return {"error": "psutil未安装"}
        
        # 获取CPU使用率和频率
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_percent_per_cpu = psutil.cpu_percent(interval=0.1, percpu=True)
        
        # 获取CPU温度（如果支持）
        temperatures = {}
        if hasattr(psutil, "sensors_temperatures"):
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    for chip, sensors in temps.items():
                        temperatures[chip] = [dict(t._asdict()) for t in sensors]
            except (AttributeError, OSError) as e:
                self.logger.debug(f"获取CPU温度失败: {e}")
        
        # 获取CPU频率
        freq_info = {}
        if hasattr(psutil, "cpu_freq"):
            try:
                freq = psutil.cpu_freq(percpu=False)
                if freq:
                    freq_info = dict(freq._asdict())
            except (AttributeError, OSError) as e:
                self.logger.debug(f"获取CPU频率失败: {e}")
        
        # 获取CPU负载
        try:
            # 确保cpu_count不为None
            cpu_count = psutil.cpu_count() or 1  # 如果为None，使用1
            load_avg = [x / cpu_count * 100 for x in psutil.getloadavg()]
        except (AttributeError, OSError):
            load_avg = []
        
        return {
            "percent_overall": cpu_percent,
            "percent_per_cpu": cpu_percent_per_cpu,
            "temperatures": temperatures,
            "frequency": freq_info,
            "load_avg": load_avg,
            "count": {
                "physical": psutil.cpu_count(logical=False),
                "logical": psutil.cpu_count(logical=True),
            },
        }
    
    def get_memory_info(self) -> Dict[str, Any]:
        """获取内存信息
        
        Returns:
            内存信息字典
        """
        if not psutil:
            return {"error": "psutil未安装"}
            
        # 获取物理内存使用情况
        vm = psutil.virtual_memory()
        vm_dict = dict(vm._asdict())
        
        # 计算GB单位
        gb_total = vm.total / (1024 ** 3)
        gb_used = vm.used / (1024 ** 3)
        gb_available = vm.available / (1024 ** 3)
        
        # 获取交换内存使用情况
        swap = psutil.swap_memory()
        swap_dict = dict(swap._asdict())
        
        # 计算GB单位
        swap_gb_total = swap.total / (1024 ** 3)
        swap_gb_used = swap.used / (1024 ** 3)
        swap_gb_free = swap.free / (1024 ** 3)
        
        return {
            "virtual": vm_dict,
            "swap": swap_dict,
            "percent": vm.percent,
            "total_gb": round(gb_total, 2),
            "used_gb": round(gb_used, 2),
            "available_gb": round(gb_available, 2),
            "swap_total_gb": round(swap_gb_total, 2),
            "swap_used_gb": round(swap_gb_used, 2),
            "swap_free_gb": round(swap_gb_free, 2),
            "swap_percent": swap.percent,
        }
    
    def get_disk_info(self) -> Dict[str, Any]:
        """获取磁盘信息
        
        Returns:
            磁盘信息字典
        """
        if not psutil:
            return {"error": "psutil未安装"}
        
        # 获取分区信息
        partitions = []
        for partition in psutil.disk_partitions():
            part_info = dict(partition._asdict())
            
            # 获取磁盘使用情况
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                usage_dict = dict(usage._asdict())
                
                # 计算GB单位
                gb_total = usage.total / (1024 ** 3)
                gb_used = usage.used / (1024 ** 3)
                gb_free = usage.free / (1024 ** 3)
                
                part_info["usage"] = usage_dict
                part_info["usage_gb"] = {
                    "total": round(gb_total, 2),
                    "used": round(gb_used, 2),
                    "free": round(gb_free, 2),
                }
            except (PermissionError, OSError) as e:
                self.logger.debug(f"无法获取分区 {partition.mountpoint} 的使用情况: {e}")
                part_info["usage"] = {"error": str(e)}
                part_info["usage_gb"] = {"error": str(e)}
            
            partitions.append(part_info)
        
        # 获取IO计数器
        try:
            io_counters = psutil.disk_io_counters()
            io_counters_dict = dict(io_counters._asdict()) if io_counters else {}
        except (AttributeError, OSError) as e:
            self.logger.debug(f"获取磁盘IO计数器失败: {e}")
            io_counters_dict = {"error": str(e)}
        
        # 获取每个磁盘的IO计数器
        disk_io = {}
        try:
            disk_io_counters = psutil.disk_io_counters(perdisk=True)
            if disk_io_counters:
                for disk, counters in disk_io_counters.items():
                    disk_io[disk] = dict(counters._asdict())
        except (AttributeError, OSError) as e:
            self.logger.debug(f"获取每个磁盘的IO计数器失败: {e}")
        
        return {
            "partitions": partitions,
            "io_counters": io_counters_dict,
            "io_counters_per_disk": disk_io,
        }
    
    def get_network_info(self) -> Dict[str, Any]:
        """获取网络信息
        
        Returns:
            网络信息字典
        """
        if not psutil:
            return {"error": "psutil未安装"}
            
        # 获取网络IO计数器
        try:
            io_counters = psutil.net_io_counters()
            io_counters_dict = dict(io_counters._asdict()) if io_counters else {}
        except (AttributeError, OSError) as e:
            self.logger.debug(f"获取网络IO计数器失败: {e}")
            io_counters_dict = {"error": str(e)}
        
        result: Dict[str, Any] = {
            "interfaces": {},
            "connections": [],
            "io_counters": io_counters_dict,
            "io_counters_per_nic": {},
        }
        
        # 获取网络接口信息
        net_if_addrs = psutil.net_if_addrs()
        net_if_stats = psutil.net_if_stats()
        
        for interface, addrs in net_if_addrs.items():
            if interface in net_if_stats:
                stats = dict(net_if_stats[interface]._asdict())
            else:
                stats = {}
                
            # 确保interfaces字典存在
            if interface not in result["interfaces"]:
                result["interfaces"][interface] = {
                    "addresses": [],
                    "stats": stats,
        }
            
            # 添加网络地址信息
            for addr in addrs:
                addr_info = dict(addr._asdict())
                # 添加到地址列表
                result["interfaces"][interface]["addresses"].append(addr_info)
        
        # 获取每个网卡的IO计数器
        if psutil.net_io_counters(pernic=True):
            for nic, counters in psutil.net_io_counters(pernic=True).items():
                result["io_counters_per_nic"][nic] = dict(counters._asdict())
        
        # 获取网络连接信息
        try:
            connections = psutil.net_connections()
            # 提前确保connections是列表类型
            if "connections" not in result or not isinstance(result["connections"], list):
                result["connections"] = []
            
            for conn in connections[:30]:  # 限制数量
                conn_info = dict(conn._asdict())
                if 'laddr' in conn_info and conn_info['laddr']:
                    conn_info['laddr'] = dict(conn_info['laddr']._asdict())
                if 'raddr' in conn_info and conn_info['raddr']:
                    conn_info['raddr'] = dict(conn_info['raddr']._asdict())
                # 添加到连接列表
                result["connections"].append(conn_info)
        except (psutil.AccessDenied, PermissionError) as e:
            self.logger.warning(f"无法获取网络连接信息: {e}")
            result["connections"] = [{"error": str(e)}]
        
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
            self.logger.warning("自动更新已经在运行中")
            return False
            
        self._stop_event.clear()
        self.auto_update_enabled = True
        
        # 创建并启动更新线程
        self.update_thread = threading.Thread(target=self._update_loop, name="SystemInfoUpdateThread")
        self.update_thread.daemon = True
        self.update_thread.start()
        
        self.logger.info(f"系统信息自动更新已启动，间隔: {self.update_interval}秒")
        return True
    
    def stop_auto_update(self) -> bool:
        """停止自动更新线程
        
        Returns:
            是否成功停止
        """
        if not self.auto_update_enabled:
            self.logger.warning("自动更新未在运行")
            return False
            
        self._stop_event.set()
        self.auto_update_enabled = False
        
        if self.update_thread and self.update_thread.is_alive():
            self.logger.info("等待更新线程结束...")
            self.update_thread.join(timeout=2.0)
        
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
        event_data = {
            "metrics": self.metrics,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        
        # 使用str()将枚举值转换为字符串类型
        self.event_system.dispatch_event(EventType.SYSTEM_STATUS_UPDATE, self, event_data) 
