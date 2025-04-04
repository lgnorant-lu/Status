# 配置系统 API 参考

## 目录

- [模块概述](#模块概述)
- [ConfigurationManager](#configurationmanager)
  - [初始化](#初始化)
  - [配置访问](#配置访问)
  - [配置文件操作](#配置文件操作)
  - [配置验证](#配置验证)
  - [自动重载](#自动重载)
  - [配置变更通知](#配置变更通知)
  - [默认配置管理](#默认配置管理)
  - [环境管理](#环境管理)
  - [差异化保存](#差异化保存)
  - [版本控制](#版本控制)
- [ConfigChangeType](#configchangetype)
- [ConfigEnvironment](#configenvironment)
- [ConfigDiff](#configdiff)
- [ConfigValidator](#configvalidator)
- [异常类](#异常类)
- [全局实例](#全局实例)

## 模块概述

配置系统模块提供了一个统一的接口来管理应用程序配置。核心功能包括配置加载、保存、监视、验证和变更通知。该模块使用单例模式确保在整个应用程序中使用相同的配置实例。

主要导入：

```python
from status.config import config_manager                  # 全局配置管理器实例
from status.config import ConfigurationManager            # 配置管理器类
from status.config import ConfigChangeType                # 配置变更类型枚举
from status.config import ConfigEnvironment               # 配置环境枚举
from status.config import ConfigDiff                      # 配置差异工具类
from status.config import ConfigValidator                 # 配置验证器类
from status.config import ConfigValidationError           # 配置验证错误
from status.config import ConfigVersionError              # 配置版本错误
```

## ConfigurationManager

主要配置管理类，实现单例模式。

### 初始化

```python
def __init__(self, config_path=None, default_config_path=None, schema_path=None, auto_create=True)
```

**参数**:
- `config_path` (str, 可选): 配置文件路径，默认为"config.json"
- `default_config_path` (str, 可选): 默认配置文件路径，默认为"default_config.json"
- `schema_path` (str, 可选): 配置模式文件路径，默认为"config_schema.json"
- `auto_create` (bool): 如果配置文件不存在，是否自动创建，默认为True

**返回值**: 无

**异常**:
- `FileNotFoundError`: 如果文件不存在且`auto_create=False`
- `json.JSONDecodeError`: 如果配置文件包含无效的JSON

---

```python
def initialize(self, config_path=None, default_config_path=None, schema_path=None, auto_create=True)
```

重新初始化配置管理器。

**参数**:
- `config_path` (str, 可选): 配置文件路径
- `default_config_path` (str, 可选): 默认配置文件路径
- `schema_path` (str, 可选): 配置模式文件路径
- `auto_create` (bool): 如果配置文件不存在，是否自动创建

**返回值**: 无

**异常**:
- `FileNotFoundError`: 如果文件不存在且`auto_create=False`
- `json.JSONDecodeError`: 如果配置文件包含无效的JSON

### 配置访问

```python
def get(self, key, default=None)
```

获取配置值。

**参数**:
- `key` (str): 点分隔的配置键路径
- `default` (任意类型, 可选): 如果键不存在，返回的默认值

**返回值**: 配置值或默认值

---

```python
def set(self, key, value, save=True, validate=True)
```

设置配置值。

**参数**:
- `key` (str): 点分隔的配置键路径
- `value` (任意类型): 要设置的值
- `save` (bool): 是否保存更改到配置文件，默认为True
- `validate` (bool): 是否在设置后验证配置，默认为True

**返回值**: 无

**异常**:
- `ConfigValidationError`: 如果验证失败
- `ConfigKeyProtectedError`: 如果尝试修改受保护的键

---

```python
def reset(self, key=None)
```

重置配置项到默认值。

**参数**:
- `key` (str, 可选): 要重置的配置键。如果为None，重置所有配置

**返回值**: 无

---

```python
def delete(self, key, save=True, validate=True)
```

删除配置项。

**参数**:
- `key` (str): 点分隔的配置键路径
- `save` (bool): 是否保存更改到配置文件，默认为True
- `validate` (bool): 是否在删除后验证配置，默认为True

**返回值**: 无

**异常**:
- `ConfigValidationError`: 如果验证失败
- `ConfigKeyProtectedError`: 如果尝试删除受保护的键

---

```python
def has(self, key)
```

检查配置键是否存在。

**参数**:
- `key` (str): 点分隔的配置键路径

**返回值**: bool - 键是否存在

### 配置文件操作

```python
def load_config(self)
```

从文件中加载配置。

**返回值**: 无

**异常**:
- `FileNotFoundError`: 如果配置文件不存在
- `json.JSONDecodeError`: 如果文件包含无效的JSON

---

```python
def save_config(self)
```

将当前配置保存到文件。

**返回值**: 无

**异常**:
- `IOError`: 如果文件无法写入

---

```python
def reload_config(self)
```

重新加载配置文件并触发变更事件。

**返回值**: 无

---

```python
def export_config(self, filepath, include_defaults=False)
```

将当前配置导出到指定文件。

**参数**:
- `filepath` (str): 导出文件路径
- `include_defaults` (bool): 是否包含默认值，默认为False

**返回值**: 无

**异常**:
- `IOError`: 如果文件无法写入

---

```python
def import_config(self, filepath, validate=True, save=True)
```

从文件导入配置。

**参数**:
- `filepath` (str): 导入文件路径
- `validate` (bool): 是否验证导入的配置，默认为True
- `save` (bool): 是否保存导入的配置，默认为True

**返回值**: 无

**异常**:
- `FileNotFoundError`: 如果文件不存在
- `json.JSONDecodeError`: 如果文件包含无效的JSON
- `ConfigValidationError`: 如果验证失败

### 配置验证

```python
def set_schema(self, schema)
```

设置配置验证模式。

**参数**:
- `schema` (dict): JSON Schema对象

**返回值**: 无

---

```python
def validate_config(self, config=None)
```

验证配置与模式一致。

**参数**:
- `config` (dict, 可选): 要验证的配置，如果为None则使用当前配置

**返回值**: bool - 验证是否成功

**异常**:
- `ConfigValidationError`: 如果验证失败

### 自动重载

```python
def set_auto_reload(self, enabled, interval=2.0)
```

启用或禁用配置文件自动重载。

**参数**:
- `enabled` (bool): 是否启用自动重载
- `interval` (float): 检查间隔秒数，默认为2.0

**返回值**: 无

### 配置变更通知

```python
def register_change_callback(self, callback, key=None)
```

注册配置变更回调函数。

**参数**:
- `callback` (callable): 回调函数，接受四个参数：key, new_value, old_value, change_type
- `key` (str, 可选): 监听的特定键，如果为None则监听所有变更

**返回值**: 无

---

```python
def unregister_change_callback(self, callback, key=None)
```

注销配置变更回调函数。

**参数**:
- `callback` (callable): 要注销的回调函数
- `key` (str, 可选): 特定键，如果为None则从全局回调中注销

**返回值**: 无

### 默认配置管理

```python
def load_default_config(self)
```

加载默认配置文件。

**返回值**: 无

**异常**:
- `FileNotFoundError`: 如果默认配置文件不存在
- `json.JSONDecodeError`: 如果文件包含无效的JSON

---

```python
def get_default(self, key, default=None)
```

获取默认配置值。

**参数**:
- `key` (str): 点分隔的配置键路径
- `default` (任意类型, 可选): 如果键不存在，返回的默认值

**返回值**: 默认配置值或指定的默认值

---

```python
def protect_key(self, key)
```

保护配置键不被修改。

**参数**:
- `key` (str): 要保护的配置键

**返回值**: 无

---

```python
def unprotect_key(self, key)
```

取消对配置键的保护。

**参数**:
- `key` (str): 要取消保护的配置键

**返回值**: 无

---

```python
def is_protected(self, key)
```

检查配置键是否受保护。

**参数**:
- `key` (str): 要检查的配置键

**返回值**: bool - 键是否受保护

### 环境管理

```python
def set_environment(self, environment, reload_config=True)
```

设置当前配置环境。

**参数**:
- `environment` (ConfigEnvironment): 配置环境
- `reload_config` (bool): 是否重新加载配置，默认为True

**返回值**: 无

---

```python
def get_environment(self)
```

获取当前配置环境。

**返回值**: ConfigEnvironment - 当前环境

---

```python
def get_environment_config(self, environment)
```

获取特定环境的配置。

**参数**:
- `environment` (ConfigEnvironment): 配置环境

**返回值**: dict - 环境配置

**异常**:
- `FileNotFoundError`: 如果环境配置文件不存在

### 差异化保存

```python
def set_save_diff_only(self, enabled)
```

设置是否仅保存与默认值不同的配置项。

**参数**:
- `enabled` (bool): 是否启用差异化保存

**返回值**: 无

---

```python
def get_config_diff(self)
```

获取当前配置与默认配置的差异。

**返回值**: dict - 差异配置

### 版本控制

```python
def register_version_upgrade(self, old_version, new_version, upgrade_func)
```

注册版本升级处理函数。

**参数**:
- `old_version` (str): 旧版本号
- `new_version` (str): 新版本号
- `upgrade_func` (callable): 升级函数，接受三个参数：old_config, old_version, new_version

**返回值**: 无

---

```python
def check_version_mismatch(self, user_config, default_config)
```

检查用户配置和默认配置的版本不匹配。

**参数**:
- `user_config` (dict): 用户配置
- `default_config` (dict): 默认配置

**返回值**: tuple - (bool是否需要升级, str当前版本, str目标版本)

---

```python
def find_upgrade_path(self, from_version, to_version)
```

查找从一个版本到另一个版本的升级路径。

**参数**:
- `from_version` (str): 起始版本
- `to_version` (str): 目标版本

**返回值**: list - 升级步骤的列表

**异常**:
- `ConfigVersionError`: 如果找不到有效的升级路径

## ConfigChangeType

配置变更类型的枚举。

```python
class ConfigChangeType(Enum):
    SET = "set"           # 设置值
    DELETE = "delete"     # 删除键
    RESET = "reset"       # 重置为默认值
    RELOAD = "reload"     # 重新加载配置
    IMPORT = "import"     # 导入配置
```

## ConfigEnvironment

配置环境的枚举。

```python
class ConfigEnvironment(Enum):
    DEFAULT = "default"           # 默认环境
    DEVELOPMENT = "development"   # 开发环境
    TESTING = "testing"           # 测试环境
    PRODUCTION = "production"     # 生产环境
```

## ConfigDiff

配置差异工具类。

```python
@staticmethod
def get_diff(config, default_config)
```

获取配置与默认配置的差异。

**参数**:
- `config` (dict): 当前配置
- `default_config` (dict): 默认配置

**返回值**: dict - 仅包含与默认值不同的配置项

---

```python
@staticmethod
def merge_configs(base_config, override_config, protected_keys=None)
```

合并两个配置对象。

**参数**:
- `base_config` (dict): 基础配置
- `override_config` (dict): 覆盖配置
- `protected_keys` (list, 可选): 不应被覆盖的保护键列表

**返回值**: dict - 合并后的配置

## ConfigValidator

配置验证器类。

```python
@staticmethod
def validate_with_schema(config, schema)
```

使用JSON Schema验证配置。

**参数**:
- `config` (dict): 要验证的配置
- `schema` (dict): JSON Schema

**返回值**: bool - 验证是否成功

**异常**:
- `ConfigValidationError`: 如果验证失败

---

```python
@staticmethod
def validate_types(config, type_map)
```

验证配置项类型。

**参数**:
- `config` (dict): 要验证的配置
- `type_map` (dict): 键到类型的映射

**返回值**: bool - 验证是否成功

**异常**:
- `ConfigValidationError`: 如果验证失败

---

```python
@staticmethod
def validate_required(config, required_keys)
```

验证必需的配置键。

**参数**:
- `config` (dict): 要验证的配置
- `required_keys` (list): 必需键的列表

**返回值**: bool - 验证是否成功

**异常**:
- `ConfigValidationError`: 如果验证失败

---

```python
@staticmethod
def validate_version(config, min_version=None, max_version=None)
```

验证配置版本。

**参数**:
- `config` (dict): 要验证的配置
- `min_version` (str, 可选): 最小版本要求
- `max_version` (str, 可选): 最大版本要求

**返回值**: bool - 验证是否成功

**异常**:
- `ConfigValidationError`: 如果验证失败
- `ConfigVersionError`: 如果版本不兼容

## 异常类

### ConfigError

所有配置错误的基类。

---

### ConfigValidationError

配置验证错误。

---

### ConfigVersionError

配置版本错误。

---

### ConfigKeyProtectedError

尝试修改受保护键时的错误。

## 全局实例

```python
config_manager
```

全局配置管理器实例，使用默认设置初始化。 