# 项目结构

此文档记录Hollow-ming项目的最新文件结构和模块组织。

## 目录结构

```
Hollow-ming/
├── status/                 # 主程序目录
│   ├── core/               # 核心系统
│   │   ├── __init__.py     # 初始化文件 [已完成]
│   │   ├── application.py  # 应用程序核心 [已完成]
│   │   ├── event_system.py # 事件系统 [已完成]
│   │   ├── app.py          # 应用程序核心类，负责引擎初始化和主循环 [已完成]
│   │   ├── events.py       # 事件系统，提供观察者模式的事件分发 [已完成]
│   │   ├── config.py       # 配置管理器，处理全局配置和设置 [已完成]
│   │   ├── utils.py        # 通用工具函数和辅助类 [已完成]
│   │   ├── debug.py        # 调试辅助工具和性能记录 [已完成]
│   │   └── constants.py    # 全局常量定义 [已完成]
│   │
│   ├── behavior/           # 桌宠行为系统
│   │   ├── __init__.py     # 初始化文件 [已完成]
│   │   ├── state_machine.py # 状态机核心实现 [已完成]
│   │   ├── behavior_manager.py # 行为管理器，管理行为的创建和执行 [已完成]
│   │   ├── environment_sensor.py # 环境感知器，感知桌面环境 [计划中]
│   │   ├── decision_maker.py # 决策系统，选择合适的行为 [计划中]
│   │   └── behaviors/      # 具体行为实现
│   │       ├── __init__.py # 初始化文件 [计划中]
│   │       ├── idle_behaviors.py # 空闲行为 [计划中]
│   │       ├── movement_behaviors.py # 移动行为 [计划中]
│   │       └── reaction_behaviors.py # 反应行为 [计划中]
│   │
│   ├── resources/           # 资源管理系统
│   │   ├── __init__.py     # 初始化文件 [已完成]
│   │   ├── asset_manager.py # 资源管理器，处理各类资源的加载和卸载 [已完成]
│   │   ├── cache.py        # 缓存系统，提供资源缓存功能 [已完成]
│   │   ├── resource_loader.py # 资源加载器，支持不同类型资源的加载 [已完成]
│   │   ├── loaders.py      # 资源加载器集合，支持不同类型资源的加载 [已完成]
│   │   └── asset_types.py  # 资源类型定义 [已完成]
│   │
│   ├── scenes/              # 场景系统
│   │   ├── __init__.py     # 初始化文件 [已完成]
│   │   ├── scene_base.py   # 场景基类，定义场景接口 [已完成]
│   │   ├── scene_transition.py # 场景转场系统，提供场景间的过渡效果 [已完成]
│   │   └── scene_manager.py # 场景管理器，负责场景切换和管理 [已完成]
│   │
│   ├── interaction/        # 交互系统
│   │   ├── __init__.py     # 初始化文件 [已完成]
│   │   ├── interaction_manager.py # 交互管理器，统一管理所有交互子系统 [已完成]
│   │   ├── interaction_event.py # 交互事件类型和数据结构 [已完成]
│   │   ├── mouse_interaction.py # 鼠标交互，处理鼠标事件 [已完成]
│   │   ├── tray_icon.py    # 系统托盘图标，实现托盘功能 [已完成]
│   │   ├── context_menu.py # 上下文菜单，处理右键菜单 [已完成]
│   │   ├── hotkey.py       # 热键管理器，处理全局热键 [已完成]
│   │   ├── hotkey_win.py   # Windows平台热键实现 [已完成]
│   │   ├── behavior_trigger.py # 行为触发器，基于时间和事件触发 [已完成]
│   │   ├── drag_manager.py # 拖拽管理器，处理窗口拖拽 [已完成]
│   │   ├── event_filter.py # 事件过滤系统 [已完成]
│   │   └── event_throttler.py # 事件节流系统 [已完成]
│   │
│   ├── monitoring/         # 系统监控模块
│   │   ├── __init__.py     # 初始化文件 [已完成]
│   │   ├── system_info.py  # 系统信息收集 [已完成]
│   │   ├── data_process.py # 数据处理 [已完成]
│   │   ├── ui_controller.py # UI控制器 [已完成]
│   │   ├── monitor.py      # 监控系统核心 [已完成]
│   │   ├── performance.py  # 性能监控工具，记录和分析性能指标 [已完成]
│   │   ├── profiler.py     # 性能分析器，用于分析性能瓶颈 [已完成]
│   │   └── tracker.py      # 资源使用追踪器 [已完成]
│   │
│   ├── renderer/           # 渲染系统
│   │   ├── __init__.py     # 初始化文件 [已完成]
│   │   ├── renderer_base.py # 渲染器基类，定义渲染接口 [已完成]
│   │   ├── renderer_manager.py # 渲染管理器，协调渲染过程 [已完成]
│   │   ├── pyqt_renderer.py # PyQt渲染器实现 [已完成]
│   │   ├── drawable.py     # 可绘制对象基类 [已完成]
│   │   ├── primitives.py   # 基础图形元素 [已完成]
│   │   ├── sprite.py       # 精灵系统，支持图像渲染 [已完成]
│   │   ├── animation.py    # 动画系统，提供动画支持 [已完成]
│   │   ├── effects.py      # 特效系统，提供各种视觉效果 [已完成]
│   │   ├── particle.py     # 粒子系统，用于创建和管理粒子效果 [已完成]
│   │   ├── transition.py   # 过渡效果系统，提供多种视觉转场效果 [已完成]
│   │   └── ui_renderer.py  # UI渲染器，专门处理UI元素的渲染 [已完成]
│   │
│   ├── ui/                 # 用户界面
│   │   ├── __init__.py     # 初始化文件 [已完成]
│   │   ├── monitor_ui.py   # 监控UI界面 [已完成]
│   │   ├── monitor_app.py  # 监控应用 [已完成]
│   │   ├── main_pet_window.py # 桌宠主窗口UI [已完成]
│   │   ├── ui_element.py   # UI元素基类 [计划中]
│   │   ├── ui_container.py # UI容器，用于组织UI元素 [计划中]
│   │   ├── ui_manager.py   # UI管理器，管理UI元素的生命周期 [计划中]
│   │   └── controls/       # 各种UI控件的实现 [计划中]
│   │       ├── button.py   # 按钮控件 [计划中]
│   │       ├── label.py    # 标签控件 [计划中]
│   │       ├── input.py    # 输入框控件 [计划中]
│   │       ├── panel.py    # 面板控件 [计划中]
│   │       └── slider.py   # 滑块控件 [计划中]
│   │
│   ├── examples/           # 示例
│   │   ├── __init__.py     # 初始化文件 [已完成]
│   │   ├── run_monitor_ui.py # 运行监控UI [已完成]
│   │   ├── monitor_example.py # 监控示例 [已完成]
│   │   ├── effects_example.py # 特效系统示例 [已完成]
│   │   ├── demo_app.py     # 演示应用程序 [计划中]
│   │   ├── particle_demo.py # 粒子系统演示 [计划中]
│   │   ├── ui_demo.py      # UI系统演示 [计划中]
│   │   └── transition_demo.py # 过渡效果演示 [计划中]
│   │
│   └── main.py             # 主程序入口 [已完成]
│
├── tests/                  # 测试目录
│   ├── __init__.py         # 测试初始化 [已完成]
│   ├── core/               # 核心系统测试
│   │   ├── __init__.py     # 初始化文件 [已完成]
│   │   ├── test_application.py # 应用程序测试 [已完成]
│   │   ├── test_event_system.py # 事件系统测试 [已完成]
│   │   ├── test_asset_manager.py # 资源管理器测试 [已完成]
│   │   ├── test_asset_manager_advanced.py # 资源管理器高级测试 [已完成]
│   │   ├── test_asset_manager_performance.py # 资源管理器性能测试 [已完成]
│   │   ├── test_cache.py   # 缓存系统测试 [已完成]
│   │   ├── test_app.py     # 应用程序核心测试 [已完成]
│   │   ├── test_events.py  # 事件系统测试 [已完成]
│   │   ├── test_config.py  # 配置管理器测试 [已完成]
│   │   └── test_utils.py   # 工具函数测试 [已完成]
│   │
│   ├── behavior/           # 行为系统测试
│   │   ├── __init__.py     # 初始化文件 [已完成]
│   │   ├── test_state_machine.py # 状态机测试 [已完成]
│   │   ├── test_behavior_manager.py # 行为管理器测试 [已完成]
│   │   ├── test_environment_sensor.py # 环境感知器测试 [计划中]
│   │   ├── test_decision_maker.py # 决策系统测试 [计划中]
│   │   └── test_behaviors/ # 具体行为测试 [计划中]
│   │       ├── __init__.py # 初始化文件 [计划中]
│   │       ├── test_idle_behaviors.py # 空闲行为测试 [计划中]
│   │       ├── test_movement_behaviors.py # 移动行为测试 [计划中]
│   │       └── test_reaction_behaviors.py # 反应行为测试 [计划中]
│   │
│   ├── scene/              # 场景系统测试
│   │   ├── __init__.py     # 初始化文件 [已完成]
│   │   ├── test_scene_base.py # 场景基类测试 [已完成]
│   │   └── test_transition.py # 场景转场测试 [已完成]
│   │
│   ├── resources/          # 资源管理测试
│   │   ├── __init__.py     # 初始化文件 [已完成]
│   │   ├── test_resource_loader.py # 资源加载器测试 [已完成]
│   │   ├── test_loaders.py # 资源加载器测试 [已完成]
│   │   └── test_cache.py   # 缓存系统测试 [已完成]
│   │
│   ├── interaction/        # 交互系统测试
│   │   ├── __init__.py     # 初始化文件 [已完成]
│   │   ├── test_interaction_manager.py # 交互管理器测试 [已完成]
│   │   ├── test_hotkey_manager.py # 热键管理器测试 [已完成]
│   │   ├── test_behavior_trigger.py # 行为触发器测试 [已完成]
│   │   ├── test_drag_manager.py # 拖拽管理器测试 [已完成]
│   │   ├── test_event_filter.py # 事件过滤器测试 [已完成]
│   │   └── test_event_throttler.py # 事件节流器测试 [已完成]
│   │
│   ├── renderer/           # 渲染系统测试
│   │   ├── __init__.py     # 初始化文件 [已完成]
│   │   ├── test_renderer.py # 渲染器测试 [计划中]
│   │   ├── test_animation.py # 动画系统测试 [待完善]
│   │   ├── test_effects.py # 特效系统测试 [已完成]
│   │   ├── test_renderer_base.py # 渲染器基类测试 [已完成]
│   │   ├── test_renderer_manager.py # 渲染管理器测试 [已完成]
│   │   ├── test_sprite.py  # 精灵系统测试 [已完成]
│   │   ├── test_animation.py # 动画系统测试 [待完善]
│   │   ├── test_effects.py # 特效系统测试 [已完成]
│   │   ├── test_particle.py # 粒子系统测试 [已完成]
│   │   ├── test_transition.py # 过渡效果系统测试 [已完成]
│   │   └── test_scene_transition.py # 场景过渡系统与过渡效果系统集成测试 [已完成]
│   │
│   ├── monitoring/         # 监控系统测试
│   │   ├── __init__.py     # 初始化文件 [已完成]
│   │   ├── test_monitor.py # 系统监控器测试 [已完成]
│   │   ├── test_performance.py # 性能监控工具测试 [已完成]
│   │   ├── test_profiler.py # 性能分析器测试 [已完成]
│   │   └── test_tracker.py # 资源使用追踪器测试 [已完成]
│   │
│   └── ui/                 # 用户界面测试
│       ├── __init__.py     # 初始化文件 [计划中]
│       ├── test_ui_element.py # UI元素测试 [计划中]
│       ├── test_ui_container.py # UI容器测试 [计划中]
│       ├── test_ui_manager.py # UI管理器测试 [计划中]
│       └── test_controls/  # 各种UI控件的测试 [计划中]
│           ├── test_button.py # 按钮控件测试 [计划中]
│           ├── test_label.py  # 标签控件测试 [计划中]
│           ├── test_input.py  # 输入框控件测试 [计划中]
│           ├── test_panel.py  # 面板控件测试 [计划中]
│           └── test_slider.py # 滑块控件测试 [计划中]
│
├── docs/                   # 文档目录
│   ├── api/                # API文档 [计划中]
│   └── user_guide/         # 用户指南 [计划中]
│
├── resources/              # 资源文件
│   ├── images/             # 图片资源 [计划中]
│   ├── sounds/             # 声音资源 [计划中]
│   └── fonts/              # 字体资源 [计划中]
│
├── Logs/                   # 详细变更日志目录 [已完成]
├── Structure.md            # 项目结构文档 [已完成]
├── Thread.md               # 任务进度文档 [已完成]
├── Log.md                  # 变更日志索引 [已完成]
├── Design.md               # 设计文档 [已完成]
├── Issues.md               # 问题跟踪 [已完成]
└── Diagram.md              # 图表索引 [已完成]
```

## 模块说明

### 核心系统 (Core)

核心系统负责应用程序的基础架构，包括应用程序生命周期管理、事件系统等。

- **application.py**: 应用程序核心，管理程序生命周期、主循环和基本流程控制。
- **event_system.py**: 事件系统，实现观察者模式，用于系统内部模块通信和解耦。
- **app.py**: 应用程序核心类，负责引擎初始化和主循环。
- **events.py**: 事件系统，提供观察者模式的事件分发。
- **config.py**: 配置管理器，处理全局配置和设置。
- **utils.py**: 通用工具函数和辅助类。
- **debug.py**: 调试辅助工具和性能记录。
- **constants.py**: 全局常量定义。

### 桌宠行为系统 (Behavior)

桌宠行为系统负责管理桌宠的自主行为和状态转换，是实现有趣交互体验的核心。

- **state_machine.py**: 状态机核心，管理桌宠的状态和状态转换。
- **behavior_manager.py**: 行为管理器，负责行为的注册、创建和执行。
- **environment_sensor.py**: 环境感知器，负责感知屏幕边界、窗口位置等信息。
- **decision_maker.py**: 决策系统，基于各种因素选择合适的行为。
- **behaviors/**: 具体行为实现，包括空闲行为、移动行为和反应行为等。

### 资源管理系统 (Resource)

资源管理系统负责加载、管理和卸载游戏资源，包括图片、音频、字体等。

- **asset_manager.py**: 资源管理器，提供统一的资源访问接口，实现单例模式。
- **cache.py**: 缓存系统，实现高效的资源缓存机制，支持多种缓存策略。
- **resource_loader.py**: 资源加载器，负责从文件系统加载各类资源，支持多种资源类型。
- **loaders.py**: 资源加载器集合，支持不同类型资源的加载。
- **asset_types.py**: 资源类型定义。

### 场景系统 (Scenes)

场景系统负责管理不同游戏场景间的切换和管理。

- **scene_base.py**: 场景基类，定义场景生命周期方法和基本功能。
- **scene_transition.py**: 场景转场模块，提供场景切换时的平滑视觉效果。
- **scene_manager.py**: 场景管理器，管理场景注册、切换和转场效果。

### 交互系统 (Interaction)

交互系统负责处理用户输入和生成交互事件。

- **interaction_manager.py**: 交互管理器，统一管理所有交互子系统。
- **interaction_event.py**: 交互事件定义，包括鼠标事件、键盘事件等。
- **mouse_interaction.py**: 鼠标交互，处理鼠标事件，如点击、移动和拖拽。
- **tray_icon.py**: 系统托盘图标，实现托盘功能和菜单。
- **context_menu.py**: 上下文菜单，处理右键菜单。
- **hotkey.py**: 热键管理器，处理全局热键。
- **hotkey_win.py**: Windows平台热键实现。
- **behavior_trigger.py**: 行为触发器，基于时间和事件触发桌宠行为。
- **drag_manager.py**: 拖拽管理器，处理窗口拖拽。
- **event_filter.py**: 事件过滤系统，过滤重复或不必要的事件。
- **event_throttler.py**: 事件节流系统，控制事件频率。

### 监控系统 (Monitoring)

监控系统负责收集和分析性能指标和系统状态。

- **system_info.py**: 系统信息收集，获取系统运行状态。
- **data_process.py**: 数据处理，分析和处理收集的数据。
- **ui_controller.py**: UI控制器，控制监控UI的显示和更新。
- **monitor.py**: 监控系统核心，协调监控相关组件。
- **performance.py**: 性能监控工具，记录和分析性能指标。
- **profiler.py**: 性能分析器，用于分析性能瓶颈。
- **tracker.py**: 资源使用追踪器，监控资源使用情况。

### 渲染系统 (Renderer)

渲染系统负责图形绘制，包括基础图形、精灵和动画等。

- **renderer_base.py**: 渲染器基类，定义渲染器接口和基本功能。
- **renderer_manager.py**: 渲染管理器，管理多个渲染器和渲染过程。
- **pyqt_renderer.py**: PyQt渲染器实现，使用PyQt进行图形绘制。
- **drawable.py**: 可绘制对象基类，定义所有可绘制对象的接口。
- **primitives.py**: 基础图形元素，如点、线、矩形等。
- **sprite.py**: 精灵系统，支持精灵渲染和精灵表管理。
- **animation.py**: 动画系统，提供属性动画和过渡效果。
- **effects.py**: 特效系统，提供各种视觉效果。
- **particle.py**: 粒子系统，用于创建和管理粒子效果。
- **transition.py**: 过渡效果系统，提供多种视觉转场效果。
- **ui_renderer.py**: UI渲染器，专门处理UI元素的渲染。

### 用户界面 (UI)

用户界面系统负责创建和管理UI界面和控件。

- **monitor_ui.py**: 监控UI界面，显示监控信息。
- **monitor_app.py**: 监控应用，提供监控功能。
- **main_pet_window.py**: 桌宠主窗口UI，实现无边框、可拖动窗口。
- **ui_element.py**: UI元素基类，定义所有UI元素的接口。
- **ui_container.py**: UI容器，用于组织UI元素。
- **ui_manager.py**: UI管理器，管理UI元素的生命周期。
- **controls/**: 各种UI控件的实现，如按钮、标签等。

### 主程序入口 (Main)

- **main.py**: 主程序入口，初始化并启动应用程序。

## 测试系统 (Tests)

测试系统包含各个模块的单元测试和集成测试。

- **core/**: 核心系统测试
  - **test_application.py**: 应用程序和事件系统测试
  - **test_event_system.py**: 事件系统测试
  - **test_asset_manager.py**: 资源管理器测试，包括资源类型、异步预加载和缓存管理测试
  - **test_asset_manager_advanced.py**: 资源管理器高级测试，测试依赖关系、事件和回调
  - **test_asset_manager_performance.py**: 资源管理器性能测试，测试并发加载、缓存命中率和内存使用
  - **test_cache.py**: 缓存系统测试，包括缓存策略、并发和事件测试
- **behavior/**: 行为系统测试，验证状态机和行为管理功能
  - **test_state_machine.py**: 状态机测试，验证状态转换和条件判断
  - **test_behavior_manager.py**: 行为管理器测试，验证行为注册、创建和执行
- **scene/**: 场景系统测试，验证场景生命周期、场景转场和场景管理功能
  - **test_scene_base.py**: 场景基类测试
  - **test_transition.py**: 场景转场测试
- **resources/**: 资源加载器测试，确保资源加载正确工作
  - **test_resource_loader.py**: 资源加载器测试
- **interaction/**: 交互系统测试，验证用户交互和桌宠行为触发功能
  - **test_interaction_manager.py**: 交互管理器测试
  - **test_hotkey_manager.py**: 热键管理器测试
  - **test_behavior_trigger.py**: 行为触发器测试
  - **test_drag_manager.py**: 拖拽管理器测试
  - **test_event_filter.py**: 事件过滤器测试
  - **test_event_throttler.py**: 事件节流器测试
- **renderer/**: 渲染系统测试，验证渲染器、动画系统和特效系统功能
  - **test_renderer.py**: 渲染器测试 [计划中]
  - **test_animation.py**: 动画系统测试 [待完善]
  - **test_effects.py**: 特效系统测试，验证特效和粒子系统功能

### tests/launcher/
快捷启动器模块的单元测试。[已完成]

- **test_launcher_types.py**: 测试启动器数据类型 [已完成]
- **test_launcher_manager.py**: 测试启动器管理器 [已完成]

### status/examples/
示例代码和演示应用。

- **launcher_example.py**: 快速启动器功能演示 [已完成]

## 依赖关系

- **核心系统**: 基础模块，被其他所有模块依赖
- **资源管理系统**: 依赖于核心系统，被渲染系统和场景系统依赖
- **渲染系统**: 依赖于核心系统和资源管理系统，被场景系统依赖
- **场景系统**: 依赖于核心系统、资源管理系统、渲染系统和交互系统
- **交互系统**: 依赖于核心系统，与场景系统协作
- **监控系统**: 依赖于核心系统，监控其他系统的性能和资源使用
- **行为系统**: 依赖于核心系统和交互系统，与场景系统和渲染系统协作