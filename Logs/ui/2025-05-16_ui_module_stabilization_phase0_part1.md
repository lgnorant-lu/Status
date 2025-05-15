# UI 模块稳定化 Phase 0 - Part 1: 修复 AttributeError (2025/05/16)

## 背景
在开始 UI 模块 (`tests/ui/`) 的稳定化工作时，初步运行测试显示大量失败。
通过分析之前的 `tests/core/` 修复经验，推断许多失败与 `EventManager` 的获取方式有关。
具体表现为 `AttributeError: 'function' object has no attribute 'get_instance'`，因为代码中多处使用了旧的 `EventManager.get_instance()` 而不是新的 `EventManager()` (其中 `EventManager` 是 `LegacyEventManagerAdapter.get_instance` 方法的别名)。

## 修复过程

1.  **初步诊断**:
    *   运行 `pytest tests/ui/ -v`，结果：29 failed, 18 passed.
    *   通过错误日志，确认多处存在 `AttributeError: 'function' object has no attribute 'get_instance'`。

2.  **定位问题模块**:
    *   `status/ui/stats_panel.py`: 在 `__init__` 中使用 `EventManager.get_instance()`。
    *   `status/interaction/drag_manager.py`: 在 `__init__` 中使用 `EventManager.get_instance()` (尽管它在 `interaction` 模块，但被UI测试间接调用)。
    *   `status/monitoring/system_monitor.py`: 在 `publish_stats` 函数中使用 `EventManager.get_instance()`。

3.  **代码修改**:
    *   **`status/ui/stats_panel.py`**:
        *   将 `self.event_manager = EventManager.get_instance()` 修改为 `self.event_manager = EventManager()`。
    *   **`status/interaction/drag_manager.py`**:
        *   将 `self.event_manager = EventManager.get_instance()` 修改为 `self.event_manager = EventManager()`。
    *   **`status/monitoring/system_monitor.py`**:
        *   将 `event_manager = EventManager.get_instance()` 修改为 `event_manager = EventManager()`。

4.  **验证**:
    *   针对性运行 `tests/ui/test_stats_panel.py`, `tests/ui/test_stats_panel_integration.py`, `tests/ui/test_ui_optimization.py` 中的部分测试，确认相关 `AttributeError` 消失。
    *   特别运行 `tests/ui/test_stats_panel_integration.py::TestStatsPanel::test_publish_stats_updates_panel` 确认 `system_monitor.py` 的修复。
    *   最后再次运行 `pytest tests/ui/ -v`。

## 结果
*   **修复后测试结果 (`pytest tests/ui/ -v`)**: 30 passed, 17 failed, 16 warnings.
*   相比修复前 (18 passed, 29 failed)，通过的测试增加了12个，失败的测试减少了12个。
*   所有直接由 `EventManager.get_instance()` 方式调用导致的 `AttributeError` 均已解决。

## 后续问题
剩余的17个失败主要归因于：
1.  **`TypeError` (MagicMock for QMouseEvent)**: 在 `test_main_pet_window.py` 中。
2.  **`RuntimeError` (QApplication singleton)**: 在 `test_stats_panel_in_app.py` 和 `test_ui_optimization.py` 中。
3.  **`TypeError` (SystemTrayManager.__init__ args)**: 在 `test_system_tray.py` 中。
4.  **`AssertionError` (逻辑错误)**: 分散在几个测试文件中。

这些问题将在后续的 UI 模块稳定化工作中逐一解决。 