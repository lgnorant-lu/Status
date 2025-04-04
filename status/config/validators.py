"""
---------------------------------------------------------------
File name:                  validators.py
Author:                     Ignorant-lu
Date created:               2024/04/05
Description:                配置验证工具类
----------------------------------------------------------------

Changed history:            
                            2024/04/05: 初始创建;
----
"""

import json
import jsonschema
from typing import Dict, Any, List, Optional, Union, Callable


class ConfigValidationError(Exception):
    """配置验证错误"""
    pass


class ConfigValidator:
    """配置验证器类，提供对配置的验证功能"""
    
    @staticmethod
    def validate_with_schema(config: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """使用JSON Schema验证配置
        
        Args:
            config: 要验证的配置
            schema: JSON Schema定义
            
        Returns:
            bool: 验证是否通过
            
        Raises:
            ConfigValidationError: 验证失败时抛出，包含错误详情
        """
        try:
            jsonschema.validate(instance=config, schema=schema)
            return True
        except jsonschema.exceptions.ValidationError as e:
            path = "/".join(str(p) for p in e.path)
            error_message = f"配置验证失败: {e.message}，路径: {path}"
            raise ConfigValidationError(error_message) from e
    
    @staticmethod
    def validate_with_function(config: Dict[str, Any], 
                             validator: Callable[[Dict[str, Any]], bool]) -> bool:
        """使用自定义函数验证配置
        
        Args:
            config: 要验证的配置
            validator: 验证函数，接收配置作为参数，返回布尔值
            
        Returns:
            bool: 验证是否通过
            
        Raises:
            ConfigValidationError: 验证失败时抛出
        """
        try:
            result = validator(config)
            if not result:
                raise ConfigValidationError("配置验证失败: 自定义验证未通过")
            return True
        except Exception as e:
            if not isinstance(e, ConfigValidationError):
                error_message = f"配置验证失败: {str(e)}"
                raise ConfigValidationError(error_message) from e
            raise
    
    @staticmethod
    def load_schema_from_file(schema_path: str) -> Dict[str, Any]:
        """从文件加载JSON Schema
        
        Args:
            schema_path: Schema文件路径
            
        Returns:
            Dict[str, Any]: 加载的Schema
            
        Raises:
            ConfigValidationError: 加载失败时抛出
        """
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            return schema
        except Exception as e:
            error_message = f"无法加载Schema文件 {schema_path}: {str(e)}"
            raise ConfigValidationError(error_message) from e
            
    @staticmethod
    def validate_types(config: Dict[str, Any], type_map: Dict[str, type]) -> bool:
        """验证配置项的类型
        
        Args:
            config: 要验证的配置
            type_map: 键到类型的映射，如 {'key': str, 'count': int}
            
        Returns:
            bool: 验证是否通过
            
        Raises:
            ConfigValidationError: 验证失败时抛出
        """
        for key, expected_type in type_map.items():
            if key in config:
                value = config[key]
                if not isinstance(value, expected_type):
                    error_message = f"配置项 '{key}' 类型错误: 期望 {expected_type.__name__}，" \
                                  f"实际是 {type(value).__name__}"
                    raise ConfigValidationError(error_message)
        return True
        
    @staticmethod
    def validate_required(config: Dict[str, Any], required_keys: List[str]) -> bool:
        """验证必需的配置项是否存在
        
        Args:
            config: 要验证的配置
            required_keys: 必需键列表
            
        Returns:
            bool: 验证是否通过
            
        Raises:
            ConfigValidationError: 验证失败时抛出
        """
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            error_message = f"缺少必需的配置项: {', '.join(missing_keys)}"
            raise ConfigValidationError(error_message)
        return True
        
    @staticmethod
    def validate_version(config: Dict[str, Any], 
                       min_version: Optional[str] = None, 
                       max_version: Optional[str] = None) -> bool:
        """验证配置版本
        
        Args:
            config: 要验证的配置
            min_version: 最小版本要求
            max_version: 最大版本要求
            
        Returns:
            bool: 验证是否通过
            
        Raises:
            ConfigValidationError: 验证失败时抛出
        """
        if "version" not in config:
            error_message = "配置缺少版本信息"
            raise ConfigValidationError(error_message)
            
        version = config["version"]
        if not isinstance(version, str):
            error_message = f"版本必须是字符串，而不是 {type(version).__name__}"
            raise ConfigValidationError(error_message)
            
        # 解析版本号
        try:
            version_parts = list(map(int, version.split('.')))
        except ValueError:
            error_message = f"无效的版本格式: {version}"
            raise ConfigValidationError(error_message)
            
        # 验证最小版本
        if min_version:
            try:
                min_parts = list(map(int, min_version.split('.')))
                
                # 确保两个版本有相同的部分数
                while len(version_parts) < len(min_parts):
                    version_parts.append(0)
                while len(min_parts) < len(version_parts):
                    min_parts.append(0)
                    
                # 比较各部分
                for i in range(len(version_parts)):
                    if version_parts[i] < min_parts[i]:
                        error_message = f"配置版本 {version} 低于最小要求 {min_version}"
                        raise ConfigValidationError(error_message)
                    elif version_parts[i] > min_parts[i]:
                        break
            except ValueError:
                error_message = f"无效的最小版本格式: {min_version}"
                raise ConfigValidationError(error_message)
                
        # 验证最大版本
        if max_version:
            try:
                max_parts = list(map(int, max_version.split('.')))
                
                # 确保两个版本有相同的部分数
                while len(version_parts) < len(max_parts):
                    version_parts.append(0)
                while len(max_parts) < len(version_parts):
                    max_parts.append(0)
                    
                # 比较各部分
                for i in range(len(version_parts)):
                    if version_parts[i] > max_parts[i]:
                        error_message = f"配置版本 {version} 高于最大要求 {max_version}"
                        raise ConfigValidationError(error_message)
                    elif version_parts[i] < max_parts[i]:
                        break
            except ValueError:
                error_message = f"无效的最大版本格式: {max_version}"
                raise ConfigValidationError(error_message)
                
        return True 