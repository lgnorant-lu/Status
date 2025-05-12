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
import logging

from status.renderer.renderer_base import RendererBase, Color, Rect, RenderLayer
from status.renderer.drawable import Drawable
from status.resources.asset_manager import AssetManager
from PySide6.QtGui import QImage, QPixmap

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
            self._image = asset_manager.load_image(self.image_path)
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
    
    def get_frame(self, time: float) -> Optional[Tuple[SpriteFrame, float]]:
        """根据时间获取当前帧和剩余时间
        
        Args:
            time: 动画时间（秒）
            
        Returns:
            Optional[Tuple[SpriteFrame, float]]: 当前帧和该帧已播放时间
        """
        if self.total_frames == 0:
            return None
            
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
                 image: Optional[Union[str, QImage, QPixmap]] = None, 
                 layer: RenderLayer = RenderLayer.MIDDLE, priority: int = 0):
        """初始化精灵
        
        Args:
            x: X坐标
            y: Y坐标
            width: 宽度，0表示使用图像宽度
            height: 高度，0表示使用图像高度
            image: 图像路径、QImage 或 QPixmap 对象
            layer: 渲染层级
            priority: 渲染优先级
        """
        super().__init__(x, y, width, height, layer, priority)
        
        self.asset_manager = AssetManager.get_instance()
        self._image: Optional[QPixmap] = None
        self.image_path: Optional[str] = None
        self.source_rect: Optional[Rect] = None
        self.pivot: Optional[Tuple[float, float]] = None
        
        # 动画相关
        self.animations: Dict[str, SpriteAnimation] = {}  # 存储动画的字典
        self.current_animation: Optional[SpriteAnimation] = None
        self.animation_time: float = 0.0
        self.paused: bool = False
        
        # 如果提供了图像，立即设置
        if image:
            self.set_image(image)
    
    @property
    def image(self) -> Optional[QPixmap]:
        """获取当前显示的 QPixmap 图像"""
        if self.current_animation and not self.paused:
            self._update_animation_frame()
            
        return self._image
        
    def set_image(self, image: Union[str, QImage, QPixmap]) -> None:
        """设置精灵图像
        
        Args:
            image: 图像路径、QImage 或 QPixmap 对象
        """
        # 重置动画和源矩形相关状态
        self.current_animation = None
        self.source_rect = None
        
        # 初始化变量以确保所有分支都有定义
        loaded_pixmap = None
        
        # 根据不同类型的输入加载图像
        if isinstance(image, str):
            self.image_path = image
            try:
                img_obj = self.asset_manager.load_image(image)
                if isinstance(img_obj, QImage):
                    loaded_pixmap = QPixmap.fromImage(img_obj)
                elif isinstance(img_obj, QPixmap):
                    loaded_pixmap = img_obj
                # 如果加载失败(None或不是QImage/QPixmap)，loaded_pixmap保持为None
            except Exception as e:
                logging.error(f"Sprite: 加载图像路径 '{image}' 失败: {e}")
                # 异常情况下，loaded_pixmap保持为None
        elif isinstance(image, QImage):
            loaded_pixmap = QPixmap.fromImage(image)
            self.image_path = None
        elif isinstance(image, QPixmap):
            loaded_pixmap = image
            self.image_path = None
        else:
            logging.error(f"Sprite: 不支持的图像类型: {type(image)}")
            # 不支持的类型，loaded_pixmap保持为None
            
        # 图像处理，适用于所有情况
        if loaded_pixmap is not None and not loaded_pixmap.isNull():
            self._image = loaded_pixmap
            # 如果宽高为0，从图像更新
            if self.width == 0:
                self.width = self._image.width()
            if self.height == 0:
                self.height = self._image.height()
            # 如果没有设置锚点，设置为中心
            if self.pivot is None:
                self.pivot = (self.width / 2, self.height / 2)
        else:
            # 如果加载失败，清空图像
            self._image = None
        
        # 标记为脏以便更新渲染
        self._dirty = True
    
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
    
    def play(self, animation: SpriteAnimation, restart: bool = False) -> None:
        """播放精灵动画
        
        Args:
            animation: SpriteAnimation 对象
            restart: 如果动画已在播放，是否重新开始
        """
        if not animation or not animation.frames:
            logging.warning(f"Sprite: 尝试播放无效动画")
            return
            
        if self.current_animation == animation and not restart:
            self.resume()
            return
            
        self.current_animation = animation
        self.animation_time = 0.0
        self.paused = False
        self._update_animation_frame()
    
    def pause(self) -> None:
        """暂停动画"""
        self.paused = True
    
    def resume(self) -> None:
        """恢复动画"""
        self.paused = False
    
    def update(self, dt: float) -> None:
        """更新动画时间
        
        Args:
            dt: 时间增量（秒）
        """
        if self.current_animation and not self.paused:
            self.animation_time += dt
            
            if not self.current_animation.loop and self.current_animation.is_finished(self.animation_time):
                self.pause()
                
    def _update_animation_frame(self) -> None:
        """根据当前动画时间和状态更新精灵帧"""
        if not self.current_animation:
            return
            
        # 调用 get_frame 并检查返回值
        frame_data = self.current_animation.get_frame(self.animation_time)
        
        if frame_data is not None:
            # 只有在获取到有效帧数据时才解包和设置
            frame, frame_time = frame_data
            if frame: # 再次确认 frame 对象本身有效
                self.set_frame(frame)
            else:
                # 理论上 frame_data 不为 None 时 frame 也不应为 None，但以防万一
                logging.warning(f"Sprite: get_frame 返回了有效的元组，但帧对象无效")
                self._image = None
        else:
            # 动画可能没有帧或已结束 (get_frame 返回 None)
            # 可以选择保持最后一帧或清空
            # logging.debug(f"Sprite: get_frame 未返回有效帧数据")
            self._image = None # 或者保持 self._image 不变？取决于期望行为
            
    def set_frame(self, frame: SpriteFrame) -> None:
        """设置精灵为精灵表中的特定帧
        
        Args:
            frame: SpriteFrame 对象
        """
        self.current_animation = None
        self.image_path = frame.image_path
        self.source_rect = frame.source_rect
        self.pivot = frame.pivot
        
        try:
            img_obj = frame.get_image(self.asset_manager)
            if isinstance(img_obj, QImage):
                self._image = QPixmap.fromImage(img_obj)
            elif isinstance(img_obj, QPixmap):
                self._image = img_obj
            else:
                logging.warning(f"Sprite: Frame未能加载有效图像 '{self.image_path}'")
                self._image = None
                 
            if self._image and not self._image.isNull():
                self.width = frame.source_rect.width
                self.height = frame.source_rect.height
            else:
                self._image = None
                 
        except Exception as e:
            logging.error(f"Sprite: 加载帧图像 '{self.image_path}' 失败: {e}")
            self._image = None
            
    def is_playing(self) -> bool:
        """检查是否正在播放动画
        
        Returns:
            bool: 是否正在播放
        """
        return self.paused and self.current_animation is not None

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

def load_spritesheet_from_json(json_path: str, asset_manager: AssetManager) -> Optional[SpriteSheet]:
    """从 JSON 文件加载精灵表定义"""
    try:
        data = asset_manager.load_json(json_path)
        if not data:
            return None
            
        image_path = data.get("meta", {}).get("image")
        if not image_path:
            raise ValueError("JSON 中缺少 'meta.image' 字段")
            
        sheet = SpriteSheet(image_path)
        
        frames_data = data.get("frames", {})
        for name, frame_info in frames_data.items():
            rect_info = frame_info.get("frame")
            pivot_info = frame_info.get("pivot")
            if not rect_info:
                logging.warning(f"跳过帧 '{name}': 缺少 'frame' 信息")
                continue
                
            x = rect_info.get("x", 0)
            y = rect_info.get("y", 0)
            w = rect_info.get("w", 0)
            h = rect_info.get("h", 0)
            
            pivot = None
            if pivot_info:
                pivot = (pivot_info.get("x", 0.5) * w, pivot_info.get("y", 0.5) * h)
                
            sheet.add_frame(name, x, y, w, h, pivot)
            
        animations_data = data.get("meta", {}).get("animations", {})
        for anim_name, anim_info in animations_data.items():
            frame_names = anim_info.get("frames")
            duration = anim_info.get("duration", 0.1)
            loop = anim_info.get("loop", True)
            
            if not frame_names:
                logging.warning(f"跳过动画 '{anim_name}': 缺少 'frames' 信息")
                continue
                
            sheet.add_animation(anim_name, frame_names, duration, loop)
            
        return sheet
        
    except Exception as e:
        logging.error(f"从 JSON 加载精灵表失败 '{json_path}': {e}")
        return None 