# [2025-04-17] Project Cleanup - Phase 1

## 背景
为了将桌宠项目从《空洞骑士》主题转向新的、素材获取更自由的主题（例如猫咪，像素风格），需要对现有项目结构进行清理，移除旧主题相关的资源和代码，并解决模块冗余问题。本次为第一阶段清理。

## 清理内容

### 1. `assets/` 目录
- **已删除:**
  - `assets/sprites/idle/README.md`
  - `assets/sprites/idle/generate_idle_frames.py`
  - `assets/Plan.md` (确认为旧版计划文档)
- **待手动删除:**
  - `assets/sprites/idle/` 目录下的所有 `.png` 文件 (旧knight动画帧)
  - `assets/images/characters/knight/` 目录及其所有内容 (旧knight角色图)
    - *原因：工具无法直接删除二进制文件和非空目录。*

### 2. `status/core/` 目录 (冗余模块清理)
- **已删除:**
  - `status/core/asset_manager.py` (功能被 `status/resources/asset_manager.py` 替代)
  - `status/core/resource_loader.py` (功能被 `status/resources/resource_loader.py` 替代)
  - `status/core/cache.py` (功能被 `status/resources/cache.py` 替代)
  - `status/core/scene_manager.py` (功能被 `status/scenes/scene_manager.py` 替代)

## 目标
- 为新主题开发清理出干净的项目环境。
- 解决已识别的模块冗余，使用功能更完善的模块版本。

## 后续计划
- 继续审查项目内其他目录 (`resources/`, `tests/`, `docs/` 等以及 `status/` 下未分析的子目录)。
- 解决 `status/monitor/` vs `status/monitoring/` 和 `status/config/` vs `status/core/config/` 的冗余问题。
- 在完成所有清理后，再进行可能的项目结构重构。 

### 3. 根目录文件及目录清理 (执行于 2025-05-12)
- **已删除文件:**
  - `spritemaskeditor.log`
  - `simple_knight_idle_demo.py`
  - `Thread.old.md`
  - `Plan.md` (根目录下)
  - `config_schema.json`
  - `default_config.json`
- **已删除目录:**
  - `resources/` (根目录下)
  - `core/` (根目录下)
  - `renderer/` (根目录下)
  - `temp_config/`
  - `__pycache__/` (根目录下，如果存在)

### 4. `assets/` 目录空子目录清理 (执行于 2025-05-12)
- **已检查并尝试删除以下空目录 (实际删除取决于目录是否为空):**
  - `assets/fonts/`
  - `assets/audio/sfx/`
  - `assets/audio/music/`
  - `assets/images/effects/`
  - `assets/images/ui/`
  - `assets/images/scenes/`

### 5. `status/` 内部模块删除 (执行于 2025-05-12)
- **已删除目录:**
  - `status/config/`
  - `status/monitor/`
  - `status/examples/`
  - `status/launcher/`
  - `status/pomodoro/`
  - `status/screenshot/`
  - `status/notes/`
  - `status/weather/`
  - `status/reminder/`
  - `status/interaction/command/`

### 6. `status/ui/` 内部清理 (执行于 2025-05-12)
- **已删除:**
  - `status/ui/examples/` (目录)
  - `status/ui/monitor_ui.py`
  - `status/ui/monitor_app.py`

### 7. `tests/` 内部清理 (执行于 2025-05-12)
- **已删除目录:**
  - `tests/launcher/`
  - `tests/weather/`
  - `tests/reminder/`
  - `tests/monitor/`
  - `tests/core/docs/`
  - `tests/test_renderer/` (移动文件后删除空目录)
  - `tests/test_scene/` (移动文件后删除空目录)
- **已删除文件:**
  - `tests/test_knight_idle_widget.py`
  - `tests/test_knight_idle_widget_gui.py`
  - `tests/renderer/tray_demo.py`
- **已移动文件:**
  - `tests/test_renderer/test_drawable.py` -> `tests/renderer/test_drawable.py`
  - `tests/test_renderer/test_effects.py` -> `tests/renderer/test_effects.py`
  - `tests/test_scene/test_scene_manager_transition.py` -> `tests/scenes/test_scene_manager_transition.py`

### 8. 代码编辑 (执行于 2025-05-12)
- **文件:** `status/interaction/interaction_manager.py`
- **操作:** 检查并确认 `CommandManager` 相关引用已被移除或注释。
- **状态:** 操作符合预期，无需进一步编辑以移除 `CommandManager`。然而，文件在之前的编辑后（由IDE辅助模型执行的更广泛的更改）**目前存在多处linter错误**。用户已决定在此阶段继续，后续可能需要修复这些错误。

## 清理阶段总结 (截至 2025-05-12)
- 大部分计划的文件和目录清理已完成。
- `status/interaction/interaction_manager.py` 中目标解耦已完成，但附带了较多linter错误。
- 项目结构得到显著精简，为后续新主题的引入和重构奠定了基础。 