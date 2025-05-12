# 监控模块类型提示优化

## 修复概述
2025-05-15，对Status项目的监控模块进行了类型提示优化。主要修复了以下问题：

1. `system_info.py` 中的 `Collection[Any]` 类型索引错误
2. 所有监控模块类中 `_initialized` 的类型未定义问题
3. `Event` 类的导入路径错误
4. 一些类型变量导入缺失问题

## 修复细节

### system_info.py
- 修复了网络接口地址列表使用 `Collection[Any]` 类型的问题，将其改为明确的 `Dict` 和 `List` 类型
- 为 `result` 变量添加了明确的类型注解 `Dict[str, Any]`
- 修改了对象初始化流程，添加了类变量 `_initialized: bool = False`
- 更正了导入语句，从 `status.core.event_system` 导入 `Event` 类而非 `status.core.types`

### data_process.py
- 添加了类变量 `_initialized: bool = False`
- 确保 `TypeVar` 被正确导入
- 修复了 `TypeVar('T')` 的定义和使用

### monitor.py
- 添加了类变量 `_initialized: bool = False`
- 修复了导入语句，从 `status.core.event_system` 导入 `Event` 类
- 添加了获取实例的类方法 `get_instance()`

### ui_controller.py
- 添加了类变量 `_initialized: bool = False`
- 修复了导入语句，从 `status.core.event_system` 导入 `Event` 类
- 添加了获取实例的类方法 `get_instance()`

## 遗留问题
1. 一些测试用例失败，需要单独处理：
   - SystemMonitor 缺少 `is_running` 属性和 `start`/`stop` 方法
   - 部分测试断言需要更新以匹配新的代码结构
2. 外部库类型提示问题：
   - psutil 库缺少类型存根（需要安装 types-psutil）
   - GPUtil 库缺少类型标记

## 影响和总结
这些更改提高了代码的类型安全性，消除了主要的类型错误。mypy 检查现在只显示外部库的类型问题，所有内部代码的类型错误已经修复。

测试结果显示大部分测试通过，但有9个测试失败，这些主要是由于代码结构变化导致的，需要在后续更新中进行调整。 