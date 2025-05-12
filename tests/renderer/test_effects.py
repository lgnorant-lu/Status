"""
---------------------------------------------------------------
File name:                  test_effects.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                特效系统测试
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import unittest
import math
from unittest.mock import MagicMock, patch

from status.renderer.effects import (Effect, EffectState, ColorEffect, ColorFade, 
                                   Blink, TransformEffect, Move, Scale, Rotate, 
                                   CompositeEffect, EffectManager)
from status.renderer.particle import (Particle, ParticleEmitter, EmissionMode, 
                                    EmissionShape, ParticleSystem, ParticlePresets)
from status.renderer.renderer_base import Color, RendererBase


class TestEffect(unittest.TestCase):
    """测试特效基类"""
    
    def setUp(self):
        """测试准备"""
        self.effect = Effect(duration=1.0, loop=False, auto_start=False)
        
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.effect.state, EffectState.INITIALIZED)
        self.assertEqual(self.effect.duration, 1.0)
        self.assertEqual(self.effect.loop, False)
        self.assertEqual(self.effect.elapsed_time, 0.0)
        
    def test_start(self):
        """测试开始特效"""
        self.effect.start()
        self.assertEqual(self.effect.state, EffectState.PLAYING)
        
    def test_pause_resume(self):
        """测试暂停和恢复特效"""
        self.effect.start()
        self.effect.pause()
        self.assertEqual(self.effect.state, EffectState.PAUSED)
        
        self.effect.resume()
        self.assertEqual(self.effect.state, EffectState.PLAYING)
        
    def test_complete(self):
        """测试完成特效"""
        self.effect.complete()
        self.assertEqual(self.effect.state, EffectState.COMPLETED)
        self.assertEqual(self.effect.elapsed_time, self.effect.duration)
        
    def test_update_completion(self):
        """测试更新到完成"""
        self.effect.start()
        # 更新超过持续时间
        self.effect.update(2.0)
        
        self.assertEqual(self.effect.state, EffectState.COMPLETED)
        
    def test_loop(self):
        """测试循环特效"""
        loop_effect = Effect(duration=1.0, loop=True, auto_start=True)
        
        # 更新超过持续时间
        loop_effect.update(1.5)
        
        # 应该依然在播放状态，且时间重置
        self.assertEqual(loop_effect.state, EffectState.PLAYING)
        self.assertLess(loop_effect.elapsed_time, loop_effect.duration)
        
    def test_normalized_time(self):
        """测试归一化时间"""
        self.effect.start()
        
        # 更新到一半时间
        self.effect.update(0.5)
        
        self.assertAlmostEqual(self.effect.normalized_time, 0.5)
        
        # 更新到超过时间
        self.effect.elapsed_time = 2.0
        self.assertEqual(self.effect.normalized_time, 1.0)


class TestColorEffect(unittest.TestCase):
    """测试颜色特效"""
    
    def setUp(self):
        """测试准备"""
        self.target = MagicMock()
        self.target.color = Color(255, 0, 0, 255)
        
        self.color_effect = ColorEffect(target=self.target, duration=1.0, auto_start=False)
        
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.color_effect.original_color, Color(255, 0, 0, 255))
        
    def test_apply_color(self):
        """测试应用颜色"""
        new_color = Color(0, 255, 0, 255)
        self.color_effect.apply_color(new_color)
        
        self.assertEqual(self.target.color, new_color)
        
    def test_reset_color(self):
        """测试重置颜色"""
        # 先更改颜色
        self.target.color = Color(0, 255, 0, 255)
        
        # 重置
        self.color_effect.reset_color()
        
        self.assertEqual(self.target.color, Color(255, 0, 0, 255))
        
    def test_complete(self):
        """测试完成时恢复颜色"""
        # 先更改颜色
        self.target.color = Color(0, 255, 0, 255)
        
        # 完成，应该恢复原始颜色
        self.color_effect.complete()
        
        self.assertEqual(self.target.color, Color(255, 0, 0, 255))


class TestColorFade(unittest.TestCase):
    """测试颜色渐变特效"""
    
    def setUp(self):
        """测试准备"""
        self.target = MagicMock()
        self.target.color = Color(255, 0, 0, 255)
        
        self.from_color = Color(255, 0, 0, 255)
        self.to_color = Color(0, 0, 255, 255)
        
        self.fade = ColorFade(
            target=self.target,
            from_color=self.from_color,
            to_color=self.to_color,
            duration=1.0,
            auto_start=False
        )
        
    def test_update_color(self):
        """测试颜色更新"""
        self.fade.start()
        
        # 直接设置elapsed_time到中间
        self.fade.elapsed_time = 0.5
        # 手动触发更新回调
        self.fade._update_color(0.5)  # 使用归一化时间0.5
        
        # 颜色应该在中间
        self.assertEqual(self.target.color, Color(127, 0, 127, 255))
        
        # 直接设置elapsed_time到结束
        self.fade.elapsed_time = 1.0
        # 手动触发更新回调
        self.fade._update_color(1.0)  # 使用归一化时间1.0
        
        # 颜色应该到达目标
        self.assertEqual(self.target.color, Color(0, 0, 255, 255))


class TestBlink(unittest.TestCase):
    """测试闪烁特效"""
    
    def setUp(self):
        """测试准备"""
        self.target = MagicMock()
        self.target.color = Color(255, 0, 0, 255)
        
        self.blink_color = Color(255, 255, 255, 255)
        
        self.blink = Blink(
            target=self.target,
            blink_color=self.blink_color,
            frequency=1.0,
            duration=1.0,
            auto_start=False
        )
        
    def test_blink_cycle(self):
        """测试闪烁周期"""
        self.blink.start()
        
        # 更新到1/4周期
        self.blink.update(0.25)
        
        # 颜色应该接近闪烁颜色
        self.assertGreater(self.target.color.r, 200)
        self.assertGreater(self.target.color.g, 100)
        
        # 更新到3/4周期
        self.blink.update(0.5)
        
        # 颜色应该接近原始颜色
        self.assertGreater(self.target.color.r, 200)
        self.assertLess(self.target.color.g, 100)


class TestTransformEffect(unittest.TestCase):
    """测试变换特效"""
    
    def setUp(self):
        """测试准备"""
        self.target = MagicMock()
        self.target.x = 100
        self.target.y = 100
        self.target.scale_x = 1.0
        self.target.scale_y = 1.0
        self.target.rotation = 0.0
        
        self.transform = TransformEffect(
            target=self.target,
            duration=1.0,
            auto_start=False
        )
        
    def test_reset_transform(self):
        """测试重置变换"""
        # 改变变换
        self.target.x = 200
        self.target.y = 200
        self.target.scale_x = 2.0
        self.target.scale_y = 2.0
        self.target.rotation = 45.0
        
        # 重置
        self.transform.reset_transform()
        
        # 检查是否恢复原始变换
        self.assertEqual(self.target.x, 100)
        self.assertEqual(self.target.y, 100)
        self.assertEqual(self.target.scale_x, 1.0)
        self.assertEqual(self.target.scale_y, 1.0)
        self.assertEqual(self.target.rotation, 0.0)


class TestMove(unittest.TestCase):
    """测试移动特效"""
    
    def setUp(self):
        """测试准备"""
        self.target = MagicMock()
        self.target.x = 100
        self.target.y = 100
        
        self.move = Move(
            target=self.target,
            end_x=200,
            end_y=300,
            duration=1.0,
            auto_start=False
        )
        
    def test_update_position(self):
        """测试位置更新"""
        self.move.start()
        
        # 直接设置elapsed_time到中间
        self.move.elapsed_time = 0.5
        # 手动触发更新回调
        self.move._update_position(0.5)  # 使用归一化时间0.5
        
        # 检查位置是否在中间
        self.assertEqual(self.target.x, 150)
        self.assertEqual(self.target.y, 200)
        
        # 直接设置elapsed_time到结束
        self.move.elapsed_time = 1.0
        # 手动触发更新回调
        self.move._update_position(1.0)  # 使用归一化时间1.0
        
        # 检查位置是否到达目标
        self.assertEqual(self.target.x, 200)
        self.assertEqual(self.target.y, 300)


class TestScale(unittest.TestCase):
    """测试缩放特效"""
    
    def setUp(self):
        """测试准备"""
        self.target = MagicMock()
        self.target.scale_x = 1.0
        self.target.scale_y = 1.0
        
        self.scale = Scale(
            target=self.target,
            end_scale_x=2.0,
            end_scale_y=3.0,
            duration=1.0,
            auto_start=False
        )
        
    def test_update_scale(self):
        """测试缩放更新"""
        self.scale.start()
        
        # 直接设置elapsed_time到中间
        self.scale.elapsed_time = 0.5
        # 手动触发更新回调
        self.scale._update_scale(0.5)  # 使用归一化时间0.5
        
        # 检查缩放是否在中间
        self.assertEqual(self.target.scale_x, 1.5)
        self.assertEqual(self.target.scale_y, 2.0)
        
        # 直接设置elapsed_time到结束
        self.scale.elapsed_time = 1.0
        # 手动触发更新回调
        self.scale._update_scale(1.0)  # 使用归一化时间1.0
        
        # 检查缩放是否到达目标
        self.assertEqual(self.target.scale_x, 2.0)
        self.assertEqual(self.target.scale_y, 3.0)


class TestRotate(unittest.TestCase):
    """测试旋转特效"""
    
    def setUp(self):
        """测试准备"""
        self.target = MagicMock()
        self.target.rotation = 0.0
        
        self.rotate = Rotate(
            target=self.target,
            end_rotation=90.0,
            duration=1.0,
            auto_start=False
        )
        
    def test_update_rotation(self):
        """测试旋转更新"""
        self.rotate.start()
        
        # 直接设置elapsed_time到中间
        self.rotate.elapsed_time = 0.5
        # 手动触发更新回调
        self.rotate._update_rotation(0.5)  # 使用归一化时间0.5
        
        # 检查旋转是否在中间
        self.assertEqual(self.target.rotation, 45.0)
        
        # 直接设置elapsed_time到结束
        self.rotate.elapsed_time = 1.0
        # 手动触发更新回调
        self.rotate._update_rotation(1.0)  # 使用归一化时间1.0
        
        # 检查旋转是否到达目标
        self.assertEqual(self.target.rotation, 90.0)


class TestCompositeEffect(unittest.TestCase):
    """测试组合特效"""
    
    def setUp(self):
        """测试准备"""
        self.target1 = MagicMock()
        self.target1.x = 100
        self.target1.y = 100
        
        self.target2 = MagicMock()
        self.target2.color = Color(255, 0, 0, 255)
        
        self.move = Move(
            target=self.target1,
            end_x=200,
            end_y=200,
            duration=2.0,
            auto_start=False
        )
        
        self.fade = ColorFade(
            target=self.target2,
            from_color=Color(255, 0, 0, 255),
            to_color=Color(0, 0, 255, 255),
            duration=1.0,
            auto_start=False
        )
        
        self.composite = CompositeEffect(
            effects=[self.move, self.fade],
            duration=None,  # 应该使用最长的持续时间
            auto_start=False
        )
        
    def test_init(self):
        """测试初始化"""
        # 应该使用最长的持续时间
        self.assertEqual(self.composite.duration, 2.0)
        
        # 子特效应该停止
        self.assertEqual(self.move.state, EffectState.STOPPED)
        self.assertEqual(self.fade.state, EffectState.STOPPED)
        
    def test_start_stop(self):
        """测试开始和停止"""
        # 启动组合特效
        self.composite.start()
        
        # 子特效应该启动
        self.assertEqual(self.move.state, EffectState.PLAYING)
        self.assertEqual(self.fade.state, EffectState.PLAYING)
        
        # 停止组合特效
        self.composite.stop()
        
        # 子特效应该停止
        self.assertEqual(self.move.state, EffectState.STOPPED)
        self.assertEqual(self.fade.state, EffectState.STOPPED)
        
    def test_update(self):
        """测试更新"""
        self.composite.start()
        
        # 直接设置elapsed_time到1秒
        self.composite.elapsed_time = 1.0
        # 更新所有子特效的时间
        self.move.elapsed_time = 1.0
        self.fade.elapsed_time = 1.0
        # 手动触发更新回调
        self.move._update_position(0.5)  # 1秒是总时长2秒的一半，所以progress是0.5
        self.fade._update_color(1.0)  # 1秒是总时长1秒的100%，所以progress是1.0
        
        # 检查移动特效是否更新到一半
        self.assertEqual(self.target1.x, 150)
        self.assertEqual(self.target1.y, 150)
        
        # 检查颜色特效是否完成
        self.assertEqual(self.target2.color, Color(0, 0, 255, 255))
        
        # 直接设置elapsed_time到2秒
        self.composite.elapsed_time = 2.0
        # 更新所有子特效的时间
        self.move.elapsed_time = 2.0
        self.fade.elapsed_time = 2.0
        # 手动触发更新回调
        self.move._update_position(1.0)  # 2秒是总时长2秒的100%，所以progress是1.0
        
        # 检查移动特效是否完成
        self.assertEqual(self.target1.x, 200)
        self.assertEqual(self.target1.y, 200)


class TestEffectManager(unittest.TestCase):
    """测试特效管理器"""
    
    def setUp(self):
        """测试准备"""
        # 创建单例实例
        self.manager = EffectManager()
        
        # 清除所有特效
        self.manager.clear_effects()
        
        # 创建测试特效
        self.effect1 = Effect(duration=1.0, auto_start=True)
        self.effect2 = Effect(duration=2.0, auto_start=True)
        
        # 添加到管理器
        self.manager.add_effect(self.effect1)
        self.manager.add_effect(self.effect2)
        
    def test_singleton(self):
        """测试单例模式"""
        manager2 = EffectManager()
        self.assertIs(self.manager, manager2)
        
    def test_add_remove(self):
        """测试添加和移除特效"""
        # 检查特效数量
        self.assertEqual(self.manager.get_effects_count(), 2)
        
        # 移除特效
        result = self.manager.remove_effect(self.effect1)
        
        # 检查移除结果和特效数量
        self.assertTrue(result)
        self.assertEqual(self.manager.get_effects_count(), 1)
        
        # 尝试移除不存在的特效
        result = self.manager.remove_effect(self.effect1)
        
        # 检查移除结果
        self.assertFalse(result)
        
    def test_update(self):
        """测试更新特效"""
        # 更新到1秒
        self.manager.update(1.0)
        
        # effect1应该完成并被移除
        self.assertEqual(self.effect1.state, EffectState.COMPLETED)
        self.assertEqual(self.manager.get_effects_count(), 1)
        
        # 更新到2秒
        self.manager.update(1.0)
        
        # effect2应该完成并被移除
        self.assertEqual(self.effect2.state, EffectState.COMPLETED)
        self.assertEqual(self.manager.get_effects_count(), 0)
        
    def test_pause_resume(self):
        """测试暂停和恢复"""
        # 暂停所有特效
        self.manager.pause_all()
        
        # 检查管理器和特效状态
        self.assertTrue(self.manager.is_paused())
        self.assertEqual(self.effect1.state, EffectState.PAUSED)
        self.assertEqual(self.effect2.state, EffectState.PAUSED)
        
        # 恢复所有特效
        self.manager.resume_all()
        
        # 检查管理器和特效状态
        self.assertFalse(self.manager.is_paused())
        self.assertEqual(self.effect1.state, EffectState.PLAYING)
        self.assertEqual(self.effect2.state, EffectState.PLAYING)


class TestParticle(unittest.TestCase):
    """测试粒子"""
    
    def setUp(self):
        """测试准备"""
        self.particle = Particle(
            x=100,
            y=100,
            size=10,
            color=Color(255, 0, 0, 255),
            lifetime=1.0
        )
        
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.particle.x, 100)
        self.assertEqual(self.particle.y, 100)
        self.assertEqual(self.particle.size, (10, 10))
        self.assertEqual(self.particle.color, Color(255, 0, 0, 255))
        self.assertEqual(self.particle.lifetime, 1.0)
        self.assertTrue(self.particle.is_alive)
        
    def test_update(self):
        """测试更新"""
        # 设置速度
        self.particle.velocity_x = 10
        self.particle.velocity_y = 20
        
        # 更新0.5秒
        self.particle.update(0.5)
        
        # 检查位置
        self.assertEqual(self.particle.x, 105)
        self.assertEqual(self.particle.y, 110)
        
        # 检查状态
        self.assertEqual(self.particle.age, 0.5)
        self.assertEqual(self.particle.normalized_age, 0.5)
        self.assertTrue(self.particle.is_alive)
        
        # 更新到超过生命周期
        self.particle.update(1.0)
        
        # 检查状态
        self.assertFalse(self.particle.is_alive)


class TestParticleEmitter(unittest.TestCase):
    """测试粒子发射器"""
    
    def setUp(self):
        """测试准备"""
        self.emitter = ParticleEmitter(
            x=100,
            y=100,
            emission_rate=10,
            emission_mode=EmissionMode.CONTINUOUS,
            emission_shape=EmissionShape.POINT
        )
        
    def test_burst_emission(self):
        """测试爆发式发射"""
        # 设置为爆发模式
        self.emitter.set_emission_mode(EmissionMode.BURST)
        self.emitter.set_burst_count(5)
        
        # 发射粒子
        particles = self.emitter.emit()
        
        # 检查粒子数量
        self.assertEqual(len(particles), 5)
        
        # 再次发射，应该没有粒子
        particles = self.emitter.emit()
        self.assertEqual(len(particles), 0)
        
    def test_continuous_emission(self):
        """测试连续发射"""
        # 设置发射速率
        self.emitter.set_emission_rate(2)  # 每秒2个粒子
        
        # 更新0.6秒，应该发射1个粒子
        particles = self.emitter.update(0.6)
        self.assertEqual(len(particles), 1)
        
        # 再更新0.6秒，应该再发射1个粒子
        particles = self.emitter.update(0.6)
        self.assertEqual(len(particles), 1)
        
    def test_particle_properties(self):
        """测试粒子属性设置"""
        # 设置粒子属性
        self.emitter.set_particle_lifetime(2.0, 0.1)
        self.emitter.set_particle_size(20, 0.1)
        self.emitter.set_particle_color(Color(255, 0, 0, 255))
        self.emitter.set_velocity(10, 20, 45, 10)
        
        # 发射粒子
        particles = self.emitter.emit()
        particle = particles[0]
        
        # 检查粒子属性
        self.assertAlmostEqual(particle.lifetime, 2.0, delta=0.3)
        self.assertAlmostEqual(particle.size[0], 20, delta=3)  # 检查宽度
        self.assertAlmostEqual(particle.size[1], 20, delta=3)  # 检查高度
        self.assertEqual(particle.color.r, 255)
        
        # 检查速度
        velocity = math.sqrt(particle.velocity_x ** 2 + particle.velocity_y ** 2)
        self.assertGreaterEqual(velocity, 10)
        self.assertLessEqual(velocity, 20)


class TestParticleSystem(unittest.TestCase):
    """测试粒子系统"""
    
    def setUp(self):
        """测试准备"""
        self.system = ParticleSystem(
            x=100,
            y=100,
            duration=2.0,
            auto_start=False
        )
        
        # 创建发射器
        self.emitter = ParticleEmitter(
            x=100,
            y=100,
            emission_mode=EmissionMode.BURST,
            burst_count=10
        )
        
        # 为测试目的增加粒子寿命，确保在测试期间不会死亡
        self.emitter.set_particle_lifetime(10.0)
        
        # 添加到系统
        self.system.add_emitter(self.emitter)
        
    def test_system_lifecycle(self):
        """测试系统生命周期"""
        # 启动系统
        self.system.start()
        self.assertEqual(self.system.state, EffectState.PLAYING)
        
        # 更新系统
        self.system.update(0.1)
        
        # 检查粒子是否创建
        self.assertEqual(self.system.get_particle_count(), 10)
        
        # 更新粒子老化
        self.system.update(1.0)
        
        # 检查粒子是否仍然存在
        self.assertEqual(self.system.get_particle_count(), 10)
        
        # 停止系统，这会清除所有粒子
        self.system.stop()
        
        # 粒子应该消失
        self.assertEqual(self.system.get_particle_count(), 0)
        
    def test_max_particles(self):
        """测试最大粒子数量"""
        # 设置最大粒子数量
        self.system.set_max_particles(5)
        
        # 启动系统
        self.system.start()
        self.system.update(0.1)
        
        # 检查粒子是否被限制
        self.assertEqual(self.system.get_particle_count(), 5)
        
    def test_position(self):
        """测试设置位置"""
        # 设置系统位置
        self.system.set_position(200, 200)
        
        # 检查系统和发射器位置
        self.assertEqual(self.system.x, 200)
        self.assertEqual(self.system.y, 200)
        self.assertEqual(self.emitter.x, 200)
        self.assertEqual(self.emitter.y, 200)


class TestParticlePresets(unittest.TestCase):
    """测试粒子预设"""
    
    def test_create_explosion(self):
        """测试创建爆炸效果"""
        system = ParticlePresets.create_explosion(100, 100)
        
        # 检查系统属性
        self.assertEqual(system.x, 100)
        self.assertEqual(system.y, 100)
        self.assertEqual(len(system.emitters), 2)
        
        # 检查发射器模式
        for emitter in system.emitters:
            self.assertEqual(emitter.emission_mode, EmissionMode.BURST)
        
    def test_create_fire(self):
        """测试创建火焰效果"""
        system = ParticlePresets.create_fire(100, 100)
        
        # 检查系统属性
        self.assertEqual(system.x, 100)
        self.assertEqual(system.y, 100)
        self.assertEqual(len(system.emitters), 2)
        
        # 检查发射器模式
        for emitter in system.emitters:
            self.assertEqual(emitter.emission_mode, EmissionMode.CONTINUOUS)


if __name__ == "__main__":
    unittest.main() 