# 变更日志索引

*此文档索引记录了 Status-Ming 项目的重要变更。*

## 核心系统
- [2025-03-25] [核心系统] 基础引擎架构实现 - 详见 [Logs/2025-03-25_core_framework.md]
- [2025-03-26] [核心系统] 事件系统实现 - 详见 [Logs/2025-03-26_event_system.md]
- [2025-03-27] [核心系统] 资源管理系统实现 - 详见 [Logs/2025-03-27_resource_management.md]
- [2025-03-28] [核心系统] 日志系统实现 - 详见 [Logs/2025-03-28_logging_system.md]
- [2025-04-03] [核心系统] 资源管理系统测试增强 - 详见 [Logs/2025-04-03_resource_system_test_enhancement.md]
- [2025-04-01] [核心系统] 事件管理器实现 - 详见 [Logs/2025-04-01_event_manager.md]
- [2025-04-01] [核心系统] 配置管理器实现 - 详见 [Logs/2025-04-01_config_manager.md]
- [2025-04-02] [核心系统] 应用生命周期管理实现 - 详见 [Logs/2025-04-02_lifecycle_manager.md]
- [2025-04-01_core_events.md](Logs/Core/2025-04-01_core_events.md) - 事件系统实现
- [2025-04-01_core_logging.md](Logs/Core/2025-04-01_core_logging.md) - 日志系统实现
- [2025-04-02_core_config.md](Logs/Core/2025-04-02_core_config.md) - 配置系统实现
- [2025-04-02_core_plugin.md](Logs/Core/2025-04-02_core_plugin.md) - 插件系统实现

## 项目规划
- [2025-05-15] [项目规划] 项目开发计划精细化调整 - 详见 [Logs/main/2025-05-15_project_plan_enhancement.md]

## 渲染系统
- [2025-03-29] [渲染系统] 基础渲染器实现 - 详见 [Logs/2025-03-29_renderer_base.md]
- [2025-03-30] [渲染系统] UI渲染实现 - 详见 [Logs/2025-03-30_ui_renderer.md]
- [2025-04-01] [渲染系统] 特效系统实现 - 详见 [Logs/2025-04-01_effects_system.md]
- [2025-04-02] [渲染系统] 粒子系统实现 - 详见 [Logs/2025-04-02_particle_system.md]
- [2025-04-03] [渲染系统] 过渡效果系统实现 - 详见 [Logs/2025-04-03_transition_system.md]
- [2025-04-03] [渲染系统] 场景过渡与过渡效果系统集成 - 详见 [Logs/2025-04-03_scene_transition_integration.md]
- [2025-04-02] [渲染系统] 动画系统基础框架实现 - 详见 [Logs/2025-04-02_animation_system.md]
- [2025-04-16] [渲染系统] 桌宠动画集成与优化 - 详见 [Logs/2025-04-16_idle_animation_integration.md]

## 场景管理
- [2025-03-31] [场景管理] 场景基类实现 - 详见 [Logs/2025-03-31_scene_base.md]
- [2025-04-01] [场景管理] 场景转场动画实现 - 详见 [Logs/2025-04-01_scene_transition.md]
- [2025-04-02] [场景管理] 场景管理器实现 - 详见 [Logs/2025-04-01_scene_manager.md]
- [2025-04-02] [场景管理] 场景加载与切换机制实现 - 详见 [Logs/2025-04-02_scene_loading.md]

## 资源管理
- [2025-03-27] [资源管理] 资源加载器实现 - 详见 [Logs/2025-03-27_resource_loader.md]
- [2025-03-28] [资源管理] 缓存系统实现 - 详见 [Logs/2025-03-28_cache_system.md]
- [2025-03-29] [资源管理] 资源预加载实现 - 详见 [Logs/2025-03-29_resource_preloading.md]
- [2025-04-01] [资源管理] 资源缓存系统实现 - 详见 [Logs/2025-04-01_resource_cache.md]
- [2025-04-01] [资源管理] 资源管理器实现 - 详见 [Logs/2025-04-01_asset_manager.md]
- [2025-04-02] [资源管理] 资源预加载机制实现 - 详见 [Logs/2025-04-02_resource_preloading.md]
- [2025-04-16] [资源管理] 图像加载优化与PyQt集成 - 详见 [Logs/2025-04-16_resource_loading_pyqt.md]
- [2025-05-15] [资源管理] 实现可插拔的宠物状态占位符系统 - 详见 [Logs/pet_assets/2025-05-15_placeholder_system_implementation.md]
  - 设计与实现了单状态单文件的占位符管理架构，提高模块化和可维护性
  - 开发了`PlaceholderFactory`工厂类，使用`importlib`动态加载和提供各状态的占位符动画
  - 使用Qt绘图API程序化生成了高精度(L3/L4)的HAPPY状态占位符动画
  - 实现了统一的`create_animation()`接口，确保所有占位符组件遵循一致的标准
  - 集成到`StatusPet`主流程，支持初始化和动态加载状态占位符
  - 编写了全面的单元测试和集成测试，所有测试用例通过
- [2025-05-15] [资源管理] 为特殊日期/节气创建L4占位符动画 - 详见 [Logs/pet_assets/2025-05-15_special_date_animations.md]
- [2025-05-15] [资源管理] 核心占位符动画L4质量提升 - 详见 [Logs/pet_assets/2025-05-15_core_animations_L4_enhancement.md]
- [2025-05-15] [资源管理] 资源压缩与优化 - 详见 [Logs/resources/2025-05-15_resource_compression_optimization.md]
- [2025-05-15] [资源管理] 资源加载进度监控机制设计 - 详见 [Logs/resources/2025-05-15_resource_loading_progress.md]
- [2025-05-16] [资源管理] 资源缓存优化 (完善ResourceLoader与AssetManager集成) - 详见 [Logs/resources/2025-05-16_cache_optimization.md]

## 交互系统
- [2025-04-03] [交互系统] 交互管理器实现 - 详见 [Logs/2025-04-03_interaction_manager.md]
- [2025-04-03] [交互系统] 鼠标交互模块实现 - 详见 [Logs/2025-04-03_mouse_interaction.md]
- [2025-04-03] [交互系统] 系统托盘图标模块实现 - 详见 [Logs/2025-04-03_tray_icon.md]
- [2025-04-03] [交互系统] 上下文菜单模块实现 - 详见 [Logs/2025-04-03_context_menu.md]
- [2025-04-03] [交互系统] 全局热键管理模块实现 - 详见 [Logs/2025-04-03_hotkey_manager.md]
- [2025-04-03] [交互系统] 行为触发器模块实现 - 详见 [Logs/2025-04-03_behavior_trigger.md]
- [2025-04-03] [交互系统] 窗口拖拽管理模块实现 - 详见 [Logs/2025-04-03_drag_manager.md]
- [2025-04-03_interaction_system.md](Logs/Interaction/2025-04-03_interaction_system.md) - 交互系统实现
- [2025-04-04_event_optimization.md](Logs/Interaction/2025-04-04_event_optimization.md) - 事件过滤与节流机制实现
- [2025-04-05] [交互系统] 交互命令系统实现 - 详见 [Logs/2025-04-05_command_system.md]
- [2025-04-16] [交互系统] 桌宠窗口拖拽与边界检测 - 详见 [Logs/2025-04-16_pet_window_drag.md]

## UI系统
- [2025-04-16] [UI系统] 桌宠主窗口实现 - 详见 [Logs/2025-04-16_main_pet_window.md]

## 工具系统
- [2025-03-30] [工具系统] 性能监视器实现 - 详见 [Logs/2025-03-30_performance_monitor.md]
- [2025-03-31] [工具系统] 内存分析器实现 - 详见 [Logs/2025-03-31_memory_analyzer.md]
- [2025-04-02] [工具系统] 日志系统实现 - 详见 [Logs/2025-04-02_logging_system.md]
- [2025-04-02] [工具系统] 调试工具实现 - 详见 [Logs/2025-04-02_debug_tools.md]

## 图形界面
- [2025-04-01_gui_main_window.md](Logs/GUI/2025-04-01_gui_main_window.md) - 主窗口实现
- [2025-04-02_gui_animation.md](Logs/GUI/2025-04-02_gui_animation.md) - 基础动画系统实现

## 版本记录
- v0.1.0 - 2025-04-01 - 基础框架搭建，包含事件系统和日志系统
- v0.1.1 - 2025-04-02 - 添加配置系统和插件系统
- v0.1.2 - 2025-04-03 - 实现交互系统基础功能
- v0.1.3 - 2025-04-04 - 优化交互系统性能，添加事件过滤与节流机制
- v0.1.4 - 2025-04-05 - 添加系统监控和提醒系统功能
- v0.1.5 - 2025-04-05 - 实现简易笔记、屏幕截图和番茄钟等实用工具功能
- v0.1.6 - 2025-04-05 - 实现交互命令系统，提供统一的命令处理框架
- v0.2.0 - 2025-04-16 - 实现MVP核心功能：可拖动桌宠窗口与Idle动画

## 桌宠系统
- [2025-04-16] [桌宠系统] MVP核心功能实现 - 详见 [Logs/2025-04-16_mvp_core.md]

## 系统监控
- [2025-04-04] [系统监控] 系统监控模块实现 - 详见 [Logs/2025-04-04_system_monitor.md]
- [2025-04-04] [系统监控] 监控系统单元测试 - 详见 [Logs/2025-04-04_monitor_tests.md]

## 提醒系统
- [2025-04-05] [提醒系统] 提醒系统基础实现 - 详见 [Logs/2025-04-05_reminder_system.md]
- [2025-04-05] [提醒系统] 提醒系统单元测试 - 详见 [Logs/2025-04-05_reminder_tests.md]

## 笔记系统
- [2025-04-05] [笔记系统] 简易笔记系统实现 - 详见 [Logs/2025-04-05_notes_system.md]

## 截图工具
- [2025-04-05] [截图工具] 屏幕截图工具实现 - 详见 [Logs/2025-04-05_screenshot_tool.md]

## 番茄钟系统
- [2025-04-05] [番茄钟] 番茄钟系统实现 - 详见 [Logs/2025-04-05_pomodoro_timer.md]

## 命令系统
- [2025-04-05] [命令系统] 交互命令系统实现 - 详见 [Logs/2025-04-05_command_system.md]

## 行为系统
- [2025-05-15 - 状态机与行为系统](Logs/behavior/2025-05-15.md) - 时间驱动的行为模式与系统负载响应行为
- [2025-05-16 - 用户交互功能](Logs/behavior/2025-05-16.md) - 交互区域实现与交互跟踪系统
- [2025-05-19 - 用户交互功能修复](Logs/behavior/2025-05-19.md) - 交互区域与交互跟踪器的测试和修复

## UI组件系统开发日志

### 2025-04-05 基础UI组件库实现
- 创建了遵循Hollow Knight主题风格的UI组件库
- 实现了5大类基础组件：
  - 按钮组件：提供主按钮、次要按钮、文本按钮和图标按钮
  - 输入组件：提供文本输入、搜索框和数字输入
  - 卡片组件：提供标准卡片和可展开卡片
  - 进度指示器：提供进度条和加载指示器
  - 通知组件：提供多种类型的通知和通知管理器
- 所有组件均支持禁用状态和适当的状态反馈
- 组件设计符合暗色主题，以蓝色作为主要强调色
- 创建了完整的组件演示程序，展示各组件的使用方法
- 组件具有良好的容错性，在不支持PyQt的环境中也不会崩溃

### 2025-04-16 桌宠核心功能实现
- 实现了桌宠的无边框、可拖动、透明背景的主窗口
- 集成了帧动画系统，支持流畅播放序列帧动画
- 优化了资源加载系统，从Pygame架构迁移到纯PyQt架构
- 添加了窗口拖拽和屏幕边界检测功能
- 实现了双击关闭应用的功能
- 重构了渲染机制，使用直接的QPixmap和QPainter进行高效绘制
- 建立了明确的动画-窗口更新流程

后续计划:
- 基于基础组件开发功能特定UI
- 应用主题系统，支持主题切换
- 开发桌面宠物动画系统

# 项目日志索引

## 核心系统
- [核心模块日志](Logs/2025-01-15_core_system.md) - 核心系统架构与实现

## 交互系统
- [事件系统日志](Logs/2025-02-10_event_system.md) - 事件驱动架构实现
- [命令系统日志](Logs/2025-04-05_command_system.md) - 命令系统架构与实现

## 功能模块
- [截图工具日志](Logs/2025-03-20_screenshot_tool.md) - 截图工具功能实现

## UI系统
- [组件库日志](Logs/2025-04-05_ui_components.md) - UI组件库实现
- [主题系统日志](Logs/2025-04-05_theme_system.md) - UI主题系统实现

## 2025-04-15

### 新增功能: 快捷启动器

- 实现了快捷启动器模块，包括以下组件:
  - 启动器数据类型定义
  - 启动器管理器
  - 启动器UI界面
  - 示例应用
- 集成到交互系统，支持通过Alt+Space热键唤起
- 为启动器模块编写单元测试

## 2025-04-16

### 新增功能: 修复画布指针偏移，统一所有显示模式下的pixmap绘制逻辑，确保与坐标换算一致

- 实现了修复画布指针偏移的功能，统一所有显示模式下的pixmap绘制逻辑，确保与坐标换算一致
- 相关日志链接: [Logs/2025-04-16_sprite_editor_pointer_offset_fix.md]

## 2025-05-11

### Project Cleanup: Phase 1
- 执行了第一阶段的项目清理，移除了旧主题的 `assets` 中的部分资源 (`assets/sprites/idle/README.md`, `assets/sprites/idle/generate_idle_frames.py`, `assets/Plan.md`) 和 `status/core/` 下的冗余模块 (`asset_manager.py`, `resource_loader.py`, `cache.py`, `scene_manager.py`)。
- **更新 (2025-05-12):** 清理范围已扩展，包括根目录下的多个文件和目录、`assets` 内的空子目录、`status` 内的多个模块（如config, monitor, examples, launcher等）、`status/ui/` 内的部分文件和目录，以及 `tests/` 目录内的大量文件和子目录。同时，对 `status/interaction/interaction_manager.py` 进行了解耦编辑（移除CommandManager引用，但附带linter错误）。
- **注意**: 部分二进制资源文件（如旧主题的 .png）和非空目录的删除仍需手动完成。
- **完整详情参见**: [Logs/2025-04-17_project_cleanup_phase1.md]


---
**重要通知: 项目演进与日志分割**

以上日志主要记录了本项目在早期阶段（可能使用名称如 "Hollow-ming" 或早期 "Status"）的开发历史和演进过程，直至 `2025-05-12` 的大规模项目清理（详情参见 `Logs/2025-04-17_project_cleanup_phase1.md`）。

自 `2025-05-12` 起，项目已正式更名为 **`Status-Ming`**，并确立了新的开发方向：
- **主题**: 猫咪（当前使用占位符）
- **核心技术**: PySide6
- **主要目标**: MVP版本 - 实现核心的桌面宠物系统参数监控反馈功能。

后续 `Status-Ming` 项目的主要开发活动、重要变更和版本发布将通过以下方式记录：
1.  **新的详细日志文件**: 将存放于 `Logs/Status-Ming/` 子目录下（例如 `Logs/Status-Ming/2025-05-15_mvp_pet_window_setup.md`）。
2.  **本 `Log.md` 文件更新**: 将会在此通知下方，创建一个新的二级标题 `## Status-Ming (猫咪主题 - 2025-05-12 起)`，用于索引这些新的详细日志文件，或记录关键的里程碑摘要。

感谢您对项目历史的关注。敬请期待 `Status-Ming` 的新进展！
---

## Status-Ming (猫咪主题 - 2025-05-12 起) 变更日志索引

*(此区域将用于索引 `Status-Ming` 的新日志文件或记录关键更新)*

- [2025-05-13] [UI系统] 使用TDD方法改进拖拽精度 - 详见 [Logs/Status-Ming/2025-05-14_drag_precision_tdd.md]
  - 创建10个专门测试用例验证拖拽精度各方面功能
  - 优化平滑系数计算和更新机制，移除特殊分支处理提高一致性
  - 实现精确模式下的位置"追赶"算法减少视觉延迟
  - 更高频率的位置更新提高跟踪响应性

- [2025-05-13] [UI系统] 优化桌宠拖动体验 - 详见 [Logs/Status-Ming/2025-05-21_drag_experience_improvement.md]
  - 修复精确模式下的严重闪动问题（轻微闪动仍存在）
  - 增强边界限制功能，防止高速拖动时超出屏幕
  - 优化平滑系数，提供更自然的拖动感觉
  - 注：精确模式下仍有待完善，不完全1:1跟随鼠标轨迹

- [2025-05-13] [运行] 解决主程序运行问题
  - 通过 `python -m status.main` 解决 `ModuleNotFoundError`
  - 移除 `main_pet_window.py` 中干扰性的测试代码块
  - 确认主程序可使用代码生成的占位符图像启动

- [2025-05-13] [规划] 开始规划 v2.x 开发阶段

- [2025-05-13] [动画][状态] 实现 MVP 动画与状态联动 (Day 3 完成)
  - 通过代码生成为 IDLE 和 BUSY 状态创建了简单的 2 帧占位符动画
  - 在主应用逻辑中实现了根据状态机状态切换和播放对应动画的功能
  - 手动验证了 IDLE 状态下的动画播放

- [2025-05-14] [UI][监控] StatsPanel迭代2完成 - 详见 [Logs/Status-Ming/2025-05-14_statspanel_iteration2.md]
  - 修复面板和桌宠窗口位置绑定问题，实现自动跟随
  - 优化面板样式，调整背景、字体颜色和展开框
  - 修复主程序定时器更新问题，确保数据正常刷新
  - 添加窗口位置变更事件系统，实现UI组件间位置同步

- [2025-05-15] [监控][功能] 增强系统监控功能 - 详见 [Logs/Status-Ming/2025-05-15_enhanced_monitoring.md]
  - 添加实时磁盘IO监控，显示读写速度
  - 添加实时网络速度监控，分别显示上传和下载速率
  - 集成GPU监控功能，包括负载率、显存使用和温度
  - 优化UI显示效果，根据各指标负载动态调整颜色
  - 改进数据采集逻辑，确保实时性和准确性

- [2025-05-15] [核心][事件系统] 事件系统统一与增强 - 详见 [Logs/core/2025-05-15_event_system_integration.md]
  - 解决EventSystem和EventManager API不一致问题
  - 添加publish/subscribe/unsubscribe兼容方法
  - 增强事件系统调用点的防御性和健壮性
  - 保持API兼容性，避免大规模系统重构
  - 所有相关测试通过，确保功能完整性

- [2025-05-15] [资源管理][功能] 资源压缩与优化机制开发 - 详见 [Logs/resources/2025-05-15_resource_compression_optimization.md]
  - 目标：实现通用资源压缩/解压缩，优化内存和存储，保持API兼容。
  - 技术方案：评估zlib、optipng等，并在ResourceLoader/AssetManager中集成。
  - TDD计划：编写压缩/解压缩、加载、保存及缓存处理的测试用例。

- [2025-05-15] [开发流程] TDD开发模式实施计划 - 详见 [Logs/development/2025-05-15_tdd_implementation_plan.md]
  - 制定测试先行策略，明确测试覆盖率目标(>80%)
  - 设计分层测试结构，区分单元测试、集成测试和系统测试
  - 规划测试自动化流程，包括CI/CD集成方案
  - 建立测试可视化系统，使用Graphviz展示测试覆盖情况
  - 更新开发工作流，确保所有新功能和修复都遵循TDD模式

- [2025-05-15] [阶段规划] 阶段0收尾计划 - 详见 [Logs/development/2025-05-15_phase0_finalization.md]
  - 评估现有模块完成度，确定阶段0剩余工作
  - 统一事件系统，将所有模块迁移到新的EventSystem
  - 优化状态机系统，改进阈值设置与状态转换
  - 增强资源管理系统，完善缓存与加载机制
  - 整合渲染系统，确保与状态和资源系统高效集成

## 2025-05-14

- **[行为系统]** 完善时间行为系统和农历支持功能 (2025-05-14 @Ignorant-lu)
  - 增强农历日期支持，创建 LunarHelper 类实现公历农历转换
  - 扩展 SpecialDate 类，支持不同类型的特殊日期
  - 丰富特殊日期集合，添加更多传统节日和节气
  - 创建 TimeAnimationManager 类管理时间相关动画资源
  - 优化测试框架，解决 QTimer 在测试环境中的限制
  - 详情: [Logs/behavior/2025-05-14_time_behavior_enhance.md]

## 2025-05-26

- **[行为系统]** 修复时间行为系统信号机制和农历支持 (2025-05-26 @Ignorant-lu)
  - 修复TimeBasedBehaviorSystem类中的Qt信号定义和使用
  - 创建专门的TimeSignals类处理信号定义和触发
  - 实现农历日期转换功能，正确使用lunar-python API
  - 增强系统稳定性和错误处理
  - 详情: [Logs/behavior/2025-05-26_time_behavior_fix.md]

# 日志索引

> **注意**: 本文件仅包含日志索引信息，具体日志内容请查看 `Logs/` 目录下的对应文件

## 旧 Status 项目日志
以下是旧版 Status 项目的开发日志，这些日志可能与当前 Status-Ming 项目不完全相关：

- [2025-04-17 项目清理第一阶段](Logs/2025-04-17_project_cleanup_phase1.md)
- [2025-04-10 渲染系统重构](Logs/2025-04-10_renderer_refactoring.md)
- [2025-04-03 资源管理系统实现](Logs/2025-04-03_resource_system_implementation.md)

--------------------

## Status-Ming 项目日志

### 项目初始设置

- [2025-04-16] [项目初始化](Logs/Setup/2025-04-16_initial_setup.md)
- [2025-04-18] [基础架构设计](Logs/Setup/2025-04-18_architecture_design.md)

### 功能开发

- [2025-05-01] [事件系统设计与实现](Logs/Core/2025-05-01_event_system.md)
- [2025-05-05] [系统监控基础实现](Logs/Status-Ming/2025-05-05_system_monitor.md)
- [2025-05-15] [增强系统监控功能](Logs/Status-Ming/2025-05-15_enhanced_monitoring.md)

### 测试与修复

- [2025-05-17] [实现TDD测试框架](Logs/Tests/2025-05-17_tdd_implementation.md)

## 类型系统

- [2025-05-12] [类型提示系统优化](Logs/2025-05-12_type_hints_optimization.md) - 创建通用类型模块并修复主要模块（包括 `resource_pack`, `resource_loader`, `cache`, `config_manager`, `interaction_manager`）的类型提示和Linter问题
- [2025-05-15] [类型提示系统优化 - Renderer模块] 完成 status/renderer/ 目录下所有文件的类型检查与修复 - 详见 [Logs/Status-Ming/2025-05-12_type_hints_renderer.md]
- [2025-05-12] [类型提示系统优化 - Resources模块] 完成 status/resources/ 目录下所有文件的类型检查与修复 - 详见 [Logs/Status-Ming/2025-05-12_type_hints_resources.md]
- [2025-05-20] [类型提示系统优化 - Interaction模块] 完成 status/interaction/ 目录下所有文件的类型检查与修复 - 详见 [Logs/2025-05-20_interaction_typehints.md]
- [2025-05-18] [类型提示系统优化 - Behavior模块] 添加缺失的组件基类和实用工具类，解决导入错误 - 详见 [Logs/Status-Ming/2025-05-18_behavior_dependencies_fix.md]

### 2025-05-18: 组件基类和工具类添加
- [核心] 创建了组件基类 ComponentBase，实现了组件的基本功能和接口 [Logs/Status-Ming/2025-05-18_behavior_dependencies_fix.md]
- [工具] 添加了二维向量类 Vector2D，提供向量数学操作功能 [Logs/Status-Ming/2025-05-18_behavior_dependencies_fix.md]
- [工具] 添加了衰减函数模块，包含指数衰减等多种衰减函数 [Logs/Status-Ming/2025-05-18_behavior_dependencies_fix.md]
- [修复] 解决了behavior模块的依赖导入错误问题 [Logs/Status-Ming/2025-05-18_behavior_dependencies_fix.md]

### 2025-05-15: 监控模块类型提示优化
- [监控] 修复了system_info.py中的Collection[Any]类型索引错误 [Logs/2025-05-15_monitor_typehints.md]
- [监控] 修复了_initialized类型问题 [Logs/2025-05-15_monitor_typehints.md]
- [监控] 纠正了导入语句，使Event类导入正确 [Logs/2025-05-15_monitor_typehints.md]

### 2025-05-12: 资源模块类型提示优化
- [资源] 修复了resource_pack.py, resource_loader.py的类型注解问题 [Logs/2025-05-12_type_hints_optimization.md]
- [资源] 改进了ResourcePackManager的类型提示 [Logs/2025-05-12_type_hints_optimization.md]
- [测试] 修复了资源系统测试中的类型问题 [Logs/2025-05-12_type_hints_optimization.md]

### 2025-05-20: 交互模块类型提示优化
- [交互] 修复了event_filter.py和event_throttler.py中的方法返回类型问题 [Logs/2025-05-20_interaction_typehints.md]
- [交互] 修复了interaction_event.py中的类型处理，优化事件类型系统 [Logs/2025-05-20_interaction_typehints.md]
- [类型] 完成了项目类型提示修复中期进度报告 [Logs/2025-05-20_type_hints_progress.md]

## 变更索引

| 日期 | 文件 | 描述 | 状态 |
|------|------|------|------|
| 2025/05/18 | [行为模块依赖修复](Logs/Status-Ming/2025-05-18_behavior_dependencies_fix.md) | 修复行为模块的核心依赖文件 | 已完成 |
| 2025/05/18 | [行为模块导入修复](Logs/Status-Ming/2025-05-18_behavior_imports_fix.md) | 修复行为模块的导入和类型问题 | 已完成 |

## UI相关
- [2025-05-20 UI拖动性能优化](logs/2025-05-20_ui_optimization.md) - 解决拖动问题，优化UI响应性能
- [2025-05-10] [主窗口实现](Logs/UI/2025-05-10_main_window.md)
- [2025-05-13] [系统托盘实现](Logs/UI/2025-05-13_system_tray.md)
- [2025-05-13] [拖动功能改进](Logs/UI/2025-05-13_drag_improvements.md)
- [2025-05-13] [统计面板实现](Logs/UI/2025-05-13_stats_panel.md)
- [2025-05-17] [StatsPanel显示问题修复与TDD测试实现](Logs/Status-Ming/2025-05-17_statsPanel_display_fix.md)

## 系统托盘
- [2025-05-13 系统托盘功能实现](logs/2025-05-13_system_tray.md) - 添加系统托盘功能

## 类型注解
- [2025-05-20 类型提示进度](logs/2025-05-20_type_hints_progress.md) - 添加类型提示改进代码质量
- [2025-05-20 交互系统类型提示](logs/2025-05-20_interaction_typehints.md) - 为交互系统添加类型提示
- [2025-05-15 监控系统类型提示](logs/2025-05-15_monitor_typehints.md) - 为监控系统添加类型提示
- [2025-05-15 类型提示监控](logs/2025-05-15_type_hints_monitoring.md) - 类型提示实施进度监控
- [2025-05-12 类型提示优化](logs/2025-05-12_type_hints_optimization.md) - 优化类型提示

## 新功能

## 2025年5月

### 2025-05-13
- [拖动功能修复](Logs/Status-Ming/2025-05-13_drag_fix.md) - 修复拖动功能有时不响应的问题
- [开发路线图](docs/development_roadmap.md) - 创建详细的后续开发三阶段规划，包括用户体验优化、功能模块扩展和架构优化

### 2025-05-13
- [系统监控增强](Logs/Status-Ming/2025-05-13_enhanced_monitoring.md) - 添加磁盘I/O、网络速度和GPU监控功能
- [系统进阶开发计划](docs/system_advancement_plan.md) - 添加详细的系统进阶开发计划，包括监控增强、行为丰富、配置系统和架构优化

### 2025-05-13
- [MVP初始版本](Logs/Status-Ming/2025-05-13_mvp_initial.md) - 实现基础窗口、系统托盘、CPU/内存监控和状态机

### 核心系统
- [2025-05-10 - 事件系统修复](Logs/core/2025-05-10.md) - 事件系统BUG修复

### 监控系统
- [2025-05-12 - 系统监控实现](Logs/monitoring/2025-05-12.md) - 资源使用监控实现

## 变更日志

### 2025-05-25 - 时间驱动行为系统实现
- 查看详情：[Logs/behavior/2025-05-25_time_behavior.md](Logs/behavior/2025-05-25_time_behavior.md)
- 描述：实现了基于时间的行为系统，使桌宠能根据一天中的不同时段和特殊日期展示不同行为

### 2025-05-25 - 交互系统与状态机集成
- 查看详情：[Logs/interaction/2025-05-25.md](Logs/interaction/2025-05-25.md)
- 描述：实现了交互状态适配器与状态机的集成，完成了交互系统与状态机的连接

### 2025-05-26 - 时间行为系统信号处理修复
- 查看详情：[Logs/behavior/2025-05-26_time_behavior_fix.md](Logs/behavior/2025-05-26_time_behavior_fix.md)
- 描述：修复了时间行为系统的PySide6信号实现问题，创建TimeSignals类并更新相关连接代码

## 2025-05-26

- **[行为系统]** 修复时间行为系统信号机制和农历支持 (2025-05-26 @Ignorant-lu)
  - 修复TimeBasedBehaviorSystem类中的Qt信号定义和使用
  - 创建专门的TimeSignals类处理信号定义和触发
  - 实现农历日期转换功能，正确使用lunar-python API
  - 增强系统稳定性和错误处理
  - 详情: [Logs/behavior/2025-05-26_time_behavior_fix.md]

### 核心架构
- [2025-05-26] [架构文档] 插件系统和事件系统文档更新 - 详见 [Logs/2025-05-26_architecture_document_update.md]

## 2025-05-14 状态机与UI组件优化

### 状态机改进
- 修复了`_recalculate_active_state`方法中的冗余判断，提高了执行效率
- 优化了状态优先级处理逻辑，确保特殊日期状态正确处理
- 改进了状态事件发布系统，增加了错误处理和更详细的日志记录
- 实现了状态历史记录功能，支持状态变化的追踪和调试
- 创建了详细的状态机文档，记录了状态优先级和使用方法
- 添加了状态机单元测试，提高了代码质量和可维护性

### UI组件优化
- 优化了StatsPanel性能，减少了不必要的重绘和更新
- 改进了多显示器支持，修复了跨显示器拖拽时的位置计算问题
- 将详细信息更新逻辑分离出来，精简了主更新方法
- 增强了UI组件的稳定性和响应速度

### 资源管理系统完善
- 使用LRUCache实现了智能缓存管理
- 添加了自动清理过旧资源的功能
- 改进了图像加载机制，确保保留透明度
- 优化了资源加载性能，减少内存使用
- 添加了缓存统计功能，便于调试和监控

## 2025-05-13 项目初始化

### 核心组件
- 初始化项目结构，建立基础架构
- 实现基本的状态机系统
- 创建UI组件框架
- 设计并实现资源管理系统

- [2025-05-15] [资源管理] 规划可插拔的宠物状态占位符系统 - 详见 [docs/placeholder_implementation_plan.md]
  - 设计单状态单文件的占位符管理架构，提高模块化和可维护性
  - 规划`PlaceholderFactory`工厂类，负责动态加载和提供各状态的占位符动画
  - 使用Python的`importlib`动态导入相应的占位符模块
  - 设计使用Qt绘图API程序化生成高精度占位符动画，目标达到L3/L4级精致度
  - 为未来资源扩展(本地缓存、云端资源下载)预留架构空间
  - 更新设计文档、线程文档和项目结构文档

- [2025-05-15] [Fix] 解决main.py运行时错误及相关组件初始化问题 - 详见 [Logs/runtime_errors/2025-05-15_main_runtime_error_fixes.md]
- [2025-05-15] [核心模块] 重构 `main.py` 中的动画创建逻辑，迁移至 `PlaceholderFactory` 和各状态占位符模块 - 详见 [Logs/main/2025-05-15_main_animation_logic_refactor.md]
- [2025-05-15] [资源管理] 核心占位符动画L4质量提升 - 详见 [Logs/pet_assets/2025-05-15_core_animations_L4_enhancement.md]
- [2025-05-15] [资源管理] 为特殊日期/节气创建L4占位符动画 - 详见 [Logs/pet_assets/2025-05-15_special_date_animations.md]
- [2025-05-15] [资源管理] 实现可插拔的宠物状态占位符系统 - 详见 [Logs/pet_assets/2025-05-15_placeholder_system_implementation.md]
- [2025-05-15] [行为系统] 完善桌宠行为丰富功能 - 详见 [Logs/behavior/2025-05-15.md]
- [2025-05-15] [监控][功能] 增强系统监控功能 - 详见 [Logs/Status-Ming/2025-05-15_enhanced_monitoring.md]

## pet_assets 模块日志
- [2025-05-15] TDD实现PlaceholderFactory缓存机制 - [查看详情](./Logs/pet_assets/2025-05-15_cache_mechanism_implementation.md)
- [2025-05-15] TDD实现PlaceholderFactory缓存统计功能 - [查看详情](./Logs/pet_assets/2025-05-15_cache_stats_implementation.md)

## resources 模块日志
- [2025-05-15] TDD实现资源包热加载功能 - [查看详情](./Logs/resources/2025-05-15_resource_hot_loading_implementation.md)


