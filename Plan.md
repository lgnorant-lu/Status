# Status-Ming 项目开发计划

这个计划将首先专注于把现有代码库中所有"半成品"或"初步实现"的模块提升到稳定、可用且经过基本测试的状态，确保它们之间的集成是正确的。然后，我们会列出您构想的后续阶段（阶段1、2、3）的核心任务，作为未来的发展蓝图。

**总纲：以打造一个稳定、可扩展、可定制的2D桌面宠物平台为长期目标，阶段性推进。当前首要任务是巩固现有基础 (阶段0)。**

---

## **阶段 0: 核心功能完善与稳定化 (当前立即执行)**

**目标：** 将现有代码库中的所有核心模块和功能点（包括那些在`Structure.md`中标记为`[计划中]`或`[待补全]`但已有部分实现的模块）进行全面审查、完善、集成和基础测试，确保应用核心功能的稳定运行和代码质量。

**核心原则：**
*   **稳定优先**：解决已知和潜在的bug，确保不崩溃。
*   **集成正确**：确保模块间依赖关系清晰，数据流正确。
*   **接口明确**：为模块定义清晰的API，方便后续扩展和维护。
*   **文档同步**：更新`Structure.md`, `Design.md`, `Log.md`, `Thread.md`以反映实际情况。
*   **基础测试**：为核心功能补充必要的单元测试和集成测试。

**详细任务清单 (基于我们的审查结果):**

**I. 核心架构与应用管理 (`status/core/`, `status/main.py`)**

1.  **`status/core/app.py` (Application 类)**:
    *   **任务**: 审阅其现有实现，并与 `status/main.py` 中的 `StatusPet` 类的职责进行对比。
    *   **决策**:
        *   **选项1 (推荐)**: 如果 `StatusPet` 已承担主要应用管理职责且运行良好，考虑将 `Application` 类中通用的、非UI耦合的功能（如更健壮的配置加载、通用的模块注册机制）提取为独立工具或服务供 `StatusPet` 使用，然后逐步废弃或简化 `Application` 类本身，以避免功能重叠和混淆。
        *   **选项2**: 如果认为 `Application` 的顶层抽象有必要，则明确其与 `StatusPet` 的职责划分（例如，`Application` 处理后台服务和生命周期，`StatusPet` 专注于UI和用户交互的协调），并完成其模块初始化、主循环（如果适用）等占位逻辑。
    *   **产出**: 清晰的应用顶层管理结构，移除冗余。

2.  **`status/core/config/` (配置管理系统)**:
    *   **任务**: 详细审阅 `config_manager.py` 和 `config_types.py`。
    *   **完善**:
        *   确保配置可以从外部文件（如 `config.ini` 或 `config.json`）加载，而不是硬编码。
        *   提供配置项的默认值和类型校验。
        *   确保应用各模块能方便、安全地读取配置。
        *   集成到 `StatusPet` (或调整后的 `Application` 类) 的初始化流程中。
    *   **测试**: 单元测试配置加载、读取、设置和默认值处理。
    *   **产出**: 稳定可靠的配置管理系统。

3.  **`status/core/recovery/` (恢复与异常处理)**:
    *   **任务**: 详细审阅 `recovery_manager.py`, `exception_handler.py`, `state_manager.py`。
    *   **完善**:
        *   确保全局异常处理器能捕获未处理的异常，并记录详细错误信息（到日志文件）。
        *   实现基本的应用状态保存与恢复机制（例如，窗口位置、关键用户设置），以应对意外退出。
        *   `state_manager.py` 的具体功能和集成点需要明确。
    *   **测试**: 测试异常捕获；模拟应用崩溃，验证状态恢复的有效性。
    *   **产出**: 增强应用鲁棒性的恢复和异常处理机制。

4.  **`status/core/event_system.py` 与 `status/core/events.py` (事件系统)**:
    *   **任务**: 确认项目中事件系统的统一性。目前 `StatsPanel` 等模块仍在使用旧的 `EventManager`。
    *   **完善**:
        *   **推荐**: 将所有模块统一到较新的 `status/core/event_system.py:EventSystem`。
        *   迁移现有使用旧 `EventManager` 的代码。
        *   确保事件定义清晰，事件发布和处理流程正确。
    *   **测试**: 测试核心事件的发布和订阅。
    *   **产出**: 统一、高效的事件系统。

5.  **`status/main.py (StatusPet 类)`**:
    *   **任务**: 作为当前的应用主控类，审阅其初始化流程、组件管理、主更新循环。
    *   **完善**:
        *   确保所有核心组件 (`PetStateMachine`, `RendererManager`, `InteractionHandler`, `TimeBasedBehaviorSystem`, `SystemTrayManager`, `StatsPanel` 等) 被正确实例化、依赖注入和激活（遵循正确的顺序）。
        *   `update()` 方法逻辑清晰，性能合理。
        *   与 `RendererManager` 和 `MainPetWindow` 的图像更新流程清晰。
    *   **产出**: 结构清晰、运行稳定的应用主控制器。

**II. 核心功能模块 (`status/behavior/`, `status/monitoring/`, `status/interaction/`, `status/renderer/`, `status/ui/`, `status/pet_assets/`)**

6.  **`status/monitoring/` (系统监控)**:
    *   **任务**: 审阅 `system_monitor.py` 及辅助文件 (`system_info.py`, `monitor.py`, `data_process.py`, `ui_controller.py`)。
    *   **完善**:
        *   解耦 `system_monitor.py` 中与 `TimeBasedBehaviorSystem` 重复的时间逻辑（如特殊日期获取），应从后者获取。
        *   明确 `ui_controller.py` 在此目录的作用，如果与监控核心数据无关，考虑移动。
        *   确保GPU信息获取稳定（如果GPUtil可用）或有明确的回退。
        *   确认 `publish_stats` 被 `StatusPet` 以合适的频率调用。
    *   **测试**: 单元测试各指标获取函数 (可mock `psutil`)；测试 `publish_stats`。
    *   **产出**: 准确、高效的系统监控数据源。

7.  **`status/behavior/system_state_adapter.py`**:
    *   **任务**: 我们已审阅，主要任务是改进阈值设置方式。
    *   **完善**: 在 `PetStateMachine` 中添加公共方法设置阈值，`SystemStateAdapter` 调用这些方法。
    *   **产出**: 更健壮的系统状态到宠物状态机的适配。

8.  **`status/behavior/pet_state_machine.py`**:
    *   **任务**: 我们已审阅，核心逻辑是状态决策。
    *   **完善**:
        *   如上一条，添加设置阈值的公共方法。
        *   确保所有状态转换逻辑清晰、无冲突。
        *   确保能正确处理从各适配器（System, Interaction, Time）传入的数据。
        *   对各个 `STATE_CATEGORIES` 的状态权重和选择逻辑进行梳理。
    *   **测试**: 针对不同的输入组合，测试状态机的状态转换是否符合预期。
    *   **产出**: 稳定、正确的宠物状态决策核心。

9.  **`status/behavior/time_based_behavior.py` 与 `status/behavior/time_state_bridge.py`**:
    *   **任务**: `time_based_behavior.py` 已审阅，包含大量时间逻辑。`time_state_bridge.py` 的作用是将时间信息桥接到状态机。
    *   **完善**:
        *   确保 `TimeBasedBehaviorSystem` 是时间相关信息（时间段、特殊日期）的唯一权威来源。
        *   `TimeStateBridge` 正确监听 `TimeBasedBehaviorSystem` 发布的事件或调用其接口，并将规范化的时间状态输入到 `PetStateMachine`。
        *   梳理 `LunarHelper` 和 `SolarTermHelper` 的使用，确保准确性。
    *   **测试**: 测试时间段判断、特殊日期计算；测试 `TimeStateBridge` 的桥接逻辑。
    *   **产出**: 可靠的时间行为驱动。

10. **`status/behavior/interaction_state_adapter.py`**:
    *   **任务**: 已审阅，连接 `InteractionManager` 和 `PetStateMachine`。
    *   **完善**: 确保从 `InteractionManager` 获取的交互数据能正确转换为对 `PetStateMachine` 的输入。
    *   **产出**: 有效的用户交互到状态的转换。

11. **`status/interaction/` (交互系统)**:
    *   **任务**: 已审阅 `interaction_manager.py`, `interaction_handler.py`, `interaction_tracker.py`, `behavior_trigger.py`。
    *   **完善**:
        *   `InteractionHandler` 与 `MainPetWindow` 的事件（点击、拖拽等）连接正确。
        *   `InteractionTracker` 对交互区域和类型的统计准确。
        *   `InteractionManager` 能基于追踪数据和配置触发相应的交互事件或状态。
        *   `BehaviorTrigger` 系统 (包括各种Trigger子类) 的逻辑清晰，与 `InteractionManager` 或 `BehaviorManager` 集成正确。
    *   **测试**: 测试鼠标事件是否能触发预期的交互处理和状态变化；测试触发器逻辑。
    *   **产出**: 响应准确、定义清晰的用户交互系统。

12. **`status/behavior/behavior_manager.py` 与 `status/behavior/basic_behaviors.py`**:
    *   **任务**: 已审阅。`BehaviorManager` 调度行为，`basic_behaviors.py` 定义行为。
    *   **完善**:
        *   `BehaviorManager` 能够根据当前宠物状态和可用行为列表，选择并执行合适的行为。
        *   行为的 `can_execute` 和 `execute` 逻辑正确。
        *   行为的优先级、互斥等调度逻辑清晰。
        *   确保 `ActionType` (如 `LOOK_AROUND`, `SPEAK`) 有对应的动画或表现。
    *   **测试**: 测试不同状态下行为的选择和执行。
    *   **产出**: 结构化的宠物行为执行框架。

13. **`status/behavior/environment_sensor.py`**:
    *   **任务**: 已审阅，感知桌面环境。
    *   **完善**:
        *   确保窗口检测、屏幕边缘检测、鼠标位置跟踪等功能稳定可靠。
        *   `find_interactive_regions` 和 `get_window_under_cursor` 等核心方法功能正确。
        *   与 `BehaviorManager` 或其他需要环境信息的模块集成。
        *   其发布的事件 (`DESKTOP_OBJECT_DETECTED` 等) 被正确处理。
    *   **测试**: 模拟不同的桌面环境（窗口、鼠标位置），测试其感知结果。
    *   **产出**: 可靠的桌面环境感知能力。

14. **`status/renderer/` (渲染系统)**:
    *   **任务**: 已审阅 `renderer_manager.py`, `pyside_renderer.py`, `renderer_base.py`。
    *   **完善**:
        *   确认 `RendererManager` 被正确初始化，并注册了 `PySideRenderer`。
        *   确认 `MainPetWindow` 通过 `PySideRenderer` (或其 `get_pixmap()`) 显示图像的流程是：动画系统/占位符工厂使用 `PySideRenderer` 绘制一帧到其内部的 `QPixmap` -> `PySideRenderer` 通知 `MainPetWindow` 更新 (通过 `widget.update()`) -> `MainPetWindow` 在 `paintEvent` (如果覆盖) 或通过 `QLabel` 显示这个 `QPixmap`。**如果 `MainPetWindow` 目前不直接在其 `paintEvent` 中绘制渲染器的 `QPixmap`，需要评估是否需要修改为这种更直接的控制方式，尤其是为了未来的分层渲染和特效。**
        *   初步审阅 `status/renderer/animation.py` (720行), `sprite.py` (647行), `drawable.py` (494行)，确保它们与 `RendererBase` 接口协同工作，用于实际的动画帧渲染。
        *   考虑 `RenderLayer` 枚举的实际应用。如果计划分层渲染，应在 `PySideRenderer` 或更高层级的动画/场景管理中实现绘制对象的排序和分层绘制逻辑。
    *   **测试**: (较难单元测试) 集成测试：验证简单的绘制指令（画线、画矩形、加载并绘制图像）能否正确显示。
    *   **产出**: 稳定、可用的2D渲染管线。

15. **`status/ui/` (用户界面)**:
    *   **任务**: 已审阅 `main_pet_window.py`, `system_tray.py`, `stats_panel.py`。
    *   **完善**:
        *   `StatsPanel`: 将事件处理从旧的 `EventManager` 迁移到新的 `EventSystem`。确保其自动定位逻辑在各种屏幕和主窗口状态下都正确。
        *   `SystemTrayManager`: 确保图标路径处理在不同环境下都稳健。
        *   `MainPetWindow`: 拖拽逻辑、边界约束的健壮性。确认与 `InteractionHandler` 的信号连接。
    *   **测试**: 测试窗口交互；测试托盘菜单功能；测试统计面板数据显示和定位。
    *   **产出**: 用户体验良好的核心UI组件。

16. **`status/pet_assets/` (宠物资源与占位符)**:
    *   **任务**: `PlaceholderFactory` 和各种占位符动画是我们之前工作的重点。
    *   **完善**:
        *   确保所有L4质量的占位符动画和测试都已稳定。
        *   确保 `PlaceholderFactory` 能根据状态正确加载和返回对应的占位符动画实例。
        *   日志清晰，错误处理得当。
    *   **产出**: 高质量的默认占位符内容。

**III. 尚未详细审阅但已存在部分实现的模块**

17. **`status/scenes/` (场景系统)**:
    *   **任务**: 快速审阅 `scene_manager.py`, `scene_base.py`, `scene_transition.py` 的核心功能和API。
    *   **完善**: 明确场景系统的当前能力和用途。如果计划在早期阶段使用（例如，简单的背景切换），则确保其基础功能可用。如果属于远期规划，则暂时保持现状，记录其功能。
    *   **产出**: 对场景系统当前状态的评估，以及是否纳入阶段0积极完善的决定。

18. **`status/resources/` (资源管理系统)**:
    *   **任务**: 快速审阅 `asset_manager.py`, `resource_loader.py`, `resource_pack.py`, `cache.py` 的核心功能。
    *   **完善**: 这是一个复杂系统。阶段0的目标是确保它能为当前核心功能（主要是加载占位符动画所需的图像）提供稳定服务。理解其资源包格式、加载流程和缓存机制。
    *   **产出**: 对资源管理系统当前状态的评估，确保其能支持阶段0的需求。

19. **`status/utils/` (工具类)**:
    *   **任务**: 已审阅 `vector.py`, `decay.py`。
    *   **完善**: 确保这些工具类被需要它们的模块正确使用。
    *   **产出**: 可靠的通用工具。

**IV. 文档与测试**

20. **项目文档 (`Structure.md`, `Design.md`, `Thread.md`, `Log.md`)**:
    *   **任务**: 在阶段0完成上述所有模块的审查和初步完善后，全面更新这些核心项目文档，确保它们准确反映项目的最新结构、设计决策、任务进展和变更历史。
    *   **产出**: 最新、最准确的项目文档。

21. **单元测试与集成测试 (`tests/`)**:
    *   **任务**: 结合各模块的完善过程，为其核心功能补充或编写单元测试和必要的集成测试。
    *   **目标**: 提升代码库的整体测试覆盖率，确保核心功能的稳定性。优先覆盖那些逻辑复杂、容易出错或处于关键路径的模块。
    *   **产出**: 更健壮的测试套件。

---

**实施清单 (阶段0 - 高层步骤):**

1.  **模块审阅与初步完善 (按上述I, II, III分类进行)**:
    1.  针对每个子任务，详细阅读相关代码，理解其当前实现。
    2.  识别问题点、不一致性、未完成的逻辑、与设计文档的偏差。
    3.  进行必要的代码修改以修复问题、完善功能、确保集成正确。
    4.  为关键部分添加或改进日志记录。
    5.  *在修改过程中，如果发现某个模块的完善工作量巨大，远超"初步完善"的范畴，则将其标记出来，作为阶段0完成后需要进一步投入的重点，或者根据其对核心稳定性的影响程度决定是否在阶段0内解决。*
2.  **事件系统统一**: 将所有使用旧 `EventManager` 的代码迁移到新的 `EventSystem`。
3.  **核心集成测试**: 对几个关键的用户场景进行端到端测试（例如：启动应用 -> 系统监控数据变化 -> 状态机改变状态 -> 占位符动画切换 -> 用户拖动窗口 -> 统计面板更新）。
4.  **文档更新**: 全面更新 `Structure.md`, `Design.md`, `Log.md`, `Thread.md`。
5.  **测试补充**: 根据完善情况，有针对性地补充单元测试和集成测试。
6.  **代码提交**: 定期提交阶段0的进展，保持版本控制清晰。

---

## **详细的未来阶段计划**

---

**细化阶段 1、2、3 的核心任务：**

**阶段 1: "个性化萌芽" - 强化核心定制与用户体验 (近期目标, 1-3个月)**

*   **核心任务 1.1: 动态主题系统 MVP**
    *   **目标**: 用户可以下载/加载简单的主题包，改变应用的基础外观。
    *   **子任务与实现**:
        1.  **`ThemeManager` 设计与实现 (`status/themes/theme_manager.py`)**:
            *   API: `load_theme(theme_name: str)`, `apply_theme(theme_name: str)`, `get_current_theme() -> Optional[Theme]`, `list_available_themes() -> List[ThemeInfo]`.
            *   逻辑: 扫描指定的主题目录 (e.g., `PROJECT_ROOT/themes/` 或用户配置的目录)，解析主题包 `manifest.json`。
            *   当应用主题时，读取QSS文件内容，并通知相关UI组件刷新样式。
        2.  **主题包结构 v1 (`themes/<theme_name>/`)**:
            *   `manifest.json`: 包含 `name`, `author`, `version`, `description`, `preview_image_path` (可选, 相对于主题包根目录), `qss_file` (指向主题的QSS文件), `icon_map` (可选, 定义需要替换的核心图标及其路径, e.g., `{"tray_icon": "icons/tray.png"}`).
            *   `*.qss`: 主题的QSS样式文件。
            *   `icons/` (可选): 主题相关的图标文件。
            *   `backgrounds/` (可选): 主题相关的背景图片。
        3.  **UI组件集成**:
            *   `MainPetWindow`, `SystemTrayManager` (菜单样式), `StatsPanel`, 以及未来可能的 `SettingsWindow` 需要能够动态应用新的QSS样式。
            *   研究 `QApplication.setStyleSheet()` 和 `QWidget.setStyleSheet()` 的动态更新机制。
            *   核心图标（如托盘图标）替换逻辑。
        4.  **自定义样式引擎初步探索 (增强型QSS)**:
            *   **研究**: 调研Python中是否有库可以辅助解析或预处理类CSS的文本。
            *   **定义v0.1语法**:
                *   变量定义与引用: e.g., `@primaryColor: #RRGGBB; QLabel { color: @primaryColor; }`
                *   简单的资源引用: e.g., `background-image: url(theme_resource('backgrounds/main_bg.png'));` (由Python端解析并替换为实际路径)。
            *   **原型**: 实现一个简单的Python脚本，可以将这种"增强型QSS"文件转换为标准的QSS字符串，供 `ThemeManager` 使用。
        5.  **预制主题包**: 创建2-3个不同风格的基础主题包用于测试和演示。
    *   **产出**: 用户可以通过某种方式（初期可能是手动放置主题包到指定目录，并通过日志或简单命令切换）切换应用的主题，看到界面颜色、部分图标和背景的变化。自定义样式引擎有一个初步的原型。

*   **核心任务 1.2: 基础角色参数化自定义 (默认角色)**
    *   **目标**: 用户可以对默认的2D猫咪角色进行一些基础的外观调整。
    *   **子任务与实现**:
        1.  **默认角色资源分析与准备**:
            *   确认默认猫咪的精灵图（L4占位符或初期实际素材）是否适合分层处理（身体、头部、眼睛、特定花纹区域等）。
            *   如果需要，对资源进行切割或标记区域，方便后续的颜色替换或图层叠加。
            *   **同时，初步评估默认角色资源是否支持除颜色和基本斑纹外的、更独立的"图案"元素（如特定形状的小装饰或可切换的局部纹理），及其对资源分层的要求。**
        2.  **自定义UI (`SettingsWindow` 或专用面板)**:
            *   颜色选择器 (QColorDialog) 用于选择身体主色、次级颜色（如斑纹）、瞳孔颜色。
            *   预览区域实时显示颜色变化效果。
        3.  **颜色应用技术**:
            *   **方案A (图像处理)**: 使用 `QPixmap` 或 `QImage` 的像素操作接口，根据选择的颜色动态修改特定区域的像素颜色。可能需要HSV颜色空间转换来实现色调替换或饱和度调整，而不是简单的RGB覆盖。
            *   **方案B (图层叠加)**: 如果角色资源是分层的，可以预制不同颜色的图层，根据用户选择显示相应的图层。
            *   **方案C (着色效果)**: 研究 `QGraphicsEffect` (如 `QGraphicsColorizeEffect`) 是否能满足需求，但这通常作用于整个QWidget。对于像素级的精灵图，前两种方案更直接。优先考虑方案A的灵活性。
        4.  **配置持久化**: 用户自定义的颜色配置需要保存并在下次启动时加载。
    *   **产出**: 用户可以在设置界面中调整默认猫咪的几种核心颜色，并看到实时预览和最终效果。

*   **核心任务 1.3: "创意工坊"系统雏形 - 本地资源管理**
    *   **目标**: 用户有一个统一的界面来查看和管理已安装的主题。
    *   **子任务与实现**:
        1.  **`WorkshopManagerUI` (`status/ui/workshop_manager_window.py`)**:
            *   使用 `QListWidget` 或 `QTableWidget` 列出本地发现的主题包（从 `ThemeManager` 获取列表）。
            *   每项显示主题名称、作者、版本（从 `manifest.json` 读取）。
            *   可选：显示主题预览图（如果 `manifest.json` 中提供）。
        2.  **功能**:
            *   选中主题后，提供"应用主题"按钮 (调用 `ThemeManager.apply_theme()`)。
            *   提供"打开主题文件夹"按钮，方便用户手动管理文件。
            *   未来可扩展为管理插件、角色包等。
        3.  **集成**: 从主应用的菜单（例如托盘菜单或设置窗口）可以打开此"创意工坊"管理界面。
    *   **产出**: 一个可以列出、预览（基本信息）、应用本地主题包的UI管理界面。

*   **核心任务 1.4: 占位符动画 -> 实际2D动画素材替换机制**
    *   **目标**: 建立一套机制，允许用实际的2D精灵动画序列替换掉当前代码生成的占位符动画。
    *   **子任务与实现**:
        1.  **`CharacterAnimationSystem` (`status/character/animation_system.py`)**:
            *   负责加载和管理角色动画资源。
            *   API: `get_animation(character_id: str, state_name: str) -> Optional[SpriteAnimation]`.
            *   与 `PetStateMachine` 解耦，状态机只关心抽象状态，由 `StatusPet` 主类或新的协调者根据当前角色和状态向 `CharacterAnimationSystem` 请求具体动画。
        2.  **动画资源格式定义 (v1)**:
            *   **目录结构**: `characters/<character_id>/animations/<state_name>/frame_###.png` (例如 `characters/default_cat/animations/idle/frame_001.png`).
            *   **描述文件**: `characters/<character_id>/animations/<state_name>/animation.json`，包含：
                *   `frame_rate: int` (帧率)
                *   `loop: bool` (是否循环)
                *   `frames: List[str]` (帧文件名列表，有序)
                *   `anchor_point: Optional[Tuple[float, float]]` (可选，归一化的锚点，0.0-1.0)
        3.  **`SpriteAnimation` 类 (`status/renderer/animation.py` 或 `status/character/sprite_animation.py`)**:
            *   持有从描述文件加载的动画数据（帧列表、帧率等）。
            *   提供 `update(dt: float)` 方法更新当前帧。
            *   提供 `get_current_frame_pixmap() -> Optional[QPixmap]` 方法获取当前帧图像（由 `AssetManager` 加载）。
        4.  **与 `PlaceholderFactory` 的过渡/替换**:
            *   修改 `StatusPet` 或相关逻辑，当请求一个状态的动画时，优先尝试从 `CharacterAnimationSystem` 加载。如果失败（例如，该角色或状态没有实际素材），则回退到 `PlaceholderFactory` 获取L4占位符动画。
        5.  **工具/文档**: 提供一个简单的Markdown文档，说明如何创建和组织精灵动画序列及`animation.json`文件。
    *   **产出**: 能够为默认猫咪的几个核心状态（如Idle, Walking, Sleeping）替换上用户提供的2D精灵动画序列，并能正确播放。

**阶段 2: "生态初具" - 扩展插件与角色多样性 (中期目标, 3-6个月)**

*   **核心任务 2.1: 插件系统 API v1 与核心服务暴露**
    *   **目标**: 插件可以安全地与应用核心功能交互，**特别是支持开发者封装和调用针对特定外部数据源或复杂交互逻辑的接口，例如通过逆向工程获得的能力，从而扩展应用的数据感知和互动维度。**
    *   **子任务与实现**:
        1.  **核心服务接口定义 (`status/services/` 或 `status/api/`)**:
            *   使用ABC或Protocol定义接口，例如：
                *   `IPetStateService`: `get_current_state() -> PetState`, `get_pet_mood() -> Dict[str, float]`.
                *   `ISystemMonitorService`: `get_cpu_usage() -> float`, `get_memory_usage() -> float`.
                *   `IEventBrokerService`: `subscribe(event_type: EventType, handler: Callable)`, `publish(event: Event)`.
                *   `IUIService` (非常有限的MVP): `show_notification(title: str, message: str)`, `add_custom_tray_menu_item(text: str, callback: Callable)`.
                *   `IAssetService`: `get_resource_path(plugin_id: str, relative_path: str) -> Optional[str]` (让插件能访问其自身包内的资源).
        2.  **`PluginManager` (`status/plugins/plugin_manager.py`) 增强**:
            *   插件加载：扫描插件目录 (e.g., `PROJECT_ROOT/plugins/` or user-defined)。
            *   插件生命周期：`load()`, `enable()`, `disable()`, `unload()`。
            *   API代理/注入：当插件请求服务时，`PluginManager` 提供服务的代理实例，可以做权限检查或日志记录。
            *   插件 `manifest.json` 扩展：声明所需API权限 `required_permissions: ["pet_state:read", "system_monitor:read", "ui:show_notification"]`.
        3.  **安全考虑 (v1 - 基础)**:
            *   插件在单独的线程中运行其耗时操作（如果需要）。
            *   严格限制插件对文件系统和网络的直接访问，除非明确授权。API应作为主要交互途径。
        4.  **官方示例插件 (2-3个)**:
            *   简单信息展示：一个插件在特定时间（通过订阅时间事件）使用 `IUIService.show_notification` 显示"今日名言"。
            *   状态响应：一个插件订阅 `PetStateChangedEvent`，当宠物进入特定状态（如 `SLEEPING`）时，播放一个（插件包内提供的）短音效（需要 `IAudioService` MVP，或暂时通过系统命令播放）。
    *   **产出**: 开发者可以通过编写符合规范的Python类（插件）与应用核心功能进行有限的、安全的交互，实现简单的功能扩展。

*   **核心任务 2.2: 2D角色配件系统 MVP**
    *   **目标**: 用户可以为默认角色添加和切换简单的2D配件。
    *   **子任务与实现**:
        1.  **默认角色配件锚点定义**:
            *   在默认猫咪角色的设计图或骨骼信息（如果是骨骼动画的话，但我们目前是精灵序列）中定义逻辑锚点 (e.g., `head_top`, `neck_front`, `tail_base`) 及其相对坐标和可能的旋转。
        2.  **配件资源格式 v1**:
            *   单个图片 (`.png` with alpha) 或简单的精灵序列 (类似动画帧)。
            *   `accessory_manifest.json`: `name`, `type` (e.g., hat, collar), `anchor_point_name` (对应角色锚点), `offset_x`, `offset_y`, `z_order_offset` (相对于锚点所在图层的渲染层级微调).
        3.  **`AccessoryManager` (`status/character/accessory_manager.py`)**:
            *   管理已加载的配件信息。
            *   允许用户为当前角色装备/卸载配件。
            *   存储当前角色的配件配置。
        4.  **渲染集成**:
            *   `CharacterAnimationSystem` 或渲染流程需要获取当前装备的配件列表。
            *   在渲染角色帧后，根据配件的锚点、偏移、旋转和层级，将配件图像叠加绘制到角色上。
        5.  **UI (`SettingsWindow`或工坊界面)**: 提供界面让用户选择并装备/卸载配件。
    *   **产出**: 用户可以为默认猫咪戴上帽子、领结等简单2D图片配件，配件会随角色动画（基础定位）。

*   **核心任务 2.3: "创意工坊"系统 v2 - 在线浏览与下载 (概念验证)**
    *   **目标**: 用户可以直接在应用内浏览和下载社区内容。
    *   **子任务与实现**:
        1.  **简单服务端原型 (可选，或纯静态)**:
            *   使用 GitHub Pages 或一个非常简单的 Python web框架 (Flask/FastAPI) 托管一个 `index.json` 文件。
            *   `index.json` 包含资源列表：`[{ "id": "theme_ocean", "type": "theme", "name": "Ocean Blue", "author": "UserA", "version": "1.0", "description": "...", "preview_url": "...", "download_url": "...", "tags": ["blue", "calm"] }, ...]`
            *   资源包 (`.zip` 或特定格式) 也托管在该服务器上。
        2.  **客户端UI (`WorkshopManagerUI` 增强)**:
            *   增加"在线"标签页。
            *   从服务器获取并解析 `index.json`，展示资源列表（带预览图、描述、作者等）。
            *   提供"下载并安装"按钮。
            *   下载后，根据资源类型 (theme, accessory_pack) 调用相应的管理器进行安装（例如，解压到 `themes/` 目录，通知 `ThemeManager` 刷新）。
        3.  **基础安全与校验**:
            *   下载前检查 `download_url` 是否可信（初期可以是白名单）。
            *   下载的压缩包进行完整性校验（如MD5/SHA256，如果服务器提供）。
            *   解压后检查 `manifest.json` 的基本格式。
    *   **产出**: 用户可以在应用内看到一个（模拟的）在线资源列表，并能成功下载、安装至少一种类型的资源（如主题包）。

**阶段 3: "社区繁荣" - 深度扩展与用户创造 (长期目标, 6个月以上)**

*   **核心任务 3.1: 完整的2D角色包系统**
    *   **目标**: 用户可以下载和使用完全不同的2D角色。
    *   **子任务与实现**:
        1.  **角色包规范 v1 (`characters/<character_id_new>/`)**:
            *   包含完整的精灵图集、所有状态的动画定义文件 (遵循阶段1.4的格式)、角色清单文件 `character_manifest.json`。
            *   `character_manifest.json`: `id`, `name`, `author`, `version`, `description`, `preview_image`, `default_scale`, 状态到动画目录的映射, 配件锚点定义 (如果该角色支持配件)。
        2.  **`CharacterFactory` / `CharacterManager` (`status/character/character_manager.py`)**:
            *   负责加载、管理和切换不同的角色包。
            *   API: `load_character_pack(path)`, `set_active_character(character_id)`, `get_active_character() -> Optional[Character]`.
        3.  **`Character` 类**: 代表一个加载的角色，包含其所有动画、属性和配件逻辑。
        4.  **动画系统和渲染系统适配**: 确保能处理不同角色包的动画数据和渲染需求。
        5.  **UI (`SettingsWindow`或工坊界面)**: 允许用户选择和切换当前激活的角色。
    *   **产出**: 用户可以下载并切换到至少一个与默认猫咪外观和动画完全不同的新2D角色。

*   **核心任务 3.2: 插件系统 API v2 与更丰富的服务**
    *   **目标**: 提供更强大的插件能力。
    *   **子任务与实现**:
        1.  **扩展核心服务API**:
            *   `IUIService` v2: 允许插件创建自定义的简单UI片段（如在StatsPanel中添加一个区域，或弹出一个简单的自定义窗口）。需要仔细设计UI注入和布局方式，避免破坏主UI。
            *   `IBehaviorService`: 允许插件建议或触发特定行为，甚至定义新的简单行为模式 (需要与 `BehaviorManager` 协作)。
            *   `IStorageService`: 为插件提供安全的、隔离的持久化存储空间。
        2.  **插件沙箱研究 (可选，视复杂度)**: 如果插件功能更强大，研究如何在一定程度上隔离插件代码，例如使用Python的 `multiprocessing` 或更轻量级的执行限制。
        3.  **更完善的权限系统**: 基于 `manifest.json` 中的权限声明，更细致地控制API的访问。
    *   **产出**: 插件能够实现更复杂的功能，例如与外部服务交互（通过代理）、自定义一部分UI、或更深度地影响宠物行为。

*   **核心任务 3.3: "创意工坊"系统 v3 - 用户上传与社区互动**
    *   **目标**: 用户可以将自己创建的内容上传到社区平台。
    *   **子任务与实现**:
        1.  **服务端增强**:
            *   需要支持用户账户系统。
            *   实现资源上传接口。
            *   数据库存储资源元信息、下载统计、用户评价等。
            *   可选：简单的审核后台。
        2.  **客户端UI (`WorkshopManagerUI` 增强)**:
            *   "我的创作"区域：允许用户打包并上传自己的主题、配件、角色包、插件。
            *   浏览在线资源时，增加评价、评论、收藏等互动功能。
    *   **产出**: 一个功能更完善的创意工坊，用户不仅可以下载，还可以上传和分享自己的创作，形成初步的社区循环。

*   **核心任务 3.4: 自定义样式引擎 v1**
    *   **目标**: 摆脱QSS的限制，提供更强大、更现代的UI样式定义能力。
    *   **子任务与实现**:
        1.  **设计与规范**: 基于阶段1.1中对"增强型QSS"的探索，正式设计自定义样式语言的v1规范。
            *   支持变量、简单计算、规则嵌套。
            *   研究如何更好地与Python端进行数据绑定或状态关联（例如，根据Python变量值改变样式）。
        2.  **解析与应用**:
            *   选择或实现一个解析器（如使用PLY, Lark等库）将自定义样式文本解析成结构化的样式规则。
            *   实现一个样式应用模块，能够将这些结构化的规则应用到PySide6的QWidget上（可能通过动态生成QSS，或者通过直接操作QWidget的属性和 `QStyle`）。
        3.  **性能考量**: 确保样式解析和应用过程高效，不会导致UI卡顿。
        4.  **工具链**: 提供语法高亮插件（如果可能）或Linter，帮助主题开发者编写自定义样式。
    *   **产出**: 一个可用的自定义样式引擎v1，允许主题开发者使用比QSS更灵活和强大的方式定义应用外观。

---

**附：关于Python版本 (3.11 vs 3.13)**

*   **结论**: 当前坚守 **Python 3.11** 是完全合理的。专注于完成阶段0和阶段1的核心功能。
*   **后续评估**: 在阶段1基本完成后，或在准备启动需要特定新版本特性的阶段2任务前，再重新评估升级到 Python 3.12 或 3.13 (届时可能已正式发布并稳定) 的必要性和收益。主要考量新特性需求、依赖兼容性和稳定性。

