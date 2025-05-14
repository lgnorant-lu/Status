# Status-Ming 插件开发指南

**版本**: 1.0.0
**日期**: 2025-05-14
**作者**: lgnorant-lu

## 目录

- [简介](#简介)
- [插件系统概述](#插件系统概述)
- [创建第一个插件](#创建第一个插件)
- [插件生命周期](#插件生命周期)
- [使用事件系统](#使用事件系统)
- [插件配置管理](#插件配置管理)
- [扩展点机制](#扩展点机制)
- [插件依赖管理](#插件依赖管理)
- [插件打包与分发](#插件打包与分发)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)
- [示例插件](#示例插件)

## 简介

Status-Ming插件系统允许开发者通过创建插件来扩展应用功能，而无需修改核心代码。本指南将帮助你理解插件系统的架构，并指导你创建自己的插件。

## 插件系统概述

Status-Ming的插件系统基于以下核心概念：

1. **插件生命周期**: 每个插件都遵循标准化的生命周期(加载、启用、禁用、卸载)
2. **扩展点**: 预定义的扩展位置，允许插件添加功能
3. **依赖管理**: 插件可以声明对其他插件的依赖关系
4. **事件驱动**: 插件通过事件系统与应用和其他插件通信

核心组件包括：

- `PluginBase`: 所有插件的抽象基类
- `PluginManager`: 负责插件的发现、加载和生命周期管理
- `PluginRegistry`: 管理插件类型和扩展点

## 创建第一个插件

### 1. 基本结构

插件必须是一个符合以下结构的Python包：

```
my_plugin/
├── __init__.py  # 必须包含create_plugin()函数
├── plugin.py    # 包含主要插件类
└── resources/   # 插件资源(可选)
```

### 2. 实现插件类

插件必须继承`PluginBase`并实现所有生命周期方法：

```python
# plugin.py
from status.plugin.plugin_base import PluginBase

class MyPlugin(PluginBase):
    def __init__(self):
        super().__init__(
            plugin_id="my_plugin",
            name="我的插件",
            version="1.0.0",
            description="这是一个示例插件"
        )
    
    def load(self) -> bool:
        """加载插件资源和初始化，但不激活功能"""
        self.logger.info("插件加载中...")
        # 初始化资源、加载配置等
        return True
    
    def enable(self) -> bool:
        """启用插件功能"""
        self.logger.info("插件启用中...")
        # 注册事件监听器、添加UI元素等
        return True
    
    def disable(self) -> bool:
        """禁用插件功能"""
        self.logger.info("插件禁用中...")
        # 注销事件监听器、移除UI元素等
        return True
    
    def unload(self) -> bool:
        """卸载插件并释放资源"""
        self.logger.info("插件卸载中...")
        # 释放资源、保存配置等
        return True
```

### 3. 创建入口点

```python
# __init__.py
from .plugin import MyPlugin

def create_plugin():
    """创建插件实例
    
    此函数是插件的入口点，必须返回一个PluginBase的子类实例
    """
    return MyPlugin()
```

### 4. 安装插件

将插件目录放入应用的`plugins`目录即可。

## 插件生命周期

插件的生命周期包含以下阶段：

1. **发现**: PluginManager扫描插件目录，找到可用插件
2. **加载（load）**: 调用`load()`方法初始化插件资源和内部状态
3. **启用（enable）**: 调用`enable()`方法激活插件功能
4. **禁用（disable）**: 调用`disable()`方法停用插件功能
5. **卸载（unload）**: 调用`unload()`方法释放插件资源

### 最佳实践

- **load()**: 只加载资源和初始化状态，不应对系统产生可见影响
- **enable()**: 注册事件监听器、添加UI元素等，使功能对用户可见
- **disable()**: 清理enable阶段添加的内容，但不释放资源
- **unload()**: 完全释放资源，为插件移除做准备

## 使用事件系统

插件应使用Status-Ming的增强事件系统（`status/events/event_manager.py`）进行通信。

### 订阅事件

```python
from status.events import EventManager, EventPriority
from status.events.event_types import SystemEventType

def my_handler(event_type, event_data):
    self.logger.info(f"收到事件: {event_type}, 数据: {event_data}")

def enable(self) -> bool:
    # 获取事件管理器实例
    event_manager = EventManager()
    
    # 订阅系统事件(普通优先级)
    self.subscription = event_manager.subscribe(
        event_type=SystemEventType.CONFIG_CHANGED,
        handler=my_handler
    )
    
    # 订阅自定义事件(高优先级)
    self.custom_subscription = event_manager.subscribe(
        event_type="my_plugin.custom_event",
        handler=self.handle_custom_event,
        priority=EventPriority.HIGH
    )
    
    return True

def disable(self) -> bool:
    # 取消事件订阅
    event_manager = EventManager()
    event_manager.unsubscribe(self.subscription)
    event_manager.unsubscribe(self.custom_subscription)
    return True
```

### 发布事件

```python
def trigger_event(self):
    event_manager = EventManager()
    event_manager.emit(
        event_type="my_plugin.custom_event",
        event_data={"value": 42, "source": "my_plugin"}
    )
```

## 插件配置管理

### 访问配置

```python
def load(self) -> bool:
    # 获取配置
    default_config = {"setting1": "default", "setting2": 42}
    self.config = self.get_config() or default_config
    return True
```

### 保存配置

```python
def set_setting(self, key, value):
    self.config[key] = value
    # 配置更新后通知事件
    event_manager = EventManager()
    event_manager.emit(
        event_type="my_plugin.config_changed",
        event_data={"key": key, "value": value}
    )
```

## 扩展点机制

### 注册扩展点

```python
from status.plugin.plugin_registry import PluginRegistry

def enable(self) -> bool:
    # 获取插件注册表
    registry = PluginRegistry()
    
    # 注册插件类型
    registry.register_plugin_type(self.plugin_id, "ui_extension")
    
    # 注册扩展
    registry.register_extension(
        plugin_id=self.plugin_id,
        extension_point="main_menu",
        extension=self.create_menu_item
    )
    
    return True
```

### 使用其他插件的扩展点

```python
def get_extensions(self):
    registry = PluginRegistry()
    extension_handler = registry.get_extension_handler("data_processor")
    if extension_handler:
        extensions = extension_handler.get_all_extensions()
        for plugin_id, processor in extensions.items():
            result = processor(self.data)
            # 处理结果...
```

## 插件依赖管理

### 声明依赖

```python
def __init__(self):
    super().__init__(
        plugin_id="my_plugin",
        name="我的插件",
        version="1.0.0",
        description="这是一个示例插件"
    )
    # 添加依赖
    self.add_dependency("core_plugin")
    self.add_dependency("utility_plugin")
```

### 使用依赖的插件

```python
def enable(self) -> bool:
    # 获取依赖的插件
    plugin_manager = PluginManager()
    core_plugin = plugin_manager.get_plugin("core_plugin")
    
    if core_plugin:
        # 使用依赖的插件
        result = core_plugin.some_method()
        # ...
    
    return True
```

## 插件打包与分发

### 文件结构

```
my_plugin/
├── __init__.py
├── plugin.py
├── resources/
├── README.md
└── requirements.txt  # 插件特定依赖
```

### 创建发布包

```bash
# 创建发布包
cd my_plugin
zip -r my_plugin.zip ./*
```

## 最佳实践

1. **保持简单**: 每个插件应专注于单一功能
2. **错误处理**: 始终优雅地处理异常，避免影响主应用
3. **资源管理**: 在unload()中释放所有资源
4. **线程安全**: 确保插件在多线程环境中安全运行
5. **版本兼容**: 注意API版本兼容性
6. **文档化**: 为插件提供清晰的文档

## 常见问题

### 插件无法加载

**常见原因**:
- `create_plugin()`函数缺失或未正确实现
- 依赖的插件未安装
- Python路径问题

**解决方案**:
- 检查`__init__.py`中是否有正确的`create_plugin()`函数
- 确保所有依赖插件都已安装和启用
- 检查插件目录是否在正确的位置

### 插件启用失败

**常见原因**:
- 依赖的插件未启用
- 资源访问错误
- 配置问题

**解决方案**:
- 检查依赖插件的状态
- 确保所有资源路径正确
- 验证配置格式和内容

## 示例插件

### 简单通知插件

通知插件示例展示了如何创建一个基本的状态通知功能：

```python
# notification_plugin/plugin.py
from status.plugin.plugin_base import PluginBase
from status.events import EventManager, EventPriority
from status.events.event_types import SystemEventType

class NotificationPlugin(PluginBase):
    def __init__(self):
        super().__init__(
            plugin_id="notification_plugin",
            name="系统通知插件",
            version="1.0.0",
            description="显示系统状态变化通知"
        )
        self.subscriptions = []
    
    def load(self) -> bool:
        self.logger.info("通知插件加载中...")
        return True
    
    def enable(self) -> bool:
        self.logger.info("通知插件启用中...")
        
        event_manager = EventManager()
        
        # 订阅系统事件
        sub1 = event_manager.subscribe(
            event_type=SystemEventType.ERROR,
            handler=self._handle_error,
            priority=EventPriority.HIGH
        )
        
        sub2 = event_manager.subscribe(
            event_type=SystemEventType.CONFIG_CHANGED,
            handler=self._handle_config_change
        )
        
        self.subscriptions = [sub1, sub2]
        return True
    
    def disable(self) -> bool:
        self.logger.info("通知插件禁用中...")
        
        event_manager = EventManager()
        for subscription in self.subscriptions:
            event_manager.unsubscribe(subscription)
        
        self.subscriptions = []
        return True
    
    def unload(self) -> bool:
        self.logger.info("通知插件卸载中...")
        return True
    
    def _handle_error(self, event_type, event_data):
        self.logger.info(f"显示错误通知: {event_data.get('message', '未知错误')}")
        # 在实际实现中，这里会显示通知UI
    
    def _handle_config_change(self, event_type, event_data):
        self.logger.info(f"配置已更改: {event_data}")
        # 在实际实现中，这里会根据需要显示配置变更通知

# notification_plugin/__init__.py
from .plugin import NotificationPlugin

def create_plugin():
    return NotificationPlugin()
```

更多示例插件可以在项目的`plugins/examples`目录中找到。 