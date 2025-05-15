# Log: 事件系统统一计划 - Phase 1: 策略制定与文档更新

- **日期**: 2025-05-16
- **模块**: Core (Event System)
- **作者**: Ignorant-lu
- **相关任务**: Thread.md - Task 2.3.4 (TDD): 事件系统深度统一 (Adapter-based Unification)

## 1. 任务背景与目标

当前项目中存在两个主要的事件系统：
1.  `status.core.event_system._EventSystem` (以下简称 `_EventSystem`): 一个基础的、基于枚举事件类型的同步事件派发器。目前被应用核心 `StatusPet` 和 `StatsPanel` 等组件使用。
2.  `status.events.event_manager.EventManager` (以下简称 `AdvancedEventManager`): 一个功能更丰富的事件系统，基于字符串事件类型，支持事件优先级、过滤、节流、异步处理、信号槽式连接等高级特性。该系统已作为 Task 2.3.2 开发完成，但尚未完全集成。

**目标**: 为了提升代码的健壮性、可维护性，并利用更高级的事件处理能力，本项目计划将所有事件处理统一到 `AdvancedEventManager`。

## 2. 当前状态分析 (API 对比摘要)

| 特性             | `_EventSystem` (status.core.event_system) | `AdvancedEventManager` (status.events.event_manager) | 主要差异与迁移影响                                                                 |
| ---------------- | ------------------------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------ |
| 事件类型定义   | `enum.Enum` (e.g., `EventType.SYS_UPDATE`)  | `str` (e.g., `"SYS_UPDATE"`)                         | **重大差异**。需转换或映射。                                                             |
| 事件数据传递   | `Event` 对象 (含 `type`, `sender`, `data`) | 直接传递 `event_type: str`, `event_data: Any`        | **重大差异**。处理器签名和事件创建/发射逻辑需重写。                                        |
| 处理器签名     | `Callable[[Event], None]`                   | `Callable[[str, Any], None/Coroutine]`               | **重大差异**。                                                                         |
| 注册/订阅      | `register_handler(EventType, handler_func)` | `subscribe(str, handler_func, ...)` 返回 `Subscription` | API及返回不同。                                                                        |
| 注销/取消订阅  | `unregister_handler(EventType, handler_func)` | `unsubscribe(Subscription)`                          | 基于订阅对象，更精确。                                                                   |
| 分发/发射      | `dispatch(Event)` 或 `dispatch_event(...)`    | `emit(str, data)`                                  | API不同。                                                                              |
| `event.handled`  | 支持                                        | 无直接对应，需通过其他方式实现                                                         | 语义可能变化。                                                                         |
| 高级特性       | 无                                          | 优先级, 过滤器, 异步, 节流, 通配符, 一次性等         | 统一的主要动机。                                                                       |

**结论**: API差异巨大，无法直接替换。必须采用兼容性策略进行过渡。

## 3. 计划采用的策略：适配器模式与渐进式迁移

为确保平稳过渡并最小化风险，将采用以下多阶段策略：

**Phase 1: API 对比分析与文档更新 (当前阶段 - 已完成分析，正在记录)**
- 深入理解两个系统的API差异。
- 更新项目文档 (`Thread.md`, `Design.md`, 本 Log 文件) 以反映统一计划和策略。

**Phase 2: 适配器 (`LegacyEventManagerAdapter`) 设计与初步实现**
- **创建分支**: `feature/unify-event-system`。
- **设计适配器**: 创建 `LegacyEventManagerAdapter` 类，暴露与 `_EventSystem` 兼容的API，内部调用 `AdvancedEventManager`。
    - 重点解决 `Event` 对象与 `(event_type_str, event_data)` 之间的转换。
    - 考虑 `event.handled` 语义的模拟。
- **初步实现**: 在新文件 (e.g., `status/events/legacy_adapter.py`) 中实现适配器。
- **修改别名**: 使 `status.core.events.EventManager` 别名指向 `LegacyEventManagerAdapter`。
- **测试验证**: 运行项目测试，迭代完善适配器，目标是使大部分现有测试通过。

**Phase 3: 基于适配器的系统稳定性验证 (TDD)**
- 在适配器模式下，对整个应用进行全面的功能测试和稳定性测试。
- 修复适配器或相关代码中发现的问题，确保应用核心功能不受影响。

**Phase 4: 分模块逐步迁移到 `AdvancedEventManager` 原生 API (TDD)**
- 从关键模块开始 (如 `StatsPanel`, `StatusPet` 的事件处理逻辑)。
- **对每个模块**:
    1.  分析其当前的事件使用方式。
    2.  编写或调整单元/集成测试，覆盖其事件处理逻辑。
    3.  重构代码，使其直接使用 `AdvancedEventManager` 的原生API (如 `subscribe`, `emit`，并使用字符串事件类型)。
    4.  利用 `AdvancedEventManager` 的高级特性 (优先级、过滤等) 优化代码。
    5.  确保所有相关测试通过。
    6.  提交模块的迁移变更。

**Phase 5: 清理适配器与旧系统 (TDD)**
- 当所有相关模块都已成功迁移并测试通过后：
    1.  移除 `LegacyEventManagerAdapter`。
    2.  确保 `status.core.events.EventManager` 直接指向 `AdvancedEventManager` (如果之前指向适配器的话)。
    3.  彻底删除 `status.core.event_system.py` 文件及其所有引用。
    4.  进行最终的全局回归测试和手动验证。

**Phase 6: 文档最终化与合并**
- 更新所有项目文档 (`Design.md`, `Structure.md`, 开发者注释等)，准确反映统一后的事件系统架构。
- 更新 `Thread.md`，将事件系统统一任务标记为完成。
- 将 `feature/unify-event-system` 分支合并到主开发分支。

## 4. 预期风险与挑战

- **API 差异的复杂性**: `Event` 对象模型到 `(type, data)` 模型的转换，以及 `event.handled` 语义的适配可能引入细微错误。
- **适配器本身的复杂度**: `LegacyEventManagerAdapter` 需要精心设计和全面测试，以避免成为新的问题源。
- **测试覆盖率**: 需要确保有足够的测试覆盖所有通过事件系统交互的模块，以在迁移过程中捕获回归。
- **性能影响**: 虽然 `AdvancedEventManager` 设计上考虑了性能，但适配器层可能会引入微小的开销。在迁移完成后应进行评估。
- **开发中断**: 如果适配不当或迁移步骤出错，可能导致主功能暂时不可用。

## 5. 当前进展

- Phase 1 的 API 对比分析已完成。
- 本 Log 文件已创建，记录了详细的统一计划。
- `Thread.md` 和 `Design.md` 已更新，反映了此任务和策略。
- 下一步将是 Phase 2：创建 `feature/unify-event-system` 分支，并开始设计和初步实现 `LegacyEventManagerAdapter`。 