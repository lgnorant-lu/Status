# 系统监控模块实现

**日期**: 2025-04-03  
**分类**: 功能, 监控  
**责任人**: Ignorant-lu  
**状态**: 完成  

## 概述

本文档记录了系统监控模块的初始设计与实现。该模块负责收集、处理和展示系统性能指标，为应用程序提供实时状态监控功能。

## 实现详情

### 1. 模块结构

监控模块采用分层设计，包括以下核心组件：

- **SystemInfo**: 系统信息收集类，负责获取各项系统性能指标
- **DataProcessor**: 数据处理类，负责处理和分析系统监控数据
- **MonitorUIController**: UI控制器，负责管理监控界面的显示与更新
- **SystemMonitor**: 系统监控器主类，作为监控模块的入口点

### 2. 功能实现

#### 2.1 系统信息收集 (SystemInfo)

- 实现了单例模式，确保全局只有一个信息收集实例
- 支持获取以下系统指标：
  - CPU使用率（总体和每个核心）
  - 内存使用情况
  - 磁盘使用情况（分区和IO）
  - 网络使用情况
  - 电池信息（如果可用）
  - 运行中的进程
- 采用线程安全设计，支持自动更新功能
- 通过事件系统发送系统状态更新事件

```python
# 核心功能示例
def update_metrics(self) -> Dict[str, Any]:
    """更新所有系统指标"""
    self.metrics = {}
    
    # 获取各项指标...
    self.metrics["cpu"] = self.get_cpu_info()
    self.metrics["memory"] = self.get_memory_info()
    # ...
    
    # 发送更新事件
    self._send_update_event()
    
    return self.metrics
```

#### 2.2 数据处理 (DataProcessor)

- 实现了单例模式和线程安全设计
- 维护各项指标的历史数据和统计信息
- 支持基于阈值的告警机制
- 允许注册自定义数据处理器
- 提供数据分析功能：
  - 统计计算（最小值、最大值、平均值等）
  - 趋势分析
  - 告警判断

```python
# 告警检测示例
def _check_thresholds(self, metrics: Dict[str, Any]) -> None:
    """检查阈值并发送告警"""
    # 检查CPU使用率
    if "cpu" in metrics and "percent_overall" in metrics["cpu"]:
        cpu_percent = metrics["cpu"]["percent_overall"]
        if cpu_percent >= self.thresholds["cpu_high"] and not self.alert_status["cpu_high"]:
            self._send_alert("cpu_high", f"CPU使用率过高: {cpu_percent:.1f}%", {
                "value": cpu_percent,
                "threshold": self.thresholds["cpu_high"],
                "metrics": metrics["cpu"],
            })
            self.alert_status["cpu_high"] = True
    # ...其他指标检查...
```

#### 2.3 UI控制器 (MonitorUIController)

- 管理多个UI组件
- 处理系统状态更新事件
- 维护告警历史
- 为UI组件提供统一的数据接口

```python
# UI组件更新示例
def _update_ui_components(self, status_data: Dict[str, Any]) -> None:
    """更新所有UI组件"""
    for component_id, component in self.ui_components.items():
        try:
            if hasattr(component, "update") and callable(component.update):
                component.update(status_data)
        except Exception as e:
            self.logger.error(f"更新UI组件 '{component_id}' 失败: {e}")
```

#### 2.4 系统监控器主类 (SystemMonitor)

- 作为监控模块的统一入口
- 协调各个子组件的工作
- 提供简洁的API接口
- 管理监控的启动和停止

```python
# 启动监控示例
def start(self) -> bool:
    """启动系统监控"""
    if self.is_running:
        self.logger.warning("系统监控已在运行")
        return False
        
    # 启动系统信息自动更新
    result = self.system_info.start_auto_update()
    if not result:
        return False
        
    self.is_running = True
    self._send_monitor_event("start")
    return True
```

### 3. 用户接口

创建了简单的控制台UI示例，展示如何使用监控模块：

```python
class SimpleConsoleUI:
    """简单的控制台UI类，用于显示系统状态"""
    
    def update(self, data: Dict[str, Any]) -> None:
        """更新UI显示"""
        # 处理告警或显示系统信息
        if data.get("alert"):
            self._display_alert(data)
        else:
            self._display_system_info(data)
```

### 4. 测试覆盖

为监控模块的各个组件编写了全面的单元测试：

- `test_system_info.py`: 测试系统信息收集功能
- `test_data_process.py`: 测试数据处理和分析功能
- `test_monitor.py`: 测试监控器主类功能

测试覆盖了各组件的核心功能、异常处理和边界情况。

## 设计模式与技术实现

1. **单例模式**: 所有核心组件都采用单例模式，确保全局状态一致性
2. **观察者模式**: 通过事件系统实现组件间的松耦合通信
3. **策略模式**: 自定义数据处理器支持灵活的数据分析策略
4. **适配器模式**: UI控制器为不同的UI组件提供统一接口
5. **线程安全**: 使用锁机制确保多线程环境下的数据一致性
6. **事件驱动**: 基于事件的异步通信降低了组件间的耦合度

## 性能考量

1. **内存占用控制**: 使用双端队列(deque)限制历史数据大小
2. **CPU使用率**: 采用可配置的更新间隔，避免频繁更新造成性能开销
3. **线程管理**: 使用守护线程进行自动更新，避免资源泄漏

## 未来改进计划

1. **图形化界面**: 开发基于PyQt的图形界面，显示各项指标的图表
2. **预测分析**: 添加基于历史数据的趋势预测功能
3. **扩展监控指标**: 增加GPU使用率、网络连接详情等更多指标
4. **配置持久化**: 支持将监控配置和阈值设置保存到配置文件
5. **远程监控**: 添加远程监控服务器的功能

## 技术债务

1. 部分异常处理需要更细致的错误恢复机制
2. 目前缺少配置持久化功能
3. 需要优化图表数据的传输效率

## 相关文档

- [psutil 文档](https://psutil.readthedocs.io/en/latest/)
- [Python 多线程编程](https://docs.python.org/3/library/threading.html)
- [事件驱动编程模式](https://en.wikipedia.org/wiki/Event-driven_programming) 