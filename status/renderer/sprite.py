"""
---------------------------------------------------------------
File name:                  sprite.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                精灵渲染系统，实现精灵和精灵表支持
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

from typing import Dict, List, Tuple, Optional, Any, Union
import math
import time

from status.renderer.renderer_base import RendererBase, Color, Rect, RenderLayer
from status.renderer.drawable import Drawable
from status.resources.asset_manager import AssetManager

class SpriteFrame:
    """精灵帧类，表示精灵表中的一帧"""
    
    def __init__(self, image_path: str, source_rect: Rect, pivot: Optional[Tuple[float, float]] = None):
        """初始化精灵帧
        
        Args:
            image_path: 图像路径
            source_rect: 源矩形，指定图像的子区域
            pivot: 锚点，相对于左上角的偏移，默认为中心点
        """
        self.image_path = image_path
        self.source_rect = source_rect
        
        # 如果未指定锚点，默认为中心点
        if pivot is None:
            self.pivot = (source_rect.width / 2, source_rect.height / 2)
        else:
            self.pivot = pivot
        
        # 缓存
        self._image = None
    
    def get_image(self, asset_manager: AssetManager) -> Any:
        """获取图像资源
        
        Args:
            asset_manager: 资源管理器
            
        Returns:
            Any: 图像资源
        """
        if self._image is None:
            self._image = asset_manager.get_image(self.image_path)
        return self._image

class SpriteAnimation:
    """精灵动画类，管理一组精灵帧的动画"""
    
    def __init__(self, name: str, frames: List[SpriteFrame], frame_duration: float = 0.1, loop: bool = True):
        """初始化精灵动画
        
        Args:
            name: 动画名称
            frames: 精灵帧列表
            frame_duration: 每帧持续时间（秒）
            loop: 是否循环播放
        """
        self.name = name
        self.frames = frames
        self.frame_duration = frame_duration
        self.loop = loop
        self.total_frames = len(frames)
        self.total_duration = frame_duration * self.total_frames
    
    def get_frame(self, time: float) -> Tuple[SpriteFrame, float]:
        """根据时间获取当前帧和剩余时间
        
        Args:
            time: 动画时间（秒）
            
        Returns:
            Tuple[SpriteFrame, float]: 当前帧和该帧已播放时间
        """
        if self.total_frames == 0:
            return None, 0
            
        if self.loop:
            # 循环播放时取模
            time = time % self.total_duration
        else:
            # 非循环播放时限制最大时间
            time = min(time, self.total_duration - 0.001)  # 避免边界情况
        
        # 计算当前帧索引
        frame_index = int(time / self.frame_duration)
        if frame_index >= self.total_frames:
            frame_index = self.total_frames - 1
            
        # 计算该帧已播放时间
        frame_time = time - frame_index * self.frame_duration
        
        return self.frames[frame_index], frame_time
    
    def get_progress(self, time: float) -> float:
        """获取动画播放进度
        
        Args:
            time: 动画时间（秒）
            
        Returns:
            float: 播放进度（0.0-1.0）
        """
        if self.total_duration <= 0:
            return 0
            
        if self.loop:
            time = time % self.total_duration
            
        return min(time / self.total_duration, 1.0)
    
    def is_finished(self, time: float) -> bool:
        """检查动画是否播放完成
        
        Args:
            time: 动画时间（秒）
            
        Returns:
            bool: 是否播放完成
        """
        if self.loop:
            return False
        return time >= self.total_duration

class SpriteSheet:
    """精灵表类，管理一组精灵帧和动画"""
    
    def __init__(self, image_path: str):
        """初始化精灵表
        
        Args:
            image_path: 图像路径
        """
        self.image_path = image_path
        self.frames: Dict[str, SpriteFrame] = {}
        self.animations: Dict[str, SpriteAnimation] = {}
        self.asset_manager = AssetManager()
    
    def add_frame(self, name: str, x: float, y: float, width: float, height: float, 
                 pivot: Optional[Tuple[float, float]] = None) -> None:
        """添加精灵帧
        
        Args:
            name: 帧名称
            x: 源矩形X坐标
            y: 源矩形Y坐标
            width: 源矩形宽度
            height: 源矩形高度
            pivot: 锚点，相对于左上角的偏移，默认为中心点
        """
        source_rect = Rect(x, y, width, height)
        frame = SpriteFrame(self.image_path, source_rect, pivot)
        self.frames[name] = frame
    
    def add_animation(self, name: str, frame_names: List[str], frame_duration: float = 0.1, loop: bool = True) -> None:
        """添加精灵动画
        
        Args:
            name: 动画名称
            frame_names: 帧名称列表
            frame_duration: 每帧持续时间（秒）
            loop: 是否循环播放
        """
        frames = []
        for frame_name in frame_names:
            if frame_name in self.frames:
                frames.append(self.frames[frame_name])
            else:
                raise ValueError(f"未找到名为 {frame_name} 的精灵帧")
                
        animation = SpriteAnimation(name, frames, frame_duration, loop)
        self.animations[name] = animation
    
    def get_frame(self, name: str) -> Optional[SpriteFrame]:
        """获取指定名称的精灵帧
        
        Args:
            name: 帧名称
            
        Returns:
            Optional[SpriteFrame]: 精灵帧，如果不存在则为None
        """
        return self.frames.get(name)
    
    def get_animation(self, name: str) -> Optional[SpriteAnimation]:
        """获取指定名称的精灵动画
        
        Args:
            name: 动画名称
            
        Returns:
            Optional[SpriteAnimation]: 精灵动画，如果不存在则为None
        """
        return self.animations.get(name)
    
    @classmethod
    def create_from_grid(cls, image_path: str, frame_width: int, frame_height: int, 
                         rows: int, cols: int, spacing_x: int = 0, spacing_y: int = 0,
                         pivot: Optional[Tuple[float, float]] = None) -> 'SpriteSheet':
        """从网格创建精灵表
        
        Args:
            image_path: 图像路径
            frame_width: 帧宽度
            frame_height: 帧高度
            rows: 行数
            cols: 列数
            spacing_x: 水平间距
            spacing_y: 垂直间距
            pivot: 默认锚点
            
        Returns:
            SpriteSheet: 精灵表实例
        """
        sheet = cls(image_path)
        
        for row in range(rows):
            for col in range(cols):
                x = col * (frame_width + spacing_x)
                y = row * (frame_height + spacing_y)
                name = f"frame_{row}_{col}"
                sheet.add_frame(name, x, y, frame_width, frame_height, pivot)
                
        return sheet

class Sprite(Drawable):
    """精灵类，用于绘制图像和动画"""
    
    def __init__(self, x: float = 0, y: float = 0, width: float = 0, height: float = 0,
                image: Optional[Union[str, Any]] = None, layer: RenderLayer = RenderLayer.MIDDLE, priority: int = 0):
        """初始化精灵
        
        Args:
            x: X坐标
            y: Y坐标
            width: 宽度，0表示使用图像宽度
            height: 高度，0表示使用图像高度
            image: 图像路径或图像对象
            layer: 渲染层级
            priority: 优先级
        """
        super().__init__(x, y, width, height, layer, priority)
        
        self.asset_manager = AssetManager()
        self.image = None
        self.image_path = None
        self.source_rect = None
        self.flip_h = False
        self.flip_v = False
        
        # 动画相关
        self.current_animation = None
        self.animation_time = 0
        self.playing = False
        self.animations: Dict[str, SpriteAnimation] = {}
        
        # 设置图像
        if image is not None:
            self.set_image(image)
    
    def set_image(self, image: Union[str, Any]) -> None:
        """设置精灵图像
        
        Args:
            image: 图像路径或图像对象
        """
        if isinstance(image, str):
            # 图像路径
            self.image_path = image
            self.image = self.asset_manager.get_image(image)
        else:
            # 图像对象
            self.image = image
            self.image_path = None
            
        # 如果尺寸为0，使用图像尺寸
        if self.width == 0 or self.height == 0:
            from PyQt6.QtGui import QImage, QPixmap
            if isinstance(self.image, QImage):
                if self.width == 0:
                    self.width = self.image.width()
                if self.height == 0:
                    self.height = self.image.height()
            elif isinstance(self.image, QPixmap):
                if self.width == 0:
                    self.width = self.image.width()
                if self.height == 0:
                    self.height = self.image.height()
            else:
                # 对于其他类型的图像，尝试获取尺寸
                try:
                    if hasattr(self.image, 'width') and hasattr(self.image, 'height'):
                        if self.width == 0:
                            self.width = self.image.width
                        if self.height == 0:
                            self.height = self.image.height
                except:
                    pass
    
    def set_source_rect(self, x: float, y: float, width: float, height: float) -> None:
        """设置源矩形（用于精灵表）
        
        Args:
            x: 源矩形X坐标
            y: 源矩形Y坐标
            width: 源矩形宽度
            height: 源矩形高度
        """
        self.source_rect = Rect(x, y, width, height)
    
    def clear_source_rect(self) -> None:
        """清除源矩形，使用整个图像"""
        self.source_rect = None
    
    def set_flip(self, horizontal: bool = False, vertical: bool = False) -> None:
        """设置翻转
        
        Args:
            horizontal: 是否水平翻转
            vertical: 是否垂直翻转
        """
        self.flip_h = horizontal
        self.flip_v = vertical
    
    def add_animation(self, name: str, animation: SpriteAnimation) -> None:
        """添加动画
        
        Args:
            name: 动画名称
            animation: 精灵动画对象
        """
        self.animations[name] = animation
    
    def add_animation_from_sheet(self, sprite_sheet: SpriteSheet, animation_name: str) -> None:
        """从精灵表添加动画
        
        Args:
            sprite_sheet: 精灵表对象
            animation_name: 动画名称
        """
        animation = sprite_sheet.get_animation(animation_name)
        if animation:
            self.animations[animation_name] = animation
        else:
            raise ValueError(f"精灵表中未找到名为 {animation_name} 的动画")
    
    def play(self, animation_name: str, restart: bool = True) -> bool:
        """播放指定动画
        
        Args:
            animation_name: 动画名称
            restart: 是否重新开始播放
            
        Returns:
            bool: 是否成功开始播放
        """
        if animation_name not in self.animations:
            return False
            
        animation = self.animations[animation_name]
        
        # 如果是同一个动画且不需要重启，直接返回
        if animation == self.current_animation and not restart and self.playing:
            return True
            
        self.current_animation = animation
        if restart or not self.playing:
            self.animation_time = 0
            
        self.playing = True
        return True
    
    def stop(self) -> None:
        """停止播放动画"""
        self.playing = False
    
    def pause(self) -> None:
        """暂停播放动画"""
        self.playing = False
    
    def resume(self) -> None:
        """恢复播放动画"""
        if self.current_animation:
            self.playing = True
    
    def is_playing(self) -> bool:
        """检查是否正在播放动画
        
        Returns:
            bool: 是否正在播放
        """
        return self.playing and self.current_animation is not None
    
    def update(self, dt: float) -> None:
        """更新精灵状态
        
        Args:
            dt: 时间增量（秒）
        """
        super().update(dt)
        
        # 更新动画
        if self.playing and self.current_animation:
            self.animation_time += dt
            
            # 检查非循环动画是否结束
            if not self.current_animation.loop and self.current_animation.is_finished(self.animation_time):
                self.playing = False
    
    def draw(self, renderer: RendererBase) -> None:
        """绘制精灵
        
        Args:
            renderer: 渲染器
        """
        if not self.visible or self.opacity <= 0 or not self.image:
            return
            
        # 获取世界坐标和尺寸
        wx, wy = self.world_position
        width = self.width * self.scale_x
        height = self.height * self.scale_y
        
        # 如果有动画，使用当前帧
        source_rect = self.source_rect
        if self.current_animation:
            current_frame, _ = self.current_animation.get_frame(self.animation_time)
            if current_frame:
                source_rect = current_frame.source_rect
                
                # 如果精灵尺寸为0，使用帧尺寸
                if self.width == 0 or self.height == 0:
                    width = source_rect.width * self.scale_x
                    height = source_rect.height * self.scale_y
        
        # 绘制图像
        renderer.draw_image(
            self.image, 
            wx, wy, 
            width, height,
            source_rect, 
            self.rotation,
            (self.origin_x * self.scale_x, self.origin_y * self.scale_y),
            self.flip_h, 
            self.flip_v,
            self.opacity
        )

class SpriteGroup:
    """精灵组类，用于管理和批量操作一组精灵"""
    
    def __init__(self):
        """初始化精灵组"""
        self.sprites: List[Sprite] = []
        self.visible = True
    
    def add(self, sprite: Sprite) -> None:
        """添加精灵
        
        Args:
            sprite: 精灵对象
        """
        if sprite not in self.sprites:
            self.sprites.append(sprite)
    
    def remove(self, sprite: Sprite) -> bool:
        """移除精灵
        
        Args:
            sprite: 精灵对象
            
        Returns:
            bool: 是否成功移除
        """
        if sprite in self.sprites:
            self.sprites.remove(sprite)
            return True
        return False
    
    def clear(self) -> None:
        """清空精灵组"""
        self.sprites.clear()
    
    def update(self, dt: float) -> None:
        """更新所有精灵
        
        Args:
            dt: 时间增量（秒）
        """
        for sprite in self.sprites:
            sprite.update(dt)
    
    def draw(self, renderer: RendererBase) -> None:
        """绘制所有精灵
        
        Args:
            renderer: 渲染器
        """
        if not self.visible:
            return
            
        for sprite in self.sprites:
            sprite.draw(renderer)
    
    def set_visible(self, visible: bool) -> None:
        """设置所有精灵的可见性
        
        Args:
            visible: 是否可见
        """
        self.visible = visible
        for sprite in self.sprites:
            sprite.set_visible(visible)
    
    def set_opacity(self, opacity: float) -> None:
        """设置所有精灵的不透明度
        
        Args:
            opacity: 不透明度 (0.0-1.0)
        """
        for sprite in self.sprites:
            sprite.set_opacity(opacity)
    
    def move(self, dx: float, dy: float) -> None:
        """移动所有精灵
        
        Args:
            dx: X方向移动距离
            dy: Y方向移动距离
        """
        for sprite in self.sprites:
            sprite.move(dx, dy)
    
    def scale(self, sx: float, sy: float) -> None:
        """缩放所有精灵
        
        Args:
            sx: X方向缩放因子
            sy: Y方向缩放因子
        """
        for sprite in self.sprites:
            sprite.set_scale(sx, sy)
    
    def count(self) -> int:
        """获取精灵数量
        
        Returns:
            int: 精灵数量
        """
        return len(self.sprites)
    
    def get_sprites_with_tag(self, tag: str) -> List[Sprite]:
        """获取具有指定标签的精灵
        
        Args:
            tag: 标签
            
        Returns:
            List[Sprite]: 精灵列表
        """
        return [sprite for sprite in self.sprites if sprite.has_tag(tag)] 