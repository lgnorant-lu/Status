# TDD测试框架实现

## 概述

按照TDD（测试驱动开发）原则，为Status-Ming项目建立了单元测试和集成测试框架，并实现了第一批测试用例。

## TDD工作流程

我们采用以下TDD工作流程：

1. **先写测试**：在编写实际功能代码前，先编写测试用例
2. **测试失败**：运行测试，确认测试失败（因为功能还未实现）
3. **实现功能**：编写最小功能代码，使测试通过
4. **测试通过**：运行测试，确认测试通过
5. **重构**：改进代码质量，确保测试仍然通过

## 选择的测试框架

- **单元测试**：使用Python标准库的unittest框架
- **模拟对象**：使用unittest.mock库进行模拟和打桩
- **GUI测试**：结合PySide6和unittest进行Qt组件测试

## 已实现的测试

### StatsPanel组件测试

1. **单元测试** (`tests/ui/test_stats_panel.py`)
   - 测试初始化
   - 测试显示/隐藏功能
   - 测试事件处理
   - 测试数据更新
   - 测试展开/折叠功能

2. **集成测试** (`tests/ui/test_stats_panel_in_app.py`)
   - 测试面板在应用中的创建
   - 测试托盘菜单控制面板显示隐藏
   - 测试窗口位置更新机制

## 测试关键点

### 1. Qt组件测试技巧

- 使用QApplication.processEvents()确保GUI事件处理
- 正确处理Qt信号和槽的测试
- 注意处理模态窗口和事件循环

```python
# 示例：确保Qt事件循环处理
def test_show_panel(self):
    """测试显示面板功能"""
    # 初始应该是隐藏的
    self.assertFalse(self.stats_panel.isVisible())
    
    # 调用显示方法
    self.stats_panel.show_panel()
    
    # 处理Qt事件循环中的事件，确保显示命令被处理
    QApplication.processEvents()
    
    # 验证面板现在是可见的
    self.assertTrue(self.stats_panel.isVisible())
```

### 2. 事件系统测试

- 模拟事件发布
- 验证事件处理器调用
- 检查组件状态变化

```python
def test_handle_stats_update(self):
    """测试处理系统统计更新事件"""
    # 准备测试数据
    test_data = {
        'cpu': 25.5,
        'memory': 60.2,
        'cpu_cores': [20.1, 30.5, 15.8, 40.2],
        # ... 更多测试数据
    }
    
    # 创建事件
    event = SystemStatsUpdatedEvent(test_data)
    
    # 存储初始显示内容
    initial_text = self.stats_panel.data_label.text()
    
    # 调用事件处理方法
    self.stats_panel.handle_stats_update(event)
    
    # 验证组件已更新显示的数据
    self.assertNotEqual(initial_text, self.stats_panel.data_label.text())
    self.assertIn("CPU: 25.5%", self.stats_panel.data_label.text())
```

### 3. 模拟和打桩

- 使用MagicMock模拟对象行为
- 使用patch装饰器替换方法

```python
@patch('status.ui.stats_panel.StatsPanel.move')
def test_update_position(self, mock_move):
    """测试更新位置方法"""
    # 设置父窗口位置和大小
    parent_pos = QPoint(100, 100)
    parent_size = QSize(200, 200)
    
    # 调用被测试的方法
    self.stats_panel.update_position(parent_pos, parent_size)
    
    # 验证move方法被调用过，并且使用了正确的参数
    mock_move.assert_called_once()
    args = mock_move.call_args[0]
    self.assertIsInstance(args[0], QPoint)
```

## 测试清理技巧

为确保测试之间互不干扰，我们实现了全面的测试清理机制：

```python
def tearDown(self):
    """每个测试后的清理工作"""
    # 恢复原始方法
    if hasattr(self, 'original_show'):
        self.stats_panel.show = self.original_show
    
    # 销毁StatsPanel实例
    if hasattr(self, 'stats_panel') and self.stats_panel:
        # 直接调用注销方法，确保事件处理器被清理
        if hasattr(self.stats_panel, 'event_manager') and self.stats_panel.event_manager:
            try:
                self.stats_panel.event_manager.unregister_handler(
                    EventType.SYSTEM_STATS_UPDATED, 
                    self.stats_panel.handle_stats_update
                )
            except Exception as e:
                logger.error(f"注销 StatsPanel 事件处理器时出错: {e}")
        
        # 使用deleteLater确保Qt对象正确销毁
        self.stats_panel.hide()
        self.stats_panel.deleteLater()
        self.stats_panel = None
```

## 后续计划

1. 扩展测试覆盖到更多组件：
   - 系统监控模块
   - 事件系统
   - 主窗口
   - 系统托盘
   
2. 自动化测试集成：
   - 建立CI/CD流程
   - 添加测试覆盖率报告
   - 实现自动化测试运行脚本

3. 性能测试：
   - 添加负载测试用例
   - 测量UI响应性能
   - 测量系统资源使用情况 