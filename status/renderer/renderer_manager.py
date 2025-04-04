"""
---------------------------------------------------------------
File name:                  renderer_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                渲染器管理器，实现单例模式和工厂方法
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import logging
from typing import Dict, Any, Type, Optional, List, Tuple
import enum
import threading

from status.renderer.renderer_base import RendererBase, Rect, RenderLayer
from status.core.event_system import EventSystem, EventType, Event

class RendererType(enum.Enum):
    """渲染器类型枚举"""
    PYQT = "pyqt"          # PyQt渲染器
    DUMMY = "dummy"        # 虚拟渲染器（用于测试）
    
class RenderCommand:
    """渲染命令类，用于渲染命令队列"""
    
    def __init__(self, layer: RenderLayer, priority: int, callback: callable, **params):
        """初始化渲染命令
        
        Args:
            layer: 渲染层级
            priority: 优先级（同一层内）
            callback: 渲染回调函数
            **params: 渲染参数
        """
        self.layer = layer
        self.priority = priority
        self.callback = callback
        self.params = params
        
    def execute(self, renderer: RendererBase) -> None:
        """执行渲染命令
        
        Args:
            renderer: 渲染器实例
        """
        self.callback(renderer, **self.params)
        
    def __lt__(self, other: 'RenderCommand') -> bool:
        """比较操作符，用于排序
        
        先按层级排序，再按优先级排序
        
        Args:
            other: 另一个渲染命令
            
        Returns:
            bool: 是否小于
        """
        if self.layer.value == other.layer.value:
            return self.priority < other.priority
        return self.layer.value < other.layer.value

class RendererManager:
    """渲染器管理器类，实现单例模式"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """实现单例模式"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(RendererManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化渲染器管理器"""
        # 避免重复初始化
        if hasattr(self, 'initialized'):
            return
            
        self.logger = logging.getLogger("Hollow-ming.Renderer.RendererManager")
        self.renderers: Dict[str, Type[RendererBase]] = {}
        self.active_renderer: Optional[RendererBase] = None
        self.renderer_type: Optional[RendererType] = None
        self.render_commands: List[RenderCommand] = []
        self.dirty_rects: List[Rect] = []
        self.use_dirty_rects = True
        self.force_full_redraw = False
        self.width = 800
        self.height = 600
        self.fps = 60
        self.frame_time = 0
        self.frame_count = 0
        self.debug_draw = False
        
        # 注册事件监听
        self.event_system = EventSystem()
        self.initialized = True
        
        self.logger.info("渲染器管理器初始化完成")
    
    def register_renderer(self, renderer_type: RendererType, renderer_class: Type[RendererBase]) -> None:
        """注册渲染器类型
        
        Args:
            renderer_type: 渲染器类型
            renderer_class: 渲染器类
        """
        self.renderers[renderer_type.value] = renderer_class
        self.logger.debug(f"注册渲染器: {renderer_type.value}")
    
    def create_renderer(self, renderer_type: RendererType, **kwargs) -> bool:
        """创建并初始化渲染器
        
        Args:
            renderer_type: 渲染器类型
            **kwargs: 传递给渲染器初始化的参数
            
        Returns:
            bool: 是否成功创建渲染器
        """
        if renderer_type.value not in self.renderers:
            self.logger.error(f"未注册的渲染器类型: {renderer_type.value}")
            return False
        
        # 关闭当前活动的渲染器
        if self.active_renderer:
            self.active_renderer.shutdown()
            self.active_renderer = None
            
        # 创建新的渲染器
        renderer_class = self.renderers[renderer_type.value]
        self.active_renderer = renderer_class()
        
        # 获取宽高参数，默认使用管理器的宽高
        width = kwargs.get('width', self.width)
        height = kwargs.get('height', self.height)
        
        # 初始化渲染器
        success = self.active_renderer.initialize(width, height, **kwargs)
        
        if success:
            self.renderer_type = renderer_type
            self.width = width
            self.height = height
            self.logger.info(f"成功创建渲染器: {renderer_type.value}, 分辨率: {width}x{height}")
        else:
            self.active_renderer = None
            self.logger.error(f"创建渲染器失败: {renderer_type.value}")
            
        return success
    
    def shutdown(self) -> None:
        """关闭渲染器"""
        if self.active_renderer:
            self.active_renderer.shutdown()
            self.active_renderer = None
            self.logger.info("渲染器已关闭")
    
    def begin_frame(self) -> bool:
        """开始一帧渲染
        
        Returns:
            bool: 是否成功开始
        """
        if not self.active_renderer:
            return False
            
        self.active_renderer.begin_frame()
        
        # 清除上一帧的渲染命令
        self.render_commands.clear()
        
        return True
    
    def end_frame(self) -> None:
        """结束一帧渲染并提交"""
        if not self.active_renderer:
            return
            
        # 排序渲染命令
        self.render_commands.sort()
        
        # 如果启用了脏矩形渲染
        if self.use_dirty_rects and not self.force_full_redraw and self.dirty_rects:
            # 合并重叠区域
            merged_rects = self._merge_dirty_rects()
            
            for rect in merged_rects:
                # 设置裁剪区域
                self.active_renderer.set_clip_rect(rect)
                
                # 执行渲染命令
                for cmd in self.render_commands:
                    cmd.execute(self.active_renderer)
                    
                # 如果开启调试绘制，显示脏矩形
                if self.debug_draw:
                    self._draw_debug_rect(rect)
        else:
            # 全屏渲染
            self.active_renderer.set_clip_rect(None)
            
            # 执行渲染命令
            for cmd in self.render_commands:
                cmd.execute(self.active_renderer)
        
        # 结束帧
        self.active_renderer.end_frame()
        
        # 清除脏矩形
        self.dirty_rects.clear()
        self.force_full_redraw = False
        
        # 更新计数
        self.frame_count += 1
    
    def add_render_command(self, layer: RenderLayer, priority: int, callback: callable, **params) -> None:
        """添加渲染命令
        
        Args:
            layer: 渲染层级
            priority: 优先级（同一层内）
            callback: 渲染回调函数
            **params: 渲染参数
        """
        cmd = RenderCommand(layer, priority, callback, **params)
        self.render_commands.append(cmd)
    
    def add_dirty_rect(self, rect: Rect) -> None:
        """添加脏矩形区域
        
        Args:
            rect: 脏矩形区域
        """
        if self.use_dirty_rects:
            self.dirty_rects.append(rect)
    
    def force_redraw(self) -> None:
        """强制重绘整个屏幕"""
        self.force_full_redraw = True
    
    def set_viewport(self, x: int, y: int, width: int, height: int) -> None:
        """设置视口
        
        Args:
            x: 视口左上角X坐标
            y: 视口左上角Y坐标
            width: 视口宽度
            height: 视口高度
        """
        if self.active_renderer:
            self.active_renderer.set_viewport(x, y, width, height)
    
    def get_renderer(self) -> Optional[RendererBase]:
        """获取当前活动的渲染器
        
        Returns:
            Optional[RendererBase]: 渲染器实例，如果未初始化则为None
        """
        return self.active_renderer
    
    def get_renderer_info(self) -> Dict[str, Any]:
        """获取渲染器信息
        
        Returns:
            Dict[str, Any]: 渲染器信息字典
        """
        info = {
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "frame_count": self.frame_count,
            "frame_time": self.frame_time,
            "renderer_type": self.renderer_type.value if self.renderer_type else "none",
            "use_dirty_rects": self.use_dirty_rects,
            "dirty_rect_count": len(self.dirty_rects),
        }
        
        # 添加活动渲染器的信息
        if self.active_renderer:
            renderer_info = self.active_renderer.get_renderer_info()
            info.update(renderer_info)
        
        return info
    
    def set_debug_draw(self, enabled: bool) -> None:
        """设置是否启用调试绘制
        
        Args:
            enabled: 是否启用
        """
        self.debug_draw = enabled
    
    def _merge_dirty_rects(self) -> List[Rect]:
        """合并重叠的脏矩形区域，优化渲染
        
        Returns:
            List[Rect]: 合并后的脏矩形列表
        """
        if not self.dirty_rects:
            return []
            
        # 简单实现：如果脏矩形过多，直接全屏刷新
        if len(self.dirty_rects) > 10:
            return [Rect(0, 0, self.width, self.height)]
            
        # TODO: 实现更复杂的矩形合并算法
        # 当前简单实现，返回原始脏矩形列表
        return self.dirty_rects.copy()
    
    def _draw_debug_rect(self, rect: Rect) -> None:
        """绘制调试用的脏矩形边框
        
        Args:
            rect: 脏矩形
        """
        if self.active_renderer and self.debug_draw:
            from status.renderer.renderer_base import Color
            debug_color = Color(255, 0, 0, 128)  # 半透明红色
            self.active_renderer.draw_rect(rect, debug_color, 1.0, False) 