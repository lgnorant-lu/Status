"""
---------------------------------------------------------------
File name:                  animation.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                基本动画类，支持帧动画播放
----------------------------------------------------------------

Changed history:            
                            2025/05/13: 初始创建;
----
"""

import logging
import time
from typing import List, Optional, Dict, Any, Union

from PySide6.QtGui import QImage

logger = logging.getLogger(__name__)

class Animation:
    """基础动画类，支持帧动画播放"""
    
    def __init__(self):
        """初始化动画"""
        self.frames: List[QImage] = []  # 帧列表
        self.frame_durations: List[int] = []  # 每帧持续时间(毫秒)
        self.current_frame_index = 0  # 当前帧索引
        self.is_playing = False  # 是否正在播放
        self.is_looping = False  # 是否循环播放
        self.last_frame_time = 0.0  # 最后一帧的时间
        self.metadata: Dict[str, Any] = {}  # 元数据
    
    def add_frame(self, image: QImage, duration_ms: int = 100) -> None:
        """添加一帧到动画
        
        Args:
            image: 帧图像
            duration_ms: 持续时间(毫秒)
        """
        self.frames.append(image)
        self.frame_durations.append(duration_ms)
    
    def set_frames(self, frames: List[QImage], durations: Union[List[int], int] = 100) -> None:
        """设置动画帧序列
        
        Args:
            frames: 帧列表
            durations: 每帧持续时间，可以是单个值或列表
        """
        self.frames = frames
        
        # 如果durations是单个值，为每一帧都应用相同的持续时间
        if isinstance(durations, int):
            self.frame_durations = [durations] * len(frames)
        else:
            # 确保durations与frames长度一致
            if len(durations) != len(frames):
                logger.warning(f"帧数量({len(frames)})与持续时间数量({len(durations)})不匹配，将使用默认值")
                self.frame_durations = [100] * len(frames)
            else:
                self.frame_durations = durations
    
    def get_current_frame(self) -> Optional[QImage]:
        """获取当前帧
        
        Returns:
            当前帧图像，如果没有帧则返回None
        """
        if not self.frames:
            return None
        
        return self.frames[self.current_frame_index]
    
    def set_loop(self, loop: bool) -> None:
        """设置是否循环播放
        
        Args:
            loop: 是否循环播放
        """
        self.is_looping = loop
    
    def play(self) -> None:
        """开始播放动画"""
        if not self.frames:
            logger.warning("尝试播放没有帧的动画")
            return
        
        self.is_playing = True
        self.last_frame_time = time.perf_counter()
    
    def pause(self) -> None:
        """暂停动画"""
        self.is_playing = False
    
    def stop(self) -> None:
        """停止动画并重置到第一帧"""
        self.is_playing = False
        self.current_frame_index = 0
    
    def update(self, dt: float) -> bool:
        """更新动画
        
        Args:
            dt: 时间增量(秒)
            
        Returns:
            bool: 当前帧是否改变
        """
        if not self.is_playing or not self.frames:
            return False
        
        current_time = time.perf_counter()
        elapsed = (current_time - self.last_frame_time) * 1000  # 转换为毫秒
        
        # 获取当前帧的持续时间
        current_duration = self.frame_durations[self.current_frame_index]
        
        # 如果经过的时间超过了当前帧的持续时间，切换到下一帧
        if elapsed >= current_duration:
            # 更新最后一帧的时间
            self.last_frame_time = current_time
            
            # 切换到下一帧
            self.current_frame_index += 1
            
            # 如果到达末尾
            if self.current_frame_index >= len(self.frames):
                if self.is_looping:
                    # 循环播放，从头开始
                    self.current_frame_index = 0
                else:
                    # 不循环播放，停留在最后一帧
                    self.current_frame_index = len(self.frames) - 1
                    self.is_playing = False
            
            return True  # 帧已经改变
        
        return False  # 帧没有改变 