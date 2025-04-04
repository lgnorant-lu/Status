# 图表索引

本文档提供Hollow-ming项目所有图表的索引，按类别组织。

## 架构图

架构图描述系统的整体结构和组件关系。

- [系统整体架构图](Architecture/system_architecture.png) - 显示系统的主要组件和它们之间的关系
- [部署架构图](Architecture/deployment_architecture.png) - 显示系统在不同环境中的部署方式（计划中）
- [分层架构图](Architecture/layered_architecture.png) - 显示系统的层次结构（计划中）

## 模块图

模块图描述系统中各模块之间的依赖关系。

- [模块依赖关系图](Modules/module_dependencies.png) - 显示核心模块和扩展模块之间的依赖关系
- [配置系统结构图](Modules/config_structure.png) - 详细展示配置系统的内部结构（计划中）
- [渲染系统结构图](Modules/renderer_structure.png) - 详细展示渲染系统的内部结构（计划中）
- [资源系统结构图](Modules/resource_structure.png) - 详细展示资源系统的内部结构（计划中）
- [场景系统结构图](Modules/scene_structure.png) - 详细展示场景系统的内部结构（计划中）
- [交互系统结构图](Modules/interaction_structure.png) - 详细展示交互系统的内部结构（计划中）

## 流程图

流程图描述系统中的数据流和业务流程。

- [数据流图](Flowcharts/data_flow.png) - 显示数据在系统中的流动路径（计划中）
- [渲染流程图](Flowcharts/rendering_flow.png) - 显示渲染过程的详细流程（计划中）
- [资源加载流程图](Flowcharts/resource_loading_flow.png) - 显示资源加载的详细流程（计划中）
- [配置加载流程图](Flowcharts/config_loading_flow.png) - 显示配置加载的详细流程（计划中）

## 算法图

算法图描述系统中使用的关键算法。

- [场景树遍历算法](Algorithms/scene_tree_traversal.png) - 显示场景树遍历算法（计划中）
- [渲染队列排序算法](Algorithms/render_queue_sort.png) - 显示渲染队列排序算法（计划中）
- [资源缓存管理算法](Algorithms/resource_cache_management.png) - 显示资源缓存管理算法（计划中）

## 数据模型图

数据模型图描述系统中的数据结构和对象关系。

- [类图](DataModels/class_diagram.png) - 显示系统的主要类及其关系（计划中）
- [实体关系图](DataModels/entity_relationship.png) - 显示数据实体间的关系（计划中）
- [状态图](DataModels/state_diagram.png) - 显示对象的状态转换（计划中）

## 图表生成

所有图表使用Python的Graphviz库生成，源代码位于各自目录下。要生成或更新图表，请运行：

```bash
# 生成所有图表
python docs/Diagrams/generate_diagrams.py

# 生成特定图表
python docs/Diagrams/Architecture/system_architecture.py
python docs/Diagrams/Modules/module_dependencies.py
```

## 图表更新日志

- 2023/04/04: 初始版本 - 创建系统架构图和模块依赖关系图 