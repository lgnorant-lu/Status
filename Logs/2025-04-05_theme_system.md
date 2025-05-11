# UI主题系统实现记录

**日期**: 2025年4月5日  
**作者**: Ignorant-lu  
**版本**: 1.0.0  
**标签**: [UI, 主题, 样式, PyQt6]

## 实现概述

Hollow-ming项目的UI主题系统设计为一个灵活、可扩展的主题切换解决方案，基于PyQt6框架，实现了统一的界面风格管理。系统支持深色和浅色主题，并提供了主题切换功能，使应用程序的外观能够根据用户偏好动态调整。

## 组件架构

主题系统由以下核心组件组成：

1. **Theme类**：主题定义类，包含主题名称、类型、颜色定义和描述等属性，提供从JSON加载和保存到JSON的功能。

2. **ThemeType枚举**：定义主题类型（DARK/LIGHT）。

3. **ColorRole枚举**：定义颜色角色，如背景色、文本色、边框色等。

4. **ThemeManager类**：实现单例模式的主题管理器，负责管理主题注册、切换和应用。

5. **CSS样式模板**：为深色和浅色主题提供的样式表模板，使用变量引用颜色值以便动态替换。

## 主要功能

主题系统提供以下主要功能：

1. **主题注册与管理**：
   - 默认提供深色和浅色两种主题
   - 支持自定义主题的注册
   - 支持从文件加载和保存主题

2. **主题切换**：
   - 通过ThemeManager实现全局主题切换
   - 支持主题变更事件通知（基于PyQt信号）
   - 提供主题变更监听器机制

3. **样式应用**：
   - 生成并应用全局样式表
   - 支持基于CSS模板的样式定义
   - 当没有CSS模板文件时，自动生成默认样式

4. **组件级别的样式应用**：
   - 提供`apply_theme_to_widget`函数用于单个组件的主题应用
   - 支持自定义样式表应用

## 技术实现细节

### 1. 主题定义

主题使用`Theme`类定义，包含主题名称、类型和颜色映射。每个主题定义了一组标准化的颜色角色，确保UI组件的一致性。

```python
class Theme:
    def __init__(self, name: str, type: ThemeType, colors: Dict[str, str], description: str = ""):
        self.name = name
        self.type = type
        self.colors = colors
        self.description = description
```

### 2. 颜色角色定义

使用`ColorRole`枚举定义标准化的颜色角色，包括：

- 基础颜色：背景色、表面色、主要强调色、次要强调色等
- 状态颜色：成功色、警告色、错误色、信息色
- 特殊颜色：阴影色、遮罩色

### 3. 主题管理器实现

`ThemeManager`实现为单例类，确保全局只有一个主题管理实例。主要方法包括：

- `register_theme`：注册新主题
- `set_theme`：切换当前主题
- `get_current_theme`：获取当前主题
- `add_theme_listener`：添加主题变更监听器

### 4. 样式应用机制

主题样式应用的主要实现：

1. **CSS模板加载**：
   - 从文件加载CSS模板
   - 使用变量替换应用主题颜色

2. **默认样式生成**：
   - 当没有CSS模板时，自动生成包含基本样式的样式表

3. **调色板应用**：
   - 除了样式表外，还通过QPalette设置应用程序调色板

### 5. 组件级别的样式应用

提供了`apply_theme_to_widget`函数，允许对单个控件应用当前主题，适用于动态创建的控件。

## 扩展性设计

主题系统的扩展性主要体现在：

1. **主题定义**：
   - 支持通过JSON文件定义新主题
   - 支持运行时动态创建和注册主题

2. **CSS模板系统**：
   - 使用变量引用方式实现颜色动态替换
   - 可以通过编辑CSS模板文件调整样式，无需修改代码

3. **监听器机制**：
   - 提供主题变更通知，方便组件响应主题变更

## 使用示例

### 1. 基本使用

```python
# 获取主题管理器单例
theme_manager = ThemeManager.instance()

# 切换主题
theme_manager.set_theme("Hollow Light")

# 注册主题变更监听器
def on_theme_changed(theme):
    print(f"主题已切换为: {theme.name}")

theme_manager.add_theme_listener(on_theme_changed)
```

### 2. 自定义主题

```python
# 创建自定义主题
custom_theme = Theme(
    name="Custom Theme",
    type=ThemeType.DARK,
    colors={
        ColorRole.BACKGROUND: "#1A1A1A",
        ColorRole.PRIMARY: "#5E81AC",
        # 其他颜色...
    },
    description="自定义深色主题"
)

# 注册自定义主题
theme_manager.register_theme(custom_theme)
```

### 3. 主题演示程序

实现了一个完整的主题演示程序`theme_demo.py`，展示了主题切换效果以及各种UI组件在不同主题下的外观。

## 适配其他UI组件

所有自定义UI组件已经适配主题系统：

1. **按钮组件**：如PrimaryButton、SecondaryButton等
2. **卡片组件**：如Card、CardHeader等 
3. **进度指示器**：如ProgressBar、CircularProgress等
4. **通知组件**：如Notification等

## 后续优化计划

1. **主题编辑器**：添加可视化主题编辑工具
2. **更多预设主题**：增加更多预设主题选项
3. **动画过渡**：添加主题切换时的过渡动画
4. **主题自动切换**：根据系统时间或系统主题自动切换
5. **主题混合**：支持组件级别的主题混合，允许单个组件使用不同于全局的主题

## 变更记录

| 日期         | 版本   | 描述                                      |
|-------------|--------|------------------------------------------|
| 2025-04-05  | 1.0.0  | 实现基本主题系统，包含深色和浅色主题        |
|             |        | 添加主题管理器和CSS模板系统                |
|             |        | 实现主题演示程序                          | 