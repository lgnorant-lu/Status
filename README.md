# Hollow-ming

![Hollow-ming系统监控](assets/images/ui/preview.png)

[![GitHub License](https://img.shields.io/github/license/username/status)](https://github.com/username/status/blob/main/LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![PyQt5](https://img.shields.io/badge/dependency-PyQt5-green)](https://pypi.org/project/PyQt5/)

## 项目简介

Hollow-ming是一个基于空洞骑士主题的系统监控桌宠应用，通过虚拟世界元素映射计算机各项性能指标，既实用又有观赏性。

项目灵感来源于[赛博小鱼缸](https://github.com/Littlefean/cyber-life)项目，但采用了空洞骑士的美术风格和世界观。

不同的系统指标使用游戏中不同区域和角色元素来表示：
- CPU使用率：小骑士和NPC活跃程度
- 内存使用：感染扩散或灵魂能量
- GPU性能：护符能量状态
- 存储空间：环境区域特性
- 网络活动：飞虫活动和环境效果

## 功能特点

- **沉浸式监控**：将系统监控数据可视化为游戏场景元素
- **多场景切换**：根据监控重点或系统状态自动切换场景
- **交互功能**：通过点击小骑士或场景元素触发操作
- **个性化设置**：自定义小骑士外观、场景元素和动画效果
- **丰富细节**：符合空洞骑士游戏风格的精美视觉效果
- **低资源占用**：优化的性能确保应用本身资源占用最小化

## 场景预览

### 德特茅斯(Dirtmouth) - 系统概览
![德特茅斯场景](assets/images/ui/dirtmouth.png)

### 黑卵圣殿(Black Egg Temple) - 处理器状态
![黑卵圣殿场景](assets/images/ui/black_egg.png)

### 王国边缘(Kingdom's Edge) - 网络连接状态
![王国边缘场景](assets/images/ui/kingdoms_edge.png)

### 皇家水道(Royal Waterways) - 存储使用情况
![皇家水道场景](assets/images/ui/waterways.png)

## 系统要求

- Python 3.8+
- 操作系统：Windows 10/11、macOS、Linux
- 依赖项：PyQt5、psutil、GPUtil、SQLite3

## 安装方法

### 使用pip安装

```bash
pip install status-pet
```

### 从源码安装

```bash
git clone https://github.com/username/status.git
cd status
pip install -r requirements.txt
python setup.py install
```

## 快速开始

```bash
# 启动应用
status

# 或从源码运行
python -m status.main
```

## 使用指南

- **左键点击小骑士**：打开/关闭主控制面板
- **右键点击小骑士**：显示快捷菜单
- **拖动小骑士**：移动整个窗口
- **点击场景元素**：显示对应资源详情
- **护符系统**：点击护符栏装备不同护符获取功能
- **场景切换**：通过菜单或自动条件触发场景切换

## 开发文档

详细的开发文档请参考以下文件：
- [Global.md](Global.md) - 全局设计文档
- [Structure.md](Structure.md) - 项目结构文档
- [Design.md](Design.md) - 设计文档
- [Thread.md](Thread.md) - 任务进程文档

## 贡献指南

我们欢迎各种形式的贡献，包括但不限于：
- 代码优化和Bug修复
- 新场景或新功能开发
- 文档完善和翻译
- 视觉资源设计

请查阅[CONTRIBUTING.md](docs/CONTRIBUTING.md)了解详细的贡献流程。

## 许可证

本项目采用MIT许可证 - 查看[LICENSE](LICENSE)文件获取详细信息。

## 鸣谢

- [赛博小鱼缸](https://github.com/Littlefean/cyber-life)项目提供的灵感
- [空洞骑士](https://www.hollowknight.com/)游戏提供的艺术灵感
- 所有为本项目做出贡献的开发者 