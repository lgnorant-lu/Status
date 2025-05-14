"""
---------------------------------------------------------------
File name:                  enhanced_time_manager.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                增强的时间动画管理器
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

import os
import logging
import time
from typing import Dict, Tuple, List, Optional, Union, Set
from PIL import Image
from PySide6.QtGui import QImage
from PySide6.QtCore import QObject, Signal

from status.animation.time_animation_manager import TimeAnimationManager
from status.animation.animation import Animation
from status.behavior.time_based_behavior import TimePeriod, SpecialDate
from status.core.types import AnimationSequence


class EnhancedTimeAnimationManager(TimeAnimationManager):
    """增强的时间动画管理器，扩展TimeAnimationManager提供更丰富的动画功能"""

    def __init__(self, base_path: str = ""):
        """初始化增强型时间动画管理器

        Args:
            base_path: 动画资源的基础路径
        """
        super().__init__(base_path)
        
        # 新增管理字典
        self.festival_animations: Dict[str, Animation] = {}
        self.solar_term_animations: Dict[str, Animation] = {}
        
        # 内存优化参数
        self.max_image_width: int = 512
        self.max_image_height: int = 512
        
        # 用于缓存的字典
        self._image_cache: Dict[str, QImage] = {}
        
        # 设置日志记录器
        self.logger = logging.getLogger(__name__)
        
        # 节日与其英文名称映射
        self.festival_name_mapping: Dict[str, str] = {
            "春节": "spring_festival",
            "元宵节": "lantern_festival",
            "端午节": "dragon_boat",
            "中秋节": "mid_autumn",
            "国庆节": "national_day",
            "元旦": "new_year_day"
        }
        
        # 节气与其英文名称映射
        self.solar_term_mapping: Dict[str, str] = {
            "立春": "spring_begins",
            "雨水": "rain_water",
            "惊蛰": "insects_awaken",
            "春分": "vernal_equinox",
            "清明": "clear_and_bright",
            "谷雨": "grain_rain",
            "立夏": "summer_begins",
            "小满": "grain_buds",
            "芒种": "grain_in_ear",
            "夏至": "summer_solstice",
            "小暑": "slight_heat",
            "大暑": "great_heat",
            "立秋": "autumn_begins",
            "处暑": "end_of_heat",
            "白露": "white_dew",
            "秋分": "autumn_equinox",
            "寒露": "cold_dew",
            "霜降": "frost_descent",
            "立冬": "winter_begins",
            "小雪": "light_snow",
            "大雪": "heavy_snow",
            "冬至": "winter_solstice",
            "小寒": "slight_cold",
            "大寒": "great_cold"
        }

    def load_festival_animations(self, resource_path: str = "") -> bool:
        """加载节日动画

        Args:
            resource_path: 节日动画资源路径，默认为空使用默认路径

        Returns:
            bool: 是否成功加载
        """
        if not resource_path:
            resource_path = os.path.join(self.base_path, "resources", "animations", "festivals")
        
        self.logger.info(f"加载节日动画从: {resource_path}")
        
        if not os.path.exists(resource_path):
            self.logger.warning(f"节日动画目录不存在: {resource_path}")
            return False
        
        # 扫描目录，加载所有子目录作为节日动画
        for item in os.listdir(resource_path):
            item_path = os.path.join(resource_path, item)
            if os.path.isdir(item_path):
                animation = self._load_animation_from_path(item_path, f"festival_{item}")
                if animation:
                    self.festival_animations[item] = animation
                    self.animation_loaded.emit(f"festival_{item}", animation)
                    self.logger.debug(f"加载节日动画: {item}")
        
        return len(self.festival_animations) > 0

    def load_solar_term_animations(self, resource_path: str = "") -> bool:
        """加载节气动画

        Args:
            resource_path: 节气动画资源路径，默认为空使用默认路径

        Returns:
            bool: 是否成功加载
        """
        if not resource_path:
            resource_path = os.path.join(self.base_path, "resources", "animations", "solar_terms")
        
        self.logger.info(f"加载节气动画从: {resource_path}")
        
        if not os.path.exists(resource_path):
            self.logger.warning(f"节气动画目录不存在: {resource_path}")
            return False
        
        # 扫描目录，加载所有子目录作为节气动画
        for item in os.listdir(resource_path):
            item_path = os.path.join(resource_path, item)
            if os.path.isdir(item_path):
                animation = self._load_animation_from_path(item_path, f"solar_term_{item}")
                if animation:
                    self.solar_term_animations[item] = animation
                    self.animation_loaded.emit(f"solar_term_{item}", animation)
                    self.logger.debug(f"加载节气动画: {item}")
        
        return len(self.solar_term_animations) > 0

    def get_animation_for_festival(self, festival_name: str) -> Animation:
        """获取指定节日的动画

        Args:
            festival_name: 节日名称，可以是中文或英文

        Returns:
            Animation: 节日动画，如果不存在则返回占位符
        """
        # 先尝试直接查找
        if festival_name in self.festival_animations:
            return self.festival_animations[festival_name]
        
        # 尝试通过中文名查找对应的英文名
        if festival_name in self.festival_name_mapping:
            english_name = self.festival_name_mapping[festival_name]
            if english_name in self.festival_animations:
                return self.festival_animations[english_name]
        
        # 如果仍然找不到，创建并返回占位符动画
        self.logger.warning(f"未找到节日动画: {festival_name}，使用占位符")
        placeholder_animation = self._create_placeholder_animation(f"festival_{festival_name}")
        return placeholder_animation

    def get_animation_for_solar_term(self, term_name: str) -> Animation:
        """获取指定节气的动画

        Args:
            term_name: 节气名称，可以是中文或英文

        Returns:
            Animation: 节气动画，如果不存在则返回占位符
        """
        # 先尝试直接查找
        if term_name in self.solar_term_animations:
            return self.solar_term_animations[term_name]
        
        # 尝试通过中文名查找对应的英文名
        if term_name in self.solar_term_mapping:
            english_name = self.solar_term_mapping[term_name]
            if english_name in self.solar_term_animations:
                return self.solar_term_animations[english_name]
        
        # 如果仍然找不到，创建并返回占位符动画
        self.logger.warning(f"未找到节气动画: {term_name}，使用占位符")
        placeholder_animation = self._create_placeholder_animation(f"solar_term_{term_name}")
        return placeholder_animation

    def get_animation_for_special_date(self, special_date: Union[str, SpecialDate]) -> Animation:
        """获取特殊日期的动画，扩展基类方法支持SpecialDate对象

        Args:
            special_date: 特殊日期名称或SpecialDate对象

        Returns:
            Animation: 特殊日期动画
        """
        if isinstance(special_date, SpecialDate):
            # 根据特殊日期类型选择不同的查找方法
            date_type = getattr(special_date, "type", "")
            if date_type == "solar_term":
                return self.get_animation_for_solar_term(special_date.name)
            elif date_type == "festival" or special_date.is_lunar:
                return self.get_animation_for_festival(special_date.name)
            else:
                # 使用基类方法
                return super().get_animation_for_special_date(special_date.name)
        else:
            # 字符串情况，先检查节日和节气
            if special_date in self.festival_name_mapping or special_date in self.festival_animations:
                return self.get_animation_for_festival(special_date)
            elif special_date in self.solar_term_mapping or special_date in self.solar_term_animations:
                return self.get_animation_for_solar_term(special_date)
            else:
                # 使用基类方法
                return super().get_animation_for_special_date(special_date)

    def load_animation_optimized(self, directory: str, name: str) -> Optional[Animation]:
        """加载动画并进行内存优化

        Args:
            directory: 动画文件目录
            name: 动画名称

        Returns:
            Optional[Animation]: 优化后的动画，如果加载失败则返回None
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
            
            # 检查缓存
            if file_path in self._image_cache:
                frames.append(self._image_cache[file_path])
                continue
            
            # 使用PIL优化图像大小
            try:
                with Image.open(file_path) as img:
                    # 检查是否需要调整大小
                    if img.width > self.max_image_width or img.height > self.max_image_height:
                        # 计算缩放比例
                        ratio = min(self.max_image_width / img.width, self.max_image_height / img.height)
                        new_size = (int(img.width * ratio), int(img.height * ratio))
                        # 使用高质量重采样方法 (1 = LANCZOS/ANTIALIAS)
                        img = img.resize(new_size, 1)
                        
                        # 保存优化后的图像
                        optimized_path = os.path.join(directory, f"opt_{file}")
                        img.save(optimized_path)
                        file_path = optimized_path
            
                # 加载为QImage
                q_image = QImage(file_path)
                if q_image.isNull():
                    self.logger.warning(f"无法加载图像: {file_path}")
                    continue
                
                # 添加到缓存
                self._image_cache[file_path] = q_image
                frames.append(q_image)
            
            except Exception as e:
                self.logger.error(f"处理图像时出错 {file_path}: {str(e)}")
                continue
        
        if not frames:
            self.logger.warning(f"没有成功加载任何帧: {directory}")
            return None
        
        # 创建动画对象
        animation = Animation(name=name, frames=frames)
        animation.metadata["source_dir"] = directory
        
        return animation

    def get_smooth_transition(self, from_period: TimePeriod, to_period: TimePeriod) -> List[Animation]:
        """获取平滑过渡的动画序列

        Args:
            from_period: 起始时间段
            to_period: 目标时间段

        Returns:
            List[Animation]: 动画序列，包含过渡动画
        """
        sequence = []
        
        # 获取起始和目标时间段的动画
        from_animation = self.get_animation_for_time_period(from_period)
        to_animation = self.get_animation_for_time_period(to_period)
        
        # 检查是否有直接的过渡动画
        transition_key = (from_period, to_period)
        if transition_key in self.transition_animations:
            # 有过渡动画，返回[起始动画，过渡动画，目标动画]
            sequence = [from_animation, self.transition_animations[transition_key], to_animation]
        else:
            # 没有过渡动画，返回[起始动画，目标动画]
            sequence = [from_animation, to_animation]
        
        return sequence

    def clear_cache(self) -> None:
        """清除图像缓存"""
        self._image_cache.clear()
        self.logger.info("已清除图像缓存") 