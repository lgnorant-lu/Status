# Status-Ming - 桌面交互式宠物应用

![占位符猫咪预览](status/temp_icon.png) <!-- 临时使用占位符图标 -->

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

- **实时系统监控**: 
    - **CPU 使用率**: 猫咪根据 CPU 负载在 `IDLE` (空闲) 和 `BUSY` (忙碌) 状态间切换，并播放对应动画。
    - **内存使用率**: 当内存使用超过阈值时，猫咪进入 `MEMORY_WARNING` 状态，并播放特殊动画。
- **交互式桌宠**: 
    - **拖拽移动**: 可以按住猫咪移动窗口。
    - **多种拖动模式**: 通过托盘菜单切换 `智能 (Smart)`、`精确 (Precise)`、`平滑 (Smooth)` 拖动模式。
    - **鼠标穿透**: 通过托盘菜单切换窗口是否响应鼠标点击 (穿透/可交互)。
- **系统托盘菜单**: 
    - 快速显示/隐藏桌宠窗口。
    - 切换拖动模式。
    - 切换鼠标交互状态。
    - 安全退出应用。
- **基础动画**: 目前包含 `IDLE`, `BUSY`, `MEMORY_WARNING` 状态的占位符动画。
- **低资源占用**: 优化性能，确保应用本身资源占用最小化。
- **跨平台支持**: 基于 PySide6，理论上支持 Windows, macOS, Linux。

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
git clone <YOUR_REPOSITORY_URL> # 请替换为实际的仓库 URL
cd Status-Ming
pip install -r requirements.txt
```

## 快速开始

```bash
# 从项目根目录运行
python -m status.main
```

## 使用指南

- **拖动角色**: 按住鼠标左键拖动猫咪以移动窗口 (需在非鼠标穿透模式下)。
- **系统托盘菜单 (右键点击任务栏图标)**:
    - **显示/隐藏**: 控制桌宠窗口的可见性。
    - **拖动模式**: 选择 `智能`, `精确`, 或 `平滑` 模式。
    - **鼠标交互**: 切换 `启用交互 (可拖动)` 或 `禁用交互 (鼠标穿透)`。
    - **退出**: 关闭应用程序。

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