"""
---------------------------------------------------------------
File name:                  __init__.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                渲染模块初始化文件
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
                            2025/05/11: 从PyQt迁移到PySide;
----
"""

# 基础渲染器
from status.renderer.renderer_base import (
    RendererBase, 
    Color, 
    Rect, 
    BlendMode, 
    TextAlign, 
    RenderLayer
)
from status.renderer.renderer_manager import RendererManager

# 特定渲染器实现
from status.renderer.pyside_renderer import PySideRenderer

# 绘制相关
from status.renderer.drawable import (
    Drawable,
    Transform
)

# 使用Layer作为RenderLayer的别名
Layer = RenderLayer

# 基础图形元素
from status.renderer.primitives import (
    Point,
    Line,
    Rectangle,
    Circle,
    Polygon
)

# 精灵系统
from status.renderer.sprite import (
    SpriteFrame,
    SpriteAnimation,
    SpriteSheet,
    Sprite,
    SpriteGroup
)

# 动画系统
from status.renderer.animation import (
    EasingType,
    AnimationState,
    Animator,
    PropertyAnimation,
    MultiPropertyAnimation,
    SequenceAnimation,
    DrawableAnimator,
    AnimationManager
)

__all__ = [
    # 基础渲染器
    'RendererBase',
    'RendererManager',
    'Color',
    'Rect',
    'BlendMode',
    'TextAlign',
    'RenderLayer',
    
    # 特定渲染器
    'PySideRenderer',
    
    # 绘制相关
    'Drawable',
    'Transform',
    'Layer',
    
    # 基础图形
    'Point',
    'Line',
    'Rectangle',
    'Circle',
    'Polygon',
    
    # 精灵系统
    'SpriteFrame',
    'SpriteAnimation',
    'SpriteSheet',
    'Sprite',
    'SpriteGroup',
    
    # 动画系统
    'EasingType',
    'AnimationState',
    'Animator',
    'PropertyAnimation',
    'MultiPropertyAnimation',
    'SequenceAnimation',
    'DrawableAnimator',
    'AnimationManager'
]
