"""
---------------------------------------------------------------
File name:                  resource_loader.py
Author:                     Ignorant-lu
Date created:               2025/04/15
Description:                资源加载器相关核心模块（最小实现，供测试用）
----------------------------------------------------------------
Changed history:            
                            2025/04/15: 初始创建，最小实现以通过pytest测试;
----
"""

import json
from .resource_pack import resource_pack_manager

class ResourceLoader:
    def __init__(self, manager=None):
        print("DEBUG: ResourceLoader loaded from", __file__)
        # 支持依赖注入，默认使用全局resource_pack_manager
        self._manager = manager or resource_pack_manager
        self._image_cache = {}
        self._sound_cache = {}
        self._font_cache = {}
        self._json_cache = {}
        self._text_cache = {}
        self.initialized = False

    @property
    def manager(self):
        return self._manager

    def set_manager(self, manager):
        # 运行时切换资源管理器实例，便于测试和mock
        if not hasattr(manager, 'initialize') or not hasattr(manager, 'has_resource') or not hasattr(manager, 'get_resource_content'):
            raise ValueError("Invalid manager instance")
        self._manager = manager

    # 兼容所有典型接口，确保测试用例访问无AttributeError
    def initialize(self):
        return self.manager.initialize()

    def has_resource(self, path):
        return self.manager.has_resource(path)

    def get_resource_content(self, path):
        return self.manager.get_resource_content(path)

    def clear_cache(self):
        self._image_cache.clear()
        self._sound_cache.clear()
        self._font_cache.clear()
        self._json_cache.clear()
        self._text_cache.clear()

    def reload(self):
        self.clear_cache()
        mgr = self.manager
        if hasattr(mgr, 'reload'):
            return mgr.reload()
        return mgr.initialize()

    def load_image(self, path):
        if path in self._image_cache:
            return self._image_cache[path]
        content = self.get_resource_content(path)
        self._image_cache[path] = content
        return content

    def load_json(self, path):
        if path in self._json_cache:
            return self._json_cache[path]
        content = self.get_resource_content(path)
        obj = json.loads(content.decode("utf-8"))
        self._json_cache[path] = obj
        return obj

    def load_text(self, path):
        if path in self._text_cache:
            return self._text_cache[path]
        content = self.get_resource_content(path)
        text = content.decode("utf-8")
        self._text_cache[path] = text
        return text

    def load_sound(self, path):
        if path in self._sound_cache:
            return self._sound_cache[path]
        content = self.get_resource_content(path)
        self._sound_cache[path] = content
        return content

    def load_font(self, path):
        if path in self._font_cache:
            return self._font_cache[path]
        content = self.get_resource_content(path)
        self._font_cache[path] = content
        return content

    def __getattr__(self, name):
        import sys
        sys.stderr.write(f"[DEBUG] ResourceLoader object has no attribute '{name}' (check test_resource_system and all test calls)\n")
        # 让异常信息包含调用堆栈，便于pytest输出
        import traceback
        traceback.print_stack(file=sys.stderr)
        raise AttributeError(f"[DEBUG] ResourceLoader object has no attribute '{name}' (check test_resource_system and all test calls)")

resource_loader = ResourceLoader()
