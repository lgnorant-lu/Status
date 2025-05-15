"""
---------------------------------------------------------------
File name:                  2025-05-15_event_system_integration.md
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                事件系统统一日志
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建;
----
"""

# 事件系统统一与增强

## 背景

Status-Ming项目的事件系统存在历史演进导致的架构不一致问题。项目最初使用`EventManager`类处理事件，后来引入了`EventSystem`类实现更强大的功能，但`EventManager`未完全兼容`EventSystem`的API，导致在使用字符串类型事件时出现无法访问属性的lint错误。

## 问题分析

1. **错误症状**：ResourcePackManager和ResourceLoader类中使用`_event_system.publish`方法时出现lint错误：无法访问类"EventSystem"的属性"publish"。

2. **根本原因**：
   - `EventSystem`类提供`dispatch_event`和`register_handler`方法
   - `EventManager`继承自`EventSystem`但未实现对应的`publish`和`subscribe`方法
   - 由于历史原因，ResourcePackManager等类使用`publish`和`subscribe`方法名

3. **解决方向**：
   - 在`EventManager`类中添加对`publish`、`subscribe`和`unsubscribe`方法的支持
   - 这些方法作为`dispatch_event`、`register_handler`和`unregister_handler`的包装

## 实施方案

### 1. 检查问题来源

检查了`resource_pack.py`和`resource_loader.py`文件，识别了所有使用`publish`和`subscribe`方法的位置：
- ResourcePackManager._check_directory_changes方法
- ResourcePackManager.hot_reload_pack方法
- ResourceLoader._register_event_handlers方法

### 2. 实现API兼容层

在`EventManager`类中添加了三个方法：
- `publish(event_type, data=None, sender=None)`
- `subscribe(event_type, handler)`
- `unsubscribe(event_type, handler)`

方法实现采用简化设计：
- 对于字符串事件类型，提供警告日志但保留API兼容性
- 对于枚举事件类型，直接转发到对应的原生方法

### 3. 增强调用点的防御性

在所有使用这些API的地方添加了防御性检查：
- ResourcePackManager._check_directory_changes
- ResourcePackManager.hot_reload_pack
- ResourceLoader._register_event_handlers

所有地方都添加了`hasattr`检查：
```python
if self._event_system and hasattr(self._event_system, 'publish'):
    self._event_system.publish(...)
```

### 4. 测试结果

- 单元测试：所有相关测试都通过，包括：
  - EventManager相关测试
  - 资源热加载测试
  - 所有核心模块测试

- 完整功能验证：通过`python -m pytest tests/unit/`运行所有单元测试，29个测试通过，1个跳过。

## 总结

1. **架构决策**：
   - 保留了当前的EventSystem/EventManager类层次结构
   - 通过增加兼容层方法解决API不一致问题
   - 避免进行大规模重构，降低项目风险
   - 保证现有代码的运行时兼容性

2. **改进**：
   - 清理了历史遗留的字符串事件类型API，提供警告
   - 增强了事件系统调用点的健壮性
   - 保持了良好的向后兼容性

3. **后续工作**：
   - 在未来版本中考虑完全统一事件系统API
   - 为字符串事件类型提供更好的支持或彻底移除
   - 更新文档和教程，引导使用标准的事件系统API 