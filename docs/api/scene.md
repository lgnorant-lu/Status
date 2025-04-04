# 场景系统 API 参考

## 模块概述

场景系统（Scene System）是 Hollow-ming 的核心组件之一，负责管理、组织和切换应用程序中的不同场景。它提供了一个统一的框架来处理场景的创建、加载、过渡和销毁等生命周期事件，同时支持场景元素的布局和管理。

场景系统的主要功能包括：
- 场景的创建和管理
- 场景之间的切换和过渡效果
- 场景元素的组织和层级管理
- 场景状态的保存和恢复
- 场景资源的加载和释放

## 主要类和接口

### 场景管理

#### `SceneManager`

全局场景管理器，负责场景的加载、切换和卸载。

**主要方法：**

- `get_instance()` - 获取场景管理器的单例实例
- `load_scene(scene_id, params=None)` - 加载指定ID的场景
- `switch_scene(scene_id, transition=None, params=None)` - 切换到指定场景
- `push_scene(scene_id, params=None)` - 将新场景压入场景堆栈
- `pop_scene()` - 弹出当前场景，返回上一个场景
- `get_current_scene()` - 获取当前活动场景
- `get_scene_by_id(scene_id)` - 通过ID获取场景实例
- `register_scene(scene_class, scene_id)` - 注册场景类和ID的映射
- `unregister_scene(scene_id)` - 取消注册场景
- `apply_transition(transition, from_scene, to_scene)` - 应用转场效果

#### `SceneFactory`

场景工厂类，负责创建不同类型的场景实例。

**主要方法：**

- `create_scene(scene_id, params=None)` - 创建指定类型的场景
- `register_creator(scene_id, creator_func)` - 注册场景创建函数
- `unregister_creator(scene_id)` - 取消注册场景创建函数
- `get_registered_scenes()` - 获取所有已注册的场景类型

### 场景基类

#### `SceneBase`

所有场景类的基类，定义了场景的基本接口和生命周期方法。

**主要属性：**

- `scene_id` - 场景的唯一标识符
- `state` - 当前场景的状态（如初始化、活动、暂停等）
- `layers` - 场景中的层集合
- `elements` - 场景中的元素集合
- `params` - 传递给场景的参数

**主要方法：**

- `initialize()` - 初始化场景
- `load()` - 加载场景资源
- `activate()` - 激活场景
- `deactivate()` - 停用场景
- `update(delta_time)` - 更新场景状态
- `render()` - 渲染场景
- `handle_event(event)` - 处理场景事件
- `pause()` - 暂停场景
- `resume()` - 恢复场景
- `unload()` - 卸载场景资源
- `add_element(element, layer=None)` - 添加场景元素
- `remove_element(element)` - 移除场景元素
- `get_element_by_id(element_id)` - 获取指定ID的元素
- `save_state()` - 保存场景状态
- `restore_state(state)` - 恢复场景状态

### 场景特化类

#### `MainScene`

应用程序的主界面场景，显示桌面宠物的默认状态。

**特有方法：**

- `set_default_behavior(behavior)` - 设置默认行为
- `toggle_menu()` - 切换菜单显示状态
- `handle_desktop_interaction(interaction_type)` - 处理桌面交互

#### `InteractionScene`

用户交互场景，处理特定交互行为。

**特有方法：**

- `set_interaction_mode(mode)` - 设置交互模式
- `process_input(input_data)` - 处理用户输入
- `complete_interaction()` - 完成交互并返回

#### `DialogueScene`

对话场景，展示与桌面宠物的对话内容。

**特有方法：**

- `display_dialogue(dialogue_data)` - 显示对话内容
- `advance_dialogue()` - 推进对话
- `select_option(option_index)` - 选择对话选项
- `end_dialogue(result=None)` - 结束对话

#### `EventScene`

事件响应场景，用于显示特殊事件。

**特有方法：**

- `trigger_event(event_id, event_data)` - 触发特定事件
- `set_event_duration(duration)` - 设置事件持续时间
- `cancel_event()` - 取消当前事件

#### `IdleScene`

空闲状态场景，在用户长时间无操作时显示。

**特有方法：**

- `set_idle_behavior(behavior)` - 设置空闲行为
- `set_wake_conditions(conditions)` - 设置唤醒条件
- `check_wake_condition()` - 检查是否满足唤醒条件

### 场景层管理

#### `SceneLayer`

场景层基类，用于组织场景中的视觉元素。

**主要属性：**

- `visible` - 层是否可见
- `opacity` - 层的不透明度
- `z_index` - 层的Z轴索引
- `elements` - 层中包含的元素

**主要方法：**

- `add_element(element)` - 添加元素到层
- `remove_element(element)` - 从层中移除元素
- `set_visibility(visible)` - 设置层的可见性
- `set_opacity(opacity)` - 设置层的不透明度
- `update(delta_time)` - 更新层中的元素
- `render()` - 渲染层及其元素

#### `BackgroundLayer`

背景层，用于渲染场景背景。

**特有方法：**

- `set_background(image_path)` - 设置背景图像
- `set_parallax(enabled, factor=0.5)` - 设置视差滚动效果
- `set_ambient_sound(sound_path)` - 设置环境音效

#### `ContentLayer`

内容层，包含场景的主要内容元素。

**特有方法：**

- `set_layout(layout)` - 设置内容布局
- `group_elements(elements, group_id)` - 将元素分组
- `set_content_area(rect)` - 设置内容区域

#### `UILayer`

UI层，包含用户界面元素。

**特有方法：**

- `add_control(control)` - 添加UI控件
- `remove_control(control)` - 移除UI控件
- `set_control_enabled(control_id, enabled)` - 设置控件启用状态
- `set_ui_theme(theme)` - 设置UI主题

#### `EffectLayer`

效果层，用于渲染视觉效果。

**特有方法：**

- `add_effect(effect)` - 添加视觉效果
- `remove_effect(effect_id)` - 移除视觉效果
- `set_global_filter(filter_type, params)` - 设置全局滤镜
- `clear_effects()` - 清除所有效果

#### `PopupLayer`

弹出层，用于显示弹出窗口和通知。

**特有方法：**

- `show_popup(popup_data)` - 显示弹出窗口
- `close_popup(popup_id)` - 关闭弹出窗口
- `show_notification(message, duration=3.0)` - 显示通知消息
- `clear_all_popups()` - 清除所有弹出内容

### 场景元素

#### `SceneElement`

场景元素基类，表示场景中的可视组件。

**主要属性：**

- `element_id` - 元素的唯一标识符
- `position` - 元素在场景中的位置
- `size` - 元素的尺寸
- `rotation` - 元素的旋转角度
- `scale` - 元素的缩放比例
- `visible` - 元素是否可见
- `alpha` - 元素的透明度

**主要方法：**

- `initialize(params=None)` - 初始化元素
- `update(delta_time)` - 更新元素状态
- `render()` - 渲染元素
- `set_position(x, y)` - 设置元素位置
- `set_size(width, height)` - 设置元素尺寸
- `set_rotation(angle)` - 设置元素旋转角度
- `set_scale(scale_x, scale_y)` - 设置元素缩放比例
- `set_visibility(visible)` - 设置元素可见性
- `set_alpha(alpha)` - 设置元素透明度
- `handle_event(event)` - 处理元素事件
- `contains_point(x, y)` - 检查点是否在元素内
- `get_bounds()` - 获取元素的边界矩形

#### `SpriteElement`

精灵元素，用于显示图像或动画。

**特有方法：**

- `set_image(image_path)` - 设置精灵图像
- `set_animation(animation_data)` - 设置精灵动画
- `play_animation(animation_name, loop=False)` - 播放动画序列
- `stop_animation()` - 停止当前动画
- `set_frame(frame_index)` - 设置当前帧索引

#### `TextElement`

文本元素，用于显示文字内容。

**特有方法：**

- `set_text(text)` - 设置文本内容
- `set_font(font_name, font_size)` - 设置字体
- `set_color(color)` - 设置文本颜色
- `set_alignment(alignment)` - 设置文本对齐方式
- `set_word_wrap(enabled, width=None)` - 设置自动换行

#### `ContainerElement`

容器元素，可包含和管理其他元素。

**特有方法：**

- `add_child(child_element)` - 添加子元素
- `remove_child(child_element)` - 移除子元素
- `clear_children()` - 清除所有子元素
- `get_child_by_id(element_id)` - 获取指定ID的子元素
- `set_layout(layout_type, params=None)` - 设置子元素布局

#### `EffectElement`

特效元素，用于显示粒子、光影等特殊效果。

**特有方法：**

- `set_effect_type(effect_type)` - 设置效果类型
- `set_parameters(params)` - 设置效果参数
- `start_effect(duration=None)` - 开始播放效果
- `stop_effect()` - 停止效果
- `reset_effect()` - 重置效果状态

### 转场系统

#### `TransitionSystem`

管理场景转换效果的系统。

**主要方法：**

- `get_instance()` - 获取转场系统实例
- `register_transition(transition_id, transition_class)` - 注册转场效果
- `create_transition(transition_id, params=None)` - 创建转场实例
- `get_available_transitions()` - 获取所有可用的转场效果
- `apply_transition(transition, from_scene, to_scene, completion_callback=None)` - 应用转场效果

#### `Transition`

转场效果基类，定义转场效果的通用接口。

**主要属性：**

- `duration` - 转场持续时间
- `easing` - 缓动函数
- `from_scene` - 源场景
- `to_scene` - 目标场景
- `progress` - 当前转场进度

**主要方法：**

- `initialize(from_scene, to_scene)` - 初始化转场
- `update(delta_time)` - 更新转场状态
- `render()` - 渲染转场效果
- `start()` - 开始转场
- `finish()` - 完成转场
- `cancel()` - 取消转场
- `set_completion_callback(callback)` - 设置完成回调函数

#### `FadeTransition`

淡入淡出转场效果。

**特有方法：**

- `set_fade_color(color)` - 设置淡入淡出的颜色
- `set_fade_mode(mode)` - 设置淡入淡出模式（如交叉淡入淡出）

#### `SlideTransition`

滑动转场效果。

**特有方法：**

- `set_direction(direction)` - 设置滑动方向
- `set_slide_mode(mode)` - 设置滑动模式（如推动、覆盖）

#### `ScaleTransition`

缩放转场效果。

**特有方法：**

- `set_scale_origin(origin_x, origin_y)` - 设置缩放原点
- `set_scale_mode(mode)` - 设置缩放模式（如缩小消失、放大出现）

#### `RotateTransition`

旋转转场效果。

**特有方法：**

- `set_rotation_center(center_x, center_y)` - 设置旋转中心
- `set_rotation_direction(direction)` - 设置旋转方向
- `set_rotation_amount(degrees)` - 设置旋转角度

## 枚举和常量

### `SceneState`

描述场景状态的枚举。

- `UNINITIALIZED` - 未初始化状态
- `INITIALIZING` - 正在初始化
- `LOADING` - 正在加载资源
- `ACTIVE` - 活动状态
- `PAUSED` - 暂停状态
- `DEACTIVATING` - 正在停用
- `UNLOADING` - 正在卸载资源
- `DESTROYED` - 已销毁

### `LayerType`

定义场景层类型的枚举。

- `BACKGROUND` - 背景层
- `CONTENT` - 内容层
- `UI` - 用户界面层
- `EFFECT` - 特效层
- `POPUP` - 弹出层

### `TransitionType`

定义转场效果类型的枚举。

- `NONE` - 无转场效果
- `FADE` - 淡入淡出
- `SLIDE` - 滑动
- `SCALE` - 缩放
- `ROTATE` - 旋转
- `DISSOLVE` - 溶解
- `PIXELATE` - 像素化
- `CUSTOM` - 自定义转场

### `ElementAlignment`

定义元素对齐方式的枚举。

- `TOP_LEFT` - 左上对齐
- `TOP_CENTER` - 顶部居中对齐
- `TOP_RIGHT` - 右上对齐
- `MIDDLE_LEFT` - 左侧中间对齐
- `CENTER` - 居中对齐
- `MIDDLE_RIGHT` - 右侧中间对齐
- `BOTTOM_LEFT` - 左下对齐
- `BOTTOM_CENTER` - 底部居中对齐
- `BOTTOM_RIGHT` - 右下对齐

### `LayoutType`

定义容器布局类型的枚举。

- `NONE` - 无布局
- `GRID` - 网格布局
- `HORIZONTAL` - 水平布局
- `VERTICAL` - 垂直布局
- `STACK` - 堆叠布局
- `ABSOLUTE` - 绝对位置布局

## 工具函数

### 场景工具

- `create_scene(scene_type, params=None)` - 快速创建指定类型的场景实例
- `register_scene_type(scene_id, scene_class)` - 注册场景类型
- `get_registered_scene_types()` - 获取所有注册的场景类型

### 转场工具

- `create_transition(transition_type, duration=1.0, params=None)` - 创建指定类型的转场效果
- `register_transition_type(transition_id, transition_class)` - 注册转场效果类型
- `get_transition_types()` - 获取所有可用的转场效果类型

### 布局工具

- `create_layout(layout_type, params=None)` - 创建指定类型的布局
- `apply_layout(container, layout_type, params=None)` - 对容器应用布局
- `calculate_layout(elements, layout_type, container_size, params=None)` - 计算元素布局位置

### 辅助工具

- `capture_scene_snapshot(scene)` - 捕获场景的快照图像
- `save_scene_state(scene, file_path=None)` - 保存场景状态到文件
- `load_scene_state(file_path)` - 从文件加载场景状态
- `convert_coordinates(x, y, from_space, to_space)` - 在不同坐标空间之间转换坐标

## 异常类

### `SceneError`

场景系统的基本异常类。

### `SceneInitializationError`

场景初始化过程中的错误。

### `SceneLoadError`

加载场景资源时的错误。

### `SceneStateError`

场景状态操作错误，如在错误的状态下执行操作。

### `ElementError`

场景元素操作错误。

### `LayoutError`

布局相关错误。

### `TransitionError`

转场效果执行错误。 