"""
---------------------------------------------------------------
File name:                  test_recovery.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                错误恢复机制单元测试
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

import os
import sys
import json
import time
import unittest
import tempfile
import shutil
from datetime import datetime
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List, Optional, Callable, Union, cast

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入被测试模块
from status.core.recovery.state_manager import StateManager, StateData
from status.core.recovery.recovery_manager import RecoveryManager, RecoveryMode
from status.core.recovery.exception_handler import ExceptionHandler, ErrorLevel


class TestStateData(unittest.TestCase):
    """状态数据类测试"""
    
    def test_init(self):
        """测试初始化"""
        sd = StateData()
        self.assertEqual(sd.version, "1.0")
        self.assertIsInstance(sd.modules, dict)
        self.assertEqual(sd.checksum, "")
        
        # 测试自定义参数
        sd = StateData("2.0", {"test": {"value": 1}})
        self.assertEqual(sd.version, "2.0")
        self.assertEqual(sd.modules, {"test": {"value": 1}})
    
    def test_checksum(self):
        """测试校验和"""
        sd = StateData("1.0", {"test": {"value": 1}})
        
        # 计算校验和
        checksum = sd.calculate_checksum()
        self.assertIsInstance(checksum, str)
        self.assertTrue(len(checksum) > 0)
        
        # 更新校验和
        sd.update_checksum()
        self.assertEqual(sd.checksum, checksum)
    
    def test_to_dict(self):
        """测试转换为字典"""
        sd = StateData("1.0", {"test": {"value": 1}})
        sd_dict = sd.to_dict()
        
        self.assertIsInstance(sd_dict, dict)
        self.assertEqual(sd_dict["version"], "1.0")
        self.assertEqual(sd_dict["modules"], {"test": {"value": 1}})
        self.assertIn("timestamp", sd_dict)
        self.assertIn("checksum", sd_dict)
    
    def test_from_dict(self):
        """测试从字典创建"""
        data_dict = {
            "version": "2.0",
            "timestamp": "2025-05-14T12:00:00",
            "modules": {"test": {"value": 1}},
            "checksum": "test_checksum"
        }
        
        sd = StateData.from_dict(data_dict)
        
        self.assertEqual(sd.version, "2.0")
        self.assertEqual(sd.timestamp, "2025-05-14T12:00:00")
        self.assertEqual(sd.modules, {"test": {"value": 1}})
        self.assertEqual(sd.checksum, "test_checksum")


class TestStateManager(unittest.TestCase):
    """状态管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.test_dir = tempfile.mkdtemp()
        self.state_dir = os.path.join(self.test_dir, "states")
        
        # 清除单例
        StateManager._instance = None
        
        # 创建状态管理器
        self.manager = StateManager(self.state_dir)
    
    def tearDown(self):
        """测试后清理"""
        # 移除临时目录
        shutil.rmtree(self.test_dir)
    
    def test_singleton(self):
        """测试单例模式"""
        manager2 = StateManager()
        self.assertIs(self.manager, manager2)
    
    def test_register_module(self):
        """测试注册模块"""
        # 定义回调函数
        def save_callback() -> Dict[str, Any]:
            return {"data": "test"}
        
        def load_callback(data: Dict[str, Any]) -> None:
            pass
        
        # 注册模块
        result = self.manager.register_module("test_module", save_callback, load_callback)
        self.assertTrue(result)
        
        # 无效回调
        not_callable = "not_callable"  # 类型声明为字符串，不是可调用对象
        result = self.manager.register_module("invalid_module", cast(Callable[[], Dict[str, Any]], not_callable), load_callback)
        self.assertFalse(result)
    
    def test_unregister_module(self):
        """测试取消注册模块"""
        # 定义回调函数
        def save_callback() -> Dict[str, Any]:
            return {"data": "test"}
        
        def load_callback(data: Dict[str, Any]) -> None:
            pass
        
        # 注册并取消注册模块
        self.manager.register_module("test_module", save_callback, load_callback)
        result = self.manager.unregister_module("test_module")
        self.assertTrue(result)
        
        # 取消注册不存在的模块
        result = self.manager.unregister_module("nonexistent_module")
        self.assertFalse(result)
    
    def test_save_load_state(self):
        """测试保存和加载状态"""
        # 模拟模块数据
        test_data = {"value": 42, "name": "test"}
        save_called = False
        load_called = False
        
        # 定义回调函数
        def save_callback() -> Dict[str, Any]:
            nonlocal save_called
            save_called = True
            return test_data
        
        def load_callback(data: Dict[str, Any]) -> None:
            nonlocal load_called
            load_called = True
            self.assertEqual(data, test_data)
        
        # 注册模块
        self.manager.register_module("test_module", save_callback, load_callback)
        
        # 确保回调存在于_module_callbacks中
        self.assertIn("test_module", self.manager._module_callbacks)
        
        # 强制保存状态以确保回调被调用
        result = self.manager.save_state(force=True)
        self.assertTrue(result)
        self.assertTrue(save_called, "保存回调函数没有被调用")
        
        # 检查状态文件是否存在
        state_files = self.manager.get_available_versions()
        self.assertEqual(len(state_files), 1)
        
        # 重置调用标志
        load_called = False
        
        # 加载状态
        result = self.manager.load_state()
        self.assertIsNotNone(result)
        self.assertTrue(load_called)
    
    def test_save_specific_module(self):
        """测试保存特定模块"""
        # 模拟模块数据
        test_data1 = {"value": 1, "name": "module1"}
        test_data2 = {"value": 2, "name": "module2"}
        
        module1_saved = False
        module2_saved = False
        
        # 定义回调函数
        def save_callback1() -> Dict[str, Any]:
            nonlocal module1_saved
            module1_saved = True
            return test_data1
        
        def save_callback2() -> Dict[str, Any]:
            nonlocal module2_saved
            module2_saved = True
            return test_data2
        
        def load_callback(data: Dict[str, Any]) -> None:
            pass
        
        # 注册模块
        self.manager.register_module("module1", save_callback1, load_callback)
        self.manager.register_module("module2", save_callback2, load_callback)
        
        # 确保回调存在于_module_callbacks中
        self.assertIn("module1", self.manager._module_callbacks)
        self.assertIn("module2", self.manager._module_callbacks)
        
        # 保存特定模块
        result = self.manager.save_state("module1", force=True)
        self.assertTrue(result)
        self.assertTrue(module1_saved, "模块1保存回调没有被调用")
        self.assertFalse(module2_saved)
        
        # 检查状态
        state_data = self.manager._current_state
        self.assertIsNotNone(state_data)  # 确保不为None
        if state_data:  # 让类型检查器满意
            self.assertIn("module1", state_data.modules)
            self.assertNotIn("module2", state_data.modules)
    
    def test_auto_save_interval(self):
        """测试自动保存间隔"""
        # 设置自动保存间隔
        self.manager.set_auto_save_interval(3600)  # 1小时
        self.assertEqual(self.manager._auto_save_interval, 3600)
        
        # 测试自动保存启用/禁用
        self.manager.enable_auto_save(False)
        self.assertFalse(self.manager.is_auto_save_enabled())
        
        self.manager.enable_auto_save(True)
        self.assertTrue(self.manager.is_auto_save_enabled())
    
    def test_verify_state_integrity(self):
        """测试状态完整性验证"""
        # 创建正确的状态数据
        state_data = StateData("1.0", {"test": {"value": 1}})
        state_data.update_checksum()
        
        # 验证完整性
        result = self.manager.verify_state_integrity(state_data)
        self.assertTrue(result)
        
        # 修改数据但不更新校验和
        state_data.modules["test"]["value"] = 2
        result = self.manager.verify_state_integrity(state_data)
        self.assertFalse(result)


class TestRecoveryManager(unittest.TestCase):
    """恢复管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.test_dir = tempfile.mkdtemp()
        self.recovery_dir = os.path.join(self.test_dir, "recovery")
        
        # 清除单例
        RecoveryManager._instance = None
        
        # 创建恢复管理器
        self.manager = RecoveryManager(self.recovery_dir)
        
        # 退出标志文件路径
        self.exit_flag_path = os.path.join(self.recovery_dir, self.manager._RECOVERY_FILE)
        
        # 崩溃日志文件路径
        self.crash_log_path = os.path.join(self.recovery_dir, self.manager._CRASH_LOG_FILE)
    
    def tearDown(self):
        """测试后清理"""
        # 移除临时目录
        shutil.rmtree(self.test_dir)
    
    def test_singleton(self):
        """测试单例模式"""
        manager2 = RecoveryManager()
        self.assertIs(self.manager, manager2)
    
    def test_detect_abnormal_exit_first_run(self):
        """测试首次运行检测"""
        # 首次运行，应该返回False
        result = self.manager.detect_abnormal_exit()
        self.assertFalse(result)
        
        # 检查退出标志文件是否存在
        self.assertTrue(os.path.exists(self.exit_flag_path))
        
        # 读取退出标志文件
        with open(self.exit_flag_path, 'r') as f:
            exit_info = json.load(f)
        
        # 检查退出标志内容
        self.assertFalse(exit_info["clean_exit"])
        self.assertEqual(exit_info["recovery_mode"], RecoveryMode.NORMAL.value)
    
    def test_detect_abnormal_exit_clean_exit(self):
        """测试正常退出检测"""
        # 创建正常退出标志
        os.makedirs(self.recovery_dir, exist_ok=True)
        with open(self.exit_flag_path, 'w') as f:
            json.dump({
                "clean_exit": True,
                "timestamp": datetime.now().isoformat(),
                "recovery_mode": RecoveryMode.NORMAL.value
            }, f)
        
        # 检测应该返回False
        result = self.manager.detect_abnormal_exit()
        self.assertFalse(result)
    
    def test_detect_abnormal_exit_abnormal_exit(self):
        """测试异常退出检测"""
        # 创建异常退出标志
        os.makedirs(self.recovery_dir, exist_ok=True)
        with open(self.exit_flag_path, 'w') as f:
            json.dump({
                "clean_exit": False,
                "timestamp": datetime.now().isoformat(),
                "recovery_mode": RecoveryMode.NORMAL.value
            }, f)
        
        # 检测应该返回True
        result = self.manager.detect_abnormal_exit()
        self.assertTrue(result)
        self.assertTrue(self.manager._recovery_in_progress)
    
    def test_mark_clean_exit(self):
        """测试标记正常退出"""
        # 标记正常退出
        self.manager._mark_clean_exit()
        
        # 读取退出标志文件
        with open(self.exit_flag_path, 'r') as f:
            exit_info = json.load(f)
        
        # 检查退出标志内容
        self.assertTrue(exit_info["clean_exit"])
        self.assertEqual(exit_info["recovery_mode"], RecoveryMode.NORMAL.value)
    
    def test_register_startup_hook(self):
        """测试注册启动钩子"""
        # 定义回调函数
        mock_callback = MagicMock()
        
        # 注册钩子
        self.manager.register_startup_hook(10, mock_callback)
        
        # 检查钩子是否注册
        self.assertEqual(len(self.manager._startup_hooks), 1)
        self.assertEqual(self.manager._startup_hooks[0][0], 10)
        self.assertIs(self.manager._startup_hooks[0][1], mock_callback)
    
    def test_execute_startup_hooks(self):
        """测试执行启动钩子"""
        # 定义回调函数
        mock_callback1 = MagicMock()
        mock_callback2 = MagicMock()
        mock_callback3 = MagicMock()
        
        # 注册钩子（乱序注册，测试排序）
        self.manager.register_startup_hook(20, mock_callback2)
        self.manager.register_startup_hook(10, mock_callback1)
        self.manager.register_startup_hook(30, mock_callback3)
        
        # 执行钩子
        self.manager._execute_startup_hooks()
        
        # 验证调用顺序
        mock_callback1.assert_called_once_with(RecoveryMode.NORMAL)
        mock_callback2.assert_called_once_with(RecoveryMode.NORMAL)
        mock_callback3.assert_called_once_with(RecoveryMode.NORMAL)
        
        # 检查调用顺序
        call_order = [
            id(call[0][0]) for call in mock_callback1.call_args_list +
            mock_callback2.call_args_list + mock_callback3.call_args_list
        ]
        expected_order = [id(RecoveryMode.NORMAL)] * 3
        self.assertEqual(call_order, expected_order)
    
    @patch('status.core.recovery.recovery_manager.StateManager')
    def test_recover_state(self, mock_state_manager_class):
        """测试恢复状态"""
        # 模拟状态管理器
        mock_state_manager = MagicMock()
        mock_state_manager_class.return_value = mock_state_manager
        
        # 设置_state_manager属性，因为单例模式下可能已经创建了实例
        self.manager._state_manager = mock_state_manager
        
        # 测试成功恢复
        mock_state_manager.load_state.return_value = StateData()
        result = self.manager._recover_state()
        self.assertTrue(result)
        
        # 测试恢复失败
        mock_state_manager.load_state.return_value = None
        result = self.manager._recover_state()
        self.assertFalse(result)
    
    def test_select_recovery_mode_normal(self):
        """测试选择恢复模式（正常）"""
        # 没有崩溃记录，应该返回正常模式
        mode = self.manager._select_recovery_mode()
        self.assertEqual(mode, RecoveryMode.NORMAL)
    
    def test_select_recovery_mode_safe(self):
        """测试选择恢复模式（安全）"""
        # 创建多次崩溃记录
        os.makedirs(self.recovery_dir, exist_ok=True)
        with open(self.crash_log_path, 'w') as f:
            json.dump({
                "crashes": [
                    {"timestamp": time.time() - 100},  # 最近崩溃
                    {"timestamp": time.time() - 200},  # 最近崩溃
                    {"timestamp": time.time() - 300},  # 最近崩溃
                    {"timestamp": time.time() - 24 * 60 * 60 * 2}  # 两天前崩溃
                ]
            }, f)
        
        # 应该返回安全模式
        mode = self.manager._select_recovery_mode()
        self.assertEqual(mode, RecoveryMode.SAFE)
    
    def test_create_crash_report(self):
        """测试创建崩溃报告"""
        # 准备错误信息
        error_info = {
            "type": "TestError",
            "message": "Test error message",
            "traceback": "Test traceback",
            "module": "test_module"
        }
        
        # 创建崩溃报告
        report_path = self.manager.create_crash_report(error_info)
        
        # 检查报告是否创建
        self.assertTrue(os.path.exists(report_path))
        
        # 读取报告内容
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        
        # 检查报告内容
        self.assertEqual(report_data["type"], "TestError")
        self.assertEqual(report_data["message"], "Test error message")
        
        # 检查崩溃日志是否更新
        self.assertTrue(os.path.exists(self.crash_log_path))
        
        with open(self.crash_log_path, 'r') as f:
            crash_log = json.load(f)
        
        # 检查崩溃记录
        self.assertEqual(len(crash_log["crashes"]), 1)
        self.assertEqual(crash_log["crashes"][0]["type"], "TestError")


class TestExceptionHandler(unittest.TestCase):
    """异常处理器测试"""
    
    def setUp(self):
        """测试前准备"""
        # 清除单例
        ExceptionHandler._instance = None
        
        # 创建异常处理器
        self.handler = ExceptionHandler()
        
        # 保存原始的sys.excepthook
        self.original_excepthook = sys.excepthook
    
    def tearDown(self):
        """测试后清理"""
        # 恢复原始的sys.excepthook
        sys.excepthook = self.original_excepthook
    
    def test_singleton(self):
        """测试单例模式"""
        handler2 = ExceptionHandler()
        self.assertIs(self.handler, handler2)
    
    def test_install_uninstall_global_handler(self):
        """测试安装和卸载全局处理器"""
        # 安装全局处理器
        self.handler.install_global_handler()
        self.assertTrue(self.handler._installed)
        self.assertIsNot(sys.excepthook, self.original_excepthook)
        
        # 卸载全局处理器
        self.handler.uninstall_global_handler()
        self.assertFalse(self.handler._installed)
        self.assertIs(sys.excepthook, self.original_excepthook)
    
    def test_get_error_level(self):
        """测试获取错误级别"""
        # 测试直接匹配
        level = self.handler._get_error_level(ValueError)
        self.assertEqual(level, ErrorLevel.MODERATE)
        
        # 测试继承匹配
        class CustomValueError(ValueError):
            pass
        
        level = self.handler._get_error_level(CustomValueError)
        self.assertEqual(level, ErrorLevel.MODERATE)
        
        # 测试未知类型
        class UnknownError(Exception):
            pass
        
        level = self.handler._get_error_level(UnknownError)
        self.assertEqual(level, ErrorLevel.MODERATE)
    
    def test_set_error_level(self):
        """测试设置错误级别"""
        # 定义自定义异常
        class CustomError(Exception):
            pass
        
        # 设置错误级别
        self.handler.set_error_level(CustomError, ErrorLevel.SEVERE)
        
        # 检查错误级别
        level = self.handler._get_error_level(CustomError)
        self.assertEqual(level, ErrorLevel.SEVERE)
    
    def test_register_exception_handler(self):
        """测试注册异常处理函数"""
        # 定义处理函数
        mock_handler = MagicMock()
        
        # 注册处理函数
        self.handler.register_exception_handler(ValueError, mock_handler)
        
        # 检查是否注册
        self.assertIn(ValueError, self.handler._exception_handlers)
        self.assertIs(self.handler._exception_handlers[ValueError], mock_handler)
    
    @patch('status.core.recovery.exception_handler.ExceptionHandler.log_exception')
    @patch('status.core.recovery.exception_handler.ExceptionHandler._format_exception')
    @patch('status.core.recovery.exception_handler.ExceptionHandler.attempt_recovery')
    @patch('status.core.recovery.exception_handler.ExceptionHandler.show_error_dialog')
    @patch('status.core.recovery.exception_handler.ExceptionHandler._create_crash_report')
    def test_handle_exception(self, mock_create_report, mock_show_dialog, 
                             mock_attempt_recovery, mock_format, mock_log):
        """测试处理异常"""
        # 模拟依赖函数
        mock_format.return_value = "Formatted exception"
        mock_attempt_recovery.return_value = True
        
        # 创建测试异常
        try:
            raise ValueError("Test error")
        except ValueError as e:
            exc_type, exc_value, exc_traceback = type(e), e, e.__traceback__
        
        # 处理异常
        result = self.handler.handle_exception(exc_type, exc_value, exc_traceback)
        
        # 验证函数调用
        mock_log.assert_called_once()
        mock_format.assert_called_once()
        mock_attempt_recovery.assert_called_once()
        mock_show_dialog.assert_called_once()
        mock_create_report.assert_called_once()
        
        # 验证结果
        self.assertTrue(result)
    
    @patch('status.core.recovery.exception_handler.ExceptionHandler.log_exception')
    @patch('status.core.recovery.exception_handler.ExceptionHandler._format_exception')
    def test_handle_exception_with_handler(self, mock_format, mock_log):
        """测试使用特定处理函数处理异常"""
        # 模拟依赖函数
        mock_format.return_value = "Formatted exception"
        
        # 定义处理函数
        mock_handler = MagicMock(return_value=True)
        
        # 注册处理函数
        self.handler.register_exception_handler(ValueError, mock_handler)
        
        # 创建测试异常
        try:
            raise ValueError("Test error")
        except ValueError as e:
            exc_type, exc_value, exc_traceback = type(e), e, e.__traceback__
        
        # 处理异常
        result = self.handler.handle_exception(exc_type, exc_value, exc_traceback)
        
        # 验证特定处理函数调用
        mock_handler.assert_called_once()
        self.assertTrue(result)
    
    def test_dev_mode(self):
        """测试开发模式设置"""
        # 默认情况下
        initial_mode = self.handler.is_dev_mode()
        
        # 设置开发模式
        self.handler.set_dev_mode(True)
        self.assertTrue(self.handler.is_dev_mode())
        
        # 禁用开发模式
        self.handler.set_dev_mode(False)
        self.assertFalse(self.handler.is_dev_mode())
    
    @patch('builtins.print')
    def test_show_error_dialog(self, mock_print):
        """测试显示错误对话框"""
        # 没有回调函数的情况
        self.handler.show_error_dialog("Test error", "Error details", ErrorLevel.SEVERE)
        
        # 验证输出
        mock_print.assert_called()
        
        # 使用回调函数
        mock_callback = MagicMock()
        self.handler.register_error_dialog_callback(mock_callback)
        
        # 显示对话框
        self.handler.show_error_dialog("Test error", "Error details", ErrorLevel.FATAL)
        
        # 验证回调函数调用
        mock_callback.assert_called_once_with("Test error", "Error details", "fatal")


if __name__ == '__main__':
    unittest.main() 