# 资源压缩与优化

## 1. 背景与目标

当前资源管理系统 (ResourceLoader, AssetManager) 虽然已具备缓存和热加载等功能，但缺乏对资源本身的压缩和优化机制。这可能导致：
- **较大的内存占用**：尤其对于图像、音频等大型资源。
- **较长的加载时间**：特别是对于未缓存的资源或首次启动应用时。
- **较大的存储空间占用**：如果资源包本身很大。

**目标**：
- 实现通用的资源压缩/解压缩机制，支持常见资源类型（如图像、JSON、文本）。
- 提供API层面的支持，允许开发者在加载和保存资源时选择是否启用压缩。
- 优化资源加载流程，在不显著增加CPU负担的前提下，减少内存占用和加载时间。
- 保持对现有资源加载API的兼容性。

## 2. 技术方案与设计

### 2.1 压缩算法选择
- **通用数据**: `zlib` (或 `gzip`) 是一个不错的选择，Python标准库内置支持，压缩率和速度均衡。
- **图像**: 
    - PNG: 本身是无损压缩。可以考虑使用如 `optipng` 或类似库进行进一步优化（元数据剥离，更优的DEFLATE参数）。
    - JPEG: 有损压缩。可以在保存时调整质量参数。
    - WebP: 可以提供更好的压缩率，但需要额外依赖。
- **JSON/Text**: `zlib` 同样适用。

### 2.2 实现层面

- **`ResourceType` 扩展**: 
    - 可能需要区分原始类型和压缩后的类型，或者在元数据中标记压缩状态。
- **`ResourceLoader`**: 
    - `load_resource()`: 增加 `compressed: bool` 或 `compression_type: Optional[str]` 参数。
    - `_get_resource_content()`: 如果检测到是压缩资源，则在返回前解压。
    - 新增 `save_resource_content(path: str, data: bytes, compress: bool = False)` (或类似方法) 用于支持带压缩的保存。
- **`AssetManager`**: 
    - 对应 `load_asset()` 等方法也需要透传压缩相关参数。
    - 需要考虑缓存机制如何处理压缩资源（是缓存原始数据还是解压后的数据）。缓存解压后的数据可以提高后续访问速度，但会增加缓存大小；缓存压缩数据则相反。
        - 初步考虑：优先缓存解压后的数据，但提供选项或策略进行调整。
- **元数据**: 考虑在资源包的manifest或单独的元数据文件中存储资源的压缩信息、原始大小等。

## 3. 开发计划 (TDD)

1.  **测试用例编写 (`tests/resources/test_resource_compression.py`)**:
    *   测试文本、JSON、简单图像资源的压缩与解压缩。
    *   测试 `ResourceLoader` 和 `AssetManager` 加载压缩资源和普通资源。
    *   测试带压缩选项的资源保存。
    *   测试缓存对压缩资源的处理。
    *   测试错误处理（如损坏的压缩数据）。
2.  **`ResourceType` 扩展 (如果需要)**。
3.  **`ResourceLoader` 实现**: 
    *   添加 `_compress_data(data: bytes, algorithm: str = 'zlib') -> bytes` 和 `_decompress_data(data: bytes, algorithm: str = 'zlib') -> bytes` 内部辅助方法。
    *   修改 `get_resource_content` 和 `load_resource` 以支持解压缩。
    *   添加资源保存时的压缩逻辑。
4.  **`AssetManager` 实现**: 
    *   将压缩参数传递给 `ResourceLoader`。
    *   调整缓存逻辑以适应压缩资源。
5.  **集成测试与性能评估**。
6.  **文档更新**。

## 4. 待讨论点

- 默认压缩行为：是否对某些类型的资源默认启用压缩？
- 压缩级别：是否允许配置压缩级别（空间换时间）？
- 异步压缩/解压缩：对于非常大的资源，是否需要异步处理以避免阻塞主线程？ 

## 5. 实现与测试记录 (2025-05-15)

- **完成 `ResourceLoader` 中的 `_compress_data` 和 `_decompress_data` 方法** (使用 `zlib`)。
- **修改 `ResourceLoader.load_resource`**:
    - 添加 `compressed: bool` 和 `compression_type: str` 参数。
    - 集成解压缩逻辑：如果 `compressed=True`，则调用 `_decompress_data`。
    - 如果解压缩失败 (例如 `zlib.error`)，会重新抛出原始异常。
- **添加 `ResourceLoader.save_resource_content` 方法**，支持在保存时进行压缩。
- **在 `status/resources/__init__.py` 中添加 `ResourceType.BINARY`** 以支持原始字节数据处理。
- **修复 `AssetManager.__init__`**，确保在单例模式下其初始化逻辑只完整执行一次 (通过 `_initialized` 标志)。
- **修改 `AssetManager.load_asset`**，确保在调用 `self.loader.load_resource` 时正确传递 `resource_type` 作为关键字参数。

- **测试 (`tests/resources/test_resource_compression.py`)**:
    - `test_compress_decompress_text` 和 `test_compress_decompress_json`: 通过。
    - `test_resource_loader_load_compressed_text` 和 `test_resource_loader_load_uncompressed_text`: 通过。
    - `test_resource_loader_save_compressed_text` 和 `test_resource_loader_save_uncompressed_text`: 通过。
    - `test_asset_manager_load_compressed_text`: 通过 (在修复 `AssetManager.load_asset` 的 `resource_type` 传递后)。
    - `test_asset_manager_load_uncompressed_text`: 通过。
    - `test_cache_with_compressed_resources`: **失败并已跳过**。该测试预期 `mock_resource_manager.get_resource_content` 在第二次加载（应从缓存读取）时不会被调用，但实际上被调用了两次。详细信息已记录在 `Issues.md`。

- **结论**: 核心的资源压缩/解压缩功能已在 `ResourceLoader` 中实现，并通过了大部分单元测试。`AssetManager` 也已适配以支持加载压缩资源。一个与缓存相关的测试用例 (`test_cache_with_compressed_resources`) 暂时失败并被跳过，需要进一步调查。整体任务状态为"待完善"。 