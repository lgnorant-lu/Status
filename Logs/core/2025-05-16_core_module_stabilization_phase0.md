# 核心模块 (`status/core/`) 功能稳定化日志 - 阶段0

**日期**: 2025/05/16

## 任务概述
此日志记录了对 `status/core/` 目录下的核心逻辑和基础组件进行测试驱动的修复和稳定化工作的过程，目标是确保所有 `tests/core/` 测试通过。
Это является частью общей задачи "Этап 0: Уточнение и стабилизация основных функций".

## 初始状态 (2025/05/16)
- **前置条件**: `tests/interaction/` 模块中的测试已全部通过。
- **当前行动**: 准备开始分析 `tests/core/` 模块的测试失败情况。
- **目标**: 识别第一个失败的测试用例，并着手进行修复。 

## 修复 `AttributeError` in `LegacyEventManagerAdapter` (2025/05/16)
- **问题**: `tests/core/test_events_manager.py` 中的测试因 `AttributeError: type object 'EventManager' has no attribute 'get_instance'` 而失败。
- **原因**: `LegacyEventManagerAdapter` 在其 `advanced_em` 属性中尝试通过 `AdvancedEventManager.get_instance()` 获取新事件管理器的实例。然而，`AdvancedEventManager` (即 `status/events/event_manager.py::EventManager`) 是通过元类实现的单例，应使用 `AdvancedEventManager()` 获取实例。
- **修复**: 修改 `status/events/legacy_adapter.py`，将 `LegacyEventManagerAdapter._advanced_event_manager_instance = AdvancedEventManager.get_instance()` 更改为 `LegacyEventManagerAdapter._advanced_event_manager_instance = AdvancedEventManager()`。
- **结果**:
    - `tests/core/test_events_manager.py` 中的所有3个测试均通过。
    - `tests/core/` 目录下的所有测试均通过 (29 passed, 1 skipped)。
- **状态**: [已完成] 