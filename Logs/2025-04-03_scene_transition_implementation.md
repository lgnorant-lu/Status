# 场景转场系统实现日志

## 日期: 2025/04/03

## 概述

场景转场系统是Hollow-ming项目的重要组件，负责在场景切换时提供平滑的视觉效果，增强用户体验。本次实现了场景转场系统的基础框架，包括转场基类、多种转场效果和转场管理器，并将其集成到场景管理器中。

## 系统架构

场景转场系统采用了模块化的设计，主要包括以下组件：

1. **场景转场基类 (SceneTransition)**：
   - 定义所有转场效果的通用接口
   - 管理转场的生命周期（开始、更新、结束）
   - 处理转场过程中的渲染逻辑

2. **具体转场效果**：
   - 淡入淡出 (FadeTransition)：通过改变透明度实现平滑过渡
   - 滑动 (SlideTransition)：场景滑入滑出效果
   - 缩放 (ZoomTransition)：放大缩小效果
   - 溶解 (DissolveTransition)：使用纹理实现场景溶解效果

3. **转场管理器 (TransitionManager)**：
   - 统一管理转场效果
   - 提供注册和获取转场效果的方法
   - 采用单例模式确保全局一致性

4. **场景管理器集成**：
   - 扩展场景管理器，支持转场效果
   - 在场景切换时应用转场动画
   - 处理转场过程中的渲染和输入

## 核心组件说明

### 1. 场景转场基类 (SceneTransition)

`SceneTransition` 是所有转场效果的基类，提供通用的转场生命周期管理：

```python
class SceneTransition(ABC):
    def __init__(self, duration: float = 0.5, easing: EasingType = EasingType.EASE_IN_OUT):
        """初始化转场效果"""
        self.duration = duration
        self.easing = easing
        self.state = TransitionState.IDLE
        self.elapsed_time = 0.0
        self.progress = 0.0
        
    def start_transition(self, is_entering: bool) -> None:
        """开始转场动画"""
        self.state = TransitionState.ENTERING if is_entering else TransitionState.LEAVING
        self.elapsed_time = 0.0
        self.progress = 0.0
        
    def update(self, delta_time: float) -> bool:
        """更新转场动画"""
        # 更新进度和状态
        
    def render(self, renderer: RendererBase, current_scene: Any, next_scene: Any) -> None:
        """渲染转场效果"""
        # 调用具体子类实现的渲染方法
        
    @abstractmethod
    def _render_transition(self, renderer: RendererBase, current_scene: Any, next_scene: Any) -> None:
        """渲染转场效果的具体实现（由子类提供）"""
        pass
```

转场基类的主要特点：

- **状态管理**：使用 `TransitionState` 枚举表示转场状态（空闲、进入、离开、完成）
- **时间管理**：跟踪转场进度，确保平滑过渡
- **缓动支持**：使用动画系统的缓动函数，使转场更自然
- **抽象渲染**：定义通用渲染接口，由子类实现具体效果

### 2. 具体转场效果

实现了多种常用的转场效果：

#### 淡入淡出效果 (FadeTransition)

```python
class FadeTransition(SceneTransition):
    def _render_transition(self, renderer: RendererBase, current_scene: Any, next_scene: Any) -> None:
        """渲染淡入淡出效果"""
        if self.state == TransitionState.ENTERING:
            # 进入动画：先渲染当前场景，再渲染下一场景（逐渐显示）
            if current_scene:
                current_scene.render(renderer)
            
            if next_scene:
                original_opacity = renderer.get_opacity()
                renderer.set_opacity(self.progress)
                next_scene.render(renderer)
                renderer.set_opacity(original_opacity)
        # ... 离开动画逻辑 ...
```

#### 滑动效果 (SlideTransition)

```python
class SlideTransition(SceneTransition):
    def __init__(self, direction: str = "left", duration: float = 0.5, 
                easing: EasingType = EasingType.EASE_IN_OUT):
        """初始化滑动转场效果"""
        super().__init__(duration, easing)
        self.direction = direction
    
    def _render_transition(self, renderer: RendererBase, current_scene: Any, next_scene: Any) -> None:
        """渲染滑动效果"""
        # 获取视口大小并计算滑动位移
        # 根据方向和进度渲染场景
```

#### 缩放效果 (ZoomTransition)

```python
class ZoomTransition(SceneTransition):
    def __init__(self, zoom_in: bool = True, duration: float = 0.5, 
                easing: EasingType = EasingType.EASE_IN_OUT):
        """初始化缩放转场效果"""
        super().__init__(duration, easing)
        self.zoom_in = zoom_in
    
    def _render_transition(self, renderer: RendererBase, current_scene: Any, next_scene: Any) -> None:
        """渲染缩放效果"""
        # 使用渲染器的变换功能实现缩放效果
```

#### 溶解效果 (DissolveTransition)

```python
class DissolveTransition(SceneTransition):
    def __init__(self, pattern_path: str = None, duration: float = 0.5, 
                easing: EasingType = EasingType.EASE_IN_OUT):
        """初始化溶解转场效果"""
        super().__init__(duration, easing)
        self.pattern_path = pattern_path
        self.pattern = None
        
    def _render_transition(self, renderer: RendererBase, current_scene: Any, next_scene: Any) -> None:
        """渲染溶解效果"""
        # 使用纹理或透明度实现溶解效果
```

### 3. 转场管理器 (TransitionManager)

`TransitionManager` 是转场效果的管理中心，采用单例模式：

```python
class TransitionManager:
    """转场管理器，负责管理和提供转场效果"""
    
    # 单例实现
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = TransitionManager()
        return cls._instance
    
    def __init__(self):
        """初始化转场管理器"""
        # 注册默认转场效果
        self.transitions = {
            "fade": FadeTransition,
            "slide_left": lambda duration=0.5, easing=EasingType.EASE_IN_OUT: 
                SlideTransition("left", duration, easing),
            # ... 其他转场效果 ...
        }
        
        # 默认转场效果
        self.default_transition = "fade"
        
    def register_transition(self, name: str, transition_factory) -> None:
        """注册新的转场效果"""
        self.transitions[name] = transition_factory
        
    def get_transition(self, name: str = None, **kwargs) -> SceneTransition:
        """获取指定的转场效果"""
        # 根据名称创建转场效果实例
```

转场管理器的主要特点：

- **集中管理**：统一管理所有转场效果，方便扩展和配置
- **工厂方法**：使用工厂函数创建转场效果实例，支持参数自定义
- **默认行为**：提供默认转场效果，简化使用

### 4. 场景管理器集成 (SceneManager)

扩展的场景管理器支持转场效果：

```python
class SceneManager:
    """场景管理器，负责管理场景切换和转场效果"""
    
    # 单例实现
    
    def __init__(self):
        """初始化场景管理器"""
        self.scenes = {}  # 场景字典
        self.current_scene = None  # 当前场景
        self.next_scene = None  # 下一个场景
        self.transition = None  # 当前转场效果
        self.transition_manager = TransitionManager.get_instance()
        
    def switch_to(self, scene_id: str, transition: Optional[str] = None, 
                 transition_params: Dict[str, Any] = None, 
                 scene_params: Dict[str, Any] = None) -> bool:
        """切换到指定场景"""
        # 场景切换逻辑，包括转场效果应用
        
    def _complete_transition(self) -> None:
        """完成当前转场"""
        # 转场完成后的处理
        
    def update(self, delta_time: float, system_data: Dict[str, Any] = None) -> None:
        """更新场景管理器"""
        # 更新转场动画和当前场景
        
    def render(self, renderer: RendererBase) -> None:
        """渲染当前场景和转场效果"""
        # 根据转场状态决定渲染方式
```

场景管理器的转场相关功能：

- **转场状态管理**：跟踪转场进度和状态
- **平滑场景切换**：在完成转场前保持两个场景都处于活动状态
- **输入处理**：转场过程中禁用场景输入，避免干扰
- **事件通知**：在场景切换完成时发送事件通知

## 设计模式应用

场景转场系统应用了多种设计模式：

1. **模板方法模式**：
   - `SceneTransition` 定义通用转场流程
   - 子类只需实现特定的渲染方法

2. **策略模式**：
   - 不同转场效果作为可互换的策略
   - 场景管理器可以灵活选择不同的转场效果

3. **单例模式**：
   - `TransitionManager` 和 `SceneManager` 使用单例确保全局一致性
   - 避免资源冲突和状态不一致

4. **工厂方法模式**：
   - `TransitionManager` 使用工厂方法创建转场效果实例
   - 支持参数自定义和运行时配置

5. **观察者模式**：
   - 场景切换时发送事件通知
   - 使用事件系统解耦场景管理和其他模块

## 实现细节

### 转场状态管理

转场效果采用状态机管理生命周期：

1. **IDLE**：转场效果初始状态，未开始
2. **ENTERING**：正在进入新场景，从0%到100%的进度
3. **LEAVING**：正在离开当前场景，从0%到100%的进度
4. **COMPLETED**：转场完成，准备清理资源

### 渲染器抽象

转场效果使用 `RendererBase` 的抽象接口，确保与具体渲染实现解耦：

- **透明度控制**：使用 `set_opacity` 和 `get_opacity` 方法
- **状态保存**：使用 `save_state` 和 `restore_state` 方法
- **变换操作**：使用 `translate`、`rotate` 和 `scale` 方法
- **特效支持**：使用 `set_dissolve_effect` 和 `clear_effects` 方法

### 缓动函数集成

集成动画系统的缓动函数，使转场效果更加自然：

- 线性缓动 (LINEAR)：匀速过渡
- 缓入缓出 (EASE_IN_OUT)：开始和结束慢，中间快
- 弹性效果 (ELASTIC)：带有弹性的过渡效果

## 测试方案

为确保场景转场系统的稳定性和性能，实现了全面的测试用例：

1. **单元测试**：
   - 测试各种转场效果的基本功能
   - 测试转场管理器的注册和获取功能
   - 测试场景管理器的转场集成

2. **性能测试**：
   - 测试复杂场景下的转场性能
   - 确保在低配置设备上仍能保持流畅

## 未来改进

场景转场系统还可以进一步改进：

1. **更多转场效果**：
   - 马赛克效果
   - 棋盘效果
   - 百叶窗效果
   - 圆形扩散效果

2. **转场效果组合**：
   - 支持多个转场效果组合使用
   - 创建更复杂和多样的视觉体验

3. **性能优化**：
   - 使用缓冲区技术减少渲染开销
   - 在低性能设备上自动降级转场效果

4. **配置化**：
   - 从配置文件加载转场效果设置
   - 支持用户自定义转场效果

5. **场景预加载**：
   - 在转场开始前预加载下一个场景
   - 减少场景切换时的加载延迟

## 文档更新

本次实现更新了以下文档：

1. 更新了 `Thread.md`，将场景转场动画标记为已完成
2. 更新了 `Structure.md`，添加了场景转场系统的文件结构
3. 更新了 `Log.md`，添加了场景转场系统实现日志

## 结论

场景转场系统的实现为Hollow-ming项目提供了平滑、自然的场景切换体验，增强了应用的视觉表现力和用户体验。系统设计考虑了扩展性和性能，能够支持未来更多转场效果的添加。通过良好的抽象和模块化设计，场景转场系统与渲染系统和场景系统实现了低耦合的集成。 