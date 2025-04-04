"""
---------------------------------------------------------------
File name:                  monitor_example.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                系统监控模块使用示例
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import time
import logging
import json
from typing import Dict, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 导入监控模块
from status.monitoring import SystemMonitor


class SimpleConsoleUI:
    """简单的控制台UI类，用于显示系统状态"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.latest_data = None
        
    def update(self, data: Dict[str, Any]) -> None:
        """更新UI显示
        
        Args:
            data: 系统状态数据
        """
        self.latest_data = data
        
        # 如果是告警，特殊处理
        if data.get("alert"):
            self._display_alert(data)
            return
            
        # 显示基本系统信息
        self._display_system_info(data)
    
    def _display_alert(self, alert_data: Dict[str, Any]) -> None:
        """显示告警信息
        
        Args:
            alert_data: 告警数据
        """
        alert_type = alert_data.get("alert_type", "unknown")
        message = alert_data.get("message", "未知告警")
        timestamp = alert_data.get("timestamp", time.time())
        
        # 格式化时间戳
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        
        # 打印告警信息
        print("\n" + "="*50)
        print(f"[告警] {time_str}")
        print(f"类型: {alert_type}")
        print(f"消息: {message}")
        print("="*50 + "\n")
    
    def _display_system_info(self, status_data: Dict[str, Any]) -> None:
        """显示系统信息
        
        Args:
            status_data: 系统状态数据
        """
        # 获取指标数据
        metrics = status_data.get("metrics", {})
        if not metrics:
            return
            
        # 清屏（仅在实际终端环境中有效）
        print("\033[H\033[J", end="")
        
        print("="*50)
        print("系统监控状态")
        print("="*50)
        
        # 显示时间
        timestamp = status_data.get("timestamp", time.time())
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        print(f"更新时间: {time_str}")
        
        # 显示CPU信息
        if "cpu" in metrics:
            cpu_data = metrics["cpu"]
            cpu_percent = cpu_data.get("percent_overall", 0)
            print(f"\nCPU 使用率: {cpu_percent:.1f}%")
            
            # 显示每个核心的使用率
            per_cpu = cpu_data.get("percent_per_cpu", [])
            if per_cpu:
                cores_str = " ".join([f"{p:.1f}%" for p in per_cpu])
                print(f"CPU 核心: {cores_str}")
        
        # 显示内存信息
        if "memory" in metrics:
            memory_data = metrics["memory"]
            memory_percent = memory_data.get("percent", 0)
            used_gb = memory_data.get("used_gb", 0)
            total_gb = memory_data.get("total_gb", 0)
            print(f"\n内存使用率: {memory_percent:.1f}% ({used_gb:.1f}GB / {total_gb:.1f}GB)")
        
        # 显示磁盘信息
        if "disk" in metrics and "partitions" in metrics["disk"]:
            print("\n磁盘使用情况:")
            for partition in metrics["disk"]["partitions"]:
                mountpoint = partition.get("mountpoint", "unknown")
                if "usage" in partition and "percent" in partition["usage"]:
                    usage_percent = partition["usage"]["percent"]
                    total_gb = partition.get("usage_gb", {}).get("total", 0)
                    used_gb = partition.get("usage_gb", {}).get("used", 0)
                    print(f"  {mountpoint}: {usage_percent:.1f}% ({used_gb:.1f}GB / {total_gb:.1f}GB)")
        
        # 显示网络信息
        if "network" in metrics and "io_counters" in metrics["network"]:
            io = metrics["network"]["io_counters"]
            sent_mb = io.get("bytes_sent", 0) / (1024 * 1024)
            recv_mb = io.get("bytes_recv", 0) / (1024 * 1024)
            print(f"\n网络流量: 发送 {sent_mb:.2f}MB, 接收 {recv_mb:.2f}MB")
        
        # 显示电池信息
        if "battery" in metrics and metrics["battery"] and "percent" in metrics["battery"]:
            battery_data = metrics["battery"]
            battery_percent = battery_data.get("percent", 0)
            is_plugged = battery_data.get("power_plugged", False)
            time_left = battery_data.get("time_left", "未知")
            
            status = "接入电源" if is_plugged else f"剩余时间 {time_left}"
            print(f"\n电池电量: {battery_percent:.1f}% ({status})")
        
        print("="*50)


def custom_data_processor(timestamp, metrics, history, stats):
    """自定义数据处理器示例
    
    Args:
        timestamp: 时间戳
        metrics: 系统指标数据
        history: 历史数据
        stats: 统计数据
    """
    # 简单示例：计算CPU使用率变化率
    if "cpu" in metrics and "cpu" in stats:
        current_cpu = metrics["cpu"].get("percent_overall", 0)
        avg_cpu = stats["cpu"].get("avg", 0)
        
        if avg_cpu > 0:
            change_rate = ((current_cpu - avg_cpu) / avg_cpu) * 100
            print(f"CPU变化率: {change_rate:.2f}%")


def main():
    """主函数"""
    # 创建系统监控器实例
    monitor = SystemMonitor(update_interval=2.0)
    
    # 创建并注册一个简单的控制台UI
    console_ui = SimpleConsoleUI()
    monitor.register_ui_component("console", console_ui)
    
    # 注册自定义数据处理器
    monitor.register_custom_processor("custom_processor", custom_data_processor)
    
    # 设置自定义告警阈值
    monitor.set_threshold("cpu_high", 70.0)  # CPU使用率超过70%告警
    monitor.set_threshold("memory_high", 75.0)  # 内存使用率超过75%告警
    monitor.set_threshold("disk_space_low", 15.0)  # 磁盘剩余空间低于15%告警
    
    try:
        # 启动监控
        if monitor.start():
            print("系统监控已启动，按Ctrl+C停止...")
            
            # 运行30秒
            time.sleep(30)
            
            # 获取统计数据
            stats = monitor.get_stats()
            print("\n统计数据:")
            print(json.dumps(stats, indent=2))
            
            # 获取CPU历史数据
            cpu_history = monitor.get_history("cpu", 5)
            print("\nCPU历史数据 (最近5条):")
            for entry in cpu_history:
                print(f"  {entry.get('percent', 0):.1f}%")
        else:
            print("启动系统监控失败")
    except KeyboardInterrupt:
        print("\n用户中断，正在停止监控...")
    finally:
        # 停止监控
        monitor.stop()
        print("系统监控已停止")


if __name__ == "__main__":
    main() 