"""
---------------------------------------------------------------
File name:                  effects_example.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                特效系统使用示例
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import sys
import time
import math
import random
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen

# 引入状态监控系统
sys.path.append('../..')  # 添加项目根目录到路径

from status.renderer.pyqt_renderer import PyQtRenderer
from status.renderer.sprite import Sprite
from status.renderer.effects import (
    Effect, EffectState, ColorEffect, ColorFade, Blink,
    TransformEffect, Move, Scale, Rotate, CompositeEffect, EffectManager
)
from status.renderer.particle import (
    ParticleSystem, ParticlePresets, ParticleEmitter, EmissionMode, EmissionShape
)
from status.renderer.renderer_base import Color
from status.renderer.drawable import Drawable


class Ball(Drawable):
    """示例可绘制对象：球"""
    
    def __init__(self, x, y, radius=20, color=None):
        super().__init__(x, y)
        self.radius = radius
        self.color = color or Color(255, 0, 0, 255)
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.rotation = 0
        
    def draw(self, renderer):
        """绘制球"""
        # 保存当前状态
        renderer.save()
        
        # 应用变换
        renderer.translate(self.x, self.y)
        renderer.rotate(self.rotation)
        renderer.scale(self.scale_x, self.scale_y)
        
        # 绘制圆形
        renderer.set_color(self.color)
        renderer.fill_circle(0, 0, self.radius)
        
        # 恢复状态
        renderer.restore()


class EffectsDemo(QMainWindow):
    """特效系统演示"""
    
    def __init__(self):
        super().__init__()
        
        # 设置窗口
        self.setWindowTitle("特效系统演示")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央窗口部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建垂直布局
        main_layout = QVBoxLayout(self.central_widget)
        
        # 创建画布
        self.canvas = Canvas(self)
        main_layout.addWidget(self.canvas)
        
        # 创建按钮布局
        btn_layout = QHBoxLayout()
        main_layout.addLayout(btn_layout)
        
        # 创建按钮
        self.btn_color_fade = QPushButton("颜色渐变")
        self.btn_blink = QPushButton("闪烁效果")
        self.btn_move = QPushButton("移动效果")
        self.btn_scale = QPushButton("缩放效果")
        self.btn_rotate = QPushButton("旋转效果")
        self.btn_composite = QPushButton("组合效果")
        self.btn_explosion = QPushButton("爆炸粒子")
        self.btn_fire = QPushButton("火焰粒子")
        self.btn_sparkle = QPushButton("闪光粒子")
        self.btn_water = QPushButton("水花粒子")
        
        # 添加按钮到布局
        btn_layout.addWidget(self.btn_color_fade)
        btn_layout.addWidget(self.btn_blink)
        btn_layout.addWidget(self.btn_move)
        btn_layout.addWidget(self.btn_scale)
        btn_layout.addWidget(self.btn_rotate)
        btn_layout.addWidget(self.btn_composite)
        btn_layout.addWidget(self.btn_explosion)
        btn_layout.addWidget(self.btn_fire)
        btn_layout.addWidget(self.btn_sparkle)
        btn_layout.addWidget(self.btn_water)
        
        # 连接信号和槽
        self.btn_color_fade.clicked.connect(self.canvas.show_color_fade)
        self.btn_blink.clicked.connect(self.canvas.show_blink)
        self.btn_move.clicked.connect(self.canvas.show_move)
        self.btn_scale.clicked.connect(self.canvas.show_scale)
        self.btn_rotate.clicked.connect(self.canvas.show_rotate)
        self.btn_composite.clicked.connect(self.canvas.show_composite)
        self.btn_explosion.clicked.connect(self.canvas.show_explosion)
        self.btn_fire.clicked.connect(self.canvas.show_fire)
        self.btn_sparkle.clicked.connect(self.canvas.show_sparkle)
        self.btn_water.clicked.connect(self.canvas.show_water)
        
        # 创建状态栏
        self.statusBar().showMessage("准备就绪")


class Canvas(QWidget):
    """绘图画布"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 500)
        
        # 创建PyQt渲染器
        self.renderer = PyQtRenderer()
        
        # 创建绘制对象
        self.ball = Ball(400, 250, 40)
        
        # 创建粒子系统列表
        self.particle_systems = []
        
        # 获取特效管理器
        self.effect_manager = EffectManager()
        
        # 创建定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_scene)
        self.timer.start(16)  # 约60FPS
        
        # 跟踪上一帧时间
        self.last_time = time.time()
        
    def paintEvent(self, event):
        """绘制事件"""
        # 设置渲染器
        self.renderer.begin(self)
        
        # 绘制背景
        self.renderer.set_color(Color(30, 30, 30, 255))
        self.renderer.fill_rect(0, 0, self.width(), self.height())
        
        # 绘制网格
        self.renderer.set_color(Color(50, 50, 50, 255))
        for x in range(0, self.width(), 50):
            self.renderer.draw_line(x, 0, x, self.height())
        for y in range(0, self.height(), 50):
            self.renderer.draw_line(0, y, self.width(), y)
        
        # 绘制球
        self.ball.draw(self.renderer)
        
        # 绘制粒子系统
        for system in self.particle_systems:
            system.draw(self.renderer)
        
        # 结束渲染
        self.renderer.end()
        
    def update_scene(self):
        """更新场景"""
        current_time = time.time()
        delta_time = current_time - self.last_time
        self.last_time = current_time
        
        # 更新特效管理器
        self.effect_manager.update(delta_time)
        
        # 更新粒子系统
        active_systems = []
        for system in self.particle_systems:
            system.update(delta_time)
            if system.state != EffectState.COMPLETED and system.state != EffectState.STOPPED:
                active_systems.append(system)
                
        self.particle_systems = active_systems
        
        # 请求重绘
        self.update()
        
        # 更新状态栏
        effects_count = self.effect_manager.get_effects_count()
        particle_count = sum(system.get_particle_count() for system in self.particle_systems)
        self.parent().statusBar().showMessage(f"当前特效: {effects_count} | 粒子数: {particle_count}")
    
    def clear_effects(self):
        """清除所有特效"""
        self.effect_manager.clear_effects()
        self.ball.x = 400
        self.ball.y = 250
        self.ball.scale_x = 1.0
        self.ball.scale_y = 1.0
        self.ball.rotation = 0
        self.ball.color = Color(255, 0, 0, 255)
        
    def show_color_fade(self):
        """显示颜色渐变特效"""
        self.clear_effects()
        
        # 创建颜色渐变特效
        fade = ColorFade(
            target=self.ball,
            from_color=Color(255, 0, 0, 255),
            to_color=Color(0, 0, 255, 255),
            duration=2.0,
            auto_start=True
        )
        
        # 添加特效到管理器
        self.effect_manager.add_effect(fade)
        
    def show_blink(self):
        """显示闪烁特效"""
        self.clear_effects()
        
        # 创建闪烁特效
        blink = Blink(
            target=self.ball,
            blink_color=Color(255, 255, 255, 255),
            frequency=2.0,
            duration=3.0,
            auto_start=True
        )
        
        # 添加特效到管理器
        self.effect_manager.add_effect(blink)
        
    def show_move(self):
        """显示移动特效"""
        self.clear_effects()
        
        # 创建移动特效
        move = Move(
            target=self.ball,
            end_x=600,
            end_y=350,
            duration=2.0,
            auto_start=True
        )
        
        # 添加特效到管理器
        self.effect_manager.add_effect(move)
        
    def show_scale(self):
        """显示缩放特效"""
        self.clear_effects()
        
        # 创建缩放特效
        scale = Scale(
            target=self.ball,
            end_scale_x=2.0,
            end_scale_y=0.5,
            duration=1.5,
            auto_start=True
        )
        
        # 添加特效到管理器
        self.effect_manager.add_effect(scale)
        
    def show_rotate(self):
        """显示旋转特效"""
        self.clear_effects()
        
        # 创建旋转特效
        rotate = Rotate(
            target=self.ball,
            end_rotation=720,  # 两圈
            duration=3.0,
            auto_start=True
        )
        
        # 添加特效到管理器
        self.effect_manager.add_effect(rotate)
        
    def show_composite(self):
        """显示组合特效"""
        self.clear_effects()
        
        # 创建多个特效
        move = Move(
            target=self.ball,
            end_x=600,
            end_y=350,
            duration=3.0,
            auto_start=False
        )
        
        fade = ColorFade(
            target=self.ball,
            from_color=Color(255, 0, 0, 255),
            to_color=Color(0, 255, 0, 255),
            duration=1.5,
            auto_start=False
        )
        
        scale = Scale(
            target=self.ball,
            end_scale_x=2.0,
            end_scale_y=2.0,
            duration=2.0,
            auto_start=False
        )
        
        rotate = Rotate(
            target=self.ball,
            end_rotation=360,
            duration=3.0,
            auto_start=False
        )
        
        # 创建组合特效
        composite = CompositeEffect(
            effects=[move, fade, scale, rotate],
            auto_start=True
        )
        
        # 添加组合特效到管理器
        self.effect_manager.add_effect(composite)
    
    def show_explosion(self):
        """显示爆炸粒子效果"""
        # 创建爆炸粒子系统
        explosion = ParticlePresets.create_explosion(
            x=self.ball.x,
            y=self.ball.y,
            color=self.ball.color,
            scale=1.0
        )
        
        # 添加到粒子系统列表
        self.particle_systems.append(explosion)
        
        # 启动粒子系统
        explosion.start()
        
    def show_fire(self):
        """显示火焰粒子效果"""
        # 创建火焰粒子系统
        fire = ParticlePresets.create_fire(
            x=self.ball.x,
            y=self.ball.y + 20,
            width=50.0,
            height=80.0,
            scale=1.0
        )
        
        # 添加到粒子系统列表
        self.particle_systems.append(fire)
        
        # 启动粒子系统
        fire.start()
        
    def show_sparkle(self):
        """显示闪光粒子效果"""
        # 创建闪光粒子系统
        sparkle = ParticlePresets.create_sparkle(
            x=self.ball.x,
            y=self.ball.y,
            color=Color(255, 255, 150, 255),
            scale=1.2
        )
        
        # 添加到粒子系统列表
        self.particle_systems.append(sparkle)
        
        # 启动粒子系统
        sparkle.start()
        
    def show_water(self):
        """显示水花粒子效果"""
        # 创建水花粒子系统
        splash = ParticlePresets.create_water_splash(
            x=self.ball.x,
            y=self.ball.y,
            color=Color(100, 150, 255, 200),
            scale=1.0
        )
        
        # 添加到粒子系统列表
        self.particle_systems.append(splash)
        
        # 启动粒子系统
        splash.start()
        
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        # 在鼠标位置创建爆炸特效
        if event.button() == Qt.LeftButton:
            explosion = ParticlePresets.create_explosion(
                x=event.x(),
                y=event.y(),
                color=Color(random.randint(150, 255), random.randint(100, 200), random.randint(0, 100), 255),
                scale=0.8 + random.random() * 0.4
            )
            self.particle_systems.append(explosion)
            explosion.start()
        elif event.button() == Qt.RightButton:
            sparkle = ParticlePresets.create_sparkle(
                x=event.x(),
                y=event.y(),
                color=Color(random.randint(200, 255), random.randint(200, 255), random.randint(100, 200), 255),
                scale=0.8 + random.random() * 0.4
            )
            self.particle_systems.append(sparkle)
            sparkle.start()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    demo = EffectsDemo()
    demo.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 