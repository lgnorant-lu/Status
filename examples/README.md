# Status-Ming 示例代码

本目录包含Status-Ming项目各个模块的示例代码，用于展示如何使用和集成项目的各个功能。

## 示例列表

1. **logging_example.py** - 增强日志系统使用示例
   - 演示如何配置和使用多级别日志
   - 展示多输出目标（控制台、文件、内存缓冲）
   - 演示日志文件轮转功能

2. **recovery_example.py** - 错误恢复机制示例
   - 演示应用状态持久化管理
   - 展示错误恢复流程和不同恢复模式
   - 演示全局异常处理和错误级别使用

## 如何运行示例

从项目根目录运行示例：

```bash
# 运行日志系统示例
python -m examples.logging_example

# 运行错误恢复机制示例
python -m examples.recovery_example
```

## 注意事项

- 示例代码默认会在`data/`目录下创建必要的数据文件
- 部分示例可能会模拟错误和崩溃，这是正常的测试行为
- 运行示例前请确保已安装所有依赖（参见根目录的`requirements.txt`） 