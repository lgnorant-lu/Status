"""
---------------------------------------------------------------
File name:                  placeholder_factory.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                占位符工厂，负责动态加载和提供各状态的占位符动画
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建;
----
"""
import importlib
import logging
from status.behavior.pet_state import PetState
from status.animation.animation import Animation

logger = logging.getLogger(__name__)

class PlaceholderFactory:
    """占位符工厂，负责动态加载和提供各状态的占位符动画"""
    
    def __init__(self):
        # 可能的未来扩展：已知状态的注册表或发现机制
        pass

    def get_animation(self, state: PetState) -> Animation | None:
        """根据状态获取对应的占位符动画
        
        Args:
            state: 宠物状态
            
        Returns:
            Animation | None: 对应状态的动画对象，如果加载失败则返回None
        """
        module_name = state.name.lower() + "_placeholder"
        try:
            module_path = f"status.pet_assets.placeholders.{module_name}"
            logger.debug(f"尝试加载占位符模块: {module_path}")
            placeholder_module = importlib.import_module(module_path)
            if hasattr(placeholder_module, "create_animation"):
                animation_instance = placeholder_module.create_animation()
                if isinstance(animation_instance, Animation):
                    logger.debug(f"成功加载{state.name}状态的占位符动画")
                    return animation_instance
                else:
                    logger.error(f"错误: {module_path}中的create_animation未返回Animation对象")
                    return None
            else:
                logger.error(f"错误: 在{module_path}中未找到create_animation函数")
                return None
        except ImportError:
            logger.warning(f"未能导入状态{state.name}的占位符模块{module_path}")
            return None
        except Exception as e:
            logger.error(f"加载状态{state.name}的占位符时发生意外错误: {e}")
            return None 