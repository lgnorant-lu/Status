# 资源管理系统

此模块提供了一个用于管理游戏资源的灵活系统，支持资源包、资源加载和缓存功能。

## 主要功能

- **资源包管理**: 支持目录和ZIP格式的资源包加载和管理
- **资源加载器**: 提供统一的资源加载接口，支持图像、声音、字体等资源类型
- **优先级系统**: 允许多个资源包之间的资源覆盖和优先级管理
- **缓存系统**: 优化资源加载性能

## 模块结构

- `resource_pack.py`: 资源包核心实现
- `resource_loader.py`: 资源加载器实现

## 使用示例

参见示例文件: `status/examples/resource_system_example.py`

```python
# 基本用法示例
from status.resources.resource_loader import resource_loader

# 初始化资源加载器
resource_loader.initialize()

# 加载图像
image = resource_loader.load_image("textures/player.png")

# 加载JSON数据
config = resource_loader.load_json("config/game.json")

# 加载文本
text = resource_loader.load_text("lang/zh_CN.txt")
```

## 资源包格式

资源包是一个包含游戏资源的目录或ZIP文件，其中必须包含一个`pack.json`元数据文件：

```json
{
    "id": "my_resource_pack",
    "name": "My Resource Pack",
    "description": "An example resource pack",
    "version": "1.0.0",
    "format_version": 2,
    "author": "Author Name"
}
```

## 测试

单元测试文件: `tests/resources/test_resource_system.py` 