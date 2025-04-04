# 资源系统 API 参考

## 目录

- [模块概述](#模块概述)
- [主要类和接口](#主要类和接口)
  - [AssetManager](#assetmanager)
  - [ResourceLoader](#resourceloader)
  - [Cache](#cache)
  - [ResourcePack](#resourcepack)
- [枚举和常量](#枚举和常量)
- [工具函数](#工具函数)
- [异常类](#异常类)

## 模块概述

资源系统是Hollow-ming项目的核心基础设施之一，负责管理和加载各类资源（如图像、音频、字体等）。该系统提供了高效的资源缓存机制、灵活的资源加载器、以及强大的资源包功能，使得应用程序能够高效地管理和使用各种资源。

主要导入：

```python
from status.resources import asset_manager         # 资源管理器
from status.resources import resource_loader       # 资源加载器
from status.resources import cache                 # 缓存系统
from status.resources import resource_pack         # 资源包系统
```

## 主要类和接口

### AssetManager

资源管理器，统一管理各类资源的加载和卸载。

```python
class AssetManager
```

#### 主要方法

```python
def get_asset(self, asset_id, asset_type=None, reload=False)
```

获取指定ID的资源。

**参数**:
- `asset_id` (str): 资源ID
- `asset_type` (AssetType, 可选): 资源类型，如果为None则自动检测
- `reload` (bool): 是否强制重新加载资源，默认为False

**返回值**: 请求的资源对象

**异常**:
- `AssetLoadError`: 如果资源加载失败
- `AssetTypeError`: 如果资源类型不匹配

---

```python
def preload_assets(self, asset_ids, asset_types=None)
```

预加载一组资源。

**参数**:
- `asset_ids` (list): 要预加载的资源ID列表
- `asset_types` (list, 可选): 对应的资源类型列表

**返回值**: bool - 是否所有资源都成功预加载

### ResourceLoader

资源加载器，负责加载不同类型的资源。

```python
class ResourceLoader
```

#### 主要方法

```python
def load_resource(self, resource_path, resource_type=None)
```

加载指定路径的资源。

**参数**:
- `resource_path` (str): 资源路径
- `resource_type` (ResourceType, 可选): 资源类型，如果为None则自动检测

**返回值**: 加载的资源对象

**异常**:
- `ResourceLoadError`: 如果资源加载失败

### Cache

缓存系统，提供资源缓存功能。

```python
class Cache
```

#### 主要方法

```python
def get(self, key, loader_func=None)
```

从缓存获取项目，如果不存在则使用loader_func加载。

**参数**:
- `key` (str): 缓存键
- `loader_func` (callable, 可选): 加载函数，在缓存未命中时调用

**返回值**: 缓存的项目

### ResourcePack

资源包系统，管理资源包的加载和使用。

```python
class ResourcePack
```

#### 主要方法

```python
def load_pack(self, pack_path)
```

加载资源包。

**参数**:
- `pack_path` (str): 资源包路径

**返回值**: bool - 加载是否成功

---

```python
def get_resource(self, resource_id, resource_type=None)
```

从资源包获取资源。

**参数**:
- `resource_id` (str): 资源ID
- `resource_type` (ResourceType, 可选): 资源类型

**返回值**: 请求的资源对象

**异常**:
- `ResourceNotFoundError`: 如果资源不存在
- `ResourceTypeError`: 如果资源类型不匹配

## 枚举和常量

### AssetType

资源类型枚举。

```python
class AssetType(Enum)
```

### CachePolicy

缓存策略枚举。

```python
class CachePolicy(Enum)
```

### ResourcePackType

资源包类型枚举。

```python
class ResourcePackType(Enum)
```

## 工具函数

```python
def detect_resource_type(resource_path)
```

根据资源路径自动检测资源类型。

**参数**:
- `resource_path` (str): 资源路径

**返回值**: AssetType - 检测到的资源类型

---

```python
def create_resource_pack(pack_path, resources, pack_type=ResourcePackType.DIRECTORY)
```

创建新的资源包。

**参数**:
- `pack_path` (str): 资源包路径
- `resources` (dict): 资源字典
- `pack_type` (ResourcePackType): 资源包类型

**返回值**: bool - 创建是否成功

## 异常类

### AssetError

资源错误基类。

```python
class AssetError(Exception)
```

### AssetLoadError

资源加载错误。

```python
class AssetLoadError(AssetError)
```

### AssetTypeError

资源类型错误。

```python
class AssetTypeError(AssetError)
```

### ResourcePackError

资源包错误。

```python
class ResourcePackError(Exception)
``` 