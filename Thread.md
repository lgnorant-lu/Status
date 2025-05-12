# 任务进程文档 for Status-Ming

## 项目信息
- **项目名称**: Status-Ming
- **作者**: lgnorant-lu (lgnorantlu@gmail.com)
- **核心技术**: PySide6
- **当前主要目标**: MVP - 实现赛博小鱼缸类似的核心桌宠监控功能 (使用占位符素材)
- **最后更新**: 2025-05-18

## 一、开发计划文档化策略 (进行中)

- **1. `Thread.md`**: [正实现] 本文档，用于跟踪任务。
- **2. `Design.md`**: [计划中] 更新MVP架构和核心模块描述。
- **3. `Structure.md`**: [计划中] 更新项目名、作者、assets占位符结构。
- **4. `README.md` (根)**: [计划中] 更新项目名、作者、PySide6依赖、MVP描述。
- **5. `docs/` 目录**: [计划中] 审查并标记过时文档，规划新文档。
- **6. `Log.md`**: [计划中] 标记旧日志，准备记录新日志。

## 二、短期开发计划 (MVP阶段)

### 阶段0: 环境与基础配置
- **0.1.** [已完成] 确认项目名称为 `Status-Ming`，作者信息更新。
- **0.2.** [进行中] 清理代码库 (参照 `Logs/2025-04-17_project_cleanup_phase1.md`)。
- **0.3.** [待办] **关键**: 解决 `status/interaction/interaction_manager.py` 的Linter错误。
- **0.4.** [待办] **关键**: 对 `status/` 目录下留存的核心模块进行单元/集成测试 (core, utils, resources, interaction, monitoring)。
- **0.5.** [待办] 确保 `requirements.txt` 正确配置 (PySide6, psutil, GPUtil)。
- **0.6.** [待办] 更新 `README.md` (项目名、作者、PySide6依赖、MVP描述)。 (与1.4部分重叠，指根README)
- **0.7.** [已完成] 初始化 `Thread.md`。 (通过当前操作完成)
- **0.8.** [待办] 初始化/更新 `Design.md` (MVP架构草图和核心模块描述)。 (与1.2部分重叠)
- **0.9.** [待办] 初始化/更新 `Structure.md` (项目名、作者、assets占位符结构)。 (与1.3部分重叠)

### 阶段1: 桌宠显示与基础交互 (PySide6 UI核心)
- **1.1.** [计划中] UI: 创建基础无边框、可透明的 `PetWindow` (PySide6)。
- **1.2.** [计划中] UI: 实现 `PetWindow` 拖拽移动。
- **1.3.** [计划中] UI: `PetWindow` 加载并显示静态占位符图像。
    - 测试 `status/resources/` 与PySide6图像加载。
- **1.4.** [计划中] Renderer: 初步集成 `status/renderer/` 与PySide6，在 `PetWindow` 绘制。
- **1.5.** [计划中] Interaction: 实现右键菜单（含\"退出\"）。
    - 测试 `status/interaction/` 与PySide6事件处理。

### 阶段2: 系统参数获取与显示
- **2.1.** [计划中] Monitoring: 实现/完善 `status/monitoring/` 获取系统核心参数。
- **2.2.** [计划中] UI: 设计并实现简约的 `StatsPanel` 显示参数。

### 阶段3: 桌宠状态与系统参数联动
- **3.1.** [计划中] Behavior: 设计 `status/behavior/` MVP版状态机 (IDLE, ACTIVE_LOW/MEDIUM/HIGH, SLEEPING)。
- **3.2.** [计划中] Renderer: 扩展 `status/renderer/` 播放占位符帧动画。
- **3.3.** [计划中] Core Logic: 实现系统参数触发行为状态转换。
- **3.4.** [计划中] Core Logic: 行为状态改变通知渲染器切换动画。

### 阶段4: 打包与回顾
- **4.1.** [计划中] 编写MVP用户使用说明。
- **4.2.** [计划中] 初步尝试MVP版本打包。
- **4.3.** [计划中] MVP开发回顾与总结。

## 三、长期开发愿景 (MVP之后 - 状态：[计划中])
- L1. 真实素材集成
- L2. 丰富桌宠行为与交互
- L3. UI界面美化与定制
- L4. 模块化快捷功能
- L5. 自定义一键式便捷功能
- L6. LLM集成探索
- L7. MCP集成探索
- L8. 桌宠记忆化与个性化
- L9. 性能优化与资源控制
- L10. 跨平台兼容性完善
- L11. 完善的文档与社区支持

## 四、当前任务与 ближайшие шаги (Next Steps)
1.  **优先文档更新 (参照 \"实施清单 1\")**:
    *   更新 `README.md` (根)
    *   更新 `Structure.md`
    *   更新 `Design.md` 框架
    *   更新 `Log.md` 标记
    *   更新 `requirements.txt`
2.  **代码库稳定 (参照 \"实施清单 2\" 和 \"阶段0\")**:
    *   解决 `status/interaction/interaction_manager.py` Linter错误。
    *   对 `status/` 下核心模块进行全面测试。

## 模块间依赖关系说明 (初步 - 待细化)
- `PetWindow (UI)` 依赖 `Renderer` 来显示内容, 依赖 `InteractionHandler` 处理用户输入。
- `Renderer` 依赖 `Resources` 加载素材, 接收 `BehaviorLogic` 的状态更新以切换动画。
- `BehaviorLogic` 接收 `SystemMonitor` 的数据, 并可能受 `InteractionHandler` 的某些输入影响。
- `SystemMonitor` 独立获取系统数据。
- `StatsPanel (UI)` 依赖 `SystemMonitor` 获取数据。

## Status-Ming 项目工作进度

### 环境与基础设施 [进行中]

#### 类型提示系统优化 [进行中]
- [已完成] 创建 `status/core/types.py` 通用类型定义模块 
- [已完成] 为项目添加 mypy 配置文件
- [进行中] 修复主要模块类型错误：
  - [已完成] 修复 `status/resources/` 目录中的类型提示问题 (包括 `resource_pack.py`, `resource_loader.py`, `cache.py`, `asset_manager.py`)
  - [已完成] 修复 `tests/resources/test_resource_system.py` 测试用例
  - [已完成] 修复 `status/core/config/config_manager.py` 中的类型问题
  - [已完成] 修复 `status/interaction/interaction_manager.py` 中的主要Linter错误 (缩进、未使用ignore)
  - [已完成] 修复 `status/monitoring/` 目录中的类型提示问题
  - [已完成] 修复 `status/renderer/` 目录中的类型提示问题
  - [已完成] 修复 `status/behavior/` 目录中的依赖问题 (添加缺失的组件基础类和实用工具)
    - [已完成] 创建 `status/core/component_base.py` 实现基础组件类
    - [已完成] 创建 `status/utils/vector.py` 实现向量计算工具
    - [已完成] 创建 `status/utils/decay.py` 实现衰减函数工具
    - [已完成] 修复 `basic_behaviors.py` 中的 `BasicBehavior` 类缺失问题
    - [已完成] 解决 `environment_sensor.py` 中的循环导入和元类冲突问题
    - [已完成] 修复 `emotion_system.py` 中的函数调用错误
  - [待完善] 处理残余的类型提示问题 (例如 `status/utils/`, `status/scenes/`)
  - [待完善] 修复严重级别较低的类型提示问题

#### 测试修复 [进行中]
- [已完成] 修复 `tests/resources/test_resource_system.py` 测试用例
- [计划中] 修复其他测试用例

### MVP 开发 [计划中]

#### 阶段0: 环境准备 [进行中]
- [已完成] 更新核心文档
- [进行中] 修复 linter 错误和测试用例
- [待完善] 更新 `requirements.txt`
- [已完成] 修复 `status/interaction/interaction_manager.py` 中的主要Linter阻塞性错误

#### 阶段1: 基础窗口功能 [计划中]
- [计划中] 实现 `PetWindow` 基础功能
- [计划中] 实现拖拽和右键菜单功能
- [计划中] 添加基本占位资源

#### 阶段2: 系统信息获取 [计划中]
- [计划中] 实现 `SystemMonitor` 核心功能
- [计划中] 设计并实现 `StatsPanel` 组件

#### 阶段3: 宠物行为与系统参数联动 [计划中]
- [计划中] 设计 `BehaviorLogic` 组件
- [计划中] 完善资源管理与渲染系统
- [计划中] 实现宠物状态与系统参数联动

#### 阶段4: MVP打包与测试 [计划中]
- [计划中] 完善错误处理和日志功能
- [计划中] 生成打包配置
- [计划中] 测试不同环境下的运行情况

## 当前任务

- [已完成] 资源模块类型提示优化（resource_pack.py, resource_loader.py, cache.py, config_manager.py）
- [已完成] 监控模块类型提示优化（system_info.py, data_process.py, monitor.py, ui_controller.py）
- [已完成] 渲染器模块类型提示优化
- [已完成] 交互模块类型提示优化（event_filter.py, interaction_event.py, event_throttler.py）
- [已完成] 添加缺失的核心基础文件（component_base.py, vector.py, decay.py）
- [待完善] UI模块类型提示优化
- [待完善] Behavior模块类型提示优化
- [待完善] Scenes模块类型提示优化

## 计划任务

- [计划中] 系统单元测试覆盖率提升
- [计划中] 资源包加载逻辑优化
- [计划中] 主题样式切换功能
- [计划中] 渲染性能优化

## 已完成

- 基础框架搭建
- PySide6 集成
- 添加缺失的基础组件：
  - [已完成] 创建 `status/core/component_base.py` 实现组件基类
  - [已完成] 创建 `status/utils/vector.py` 实现二维向量工具
  - [已完成] 创建 `status/utils/decay.py` 实现衰减函数工具

## 类型提示优化
- [已完成] 修复 Resources 模块中的类型注解
- [已完成] 修复 Monitoring 模块中的类型注解
- [已完成] 修复 Renderer 模块中的类型注解
- [已完成] 修复 Interaction 模块中的类型注解
  - [已完成] 修复 event_filter.py 类型注解
  - [已完成] 修复 interaction_event.py 类型注解
  - [已完成] 修复 event_throttler.py 类型注解
- [已完成] 添加缺失的基础组件代码和类型注解
  - [已完成] 添加 `status/core/component_base.py` 组件基类
  - [已完成] 添加 `status/utils/vector.py` 二维向量类
  - [已完成] 添加 `status/utils/decay.py` 衰减函数

---
*此文档将随项目进展动态更新。*