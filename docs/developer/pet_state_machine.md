# 状态机系统设计文档

## 概述

状态机系统是Status-Ming项目的核心组件，负责根据系统状态（如CPU、内存使用率等）、时间状态（如早晨、晚上等）、特殊日期（如节日）以及用户交互来决定桌宠应该显示的状态和行为。

## 核心组件

### PetStateMachine

`PetStateMachine`是状态机的主要实现类，负责处理所有状态转换和优先级决策。它通过一系列的状态更新方法接收来自不同来源的状态信息，并根据预定义的优先级规则决定最终显示的状态。

### PetState

`PetState`是一个枚举类，定义了所有可能的桌宠状态。状态分为以下几个主要类别：

1. **系统资源状态**：如IDLE、LIGHT_LOAD、MODERATE_LOAD等，反映系统资源（CPU、内存、GPU等）的使用情况
2. **时间相关状态**：如MORNING、NOON、AFTERNOON等，反映一天中的不同时段
3. **特殊日期状态**：如BIRTHDAY、NEW_YEAR等，反映特殊日期或节日
4. **用户交互状态**：如CLICKED、DRAGGED、PETTED等，反映用户与桌宠的交互

### StateCategory

`StateCategory`枚举定义了状态的分类，用于在状态机内部组织和管理状态。主要类别包括：

- `SYSTEM`：系统资源相关状态
- `TIME`：时间相关状态
- `SPECIAL_DATE`：特殊日期相关状态
- `INTERACTION`：用户交互相关状态

## 状态优先级系统

状态机使用数值优先级系统来决定多个状态同时存在时应该显示哪个状态。优先级值越高，状态优先级越高。

### 优先级值（从高到低）

```
用户交互状态（150-130）：
- CLICKED, DRAGGED, PETTED: 150（最高优先级）
- HAPPY, SAD, ANGRY, PLAY: 130

系统状态（120-5）：
- MEMORY_CRITICAL: 120
- CPU_CRITICAL: 110
- MEMORY_WARNING: 105
- VERY_HEAVY_LOAD: 100
- GPU_VERY_BUSY: 95
- HEAVY_LOAD: 90
- DISK_VERY_BUSY: 88
- NETWORK_VERY_BUSY: 87
- GPU_BUSY: 85
- MODERATE_LOAD: 80
- DISK_BUSY: 75
- LIGHT_LOAD: 70
- NETWORK_BUSY: 70
- IDLE: 10
- SYSTEM_IDLE: 5（最低优先级）

特殊日期状态（95）：
- BIRTHDAY, NEW_YEAR, VALENTINE: 95

时间状态（30-20）：
- NIGHT: 30（夜晚优先级略高）
- MORNING, NOON, AFTERNOON, EVENING: 20
```

### 优先级决策逻辑

1. 同一类别内，使用状态优先级数值决定显示哪个状态
2. 不同类别间，按照 `INTERACTION > SPECIAL_DATE > SYSTEM > TIME` 的顺序进行优先级判断
3. 如果没有任何活动状态，则默认使用 `IDLE` 状态

## 状态更新机制

状态机通过以下方法接收状态更新：

### 系统资源状态更新

```python
update(cpu_usage: float, memory_usage: float, gpu_usage: float = 0.0, 
       disk_usage: float = 0.0, network_usage: float = 0.0) -> bool
```

此方法接收各种系统资源的使用率，并根据预定义的阈值更新状态机的系统状态。

- CPU使用率基于多个阈值划分为不同级别（IDLE、LIGHT_LOAD、MODERATE_LOAD等）
- 内存使用率超过警告或临界阈值时设置MEMORY_WARNING或MEMORY_CRITICAL状态
- GPU、磁盘、网络使用率超过对应阈值时设置相应状态

### 时间状态更新

```python
update_time_state(time_state: PetState) -> bool
```

此方法由`TimeBasedBehaviorSystem`调用，更新与时间相关的状态。

### 特殊日期状态设置

```python
set_special_date(special_date: Optional[PetState] = None) -> bool
```

此方法设置特殊日期状态，如生日、新年等。

### 交互状态设置

```python
set_interaction_state(interaction_state: Optional[Union[PetState, int]]) -> None
```

此方法设置用户交互导致的状态，如点击、拖拽等。

## 事件发布

状态机在状态变化时发布`STATE_CHANGED`事件，事件数据包含：

- `previous_state`：前一个状态的枚举值
- `current_state`：当前状态的枚举值
- `previous_state_name`：前一个状态的名称
- `current_state_name`：当前状态的名称
- `timestamp`：状态变化的时间戳

## 使用示例

```python
# 创建状态机实例
state_machine = PetStateMachine()

# 更新系统资源状态
state_changed = state_machine.update(
    cpu_usage=45.0,
    memory_usage=60.0,
    gpu_usage=30.0
)

# 设置时间状态
state_machine.update_time_state(PetState.MORNING)

# 设置特殊日期状态
state_machine.set_special_date(PetState.BIRTHDAY)

# 设置交互状态
state_machine.set_interaction_state(PetState.CLICKED)

# 获取当前状态
current_state = state_machine.get_state()
```

## 状态机配置

状态机的行为可以通过设置不同的阈值进行配置：

```python
# 创建状态机实例，自定义阈值
state_machine = PetStateMachine(
    cpu_light_threshold=15.0,       # 低于此值为IDLE，高于此值为LIGHT_LOAD
    cpu_moderate_threshold=35.0,    # 高于此值为MODERATE_LOAD
    cpu_heavy_threshold=55.0,       # 高于此值为HEAVY_LOAD
    cpu_very_heavy_threshold=75.0,  # 高于此值为VERY_HEAVY_LOAD
    memory_warning_threshold=65.0,  # 高于此值为MEMORY_WARNING
    memory_critical_threshold=85.0  # 高于此值为MEMORY_CRITICAL
)
```

## 最佳实践

1. **状态优先级管理**：在添加新状态时，确保在`state_priorities`字典中设置适当的优先级值
2. **状态类别映射**：在添加新状态时，确保在`state_to_category`字典中设置正确的类别
3. **状态事件处理**：订阅`STATE_CHANGED`事件以在状态变化时执行相应操作
4. **阈值调整**：根据不同的系统配置，可能需要调整资源使用率阈值
5. **状态持久化**：在必要时实现状态历史记录和恢复机制，以便进行调试和分析 