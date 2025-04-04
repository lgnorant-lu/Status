# 配置系统开发指南

## 概述

配置系统是Hollow-ming的核心基础设施之一，用于管理应用程序的全局设置和参数。本指南将详细介绍如何在开发过程中使用配置系统，包括基本用法、最佳实践和高级功能。

## 目录

- [快速入门](#快速入门)
- [配置文件](#配置文件)
- [基本功能](#基本功能)
- [高级功能](#高级功能)
- [多环境配置](#多环境配置)
- [版本控制与升级](#版本控制与升级)
- [配置验证](#配置验证)
- [单元测试](#单元测试)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

## 快速入门

### 导入配置管理器

首先，从`status.config`模块导入全局配置管理器实例：

```python
from status.config import config_manager
```

### 读取和设置配置

配置系统支持通过点号分隔的路径访问嵌套配置：

```python
# 获取配置值
app_name = config_manager.get("app.name")
debug_mode = config_manager.get("app.debug", False)  # 提供默认值

# 设置配置值
config_manager.set("display.width", 1024)
config_manager.set("app.theme", "dark")
```

### 重置配置

恢复默认配置：

```python
# 重置特定配置项
config_manager.reset("audio.volume")

# 重置所有配置
config_manager.reset()
```

## 配置文件

配置系统使用以下配置文件：

- **config.json**: 用户配置文件，保存用户自定义设置
- **default_config.json**: 默认配置文件，包含所有配置项的默认值
- **config_schema.json**: 配置模式文件，定义配置的结构和验证规则
- **config.{environment}.json**: 环境特定配置文件

### 标准配置结构

配置使用嵌套的JSON对象结构：

```json
{
  "version": "1.0.0",
  "app": {
    "name": "Hollow-ming",
    "version": "0.1.0",
    "debug": false
  },
  "display": {
    "width": 800,
    "height": 600,
    "fullscreen": false
  }
}
```

## 基本功能

### 配置访问

配置系统提供了多种访问和修改配置的方法：

```python
# 获取配置值，支持点号分隔的路径
value = config_manager.get("category.subcategory.key")

# 设置配置值
config_manager.set("category.subcategory.key", new_value)

# 删除配置项
config_manager.delete("category.unused_key")

# 检查配置项是否存在
if config_manager.get("feature.experimental") is not None:
    # 配置项存在...
```

### 配置保存与加载

```python
# 加载配置（通常在初始化时自动调用）
config_manager.load_config()

# 保存配置（通常在调用set时自动保存）
config_manager.save_config()

# 导出配置到特定文件
config_manager.export_config("backup_config.json")

# 从文件导入配置
config_manager.import_config("backup_config.json")
```

### 配置热重载

配置系统支持自动监视配置文件变更并重新加载：

```python
# 启用配置热重载
config_manager.set_auto_reload(True, interval=2.0)

# 禁用自动重载
config_manager.set_auto_reload(False)

# 手动触发重载
config_manager.reload_config()
```

## 高级功能

### 变更通知

注册回调函数监听配置变更：

```python
# 监听所有配置变更
def global_config_changed(key, new_value, old_value, change_type):
    print(f"配置变更: {key} = {new_value} (之前: {old_value}), 类型: {change_type}")

config_manager.register_change_callback(global_config_changed)

# 监听特定配置项变更
def volume_changed(key, new_value, old_value, change_type):
    print(f"音量已调整为 {new_value}")

config_manager.register_change_callback(volume_changed, "audio.volume")

# 注销回调
config_manager.unregister_change_callback(volume_changed, "audio.volume")
```

### 差异化保存

配置系统支持仅保存与默认值不同的配置项，减小配置文件大小：

```python
# 启用差异化保存（默认启用）
config_manager.set_save_diff_only(True)

# 禁用差异化保存
config_manager.set_save_diff_only(False)
```

### 默认配置保护

保护关键配置项防止被用户配置覆盖：

```python
# 保护配置项
config_manager.protect_key("app.version")
config_manager.protect_key("app.api_keys.production")

# 取消保护
config_manager.unprotect_key("app.version")
```

## 多环境配置

配置系统支持在不同环境（开发、测试、生产）间切换：

```python
from status.config import ConfigEnvironment

# 切换环境
config_manager.set_environment(ConfigEnvironment.TESTING)

# 获取特定环境的配置
prod_config = config_manager.get_environment_config(ConfigEnvironment.PRODUCTION)
```

### 环境配置文件

每个环境可以有自己的配置文件，命名格式为`config.{environment}.json`：

- `config.development.json`: 开发环境配置
- `config.testing.json`: 测试环境配置
- `config.production.json`: 生产环境配置

环境配置将与默认配置和用户配置合并，优先级为：默认配置 < 环境配置 < 用户配置。

## 版本控制与升级

配置系统支持版本控制和配置格式升级：

### 版本标记

在配置中添加版本信息：

```json
{
  "version": "1.0.0",
  "app": {
    // ...
  }
}
```

### 注册升级处理器

```python
# 从1.0.0升级到1.1.0的处理函数
def upgrade_1_0_0_to_1_1_0(old_config, old_version, new_version):
    new_config = old_config.copy()
    
    # 添加新的必需字段
    if "logging" not in new_config:
        new_config["logging"] = {"level": "info"}
    
    # 重命名字段
    if "display" in new_config and "size" in new_config["display"]:
        size = new_config["display"].pop("size")
        new_config["display"]["width"] = size
        new_config["display"]["height"] = int(size * 0.75)
    
    return new_config

# 注册升级处理器
config_manager.register_version_upgrade("1.0.0", "1.1.0", upgrade_1_0_0_to_1_1_0)
```

## 配置验证

配置系统支持使用JSON Schema验证配置：

### 设置验证模式

```python
# 设置验证模式
schema = {
    "type": "object",
    "required": ["app"],
    "properties": {
        "app": {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "debug": {"type": "boolean"}
            }
        },
        "display": {
            "type": "object",
            "properties": {
                "width": {"type": "integer", "minimum": 640},
                "height": {"type": "integer", "minimum": 480}
            }
        }
    }
}

config_manager.set_schema(schema)
```

### 手动验证

```python
from status.config import ConfigValidationError

try:
    # 验证当前配置
    config_manager.validate_config()
    
    # 验证特定配置对象
    config_manager.validate_config(test_config)
except ConfigValidationError as e:
    print(f"配置验证失败: {e}")
```

### 使用验证器类

```python
from status.config import ConfigValidator, ConfigValidationError

try:
    # 使用JSON Schema验证
    ConfigValidator.validate_with_schema(config, schema)
    
    # 验证配置类型
    ConfigValidator.validate_types(config, {
        "name": str,
        "count": int,
        "enabled": bool
    })
    
    # 验证必需字段
    ConfigValidator.validate_required(config, ["name", "version"])
    
    # 验证版本
    ConfigValidator.validate_version(config, min_version="1.0.0", max_version="2.0.0")
except ConfigValidationError as e:
    print(f"验证错误: {e}")
```

## 单元测试

配置系统提供了多种方式用于单元测试：

### 方法一：使用临时文件

```python
import tempfile
import json
import os

def test_config_functionality():
    # 创建临时配置文件
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "config.json")
        default_config_path = os.path.join(temp_dir, "default_config.json")
        
        # 写入测试配置
        with open(config_path, 'w') as f:
            json.dump({"app": {"name": "Test App"}}, f)
            
        with open(default_config_path, 'w') as f:
            json.dump({"app": {"name": "Default App", "debug": False}}, f)
        
        # 重置单例（仅用于测试）
        from status.config import ConfigurationManager
        ConfigurationManager._instance = None
        
        # 创建新实例并初始化
        from status.config import config_manager
        config_manager.initialize(
            config_path=config_path,
            default_config_path=default_config_path
        )
        
        # 执行测试
        assert config_manager.get("app.name") == "Test App"
        assert config_manager.get("app.debug") == False
```

### 方法二：使用模拟对象

```python
from unittest.mock import patch, MagicMock

def test_with_mocks():
    # 模拟配置管理器
    with patch('status.config.ConfigurationManager') as MockConfigManager:
        mock_instance = MagicMock()
        MockConfigManager.return_value = mock_instance
        mock_instance.get.return_value = "mocked_value"
        
        # 导入配置管理器
        from status.config import config_manager
        
        # 执行测试
        result = config_manager.get("test.key")
        assert result == "mocked_value"
        mock_instance.get.assert_called_once_with("test.key")
```

## 最佳实践

### 配置组织

1. **使用命名空间**: 将相关配置项放在同一个命名空间下
   ```json
   {
     "audio": {
       "master_volume": 0.8,
       "music_volume": 0.5,
       "effects_volume": 1.0
     }
   }
   ```

2. **避免过深嵌套**: 嵌套不应超过3-4层，以保持可读性和易用性

3. **有意义的键名**: 使用描述性的键名，避免缩写和模糊的名称

### 配置访问

1. **提供默认值**: 在使用`get`方法时总是提供默认值
   ```python
   # 好的做法
   debug = config_manager.get("app.debug", False)
   
   # 不推荐（可能导致None值）
   debug = config_manager.get("app.debug")
   ```

2. **批量操作**: 使用变量缓存频繁访问的配置，避免重复查询
   ```python
   # 缓存配置
   display_config = {
       "width": config_manager.get("display.width", 800),
       "height": config_manager.get("display.height", 600),
       "fullscreen": config_manager.get("display.fullscreen", False)
   }
   
   # 使用缓存的配置
   width = display_config["width"]
   ```

### 错误处理

1. **验证关键配置**: 在应用启动时验证关键配置项
   ```python
   # 验证配置
   try:
       config_manager.validate_config()
   except ConfigValidationError as e:
       logging.error(f"配置验证失败: {e}")
       # 优雅降级或使用默认配置
       config_manager.reset()
   ```

2. **处理访问失败**: 处理配置项不存在的情况
   ```python
   # 使用默认值处理不存在的配置项
   volume = config_manager.get("audio.volume", 0.5)
   ```

### 性能考虑

1. **避免频繁写入**: 减少保存操作，特别是在批量更改时
   ```python
   # 批量更改时禁用自动保存
   config_manager.set("display.width", 1024, save=False)
   config_manager.set("display.height", 768, save=False)
   config_manager.set("display.fullscreen", True, save=True)  # 最后一个变更时保存
   ```

2. **谨慎使用热重载**: 在性能敏感的场景中谨慎使用自动重载
   ```python
   # 使用较长的间隔减少文件系统检查
   config_manager.set_auto_reload(True, interval=10.0)
   ```

## 常见问题

### 配置未保存

**问题**: 修改的配置没有保存到文件

**解决方案**:
- 确认`set`方法的`save`参数为`True`
- 确认配置文件路径正确且有写入权限
- 手动调用`save_config()`确保保存

### 配置重载失败

**问题**: 配置文件变更后未自动重新加载

**解决方案**:
- 确认已启用自动重载：`set_auto_reload(True)`
- 检查监视间隔是否合理
- 确保文件系统支持修改时间检测
- 尝试手动调用`reload_config()`

### 环境配置不生效

**问题**: 环境特定配置未应用

**解决方案**:
- 检查环境配置文件名是否正确（如`config.development.json`）
- 确认已设置正确的环境：`set_environment(ConfigEnvironment.DEVELOPMENT)`
- 检查环境配置文件的格式是否正确

### 配置验证错误

**问题**: 遇到配置验证错误

**解决方案**:
- 检查配置项是否符合架构定义
- 查看错误消息了解具体的验证失败原因
- 临时禁用验证：`set(key, value, validate=False)`
- 更新验证架构以适应新的配置格式 