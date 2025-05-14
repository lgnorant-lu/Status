"""
---------------------------------------------------------------
File name:                  animation.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                动画类
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

import logging
import time
from typing import List, Optional, Dict, Any, Union

from PySide6.QtGui import QImage

logger = logging.getLogger(__name__)

class Animation:
    """表示一个动画序列的类"""
    
    def __init__(self, name: str, frames: List[QImage], fps: int = 10):
        """初始化动画对象
        
        Args:
            name: 动画名称
            frames: 动画帧列表(QImage)
            fps: 每秒帧数
        """
        self.name = name
        self.frames = frames  # 帧列表
        self.fps = fps  # 每秒帧数
        self.current_frame_index = 0  # 当前帧索引
        self.metadata: Dict[str, Any] = {}  # 存储元数据的字典
        self.is_playing = False  # 是否正在播放
        self.is_looping = True  # 是否循环播放
        self.is_reversed = False  # 是否反向播放
        self.last_frame_time = 0.0  # 最后一帧的时间
    
    def next_frame(self) -> QImage:
        """获取下一帧图像
        
        Returns:
            QImage: 下一帧图像
        """
        if not self.frames:
            # 如果没有帧，返回空白图像
            return QImage()
            
        frame = self.frames[self.current_frame_index]
        
        # 更新帧索引
        if not self.is_reversed:
            self.current_frame_index = (self.current_frame_index + 1) % len(self.frames)
            # 如果动画播放到最后一帧且不循环，停止播放
            if self.current_frame_index == 0 and not self.is_looping:
                self.is_playing = False
        else:
            self.current_frame_index = (self.current_frame_index - 1) % len(self.frames)
            # 如果动画播放到第一帧且不循环，停止播放
            if self.current_frame_index == len(self.frames) - 1 and not self.is_looping:
                self.is_playing = False
                
        return frame
    
    def current_frame(self) -> QImage:
        """获取当前帧图像
        
        Returns:
            QImage: 当前帧图像
        """
        if not self.frames:
            return QImage()
        return self.frames[self.current_frame_index]
    
    def reset(self) -> None:
        """重置动画到第一帧"""
        self.current_frame_index = 0 if not self.is_reversed else len(self.frames) - 1
    
    def play(self) -> None:
        """开始播放动画"""
        self.is_playing = True
        self.last_frame_time = time.perf_counter()
    
    def pause(self) -> None:
        """暂停动画播放"""
        self.is_playing = False
    
    def stop(self) -> None:
        """停止动画播放并重置到第一帧"""
        self.is_playing = False
        self.reset()
    
    def set_loop(self, loop: bool) -> None:
        """设置是否循环播放
        
        Args:
            loop: 是否循环播放
        """
        self.is_looping = loop
    
    def set_reverse(self, reverse: bool) -> None:
        """设置是否反向播放
        
        Args:
            reverse: 是否反向播放
        """
        self.is_reversed = reverse
    
    def get_frame_count(self) -> int:
        """获取动画帧数
        
        Returns:
            int: 动画帧数
        """
        return len(self.frames)
    
    def get_duration(self) -> float:
        """获取动画持续时间（秒）
        
        Returns:
            float: 动画持续时间（秒）
        """
        return len(self.frames) / self.fps
    
    def get_frame_at_index(self, index: int) -> Optional[QImage]:
        """获取指定索引的帧图像
        
        Args:
            index: 帧索引
            
        Returns:
            Optional[QImage]: 指定索引的帧图像，如果索引无效则返回None
        """
        if 0 <= index < len(self.frames):
            return self.frames[index]
        return None
    
    def update(self, dt: float) -> bool:
        """更新动画状态
        
        Args:
            dt: 时间增量(秒)
            
        Returns:
            bool: 如果帧发生变化则返回True，否则返回False
        """
        if not self.is_playing or not self.frames:
            return False
        
        current_time = time.perf_counter()
        elapsed = current_time - self.last_frame_time
        
        # 计算每帧的持续时间(秒)
        frame_duration = 1.0 / self.fps
        
        if elapsed >= frame_duration:
            # 时间到了，更新到下一帧
            self.last_frame_time = current_time
            _ = self.next_frame()  # 更新到下一帧
            return True
            
        return False 