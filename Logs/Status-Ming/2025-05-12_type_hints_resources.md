# [2025-05-12] 类型提示系统优化 - Resources模块

## 目标
解决 `status/resources/` 目录下所有 `mypy` 类型检查错误。

## 主要变更和修复摘要

### 1. `status/resources/resource_loader.py`
- **`base_path` 属性**: 添加 `self.base_path: Optional[str] = None` 到 `__init__`。
- **`_get_resource_type` 方法**: 添加此内部方法，根据文件扩展名推断 `ResourceType`。未知或特定项目类型（如 `.pet_anim`）归类为 `ResourceType.OTHER`。
- **`load_resource` 方法**: 添加通用的资源加载方法，它使用 `_get_resource_type` 判断类型并调用相应的具体加载方法（如 `load_image`, `load_json` 等）。对未知类型（归为 `OTHER`）或无法推断类型的情况，记录警告并返回 `None`。
- **`load_json` 方法**: 参数列表添加 `encoding: str = "utf-8"`，并在缓存键和文件读取中使用该编码。
- **`get_resource_info` 方法**: 添加此方法，用于获取资源的基本信息（路径、类型、大小、修改时间）。

### 2. `status/resources/cache.py`
- **`Cache.clear()` 返回值**: 修改 `clear()` 方法，使其返回被清除的条目数量 (`int`)。
- **方法改为可调用属性**: 
    - `get` -> `_default_get_impl`, 实例属性 `self.get: Callable = self._default_get_impl`
    - `put` -> `_default_put_impl`, 实例属性 `self.put: Callable = self._default_put_impl`
    - `clear` -> `_default_clear_impl`, 实例属性 `self.clear: Callable = self._default_clear_impl`
    - `remove` -> `_default_remove_impl`, 实例属性 `self.remove_method: Callable = self._default_remove_impl` (重命名以避免与list.remove冲突)
    这样修改是为了解决 `mypy` 的 `method-assign` 错误，允许这些方法在外部被安全地替换或 mock。

### 3. `status/resources/asset_manager.py`
- **调用 `cache.remove_method`**: 所有原先调用 `cache_instance.remove(...)` 的地方改为 `cache_instance.remove_method(...)`。
- **`get_resource_info` 返回类型**: 返回类型从 `Dict[str, Any]` 修改为 `Optional[Dict[str, Any]]`，并简化了其内部路径处理逻辑，更多依赖 `ResourceLoader`。
- **`__init__` 类型提示**: 为测试钩子属性 `_load_image` 和 `_load_json` 添加了 `Optional[Callable[..., Any]]` 类型提示。
- **语法和遮蔽修复**: 
    - 修复了 `get_resource_info` 中因缺失引号导致的 f-string 语法错误。
    - 将文件末尾与 `__init__` 中属性同名的 `_load_image` 和 `_load_json` *方法*分别重命名为 `_actual_load_image_impl` 和 `_actual_load_json_impl`，以解决 `mypy` 的名称遮蔽警告。
- **`Optional[ResourceType]` 处理**:
    - 在 `load_asset` 方法中，确保传递给内部方法 `_get_cache_for_type` 和回调 `cache_decision` 的 `resource_type` 参数在推断失败后默认为 `ResourceType.OTHER`，从而保证其非 `None`。
    - 在 `is_cached` 方法中，类似地，如果无法从路径推断资源类型，则默认为 `ResourceType.OTHER` 后再调用 `_get_cache_for_type`。
- **`Optional` 参数默认值修复**:
    - `preload` 方法的 `callback` 参数类型从 `Callable[...]` 改为 `Optional[Callable[...]]`。
    - `preload_group` 方法的 `paths` 参数类型从 `List[str]` 改为 `Optional[List[str]]`，并调整了方法内部逻辑以正确处理 `paths` 为 `None` 的情况。
- **`unreachable` 代码修复**:
    - 移除了 `load_asset` 方法中 `else` (即 `use_cache is False`) 分支内一个错误的、因此无法访问的 `cache.put` 调用逻辑。
    - 移除了 `load_asset` 方法中一个因类型提示已覆盖其逻辑而无法访问的 `resource_type` 验证块。

### 4. `status/resources/resource_pack.py`
- **`unreachable` 警告处理**:
    - 为 `ResourcePack.load` (约 line 189) 和 `ResourcePackManager.initialize` (约 line 503) 中的双重检查锁模式下的内部 `return True` 语句添加了 `# type: ignore[unreachable]` 注释，以消除 `mypy` 对此并发安全模式的警告。

## 最终结果
经过上述修改，`mypy status/resources/` 命令成功执行，报告 "Success: no issues found in 5 source files"。 