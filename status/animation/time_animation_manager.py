"""
---------------------------------------------------------------
File name:                  time_animation_manager.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                时间动画管理器
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

import os
import logging
from typing import Dict, Optional, List, Union, Tuple
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage, QColor

from status.animation.animation import Animation
from status.behavior.time_based_behavior import TimePeriod


class TimeAnimationManager(QObject):
    """时间动画管理器，负责加载和管理与时间相关的动画"""
    
    # 信号：动画加载完成
    animation_loaded = Signal(str, Animation)
    
    def __init__(self, base_path: str = ""):
        """初始化时间动画管理器
        
        Args:
            base_path: 动画资源的基础路径
        """
        super().__init__()
        
        # 资源基础路径
        self.base_path = base_path
        
        # 时间段动画字典
        self.time_period_animations: Dict[TimePeriod, Animation] = {}
        
        # 特殊日期动画字典
        self.special_date_animations: Dict[str, Animation] = {}
        
        # 过渡动画字典
        self.transition_animations: Dict[Tuple[TimePeriod, TimePeriod], Animation] = {}
        
        # 设置日志记录器
        self.logger = logging.getLogger(__name__)
        
    def load_time_period_animations(self, resource_path: str = "") -> bool:
        """加载时间段动画
        
        Args:
            resource_path: 时间段动画资源路径，默认为空使用默认路径
            
        Returns:
            bool: 是否成功加载
        """
        if not resource_path:
            resource_path = os.path.join(self.base_path, "resources", "animations", "time")
        
        # 检查目录是否存在
        if not os.path.exists(resource_path):
            self.logger.warning(f"时间段动画目录不存在: {resource_path}")
            return False
        
        # 清空现有动画
        self.time_period_animations.clear()
        
        # 加载各时间段动画
        period_dirs = {
            "morning": TimePeriod.MORNING,
            "noon": TimePeriod.NOON,
            "afternoon": TimePeriod.AFTERNOON,
            "evening": TimePeriod.EVENING,
            "night": TimePeriod.NIGHT
        }
        
        for dir_name, period in period_dirs.items():
            dir_path = os.path.join(resource_path, dir_name)
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                animation = self._load_animation_from_path(dir_path, f"time_{dir_name}")
                if animation:
                    self.time_period_animations[period] = animation
                    self.animation_loaded.emit(f"time_{dir_name}", animation)
                    self.logger.debug(f"加载时间段动画: {dir_name}")
        
        return len(self.time_period_animations) > 0
    
    def load_special_date_animations(self, resource_path: str = "") -> bool:
        """加载特殊日期动画
        
        Args:
            resource_path: 特殊日期动画资源路径，默认为空使用默认路径
            
        Returns:
            bool: 是否成功加载
        """
        if not resource_path:
            resource_path = os.path.join(self.base_path, "resources", "animations", "special_dates")
        
        # 检查目录是否存在
        if not os.path.exists(resource_path):
            self.logger.warning(f"特殊日期动画目录不存在: {resource_path}")
            return False
        
        # 清空现有动画
        self.special_date_animations.clear()
        
        # 预定义的特殊日期列表
        special_dates = [
            "new_year", "birthday", "valentine", "birth_of_status_ming"
        ]
        
        for date_name in special_dates:
            dir_path = os.path.join(resource_path, date_name)
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                animation = self._load_animation_from_path(dir_path, f"special_{date_name}")
                if animation:
                    self.special_date_animations[date_name] = animation
                    self.animation_loaded.emit(f"special_{date_name}", animation)
                    self.logger.debug(f"加载特殊日期动画: {date_name}")
        
        return len(self.special_date_animations) > 0
    
    def load_transition_animations(self, resource_path: str = "") -> bool:
        """加载时间段过渡动画
        
        Args:
            resource_path: 过渡动画资源路径，默认为空使用默认路径
            
        Returns:
            bool: 是否成功加载
        """
        if not resource_path:
            resource_path = os.path.join(self.base_path, "resources", "animations", "transitions")
        
        # 检查目录是否存在
        if not os.path.exists(resource_path):
            self.logger.warning(f"过渡动画目录不存在: {resource_path}")
            return False
        
        # 清空现有动画
        self.transition_animations.clear()
        
        # 预定义过渡动画列表
        transitions = [
            ("morning_to_noon", TimePeriod.MORNING, TimePeriod.NOON),
            ("noon_to_afternoon", TimePeriod.NOON, TimePeriod.AFTERNOON),
            ("afternoon_to_evening", TimePeriod.AFTERNOON, TimePeriod.EVENING),
            ("evening_to_night", TimePeriod.EVENING, TimePeriod.NIGHT),
            ("night_to_morning", TimePeriod.NIGHT, TimePeriod.MORNING)
        ]
        
        for name, from_period, to_period in transitions:
            dir_path = os.path.join(resource_path, name)
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                animation = self._load_animation_from_path(dir_path, f"transition_{name}")
                if animation:
                    self.transition_animations[(from_period, to_period)] = animation
                    self.animation_loaded.emit(f"transition_{name}", animation)
                    self.logger.debug(f"加载过渡动画: {name}")
        
        return len(self.transition_animations) > 0
    
    def get_animation_for_time_period(self, period: TimePeriod) -> Animation:
        """获取指定时间段的动画
        
        Args:
            period: 时间段
            
        Returns:
            Animation: 时间段动画，如果不存在则返回占位符
        """
        if period in self.time_period_animations:
            return self.time_period_animations[period]
        
        # 如果没有找到对应的动画，创建并返回占位符
        self.logger.warning(f"未找到时间段动画: {period}，使用占位符")
        placeholder_animation = self._create_placeholder_animation(f"time_{period.name.lower()}")
        return placeholder_animation
    
    def get_animation_for_special_date(self, date_name: str) -> Animation:
        """获取指定特殊日期的动画
        
        Args:
            date_name: 特殊日期名称
            
        Returns:
            Animation: 特殊日期动画，如果不存在则返回占位符
        """
        # 处理特殊情况
        if date_name == "Birth of Status-Ming!":
            date_name = "birth_of_status_ming"
        
        # 中文名称映射
        chinese_to_english = {
            "新年": "new_year",
            "生日": "birthday",
            "情人节": "valentine"
        }
        
        # 检查中文名称映射
        if date_name in chinese_to_english:
            date_name = chinese_to_english[date_name]
        
        if date_name in self.special_date_animations:
            return self.special_date_animations[date_name]
        
        # 如果没有找到对应的动画，创建并返回占位符
        self.logger.warning(f"未找到特殊日期动画: {date_name}，使用占位符")
        placeholder_animation = self._create_placeholder_animation(f"special_{date_name}")
        return placeholder_animation
    
    def get_transition_animation(self, from_period: TimePeriod, to_period: TimePeriod) -> Optional[Animation]:
        """获取两个时间段之间的过渡动画
        
        Args:
            from_period: 起始时间段
            to_period: 目标时间段
            
        Returns:
            Optional[Animation]: 过渡动画，如果不存在则返回None
        """
        transition_key = (from_period, to_period)
        if transition_key in self.transition_animations:
            return self.transition_animations[transition_key]
        
        # 如果没有直接的过渡动画
        self.logger.warning(f"未找到过渡动画: {from_period.name} -> {to_period.name}")
        return None
    
    def on_time_period_changed(self, from_period: TimePeriod, to_period: TimePeriod) -> Animation:
        """响应时间段变化事件
        
        Args:
            from_period: 先前的时间段
            to_period: 当前时间段
            
        Returns:
            Animation: 要播放的动画
        """
        # 尝试获取过渡动画
        transition_animation = self.get_transition_animation(from_period, to_period)
        
        if transition_animation:
            # 有过渡动画，返回过渡动画
            self.logger.info(f"时间变化: {from_period.name} -> {to_period.name}，使用过渡动画")
            return transition_animation
        else:
            # 没有过渡动画，直接返回目标时间段的动画
            self.logger.info(f"时间变化: {from_period.name} -> {to_period.name}，直接切换动画")
            return self.get_animation_for_time_period(to_period)
    
    def on_special_date_triggered(self, date_name: str, description: str = "") -> Animation:
        """响应特殊日期触发事件
        
        Args:
            date_name: 特殊日期名称
            description: 特殊日期描述
            
        Returns:
            Animation: 要播放的动画
        """
        animation = self.get_animation_for_special_date(date_name)
        self.logger.info(f"特殊日期触发: {date_name} - {description}")
        return animation
    
    def _load_animation_from_path(self, directory: str, name: str) -> Optional[Animation]:
        """从目录加载动画
        
        Args:
            directory: 动画文件目录
            name: 动画名称
            
        Returns:
            Optional[Animation]: 加载的动画，如果加载失败则返回None
        """
        if not os.path.exists(directory):
            self.logger.warning(f"目录不存在: {directory}")
            return None
        
        # 收集所有图片文件
        frames = []
        files = sorted([f for f in os.listdir(directory) if f.endswith(('.png', '.jpg', '.jpeg', '.gif'))])
        
        if not files:
            self.logger.warning(f"目录中没有图片文件: {directory}")
            return None
        
        for file in files:
            file_path = os.path.join(directory, file)
            image = QImage(file_path)
            if image.isNull():
                self.logger.warning(f"无法加载图像: {file_path}")
                continue
            frames.append(image)
        
        if not frames:
            self.logger.warning(f"没有成功加载任何帧: {directory}")
            return None
        
        # 创建动画对象
        animation = Animation(name=name, frames=frames)
        animation.metadata["source_dir"] = directory
        
        # 设置为循环播放
        animation.set_loop(True)
        
        return animation
    
    def _create_placeholder_animation(self, name: str) -> Animation:
        """创建占位符动画
        
        Args:
            name: 占位符动画名称
            
        Returns:
            Animation: 占位符动画
        """
        # 创建简单的占位符动画
        size = 100
        frame1 = QImage(size, size, QImage.Format.Format_ARGB32)
        frame2 = QImage(size, size, QImage.Format.Format_ARGB32)
        
        # 根据名称选择不同颜色
        if name.startswith("time_"):
            frame1.fill(QColor(200, 200, 255, 150))  # 淡蓝色
            frame2.fill(QColor(180, 180, 255, 150))
        elif name.startswith("special_"):
            frame1.fill(QColor(255, 200, 200, 150))  # 淡红色
            frame2.fill(QColor(255, 180, 180, 150))
        else:
            frame1.fill(QColor(200, 255, 200, 150))  # 淡绿色
            frame2.fill(QColor(180, 255, 180, 150))
        
        # 创建简单的交替动画
        animation = Animation(name=name, frames=[frame1, frame2])
        animation.metadata["placeholder"] = True
        animation.metadata["description"] = f"占位符动画: {name}"
        
        # 设置为循环播放
        animation.set_loop(True)
        
        return animation