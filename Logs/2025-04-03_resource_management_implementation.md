# 资源管理系统实现日志

## 日期: 2025/04/03

## 概述

资源管理系统是Hollow-ming项目的核心组件之一，负责加载、缓存和管理各类资源，包括图像、音频、文本等。本次实现了资源管理系统的基础框架，包括资源加载器、缓存系统和资源管理器，为渲染系统和其他模块提供统一的资源访问接口。

## 系统架构

资源管理系统采用三层架构设计：

1. **资源加载器 (ResourceLoader)**：
   - 负责从文件系统加载各类资源
   - 支持多种类型资源：图像、音频、文本、JSON、CSV、字体等
   - 支持多种图像格式：PyQt6、Pillow、原始数据

2. **缓存系统 (Cache)**：
   - 实现高效的资源缓存机制
   - 支持多种缓存策略：LRU、FIFO、LFU、TTL
   - 提供自动清理过期资源的功能
   - 支持线程安全的访问

3. **资源管理器 (AssetManager)**：
   - 提供统一的资源访问接口
   - 整合资源加载器和缓存系统
   - 实现单例模式，全局唯一实例
   - 提供资源预加载、异步加载等高级功能

## 核心组件说明

### 1. 资源加载器 (ResourceLoader)

`ResourceLoader` 是资源管理系统的基础组件，负责从文件系统加载各类资源：

```python
class ResourceLoader:
    def __init__(self, base_path: str = ""):
        self.base_path = base_path
        self.logger = logging.getLogger("ResourceLoader")
        
    def load_resource(self, relative_path: str, resource_type: Optional[ResourceType] = None, 
                     **kwargs) -> Any:
        """加载资源"""
        full_path = self._get_full_path(relative_path)
        
        # 检查文件是否存在
        if not os.path.isfile(full_path):
            raise ResourceError(f"文件不存在: {full_path}")
        
        # 自动判断资源类型
        if resource_type is None:
            resource_type = self._get_resource_type(full_path)
        
        # 根据资源类型调用相应的加载函数
        try:
            if resource_type == ResourceType.IMAGE:
                return self.load_image(full_path, **kwargs)
            elif resource_type == ResourceType.AUDIO:
                return self.load_audio(full_path, **kwargs)
            # ... 其他资源类型 ...
        except Exception as e:
            raise ResourceError(f"加载资源失败 {full_path}: {str(e)}")
```

资源加载器的主要特点：

- **灵活的后端支持**：支持多种图像库（PyQt6、Pillow）和音频库（pygame）
- **自动类型检测**：根据文件扩展名自动判断资源类型
- **统一的接口**：提供统一的资源加载接口，简化上层使用
- **错误处理**：提供详细的错误信息，便于调试

### 2. 缓存系统 (Cache)

`Cache` 是资源管理系统的缓存组件，负责高效管理内存中的资源：

```python
class Cache:
    def __init__(self, 
                 strategy: CacheStrategy = CacheStrategy.LRU,
                 max_size: int = 100 * 1024 * 1024,  # 默认100MB
                 max_items: int = 1000,
                 default_ttl: float = 300,  # 默认5分钟
                 cleanup_interval: float = 60):  # 默认1分钟清理一次
        self.strategy = strategy
        self.max_size = max_size
        self.max_items = max_items
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        
        self._cache: Dict[str, CacheItem] = {}
        self._current_size = 0
        self._lock = threading.RLock()
        self._loading_locks: Dict[str, threading.Lock] = {}
        
    def get(self, key: str, default: Any = None, loader: Optional[Callable[[], Any]] = None, 
           ttl: Optional[float] = None) -> Any:
        """获取缓存项，如果不存在则返回默认值或使用加载器加载"""
        with self._lock:
            # 检查缓存项是否存在且未过期
            item = self._cache.get(key)
            if item is not None and item.status == CacheItemStatus.READY and not item.is_expired():
                item.access()
                return item.value
                
            # ... 使用加载器加载等逻辑 ...
```

缓存系统的主要特点：

- **多种缓存策略**：支持LRU、FIFO、LFU等多种缓存策略
- **内存管理**：限制缓存大小，避免内存过度使用
- **自动过期**：支持设置资源生存时间，自动清理过期资源
- **线程安全**：使用锁机制确保线程安全
- **并发加载**：支持多线程并发加载同一资源时的锁定机制

### 3. 资源管理器 (AssetManager)

`AssetManager` 是资源管理系统的顶层组件，提供统一的资源访问接口：

```python
class AssetManager:
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls) -> 'AssetManager':
        """获取单例实例"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = AssetManager()
        return cls._instance
        
    def __init__(self):
        self.loader = ResourceLoader(self.base_path)
        
        # 创建图像、音频和其他资源的缓存
        self.image_cache = Cache(
            strategy=CacheStrategy.LRU,
            max_size=200 * 1024 * 1024,  # 200MB
            default_ttl=600              # 10分钟
        )
        # ... 其他缓存初始化 ...
        
    def load_image(self, path: str, format: Optional[ImageFormat] = None,
                  scale: float = 1.0, size: Optional[Tuple[int, int]] = None,
                  use_cache: bool = True) -> Any:
        """加载图像资源"""
        return self.load_asset(
            path, 
            ResourceType.IMAGE,
            use_cache,
            format=format,
            scale=scale,
            size=size
        )
        
    def preload_async(self, paths: List[str], 
                     callback: Optional[Callable[[str, bool], None]] = None,
                     on_complete: Optional[Callable[[int, int], None]] = None) -> threading.Thread:
        """异步预加载资源"""
        # ... 异步预加载实现 ...
```

资源管理器的主要特点：

- **单例模式**：确保全局唯一实例，统一管理资源
- **分类缓存**：为图像、音频和其他资源提供单独的缓存
- **简化接口**：提供类型化的资源加载方法，简化调用
- **资源预加载**：支持同步和异步预加载资源
- **缓存管理**：提供清理、卸载和查询缓存的功能

## 实现细节

### 资源类型支持

系统实现了以下资源类型的支持：

1. **图像资源**：
   - 支持常见格式：PNG、JPG、BMP、GIF等
   - 支持多种图像库：PyQt6、Pillow
   - 支持缩放和调整大小功能

2. **音频资源**：
   - 支持常见格式：MP3、WAV、OGG等
   - 支持流式加载（适合背景音乐）和完整加载（适合音效）
   - 使用pygame库进行音频处理

3. **文本资源**：
   - 支持纯文本文件加载
   - 支持指定文件编码

4. **数据资源**：
   - 支持JSON数据加载和解析
   - 支持CSV数据加载，可以以列表或字典形式返回

5. **字体资源**：
   - 支持TTF、OTF格式
   - 支持使用PyQt6或pygame加载字体

### 缓存策略实现

缓存系统实现了多种缓存策略：

1. **LRU (最近最少使用)**：
   - 记录每个缓存项的最后访问时间
   - 当需要腾出空间时，移除最久未访问的项

2. **FIFO (先进先出)**：
   - 记录每个缓存项的创建时间
   - 当需要腾出空间时，移除最早创建的项

3. **LFU (最少使用频率)**：
   - 记录每个缓存项的访问次数
   - 当需要腾出空间时，移除访问次数最少的项

4. **TTL (基于时间)**：
   - 每个缓存项设置最大存活时间
   - 定期清理过期的缓存项

### 线程安全实现

为保证在多线程环境下正常工作，实现了以下线程安全机制：

1. **缓存锁 (RLock)**：
   - 使用可重入锁保护缓存的读写操作
   - 确保同时只有一个线程能修改缓存状态

2. **加载锁 (Lock)**：
   - 为每个正在加载的资源创建单独的锁
   - 防止多个线程同时加载同一资源
   - 实现等待机制，使得后续请求等待第一个加载完成

3. **守护线程**：
   - 使用守护线程进行缓存清理
   - 使用守护线程进行异步资源预加载

## 设计模式应用

资源管理系统应用了多种设计模式：

1. **单例模式**：
   - `AssetManager` 使用单例模式确保全局唯一实例
   - 避免资源重复加载和多份缓存

2. **策略模式**：
   - 缓存系统支持多种缓存策略
   - 可以根据需求动态切换策略

3. **工厂方法模式**：
   - `ResourceLoader` 根据资源类型选择不同的加载方法
   - 对上层代码隐藏具体的资源加载实现

4. **代理模式**：
   - `AssetManager` 作为资源操作的代理
   - 在资源访问前后添加缓存查询和存储逻辑

5. **观察者模式**：
   - 预加载功能支持回调机制
   - 允许其他组件监听资源加载状态变化

## 性能考量

资源管理系统在设计实现中考虑了以下性能因素：

1. **内存使用优化**：
   - 分类缓存，为不同类型资源设置不同的缓存大小
   - 限制最大缓存项数量和总内存使用量
   - 自动清理过期和不常用的资源

2. **加载时间优化**：
   - 资源预加载机制，提前加载可能用到的资源
   - 异步加载功能，避免阻塞主线程
   - 缓存复用，避免重复加载相同资源

3. **资源估算**：
   - 实现资源大小估算功能，特别是对图像资源
   - 根据资源特性智能调整缓存策略

4. **并发控制**：
   - 使用锁机制确保线程安全
   - 优化锁粒度，减少线程等待时间

## 未来改进

未来资源管理系统可以进一步改进的方向：

1. **异步加载改进**：
   - 使用更现代的异步机制，如asyncio
   - 支持加载优先级和加载队列

2. **资源依赖管理**：
   - 支持资源间的依赖关系
   - 实现资源包的概念，批量管理相关资源

3. **压缩和解压缩**：
   - 支持加载压缩资源
   - 实现资源压缩功能，减小存储空间

4. **资源热更新**：
   - 支持运行时更新资源
   - 实现增量更新机制

5. **更多格式支持**：
   - 添加更多资源格式的支持
   - 增加视频资源的支持

6. **资源编辑器集成**：
   - 提供与资源编辑工具的集成接口
   - 支持资源元数据管理

## 测试计划

为确保资源管理系统的稳定性和性能，制定了以下测试计划：

1. **单元测试**：
   - 测试各组件的基本功能
   - 测试边界条件和错误处理

2. **集成测试**：
   - 测试组件间的交互
   - 测试与其他系统（如渲染系统）的集成

3. **性能测试**：
   - 测试大量资源加载时的性能
   - 测试内存使用情况
   - 测试缓存命中率

4. **多线程测试**：
   - 测试多线程并发访问
   - 测试资源加载期间的线程安全性

## 文档更新

本次实现更新了以下文档：

1. 更新了`Thread.md`，标记资源管理系统基础实现为完成状态
2. 更新了`Structure.md`，添加了资源管理系统的文件结构和状态
3. 创建了本日志文件，记录资源管理系统的实现细节

## 结论

资源管理系统的基础框架已经完成，为项目提供了强大且灵活的资源管理能力。系统架构考虑了扩展性、性能和线程安全性，能够支持未来更多资源管理需求。下一步将专注于与渲染系统和场景系统的集成，以及添加更多高级资源管理功能。 