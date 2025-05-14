"""
---------------------------------------------------------------
File name:                  recovery_manager.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                恢复管理器实现
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

import os
import json
import time
import enum
import signal
import traceback
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Tuple, Union, cast
import hashlib

# 获取日志器
from status.core.logging import get_logger

# 导入状态管理器
from status.core.recovery.state_manager import StateManager

class RecoveryMode(enum.Enum):
    """恢复模式枚举
    
    定义应用可能的启动/恢复模式
    """
    
    NORMAL = "normal"  # 正常模式，加载所有模块
    SAFE = "safe"      # 安全模式，只加载核心模块
    MINIMAL = "minimal"  # 最小模式，仅加载UI和基础功能


class RecoveryManager:
    """恢复管理器类
    
    负责检测应用异常终止并提供恢复机制。使用单例模式确保全局只有一个实例。
    """
    
    # 单例实例
    _instance = None
    _lock = threading.Lock()
    _initialized: bool = False
    
    # 恢复文件名
    _RECOVERY_FILE = "recovery_status.json"
    _CRASH_LOG_FILE = "crash_log.json"
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(RecoveryManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, recovery_dir: Optional[str] = None):
        """初始化恢复管理器
        
        Args:
            recovery_dir: 恢复文件目录
        """
        # 防止重复初始化
        if self._initialized:
            return
            
        self._initialized = True
        
        # 设置日志
        self.logger = get_logger("status.core.recovery.recovery_manager")
        
        # 恢复文件目录
        self._recovery_dir = recovery_dir or os.path.join("data", "recovery")
        
        # 确保恢复目录存在
        self._ensure_recovery_directory()
        
        # 启动钩子列表 [(priority, callback)]
        self._startup_hooks: List[Tuple[int, Callable[[RecoveryMode], None]]] = []
        
        # 当前恢复模式
        self._current_mode = RecoveryMode.NORMAL
        
        # 是否已检测过异常退出
        self._exit_checked = False
        
        # 是否正在进行恢复
        self._recovery_in_progress = False
        
        # 退出标志文件路径
        self._exit_flag_path = os.path.join(self._recovery_dir, self._RECOVERY_FILE)
        
        # 崩溃日志文件路径
        self._crash_log_path = os.path.join(self._recovery_dir, self._CRASH_LOG_FILE)
        
        # 状态管理器实例
        self._state_manager = StateManager()
        
        # 安装退出处理函数
        self._install_exit_handlers()
        
        self.logger.info("恢复管理器初始化完成")
    
    def _ensure_recovery_directory(self):
        """确保恢复目录存在"""
        if not os.path.exists(self._recovery_dir):
            os.makedirs(self._recovery_dir, exist_ok=True)
            self.logger.debug(f"创建恢复目录: {self._recovery_dir}")
    
    def _install_exit_handlers(self):
        """安装退出处理函数"""
        # 注册正常退出处理
        self._original_exit = os._exit
        os._exit = self._handle_exit  # type: ignore
        
        # 注册信号处理
        try:
            signal.signal(signal.SIGTERM, self._handle_signal)
            signal.signal(signal.SIGINT, self._handle_signal)
            if hasattr(signal, 'SIGBREAK'):  # Windows特有
                signal.signal(signal.SIGBREAK, self._handle_signal)
            self.logger.debug("信号处理器安装成功")
        except Exception as e:
            self.logger.warning(f"信号处理器安装失败: {e}")
    
    def _handle_exit(self, status=0):
        """处理退出请求
        
        Args:
            status: 退出状态码
        """
        self.logger.debug(f"应用退出，状态码: {status}")
        self._mark_clean_exit()
        self._original_exit(status)
    
    def _handle_signal(self, signum, frame):
        """处理信号
        
        Args:
            signum: 信号编号
            frame: 当前帧
        """
        self.logger.debug(f"接收到信号: {signum}")
        self._mark_clean_exit()
        # 使用原始退出函数
        self._original_exit(0)
    
    def _mark_clean_exit(self):
        """标记正常退出"""
        try:
            exit_info = {
                "clean_exit": True,
                "timestamp": datetime.now().isoformat(),
                "recovery_mode": self._current_mode.value
            }
            
            with open(self._exit_flag_path, 'w', encoding='utf-8') as f:
                json.dump(exit_info, f, indent=4, ensure_ascii=False)
                
            self.logger.debug("已标记为正常退出")
        except Exception as e:
            self.logger.error(f"标记正常退出失败: {e}")
    
    def _mark_startup(self):
        """标记应用启动"""
        try:
            startup_info = {
                "clean_exit": False,
                "timestamp": datetime.now().isoformat(),
                "recovery_mode": self._current_mode.value
            }
            
            with open(self._exit_flag_path, 'w', encoding='utf-8') as f:
                json.dump(startup_info, f, indent=4, ensure_ascii=False)
                
            self.logger.debug("已标记为应用启动")
        except Exception as e:
            self.logger.error(f"标记应用启动失败: {e}")
    
    def detect_abnormal_exit(self) -> bool:
        """检测上次是否非正常退出
        
        Returns:
            是否检测到非正常退出
        """
        # 如果已经检测过，直接返回结果
        if self._exit_checked:
            return self._recovery_in_progress
        
        self._exit_checked = True
        
        try:
            # 检查退出标志文件是否存在
            if not os.path.exists(self._exit_flag_path):
                self.logger.info("首次运行或恢复文件不存在")
                self._mark_startup()
                return False
            
            # 读取退出信息
            with open(self._exit_flag_path, 'r', encoding='utf-8') as f:
                exit_info = json.load(f)
            
            # 检查是否正常退出
            if exit_info.get("clean_exit", False):
                self.logger.info("上次正常退出")
                self._mark_startup()
                return False
            
            # 非正常退出
            self.logger.warning("检测到上次非正常退出")
            self._recovery_in_progress = True
            return True
            
        except Exception as e:
            self.logger.error(f"检测异常退出失败: {e}")
            # 出错时，假设需要恢复
            self._recovery_in_progress = True
            self._mark_startup()
            return True
    
    def register_startup_hook(self, priority: int, callback: Callable[[RecoveryMode], None]) -> None:
        """注册启动钩子
        
        Args:
            priority: 优先级（数字越小优先级越高）
            callback: 回调函数
        """
        if not callable(callback):
            self.logger.error("注册启动钩子失败: 回调必须是可调用对象")
            return
        
        self._startup_hooks.append((priority, callback))
        self._startup_hooks.sort(key=lambda x: x[0])  # 按优先级排序
        self.logger.debug(f"注册启动钩子成功，优先级: {priority}")
    
    def start_recovery_process(self, mode: Optional[RecoveryMode] = None) -> bool:
        """启动恢复流程
        
        Args:
            mode: 恢复模式，如果未指定则自动选择

        Returns:
            是否恢复成功
        """
        try:
            # 如果未指定模式，根据崩溃记录自动选择
            if mode is None:
                mode = self._select_recovery_mode()
            
            self._current_mode = mode
            self.logger.info(f"开始恢复流程，模式: {mode.value}")
            
            # 尝试恢复状态
            if mode != RecoveryMode.MINIMAL:
                self._recover_state()
            
            # 执行启动钩子
            self._execute_startup_hooks()
            
            # 标记恢复完成
            self._recovery_in_progress = False
            
            # 记录恢复日志
            self._log_recovery(True)
            
            self.logger.info("恢复流程完成")
            return True
        
        except Exception as e:
            self.logger.error(f"恢复流程失败: {e}")
            self._log_recovery(False, str(e))
            return False
    
    def _select_recovery_mode(self) -> RecoveryMode:
        """选择合适的恢复模式
        
        根据崩溃记录和历史情况，自动选择恢复模式

        Returns:
            恢复模式
        """
        try:
            # 检查崩溃日志
            if os.path.exists(self._crash_log_path):
                with open(self._crash_log_path, 'r', encoding='utf-8') as f:
                    crash_log = json.load(f)
                
                # 获取最近的崩溃记录
                recent_crashes = crash_log.get("crashes", [])
                
                # 如果最近有多次崩溃，使用安全模式
                if len(recent_crashes) >= 3:
                    recent_time = time.time() - 24 * 60 * 60  # 24小时内
                    recent_count = sum(1 for crash in recent_crashes 
                                     if crash.get("timestamp", 0) > recent_time)
                    
                    if recent_count >= 2:
                        self.logger.warning("检测到24小时内多次崩溃，使用安全模式")
                        return RecoveryMode.SAFE
            
            # 默认使用正常模式
            return RecoveryMode.NORMAL
            
        except Exception as e:
            self.logger.error(f"选择恢复模式失败: {e}，使用安全模式")
            return RecoveryMode.SAFE
    
    def _recover_state(self) -> bool:
        """恢复应用状态
        
        Returns:
            是否恢复成功
        """
        try:
            # 尝试加载最新状态
            state_data = self._state_manager.load_state()
            
            if state_data:
                self.logger.info("状态恢复成功")
                return True
            else:
                self.logger.warning("没有可用的状态数据")
                return False
                
        except Exception as e:
            self.logger.error(f"状态恢复失败: {e}")
            return False
    
    def _execute_startup_hooks(self):
        """执行启动钩子"""
        if not self._startup_hooks:
            self.logger.debug("没有注册的启动钩子")
            return
        
        for priority, callback in self._startup_hooks:
            try:
                callback(self._current_mode)
                self.logger.debug(f"执行启动钩子成功，优先级: {priority}")
            except Exception as e:
                self.logger.error(f"执行启动钩子失败，优先级: {priority}, 错误: {e}")
    
    def _log_recovery(self, success: bool, error_message: Optional[str] = None):
        """记录恢复日志
        
        Args:
            success: 是否恢复成功
            error_message: 错误消息
        """
        try:
            # 读取现有崩溃日志
            crash_log: Dict[str, List[Dict[str, Any]]] = {"crashes": [], "recoveries": []}
            if os.path.exists(self._crash_log_path):
                with open(self._crash_log_path, 'r', encoding='utf-8') as f:
                    crash_log = json.load(f)
            
            # 添加新记录
            recovery_record = {
                "timestamp": time.time(),
                "datetime": datetime.now().isoformat(),
                "mode": self._current_mode.value,
                "success": success
            }
            
            if error_message:
                recovery_record["error"] = error_message
            
            # 将恢复记录添加到崩溃日志中
            if "recoveries" not in crash_log:
                crash_log["recoveries"] = []
            
            crash_log["recoveries"].append(recovery_record)
            
            # 保存崩溃日志
            with open(self._crash_log_path, 'w', encoding='utf-8') as f:
                json.dump(crash_log, f, indent=4, ensure_ascii=False)
                
            self.logger.debug("恢复日志记录成功")
            
        except Exception as e:
            self.logger.error(f"记录恢复日志失败: {e}")
    
    def create_crash_report(self, error_info: Dict[str, Any]) -> str:
        """创建崩溃报告
        
        Args:
            error_info: 错误信息
            
        Returns:
            崩溃报告文件路径
        """
        try:
            # 确保目录存在
            self._ensure_recovery_directory()
            
            # 报告时间戳
            timestamp = datetime.now().isoformat().replace(':', '-').replace('.', '-')
            
            # 添加基本信息
            report = {
                "timestamp": timestamp,
                "recovery_mode": self._current_mode.value,
                "error": error_info
            }
            
            # 崩溃报告文件名
            crash_report_file = f"crash_report_{timestamp}.json"
            crash_report_path = os.path.join(self._recovery_dir, crash_report_file)
            
            # 写入报告文件
            with open(crash_report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=4, ensure_ascii=False)
            
            # 更新崩溃日志
            crash_log: List[Dict[str, Any]] = []
            
            # 读取现有崩溃日志
            if os.path.exists(self._crash_log_path):
                try:
                    with open(self._crash_log_path, 'r', encoding='utf-8') as f:
                        crash_log = json.load(f)
                except Exception as e:
                    self.logger.error(f"读取崩溃日志失败: {e}")
                    crash_log = []
            
            # 确保crash_log是列表
            if not isinstance(crash_log, list):
                crash_log = []
            
            # 添加新的崩溃记录
            crash_entry = {
                "timestamp": timestamp,
                "report_file": crash_report_file,
                "error_type": error_info.get("type", "未知"),
                "error_message": error_info.get("message", "未知错误")
            }
            
            crash_log.append(crash_entry)
            
            # 限制日志条目数量
            if len(crash_log) > 20:
                crash_log = crash_log[-20:]
            
            # 写入崩溃日志
            with open(self._crash_log_path, 'w', encoding='utf-8') as f:
                json.dump(crash_log, f, indent=4, ensure_ascii=False)
            
            self.logger.info(f"崩溃报告已创建: {crash_report_path}")
            return crash_report_path
            
        except Exception as e:
            self.logger.error(f"创建崩溃报告失败: {e}")
            return ""
    
    def verify_and_repair_data(self) -> Dict[str, Any]:
        """验证并修复数据
        
        尝试验证和修复关键的应用数据文件。
        
        Returns:
            修复报告，包含修复的文件和状态
        """
        self.logger.info("开始验证并修复数据")
        
        # 修复报告
        repair_report: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "fixed_files": [],
            "failed_files": [],
            "skipped_files": [],
            "errors": []
        }
        
        try:
            # 修复状态文件
            self._verify_state_files(repair_report)
            
            # 修复配置文件
            self._verify_config_files(repair_report)
            
            # 修复日志文件
            self._verify_log_files(repair_report)
            
            # 记录修复报告
            self.logger.info(f"数据验证完成，修复: {len(repair_report['fixed_files'])}, "
                            f"失败: {len(repair_report['failed_files'])}, "
                            f"跳过: {len(repair_report['skipped_files'])}")
            
        except Exception as e:
            error_msg = f"数据验证过程出错: {e}"
            self.logger.error(error_msg)
            repair_report["errors"].append(error_msg)
        
        return repair_report
    
    def _verify_state_files(self, report: Dict[str, Any]) -> None:
        """验证状态文件
        
        Args:
            report: 修复报告
        """
        state_dir = os.path.join("data", "states")
        if not os.path.exists(state_dir):
            self.logger.info(f"状态目录不存在，创建: {state_dir}")
            os.makedirs(state_dir, exist_ok=True)
            return
        
        # 检查状态文件
        state_files = [f for f in os.listdir(state_dir) 
                      if f.startswith("state_") and f.endswith(".json")]
        
        for state_file in state_files:
            file_path = os.path.join(state_dir, state_file)
            try:
                # 读取状态文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 验证基本结构
                if not all(k in data for k in ("version", "timestamp", "modules", "checksum")):
                    raise ValueError("状态文件结构不完整")
                
                # 验证校验和
                original_checksum = data.get("checksum", "")
                data_copy = data.copy()
                data_copy.pop("checksum", None)
                
                # 计算新的校验和
                data_str = json.dumps(data_copy, sort_keys=True)
                new_checksum = hashlib.md5(data_str.encode('utf-8')).hexdigest()
                
                if original_checksum != new_checksum:
                    self.logger.warning(f"状态文件校验和不匹配: {file_path}")
                    # 修复校验和
                    data["checksum"] = new_checksum
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                    report["fixed_files"].append(file_path)
                else:
                    report["skipped_files"].append(file_path)
            
            except Exception as e:
                error_msg = f"验证状态文件失败: {file_path}, 错误: {e}"
                self.logger.error(error_msg)
                report["failed_files"].append(file_path)
                report["errors"].append(error_msg)
    
    def _verify_config_files(self, report: Dict[str, Any]) -> None:
        """验证配置文件
        
        Args:
            report: 修复报告
        """
        config_dir = os.path.join("data", "config")
        if not os.path.exists(config_dir):
            self.logger.info(f"配置目录不存在，创建: {config_dir}")
            os.makedirs(config_dir, exist_ok=True)
            return
        
        # 检查配置文件
        config_files = [f for f in os.listdir(config_dir) if f.endswith(".json")]
        
        for config_file in config_files:
            file_path = os.path.join(config_dir, config_file)
            try:
                # 读取配置文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 简单验证JSON结构
                if not isinstance(data, dict):
                    raise ValueError("配置文件必须是有效的JSON对象")
                
                report["skipped_files"].append(file_path)
            
            except json.JSONDecodeError:
                self.logger.error(f"配置文件JSON格式错误: {file_path}")
                # 尝试修复JSON
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 简单修复尝试 (删除尾部逗号等)
                    content = content.replace(",\n}", "\n}")
                    content = content.replace(",]", "]")
                    
                    # 尝试解析修复后的内容
                    data = json.loads(content)
                    
                    # 如果成功，保存修复后的文件
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                    
                    report["fixed_files"].append(file_path)
                except Exception as e:
                    error_msg = f"修复配置文件失败: {file_path}, 错误: {e}"
                    self.logger.error(error_msg)
                    report["failed_files"].append(file_path)
                    report["errors"].append(error_msg)
            
            except Exception as e:
                error_msg = f"验证配置文件失败: {file_path}, 错误: {e}"
                self.logger.error(error_msg)
                report["failed_files"].append(file_path)
                report["errors"].append(error_msg)
    
    def _verify_log_files(self, report: Dict[str, Any]) -> None:
        """验证日志文件
        
        Args:
            report: 修复报告
        """
        log_dir = os.path.join("logs")
        if not os.path.exists(log_dir):
            self.logger.info(f"日志目录不存在，创建: {log_dir}")
            os.makedirs(log_dir, exist_ok=True)
            return
        
        # 日志文件通常不需要修复，只检查是否存在损坏
        log_files = [f for f in os.listdir(log_dir) if f.endswith(".log")]
        
        for log_file in log_files:
            file_path = os.path.join(log_dir, log_file)
            try:
                # 检查文件是否可读
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    # 只读取前几行以验证
                    for _ in range(5):
                        f.readline()
                
                report["skipped_files"].append(file_path)
            
            except Exception as e:
                error_msg = f"验证日志文件失败: {file_path}, 错误: {e}"
                self.logger.error(error_msg)
                report["failed_files"].append(file_path)
                report["errors"].append(error_msg)
    
    def get_current_mode(self) -> RecoveryMode:
        """获取当前恢复模式
        
        Returns:
            当前恢复模式
        """
        return self._current_mode
    
    def is_recovery_in_progress(self) -> bool:
        """检查是否正在进行恢复
        
        Returns:
            是否正在恢复
        """
        return self._recovery_in_progress
    
    def get_crash_history(self) -> List[Dict[str, Any]]:
        """获取崩溃历史记录
        
        Returns:
            崩溃记录列表
        """
        try:
            if os.path.exists(self._crash_log_path):
                with open(self._crash_log_path, 'r', encoding='utf-8') as f:
                    crash_log = json.load(f)
                return crash_log.get("crashes", [])
            return []
        except Exception as e:
            self.logger.error(f"获取崩溃历史失败: {e}")
            return [] 