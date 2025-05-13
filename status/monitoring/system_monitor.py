"""
---------------------------------------------------------------
File name:                  system_monitor.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                系统监控模块，获取CPU、内存等系统信息
----------------------------------------------------------------

Changed history:            
                            2025/04/07: 初始创建;
                            2025/04/08: 添加详细系统信息;
                            2025/05/14: 添加时间数据功能;
----
"""

import psutil
import platform
import logging
import time
import datetime
from enum import Enum, auto
import os
from typing import Dict, Any, Optional, List, Tuple

# 导入事件系统相关
from status.core.events import EventManager, SystemStatsUpdatedEvent, EventType, get_app_instance

# 直接导入时间相关模块，避免依赖于应用实例
from status.behavior.time_based_behavior import TimePeriod, SpecialDate, LunarHelper

logger = logging.getLogger(__name__)

# 全局变量，用于存储上次的网络和磁盘IO计数，计算实时速率
_last_net_io: Optional[Dict[str, int]] = None
_last_disk_io: Optional[Dict[str, int]] = None
_last_check_time: float = 0.0

def get_cpu_usage() -> float:
    """获取当前的CPU平均使用率

    Returns:
        float: CPU使用率 (0.0 到 100.0)
    """
    try:
        # interval=None 获取自上次调用或模块初始化以来的平均CPU使用率
        # 这通常比 interval=0.1 或更高更适合快速、低开销的读取
        usage = psutil.cpu_percent(interval=None)
        logger.debug(f"psutil.cpu_percent returned: {usage}")
        return usage if usage is not None else 0.0
    except Exception as e:
        logger.error(f"获取CPU使用率时发生错误: {e}")
        return 0.0 # 发生错误时返回0.0，确保函数总有float返回 

def get_memory_usage() -> float:
    """获取当前内存使用率百分比"""
    try:
        memory_info = psutil.virtual_memory()
        logger.debug(f"内存信息: {memory_info}") # 记录原始信息以供调试
        return memory_info.percent
    except Exception as e:
        logger.error(f"获取内存使用率时出错: {e}")
        return 0.0 # 发生错误时返回 0

def get_cpu_cores_usage() -> list:
    """获取每个CPU核心的使用率

    Returns:
        list: 每个CPU核心的使用率列表
    """
    try:
        cores_usage = psutil.cpu_percent(percpu=True)
        logger.debug(f"CPU核心使用率: {cores_usage}")
        return cores_usage
    except Exception as e:
        logger.error(f"获取CPU核心使用率时出错: {e}")
        return [] # 发生错误时返回空列表

def get_memory_details() -> dict:
    """获取详细的内存使用情况

    Returns:
        dict: 包含内存详细信息的字典，包括总内存、可用内存、已用内存、空闲内存及使用率
    """
    try:
        memory_info = psutil.virtual_memory()
        
        # 转换为MB，并保留整数精度
        total_mb = int(memory_info.total / (1024 * 1024))
        available_mb = int(memory_info.available / (1024 * 1024))
        used_mb = int(memory_info.used / (1024 * 1024))
        free_mb = int(memory_info.free / (1024 * 1024))
        
        memory_details = {
            'total_mb': total_mb,
            'available_mb': available_mb,
            'used_mb': used_mb,
            'free_mb': free_mb,
            'percent': memory_info.percent
        }
        
        logger.debug(f"内存详细信息: {memory_details}")
        return memory_details
    except Exception as e:
        logger.error(f"获取内存详细信息时出错: {e}")
        return {
            'total_mb': 0,
            'available_mb': 0,
            'used_mb': 0,
            'free_mb': 0,
            'percent': 0.0
        }

def get_disk_usage(path='/') -> dict:
    """获取指定路径的磁盘使用情况

    Args:
        path: 要检查的磁盘路径，默认为根目录

    Returns:
        dict: 包含磁盘使用情况的字典，包括总容量、已用空间、可用空间及使用率
    """
    try:
        disk_info = psutil.disk_usage(path)
        
        # 转换为GB，保留2位小数
        total_gb = round(disk_info.total / (1024 * 1024 * 1024), 2)
        used_gb = round(disk_info.used / (1024 * 1024 * 1024), 2)
        free_gb = round(disk_info.free / (1024 * 1024 * 1024), 2)
        
        disk_details = {
            'total_gb': total_gb,
            'used_gb': used_gb,
            'free_gb': free_gb,
            'percent': disk_info.percent
        }
        
        logger.debug(f"磁盘使用情况 ({path}): {disk_details}")
        return disk_details
    except Exception as e:
        logger.error(f"获取磁盘使用情况时出错 ({path}): {e}")
        return {
            'total_gb': 0.0,
            'used_gb': 0.0,
            'free_gb': 0.0,
            'percent': 0.0
        }

def get_network_info() -> dict:
    """获取网络使用情况

    Returns:
        dict: 包含网络使用情况的字典，包括已发送和已接收的数据量
    """
    try:
        net_info = psutil.net_io_counters()
        
        # 转换为MB，保留2位小数
        sent_mb = round(net_info.bytes_sent / (1024 * 1024), 2)
        recv_mb = round(net_info.bytes_recv / (1024 * 1024), 2)
        
        network_info = {
            'sent_mb': sent_mb,
            'recv_mb': recv_mb
        }
        
        logger.debug(f"网络使用情况: {network_info}")
        return network_info
    except Exception as e:
        logger.error(f"获取网络使用情况时出错: {e}")
        return {
            'sent_mb': 0.0,
            'recv_mb': 0.0
        }

def get_network_io() -> dict:
    """获取网络IO原始数据，用于计算实时速度

    Returns:
        dict: 包含发送和接收字节数的字典
    """
    try:
        net_io = psutil.net_io_counters()
        return {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv
        }
    except Exception as e:
        logger.error(f"获取网络IO数据时出错: {e}")
        return {
            'bytes_sent': 0,
            'bytes_recv': 0
        }

def calculate_network_speed(prev_net: dict, curr_net: dict, time_diff: float) -> dict:
    """计算网络速度

    Args:
        prev_net: 上次获取的网络IO数据
        curr_net: 当前获取的网络IO数据
        time_diff: 两次获取之间的时间差（秒）

    Returns:
        dict: 包含上传和下载速度的字典（KB/s）
    """
    if time_diff <= 0:
        return {
            'upload_kbps': 0,
            'download_kbps': 0
        }
    
    try:
        # 计算上传速度 (KB/s)
        bytes_sent_diff = curr_net['bytes_sent'] - prev_net['bytes_sent']
        upload_speed = round(bytes_sent_diff / 1024 / time_diff, 2)
        
        # 计算下载速度 (KB/s)
        bytes_recv_diff = curr_net['bytes_recv'] - prev_net['bytes_recv']
        download_speed = round(bytes_recv_diff / 1024 / time_diff, 2)
        
        return {
            'upload_kbps': upload_speed,
            'download_kbps': download_speed
        }
    except Exception as e:
        logger.error(f"计算网络速度时出错: {e}")
        return {
            'upload_kbps': 0,
            'download_kbps': 0
        }

def get_network_speed() -> dict:
    """获取实时网络速度（上传和下载）

    Returns:
        dict: 包含实时网络速度的字典，单位为KB/s
    """
    global _last_net_io, _last_check_time
    try:
        current_time = time.time()
        current_net_io = get_network_io()
        
        # 默认值
        upload_speed = 0.0
        download_speed = 0.0
        
        # 如果有上次的数据，计算速度
        if _last_net_io is not None and _last_check_time > 0:
            time_diff = current_time - _last_check_time  # 时间差(秒)
            if time_diff > 0:  # 防止除以0
                net_speed = calculate_network_speed(_last_net_io, current_net_io, time_diff)
                upload_speed = net_speed['upload_kbps']
                download_speed = net_speed['download_kbps']
        
        # 更新上次的数据
        _last_net_io = current_net_io
        _last_check_time = current_time
        
        logger.debug(f"网络速度: 上传 {upload_speed} KB/s, 下载 {download_speed} KB/s")
        return {
            'upload_kbps': upload_speed,
            'download_kbps': download_speed
        }
    except Exception as e:
        logger.error(f"获取网络速度时出错: {e}")
        return {
            'upload_kbps': 0.0,
            'download_kbps': 0.0
        }

def get_disk_io() -> dict:
    """获取磁盘IO原始数据，用于计算实时速度

    Returns:
        dict: 包含读取和写入字节数的字典
    """
    try:
        disk_io = psutil.disk_io_counters()
        if disk_io is None:
            return {'read_bytes': 0, 'write_bytes': 0}
        return {
            'read_bytes': disk_io.read_bytes,
            'write_bytes': disk_io.write_bytes
        }
    except Exception as e:
        logger.error(f"获取磁盘IO数据时出错: {e}")
        return {
            'read_bytes': 0,
            'write_bytes': 0
        }

def calculate_disk_io_speed(prev_io: dict, curr_io: dict, time_diff: float) -> dict:
    """计算磁盘IO速度

    Args:
        prev_io: 上次获取的磁盘IO数据
        curr_io: 当前获取的磁盘IO数据
        time_diff: 两次获取之间的时间差（秒）

    Returns:
        dict: 包含读取和写入速度的字典（KB/s）
    """
    if time_diff <= 0:
        return {
            'read_kbps': 0,
            'write_kbps': 0
        }
    
    try:
        # 计算读取速度 (KB/s)
        read_bytes_diff = curr_io['read_bytes'] - prev_io['read_bytes']
        read_speed = round(read_bytes_diff / 1024 / time_diff, 2)
        
        # 计算写入速度 (KB/s)
        write_bytes_diff = curr_io['write_bytes'] - prev_io['write_bytes']
        write_speed = round(write_bytes_diff / 1024 / time_diff, 2)
        
        return {
            'read_kbps': read_speed,
            'write_kbps': write_speed
        }
    except Exception as e:
        logger.error(f"计算磁盘IO速度时出错: {e}")
        return {
            'read_kbps': 0,
            'write_kbps': 0
        }

def get_disk_io_speed() -> dict:
    """获取实时磁盘IO速度（读写）

    Returns:
        dict: 包含实时磁盘IO速度的字典，单位为MB/s
    """
    global _last_disk_io, _last_check_time # _last_check_time共享用于网络和磁盘
    try:
        current_time = time.time()
        current_disk_io = get_disk_io()
        
        # 默认值
        read_speed = 0.0
        write_speed = 0.0
        
        # 如果有上次的数据，计算速度
        if _last_disk_io is not None and _last_check_time > 0:
            time_diff = current_time - _last_check_time  # 时间差(秒)
            if time_diff > 0:  # 防止除以0
                io_speed = calculate_disk_io_speed(_last_disk_io, current_disk_io, time_diff)
                read_speed = io_speed['read_kbps']
                write_speed = io_speed['write_kbps']
        
        # 更新上次的数据
        _last_disk_io = current_disk_io
        # _last_check_time 已在get_network_speed中更新，这里不再重复更新以避免竞争
        
        logger.debug(f"磁盘IO速度: 读取 {read_speed} KB/s, 写入 {write_speed} KB/s")
        return {
            'read_mbps': read_speed,
            'write_mbps': write_speed
        }
    except Exception as e:
        logger.error(f"获取磁盘IO速度时出错: {e}", exc_info=True)
        return {
            'read_mbps': 0.0,
            'write_mbps': 0.0
        }

def get_gpu_info() -> dict:
    """获取GPU相关信息 (需要GPUtil库)

    Returns:
        dict: 包含GPU信息的字典 (负载、内存使用、温度等)
    """
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if not gpus:
            logger.debug("未检测到GPU。")
            return {"error": "No GPU detected"}

        gpu_data_list = []
        for gpu in gpus:
            gpu_data = {
                "id": gpu.id,
                "name": gpu.name,
                "load": gpu.load * 100,  # 转换为百分比
                "memoryUtil": gpu.memoryUtil * 100, # 转换为百分比
                "memoryTotal": gpu.memoryTotal,
                "memoryUsed": gpu.memoryUsed,
                "memoryFree": gpu.memoryFree,
                "temperature": gpu.temperature
            }
            gpu_data_list.append(gpu_data)
        
        logger.debug(f"获取到的GPU信息: {gpu_data_list}")
        # 简化处理，如果只有一个GPU，直接返回其数据，否则返回列表
        return gpu_data_list[0] if len(gpu_data_list) == 1 else {"gpus": gpu_data_list}

    except ImportError:
        logger.warning("GPUtil库未安装，无法获取GPU信息。请运行 'pip install GPUtil'")
        return {"error": "GPUtil not installed"}
    except Exception as e:
        logger.error(f"获取GPU信息时出错: {e}")
        return {"error": str(e)}

def get_current_time_period() -> TimePeriod:
    """获取当前时间段
    
    Returns:
        TimePeriod: 当前时间段
    """
    now = datetime.datetime.now()
    hour = now.hour
    
    if 5 <= hour < 12:
        return TimePeriod.MORNING
    elif 12 <= hour < 14:
        return TimePeriod.NOON
    elif 14 <= hour < 18:
        return TimePeriod.AFTERNOON
    elif 18 <= hour < 23:
        return TimePeriod.EVENING
    else:  # 23, 0, 1, 2, 3, 4
        return TimePeriod.NIGHT

def get_special_dates() -> List[Tuple[SpecialDate, datetime.date]]:
    """获取当前活跃的特殊日期
    
    Returns:
        List[Tuple[SpecialDate, datetime.date]]: 特殊日期列表，每个元素是一个元组(特殊日期, 对应的公历日期)
    """
    try:
        # 获取今天日期
        today = datetime.date.today()
        
        # 创建一些默认的特殊日期
        special_dates = []
        
        # 检查是否是某些重要节日
        # 这里仅作示例，实际应使用完整实现
        if today.month == 5 and today.day == 19:
            special_dates.append(
                (SpecialDate.create_solar_festival("Birth of Status-Ming", 5, 19, "Status-Ming 诞辰"), today)
            )
        elif today.month == 1 and today.day == 1:
            special_dates.append(
                (SpecialDate.create_solar_festival("元旦", 1, 1, "新的一年开始了"), today)
            )
        elif today.month == 6 and today.day == 1:
            special_dates.append(
                (SpecialDate.create_solar_festival("儿童节", 6, 1, "六一儿童节"), today)
            )
        elif today.month == 5 and today.day == 31:
            special_dates.append(
                (SpecialDate.create_solar_festival("端午节", 5, 31, "端午节，吃粽子"), today)
            )
        
        return special_dates
    except Exception as e:
        logger.error(f"获取特殊日期出错: {e}")
        return []

def get_upcoming_special_dates(days: int = 7) -> List[Tuple[SpecialDate, datetime.date]]:
    """获取未来n天内的特殊日期
    
    Args:
        days: 往后检查的天数
        
    Returns:
        List[Tuple[SpecialDate, datetime.date]]: 特殊日期列表，每个元素是一个元组(特殊日期, 对应的公历日期)
    """
    try:
        today = datetime.date.today()
        upcoming_dates = []
        
        # 创建一些默认的特殊日期
        # 这里仅作示例
        birth_date = SpecialDate.create_solar_festival("Birth of Status-Ming", 5, 19, "Status-Ming 诞辰")
        children_day = SpecialDate.create_solar_festival("儿童节", 6, 1, "六一儿童节")
        dragon_boat = SpecialDate.create_solar_festival("端午节", 5, 31, "端午节，吃粽子")
        
        # 检查日期是否在接下来的days天内
        birth_date_date = datetime.date(today.year, 5, 19)
        if birth_date_date < today:
            birth_date_date = datetime.date(today.year + 1, 5, 19)
        if (birth_date_date - today).days <= days:
            upcoming_dates.append((birth_date, birth_date_date))
            
        children_day_date = datetime.date(today.year, 6, 1)
        if children_day_date < today:
            children_day_date = datetime.date(today.year + 1, 6, 1)
        if (children_day_date - today).days <= days:
            upcoming_dates.append((children_day, children_day_date))
            
        dragon_boat_date = datetime.date(today.year, 5, 31)
        if dragon_boat_date < today:
            dragon_boat_date = datetime.date(today.year + 1, 5, 31)
        if (dragon_boat_date - today).days <= days:
            upcoming_dates.append((dragon_boat, dragon_boat_date))
            
        # 按日期排序
        upcoming_dates.sort(key=lambda x: x[1])
        
        return upcoming_dates
    except Exception as e:
        logger.error(f"获取未来特殊日期出错: {e}")
        return []

def get_time_data() -> Dict[str, Any]:
    """获取时间相关数据
    
    Returns:
        Dict[str, Any]: 包含时间段、特殊日期等信息的字典
    """
    time_data = {}
    
    # 获取当前时间段
    current_period = get_current_time_period()
    time_data["period"] = current_period.name
    
    # 尝试获取特殊日期信息
    try:
        # 获取当前特殊日期
        special_dates = get_special_dates()
        if special_dates:
            first_date, _ = special_dates[0]
            time_data["special_date"] = {
                "name": first_date.name,
                "description": first_date.description
            }
        
        # 获取即将到来的特殊日期
        upcoming_dates = get_upcoming_special_dates(days=7)
        if upcoming_dates:
            upcoming_list = []
            for date_obj, date_time in upcoming_dates[:3]:  # 只取前3个
                upcoming_list.append({
                    "name": date_obj.name,
                    "date": date_time.strftime("%Y-%m-%d"),
                    "description": date_obj.description
                })
            time_data["upcoming_dates"] = upcoming_list
    except Exception as e:
        logger.error(f"获取特殊日期数据失败: {e}")
    
    return time_data

def publish_stats(include_details: bool = False):
    """发布系统统计信息
    
    Args:
        include_details: 是否包含详细的系统指标
    """
    logger.info("开始收集系统统计信息...")

    # 获取基本指标
    cpu_usage = get_cpu_usage()
    memory_usage = get_memory_usage()
    
    # 构建基本数据
    stats_data: Dict[str, Any] = {
        "cpu_usage": cpu_usage,
        "memory_usage": memory_usage,
    }
    
    # 如果需要详细指标
    if include_details:
        # 获取CPU核心使用率
        try:
            cpu_cores = get_cpu_cores_usage()
            stats_data["cpu_cores_usage"] = cpu_cores
        except Exception as e:
            logger.error(f"获取CPU核心使用率失败: {e}")
        
        # 获取内存详情
        try:
            memory_details = get_memory_details()
            stats_data["memory_details"] = memory_details
        except Exception as e:
            logger.error(f"获取内存详情失败: {e}")
            
        # 获取磁盘使用率
        try:
            disk_info = get_disk_usage()
            # 保存完整磁盘信息，而不仅仅是百分比
            stats_data["disk_usage_root"] = disk_info
            # 同时保持原有的disk_usage百分比，确保兼容性
            stats_data["disk_usage"] = disk_info.get("percent", 0.0)
        except Exception as e:
            logger.error(f"获取磁盘使用率失败: {e}")
        
        # 获取网络信息
        try:
            network_info = get_network_info()
            stats_data["network_info"] = network_info
        except Exception as e:
            logger.error(f"获取网络信息失败: {e}")
            
        # 获取网络速度
        try:
            network_speed = get_network_speed()
            stats_data["network_speed"] = network_speed
            
            # 计算总网络使用率（上传+下载）作为指标
            total_network = network_speed.get("upload_kbps", 0.0) + network_speed.get("download_kbps", 0.0)
            # 转换为百分比形式（假设100Mbps为标准带宽）
            network_percent = min(100.0, (total_network / 1024) * 10)  # 10Mbps = 100%
            stats_data["network_usage"] = network_percent
        except Exception as e:
            logger.error(f"获取网络速度失败: {e}")
            
        # 获取磁盘IO速度
        try:
            disk_io_speed = get_disk_io_speed()
            stats_data["disk_io_speed"] = disk_io_speed
        except Exception as e:
            logger.error(f"获取磁盘IO速度失败: {e}")
            
        # 获取GPU信息
        try:
            gpu_info = get_gpu_info()
            stats_data["gpu_info"] = gpu_info
            
            # 提取GPU使用率
            if isinstance(gpu_info, dict) and "load" in gpu_info:
                # 如果是单个GPU，直接使用其负载
                stats_data["gpu_usage"] = gpu_info.get("load", 0.0)
            elif isinstance(gpu_info, dict) and "gpus" in gpu_info:
                # 如果是多GPU，计算平均负载
                gpus = gpu_info.get("gpus", [])
                if gpus:
                    avg_load = sum(gpu.get("load", 0.0) for gpu in gpus) / len(gpus)
                    stats_data["gpu_usage"] = avg_load
                else:
                    stats_data["gpu_usage"] = 0.0
            else:
                stats_data["gpu_usage"] = 0.0
        except Exception as e:
            logger.error(f"获取GPU信息失败: {e}")
        
        # 添加时间数据 - 首先尝试从时间行为系统获取
        try:
            # 使用全局函数获取应用主实例
            app = get_app_instance()
            time_data_added = False
            
            # 如果找到应用实例且存在时间行为系统
            if app and hasattr(app, 'time_behavior_system') and app.time_behavior_system and app.time_behavior_system.is_active:
                tbs = app.time_behavior_system
                logger.debug(f"时间行为系统实例: {tbs}, 已初始化: {tbs.is_initialized}, 已激活: {tbs.is_active}")
                
                # 添加当前时间段
                current_period = tbs.get_current_period()
                if current_period:
                    stats_data["period"] = current_period.name
                    logger.debug(f"从时间行为系统获取到当前时间段: {current_period.name}")
                
                # 添加当前特殊日期
                special_dates = tbs.get_current_special_dates()
                if special_dates:
                    first_date = special_dates[0]
                    stats_data["special_date"] = {
                        "name": first_date.name,
                        "description": first_date.description
                    }
                    logger.debug(f"从时间行为系统获取到当前特殊日期: {first_date.name}")
                
                # 添加即将到来的特殊日期
                upcoming_dates = tbs.get_upcoming_special_dates(days=7)
                if upcoming_dates:
                    upcoming_list = []
                    for date_obj, date_time in upcoming_dates[:3]:  # 只取前3个
                        upcoming_list.append({
                            "name": date_obj.name,
                            "date": date_time.strftime("%Y-%m-%d"),
                            "description": date_obj.description
                        })
                    stats_data["upcoming_dates"] = upcoming_list
                    logger.debug(f"从时间行为系统获取到即将到来的特殊日期: {len(upcoming_list)}个")
                
                logger.debug(f"已添加时间行为系统数据: 当前时间段={current_period.name if current_period else '未知'}")
                time_data_added = True
            
            # 如果无法从时间行为系统获取数据，使用独立函数
            if not time_data_added:
                logger.debug("无法从时间行为系统获取数据，使用独立函数获取时间数据")
                time_data = get_time_data()
                stats_data.update(time_data)
                logger.debug(f"使用独立函数获取的时间数据: {time_data}")
        except Exception as e:
            # 如果上述方法失败，确保至少有基本的时间数据
            logger.error(f"获取时间数据失败, 使用备用方法: {e}", exc_info=True)
            try:
                # 使用备用方法获取时间数据
                time_data = get_time_data()
                stats_data.update(time_data)
                logger.debug("使用备用方法成功获取时间数据")
            except Exception as e2:
                logger.error(f"备用时间数据获取也失败: {e2}")
    
    # 检查并记录时间相关数据
    time_related_keys = ['period', 'special_date', 'upcoming_dates']
    time_data_exists = any(key in stats_data for key in time_related_keys)
    
    if time_data_exists:
        # 只记录确实存在的数据
        time_data = {k: stats_data[k] for k in time_related_keys if k in stats_data}
        time_keys = list(time_data.keys())
        logger.info(f"系统统计包含时间数据: 包含{time_keys}")
    else:
        # 如果没有时间数据但需要详细信息，尝试添加基本时间段
        if include_details:
            try:
                current_period = get_current_time_period()
                stats_data['period'] = current_period.name
                logger.info(f"添加基本时间段信息: {current_period.name}")
            except Exception as e:
                logger.error(f"添加基本时间段失败: {e}")
    
    # 创建事件对象
    event = SystemStatsUpdatedEvent(stats_data=stats_data, sender="SystemMonitor")
    
    # 发布事件
    event_manager = EventManager.get_instance()
    event_manager.dispatch(event)
    
    detailed_str = "详细" if include_details else "基本"
    logger.info(f"系统{detailed_str}统计信息已发布: CPU {cpu_usage:.1f}%, Mem {memory_usage:.1f}%")

# 可以在这里添加其他系统监控函数