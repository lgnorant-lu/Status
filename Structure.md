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
│   │   ├── __init__.py
│   │   ├── basic_behaviors.py # 基础行为定义及行为基类 [进行中]
│   │   ├── behavior_manager.py # 行为管理器 [进行中]
│   │   ├── decision_maker.py # 决策系统 [进行中]
│   │   ├── emotion_system.py # 情绪系统 [进行中]
│   │   ├── environment_sensor.py # 环境感知器 [进行中]
│   │   ├── interaction_state_adapter.py # 交互状态适配器 [进行中]
│   │   ├── interaction_tracker.py # 用户交互追踪器 (与behavior紧密相关) [进行中]
│   │   ├── pet_state.py # 宠物状态定义枚举 [进行中]
│   │   ├── pet_state_machine.py # 宠物状态机 [进行中]
│   │   ├── reaction_system.py # 反应系统 [进行中]
│   │   ├── system_state_adapter.py # 系统状态适配器 [进行中]
│   │   ├── time_based_behavior.py # 时间驱动行为及农历助手 [进行中]
│   │   ├── time_state_adapter.py # 时间状态适配器 [待移除 - 功能将整合到 TimeStateBridge]
│   │   └── time_state_bridge.py # 时间状态桥接器 [进行中]
│   ├── components/             # 可复用的应用组件 (例如 SystemStateAdapter, InteractionHandler) [进行中]
│   │   ├── __init__.py
│   │   ├── system_state_adapter.py # 系统状态适配器 [进行中]
│   │   ├── interaction_handler.py  # 用户交互处理器 [进行中]
│   │   ├── interaction_tracker.py  # 用户交互追踪器 [进行中]
│   │   └── time_based_behavior_system.py # 时间行为系统组件 [进行中]
│   ├── core/                   # 核心基础模块 (事件、配置、组件基类等) [进行中]
│   │   ├── __init__.py         # 包初始化文件
│   │   ├── component_base.py   # 应用组件基类，定义了组件生命周期和激活机制 [已完成]
│   │   ├── event_system.py     # 旧版事件系统 [已完成]
│   │   ├── types.py            # 核心类型定义 [已完成]
│   │   ├── errors.py           # 核心错误和异常定义 [新创建]
│   │   ├── logging/            # 增强日志系统 [已完成]
│   │   │   ├── __init__.py     # 包初始化文件
│   │   │   └── log_manager.py  # 日志管理器实现 [已完成]
│   │   └── recovery/           # 错误恢复机制 [已完成]
│   │       ├── __init__.py     # 包初始化文件
│   │       ├── state_manager.py    # 状态管理器实现 [已完成]
│   │       ├── recovery_manager.py # 恢复管理器实现 [已完成]
│   │       └── exception_handler.py # 异常处理器实现 [已完成]
│   ├── events/                 # 增强事件系统 [核心模块] [已完成]
│   │   ├── __init__.py         # 包初始化文件
│   │   ├── event_manager.py    # 事件管理器实现，包含优先级、过滤和节流功能 [已完成]
│   │   └── event_types.py      # 事件类型定义 [已完成]
│   │                           # - 新增: ResourceLoadingBatchStartEvent
│   │                           # - 新增: ResourceLoadingProgressEvent
│   │                           # - 新增: ResourceLoadingBatchCompleteEvent
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
│   ├── main.py                 # 应用主入口, 依赖PlaceholderFactory加载动画, 负责组件初始化和主循环 [核心模块] [进行中]
│   ├── monitoring/             # 系统监控模块 [计划中]
│   │   └── ... [待补全]
│   ├── pet_assets/             # 宠物资源管理模块 [已完成]
│   │   ├── __init__.py         # 包初始化文件 [已完成]
│   │   ├── placeholder_factory.py # 占位符工厂，负责动态加载状态占位符 [已完成]
│   │   └── placeholders/       # 各状态的占位符实现目录 [已完成]
│   │       ├── __init__.py     # 包初始化文件 [已完成]
│   │       ├── happy_placeholder.py # "开心"状态占位符实现 [已完成]
│   │       ├── idle_placeholder.py # "空闲"状态占位符实现 (L4 质量) [已完成]
│   │       ├── busy_placeholder.py # "忙碌"状态占位符实现 (L4 质量) [已完成]
│   │       ├── memory_warning_placeholder.py # "内存警告"状态占位符实现 [已完成]
│   │       ├── system_error_placeholder.py # "系统错误"状态占位符实现 (原 error_placeholder.py) [已完成]
│   │       ├── clicked_placeholder.py # "点击"状态占位符实现 (L4 质量) [已完成]
│   │       ├── dragged_placeholder.py # "拖拽"状态占位符实现 [已完成]
│   │       ├── petted_placeholder.py # "抚摸"状态占位符实现 [已完成]
│   │       ├── hover_placeholder.py # "悬停"状态占位符实现 [已完成]
│   │       ├── morning_placeholder.py # "早晨"状态占位符实现 (L4 质量) [已完成]
│   │       ├── noon_placeholder.py # "中午"状态占位符实现 [已完成]
│   │       ├── afternoon_placeholder.py # "下午"状态占位符实现 [已完成]
│   │       ├── evening_placeholder.py # "傍晚"状态占位符实现 [已完成]
│   │       ├── night_placeholder.py # "夜晚"状态占位符实现 (L4 质量) [已完成]
│   │       ├── spring_festival_placeholder.py # "春节"L4占位符实现 [已完成]
│   │       ├── lichun_placeholder.py # "立春"L4占位符实现 [已完成]
│   │       ├── moderate_load_placeholder.py # "中等负载"状态占位符实现 [已完成]
│   │       ├── low_battery_placeholder.py # "低电量"状态占位符实现 [已完成]
│   │       ├── charging_placeholder.py # "充电中"状态占位符实现 [已完成]
│   │       ├── fully_charged_placeholder.py # "已充满"状态占位符实现 [已完成]
│   │       ├── system_update_placeholder.py # "系统更新"状态占位符实现 [已完成]
│   │       └── sleep_placeholder.py # "睡眠"状态占位符实现 [已完成]
│   ├── plugin/                 # 插件系统模块 [核心模块] [已完成]
│   │   ├── __init__.py         # 包初始化文件
│   │   ├── plugin_base.py      # 插件基类定义 [已完成]
│   │   ├── plugin_manager.py   # 插件管理器实现 [已完成]
│   │   └── plugin_registry.py  # 插件注册表实现 [已完成]
│   ├── renderer/               # 基于PySide6的渲染逻辑 (猫咪占位符动画、未来UI元素等)。 [进行中]
│   │   └── ... [待补全]
│   ├── resources/              # 运行时资源管理 [进行中]
│   │   └── ... [待补全]
│   │   # - AssetManager.py (或类似模块) 将包含 load_assets_batch 方法
│   ├── scenes/                 # 场景管理 [进行中]
│   │   └── ... [待补全]
│   ├── ui/                     # 基于PySide6的用户界面元素和逻辑 (如设置面板、信息面板、系统托盘)。 [进行中]
│   │   ├── __init__.py
│   │   ├── system_tray.py      # 系统托盘图标及菜单逻辑 [进行中]
│   │   └── ... [待补全]
│   └── utils/                  # 通用工具函数 [进行中]
│       └── ... [待补全]
├── tests/                      # 测试代码 [测试模块] [进行中]
│   ├── __init__.py             # 包初始化文件
│   ├── conftest.py             # Pytest配置文件和fixtures [配置模块] [进行中]
│   │   ├── 包含标准测试夹具，支持模块化测试环境
│   │   ├── 集成pytest-cov配置，用于生成测试覆盖率报告
│   │   ├── 提供Qt/PySide6测试环境支持
│   │   └── 支持模拟和存根对象创建
│   ├── events/                 # 事件系统测试 [已完成]
│   ├── mocks.py                # Mock对象定义 [待补全]
│   ├── pet_assets/             # 宠物资源管理模块测试 [已完成]
│   ├── plugin/                 # 插件系统测试 [已完成]
│   ├── run_tests.py            # 测试运行脚本 [工具模块] [进行中]
│   │   ├── 支持运行单元、集成和系统测试
│   │   ├── 提供测试覆盖率报告生成
│   │   ├── 集成测试结果可视化
│   │   └── 支持并行测试执行
│   ├── behavior/               # 行为模块测试 [待补全]
│   ├── core/                   # 核心模块测试 [待补全]
│   ├── interaction/            # 交互模块测试 [待补全]
│   ├── integration/            # 集成测试 [进行中]
│   │   ├── 测试多个组件的协同工作
│   │   ├── 验证跨模块功能和数据流
│   │   └── 模拟真实使用场景
│   ├── mocks/                  # 模拟对象目录 [进行中]
│   │   ├── 提供标准化的模拟对象
│   │   ├── 支持复杂场景模拟
│   │   └── 包含测试数据生成器
│   ├── monitoring/             # 监控模块测试 [待补全]
│   ├── renderer/               # 渲染模块测试 [进行中]
│   ├── resources/              # 资源模块测试 [待补全]
│   ├── scenes/                 # 场景模块测试 [进行中]
│   ├── system/                 # 系统测试 [计划中]
│   │   ├── 端到端测试流程
│   │   ├── 用户场景测试
│   │   └── 性能基准测试
│   ├── unit/                   # 单元测试 [进行中]
│   │   ├── 按模块组织的独立单元测试
│   │   ├── 使用标准命名规范：test_{被测函数}_{测试场景}_{预期结果}
│   │   └── 遵循TDD开发模式
│   └── utils/                  # 测试工具 [计划中]
│       ├── 测试辅助函数
│       ├── 测试数据生成器
│       └── 自定义断言函数
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
    - `behavior/`: 管理和实现桌宠（猫咪占位符）的各种行为状态和逻辑，响应系统参数。包含时间驱动行为及农历日期处理 (`time_based_behavior.py`)。`[进行中]`
    - `components/`: 包含可复用的应用组件，如系统状态适配器 (`SystemStateAdapter`)、用户交互处理器 (`