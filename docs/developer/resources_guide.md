# 资源系统开发指南

## 概述

资源系统是Hollow-ming的核心组件之一，负责管理所有外部资源的加载、卸载和缓存。本指南将介绍如何使用资源系统，包括基本资源管理、资源包(Resource Pack)、缓存策略和优化技术等内容。

## 目录

- [快速入门](#快速入门)
- [资源管理器](#资源管理器)
- [资源加载器](#资源加载器)
- [缓存系统](#缓存系统)
- [资源包](#资源包)
- [异步资源加载](#异步资源加载)
- [内存管理](#内存管理)
- [优化技术](#优化技术)
- [扩展和自定义](#扩展和自定义)
- [常见问题](#常见问题)

## 快速入门

### 基本资源加载

资源系统使用资产管理器(AssetManager)来协调所有资源的加载和管理。以下是一个基本使用示例：

```python
from status.resources import asset_manager

# 获取资产管理器实例
assets = asset_manager.AssetManager.instance()

# 加载图像资源
image = assets.get_asset("images/player.png")

# 加载音频资源
sound = assets.get_asset("sounds/explosion.wav")

# 加载文本资源
text = assets.get_asset("texts/dialog.txt")
```

### 预加载资源

为了提高性能，您可以预先加载将要使用的资源：

```python
# 预加载单个资源
assets.preload_asset("images/background.jpg")

# 预加载多个资源
assets.preload_assets([
    "images/player.png",
    "images/enemy.png",
    "sounds/background_music.mp3"
])
```

### 卸载资源

当不再需要某些资源时，应该卸载它们以释放内存：

```python
# 卸载单个资源
assets.unload_asset("images/temp_image.png")

# 卸载多个资源
assets.unload_assets([
    "images/level1_background.jpg",
    "sounds/level1_music.mp3"
])

# 卸载标签分组的资源
assets.unload_assets_by_tag("level1")
```

## 资源管理器

资源管理器(AssetManager)是资源系统的中心组件，负责协调资源的加载、缓存和卸载等操作。

### 资源类型

资源管理器支持多种资源类型，每种类型都有对应的加载器：

```python
from status.resources.asset_manager import AssetType

# 图像资源
image = assets.get_asset("path/to/image.png", asset_type=AssetType.IMAGE)

# 音频资源
sound = assets.get_asset("path/to/sound.wav", asset_type=AssetType.AUDIO)

# 字体资源
font = assets.get_asset("path/to/font.ttf", asset_type=AssetType.FONT)

# JSON数据资源
data = assets.get_asset("path/to/data.json", asset_type=AssetType.JSON)

# 文本资源
text = assets.get_asset("path/to/text.txt", asset_type=AssetType.TEXT)

# 二进制资源
binary = assets.get_asset("path/to/data.bin", asset_type=AssetType.BINARY)
```

如果不指定资源类型，资源管理器会根据文件扩展名自动检测：

```python
# 自动检测资源类型
image = assets.get_asset("path/to/image.png")  # 识别为图像资源
sound = assets.get_asset("path/to/sound.wav")  # 识别为音频资源
```

### 资源路径

资源管理器使用基于项目根目录的相对路径来定位资源：

```python
# 设置资源根目录
assets.set_base_path("assets")

# 加载图像资源（实际路径为: assets/images/player.png）
image = assets.get_asset("images/player.png")
```

您还可以为不同类型的资源设置不同的子目录：

```python
# 设置不同类型资源的子目录
assets.set_type_path(AssetType.IMAGE, "images")
assets.set_type_path(AssetType.AUDIO, "sounds")
assets.set_type_path(AssetType.FONT, "fonts")

# 现在，您可以使用更短的路径
image = assets.get_asset("player.png")  # 实际路径为: assets/images/player.png
sound = assets.get_asset("explosion.wav")  # 实际路径为: assets/sounds/explosion.wav
```

### 资源标签

您可以使用标签来组织和管理资源：

```python
# 添加标签到资源
assets.tag_asset("images/player.png", "player")
assets.tag_asset("images/player.png", "character")

# 批量添加标签
assets.tag_assets(["images/level1_bg.png", "sounds/level1_music.mp3"], "level1")

# 通过标签获取资源
player_assets = assets.get_assets_by_tag("player")
level1_assets = assets.get_assets_by_tag("level1")

# 通过标签卸载资源
assets.unload_assets_by_tag("level1")
```

## 资源加载器

资源加载器(ResourceLoader)负责实际加载资源文件并将其转换为可用的对象。

### 内置加载器

系统内置了多种资源加载器：

```python
from status.resources import resource_loader

# 获取资源加载器实例
loader = resource_loader.ResourceLoader.instance()

# 手动加载图像资源
image = loader.load_resource("images/player.png", AssetType.IMAGE)

# 手动加载音频资源
sound = loader.load_resource("sounds/explosion.wav", AssetType.AUDIO)
```

### 自定义加载参数

资源加载器支持传递自定义参数到特定的加载器：

```python
# 加载图像并指定尺寸
image = loader.load_resource(
    "images/background.png", 
    AssetType.IMAGE,
    params={"size": (800, 600)}
)

# 加载音频并指定音量
sound = loader.load_resource(
    "sounds/music.mp3", 
    AssetType.AUDIO,
    params={"volume": 0.7}
)
```

### 注册自定义加载器

您可以注册自定义加载器来处理特定类型的资源：

```python
# 创建自定义加载器
class XMLLoader:
    def load(self, path, params=None):
        # 实现XML加载逻辑
        import xml.etree.ElementTree as ET
        return ET.parse(path)

# 注册自定义加载器
loader.register_loader(AssetType.XML, XMLLoader())

# 使用自定义加载器
xml_data = loader.load_resource("data/config.xml", AssetType.XML)
```

## 缓存系统

缓存系统(Cache)负责存储已加载的资源，以避免重复加载和提高性能。

### 缓存策略

系统提供了多种缓存策略：

```python
from status.resources.cache import CachePolicy

# 获取缓存系统实例
cache = assets.get_cache()

# 设置全局缓存策略（默认）
cache.set_default_policy(CachePolicy.LRU)

# 为特定资源类型设置缓存策略
cache.set_type_policy(AssetType.IMAGE, CachePolicy.LRU)
cache.set_type_policy(AssetType.AUDIO, CachePolicy.FIFO)

# 为特定资源设置缓存策略
cache.set_asset_policy("images/large_texture.png", CachePolicy.MANUAL)
```

可用的缓存策略包括：

- **LRU(最近最少使用)**：当缓存满时，移除最长时间未使用的资源
- **FIFO(先进先出)**：当缓存满时，移除最早加载的资源
- **MANUAL(手动)**：不自动清除，必须手动卸载

### 缓存大小限制

您可以设置缓存的大小限制：

```python
# 设置全局缓存大小限制（单位：字节）
cache.set_size_limit(100 * 1024 * 1024)  # 100MB

# 设置特定类型的缓存大小限制
cache.set_type_size_limit(AssetType.IMAGE, 50 * 1024 * 1024)  # 50MB
```

### 缓存状态监控

您可以监控缓存的状态和使用情况：

```python
# 获取缓存统计信息
stats = cache.get_statistics()
print(f"总缓存大小: {stats['total_size']} 字节")
print(f"缓存项数量: {stats['item_count']}")
print(f"缓存命中率: {stats['hit_rate']}%")

# 获取特定类型的缓存统计信息
image_stats = cache.get_type_statistics(AssetType.IMAGE)
print(f"图像缓存大小: {image_stats['total_size']} 字节")
```

### 手动缓存控制

您可以手动控制缓存中的项目：

```python
# 检查资源是否在缓存中
is_cached = cache.has("images/player.png")

# 从缓存中移除资源
cache.remove("images/temp.png")

# 清空缓存
cache.clear()

# 清空特定类型的缓存
cache.clear_type(AssetType.AUDIO)
```

## 资源包

资源包(ResourcePack)是一种将多个相关资源打包在一起的机制，使资源管理更加高效和灵活。

### 创建和使用资源包

```python
from status.resources import resource_pack

# 创建新的资源包
pack = resource_pack.create_resource_pack("level1_pack")

# 将资源添加到资源包
pack.add_resource("images/level1_bg.png")
pack.add_resource("images/level1_tileset.png")
pack.add_resource("sounds/level1_music.mp3")

# 保存资源包
pack.save("packs/level1.pack")

# 加载资源包
loaded_pack = resource_pack.load_resource_pack("packs/level1.pack")

# 从资源包获取资源
bg_image = loaded_pack.get_resource("images/level1_bg.png")
```

### 资源包压缩和加密

资源包支持压缩和加密功能：

```python
# 创建压缩的资源包
pack = resource_pack.create_resource_pack(
    "compressed_pack", 
    compression=True,
    compression_level=9  # 最高压缩率
)

# 创建加密的资源包
pack = resource_pack.create_resource_pack(
    "encrypted_pack", 
    encryption=True,
    encryption_key="your-secret-key"
)
```

### 注册资源包

您可以将资源包注册到资源管理器，以便直接通过资源管理器访问其中的资源：

```python
# 注册资源包到资源管理器
assets.register_resource_pack(loaded_pack)

# 现在可以直接通过资源管理器访问资源包中的资源
bg_image = assets.get_asset("images/level1_bg.png")
```

## 异步资源加载

为了避免在加载大型资源时阻塞主线程，您可以使用异步加载功能。

### 基本异步加载

```python
import asyncio

# 异步加载资源
async def load_resources():
    # 异步加载单个资源
    image = await assets.get_asset_async("images/large_background.png")
    
    # 异步预加载多个资源
    await assets.preload_assets_async([
        "images/character.png",
        "sounds/background_music.mp3",
        "models/character.obj"
    ])
    
    return image

# 在异步环境中使用
async def main():
    image = await load_resources()
    # 使用加载的资源
```

### 加载进度跟踪

您可以跟踪异步加载的进度：

```python
# 带进度报告的异步加载
async def load_with_progress():
    # 创建进度回调
    def progress_callback(path, progress, total):
        percent = (progress / total) * 100
        print(f"Loading {path}: {percent:.1f}%")
    
    # 异步预加载带进度报告
    await assets.preload_assets_async([
        "images/level2_background.png",
        "sounds/level2_music.mp3",
        "data/level2_data.json"
    ], progress_callback=progress_callback)
```

### 加载优先级

您可以为异步加载设置优先级：

```python
# 设置加载优先级
await assets.preload_assets_async([
    "images/ui_elements.png",  # 默认优先级（0）
    ("images/player.png", 10),  # 高优先级
    ("sounds/background.mp3", -5)  # 低优先级
])
```

## 内存管理

有效的内存管理是高性能应用程序的关键。资源系统提供了多种工具来管理内存使用。

### 内存使用监控

```python
# 获取资源系统内存使用情况
memory_usage = assets.get_memory_usage()
print(f"总内存使用: {memory_usage['total']} 字节")
print(f"图像资源: {memory_usage[AssetType.IMAGE]} 字节")
print(f"音频资源: {memory_usage[AssetType.AUDIO]} 字节")
```

### 自动内存管理

资源系统可以根据内存压力自动管理资源：

```python
# 启用自动内存管理
assets.enable_auto_memory_management()

# 设置内存使用阈值（触发资源卸载的阈值）
assets.set_memory_threshold(0.75)  # 当内存使用超过75%时触发卸载
```

### 内存使用优化

```python
# 卸载长时间未使用的资源
assets.unload_unused(timeout=300)  # 卸载5分钟未使用的资源

# 生成内存使用报告
report = assets.generate_memory_report()
for entry in report:
    print(f"{entry['path']}: {entry['size']} 字节, 最后使用: {entry['last_used']}")

# 手动触发垃圾回收
assets.collect_garbage()
```

## 优化技术

### 资源池

对于频繁创建和销毁的资源，可以使用资源池来提高性能：

```python
from status.resources import resource_pool

# 创建资源池
bullet_texture_pool = resource_pool.ResourcePool("images/bullet.png", max_size=50)

# 从池中获取资源
bullet_texture = bullet_texture_pool.get()

# 使用完后归还资源
bullet_texture_pool.release(bullet_texture)
```

### 资源分组与批量处理

将相关资源分组处理可以提高加载效率：

```python
# 创建资源组
assets.create_group("level1", [
    "images/level1_bg.png",
    "images/level1_tileset.png",
    "sounds/level1_music.mp3"
])

# 加载整个资源组
assets.load_group("level1")

# 卸载整个资源组
assets.unload_group("level1")
```

### 资源热替换

在开发过程中，资源热替换可以不重启应用程序就更新资源：

```python
# 启用资源热替换（开发模式）
assets.enable_hot_reload()

# 设置热替换回调
def on_resource_changed(path):
    print(f"资源已更新: {path}")
    # 更新使用该资源的对象
    
assets.set_hot_reload_callback(on_resource_changed)
```

## 扩展和自定义

### 创建自定义资源类型

您可以通过以下方式添加对新资源类型的支持：

1. 创建新的资源类型枚举值
2. 实现加载器
3. 注册加载器到系统

```python
# 1. 扩展资源类型枚举
class CustomAssetType(AssetType):
    SHADER = "shader"

# 2. 实现加载器
class ShaderLoader:
    def load(self, path, params=None):
        with open(path, 'r') as file:
            shader_code = file.read()
        # 编译着色器等处理逻辑
        return compiled_shader

# 3. 注册加载器
loader = resource_loader.ResourceLoader.instance()
loader.register_loader(CustomAssetType.SHADER, ShaderLoader())

# 使用新的资源类型
shader = assets.get_asset("shaders/bloom.glsl", asset_type=CustomAssetType.SHADER)
```

### 自定义缓存行为

您可以创建自定义缓存策略：

```python
from status.resources.cache import BaseCachePolicy

class TimeLimitedPolicy(BaseCachePolicy):
    def __init__(self, time_limit=3600):  # 默认1小时
        self.time_limit = time_limit
        self.timestamps = {}
        
    def on_access(self, key):
        # 更新访问时间戳
        self.timestamps[key] = time.time()
    
    def select_victim(self, cache_items):
        current_time = time.time()
        # 选择超过时间限制的项目
        for key, item in cache_items.items():
            if current_time - self.timestamps.get(key, 0) > self.time_limit:
                return key
        # 如果没有超时项目，回退到LRU策略
        return min(self.timestamps, key=self.timestamps.get)

# 注册自定义缓存策略
cache = assets.get_cache()
cache.register_policy("time_limited", TimeLimitedPolicy(time_limit=1800))  # 30分钟

# 使用自定义缓存策略
cache.set_type_policy(AssetType.AUDIO, "time_limited")
```

## 常见问题

### 问题：资源加载缓慢

**解决方案**:
- 启用资源预加载
- 使用异步加载机制
- 检查资源大小和格式
- 利用资源包减少文件I/O操作
- 启用资源压缩

### 问题：内存使用过高

**解决方案**:
- 适时卸载不需要的资源
- 设置合理的缓存大小限制
- 使用合适的缓存策略
- 监控资源系统内存使用
- 考虑使用资源池管理

### 问题：资源路径错误

**解决方案**:
- 检查资源路径是否正确
- 确认资源基础路径设置
- 验证文件是否存在
- 使用绝对路径测试
- 检查资源类型与路径是否匹配 