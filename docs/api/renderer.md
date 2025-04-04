# 渲染系统 API 参考

## 目录

- [模块概述](#模块概述)
- [主要类和接口](#主要类和接口)
  - [RendererBase](#rendererbase)
  - [RendererManager](#renderermanager)
  - [PyQtRenderer](#pyqtrenderer)
  - [Drawable](#drawable)
  - [Sprite](#sprite)
  - [Animation](#animation)
  - [Effects](#effects)
  - [Transition](#transition)
  - [Particle](#particle)
  - [Primitives](#primitives)
- [枚举和常量](#枚举和常量)
- [工具函数](#工具函数)
- [异常类](#异常类)

## 模块概述

渲染系统是Hollow-ming项目的核心组件之一，负责所有图形渲染和视觉效果的处理。该系统采用模块化设计，支持多种渲染技术、动画、特效、转场效果和粒子系统，为应用程序提供丰富多样的视觉表现。

主要导入：

```python
from status.renderer import renderer_manager       # 渲染管理器
from status.renderer import renderer_base          # 渲染器基类
from status.renderer import pyqt_renderer          # PyQt渲染器实现
from status.renderer import drawable               # 可绘制对象
from status.renderer import sprite                 # 精灵系统
from status.renderer import animation              # 动画系统
from status.renderer import effects                # 特效系统
from status.renderer import transition             # 转场效果系统
from status.renderer import particle               # 粒子系统
from status.renderer import primitives             # 基础图形元素
```

## 主要类和接口

### RendererBase

渲染器基类，定义通用渲染接口。所有具体渲染器实现都应继承此类。

```python
class RendererBase
```

#### 主要方法

```python
def initialize(self, width, height)
```

初始化渲染器。

**参数**:
- `width` (int): 渲染区域宽度
- `height` (int): 渲染区域高度

**返回值**: bool - 初始化是否成功

---

```python
def render(self, scene)
```

渲染场景。

**参数**:
- `scene` (Scene): 要渲染的场景

**返回值**: 无

### RendererManager

渲染管理器，协调不同渲染器和渲染过程。

```python
class RendererManager
```

#### 主要方法

```python
def register_renderer(self, renderer_type, renderer)
```

注册新的渲染器。

**参数**:
- `renderer_type` (str): 渲染器类型标识符
- `renderer` (RendererBase): 渲染器实例

**返回值**: 无

### PyQtRenderer

基于PyQt的渲染器实现。

```python
class PyQtRenderer(RendererBase)
```

### Drawable

可绘制对象基类，所有可在屏幕上绘制的元素的基类。

```python
class Drawable
```

### Sprite

精灵系统，用于图像渲染。

```python
class Sprite(Drawable)
```

### Animation

动画系统，提供各类动画支持。

```python
class Animation
```

### Effects

特效系统，提供各种视觉效果。

```python
class Effect
```

### Transition

转场效果系统，提供场景切换时的视觉转场效果。

```python
class Transition
```

### Particle

粒子系统，用于创建和管理粒子效果。

```python
class ParticleSystem
```

### Primitives

基础图形元素，如矩形、圆形等。

```python
class Shape
```

## 枚举和常量

### RendererType

渲染器类型枚举。

```python
class RendererType(Enum)
```

### BlendMode

混合模式枚举，定义不同的图像混合方式。

```python
class BlendMode(Enum)
```

### TransitionType

转场效果类型枚举。

```python
class TransitionType(Enum)
```

## 工具函数

```python
def create_renderer(renderer_type, width, height)
```

创建指定类型的渲染器。

**参数**:
- `renderer_type` (RendererType): 渲染器类型
- `width` (int): 渲染区域宽度
- `height` (int): 渲染区域高度

**返回值**: RendererBase - 创建的渲染器实例

## 异常类

### RenderError

渲染错误基类。

```python
class RenderError(Exception)
```

### InitializationError

渲染器初始化错误。

```python
class InitializationError(RenderError)
```

### ResourceError

渲染资源错误。

```python
class ResourceError(RenderError)
``` 