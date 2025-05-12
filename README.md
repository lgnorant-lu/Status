# Status-Ming - 桌面交互式宠物应用

![新主题预览图待更新]()

[![GitHub License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![PySide6](https://img.shields.io/badge/UI%20Framework-PySide6-blue)](https://pypi.org/project/PySide6/)

## 项目简介

Status-Ming是一个以猫咪为主题的交互式桌面宠物应用，结合系统监控功能，通过虚拟角色映射计算机各项性能指标，既实用又有观赏性。

项目灵感来源于[赛博小鱼缸](https://github.com/Littlefean/cyber-life)项目，但采用了全新的设计和交互方式，并聚焦于猫咪主题。

不同的系统指标将通过猫咪（当前为占位符）的状态和动画来表现：
- CPU使用率：猫咪的活跃程度和动画状态变化
- 内存使用：猫咪周围环境元素的细微变化（远期）
- GPU性能：猫咪相关的特殊视觉效果状态（远期）
- 存储空间：猫咪所处环境区域的特征变化（远期）
- 网络活动：猫咪与虚拟元素的互动或背景效果（远期）

## 功能特点

- **沉浸式监控**：将系统监控数据可视化为生动的桌宠行为
- **多场景切换**：根据监控重点或系统状态自动切换场景（远期规划）
- **交互功能**：通过点击角色或场景元素触发操作（基础交互优先）
- **个性化设置**：自定义角色外观、场景元素和动画效果（远期规划，新主题素材确定后）
- **丰富细节**：计划采用精美的像素风格视觉效果（新主题素材确定后）
- **低资源占用**：优化的性能确保应用本身资源占用最小化

## 场景预览

新主题的场景预览将在素材到位后更新。

## 系统要求

- Python 3.8+
- 操作系统：Windows 10/11、macOS、Linux
- 依赖项：PySide6、psutil、GPUtil、SQLite3 (SQLite3为计划使用)

## 安装方法

### 使用pip安装 (待发布)

```bash
pip install status-ming 
```

### 从源码安装

```bash
git clone https://github.com/lgnorant-lu/Status-Ming.git # 假设的仓库路径，请用户确认
cd Status-Ming
pip install -r requirements.txt # 确保 requirements.txt 已更新为 PySide6
python setup.py install # 若使用setup.py
```

## 快速开始

```bash
# 启动应用 (待定具体命令)
status-ming

# 或从源码运行
python -m status.main # 假设的主入口，请用户确认
```

## 使用指南

- **左键点击角色**：打开/关闭主控制面板 (远期规划)
- **右键点击角色**：显示快捷菜单 (MVP包含退出)
- **拖动角色**：移动整个窗口 (MVP)
- **点击场景元素**：显示对应资源详情 (远期规划)
- **特殊功能**：通过菜单启用不同功能 (远期规划)
- **场景切换**：通过菜单或自动条件触发场景切换 (远期规划)

## 开发文档

详细的开发文档请参考以下资源（部分正在重构或撰写中）：
- [项目结构](Structure.md) - 项目结构文档
- [系统架构](Design.md) - 设计文档
- [开发指南](Development_Guidelines.md) - 开发规范文档
- [任务进度](Thread.md) - 任务进程文档
- [变更日志](Log.md) - 详细变更记录

## 贡献指南

我们欢迎各种形式的贡献。请查阅[贡献指南](docs/contributing.md)（注意：此文档也正在针对Status-Ming项目进行更新）了解详细的贡献流程。

## 许可证

本项目采用MIT许可证 - 查看[LICENSE](LICENSE)文件获取详细信息。

## 鸣谢

- [赛博小鱼缸](https://github.com/Littlefean/cyber-life)项目提供的灵感
- 所有为本项目做出贡献的开发者 