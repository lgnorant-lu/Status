# 2025-05-17 StatsPanel显示问题修复与TDD测试实现

## 概述

解决了StatsPanel组件不显示的问题，并实现了符合TDD规范的测试用例。

## 问题诊断

在之前的实现中，StatsPanel组件虽然逻辑上运行正常，但没有在屏幕上实际显示。通过添加更多的调试日志和测试，发现了以下问题：

1. 窗口显示逻辑存在问题，包括位置计算和实际显示调用
2. 开发方式不符合TDD规范，缺乏针对UI组件的单元测试
3. Qt事件处理机制中对于窗口显示状态的管理不完善

## 实施变更

### 1. 增强StatsPanel调试功能

- 添加了更详细的日志记录，跟踪窗口状态
- 实现了showEvent和paintEvent方法以便观察渲染过程
- 临时修改窗口样式以提高可见性和便于调试

```python
def showEvent(self, event):
    """窗口显示事件处理"""
    super().showEvent(event)
    logger.info(f"StatsPanel.showEvent triggered. Visible: {self.isVisible()}, Position: {self.pos()}, Size: {self.size()}")

def paintEvent(self, event):
    """窗口绘制事件处理"""
    super().paintEvent(event)
    if self.isVisible():
        logger.info(f"StatsPanel.paintEvent triggered. Rect: {event.rect()}, Visible: {self.isVisible()}")
```

### 2. 修复主应用程序中的显示控制逻辑

- 改进了_handle_toggle_stats_panel方法，确保StatsPanel在显示时正确可见
- 添加了额外的位置更新和渲染调用
- 确保窗口在实际显示时设置了正确的标志

```python
def _handle_toggle_stats_panel(self, show: bool):
    """处理显示/隐藏统计面板的请求。"""
    if not self.stats_panel or not self.main_window:
        logger.warning("StatsPanel 或主窗口不存在，无法切换统计面板可见性。")
        return

    if show:
        # 获取当前主窗口位置和大小
        pet_pos = self.main_window.pos()
        pet_size = self.main_window.size()
        
        logger.info(f"展示统计面板 - 主窗口当前位置: {pet_pos}, 大小: {pet_size}")
        
        # 主动调用更新位置方法
        self.stats_panel.parent_window_pos = pet_pos
        self.stats_panel.parent_window_size = pet_size
        self.stats_panel.update_position(pet_pos, pet_size)
        
        # 确保面板在前台显示
        self.stats_panel.show_panel()
        self.stats_panel.raise_()
        self.stats_panel.activateWindow()
    else:
        self.stats_panel.hide_panel()
```

### 3. 实现TDD测试用例

创建了两个测试文件，遵循TDD开发规范：

1. test_stats_panel.py - 单元测试，测试StatsPanel的基本功能
   - 测试初始化
   - 测试显示/隐藏功能
   - 测试事件处理
   - 测试数据更新
   - 测试展开/折叠功能

2. test_stats_panel_in_app.py - 集成测试，测试StatsPanel在主应用中的行为
   - 测试面板创建
   - 测试托盘菜单控制
   - 测试窗口位置更新

## 结果

1. StatsPanel现在可以正常显示，并正确响应用户操作
2. 实现了符合TDD规范的单元测试和集成测试
3. 系统监控数据可以正确显示，包括之前添加的GPU、磁盘I/O和网络速度监控

## 后续计划

1. 扩展测试覆盖率到其他组件
2. 优化StatsPanel的性能
3. 添加自定义主题支持 