# Status - 桌面交互式宠物应用

![系统监控预览](assets/images/ui/preview.png)

[![GitHub License](https://img.shields.io/github/license/username/status)](https://github.com/username/status/blob/main/LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![PyQt5](https://img.shields.io/badge/dependency-PyQt5-green)](https://pypi.org/project/PyQt5/)

## 项目简介

Status是一个交互式桌面宠物应用，结合系统监控功能，通过虚拟角色映射计算机各项性能指标，既实用又有观赏性。

项目灵感来源于[赛博小鱼缸](https://github.com/Littlefean/cyber-life)项目，但采用了全新的设计和交互方式。

不同的系统指标使用不同的视觉元素来表示：
- CPU使用率：角色活跃程度和状态变化
- 内存使用：环境元素的变化
- GPU性能：特殊效果状态
- 存储空间：环境区域特性
- 网络活动：背景元素和环境效果

## 功能特点

- **沉浸式监控**：将系统监控数据可视化为生动场景元素
- **多场景切换**：根据监控重点或系统状态自动切换场景
- **交互功能**：通过点击角色或场景元素触发操作
- **个性化设置**：自定义角色外观、场景元素和动画效果
- **丰富细节**：精美的像素风格视觉效果
- **低资源占用**：优化的性能确保应用本身资源占用最小化

## 场景预览

### 主菜单 - 系统概览
![主菜单场景](assets/images/ui/main_menu.png)

### 核心监控 - 处理器状态
![处理器监控](assets/images/ui/cpu_monitor.png)

### 网络监控 - 网络连接状态
![网络监控](assets/images/ui/network_monitor.png)

### 存储监控 - 存储使用情况
![存储监控](assets/images/ui/storage_monitor.png)

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

- **左键点击角色**：打开/关闭主控制面板
- **右键点击角色**：显示快捷菜单
- **拖动角色**：移动整个窗口
- **点击场景元素**：显示对应资源详情
- **特殊功能**：通过菜单启用不同功能
- **场景切换**：通过菜单或自动条件触发场景切换

## 开发文档

详细的开发文档请参考以下资源：
- [项目结构](docs/development/structure.md) - 项目结构文档
- [系统架构](docs/development/architecture.md) - 设计文档
- [开发指南](docs/development/guidelines.md) - 开发规范文档
- [任务进度](docs/project/tasks.md) - 任务进程文档
- [变更日志](docs/project/changelog.md) - 详细变更记录

## 贡献指南

我们欢迎各种形式的贡献，包括但不限于：
- 代码优化和Bug修复
- 新场景或新功能开发
- 文档完善和翻译
- 视觉资源设计

请查阅[贡献指南](docs/contributing.md)了解详细的贡献流程。

## 许可证

本项目采用MIT许可证 - 查看[LICENSE](LICENSE)文件获取详细信息。

## 鸣谢

- [赛博小鱼缸](https://github.com/Littlefean/cyber-life)项目提供的灵感
- 所有为本项目做出贡献的开发者 