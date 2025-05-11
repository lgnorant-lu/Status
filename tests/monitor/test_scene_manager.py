"""
---------------------------------------------------------------
File name:                  test_scene_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                场景管理器测试
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import unittest
from unittest.mock import patch, MagicMock
import logging

from status.monitor.scene_manager import SceneManager


class TestSceneManager(unittest.TestCase):
    """测试场景管理器"""

    def setUp(self):
        """测试前的准备工作"""
        # 配置日志
        logging.basicConfig(level=logging.CRITICAL)
        
        # 创建场景管理器实例
        self.data_collector = MagicMock()
        self.scene_manager = SceneManager()
        
    def test_init(self):
        """测试初始化"""
        # 默认配置初始化
        scene_manager = SceneManager()
        self.assertIsNotNone(scene_manager)
        self.assertIsInstance(scene_manager.config, dict)
        
        # 自定义配置初始化
        config = {
            "default_scenes": [
                {
                    "id": "test_scene",
                    "metadata": {
                        "name": "测试场景"
                    },
                    "collection": {
                        "metrics": ["cpu", "memory"]
                    }
                }
            ]
        }
        scene_manager = SceneManager(config)
        self.assertEqual(scene_manager.config, config)
        
        # 验证默认场景是否创建
        self.assertTrue(len(scene_manager.scenes) > 0)
        
    def test_register_default_scenes(self):
        """测试注册默认场景"""
        # 清空场景
        self.scene_manager.scenes = {}
        self.scene_manager.active_scene_id = None
        
        # 创建默认场景
        self.scene_manager.create_default_scenes()
        
        # 验证结果
        self.assertNotEqual(len(self.scene_manager.scenes), 0)
        
    def test_register_scene(self):
        """测试注册新场景"""
        # 创建新场景
        scene_config = {
            "metadata": {
                "name": "自定义场景",
                "description": "自定义场景描述",
                "icon": "custom_icon"
            },
            "collection": {
                "metrics": ["cpu", "memory", "disk"],
                "interval": 1.5
            }
        }
        
        scene = self.scene_manager.create_scene("custom_scene", scene_config)
        
        # 验证结果
        self.assertIsNotNone(scene)
        self.assertIn("custom_scene", self.scene_manager.scenes)
        
    def test_unregister_scene(self):
        """测试注销场景"""
        # 创建测试场景
        scene_config = {
            "metadata": {
                "name": "测试场景",
            },
            "collection": {
                "metrics": ["cpu"]
            }
        }
        self.scene_manager.create_scene("test_scene", scene_config)
        
        # 切换到测试场景
        self.scene_manager.set_active_scene("test_scene")
        self.assertEqual(self.scene_manager.active_scene_id, "test_scene")
        
        # 删除测试场景
        result = self.scene_manager.delete_scene("test_scene")
        
        # 验证结果
        self.assertTrue(result)
        self.assertNotIn("test_scene", self.scene_manager.scenes)
        self.assertNotEqual(self.scene_manager.active_scene_id, "test_scene")  # 应该已切换到其他场景
        
        # 测试删除不存在的场景
        result = self.scene_manager.delete_scene("non_existent_scene")
        
        # 验证结果
        self.assertFalse(result)
        
        # 测试删除所有场景
        for scene_id in list(self.scene_manager.scenes.keys()):
            self.scene_manager.delete_scene(scene_id)
            
        # 验证结果
        self.assertEqual(len(self.scene_manager.scenes), 0)
        self.assertIsNone(self.scene_manager.active_scene_id)
        
    def test_switch_to_scene(self):
        """测试切换场景"""
        # 创建两个测试场景
        self.scene_manager.create_scene("scene1", {
            "metadata": {
                "name": "场景1",
            },
            "collection": {
                "metrics": ["cpu"]
            }
        })
        
        self.scene_manager.create_scene("scene2", {
            "metadata": {
                "name": "场景2",
            },
            "collection": {
                "metrics": ["memory"]
            }
        })
        
        # 切换到场景1
        result = self.scene_manager.set_active_scene("scene1")
        
        # 验证结果
        self.assertTrue(result)
        self.assertEqual(self.scene_manager.active_scene_id, "scene1")
        
        # 切换到场景2
        result = self.scene_manager.set_active_scene("scene2")
        
        # 验证结果
        self.assertTrue(result)
        self.assertEqual(self.scene_manager.active_scene_id, "scene2")
        
        # 测试切换到不存在的场景
        result = self.scene_manager.set_active_scene("non_existent_scene")
        
        # 验证结果
        self.assertFalse(result)
        self.assertEqual(self.scene_manager.active_scene_id, "scene2")  # 保持原场景
        
    def test_get_current_scene(self):
        """测试获取当前场景"""
        # 创建测试场景
        self.scene_manager.create_scene("test_scene", {
            "metadata": {
                "name": "测试场景",
                "description": "测试场景描述"
            },
            "collection": {
                "metrics": ["cpu", "memory"]
            }
        })
        
        # 切换到测试场景
        self.scene_manager.set_active_scene("test_scene")
        
        # 获取当前场景
        scene = self.scene_manager.get_active_scene()
        
        # 验证结果
        self.assertIsNotNone(scene)
        self.assertEqual(scene.scene_id, "test_scene")
        
        # 测试无当前场景的情况
        self.scene_manager.active_scene_id = None
        scene = self.scene_manager.get_active_scene()
        
        # 验证结果
        self.assertIsNone(scene)
        
    def test_get_scene(self):
        """测试获取指定场景"""
        # 创建测试场景
        scene_config = {
            "metadata": {
                "name": "测试场景",
                "description": "测试场景描述"
            },
            "collection": {
                "metrics": ["cpu", "memory"]
            }
        }
        self.scene_manager.create_scene("test_scene", scene_config)
        
        # 获取场景
        scene = self.scene_manager.get_scene("test_scene")
        
        # 验证结果
        self.assertIsNotNone(scene)
        self.assertEqual(scene.scene_id, "test_scene")
        
        # 测试获取不存在的场景
        scene = self.scene_manager.get_scene("non_existent_scene")
        
        # 验证结果
        self.assertIsNone(scene)
        
    def test_get_all_scenes(self):
        """测试获取所有场景"""
        # 清空场景
        self.scene_manager.scenes = {}
        
        # 创建多个测试场景
        self.scene_manager.create_scene("scene1", {
            "metadata": {
                "name": "场景1"
            },
            "collection": {
                "metrics": ["cpu"]
            }
        })
        
        self.scene_manager.create_scene("scene2", {
            "metadata": {
                "name": "场景2"
            },
            "collection": {
                "metrics": ["memory"]
            }
        })
        
        # 获取所有场景
        scenes = self.scene_manager.list_scenes()
        
        # 验证结果
        self.assertEqual(len(scenes), 2)
        scene_ids = [scene["id"] for scene in scenes]
        self.assertIn("scene1", scene_ids)
        self.assertIn("scene2", scene_ids)
        
    def test_register_scene_change_callback(self):
        """测试注册场景切换回调"""
        # 这个测试假设SceneManager实现了回调机制
        # 如果没有实现，需要修改SceneManager或跳过此测试
        
        # 创建模拟回调函数
        callback1 = MagicMock()
        callback2 = MagicMock()
        
        # 目前SceneManager没有实现回调机制，跳过此测试
        self.skipTest("SceneManager目前未实现场景切换回调机制")
        
    def test_unregister_scene_change_callback(self):
        """测试注销场景切换回调"""
        # 这个测试假设SceneManager实现了回调机制
        # 如果没有实现，需要修改SceneManager或跳过此测试
        
        # 目前SceneManager没有实现回调机制，跳过此测试
        self.skipTest("SceneManager目前未实现场景切换回调机制")
        
    def test_get_current_metrics(self):
        """测试获取当前场景指标"""
        # 创建测试场景
        self.scene_manager.create_scene("test_scene", {
            "metadata": {
                "name": "测试场景"
            },
            "collection": {
                "metrics": ["cpu", "memory", "disk"]
            }
        })
        
        # 切换到测试场景
        self.scene_manager.set_active_scene("test_scene")
        
        # 获取当前场景配置
        config = self.scene_manager.get_scene_collection_config()
        
        # 验证结果
        self.assertIn("metrics", config)
        self.assertIn("cpu", config["metrics"])
        self.assertIn("memory", config["metrics"])
        self.assertIn("disk", config["metrics"])
        
    def test_get_current_update_interval(self):
        """测试获取当前场景更新间隔"""
        # 创建测试场景
        self.scene_manager.create_scene("test_scene", {
            "metadata": {
                "name": "测试场景"
            },
            "collection": {
                "interval": 2.5
            }
        })
        
        # 切换到测试场景
        self.scene_manager.set_active_scene("test_scene")
        
        # 获取当前场景采集配置
        config = self.scene_manager.get_scene_collection_config()
        
        # 验证结果
        self.assertIn("interval", config)
        self.assertEqual(config["interval"], 2.5)
        
    def test_collect_current_scene_data(self):
        """测试收集当前场景数据"""
        # 创建测试场景
        self.scene_manager.create_scene("test_scene", {
            "metadata": {
                "name": "测试场景"
            },
            "collection": {
                "metrics": ["cpu", "memory"],
                "interval": 1.0
            }
        })
        
        # 切换到测试场景
        self.scene_manager.set_active_scene("test_scene")
        
        # 创建模拟数据采集器
        mock_collector = MagicMock()
        mock_collector.collect_data.return_value = {
            "cpu": {"usage": 50.0},
            "memory": {"percent": 60.0}
        }
        
        # 这个测试假设SceneManager可以接收外部数据采集器
        # 目前SceneManager不支持此功能，跳过此测试
        self.skipTest("SceneManager目前不支持外部数据采集器")
        
    def test_set_data_collector(self):
        """测试设置数据采集器"""
        # 创建模拟数据采集器
        new_collector = MagicMock()
        
        # 这个测试假设SceneManager可以接收外部数据采集器
        # 目前SceneManager不支持此功能，跳过此测试
        self.skipTest("SceneManager目前不支持外部数据采集器")
        
    def test_update_scene_config(self):
        """测试更新场景配置"""
        # 创建测试场景
        self.scene_manager.create_scene("test_scene", {
            "metadata": {
                "name": "测试场景"
            },
            "collection": {
                "metrics": ["cpu"],
                "interval": 1.0
            }
        })
        
        # 更新场景配置
        new_config = {
            "collection": {
                "metrics": ["cpu", "memory", "disk"],
                "interval": 2.0
            },
            "metadata": {
                "description": "已更新的场景描述"
            }
        }
        
        result = self.scene_manager.update_scene_config("test_scene", new_config)
        
        # 验证结果
        self.assertTrue(result)
        
        # 获取更新后的场景
        scene = self.scene_manager.get_scene("test_scene")
        self.assertIsNotNone(scene)
        
        # 验证配置是否已更新
        collection_config = scene.get_collection_config()
        self.assertIn("metrics", collection_config)
        self.assertEqual(len(collection_config["metrics"]), 3)
        self.assertEqual(collection_config["interval"], 2.0)
        
        metadata = scene.get_metadata()
        self.assertIn("description", metadata)
        self.assertEqual(metadata["description"], "已更新的场景描述")
        
        # 测试更新不存在的场景
        result = self.scene_manager.update_scene_config("non_existent_scene", new_config)
        self.assertFalse(result)
        
    def tearDown(self):
        """测试结束后的清理工作"""
        pass


if __name__ == '__main__':
    unittest.main() 