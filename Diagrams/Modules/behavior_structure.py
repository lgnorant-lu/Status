"""
---------------------------------------------------------------
File name:                  behavior_structure.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                行为系统结构图
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import graphviz

# 创建一个有向图
dot = graphviz.Digraph(
    'behavior_system_structure', 
    comment='行为系统结构图',
    format='png', 
    engine='dot'
)

# 设置图形属性
dot.attr(
    rankdir='TB',  # 从上到下的布局
    size='12,8',   # 图大小
    dpi='300',     # 分辨率
    bgcolor='#BFFDCC',  # 背景颜色
    splines='ortho',  # 使用正交线
    nodesep='0.5',  # 节点间距
    ranksep='0.8',  # 层级间距
    fontname='Arial',
    fontsize='16'
)

# 设置节点属性
dot.attr('node', 
    shape='box', 
    style='rounded,filled', 
    fontname='Arial',
    fontsize='14',
    margin='0.3,0.1',
    height='0.6'
)

# 设置边属性
dot.attr('edge', 
    fontname='Arial', 
    fontsize='12', 
    arrowsize='0.8'
)

# 创建子图：核心组件
with dot.subgraph(name='cluster_core') as c:
    c.attr(label='核心组件', style='filled', color='#E6F5FF', fillcolor='#E6F5FF', fontcolor='black', fontsize='16')
    
    # 状态机组件
    c.node('state_machine', 'StateMachine\n状态机', fillcolor='#90CAF9', color='#5D99C6')
    c.node('state', 'State\n状态', fillcolor='#90CAF9', color='#5D99C6')
    c.node('transition', 'Transition\n状态转换', fillcolor='#90CAF9', color='#5D99C6')
    
    # 行为管理器组件
    c.node('behavior_manager', 'BehaviorManager\n行为管理器', fillcolor='#FFE082', color='#CAAE53')
    c.node('behavior', 'Behavior\n行为', fillcolor='#FFE082', color='#CAAE53')
    c.node('behavior_factory', 'BehaviorFactory\n行为工厂', fillcolor='#FFE082', color='#CAAE53')
    
    # 状态机内部连接
    c.edge('state_machine', 'state', label='管理')
    c.edge('state_machine', 'transition', label='管理')
    c.edge('state', 'transition', label='触发')
    
    # 行为管理器内部连接
    c.edge('behavior_manager', 'behavior', label='管理')
    c.edge('behavior_manager', 'behavior_factory', label='使用')
    c.edge('behavior_factory', 'behavior', label='创建')

# 创建子图：感知系统
with dot.subgraph(name='cluster_perception') as p:
    p.attr(label='感知系统', style='filled', color='#E8F5E9', fillcolor='#E8F5E9', fontcolor='black', fontsize='16')
    
    p.node('environment_sensor', 'EnvironmentSensor\n环境感知器', fillcolor='#A5D6A7', color='#75A478')
    p.node('screen_boundary', 'ScreenBoundary\n屏幕边界', fillcolor='#A5D6A7', color='#75A478')
    p.node('window_position', 'WindowPosition\n窗口位置', fillcolor='#A5D6A7', color='#75A478')
    p.node('desktop_objects', 'DesktopObjects\n桌面物体', fillcolor='#A5D6A7', color='#75A478')
    
    p.edge('environment_sensor', 'screen_boundary', label='检测')
    p.edge('environment_sensor', 'window_position', label='检测')
    p.edge('environment_sensor', 'desktop_objects', label='检测')

# 创建子图：决策系统
with dot.subgraph(name='cluster_decision') as d:
    d.attr(label='决策系统', style='filled', color='#FFF3E0', fillcolor='#FFF3E0', fontcolor='black', fontsize='16')
    
    d.node('decision_maker', 'DecisionMaker\n决策系统', fillcolor='#FFCC80', color='#CA9B52')
    d.node('rule_engine', 'RuleEngine\n规则引擎', fillcolor='#FFCC80', color='#CA9B52')
    d.node('behavior_selector', 'BehaviorSelector\n行为选择器', fillcolor='#FFCC80', color='#CA9B52')
    d.node('probability_provider', 'ProbabilityProvider\n概率提供器', fillcolor='#FFCC80', color='#CA9B52')
    
    d.edge('decision_maker', 'rule_engine', label='使用')
    d.edge('decision_maker', 'behavior_selector', label='使用')
    d.edge('decision_maker', 'probability_provider', label='使用')
    d.edge('rule_engine', 'behavior_selector', label='影响')

# 创建子图：具体行为
with dot.subgraph(name='cluster_behaviors') as b:
    b.attr(label='具体行为', style='filled', color='#F3E5F5', fillcolor='#F3E5F5', fontcolor='black', fontsize='16')
    
    b.node('idle_behaviors', 'IdleBehaviors\n空闲行为', fillcolor='#CE93D8', color='#9C64A6')
    b.node('movement_behaviors', 'MovementBehaviors\n移动行为', fillcolor='#CE93D8', color='#9C64A6')
    b.node('reaction_behaviors', 'ReactionBehaviors\n反应行为', fillcolor='#CE93D8', color='#9C64A6')
    b.node('composite_behaviors', 'CompositeBehaviors\n组合行为', fillcolor='#CE93D8', color='#9C64A6')
    
    b.edge('idle_behaviors', 'composite_behaviors', style='dashed')
    b.edge('movement_behaviors', 'composite_behaviors', style='dashed')
    b.edge('reaction_behaviors', 'composite_behaviors', style='dashed')

# 核心组件之间的连接
dot.edge('state_machine', 'behavior_manager', label='状态变化触发行为')
dot.edge('behavior_manager', 'state_machine', label='行为执行改变状态')

# 感知系统与核心和决策的连接
dot.edge('environment_sensor', 'state_machine', label='提供状态转换条件')
dot.edge('environment_sensor', 'decision_maker', label='提供环境信息')

# 决策系统与核心的连接
dot.edge('decision_maker', 'behavior_manager', label='选择执行行为')

# 具体行为与核心的连接
dot.edge('behavior_manager', 'idle_behaviors', label='管理')
dot.edge('behavior_manager', 'movement_behaviors', label='管理')
dot.edge('behavior_manager', 'reaction_behaviors', label='管理')
dot.edge('behavior_manager', 'composite_behaviors', label='管理')

# 事件接口
dot.node('event_interface', '事件接口', shape='ellipse', fillcolor='#FFCDD2', color='#CB9CA1')
dot.edge('event_interface', 'decision_maker', label='触发决策')
dot.edge('event_interface', 'state_machine', label='触发状态变化')

# 渲染接口
dot.node('render_interface', '渲染接口', shape='ellipse', fillcolor='#B2DFDB', color='#80CBC4')
dot.edge('behavior_manager', 'render_interface', label='更新图像')

# 渲染生成图片
dot.render(directory='Diagrams/Modules', cleanup=True)

print("行为系统结构图已生成：Diagrams/Modules/behavior_system_structure.png") 