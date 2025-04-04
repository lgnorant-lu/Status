# Hollow-ming 插件开发指南

## 目录

- [插件系统概述](#插件系统概述)
- [插件类型](#插件类型)
- [创建第一个插件](#创建第一个插件)
- [插件API参考](#插件api参考)
- [插件生命周期](#插件生命周期)
- [最佳实践](#最佳实践)
- [插件分发](#插件分发)
- [示例插件](#示例插件)
- [故障排除](#故障排除)

## 插件系统概述

Hollow-ming的插件系统允许开发者扩展应用功能，而无需修改核心代码。插件可以添加新功能、修改现有行为、集成外部服务，或自定义用户界面。

### 设计原则

Hollow-ming的插件系统遵循以下设计原则：

1. **模块化设计**：每个插件都是独立的功能单元
2. **非侵入性**：插件不应修改或破坏核心系统代码
3. **稳定API**：提供稳定的插件API，减少版本更新带来的影响
4. **隔离性**：插件间应相互隔离，一个插件的故障不应影响其他插件
5. **资源管理**：提供统一的资源访问机制，避免资源冲突

### 架构概览

插件系统的核心组件包括：

- **插件管理器**：负责插件的加载、卸载和生命周期管理
- **插件注册表**：维护已安装插件的信息和状态
- **API提供器**：为插件提供访问核心功能的接口
- **事件分发器**：允许插件监听和响应系统事件
- **资源管理器**：管理插件资源的加载和访问
- **配置管理器**：处理插件配置的存储和检索

```
┌────────────────────────────┐
│       Hollow-ming核心      │
├────────────────────────────┤
│                            │
│    ┌──────────────────┐    │
│    │   插件管理器     │    │
│    └──────────────────┘    │
│              ↑             │
│              ↓             │
│    ┌──────────────────┐    │
│    │   插件API提供器  │    │
│    └──────────────────┘    │
│                            │
└────────────────────────────┘
            ↑   ↑   ↑
            │   │   │
┌───────────┐ ┌───────────┐ ┌───────────┐
│  插件 A   │ │  插件 B   │ │  插件 C   │
└───────────┘ └───────────┘ └───────────┘
```

## 插件类型

Hollow-ming支持多种类型的插件，每种类型专注于特定的功能领域：

### 功能插件

功能插件扩展应用的核心功能，如添加新的工具、实用程序或特性。

**示例**：
- 日程提醒插件
- 天气显示插件
- 系统监控插件

### 行为插件

行为插件修改或扩展桌宠的行为模式和反应。

**示例**：
- 自定义动作插件
- 互动模式扩展
- 情绪系统增强

### 外观插件

外观插件修改桌宠的视觉呈现和用户界面。

**示例**：
- 主题插件
- 特效插件
- UI自定义插件

### 集成插件

集成插件将Hollow-ming与外部服务或应用程序连接。

**示例**：
- 社交媒体集成
- 云服务同步
- 第三方API连接

### 扩展插件

扩展插件为插件系统本身提供额外功能，供其他插件使用。

**示例**：
- 插件市场连接器
- 高级事件处理框架
- 国际化支持库

## 创建第一个插件

本节将指导您创建一个基本的Hollow-ming插件。我们将以一个简单的"问候插件"为例，这个插件会定期显示问候消息。

### 先决条件

- Python 3.8或更高版本
- Hollow-ming主程序
- 熟悉Python编程基础

### 插件结构

一个标准的Hollow-ming插件通常包含以下文件和目录：

```
greeting_plugin/
├── plugin.json       # 插件元数据
├── __init__.py       # 插件入口点
├── main.py           # 主要功能实现
├── resources/        # 资源文件（图像、音频等）
│   ├── icon.png
│   └── sound.wav
└── settings.py       # 设置界面定义（可选）
```

### 步骤1：创建插件目录

首先，在Hollow-ming的`plugins`目录下创建您的插件文件夹：

```bash
mkdir -p /path/to/hollow-ming/plugins/greeting_plugin
cd /path/to/hollow-ming/plugins/greeting_plugin
```

### 步骤2：创建元数据文件

创建`plugin.json`文件，定义插件的基本信息：

```json
{
  "name": "Greeting Plugin",
  "id": "greeting_plugin",
  "version": "1.0.0",
  "description": "A simple plugin that displays greeting messages",
  "author": "Your Name",
  "email": "your.email@example.com",
  "website": "https://example.com",
  "requires": {
    "hollow-ming": ">=1.0.0"
  },
  "main": "__init__.py",
  "settings": "settings.py",
  "icon": "resources/icon.png",
  "categories": ["utility", "communication"]
}
```

### 步骤3：创建插件入口点

创建`__init__.py`文件，定义插件的入口点：

```python
"""
Greeting Plugin - A simple plugin that displays greeting messages.
"""

from status.plugin import PluginBase
from status.event import EventType
import time
import random

class GreetingPlugin(PluginBase):
    """Greeting plugin main class."""
    
    def __init__(self, plugin_manager):
        super().__init__(plugin_manager)
        self.messages = [
            "你好！今天过得怎么样？",
            "嗨！希望你有美好的一天！",
            "你好啊！需要帮忙吗？",
            "欢迎回来！"
        ]
        self.last_greeting_time = 0
        self.greeting_interval = 3600  # 默认1小时一次
        
    def on_load(self):
        """Called when the plugin is loaded."""
        self.logger.info("Greeting Plugin loaded")
        # 读取插件配置
        self.greeting_interval = self.get_config().get("interval", 3600)
        custom_messages = self.get_config().get("custom_messages", [])
        if custom_messages:
            self.messages.extend(custom_messages)
        
        # 注册定时器事件
        self.register_timer(self.check_greeting, 60)  # 每分钟检查一次
        
        # 注册系统事件
        self.register_event(EventType.APPLICATION_READY, self.on_app_ready)
        self.register_event(EventType.USER_IDLE, self.on_user_idle)
        
        return True
        
    def on_unload(self):
        """Called when the plugin is unloaded."""
        self.logger.info("Greeting Plugin unloaded")
        return True
    
    def check_greeting(self):
        """Check if it's time to show a greeting."""
        current_time = time.time()
        if current_time - self.last_greeting_time >= self.greeting_interval:
            self.show_greeting()
            self.last_greeting_time = current_time
    
    def show_greeting(self):
        """Show a random greeting message."""
        message = random.choice(self.messages)
        self.api.show_message(message, duration=5000)
    
    def on_app_ready(self, event):
        """Called when the application is ready."""
        # 应用启动后显示一条欢迎消息
        self.show_greeting()
    
    def on_user_idle(self, event):
        """Called when the user is idle."""
        # 用户空闲时也显示一条消息
        if event.idle_time >= 300:  # 5分钟没活动
            self.show_greeting()

# 插件入口函数，必须返回插件的主类
def plugin_entry(plugin_manager):
    return GreetingPlugin(plugin_manager)
```

### 步骤4：添加设置界面

创建`settings.py`文件，定义插件的设置界面：

```python
"""
Greeting Plugin settings interface.
"""

from status.plugin import PluginSettingsBase
from status.ui import FormBuilder

class GreetingSettings(PluginSettingsBase):
    """Settings interface for the Greeting Plugin."""
    
    def build_settings_ui(self, builder):
        """Build the settings UI."""
        builder.add_section("基本设置")
        
        builder.add_number(
            key="interval",
            label="问候间隔（秒）",
            min_value=60,
            max_value=86400,
            default_value=3600,
            help_text="显示问候消息的间隔时间"
        )
        
        builder.add_section("消息设置")
        
        builder.add_text_list(
            key="custom_messages",
            label="自定义问候消息",
            default_value=[],
            help_text="添加您自己的问候消息（每行一条）"
        )
        
        builder.add_checkbox(
            key="show_on_startup",
            label="启动时显示问候",
            default_value=True,
            help_text="应用启动时是否显示问候消息"
        )
        
        builder.add_checkbox(
            key="show_on_idle",
            label="空闲时显示问候",
            default_value=True,
            help_text="用户空闲时是否显示问候消息"
        )

# 设置界面入口函数，必须返回设置界面类
def settings_entry():
    return GreetingSettings
```

### 步骤5：创建资源文件夹

创建资源目录并添加图标文件：

```bash
mkdir -p resources
# 添加一个图标文件到resources/icon.png
```

### 步骤6：测试插件

1. 启动Hollow-ming应用
2. 进入插件管理界面
3. 启用"Greeting Plugin"
4. 检查插件是否正常工作

## 插件API参考

Hollow-ming为插件提供了丰富的API，允许插件与应用的各个部分交互。以下是主要API类别的概述：

### 核心API

通过`self.api`访问的核心功能：

| 方法 | 描述 |
|------|------|
| `show_message(text, duration=3000)` | 显示桌宠消息气泡 |
| `play_animation(anim_name)` | 播放特定动画 |
| `play_sound(sound_name)` | 播放音效 |
| `get_character()` | 获取当前角色信息 |
| `set_state(state_name)` | 设置角色状态 |
| `execute_action(action_name, **params)` | 执行指定动作 |

### 事件API

通过`self.register_event`和`self.unregister_event`管理事件监听：

```python
# 注册事件监听
self.register_event(EventType.MOUSE_CLICK, self.on_mouse_click)

# 取消事件监听
self.unregister_event(EventType.MOUSE_CLICK, self.on_mouse_click)
```

主要事件类型（`EventType`枚举）：

| 事件类型 | 描述 |
|---------|------|
| `APPLICATION_START` | 应用启动 |
| `APPLICATION_READY` | 应用就绪 |
| `APPLICATION_EXIT` | 应用退出 |
| `MOUSE_CLICK` | 鼠标点击 |
| `MOUSE_MOVE` | 鼠标移动 |
| `KEYBOARD_SHORTCUT` | 键盘快捷键 |
| `CHARACTER_CHANGE` | 角色变更 |
| `USER_IDLE` | 用户空闲 |
| `USER_RETURN` | 用户返回 |
| `TRAY_MENU_CLICK` | 托盘菜单点击 |

### 配置API

通过`self.get_config`和`self.save_config`管理插件配置：

```python
# 获取配置
config = self.get_config()
interval = config.get("interval", 3600)

# 保存配置
config["interval"] = 7200
self.save_config(config)
```

### 资源API

通过`self.get_resource`访问插件资源：

```python
# 加载图像资源
image = self.get_resource("images/icon.png")

# 加载音频资源
sound = self.get_resource("sounds/notification.wav")

# 加载文本资源
text = self.get_resource("texts/messages.txt", as_text=True)
```

### 日志API

通过`self.logger`记录日志：

```python
self.logger.debug("调试信息")
self.logger.info("一般信息")
self.logger.warning("警告信息")
self.logger.error("错误信息")
self.logger.critical("严重错误")
```

### UI API

通过`self.create_window`创建自定义窗口：

```python
def show_custom_ui(self):
    window = self.create_window(
        title="插件界面",
        width=400,
        height=300,
        resizable=True
    )
    
    # 使用FormBuilder构建UI
    from status.ui import FormBuilder
    builder = FormBuilder(window)
    builder.add_label("这是一个自定义界面")
    builder.add_button("确定", self.on_button_click)
    
    window.show()
```

## 插件生命周期

Hollow-ming插件的生命周期包括以下阶段：

### 1. 发现

Hollow-ming在启动时扫描`plugins`目录，识别所有包含有效`plugin.json`文件的插件。

### 2. 加载

当插件被启用时，插件管理器会：
1. 读取`plugin.json`文件
2. 导入插件的主模块
3. 调用`plugin_entry`函数获取插件实例
4. 调用插件的`on_load`方法

### 3. 运行

插件加载后进入运行状态，可以：
- 响应事件
- 执行定时任务
- 与用户交互
- 访问应用功能

### 4. 卸载

当插件被禁用或应用关闭时，插件管理器会：
1. 调用插件的`on_unload`方法
2. 清理插件注册的事件监听器和定时器
3. 释放插件占用的资源

### 钩子方法

插件类（继承自`PluginBase`）可以实现以下钩子方法：

| 方法 | 调用时机 | 返回值 |
|------|---------|-------|
| `on_load()` | 插件加载时 | 布尔值，指示加载是否成功 |
| `on_unload()` | 插件卸载时 | 布尔值，指示卸载是否成功 |
| `on_enable()` | 插件启用时 | 无 |
| `on_disable()` | 插件禁用时 | 无 |
| `on_config_changed()` | 配置变更时 | 无 |

## 最佳实践

开发Hollow-ming插件时，请遵循以下最佳实践：

### 代码质量

- **遵循PEP 8**：遵循Python的代码风格指南
- **添加文档**：为类、方法和函数添加docstring
- **类型提示**：使用类型注解提高代码可读性
- **异常处理**：妥善处理异常，避免插件崩溃影响主应用

### 性能优化

- **避免阻塞主线程**：将耗时操作放入后台线程
- **谨慎使用资源**：及时释放不再使用的资源
- **避免频繁IO**：缓存经常访问的数据
- **合理使用定时器**：避免过高频率的定时任务

### 安全考虑

- **输入验证**：验证所有外部输入
- **权限控制**：遵循最小权限原则
- **安全存储**：敏感数据使用加密存储
- **第三方库**：谨慎引入第三方依赖

### 用户体验

- **响应式UI**：保持界面响应流畅
- **清晰提示**：提供明确的操作反馈
- **渐进式设置**：提供基本和高级设置选项
- **国际化支持**：考虑多语言支持

### 兼容性

- **版本检查**：明确声明兼容的Hollow-ming版本
- **向前兼容**：处理配置格式变更
- **平台适配**：考虑不同操作系统的差异
- **清理资源**：确保插件卸载时彻底清理资源

## 插件分发

### 打包插件

打包插件的标准格式是`.hmp`文件（Hollow-ming Plugin），这实际上是一个ZIP文件，包含所有插件文件。

使用以下命令创建插件包：

```bash
cd /path/to/hollow-ming/plugins
zip -r greeting_plugin.hmp greeting_plugin/
```

### 插件元数据要求

确保您的`plugin.json`包含以下必要字段：

- `name`：插件显示名称
- `id`：插件唯一标识符（小写字母、数字和下划线）
- `version`：符合语义化版本的版本号
- `description`：简短描述
- `author`：作者姓名
- `requires`：依赖信息，特别是兼容的Hollow-ming版本

### 发布渠道

您可以通过以下渠道分享您的插件：

1. **Hollow-ming官方插件仓库**：
   - 提交到官方插件仓库需要经过审核
   - 访问[提交页面](https://hollow-ming.com/plugins/submit)（需要账号）

2. **GitHub或其他代码托管平台**：
   - 创建专门的仓库托管您的插件
   - 使用Releases功能发布版本

3. **插件论坛**：
   - 在[Hollow-ming社区论坛](https://forum.hollow-ming.com)的插件板块分享

### 版本升级

发布插件更新时：

1. 更新`plugin.json`中的版本号
2. 在仓库中添加CHANGELOG.md记录变更
3. 通过相同渠道发布更新版本

## 示例插件

以下是几个示例插件，展示不同类型的功能实现：

### 天气插件示例

这个示例展示如何创建一个集成外部API的插件：

```python
"""
Weather Plugin - 显示当前天气的插件
"""

import requests
from status.plugin import PluginBase
from status.event import EventType

class WeatherPlugin(PluginBase):
    def __init__(self, plugin_manager):
        super().__init__(plugin_manager)
        self.api_key = ""
        self.city = "Beijing"
        self.update_interval = 3600  # 1小时更新一次
        
    def on_load(self):
        # 获取配置
        config = self.get_config()
        self.api_key = config.get("api_key", "")
        self.city = config.get("city", "Beijing")
        self.update_interval = config.get("update_interval", 3600)
        
        # 如果没有API密钥，显示错误
        if not self.api_key:
            self.logger.error("未配置API密钥")
            self.api.show_message("天气插件：请配置API密钥")
            return False
            
        # 注册定时更新
        self.register_timer(self.update_weather, self.update_interval)
        
        # 添加菜单项
        self.add_menu_item("显示天气", self.show_weather_now)
        
        # 首次更新天气
        self.update_weather()
        return True
    
    def update_weather(self):
        """更新天气数据"""
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={self.city}&appid={self.api_key}&lang=zh_cn&units=metric"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if response.status_code == 200:
                temp = data["main"]["temp"]
                weather = data["weather"][0]["description"]
                self.last_weather = f"{self.city}: {temp}°C, {weather}"
                self.logger.info(f"天气更新成功: {self.last_weather}")
            else:
                self.logger.error(f"天气更新失败: {data.get('message', '未知错误')}")
        except Exception as e:
            self.logger.error(f"天气更新异常: {str(e)}")
    
    def show_weather_now(self):
        """立即显示天气"""
        if hasattr(self, "last_weather"):
            self.api.show_message(self.last_weather, 5000)
        else:
            self.api.show_message("正在获取天气...", 2000)
            self.update_weather()

def plugin_entry(plugin_manager):
    return WeatherPlugin(plugin_manager)
```

### 更多示例

您可以参考以下官方示例插件：

- [系统监控插件](https://github.com/hollow-ming/system-monitor-plugin)：展示如何收集和显示系统信息
- [提醒插件](https://github.com/hollow-ming/reminder-plugin)：演示如何创建和管理提醒
- [翻译插件](https://github.com/hollow-ming/translator-plugin)：展示如何集成第三方API和创建自定义界面

## 故障排除

### 常见问题

#### 插件无法加载

可能原因：
- `plugin.json`格式错误
- 缺少必要依赖
- 入口点函数未正确定义
- Python版本不兼容

解决方法：
- 检查日志文件（`%APPDATA%\Hollow-ming\logs\plugins.log`）
- 验证`plugin.json`格式
- 确保所有依赖已安装
- 检查入口点函数名称是否为`plugin_entry`

#### 插件加载但不工作

可能原因：
- 事件注册失败
- 配置访问错误
- 异常未捕获
- API使用不正确

解决方法：
- 添加详细日志输出
- 检查事件注册代码
- 验证配置访问逻辑
- 使用try-except捕获并记录异常

#### 插件影响应用性能

可能原因：
- 过于频繁的操作
- 阻塞主线程的耗时操作
- 内存泄漏
- 过多的资源使用

解决方法：
- 减少定时器频率
- 使用线程执行耗时操作
- 减少资源使用并及时释放
- 使用性能分析工具识别瓶颈

### 调试技巧

#### 启用调试日志

```python
# 在插件初始化时启用调试日志
def on_load(self):
    self.logger.setLevel("DEBUG")
    self.logger.debug("调试模式已启用")
```

#### 显示调试信息

```python
# 在桌面显示调试信息
self.api.show_message(f"调试: {debug_info}", duration=3000)
```

#### 检查插件状态

在应用的插件管理界面中，可以查看插件的状态和错误信息。

#### 使用调试器

可以使用IDE调试器（如PyCharm或VS Code）附加到正在运行的Hollow-ming进程进行调试。

---

## 获取帮助

如果您在开发插件过程中遇到问题，可以通过以下渠道获取帮助：

- [官方文档](https://docs.hollow-ming.com)
- [开发者论坛](https://forum.hollow-ming.com/developers)
- [GitHub仓库](https://github.com/hollow-ming/hollow-ming)
- [开发者Discord频道](https://discord.gg/hollow-ming-dev)

我们也欢迎您提交改进建议和贡献代码，帮助我们完善插件系统！ 