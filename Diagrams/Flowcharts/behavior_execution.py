"""
---------------------------------------------------------------
File name:                  behavior_execution.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                行为执行流程图
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import graphviz

# 创建一个有向图
dot = graphviz.Digraph(
    'behavior_execution_flow', 
    comment='行为执行流程图',
    format='png', 
    engine='dot'
)

# 设置图形属性
dot.attr(
    rankdir='TB',  # 从上到下的布局
    size='10,12',   # 图大小
    dpi='300',     # 分辨率
    bgcolor='#BFFDCC',  # 背景颜色
    splines='ortho',  # 使用正交线
    nodesep='0.5',  # 节点间距
    ranksep='0.6',  # 层级间距
    fontname='Arial',
    fontsize='16'
)

# 设置节点属性
dot.attr('node', 
    shape='box', 
    style='rounded,filled', 
    fontname='Arial',
    fontsize='14',
    margin='0.3,0.2',
    height='0.6',
    fillcolor='white'
)

# 设置边属性
dot.attr('edge', 
    fontname='Arial', 
    fontsize='12', 
    arrowsize='0.8'
)

# 开始和结束节点
dot.node('start', '开始', shape='oval', fillcolor='#BBDEFB')
dot.node('end', '结束', shape='oval', fillcolor='#BBDEFB')

# 行为创建阶段
dot.node('request_behavior', '请求创建行为', fillcolor='#B3E5FC')
dot.node('check_exists', '检查行为注册', shape='diamond', fillcolor='#FFF9C4')
dot.node('behavior_not_found', '行为未找到', fillcolor='#FFCDD2')
dot.node('create_behavior', '创建行为实例', fillcolor='#B3E5FC')
dot.node('set_params', '设置行为参数', fillcolor='#B3E5FC')

# 行为准备阶段
dot.node('request_execute', '请求执行行为', fillcolor='#C8E6C9')
dot.node('check_can_execute', '检查是否可执行', shape='diamond', fillcolor='#FFF9C4')
dot.node('check_priority', '检查优先级', shape='diamond', fillcolor='#FFF9C4')
dot.node('lower_priority', '优先级不足', fillcolor='#FFCDD2')
dot.node('interrupt_current', '中断当前行为', fillcolor='#C8E6C9')

# 行为执行阶段
dot.node('execute_behavior', '执行行为', fillcolor='#DCEDC8')
dot.node('check_completed', '检查是否完成', shape='diamond', fillcolor='#FFF9C4')
dot.node('update_behavior', '更新行为状态', fillcolor='#DCEDC8')
dot.node('behavior_finished', '行为完成', fillcolor='#DCEDC8')

# 行为切换阶段
dot.node('restore_previous', '恢复上一个行为', fillcolor='#E1BEE7')
dot.node('check_queue', '检查行为队列', shape='diamond', fillcolor='#FFF9C4')
dot.node('next_behavior', '执行下一个行为', fillcolor='#E1BEE7')
dot.node('idle_state', '进入空闲状态', fillcolor='#E1BEE7')

# 事件处理
dot.node('behavior_event', '行为事件触发', fillcolor='#FFCCBC')
dot.node('update_state', '更新状态机', fillcolor='#FFCCBC')

# 连接

# 行为创建阶段连接
dot.edge('start', 'request_behavior')
dot.edge('request_behavior', 'check_exists')
dot.edge('check_exists', 'behavior_not_found', label='  否')
dot.edge('behavior_not_found', 'end')
dot.edge('check_exists', 'create_behavior', label='  是')
dot.edge('create_behavior', 'set_params')

# 行为准备阶段连接
dot.edge('set_params', 'request_execute')
dot.edge('request_execute', 'check_can_execute')
dot.edge('check_can_execute', 'end', label='  否')
dot.edge('check_can_execute', 'check_priority', label='  是')
dot.edge('check_priority', 'lower_priority', label='  低')
dot.edge('lower_priority', 'end')
dot.edge('check_priority', 'interrupt_current', label='  高')
dot.edge('interrupt_current', 'execute_behavior')

# 行为执行阶段连接
dot.edge('execute_behavior', 'check_completed')
dot.edge('check_completed', 'update_behavior', label='  否')
dot.edge('update_behavior', 'behavior_event', style='dashed')
dot.edge('behavior_event', 'update_state', style='dashed')
dot.edge('update_state', 'check_completed', style='dashed')
dot.edge('check_completed', 'behavior_finished', label='  是')

# 行为切换阶段连接
dot.edge('behavior_finished', 'check_queue')
dot.edge('check_queue', 'next_behavior', label='  有待执行行为')
dot.edge('next_behavior', 'execute_behavior')
dot.edge('check_queue', 'restore_previous', label='  无待执行行为\n  有上一个行为')
dot.edge('restore_previous', 'execute_behavior')
dot.edge('check_queue', 'idle_state', label='  无待执行行为\n  无上一个行为')
dot.edge('idle_state', 'end')

# 子图分组
with dot.subgraph(name='cluster_creation') as c:
    c.attr(label='行为创建阶段', style='filled', color='#E3F2FD', fillcolor='#E3F2FD')
    c.node_attr.update(style='filled')
    for n in ['request_behavior', 'check_exists', 'behavior_not_found', 'create_behavior', 'set_params']:
        c.node(n)

with dot.subgraph(name='cluster_preparation') as p:
    p.attr(label='行为准备阶段', style='filled', color='#E8F5E9', fillcolor='#E8F5E9')
    p.node_attr.update(style='filled')
    for n in ['request_execute', 'check_can_execute', 'check_priority', 'lower_priority', 'interrupt_current']:
        p.node(n)

with dot.subgraph(name='cluster_execution') as e:
    e.attr(label='行为执行阶段', style='filled', color='#F1F8E9', fillcolor='#F1F8E9')
    e.node_attr.update(style='filled')
    for n in ['execute_behavior', 'check_completed', 'update_behavior', 'behavior_finished', 'behavior_event', 'update_state']:
        e.node(n)

with dot.subgraph(name='cluster_switching') as s:
    s.attr(label='行为切换阶段', style='filled', color='#F3E5F5', fillcolor='#F3E5F5')
    s.node_attr.update(style='filled')
    for n in ['check_queue', 'next_behavior', 'restore_previous', 'idle_state']:
        s.node(n)

# 渲染生成图片
dot.render(directory='Diagrams/Flowcharts', cleanup=True)

print("行为执行流程图已生成：Diagrams/Flowcharts/behavior_execution_flow.png") 