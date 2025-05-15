"""
---------------------------------------------------------------
File name:                  errors.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                核心错误和异常定义
----------------------------------------------------------------

Changed history:
                            2025/05/15: 初始创建;
----
"""

class AssetLoadError(Exception):
    """资源加载失败时引发的基础异常。"""
    pass

class ResourceNotFoundError(AssetLoadError):
    """当找不到特定资源时引发。"""
    def __init__(self, resource_path: str, message: str = ""):
        self.resource_path = resource_path
        self.message = message if message else f"Resource not found at path: {resource_path}"
        super().__init__(self.message)

class ResourceDecodingError(AssetLoadError):
    """当资源内容无法解码时引发（例如，损坏的图像、无效的JSON）。"""
    def __init__(self, resource_path: str, original_error: Exception | None = None, message: str = ""):
        self.resource_path = resource_path
        self.original_error = original_error
        self.message = message if message else f"Error decoding resource at path: {resource_path}"
        if original_error:
            self.message += f" (Original error: {original_error})"
        super().__init__(self.message)

# 可以在此添加更多特定于核心功能的异常类型 