# 资源加载进度监控机制

## 1. 背景与目标 (2025-05-15)

当前资源系统在加载大量资源或大型资源时，缺乏明确的进度反馈，可能导致用户在等待时感到应用无响应。为了提升用户体验，特别是在应用启动、场景切换或按需加载大量资源时，需要实现一套资源加载进度监控机制。

**目标**:
- 为批量资源加载操作提供基于已加载资源数量的进度反馈。
- 通过事件系统发布进度信息，方便UI或其他模块订阅和展示。
- 初期实现同步加载模式下的进度通知，为未来可能的异步加载打下基础。
- 遵循TDD流程进行开发。

## 2. 技术方案与设计

### 2.1 事件定义
将在 `status/core/events.py` (或项目中统一的事件定义位置) 定义以下事件类：

- **`ResourceLoadingBatchStartEvent`**:
    - `batch_id: str`: 唯一标识一批加载任务。
    - `total_resources: int`: 本次批量加载的总资源数。
    - `description: Optional[str]`: 可选，描述此次加载的内容 (例如 "Loading main menu assets")。

- **`ResourceLoadingProgressEvent`**:
    - `batch_id: str`: 关联的批量加载任务ID。
    - `resource_path: str`: 当前刚完成加载的资源路径。
    - `loaded_count: int`: 当前批次中已加载完成的资源数量。
    - `total_resources: int`: 当前批次的总资源数量。
    - `progress_percent: float`: 计算得出 (`loaded_count / total_resources`)。

- **`ResourceLoadingBatchCompleteEvent`**:
    - `batch_id: str`: 关联的批量加载任务ID。
    - `loaded_count: int`: 最终加载完成的资源数量。
    - `total_resources: int`: 批次的总资源数量。
    - `succeeded: bool`: 指示整个批次是否所有资源都成功加载。
    - `errors: List[Tuple[str, str]]`: 一个元组列表，包含加载失败的资源路径及其错误信息。

### 2.2 模块职责

- **`ResourceLoader`**:
    - 保持其现有职责，主要负责加载单个资源。
    - 本身不直接发布批量加载进度事件。

- **`AssetManager`**:
    - 将引入新的公共方法: `load_assets_batch(self, asset_paths: List[str], batch_description: Optional[str] = None) -> str`。
    - **主要逻辑**:
        1.  生成一个唯一的 `batch_id` (例如使用 `uuid.uuid4().hex`)。
        2.  发布 `ResourceLoadingBatchStartEvent`，包含 `batch_id`, `total_resources` (即 `len(asset_paths)`) 和 `batch_description`。
        3.  初始化 `loaded_count = 0` 和 `errors_list = []`。
        4.  遍历 `asset_paths`:
            a.  尝试使用现有的 `self.load_asset(path, ...)` 加载每个资源。
            b.  如果加载成功: `loaded_count += 1`。
            c.  如果加载失败 (例如捕获 `AssetLoadError` 或其他相关异常): 将 `(path, error_message)` 添加到 `errors_list`。
            d.  无论成功与否（只要尝试过），都发布一个 `ResourceLoadingProgressEvent`，包含当前的 `batch_id`, `path`, `loaded_count`, `total_resources`。
        5.  遍历完成后，发布 `ResourceLoadingBatchCompleteEvent`，包含 `batch_id`, `loaded_count`, `total_resources`，并根据 `errors_list` 是否为空设置 `succeeded` 字段及填充 `errors` 字段。
        6.  返回 `batch_id`。

### 2.3 TDD 测试策略
- 将在 `tests/resources/test_asset_manager_progress.py` (或类似命名的新文件) 中编写测试。
- **核心测试场景**:
    - 成功加载一批资源（例如3个），验证 `Start`, `Progress` (3次，`loaded_count` 和 `progress_percent` 递增), `Complete` (succeeded=True) 事件的正确发布和内容。
    - 加载一批资源，其中部分成功，部分失败。验证 `Progress` 事件仍按尝试次数发布，`Complete` 事件的 `succeeded=False`，且 `errors` 列表包含正确的失败信息。
    - 加载一个空资源列表，验证 `Start` 和 `Complete` (succeeded=True, loaded_count=0) 事件被正确发布，没有 `Progress` 事件。
    - 验证 `batch_id` 在同一批次的所有事件中保持一致。

## 3. 待讨论/后续考虑
- 异步加载: 当前方案是同步加载。未来可以探索将 `AssetManager.load_assets_batch`改造为异步方法，或提供异步版本。
- 取消机制: 如何取消一个正在进行的批量加载任务。
- 基于大小的进度: 当前只考虑基于数量的进度。 

## 4. 实现与测试记录 (2025-05-15)

- **事件定义 (`status/events/event_types.py`)**:
    - 创建了 `ResourceLoadingBatchStartEvent`, `ResourceLoadingProgressEvent`, `ResourceLoadingBatchCompleteEvent` 作为普通Python类，包含必要的属性和 `TYPE` 字符串常量。
    - 更新了 `ResourceEventType` 枚举以包含这些新的事件类型字符串。
- **错误定义 (`status/core/errors.py`)**:
    - 创建了 `errors.py` 文件并定义了 `AssetLoadError`, `ResourceNotFoundError`, `ResourceDecodingError`。
- **`AssetManager` 实现 (`status/resources/asset_manager.py`)**:
    - 在 `__init__` 中正确实例化 `EventManager()`。
    - 添加了 `load_assets_batch` 方法：
        - 生成唯一 `batch_id`。
        - 按设计发布 `ResourceLoadingBatchStartEvent`。
        - 循环处理资源路径，调用 `self.load_asset()`。
        - 对每个尝试加载的资源（无论成功或失败）发布 `ResourceLoadingProgressEvent`，并正确更新 `loaded_count`。
        - 收集加载错误到 `errors_list`。
        - 发布 `ResourceLoadingBatchCompleteEvent`，包含正确的 `loaded_count`, `total_resources`, `succeeded` 状态和 `errors` 列表。
    - 添加了 `clear_all_caches()` 方法用于测试清理。
- **测试 (`tests/resources/test_asset_manager_progress.py`)**:
    - 创建了 `TestAssetManagerProgress` 测试类。
    - **`test_load_assets_batch_success_events`**: 验证所有资源成功加载时的事件流和内容。 [通过]
    - **`test_load_assets_batch_partial_failure_events`**: 验证部分资源加载失败时的事件流、`CompleteEvent.succeeded = False` 和 `CompleteEvent.errors` 内容。 [通过]
    - **`test_load_assets_batch_empty_list`**: 验证空资源列表输入时，只发布 `Start` 和 `Complete` (succeeded=True, counts=0) 事件，`load_asset` 不被调用。 [通过]
    - **`test_load_assets_batch_all_fail`**: 验证所有资源加载失败时的事件流、`CompleteEvent.succeeded = False` 和 `CompleteEvent.errors` 包含所有失败信息。 [通过]
    - Fixture `mock_event_manager` 更新为模拟 `emit` 方法。
    - 测试用例中对 `emit` 参数的提取方式已修正。

**结论**: `AssetManager.load_assets_batch` 的核心功能已通过TDD实现，并能正确处理成功、部分失败、全部失败和空列表等场景下的事件发布。所有主要测试用例均已通过。 