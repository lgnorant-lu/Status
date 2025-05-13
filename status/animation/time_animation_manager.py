"""
---------------------------------------------------------------
File name:                  time_animation_manager.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                时间相关动画管理器
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Union

from PySide6.QtCore import QObject, Slot, Signal
from PySide6.QtGui import QImage

from status.animation.animation import Animation
from status.behavior.time_based_behavior import TimePeriod, SpecialDate


class TimeAnimationManager(QObject):
    """时间相关动画管理器，负责加载和管理基于时间的动画资源"""
    
    # 信号定义
    animation_loaded = Signal(str, object)  # 动画加载完成信号，参数：动画名称, 动画对象
    
    def __init__(self, base_path: str = ""):
        """初始化时间动画管理器
        
        Args:
            base_path: 动画资源的基础路径，默认为空（使用相对路径）
        """
        super().__init__()
        
        self.logger = logging.getLogger("Status.Animation.TimeAnimationManager")
        
        # 基础路径
        self.base_path = base_path
        
        # 时间段对应的动画
        self.time_period_animations: Dict[TimePeriod, Animation] = {}
        
        # 特殊日期对应的动画
        self.special_date_animations: Dict[str, Animation] = {}
        
        # 过渡动画
        self.transition_animations: Dict[Tuple[TimePeriod, TimePeriod], Animation] = {}
        
        self.logger.info("时间动画管理器初始化完成")
    
    def load_time_period_animations(self, resource_path: str = "resources/animations/time") -> bool:
        """加载时间段动画
        
        Args:
            resource_path: 时间动画资源路径
            
        Returns:
            bool: 是否成功加载所有动画
        """
        # 确保完整路径
        full_path = os.path.join(self.base_path, resource_path)
        
        if not os.path.exists(full_path):
            self.logger.warning(f"时间动画资源路径不存在: {full_path}")
            return False
        
        # 加载每个时间段的动画
        success = True
        for period in TimePeriod:
            period_name = period.name.lower()
            period_path = os.path.join(full_path, period_name)
            
            if os.path.exists(period_path):
                animation = self._load_animation_from_path(period_path, f"time_{period_name}")
                if animation:
                    self.time_period_animations[period] = animation
                    self.animation_loaded.emit(f"time_{period_name}", animation)
                    self.logger.info(f"加载时间段动画: {period_name}")
                else:
                    success = False
                    self.logger.error(f"无法加载时间段动画: {period_name}")
            else:
                success = False
                self.logger.warning(f"时间段动画路径不存在: {period_path}")
        
        return success
    
    def load_special_date_animations(self, resource_path: str = "resources/animations/special_dates") -> bool:
        """加载特殊日期动画
        
        Args:
            resource_path: 特殊日期动画资源路径
            
        Returns:
            bool: 是否成功加载所有动画
        """
        # 确保完整路径
        full_path = os.path.join(self.base_path, resource_path)
        
        if not os.path.exists(full_path):
            self.logger.warning(f"特殊日期动画资源路径不存在: {full_path}")
            return False
        
        # 加载特殊日期动画
        # 预定义一些常见节日
        special_dates = [
            "new_year",      # 新年
            "spring_festival", # 春节
            "lantern_festival", # 元宵节
            "dragon_boat",    # 端午节
            "mid_autumn",     # 中秋节
            "national_day",   # 国庆节
            "christmas"       # 圣诞节
        ]
        
        success = True
        for date_name in special_dates:
            date_path = os.path.join(full_path, date_name)
            
            if os.path.exists(date_path):
                animation = self._load_animation_from_path(date_path, f"special_{date_name}")
                if animation:
                    self.special_date_animations[date_name] = animation
                    self.animation_loaded.emit(f"special_{date_name}", animation)
                    self.logger.info(f"加载特殊日期动画: {date_name}")
                else:
                    success = False
                    self.logger.error(f"无法加载特殊日期动画: {date_name}")
            else:
                success = False
                self.logger.warning(f"特殊日期动画路径不存在: {date_path}")
        
        return success
    
    def load_transition_animations(self, resource_path: str = "resources/animations/transitions") -> bool:
        """加载过渡动画
        
        Args:
            resource_path: 过渡动画资源路径
            
        Returns:
            bool: 是否成功加载所有动画
        """
        # 确保完整路径
        full_path = os.path.join(self.base_path, resource_path)
        
        if not os.path.exists(full_path):
            self.logger.warning(f"过渡动画资源路径不存在: {full_path}")
            return False
        
        # 为了简化，仅加载几个重要的过渡动画
        # 例如：早上->中午，中午->晚上，晚上->夜晚，夜晚->早上
        transitions = [
            (TimePeriod.MORNING, TimePeriod.NOON),
            (TimePeriod.NOON, TimePeriod.AFTERNOON),
            (TimePeriod.AFTERNOON, TimePeriod.EVENING),
            (TimePeriod.EVENING, TimePeriod.NIGHT),
            (TimePeriod.NIGHT, TimePeriod.MORNING)
        ]
        
        success = True
        for from_period, to_period in transitions:
            transition_name = f"{from_period.name.lower()}_to_{to_period.name.lower()}"
            transition_path = os.path.join(full_path, transition_name)
            
            if os.path.exists(transition_path):
                animation = self._load_animation_from_path(transition_path, f"transition_{transition_name}")
                if animation:
                    self.transition_animations[(from_period, to_period)] = animation
                    self.animation_loaded.emit(f"transition_{transition_name}", animation)
                    self.logger.info(f"加载过渡动画: {transition_name}")
                else:
                    success = False
                    self.logger.error(f"无法加载过渡动画: {transition_name}")
            else:
                success = False
                self.logger.warning(f"过渡动画路径不存在: {transition_path}")
        
        return success
    
    def _load_animation_from_path(self, path: str, name: str) -> Optional[Animation]:
        """从指定路径加载动画
        
        Args:
            path: 动画资源路径
            name: 动画名称
            
        Returns:
            Optional[Animation]: 动画对象，如果加载失败则返回None
        """
        try:
            # 创建动画对象
            animation = Animation()
            
            # 检查路径是文件还是目录
            if os.path.isfile(path):
                # 单一图像文件 - 需要加载为QImage
                image = QImage(path)
                if not image.isNull():
                    animation.add_frame(image)
                else:
                    self.logger.error(f"无法加载图像文件: {path}")
                    return None
            elif os.path.isdir(path):
                # 目录中的多个图像文件
                # 查找所有图像文件（支持png和jpg格式）
                image_files = []
                for file in os.listdir(path):
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        image_files.append(os.path.join(path, file))
                
                # 按名称排序，以确保帧顺序正确
                image_files.sort()
                
                # 添加所有帧
                for image_file in image_files:
                    # 加载为QImage对象
                    image = QImage(image_file)
                    if not image.isNull():
                        animation.add_frame(image)
                    else:
                        self.logger.warning(f"无法加载图像文件: {image_file}")
                
                if not animation.frames:
                    self.logger.error(f"目录中没有有效的图像文件: {path}")
                    return None
            else:
                self.logger.error(f"路径既不是文件也不是目录: {path}")
                return None
            
            # 设置循环播放
            animation.set_loop(True)
            
            # 设置元数据
            animation.metadata["name"] = name
            animation.metadata["source_path"] = path
            
            return animation
        except Exception as e:
            self.logger.error(f"加载动画失败: {path} - {e}")
            return None
    
    def get_animation_for_time_period(self, period: TimePeriod) -> Optional[Animation]:
        """获取指定时间段的动画
        
        Args:
            period: 时间段
            
        Returns:
            Optional[Animation]: 动画对象，如果不存在则返回None
        """
        return self.time_period_animations.get(period)
    
    def get_animation_for_special_date(self, date_name: str) -> Optional[Animation]:
        """获取指定特殊日期的动画
        
        Args:
            date_name: 特殊日期名称
            
        Returns:
            Optional[Animation]: 动画对象，如果不存在则返回None
        """
        # 尝试直接匹配
        if date_name in self.special_date_animations:
            return self.special_date_animations[date_name]
        
        # 尝试转换为英文名称匹配（简单映射示例）
        name_map = {
            "新年": "new_year",
            "春节": "spring_festival",
            "元宵节": "lantern_festival",
            "端午节": "dragon_boat",
            "中秋节": "mid_autumn",
            "国庆节": "national_day",
            "圣诞节": "christmas"
        }
        
        if date_name in name_map and name_map[date_name] in self.special_date_animations:
            return self.special_date_animations[name_map[date_name]]
        
        return None
    
    def get_transition_animation(self, from_period: TimePeriod, to_period: TimePeriod) -> Optional[Animation]:
        """获取两个时间段之间的过渡动画
        
        Args:
            from_period: 起始时间段
            to_period: 目标时间段
            
        Returns:
            Optional[Animation]: 过渡动画对象，如果不存在则返回None
        """
        return self.transition_animations.get((from_period, to_period))
    
    @Slot(TimePeriod, TimePeriod)
    def on_time_period_changed(self, new_period: TimePeriod, old_period: TimePeriod) -> Optional[Animation]:
        """响应时间段变化
        
        Args:
            new_period: 新的时间段
            old_period: 旧的时间段
            
        Returns:
            Optional[Animation]: 应该播放的动画（优先返回过渡动画，否则返回新时间段的动画）
        """
        # 优先使用过渡动画
        transition_animation = self.get_transition_animation(old_period, new_period)
        if transition_animation:
            self.logger.debug(f"使用过渡动画: {old_period.name} -> {new_period.name}")
            return transition_animation
        
        # 如果没有过渡动画，使用时间段动画
        time_animation = self.get_animation_for_time_period(new_period)
        if time_animation:
            self.logger.debug(f"使用时间段动画: {new_period.name}")
            return time_animation
        
        # 如果没有相应的动画，返回None
        self.logger.warning(f"找不到时间段动画: {new_period.name}")
        return None
    
    @Slot(str, str)
    def on_special_date_triggered(self, date_name: str, description: str) -> Optional[Animation]:
        """响应特殊日期触发
        
        Args:
            date_name: 特殊日期名称
            description: 特殊日期描述
            
        Returns:
            Optional[Animation]: 应该播放的动画
        """
        animation = self.get_animation_for_special_date(date_name)
        if animation:
            self.logger.debug(f"使用特殊日期动画: {date_name}")
            return animation
        
        self.logger.warning(f"找不到特殊日期动画: {date_name}")
        return None 
    
    def _create_placeholder_animation(self, name: str) -> Optional[Animation]:
        """创建占位符动画，用于资源不存在时
        
        Args:
            name: 动画名称
            
        Returns:
            Optional[Animation]: 占位符动画对象，如果创建失败则返回None
        """
        try:
            # 创建动画对象
            animation = Animation()
            
            # 创建占位符图像
            # 注意：实际应用中应该创建更好的占位符图像
            size = 100
            image = QImage(size, size, QImage.Format.Format_ARGB32)  # 使用QImage.Format_ARGB32格式创建图像
            image.fill(0)  # 填充透明背景
            
            # 根据名称设置不同颜色
            if "morning" in name:
                image.fill(0xFF87CEEB)  # 天蓝色
            elif "noon" in name:
                image.fill(0xFFFFD700)  # 金色
            elif "afternoon" in name:
                image.fill(0xFF32CD32)  # 绿色
            elif "evening" in name:
                image.fill(0xFFFF8C00)  # 深橙色
            elif "night" in name:
                image.fill(0xFF483D8B)  # 深蓝色
            elif "new_year" in name or "spring_festival" in name:
                image.fill(0xFFFF0000)  # 红色
            elif "christmas" in name:
                image.fill(0xFF006400)  # 深绿色
            else:
                image.fill(0xFFB0C4DE)  # 默认浅蓝色
                
            animation.add_frame(image)
            animation.add_frame(image)  # 添加两帧相同图像以支持动画播放
            
            # 设置循环播放
            animation.set_loop(True)
            
            # 设置元数据
            animation.metadata["name"] = name
            animation.metadata["placeholder"] = True
            
            return animation
        except Exception as e:
            self.logger.error(f"创建占位符动画失败: {name} - {e}")
            return None