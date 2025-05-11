# 行为系统变更日志

## 版本 0.1.0 - 2023-11-12 - 行为系统基础实现

### 新增功能

#### 1. 状态机实现
- 添加状态机基类 `StateMachine`
- 实现状态定义与注册机制
- 添加状态转换条件支持
- 实现状态进入/退出回调
- 支持状态持续时间限制
- 添加状态转换事件
- 实现状态历史记录

#### 2. 行为管理器实现
- 创建行为管理器 `BehaviorManager`
- 实现行为注册与查找机制
- 添加行为创建工厂方法
- 实现行为执行与中断控制
- 支持行为优先级机制
- 添加行为组合支持
- 实现行为队列管理
- 支持行为执行回调
- 添加条件行为支持

#### 3. 测试用例
- 添加状态机单元测试
  - 测试状态注册与获取
  - 测试状态转换条件
  - 测试状态回调
  - 测试状态历史
- 添加行为管理器单元测试
  - 测试行为注册与查找
  - 测试行为创建
  - 测试行为执行与中断
  - 测试行为优先级
  - 测试行为组合与队列
  - 测试行为条件

### 代码结构

```
status/behavior/
├── __init__.py          # 模块初始化
├── state_machine.py     # 状态机实现
└── behavior_manager.py  # 行为管理器实现

tests/behavior/
├── __init__.py                # 测试初始化
├── test_state_machine.py      # 状态机测试
└── test_behavior_manager.py   # 行为管理器测试
```

### 详细变更

#### state_machine.py
- 实现 `State` 类，表示状态机中的一个状态
  - 添加状态名称、进入/退出回调
  - 支持状态持续时间限制
  - 实现状态条件检查
- 实现 `StateMachine` 类，管理状态转换
  - 添加状态注册与获取方法
  - 实现状态转换逻辑
  - 添加状态历史记录
  - 支持状态事件回调
  - 实现状态过渡条件

#### behavior_manager.py
- 实现 `Behavior` 类，表示一个行为
  - 添加行为名称、优先级、执行逻辑
  - 支持行为条件检查
  - 实现行为执行回调
- 实现 `BehaviorManager` 类，管理行为
  - 添加行为注册与查找方法
  - 实现行为创建工厂
  - 添加行为执行控制
  - 支持行为队列管理
  - 实现行为组合
  - 支持行为中断机制

#### test_state_machine.py
- 添加状态机基本功能测试
- 测试状态注册与获取
- 验证状态转换条件
- 测试状态回调执行
- 验证状态历史记录

#### test_behavior_manager.py
- 添加行为管理器基本功能测试
- 测试行为注册与查找
- 验证行为创建逻辑
- 测试行为执行控制
- 验证行为优先级机制
- 测试行为组合与队列
- 验证行为条件检查

### API示例

```python
# 状态机使用示例
state_machine = StateMachine()
state_machine.add_state("idle", on_enter=idle_enter, on_exit=idle_exit)
state_machine.add_state("walking", duration=5.0)
state_machine.add_transition("idle", "walking", condition=should_walk)
state_machine.set_state("idle")

# 行为管理器使用示例
behavior_manager = BehaviorManager()
behavior_manager.register_behavior("idle", IdleBehavior)
behavior_manager.register_behavior("walk", WalkBehavior)
idle_behavior = behavior_manager.create_behavior("idle")
behavior_manager.execute_behavior(idle_behavior)
```

### 下一步计划

1. 实现环境感知器 `EnvironmentSensor`
   - 添加屏幕边界感知
   - 实现窗口位置感知
   - 添加桌面物体检测

2. 开发决策系统 `DecisionMaker`
   - 实现基于规则的决策
   - 添加决策树
   - 支持基于概率的选择

3. 实现具体行为
   - 添加空闲行为
   - 实现移动行为
   - 添加反应行为

### 已知问题

- 状态机在快速切换状态时可能存在竞态条件
- 行为管理器在高优先级行为多次中断时可能导致行为栈增长过多
- 需要添加更多测试用例覆盖边缘情况

### 贡献者

- Ignorant-lu 