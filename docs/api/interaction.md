# 交互系统 API 参考

## 模块概述

交互系统（Interaction System）是 Hollow-ming 的核心组件之一，负责处理所有用户与桌面宠物之间的交互行为。该系统提供了统一的事件处理框架，支持多种交互方式，包括鼠标交互、键盘交互、系统托盘交互、文件拖放和全局热键等。

交互系统的主要功能包括：
- 用户输入事件的捕获与处理
- 不同交互类型的管理与分发
- 交互事件的过滤与节流
- 桌面宠物行为的触发
- 系统托盘菜单的管理
- 全局热键的注册与响应
- 拖拽操作的处理

## 主要类和接口

### 交互管理

#### `InteractionManager`

全局交互管理器，负责协调所有交互子系统的运行。

**主要属性：**

- `enabled` - 是否启用交互系统
- `active_systems` - 当前活动的交互子系统集合
- `event_bus` - 交互事件总线
- `event_queue` - 待处理的事件队列

**主要方法：**

- `get_instance()` - 获取交互管理器的单例实例
- `initialize()` - 初始化交互系统
- `shutdown()` - 关闭交互系统
- `register_system(system)` - 注册交互子系统
- `unregister_system(system_id)` - 注销交互子系统
- `enable_system(system_id)` - 启用特定的交互子系统
- `disable_system(system_id)` - 禁用特定的交互子系统
- `process_events()` - 处理所有待处理的交互事件
- `dispatch_event(event)` - 分发交互事件到对应的处理系统
- `post_event(event)` - 发布事件到事件队列
- `add_event_listener(event_type, listener)` - 添加事件监听器
- `remove_event_listener(event_type, listener)` - 移除事件监听器
- `get_system(system_id)` - 获取指定ID的交互子系统

### 事件过滤与节流

#### `EventFilter`

事件过滤器，用于过滤冗余或无用的事件。

**主要方法：**

- `filter(event)` - 过滤事件，返回是否保留该事件
- `set_filter_rule(event_type, rule)` - 设置特定事件类型的过滤规则
- `remove_filter_rule(event_type)` - 移除特定事件类型的过滤规则
- `clear_rules()` - 清除所有过滤规则

#### `EventThrottler`

事件节流器，用于控制高频事件的处理速率。

**主要方法：**

- `throttle(event)` - 对事件进行节流处理，返回是否应处理该事件
- `set_throttle_rule(event_type, strategy, params)` - 设置节流规则
- `remove_throttle_rule(event_type)` - 移除节流规则
- `reset()` - 重置所有节流状态

### 交互子系统

#### `InteractionSystem`

所有交互子系统的基类，定义了交互系统的基本接口。

**主要属性：**

- `system_id` - 子系统的唯一标识符
- `enabled` - 子系统是否启用
- `priority` - 事件处理的优先级

**主要方法：**

- `initialize()` - 初始化子系统
- `shutdown()` - 关闭子系统
- `can_handle_event(event)` - 检查是否可以处理特定事件
- `handle_event(event)` - 处理交互事件
- `update(delta_time)` - 更新子系统状态
- `set_enabled(enabled)` - 设置子系统启用状态
- `set_priority(priority)` - 设置子系统优先级

#### `MouseInteractionSystem`

处理鼠标相关交互的子系统。

**特有属性：**

- `hover_elements` - 当前鼠标悬停的元素
- `click_position` - 最近点击的位置
- `is_dragging` - 是否正在拖动
- `drag_target` - 当前拖动的目标

**特有方法：**

- `register_click_handler(handler)` - 注册点击处理器
- `register_hover_handler(handler)` - 注册悬停处理器
- `register_drag_handler(handler)` - 注册拖动处理器
- `start_drag(target, position)` - 开始拖动操作
- `end_drag()` - 结束拖动操作
- `set_click_detection_area(rect)` - 设置点击检测区域
- `get_mouse_position()` - 获取当前鼠标位置

#### `SystemTraySystem`

管理系统托盘图标和菜单的子系统。

**特有属性：**

- `tray_icon` - 系统托盘图标
- `tray_menu` - 系统托盘菜单
- `notification_enabled` - 是否启用通知

**特有方法：**

- `set_icon(icon_path)` - 设置托盘图标
- `set_tooltip(tooltip)` - 设置托盘图标提示文本
- `build_menu(menu_items)` - 构建托盘菜单
- `update_menu_item(item_id, properties)` - 更新菜单项
- `show_notification(title, message, duration=5000)` - 显示托盘通知
- `set_notification_enabled(enabled)` - 设置通知启用状态

#### `MenuInteractionSystem`

处理菜单交互的子系统。

**特有属性：**

- `active_menu` - 当前活动的菜单
- `menu_definitions` - 菜单定义集合

**特有方法：**

- `register_menu(menu_id, definition)` - 注册菜单定义
- `show_menu(menu_id, position)` - 显示指定菜单
- `hide_menu()` - 隐藏当前菜单
- `add_menu_item(menu_id, item)` - 添加菜单项
- `remove_menu_item(menu_id, item_id)` - 移除菜单项
- `enable_menu_item(menu_id, item_id, enabled)` - 启用/禁用菜单项
- `handle_menu_selection(menu_id, item_id)` - 处理菜单项选择

#### `HotkeySystem`

管理全局热键的子系统。

**特有属性：**

- `registered_hotkeys` - 已注册的热键集合
- `hotkey_handlers` - 热键处理器映射

**特有方法：**

- `register_hotkey(hotkey_id, key_combination, handler)` - 注册热键
- `unregister_hotkey(hotkey_id)` - 注销热键
- `modify_hotkey(hotkey_id, new_key_combination)` - 修改热键组合
- `is_hotkey_registered(hotkey_id)` - 检查热键是否已注册
- `get_hotkey_combination(hotkey_id)` - 获取热键组合
- `handle_key_event(key_event)` - 处理键盘事件

#### `DragSystem`

管理拖拽操作的子系统。

**特有属性：**

- `drag_enabled` - 是否启用拖拽
- `drag_state` - 当前拖拽状态
- `boundaries` - 拖拽边界
- `snap_edges` - 是否启用边缘吸附

**特有方法：**

- `start_drag(object, initial_position)` - 开始拖拽
- `update_drag(current_position)` - 更新拖拽位置
- `end_drag()` - 结束拖拽
- `set_boundaries(rect)` - 设置拖拽边界
- `enable_edge_snapping(enabled, snap_distance=10)` - 启用边缘吸附
- `set_drag_enabled(enabled)` - 设置拖拽启用状态
- `save_position()` - 保存当前位置

#### `BehaviorTriggerSystem`

基于各种条件触发桌面宠物行为的子系统。

**特有属性：**

- `triggers` - 已注册的触发器集合
- `active_behaviors` - 当前活动的行为

**特有方法：**

- `register_trigger(trigger_id, conditions, behavior)` - 注册触发器
- `unregister_trigger(trigger_id)` - 注销触发器
- `evaluate_triggers(context)` - 评估所有触发器
- `execute_behavior(behavior_id, params=None)` - 执行特定行为
- `stop_behavior(behavior_id)` - 停止特定行为
- `add_condition(trigger_id, condition)` - 添加触发条件
- `remove_condition(trigger_id, condition_id)` - 移除触发条件

### 事件类

#### `InteractionEvent`

所有交互事件的基类。

**主要属性：**

- `event_type` - 事件类型
- `timestamp` - 事件发生时间戳
- `source` - 事件源
- `handled` - 事件是否已处理

**主要方法：**

- `get_type()` - 获取事件类型
- `get_timestamp()` - 获取事件时间戳
- `get_source()` - 获取事件源
- `is_handled()` - 检查事件是否已处理
- `set_handled(handled)` - 设置事件处理状态
- `clone()` - 创建事件的克隆

#### `MouseEvent`

鼠标相关事件。

**特有属性：**

- `position` - 鼠标位置
- `button` - 鼠标按钮
- `click_count` - 点击次数
- `delta` - 鼠标滚轮增量

**特有方法：**

- `get_position()` - 获取鼠标位置
- `get_button()` - 获取鼠标按钮
- `get_click_count()` - 获取点击次数
- `get_delta()` - 获取滚轮增量

#### `KeyEvent`

键盘相关事件。

**特有属性：**

- `key_code` - 键码
- `modifiers` - 修饰键状态
- `repeat_count` - 重复次数
- `is_auto_repeat` - 是否为自动重复

**特有方法：**

- `get_key_code()` - 获取键码
- `get_modifiers()` - 获取修饰键状态
- `has_modifier(modifier)` - 检查是否按下特定修饰键
- `get_key_combination()` - 获取键位组合

#### `MenuEvent`

菜单相关事件。

**特有属性：**

- `menu_id` - 菜单ID
- `item_id` - 菜单项ID
- `position` - 菜单位置

**特有方法：**

- `get_menu_id()` - 获取菜单ID
- `get_item_id()` - 获取菜单项ID
- `get_position()` - 获取菜单位置

#### `SystemTrayEvent`

系统托盘相关事件。

**特有属性：**

- `action` - 托盘动作类型
- `menu_item_id` - 菜单项ID

**特有方法：**

- `get_action()` - 获取托盘动作类型
- `get_menu_item_id()` - 获取菜单项ID

#### `DragEvent`

拖拽相关事件。

**特有属性：**

- `drag_target` - 拖拽目标
- `start_position` - 拖拽起始位置
- `current_position` - 当前位置
- `delta` - 位置变化量

**特有方法：**

- `get_drag_target()` - 获取拖拽目标
- `get_start_position()` - 获取起始位置
- `get_current_position()` - 获取当前位置
- `get_delta()` - 获取位置变化量

#### `HotkeyEvent`

热键相关事件。

**特有属性：**

- `hotkey_id` - 热键ID
- `key_combination` - 键位组合

**特有方法：**

- `get_hotkey_id()` - 获取热键ID
- `get_key_combination()` - 获取键位组合

## 枚举和常量

### `InteractionType`

定义交互类型的枚举。

- `MOUSE` - 鼠标交互
- `KEYBOARD` - 键盘交互
- `MENU` - 菜单交互
- `SYSTEM_TRAY` - 系统托盘交互
- `DRAG` - 拖拽交互
- `HOTKEY` - 热键交互
- `BEHAVIOR` - 行为交互

### `MouseEventType`

定义鼠标事件类型的枚举。

- `MOVE` - 鼠标移动
- `ENTER` - 鼠标进入
- `LEAVE` - 鼠标离开
- `DOWN` - 鼠标按下
- `UP` - 鼠标释放
- `CLICK` - 鼠标点击
- `DOUBLE_CLICK` - 鼠标双击
- `RIGHT_CLICK` - 鼠标右键点击
- `WHEEL` - 鼠标滚轮

### `KeyEventType`

定义键盘事件类型的枚举。

- `KEY_DOWN` - 键盘按下
- `KEY_UP` - 键盘释放
- `KEY_TYPED` - 键盘输入

### `MenuEventType`

定义菜单事件类型的枚举。

- `MENU_OPEN` - 菜单打开
- `MENU_CLOSE` - 菜单关闭
- `MENU_ITEM_SELECT` - 菜单项选择
- `MENU_ITEM_HOVER` - 菜单项悬停

### `SystemTrayActionType`

定义系统托盘动作类型的枚举。

- `ICON_CLICK` - 图标点击
- `ICON_DOUBLE_CLICK` - 图标双击
- `ICON_RIGHT_CLICK` - 图标右键点击
- `MENU_ITEM_CLICK` - 菜单项点击
- `BALLOON_SHOW` - 气球提示显示
- `BALLOON_CLOSE` - 气球提示关闭
- `BALLOON_TIMEOUT` - 气球提示超时
- `BALLOON_CLICK` - 气球提示点击

### `DragEventType`

定义拖拽事件类型的枚举。

- `DRAG_START` - 拖拽开始
- `DRAG_UPDATE` - 拖拽更新
- `DRAG_END` - 拖拽结束
- `DRAG_ENTER` - 拖拽进入区域
- `DRAG_LEAVE` - 拖拽离开区域
- `DROP` - 放置

### `MouseButton`

定义鼠标按钮的枚举。

- `LEFT` - 左键
- `MIDDLE` - 中键
- `RIGHT` - 右键
- `BUTTON4` - 按钮4
- `BUTTON5` - 按钮5

### `KeyModifier`

定义键盘修饰键的枚举。

- `SHIFT` - Shift键
- `CTRL` - Ctrl键
- `ALT` - Alt键
- `META` - Meta/Win键
- `NUM_LOCK` - Num Lock键
- `CAPS_LOCK` - Caps Lock键

### `ThrottleStrategy`

定义事件节流策略的枚举。

- `TIME` - 基于时间的节流
- `COUNT` - 基于计数的节流
- `LAST` - 仅处理最后一个事件
- `FIRST` - 仅处理第一个事件
- `SAMPLE` - 采样处理事件

## 工具函数

### 交互管理工具

- `initialize_interaction_system()` - 初始化交互系统
- `shutdown_interaction_system()` - 关闭交互系统
- `is_interaction_system_initialized()` - 检查交互系统是否已初始化
- `get_interaction_manager()` - 获取交互管理器实例

### 事件工具

- `create_event(event_type, params=None)` - 创建交互事件
- `post_event(event)` - 发布事件到事件队列
- `dispatch_event(event)` - 立即分发事件
- `add_global_event_listener(event_type, listener)` - 添加全局事件监听器
- `remove_global_event_listener(event_type, listener)` - 移除全局事件监听器

### 鼠标交互工具

- `get_mouse_position()` - 获取当前鼠标位置
- `is_mouse_button_down(button)` - 检查鼠标按钮是否按下
- `set_cursor(cursor_type)` - 设置鼠标光标类型
- `reset_cursor()` - 重置鼠标光标

### 热键工具

- `register_global_hotkey(hotkey_id, key_combination, handler)` - 注册全局热键
- `unregister_global_hotkey(hotkey_id)` - 注销全局热键
- `parse_key_combination(combination_string)` - 解析键位组合字符串
- `key_combination_to_string(key_combination)` - 转换键位组合为字符串

### 系统托盘工具

- `show_tray_notification(title, message, icon=None, duration=5000)` - 显示托盘通知
- `update_tray_icon(icon_path)` - 更新托盘图标
- `update_tray_tooltip(tooltip)` - 更新托盘提示文本
- `rebuild_tray_menu(menu_items)` - 重建托盘菜单

### 行为触发工具

- `trigger_behavior(behavior_id, params=None)` - 触发特定行为
- `register_behavior_trigger(trigger_id, conditions, behavior)` - 注册行为触发器
- `unregister_behavior_trigger(trigger_id)` - 注销行为触发器
- `create_condition(condition_type, params)` - 创建触发条件

## 异常类

### `InteractionError`

交互系统的基本异常类。

### `EventError`

事件处理相关的错误。

### `SystemError`

交互子系统相关的错误。

### `HotkeyError`

热键注册和处理的错误。

### `MenuError`

菜单操作的错误。

### `DragError`

拖拽操作的错误。

### `TriggerError`

行为触发器相关的错误。 