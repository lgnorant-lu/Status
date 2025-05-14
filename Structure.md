# 项目结构文档

## 概述
本文档描述了 `Status-Ming` 项目（作者: `lgnorant-lu`）的当前文件和目录结构。每个主要模块都附有简要描述和状态标记。

**状态标记说明:**
- `[已完成]`：模块功能完整，文档和测试齐全。
- `[进行中]`：模块正在积极开发中。
- `[计划中]`：模块已规划，但尚未开始开发。
- `[待补全]`：模块存在，但描述、功能细节或文档需要补充。
- `[核心模块]`：项目的核心功能组件。
- `[工具模块]`：辅助开发或项目管理工具。
- `[配置模块]`：包含配置文件或配置相关逻辑。
- `[资源模块]`：存放静态资源。
- `[测试模块]`：包含测试代码。
- `[文档模块]`：包含项目文档。
- `[日志模块]`：存放日志文件。
- `[示例模块]`：包含示例代码或演示。

---

## 根目录结构

```
.
├── .git/                       # Git版本控制目录 [配置模块]
├── .gitignore                  # Git忽略文件配置 [配置模块] [已完成]
├── .pytest_cache/              # Pytest缓存目录 [测试模块]
├── .tasks/                     # RIPER-5任务文件目录 [工具模块]
├── .vscode/                    # VS Code编辑器配置 [配置模块]
├── assets/                     # 静态资源 [资源模块] [进行中]
│   ├── placeholders/           # 当前使用的占位符资源 [进行中]
│   │   ├── cat_idle_strip.png  # 猫咪待机动画序列帧图 (占位符)
│   │   ├── cat_walk_strip.png  # 猫咪行走动画序列帧图 (占位符)
│   │   └── app_icon.png        # 应用图标 (占位符)
│   └── cat_theme/              # 新猫咪主题资源 (规划中) [计划中]
│       └── ... 
├── Diagrams/                   # 项目图表 (Graphviz Python脚本) [文档模块] [待重新设计-Status-Ming]
│   ├── Architecture/           # 架构图 [待重新设计-Status-Ming]
│   ├── Algorithms/             # 算法图 [待重新设计-Status-Ming]
│   ├── DataModels/             # 数据模型图 [待重新设计-Status-Ming]
│   ├── Flowcharts/             # 流程图 [待重新设计-Status-Ming]
│   └── Modules/                # 模块图 [待重新设计-Status-Ming]
├── docs/                       # 项目详细文档 [文档模块] [进行中-内容重构]
│   ├── api/                    # API文档 [待审查-Status-Ming]
│   ├── developer/              # 开发者文档 [待审查-Status-Ming]
│   │   └── plugin_development_guide.md # 插件开发指南 [已完成]
│   ├── overview/               # 项目概览文档 [待审查-Status-Ming]
│   ├── user/                   # 用户手册 [待审查-Status-Ming]
│   ├── Diagrams/               # 文档用图表副本 [待审查-Status-Ming]
│   ├── changelog.md            # 项目变更日志 [待审查-Status-Ming]
│   ├── contributing.md         # 贡献指南 [待审查-Status-Ming]
│   ├── index.md                # 文档首页 [待审查-Status-Ming]
│   ├── README.md               # Docs模块说明 [待审查-Status-Ming]
│   ├── roadmap.md              # 项目路线图 [待审查-Status-Ming]
│   └── ui_design_guide.md      # UI设计规范 [已废弃-旧主题]
├── Logs/                       # 详细开发日志 [日志模块] [进行中]
│   ├── 2025-04-17_project_cleanup_phase1.md # 项目清理日志 [已完成]
│   └── ... (其他日志文件)
├── plugins/                    # 插件目录 [核心模块] [已完成]
│   └── example_plugin/         # 示例插件 [示例模块] [已完成]
│       ├── __init__.py         # 插件入口
│       └── ... (插件文件)
├── status/                     # 项目核心应用代码 [核心模块] [进行中]
│   ├── __init__.py             # 包初始化文件
│   ├── behavior/               # 桌宠（猫咪占位符）行为逻辑，响应系统参数，基于PySide6事件。 [进行中]
│   │   └── ... [待补全]
│   ├── core/                   # 核心基础模块 (事件、配置等) [进行中]
│   │   ├── __init__.py         # 包初始化文件
│   │   ├── event_system.py     # 旧版事件系统 [已完成]
│   │   ├── types.py            # 核心类型定义 [已完成]
│   │   ├── logging/            # 增强日志系统 [已完成]
│   │   │   ├── __init__.py     # 包初始化文件
│   │   │   └── log_manager.py  # 日志管理器实现 [已完成]
│   │   ├── recovery/           # 错误恢复机制 [已完成]
│   │   │   ├── __init__.py     # 包初始化文件
│   │   │   ├── state_manager.py    # 状态管理器实现 [已完成]
│   │   │   ├── recovery_manager.py # 恢复管理器实现 [已完成]
│   │   │   └── exception_handler.py # 异常处理器实现 [已完成]
│   │   └── ... [待补全]
│   ├── events/                 # 增强事件系统 [核心模块] [已完成]
│   │   ├── __init__.py         # 包初始化文件
│   │   ├── event_manager.py    # 事件管理器实现，包含优先级、过滤和节流功能 [已完成]
│   │   ├── event_types.py      # 事件类型定义 [已完成]
│   │   └── ... [待补全]
│   ├── interaction/            # 基于PySide6的用户交互处理 (鼠标、键盘、系统托盘等)。 [进行中]
│   │   ├── __init__.py
│   │   ├── base_interaction_handler.py # 交互处理基类 [待补全]
│   │   ├── behavior_trigger.py         # 行为触发器 [待补全]
│   │   ├── context_menu.py           # 上下文菜单逻辑 [待补全]
│   │   ├── drag_manager.py           # 拖拽管理器 [待补全]
│   │   ├── event_filter.py           # 事件过滤器 [待补全]
│   │   ├── event_throttler.py        # 事件节流器 [待补全]
│   │   ├── hotkey_manager.py         # 热键管理器 [待补全]
│   │   ├── interaction_event.py      # 交互事件定义 [待补全]
│   │   ├── interaction_manager.py    # 交互总管理器 (Linter错误待处理) [进行中]
│   │   └── mouse_interaction.py      # 鼠标交互处理 [待补全]
│   ├── main.py                 # 应用主入口, 依赖PlaceholderFactory加载动画 [核心模块] [进行中]
│   ├── monitoring/             # 系统监控模块 [计划中]
│   │   └── ... [待补全]
│   ├── pet_assets/             # 宠物资源管理模块 [已完成]
│   │   ├── __init__.py         # 包初始化文件 [已完成]
│   │   ├── placeholder_factory.py # 占位符工厂，负责动态加载状态占位符 [已完成]
│   │   └── placeholders/       # 各状态的占位符实现目录 [已完成]
│   │       ├── __init__.py     # 包初始化文件 [已完成]
│   │       ├── happy_placeholder.py # \"开心\"状态占位符实现 [已完成]
│   │       ├── idle_placeholder.py # \"空闲\"状态占位符实现 (L4 质量) [已完成]
│   │       ├── busy_placeholder.py # \"忙碌\"状态占位符实现 (L4 质量) [已完成]
│   │       ├── memory_warning_placeholder.py # \"内存警告\"状态占位符实现 [已完成]
│   │       ├── error_placeholder.py # \"错误\"状态占位符实现 [已完成]
│   │       ├── clicked_placeholder.py # \"点击\"状态占位符实现 (L4 质量) [已完成]
│   │       ├── dragged_placeholder.py # \"拖拽\"状态占位符实现 [已完成]
│   │       ├── petted_placeholder.py # \"抚摸\"状态占位符实现 [已完成]
│   │       ├── hover_placeholder.py # \"悬停\"状态占位符实现 [已完成]
│   │       ├── morning_placeholder.py # \"早晨\"状态占位符实现 (L4 质量) [已完成]
│   │       ├── noon_placeholder.py # \"中午\"状态占位符实现 [已完成]
│   │       ├── afternoon_placeholder.py # \"下午\"状态占位符实现 [已完成]
│   │       ├── evening_placeholder.py # \"傍晚\"状态占位符实现 [已完成]
│   │       └── night_placeholder.py # \"夜晚\"状态占位符实现 (L4 质量) [已完成]
│   │       ├── spring_festival_placeholder.py # \"春节\"L4占位符实现 [已完成]
│   │       └── lichun_placeholder.py # \"立春\"L4占位符实现 [已完成]
│   ├── plugin/                 # 插件系统模块 [核心模块] [已完成]
│   │   ├── __init__.py         # 包初始化文件
│   │   ├── plugin_base.py      # 插件基类定义 [已完成]
│   │   ├── plugin_manager.py   # 插件管理器实现 [已完成]
│   │   ├── plugin_registry.py  # 插件注册表实现 [已完成]
│   │   └── ... [待补全]
│   ├── renderer/               # 基于PySide6的渲染逻辑 (猫咪占位符动画、未来UI元素等)。 [进行中]
│   │   └── ... [待补全]
│   ├── resources/              # 运行时资源管理 [进行中]
│   │   └── ... [待补全]
│   ├── scenes/                 # 场景管理 [进行中]
│   │   └── ... [待补全]
│   ├── ui/                     # 基于PySide6的用户界面元素和逻辑 (如设置面板、信息面板等)。 [进行中]
│   │   └── ... [待补全]
│   └── utils/                  # 通用工具函数 [进行中]
│       └── ... [待补全]
├── tests/                      # 测试代码 [测试模块] [进行中]
│   ├── __init__.py             # 包初始化文件
│   ├── conftest.py             # Pytest配置文件和fixtures [配置模块]
│   ├── events/                 # 事件系统测试 [已完成]
│   │   ├── __init__.py         # 包初始化文件
│   │   └── test_event_manager.py  # 事件管理器测试 [已完成]
│   ├── mocks.py                # Mock对象定义 [待补全]
│   ├── pet_assets/             # 宠物资源管理模块测试 [已完成]
│   │   ├── __init__.py         # 包初始化文件 [已完成]
│   │   ├── test_placeholder_factory.py # 占位符工厂测试 [已完成]
│   │   └── placeholders/       # 各状态占位符实现测试 [已完成]
│   │       ├── __init__.py     # 包初始化文件 [已完成]
│   │       ├── test_happy_placeholder.py # \"开心\"状态占位符测试 (L2/L3) [已完成]
│   │       ├── test_idle_placeholder.py # \"空闲\"状态占位符测试 (旧版L2/L3) [已完成]
│   │       ├── test_busy_placeholder.py # \"忙碌\"状态占位符测试 (旧版L2/L3) [已完成]
│   │       ├── test_memory_warning_placeholder.py # \"内存警告\"状态占位符测试 (L2/L3) [已完成]
│   │       ├── test_error_placeholder.py # \"错误\"状态占位符测试 (L2/L3) [已完成]
│   │       ├── test_clicked_placeholder.py # \"点击\"状态占位符测试 (旧版L2/L3) [已完成]
│   │       ├── test_dragged_placeholder.py # \"拖拽\"状态占位符测试 (L2/L3) [已完成]
│   │       ├── test_petted_placeholder.py # \"抚摸\"状态占位符测试 (L2/L3) [已完成]
│   │       ├── test_hover_placeholder.py # \"悬停\"状态占位符测试 (L2/L3) [已完成]
│   │       ├── test_morning_placeholder.py # \"早晨\"状态占位符测试 (旧版L2/L3) [已完成]
│   │       ├── test_noon_placeholder.py # \"中午\"状态占位符测试 (L2/L3) [已完成]
│   │       ├── test_afternoon_placeholder.py # \"下午\"状态占位符测试 (L2/L3) [已完成]
│   │       ├── test_evening_placeholder.py # \"傍晚\"状态占位符测试 (L2/L3) [已完成]
│   │       ├── test_night_placeholder.py # \"夜晚\"状态占位符测试 (旧版L2/L3) [已完成]
│   │       ├── test_idle_placeholder_core.py # \"空闲\"核心L4动画单元测试 [已完成]
│   │       ├── test_busy_placeholder_core.py # \"忙碌\"核心L4动画单元测试 [已完成]
│   │       ├── test_clicked_placeholder_core.py # \"点击\"核心L4动画单元测试 [已完成]
│   │       ├── test_morning_placeholder_core.py # \"早晨\"核心L4动画单元测试 [已完成]
│   │       └── test_night_placeholder_core.py # \"夜晚\"核心L4动画单元测试 [已完成]
│   │       ├── test_spring_festival_placeholder.py # \"春节\"L4占位符测试 [已完成]
│   │       └── test_lichun_placeholder.py # \"立春\"L4占位符测试 [已完成]
│   ├── plugin/                 # 插件系统测试 [已完成]
│   │   ├── __init__.py         # 包初始化文件
│   │   ├── test_plugin_manager.py  # 插件管理器测试 [已完成]
│   │   └── test_plugin_registry.py # 插件注册表测试 [已完成]
│   ├── run_tests.py            # 测试运行脚本 [工具模块]
│   ├── behavior/               # 行为模块测试 [待补全]
│   ├── core/                   # 核心模块测试 [待补全]
│   ├── interaction/            # 交互模块测试 [待补全]
│   ├── integration/            # 集成测试 [待补全]
│   ├── mocks/                  # (目录结构重复?) [待补全]
│   ├── monitoring/             # 监控模块测试 [待补全]
│   ├── renderer/               # 渲染模块测试 [进行中]
│   │   ├── test_drawable.py    # Drawable对象测试 [待补全]
│   │   └── test_effects.py     # 特效测试 [待补全]
│   ├── resources/              # 资源模块测试 [待补全]
│   ├── scenes/                 # 场景模块测试 [进行中]
│   │   └── test_scene_manager_transition.py # 场景切换测试 [待补全]
│   └── unit/                   # 单元测试 [待补全]
├── tools/                      # 辅助工具和脚本 [工具模块] [进行中]
│   ├── .git/                   # (嵌套Git仓库?)
│   ├── .gitignore              # 工具目录的Git忽略配置
│   ├── LICENSE                 # 工具许可证
│   ├── Plan.md                 # 工具开发计划 [待补全]
│   ├── README.md               # 工具模块说明
│   ├── build_resources.py      # Qt资源编译脚本 [待补全]
│   ├── icons/                  # 图标资源 [待补全]
│   ├── requirements.txt        # 工具依赖
│   ├── resources.py            # Qt资源模块 (Python) [待补全]
│   ├── resources.qrc           # Qt资源文件 (XML) [待补全]
│   ├── sprite_character_output/# 精灵处理输出目录 [待补全]
│   ├── sprite_editor/          # 精灵编辑器工具 [进行中]
│   │   └── ... [待补全]
│   └── sprite_extract_opencv.py # 使用OpenCV提取精灵的脚本 [待补全]
├── Design.md                   # 设计文档 (架构, 决策等) [文档模块] [进行中]
├── Development_Guidelines.md   # 开发规范文档 [文档模块] [进行中]
├── Diagram.md                  # 图表日志索引 [文档模块] [进行中]
├── Global.md                   # 全局宏定义与常量 [配置模块] [进行中]
├── Issues.md                   # 问题追踪文档 [文档模块] [进行中]
├── Log.md                      # 变更日志索引 [日志模块] [进行中]
├── README.md                   # 项目总览和入口说明 [文档模块] [已完成]
├── requirements.txt            # Python项目依赖 [配置模块] [进行中]
├── setup.py                    # 项目打包和分发脚本 [工具模块] [待补全]
└── Thread.md                   # 任务进程文档 [文档模块] [进行中]
├── data/                       # 数据存储目录 [资源模块] [已完成]
│   ├── .gitkeep                # 保证空目录包含在版本控制中 [已完成]
│   ├── states/                 # 应用状态存储目录 [已完成]
│   └── recovery/               # 恢复数据存储目录 [已完成]
│       └── reports/            # 崩溃报告存储目录 [已完成]
```

---

## 模块功能详述

### 1. `status/` - 核心应用代码
- **描述**: 包含桌宠应用 (`Status-Ming`) 的主要逻辑代码，包括核心引擎、渲染、交互、行为、资源管理、UI等，UI层基于PySide6。
- **子模块**:
    - `behavior/`: 管理和实现桌宠（猫咪占位符）的各种行为状态和逻辑，响应系统参数。`[进行中]`
    - `core/`: 提供项目范围内的核心基础服务，如事件总线、配置管理、日志封装等。`[进行中]`
      - `logging/`: 实现增强的日志系统，支持多日志级别、多输出目标和文件轮转功能。`[已完成]`
      - `recovery/`: 提供错误恢复机制，包括状态持久化、崩溃检测和异常处理功能。`[已完成]`
    - `events/`: 实现增强的事件系统，包括优先级、过滤、节流和异步处理功能。`[已完成]`
    - `interaction/`: 处理所有用户输入和系统交互（基于PySide6），如鼠标点击/移动、键盘输入、系统命令等。`[进行中]`
    - `main.py`: 应用程序的主入口点，负责初始化和启动整个应用。现在依赖 `PlaceholderFactory` 来加载所有状态动画，移除了内部的动画直接创建逻辑。`[核心模块] [进行中]`
    - `monitoring/`: (新规划) 负责监控系统性能、应用状态等。`[计划中]`
    - `pet_assets/`: 宠物资源管理模块，负责动态加载状态占位符。其子目录 `placeholders/` 存放了各个具体状态（如 idle, busy, morning, clicked 等）的动画实现模块。`[已完成]`
    - `plugin/`: 实现基于生命周期管理的插件系统，支持动态加载、启用和卸载插件。`[已完成]`
    - `renderer/`: 处理所有视觉元素的渲染（基于PySide6），包括桌宠精灵（猫咪占位符）、动画、未来UI组件等。`[进行中]`
    - `resources/`: 负责运行时资源的加载、管理和缓存。`[进行中]`
    - `scenes/`: 管理不同的应用场景或状态（如果项目需要）。`[进行中]`
    - `ui/`: 包含基于PySide6的用户界面的构建块和特定于UI的逻辑。`[进行中]`
    - `utils/`: 提供项目内各模块可复用的通用工具函数和类。`[进行中]`

### 2. `tests/` - 测试代码
- **描述**: 包含项目的所有测试代码，包括单元测试、集成测试和功能测试。
- **子模块**:
    - `events/`: 包含对增强事件系统的测试用例。`[已完成]`
    - `plugin/`: 包含对插件系统各组件的测试用例。`[已完成]`
    - `pet_assets/`: 包含对宠物资源管理模块的测试用例，包括工厂和所有具体的状态占位符。`[已完成]`
- **结构**: 通常会按照 `status/` 目录结构镜像组织测试文件。`[进行中]`

### 3. `plugins/` - 插件目录
- **描述**: 存放应用的所有插件，包括官方插件和第三方插件。`[已完成]`
- **子模块**:
    - `example_plugin/`: 作为插件开发参考的示例插件实现。`[已完成]`

### 4. `assets/` - 静态资源
- **描述**: 存放项目所需的所有静态资源。当前主要使用 `assets/placeholders/` 下的占位符图像，未来将替换为正式的猫咪主题资源（规划存放于 `assets/cat_theme/`）。`[进行中]`

### 5. `Diagrams/` - 项目图表
- **描述**: 存放使用 Python Graphviz 库创建的各种项目图表，用于可视化架构、模块依赖、流程等。所有图表均需基于 `Status-Ming` 项目重新设计。`[待重新设计-Status-Ming]`

### 6. `docs/` - 项目文档
- **描述**: 包含所有详细的项目文档，如API文档、用户手册、开发者指南、设计决策等。大部分文档源于旧项目，正在针对 `Status-Ming` 进行全面审查、更新或重写。`[进行中-内容重构]`
- **子模块**:
    - `developer/plugin_development_guide.md`: 插件开发指南，详细说明如何为Status-Ming开发插件。`[已完成]`

### 7. `Logs/` - 开发日志
- **描述**: 记录详细的开发过程、变更历史、遇到的问题和解决方案。`[进行中]`

### 8. `tools/` - 辅助工具
- **描述**: 包含用于辅助开发、构建、资源处理等的脚本和工具。例如，精灵编辑器、资源编译脚本等。`[进行中]`

---
**注意**:
- `__pycache__/` 目录存在于多个位置，是Python解释器自动生成的字节码缓存，已在 `.gitignore` 中配置忽略，此处不详细列出。
- 标记为 `[待补全]` 的部分需要后续根据开发进度进行详细补充。
- `status/interaction/interaction_manager.py` 文件目前存在较多linter错误，已在 `Thread.md` 和详细日志中记录，需后续修复。