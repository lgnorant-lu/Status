# 配置系统使用指南

## 概述

配置系统负责管理应用程序的全局设置和配置项，提供了灵活的配置管理能力，包括配置读写、验证、热重载和环境管理等功能。配置系统是应用程序的核心基础设施之一，为其他模块提供统一的配置访问接口。

## 主要特性

- **单例模式**: 确保全局唯一的配置实例
- **默认配置与用户配置分离**: 区分系统默认配置和用户自定义配置
- **配置热重载**: 监视配置文件变更并自动重新加载
- **JSON Schema验证**: 使用模式验证配置格式和值
- **点号路径访问**: 支持通过点号分隔的路径访问嵌套配置
- **配置变更事件**: 配置变更时触发回调和全局事件
- **环境特定配置**: 支持开发、测试和生产等不同环境的配置
- **差异化保存**: 仅保存与默认值不同的配置项

## 快速入门

### 基本使用

配置系统设计为单例模式，通过全局实例`config_manager`访问：

```python
from status.config import config_manager

# 初始化配置管理器
config_manager.initialize()

# 获取配置项
app_name = config_manager.get("app.name")

# 设置配置项
config_manager.set("display.width", 1024)

# 重置配置项为默认值
config_manager.reset("audio.volume")
```

### 配置热重载

配置系统支持自动监视配置文件变更并重新加载：

```python
# 启用自动重载，检查间隔为2秒
config_manager.set_auto_reload(True, interval=2)

# 禁用自动重载
config_manager.set_auto_reload(False)

# 手动重新加载配置
config_manager.reload_config()
```

### 配置变更回调

可以注册配置变更的回调函数：

```python
# 注册全局配置变更回调
def on_config_change(key, new_value, old_value, change_type):
    print(f"配置变更: {key} = {new_value} (之前为 {old_value}), 变更类型: {change_type}")

config_manager.register_change_callback(on_config_change)

# 监听特定配置项变更
config_manager.register_change_callback(lambda k, n, o, t: print(f"音量变更为 {n}"), "audio.volume")
```

### 多环境配置

配置系统支持不同环境的配置：

```python
from status.config import ConfigEnvironment

# 切换到测试环境
config_manager.set_environment(ConfigEnvironment.TESTING)

# 获取生产环境的配置
prod_config = config_manager.get_environment_config(ConfigEnvironment.PRODUCTION)
```

## 配置文件结构

系统使用多个配置文件：

- `config.json`: 用户配置文件，保存用户自定义设置
- `default_config.json`: 默认配置文件，包含所有配置项的默认值
- `config_schema.json`: 配置模式文件，定义配置的结构和验证规则
- `config.{environment}.json`: 环境特定配置文件，如`config.development.json`

配置使用JSON格式，例如：

```json
{
  "app": {
    "name": "Hollow-ming",
    "version": "0.1.0"
  },
  "display": {
    "width": 800,
    "height": 600
  }
}
```

## 高级功能

### 差异化保存

启用差异化保存后，配置系统只会保存与默认值不同的配置项：

```python
# 启用差异化保存
config_manager.set_save_diff_only(True)

# 禁用差异化保存
config_manager.set_save_diff_only(False)
```

### 配置导入/导出

配置系统支持导入和导出配置：

```python
# 导出配置到文件
config_manager.export_config("config_backup.json")

# 从文件导入配置
config_manager.import_config("config_backup.json")
```

### 默认配置锁定

为防止意外修改默认配置，系统提供了锁定机制：

```python
# 锁定默认配置（默认状态）
config_manager.lock_default_config()

# 解锁默认配置（不推荐）
config_manager.unlock_default_config()

# 设置默认配置项（需先解锁）
config_manager.set_default_config("app.name", "Custom App")
```

## API参考

### ConfigurationManager类

配置管理器类，负责管理应用程序配置。

#### 初始化

- `initialize(config_path=None, schema_path=None, default_config_path=None, auto_reload=False, reload_interval=5, save_diff_only=True, lock_default_config=True, environment=None, env_config_template=None)`: 初始化配置管理器

#### 配置访问

- `get(key, default=None)`: 获取配置项值
- `set(key, value, save=True, validate=True)`: 设置配置项值
- `delete(key, save=True)`: 删除配置项
- `reset(key=None, save=True)`: 重置配置项为默认值

#### 配置文件操作

- `load_config()`: 从文件加载配置
- `save_config()`: 保存配置到文件
- `reload_config()`: 重新加载配置文件
- `load_default_config()`: 加载默认配置
- `export_config(path=None)`: 导出配置到文件
- `import_config(path, validate=True, save=True)`: 从文件导入配置

#### 配置验证

- `set_schema(schema)`: 设置配置模式
- `validate_config(config=None)`: 验证配置是否符合模式

#### 自动重载

- `set_auto_reload(enabled, interval=None)`: 设置自动重载
- `_start_file_monitoring()`: 启动配置文件监视
- `_stop_file_monitoring()`: 停止配置文件监视

#### 配置变更通知

- `register_change_callback(callback, key="")`: 注册配置变更回调
- `unregister_change_callback(callback, key="")`: 注销配置变更回调
- `_trigger_change_event(key, new_value, old_value, change_type)`: 触发配置变更事件

#### 默认配置管理

- `lock_default_config()`: 锁定默认配置，防止修改
- `unlock_default_config()`: 解锁默认配置，允许修改
- `set_default_config(key, value)`: 设置默认配置项
- `_set_builtin_defaults()`: 设置内建默认配置

#### 环境管理

- `set_environment(environment)`: 设置当前环境并加载对应配置
- `get_environment_config(environment=None)`: 获取指定环境的配置
- `_load_environment_configs()`: 加载所有环境配置

#### 差异化保存

- `set_save_diff_only(enabled)`: 设置是否只保存与默认值不同的配置

### 枚举类型

#### ConfigChangeType

配置变更类型：

- `ConfigChangeType.ADD`: 添加新配置项
- `ConfigChangeType.MODIFY`: 修改现有配置项
- `ConfigChangeType.DELETE`: 删除配置项
- `ConfigChangeType.RELOAD`: 重新加载整个配置

#### ConfigEnvironment

配置环境类型：

- `ConfigEnvironment.DEVELOPMENT`: 开发环境
- `ConfigEnvironment.TESTING`: 测试环境
- `ConfigEnvironment.PRODUCTION`: 生产环境

### 异常类型

- `ConfigValidationError`: 配置验证错误异常

## 最佳实践

### 配置组织

1. 将相关的配置项组织在同一个命名空间下
2. 使用有意义的键名，避免太深的嵌套
3. 为可选配置提供合理的默认值

### 错误处理

1. 使用`try/except`包装配置操作，处理可能的异常
2. 验证关键配置项的合法性
3. 在加载失败时有优雅的回退策略

### 性能优化

1. 避免频繁读写配置文件
2. 缓存经常访问的配置值
3. 谨慎使用配置变更回调，避免性能开销

## 扩展开发

如果需要扩展配置系统功能，可以：

1. 继承`ConfigurationManager`类添加自定义功能
2. 通过子类化修改默认行为
3. 使用装饰器扩展现有方法

## 常见问题

### 配置系统初始化失败

检查配置文件路径是否正确，以及JSON格式是否有效。

### 配置验证错误

确认配置值符合schema中定义的类型和限制。

### 配置热重载不工作

检查文件权限和监视线程是否正常运行，可以尝试手动调用`reload_config()`方法。 