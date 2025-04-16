# 设计文档

## 系统架构设计

### 整体架构

Hollow-ming采用分层架构设计，主要由以下几个层次组成：

1. **核心层（Core Layer）**：提供应用程序的基础设施，包括应用程序生命周期管理、事件系统、配置管理等。
2. **服务层（Service Layer）**：提供各种通用服务，如资源管理、渲染、监控等。
3. **功能层（Function Layer）**：实现应用程序的具体功能，如场景管理、交互系统、行为系统等。
4. **表现层（Presentation Layer）**：负责用户界面和视觉效果。

### 模块划分

1. **核心系统（Core System）**
   - 应用程序核心（Application Core）
   - 事件系统（Event System）
   - 配置管理（Configuration Management）
   - 调试工具（Debug Tools）

2. **资源管理系统（Resource Management System）**
   - 资源加载（Resource Loading）
   - 资源缓存（Resource Caching）
   - 资源类型抽象（Resource Type Abstraction）

3. **渲染系统（Rendering System）**
   - 渲染器抽象（Renderer Abstraction）
   - 精灵系统（Sprite System）
   - 动画系统（Animation System）
   - 特效系统（Effect System）
   - 粒子系统（Particle System）

4. **场景系统（Scene System）**
   - 场景管理（Scene Management）
   - 场景转场（Scene Transition）

5. **交互系统（Interaction System）**
   - 鼠标交互（Mouse Interaction）
   - 热键管理（Hotkey Management）
   - 行为触发器（Behavior Trigger）
   - 拖拽管理（Drag Management）
   - 事件过滤（Event Filtering）
   - 事件节流（Event Throttling）

6. **监控系统（Monitoring System）**
   - 性能监控（Performance Monitoring）
   - 资源监控（Resource Monitoring）
   - 性能分析（Performance Profiling）

7. **行为系统（Behavior System）**
   - 状态机（State Machine）
   - 行为管理器（Behavior Manager）
   - 环境感知器（Environment Sensor）
   - 决策系统（Decision Maker）
   - 具体行为实现（Behavior Implementations）

8. **UI系统（UI System）**
   - UI元素（UI Elements）
   - UI控件（UI Controls）
   - UI主题（UI Themes）

### 数据流

```
用户输入 -> 交互系统 -> 事件系统 -> 行为系统/场景系统 -> 渲染系统 -> 显示
```

## 主要模块设计

### 核心系统

#### 应用程序核心

应用程序核心负责管理应用程序的生命周期，包括初始化、主循环和清理。

```python
class Application:
    def __init__(self):
        self.running = False
        self.systems = []

    def initialize(self):
        # 初始化各个系统
        pass

    def run(self):
        self.running = True
        while self.running:
            self.update()
            self.render()
            self.process_events()

    def shutdown(self):
        self.running = False
        # 清理资源
        pass
```

#### 事件系统

事件系统采用观察者模式，用于系统内部模块之间的通信。

```python
class EventManager:
    def __init__(self):
        self.listeners = {}

    def add_listener(self, event_type, listener):
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(listener)

    def remove_listener(self, event_type, listener):
        if event_type in self.listeners and listener in self.listeners[event_type]:
            self.listeners[event_type].remove(listener)

    def dispatch(self, event):
        if event.type in self.listeners:
            for listener in self.listeners[event.type]:
                listener(event)
```

### 资源管理系统

#### 资源管理器

资源管理器负责加载和管理各种资源，包括图片、音频、字体等。

```python
class AssetManager:
    def __init__(self):
        self.assets = {}
        self.loaders = {}

    def register_loader(self, asset_type, loader):
        self.loaders[asset_type] = loader

    def load(self, asset_id, asset_path, asset_type):
        if asset_id in self.assets:
            return self.assets[asset_id]

        if asset_type in self.loaders:
            asset = self.loaders[asset_type].load(asset_path)
            self.assets[asset_id] = asset
            return asset
        
        return None

    def unload(self, asset_id):
        if asset_id in self.assets:
            del self.assets[asset_id]
```

### 渲染系统

#### 渲染器

渲染器负责绘制图形和处理渲染状态。

```python
class Renderer:
    def __init__(self):
        self.drawables = []

    def add_drawable(self, drawable):
        self.drawables.append(drawable)

    def remove_drawable(self, drawable):
        if drawable in self.drawables:
            self.drawables.remove(drawable)

    def render(self):
        for drawable in sorted(self.drawables, key=lambda d: d.z_order):
            drawable.draw(self)
```

### 场景系统

#### 场景管理器

场景管理器负责管理不同场景之间的切换。

```python
class SceneManager:
    def __init__(self):
        self.scenes = {}
        self.current_scene = None

    def add_scene(self, scene_id, scene):
        self.scenes[scene_id] = scene

    def switch_scene(self, scene_id):
        if self.current_scene:
            self.current_scene.exit()
        
        if scene_id in self.scenes:
            self.current_scene = self.scenes[scene_id]
            self.current_scene.enter()
```

### 交互系统

#### 交互管理器

交互管理器负责处理用户输入和生成交互事件。

```python
class InteractionManager:
    def __init__(self, event_manager):
        self.event_manager = event_manager
        self.mouse_handler = MouseHandler(event_manager)
        self.hotkey_manager = HotkeyManager(event_manager)
        self.drag_manager = DragManager(event_manager)

    def process_input(self, input_event):
        # 处理输入事件
        pass
```

### 监控系统

#### 性能监控器

性能监控器负责收集和分析性能指标。

```python
class PerformanceMonitor:
    def __init__(self):
        self.fps = 0
        self.frame_time = 0
        self.memory_usage = 0

    def update(self):
        # 更新性能指标
        pass

    def get_report(self):
        # 生成性能报告
        pass
```

### 行为系统

#### 状态机

状态机负责管理桌宠的状态和状态转换。

```python
class State:
    def __init__(self, name, on_enter=None, on_exit=None, duration=0):
        self.name = name
        self.on_enter = on_enter
        self.on_exit = on_exit
        self.duration = duration
        self.transitions = []

    def add_transition(self, to_state, condition):
        self.transitions.append((to_state, condition))

class StateMachine:
    def __init__(self):
        self.states = {}
        self.current_state = None
        self.history = []

    def add_state(self, state_name, on_enter=None, on_exit=None, duration=0):
        self.states[state_name] = State(state_name, on_enter, on_exit, duration)
        return self.states[state_name]

    def add_transition(self, from_state_name, to_state_name, condition):
        if from_state_name in self.states and to_state_name in self.states:
            self.states[from_state_name].add_transition(to_state_name, condition)

    def set_state(self, state_name):
        if state_name in self.states:
            if self.current_state:
                if self.current_state.on_exit:
                    self.current_state.on_exit()
                self.history.append(self.current_state.name)

            self.current_state = self.states[state_name]
            
            if self.current_state.on_enter:
                self.current_state.on_enter()

    def update(self):
        if not self.current_state:
            return

        for to_state, condition in self.current_state.transitions:
            if condition():
                self.set_state(to_state)
                break
```

#### 行为管理器

行为管理器负责管理桌宠的各种行为。

```python
class Behavior:
    def __init__(self, name, priority=0):
        self.name = name
        self.priority = priority
        self.is_running = False

    def can_execute(self):
        return True

    def execute(self):
        self.is_running = True

    def interrupt(self):
        self.is_running = False

class BehaviorManager:
    def __init__(self):
        self.behaviors = {}
        self.current_behavior = None

    def register_behavior(self, behavior_name, behavior_class):
        self.behaviors[behavior_name] = behavior_class

    def create_behavior(self, behavior_name, **kwargs):
        if behavior_name in self.behaviors:
            return self.behaviors[behavior_name](**kwargs)
        return None

    def execute_behavior(self, behavior):
        if not behavior.can_execute():
            return False

        if self.current_behavior:
            if behavior.priority <= self.current_behavior.priority:
                return False
            self.current_behavior.interrupt()

        self.current_behavior = behavior
        self.current_behavior.execute()
        return True

    def update(self):
        if self.current_behavior and self.current_behavior.is_running:
            self.current_behavior.update()
```

### UI系统

#### UI管理器

UI管理器负责管理用户界面元素。

```python
class UIManager:
    def __init__(self):
        self.elements = []

    def add_element(self, element):
        self.elements.append(element)

    def remove_element(self, element):
        if element in self.elements:
            self.elements.remove(element)

    def update(self):
        for element in self.elements:
            element.update()

    def render(self, renderer):
        for element in sorted(self.elements, key=lambda e: e.z_order):
            element.render(renderer)
```

## 关键算法和数据结构

### 状态机

状态机使用有向图数据结构，其中节点是状态，边是转换条件。

```
状态A --(条件1)--> 状态B
      --(条件2)--> 状态C
状态B --(条件3)--> 状态A
状态C --(条件4)--> 状态B
```

### 行为树

行为树使用树形数据结构，用于实现复杂的决策逻辑。

```
        Root
       /    \
  Sequence  Selector
  /  |  \    /  |  \
 A   B   C  D   E   F
```

### 资源缓存

资源缓存使用LRU（最近最少使用）算法进行缓存管理。

### 事件过滤

事件过滤使用责任链模式，每个过滤器可以选择处理或传递事件。

### 粒子系统

粒子系统使用面向数据的设计，将粒子数据存储在连续的内存块中，以提高性能。

## 技术选型

### 编程语言

- **Python**：主要开发语言，具有良好的跨平台性和丰富的库支持。

### 图形渲染

- **PyQt6**：用于窗口管理和图形渲染，提供丰富的GUI组件和OpenGL支持。

### 音频处理

- **pygame**：用于音频播放和处理，提供简单易用的音频API。

### 资源管理

- 自定义资源管理系统，支持异步加载和缓存机制。

### 事件系统

- 基于观察者模式的自定义事件系统，实现模块间的解耦。

### 物理引擎

- 简单的物理系统，使用基础的碰撞检测和响应算法。

## API设计规范

### 命名约定

- **类名**：使用PascalCase（如`AssetManager`）
- **方法名**：使用snake_case（如`load_asset`）
- **变量名**：使用snake_case，描述性命名
- **常量**：使用大写下划线（如`MAX_FPS`）

### 错误处理

- 使用异常机制处理错误
- 定义自定义异常类型
- 在适当的地方捕获和记录异常

### 接口设计

- 使用抽象基类定义接口
- 遵循单一职责原则
- 保持接口简单和一致 