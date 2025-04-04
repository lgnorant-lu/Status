# 绘图日志索引

本文档索引项目的各类图表文件，详细图表存储在 Diagrams 目录下。

## 架构图索引

| 图表名称 | 文件路径 | 描述 | 状态 | 更新日期 |
|---------|---------|------|------|----------|
| 系统总体架构图 | [Diagrams/Architecture/system_architecture.py](/Diagrams/Architecture/system_architecture.py) | 展示系统三层架构和主要模块 | [计划中] | - |
| 模块交互图 | [Diagrams/Architecture/module_interactions.py](/Diagrams/Architecture/module_interactions.py) | 展示各模块之间的交互关系 | [计划中] | - |
| 部署架构图 | [Diagrams/Architecture/deployment_architecture.py](/Diagrams/Architecture/deployment_architecture.py) | 展示部署架构和组件分布 | [计划中] | - |

## 模块图索引

| 图表名称 | 文件路径 | 描述 | 状态 | 更新日期 |
|---------|---------|------|------|----------|
| 核心引擎结构图 | [Diagrams/Modules/core_structure.py](/Diagrams/Modules/core_structure.py) | 核心引擎内部结构和关系 | [计划中] | - |
| 渲染系统结构图 | [Diagrams/Modules/renderer_structure.py](/Diagrams/Modules/renderer_structure.py) | 渲染系统内部结构和组件 | [计划中] | - |
| 监控系统结构图 | [Diagrams/Modules/monitor_structure.py](/Diagrams/Modules/monitor_structure.py) | 监控系统内部结构和数据流 | [计划中] | - |
| 场景系统结构图 | [Diagrams/Modules/scenes_structure.py](/Diagrams/Modules/scenes_structure.py) | 场景系统内部结构和继承关系 | [计划中] | - |
| 交互系统结构图 | [Diagrams/Modules/interaction_structure.py](/Diagrams/Modules/interaction_structure.py) | 交互系统内部结构和事件流 | [计划中] | - |

## 流程图索引

| 图表名称 | 文件路径 | 描述 | 状态 | 更新日期 |
|---------|---------|------|------|----------|
| 应用启动流程图 | [Diagrams/Flowcharts/startup_flow.py](/Diagrams/Flowcharts/startup_flow.py) | 应用启动和初始化流程 | [计划中] | - |
| 场景切换流程图 | [Diagrams/Flowcharts/scene_change_flow.py](/Diagrams/Flowcharts/scene_change_flow.py) | 场景切换和资源加载流程 | [计划中] | - |
| 数据采集流程图 | [Diagrams/Flowcharts/data_collection_flow.py](/Diagrams/Flowcharts/data_collection_flow.py) | 系统数据采集和处理流程 | [计划中] | - |
| 交互响应流程图 | [Diagrams/Flowcharts/interaction_flow.py](/Diagrams/Flowcharts/interaction_flow.py) | 用户交互和系统响应流程 | [计划中] | - |

## 算法图索引

| 图表名称 | 文件路径 | 描述 | 状态 | 更新日期 |
|---------|---------|------|------|----------|
| 动画状态机 | [Diagrams/Algorithms/animation_state_machine.py](/Diagrams/Algorithms/animation_state_machine.py) | 动画状态转换逻辑 | [计划中] | - |
| 资源加载算法 | [Diagrams/Algorithms/resource_loading_algorithm.py](/Diagrams/Algorithms/resource_loading_algorithm.py) | 资源懒加载和缓存策略 | [计划中] | - |
| 渲染优化算法 | [Diagrams/Algorithms/rendering_optimization.py](/Diagrams/Algorithms/rendering_optimization.py) | 脏区域渲染和图层管理 | [计划中] | - |
| 数据分析算法 | [Diagrams/Algorithms/data_analysis_algorithm.py](/Diagrams/Algorithms/data_analysis_algorithm.py) | 系统数据处理和分析 | [计划中] | - |

## 数据模型图索引

| 图表名称 | 文件路径 | 描述 | 状态 | 更新日期 |
|---------|---------|------|------|----------|
| 数据库模型图 | [Diagrams/DataModels/database_model.py](/Diagrams/DataModels/database_model.py) | 数据库表结构和关系 | [计划中] | - |
| 类继承关系图 | [Diagrams/DataModels/class_inheritance.py](/Diagrams/DataModels/class_inheritance.py) | 类的继承和实现关系 | [计划中] | - |
| 场景数据模型 | [Diagrams/DataModels/scene_data_model.py](/Diagrams/DataModels/scene_data_model.py) | 场景数据结构和关系 | [计划中] | - |
| 配置数据模型 | [Diagrams/DataModels/config_data_model.py](/Diagrams/DataModels/config_data_model.py) | 配置数据结构和关系 | [计划中] | - |

## 图表生成指南

### 创建新图表

1. 使用Python Graphviz库创建图表
2. 在适当的目录下创建Python脚本
3. 添加必要的注释和文档
4. 生成图表图像文件
5. 更新本索引文档

### 图表命名规范

- 使用小写下划线命名文件
- 图表文件名应明确表达图表内容
- 图表脚本和生成的图像使用相同基础名称

### 图表代码示例

```python
import graphviz

def create_diagram():
    """创建示例图表"""
    dot = graphviz.Digraph('示例图表', comment='这是一个示例图表')
    
    # 添加节点
    dot.node('A', '节点A')
    dot.node('B', '节点B')
    dot.node('C', '节点C')
    
    # 添加边
    dot.edge('A', 'B', '关系1')
    dot.edge('B', 'C', '关系2')
    
    # 设置图表属性
    dot.attr(rankdir='TB', size='8,5')
    
    # 保存图表
    dot.render('example_diagram', format='png', cleanup=True)
    
if __name__ == '__main__':
    create_diagram()
```

### 图表更新流程

1. 修改图表脚本
2. 重新生成图表图像
3. 更新索引中的描述和状态
4. 更新索引中的更新日期 