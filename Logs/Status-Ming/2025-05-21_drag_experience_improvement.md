---------------------------------------------------------------
日志文件名:                  2025-05-21_drag_experience_improvement.md
作者:                       Ignorant-lu
日期:                       2025/05/13
描述:                       桌宠拖动体验优化记录
----------------------------------------------------------------
```

# 桌宠拖动体验优化

## 背景

桌宠窗口作为Status-Ming应用的关键交互界面，其拖动体验直接影响用户使用舒适度。之前在测试过程中发现了两个主要问题：

1. **精确模式闪动问题**：在精确拖动模式下，当用户快速拖动桌宠时，桌宠位置会出现不连贯的"闪动"现象。
2. **高速拖动边界问题**：在高速大幅度拖动桌宠时，窗口可能会部分或完全移出屏幕边界，导致用户难以找回桌宠。

## 修改概述

### 1. 优化拖动平滑系数

- 调整`DRAG_SMOOTHING_FACTOR`基础平滑系数从0.6降低到0.5，提供更平滑的默认体验
- 降低`DRAG_MAX_SMOOTHING`从0.9降至0.85，减少精确模式的过度敏感性
- 调整`DRAG_SPEED_THRESHOLD`速度阈值从5.0降至4.0，使平滑效果更加渐进

### 2. 添加严格边界限制

- 引入新常量`STRICT_BOUNDARY_CHECK`确保每次位置更新都进行边界检查
- 为最小可见区域尺寸设置绝对下限（50像素），确保窗口始终有足够部分在屏幕内
- 在`_update_position`方法中添加边界检查，解决高速滑动时的边界问题

### 3. 修改拖动处理逻辑

- 移除精确模式下直接设置位置的特殊处理，统一使用平滑定时器
- 在鼠标释放事件中添加边界检查，确保释放时窗口位置仍在屏幕内
- 完善智能模式下的平滑系数计算，使用二次函数而非线性关系，实现更自然的渐进效果

## 详细技术修改

### 主要常量调整
```python
# 调整前
DRAG_SMOOTHING_FACTOR = 0.6   # 基础平滑系数
DRAG_MAX_SMOOTHING = 0.95     # 最大平滑系数(接近1:1跟随)
DRAG_MIN_SMOOTHING = 0.4      # 最小平滑系数(最平滑)
DRAG_SPEED_THRESHOLD = 5.0    # 速度阈值

# 调整后
DRAG_SMOOTHING_FACTOR = 0.5   # 基础平滑系数 (降低以获得更平滑的体验)
DRAG_MAX_SMOOTHING = 0.85     # 最大平滑系数(接近1:1跟随) - 降低以避免精确模式闪动
DRAG_MIN_SMOOTHING = 0.3      # 最小平滑系数(最平滑)
DRAG_SPEED_THRESHOLD = 4.0    # 速度阈值，超过此值使用最大平滑系数

# 新增常量
STRICT_BOUNDARY_CHECK = True  # 严格边界检查，确保始终在屏幕内
```

### 关键逻辑修改

1. 从精确模式中移除直接位置设置，确保动画连贯：
```python
# 修改前
if self.drag_mode == "precise" and self.mouse_speed > DRAG_SPEED_THRESHOLD * 1.5:
    self.current_pos = constrained_pos
    self.move(constrained_pos)
elif not self.smoothing_timer.isActive():
    # 启动平滑定时器
    self.smoothing_timer.start()

# 修改后
# 移除直接设置位置的特殊处理，统一使用平滑定时器
if not self.smoothing_timer.isActive():
    # 启动平滑定时器
    self.smoothing_timer.start()
```

2. 在`_update_position`方法中添加边界检查：
```python
# 确保当前位置仍然在屏幕边界内
# 这是修复高速滑动问题的关键，确保每次位置更新都检查边界
if STRICT_BOUNDARY_CHECK:
    screen_geometry = self._get_screen_geometry()
    self.current_pos = self._constrain_to_screen_boundary(self.current_pos, screen_geometry)
```

3. 优化智能模式下的平滑系数计算：
```python
# 修改前
speed_factor = min(1.0, self.mouse_speed / DRAG_SPEED_THRESHOLD)

# 修改后
# 调整速度与平滑度的关系曲线，使其更自然
# 使用二次方曲线而不是线性关系，提供更好的渐进效果
speed_factor = min(1.0, (self.mouse_speed / DRAG_SPEED_THRESHOLD) ** 2)
```

4. 增强最小可见区域计算：
```python
# 确保最小可见区域不小于一个合理的值
min_visible_width = max(min_visible_width, 50)
min_visible_height = max(min_visible_height, 50)
```

## 测试结果

经过修改后的拖动体验有显著改善，但仍有一些问题：

1. **精确模式闪动问题**：通过移除直接位置设置逻辑并降低最大平滑系数，精确模式下的闪动问题减轻但未完全解决。仍然观察到轻微闪动，且拖动不是完全1:1跟随鼠标轨迹。

2. **高速拖动边界问题**：通过在位置更新循环中添加严格边界检查，即使在高速拖动时也能保证窗口不会超出屏幕边界，至少有50像素的可见区域保持在屏幕内。这一问题基本解决。

3. **整体拖动体验**：调整平滑系数和使用二次函数计算渐进效果，使拖动体验更加自然流畅，特别是在智能模式下。

## 下一步计划

1. **优先改进精确模式**：重点解决精确模式下的轻微闪动和不完全1:1跟随问题
   - 考虑完全重构拖动算法，可能需要使用不同的平滑方法或完全取消平滑
   - 尝试使用更高的更新频率(如8ms而非16ms)提高响应速度
   - 研究鼠标事件的直接处理方式，减少中间计算环节

2. 考虑添加更丰富的交互反馈，例如在边缘吸附时播放一个轻微的动画效果

3. 探索多屏幕支持，确保在多显示器环境中也能正确处理边界

4. 评估拖动优化对性能的影响，必要时进行进一步优化

## 提交记录

- **提交消息**: [UI] 修复: 优化桌宠拖动体验，修复精确模式闪动和边界问题
- **修改文件**: `status/ui/main_pet_window.py`
- **提交时间**: 2025-05-21 