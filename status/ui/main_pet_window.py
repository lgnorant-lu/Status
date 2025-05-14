"""
---------------------------------------------------------------
File name:                  main_pet_window.py
Author:                     Ignorant-lu
Date created:               2025/04/16
Description:                桌宠主窗口，负责显示桌宠动画并处理窗口相关事件
----------------------------------------------------------------

Changed history:            
                            2025/04/16: 初始创建;
                            2025/04/17: 从PyQt6迁移到PySide6;
                            2025/05/20: 添加平滑拖拽效果;
                            2025/05/13: 添加屏幕边界检测和边缘吸附功能;
                            2025/05/13: 修复精确模式闪动和高速滑动边界问题;
                            2025/05/13: 优化拖拽精度并通过TDD测试;
                            2025/05/13: 修复拖动功能有时不响应的问题;
----
"""

import logging
import sys
from typing import Optional, Tuple

from PySide6.QtWidgets import QMainWindow, QWidget, QApplication, QVBoxLayout, QLabel
from PySide6.QtGui import (
    QPixmap, QPainter, QMouseEvent, QImage, QPaintEvent, QCursor,
    QResizeEvent, QMoveEvent, Qt, QGuiApplication, QScreen
)
from PySide6.QtCore import QPoint, QSize, QRect, QTimer, Signal, Slot, QObject, QTime, QElapsedTimer

from status.core.events import WindowPositionChangedEvent
from status.core.event_system import EventSystem, EventType

logger = logging.getLogger(__name__)

# 拖拽平滑系数参数
DRAG_SMOOTHING_FACTOR = 0.5    # 基础平滑系数 (降低以获得更平滑的体验)
DRAG_MAX_SMOOTHING = 0.85      # 最大平滑系数(接近1:1跟随) - 精确模式使用
DRAG_MIN_SMOOTHING = 0.3       # 最小平滑系数(最平滑) - 平滑模式使用
DRAG_SPEED_THRESHOLD = 4.0     # 速度阈值，超过此值使用最大平滑系数
POSITION_CLOSE_THRESHOLD = 2   # 位置接近阈值（像素）
UPDATE_INTERVAL = 16           # 更新间隔(ms)，约60fps
PRECISE_UPDATE_INTERVAL = 8    # 精确模式下的更新间隔(ms)，更高刷新率
MAX_SPEED_HISTORY = 3          # 速度历史记录最大长度
DRAG_THRESHOLD = 3             # 鼠标移动多少像素才被视为拖动开始

# 屏幕边界限制参数
SCREEN_EDGE_MARGIN = 20        # 窗口必须在屏幕内保留的最小边距（像素）
EDGE_SNAP_DISTANCE = 15        # 距离屏幕边缘多少像素时吸附到边缘
MINIMUM_VISIBLE_AREA = 0.3     # 窗口可见区域的最小百分比（0.3 = 30%）
STRICT_BOUNDARY_CHECK = True   # 严格边界检查，确保始终在屏幕内

class MainPetWindow(QMainWindow):
    """桌宠主窗口，负责显示桌宠动画并处理窗口相关行为"""
    
    # 信号
    clicked = Signal(QPoint)         # 点击信号，参数为点击位置
    double_clicked = Signal(QPoint)  # 双击信号，参数为点击位置
    dragged = Signal(QPoint)         # 拖拽信号，参数为拖拽位置
    dropped = Signal(QPoint)         # 放下信号，参数为放下位置
    mouse_moved = Signal(QPoint)     # 鼠标移动信号，参数为鼠标位置
    size_changed = Signal(QSize)     # 大小改变信号，参数为新大小
    position_changed = Signal(QPoint)  # 位置改变信号，参数为新位置
    
    def __init__(self, parent=None):
        """初始化主窗口"""
        super().__init__(parent)
        
        self.setWindowTitle("Status Pet")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |      # 无边框
            Qt.WindowType.Tool |                    # 工具窗口（不在任务栏显示）
            Qt.WindowType.WindowStaysOnTopHint     # 保持在最前
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # 透明背景
        
        # 创建一个中央部件来显示图像
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        
        # 布局
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)  # 无边距
        
        # 图像标签
        self.image_label = QLabel(self.central_widget)
        self.image_label.setScaledContents(True)  # 图像自动缩放
        self.main_layout.addWidget(self.image_label)
        
        # 初始化变量
        self.image = None  # 当前显示的图像
        self.is_dragging = False  # 是否正在拖拽
        self.drag_start_pos = QPoint()  # 拖拽开始位置
        self.window_start_pos = QPoint()  # 窗口开始位置
        self.drag_activated = False  # 是否已激活拖动（超过阈值）
        
        # 平滑拖拽相关
        self.target_pos = QPoint()  # 目标位置
        self.current_pos = QPoint()  # 当前位置
        self.smoothing_factor = DRAG_SMOOTHING_FACTOR  # 动态平滑系数
        self.smoothing_timer = QTimer(self)  # 平滑定时器
        self.smoothing_timer.setInterval(UPDATE_INTERVAL)
        self.smoothing_timer.timeout.connect(self._update_position)
        
        # 拖动速度检测
        self.last_mouse_pos = QPoint()
        self.last_mouse_time = QElapsedTimer()
        self.mouse_speed = 0.0  # 像素/毫秒
        self.speed_history = []  # 用于平滑速度计算
        
        # 拖动模式
        self.drag_mode = "smart"  # "smart", "precise", "smooth"
        
        # 初始化时获取屏幕大小
        self._get_screen_geometry()
        
        # 看门狗定时器，确保拖动过程不会卡住
        self.watchdog_timer = QTimer(self)
        self.watchdog_timer.setInterval(100)  # 100ms检查一次
        self.watchdog_timer.timeout.connect(self._check_drag_state)
        
        logger.debug("MainPetWindow初始化完成")
    
    def _check_drag_state(self):
        """检查拖动状态，确保没有卡在拖动状态"""
        if self.is_dragging:
            # 检查鼠标是否仍然按下
            if not (QApplication.mouseButtons() & Qt.MouseButton.LeftButton):
                logger.debug("检测到鼠标按钮已释放但拖动状态未重置，强制重置")
                self.is_dragging = False
                self.drag_activated = False
                self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
                self.watchdog_timer.stop()
                
                # 确保平滑移动完成
                self._check_smooth_complete()
    
    def _get_screen_geometry(self) -> QRect:
        """获取当前屏幕几何信息
        
        Returns:
            QRect: 屏幕几何信息
        """
        # 获取窗口所在屏幕
        screen = QGuiApplication.screenAt(self.pos()) or QGuiApplication.primaryScreen()
        return screen.availableGeometry()
    
    def set_image(self, image) -> None:
        """设置要显示的图像
        
        Args:
            image: QImage、QPixmap或文件路径
        """
        logger.debug(f"MainPetWindow.set_image called with: {type(image)}, {image}")
        pixmap = None
        
        # 转换各种类型到QPixmap
        if isinstance(image, QPixmap):
            pixmap = image
        elif isinstance(image, QImage):
            pixmap = QPixmap.fromImage(image)
        elif isinstance(image, str):
            # 尝试从文件加载
            pixmap = QPixmap(image)
            if pixmap.isNull():
                logger.error(f"无法加载图像: {image}")
                return
        else:
            logger.error(f"不支持的图像类型: {type(image)}")
            return
        
        # 更新图像
        self.image = pixmap
        self.image_label.setPixmap(pixmap)
        
        # 调整窗口大小以适应图像
        self.resize_to_image()
        
        # 更新
        self.update()
    
    def resize_to_image(self) -> None:
        """调整窗口大小以适应当前图像"""
        if self.image and not self.image.isNull():
            # 设置窗口大小为图像大小
            self.resize(self.image.size())
            logger.debug(f"窗口大小已调整为: {self.image.size()}")
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """鼠标按下事件处理
        
        Args:
            event: 鼠标事件
        """
        if event.button() == Qt.MouseButton.LeftButton:
            # 记录拖拽开始位置
            self.is_dragging = True
            self.drag_activated = False  # 重置激活状态，等待移动超过阈值
            self.drag_start_pos = event.position().toPoint()
            self.window_start_pos = self.pos()
            
            # 初始化平滑拖拽位置
            self.current_pos = self.pos()
            self.target_pos = self.pos()
            
            # 重置速度检测
            self.last_mouse_pos = event.position().toPoint()
            self.last_mouse_time.start()
            self.mouse_speed = 0.0
            self.speed_history = []
            
            # 根据拖动模式设置平滑系数
            self._update_smoothing_factor()
            
            # 根据拖动模式调整更新间隔
            self._update_timer_interval()
            
            # 发送点击信号
            self.clicked.emit(event.position().toPoint())
            
            # 设置鼠标形状为抓取
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            
            # 启动看门狗定时器
            self.watchdog_timer.start()
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """鼠标移动事件处理
        
        Args:
            event: 鼠标事件
        """
        current_mouse_pos = event.position().toPoint()
        
        # 发出鼠标移动信号，用于hover交互
        # 注意：仅在非拖动状态下才发送mouse_moved信号，避免拖动和hover冲突
        if not self.is_dragging:
            self.mouse_moved.emit(current_mouse_pos)
            
        if self.is_dragging:
            # 检查是否超过拖动阈值
            if not self.drag_activated:
                delta_move = (current_mouse_pos - self.drag_start_pos)
                move_distance = (delta_move.x() ** 2 + delta_move.y() ** 2) ** 0.5
                
                if move_distance >= DRAG_THRESHOLD:
                    self.drag_activated = True
                    logger.debug(f"拖动已激活，移动距离: {move_distance}像素")
            
            # 只有在拖动激活后才处理移动
            if self.drag_activated:
                # 计算鼠标移动速度
                elapsed = self.last_mouse_time.elapsed()
                if elapsed > 0:  # 避免除以零
                    # 计算当前速度（像素/毫秒）
                    distance = ((current_mouse_pos - self.last_mouse_pos).x() ** 2 + 
                               (current_mouse_pos - self.last_mouse_pos).y() ** 2) ** 0.5
                    current_speed = distance / elapsed
                    
                    # 记录历史速度用于平滑计算
                    self.speed_history.append(current_speed)
                    if len(self.speed_history) > MAX_SPEED_HISTORY:
                        self.speed_history.pop(0)
                    
                    # 计算平均速度
                    self.mouse_speed = sum(self.speed_history) / len(self.speed_history)
                    
                    # 根据拖动模式和速度动态调整平滑系数
                    self._update_smoothing_factor()
                
                # 更新最后的鼠标位置和时间
                self.last_mouse_pos = current_mouse_pos
                self.last_mouse_time.restart()
                
                # 计算拖拽位置
                delta = current_mouse_pos - self.drag_start_pos
                new_pos = self.window_start_pos + delta
                
                # 限制位置在屏幕边界内
                screen_geometry = self._get_screen_geometry()
                constrained_pos = self._constrain_to_screen_boundary(new_pos, screen_geometry)
                
                # 更新目标位置
                self.target_pos = constrained_pos
                
                # 精确模式下，考虑直接设置部分位置差，减少延迟感
                if self.drag_mode == "precise" and self.mouse_speed > DRAG_SPEED_THRESHOLD * 2:
                    # 计算当前位置和目标位置之间的直接差值
                    diff_x = self.target_pos.x() - self.current_pos.x()
                    diff_y = self.target_pos.y() - self.current_pos.y()
                    
                    # 如果差值很大，让位置"追赶"过去，以减少跟踪延迟
                    if abs(diff_x) > 50 or abs(diff_y) > 50:
                        # 直接"跳跃"到接近目标位置的地方
                        jump_factor = 0.7  # 直接跳跃70%的距离
                        self.current_pos = QPoint(
                            int(self.current_pos.x() + diff_x * jump_factor),
                            int(self.current_pos.y() + diff_y * jump_factor)
                        )
                
                # 如果定时器没有启动，则启动它
                if not self.smoothing_timer.isActive():
                    logger.debug("启动平滑定时器")
                    self.smoothing_timer.start()
                
                # 发送拖拽信号
                self.dragged.emit(constrained_pos)
        
        super().mouseMoveEvent(event)
    
    def _update_smoothing_factor(self):
        """根据拖动模式和速度更新平滑系数"""
        if self.drag_mode == "precise":
            self.smoothing_factor = DRAG_MAX_SMOOTHING
        elif self.drag_mode == "smooth":
            self.smoothing_factor = DRAG_MIN_SMOOTHING
        else:  # "smart" mode
            # 调整速度与平滑度的关系，使用二次方曲线提供更自然的渐进效果
            speed_factor = min(1.0, (self.mouse_speed / DRAG_SPEED_THRESHOLD) ** 2)
            self.smoothing_factor = DRAG_MIN_SMOOTHING + speed_factor * (DRAG_MAX_SMOOTHING - DRAG_MIN_SMOOTHING)
    
    def _update_timer_interval(self):
        """根据拖动模式更新定时器间隔"""
        if self.drag_mode == "precise":
            self.smoothing_timer.setInterval(PRECISE_UPDATE_INTERVAL)
        else:
            self.smoothing_timer.setInterval(UPDATE_INTERVAL)
    
    def _constrain_to_screen_boundary(self, pos: QPoint, screen_geometry: QRect) -> QPoint:
        """限制位置在屏幕边界内，并实现边缘吸附效果
        
        Args:
            pos: 目标位置
            screen_geometry: 屏幕几何信息
            
        Returns:
            QPoint: 调整后的位置
        """
        # 获取窗口大小
        window_width = self.width()
        window_height = self.height()
        
        # 计算最小可见区域尺寸
        min_visible_width = int(window_width * MINIMUM_VISIBLE_AREA)
        min_visible_height = int(window_height * MINIMUM_VISIBLE_AREA)
        
        # 确保最小可见区域不小于一个合理的值
        min_visible_width = max(min_visible_width, 50)
        min_visible_height = max(min_visible_height, 50)
        
        # 屏幕边界
        screen_left = screen_geometry.left()
        screen_top = screen_geometry.top()
        screen_right = screen_geometry.right()
        screen_bottom = screen_geometry.bottom()
        
        # 调整后的位置
        adjusted_x = pos.x()
        adjusted_y = pos.y()
        
        # 限制左边界，保证一部分窗口可见
        if adjusted_x < screen_left - window_width + min_visible_width:
            adjusted_x = screen_left - window_width + min_visible_width
        
        # 限制上边界，保证一部分窗口可见
        if adjusted_y < screen_top - window_height + min_visible_height:
            adjusted_y = screen_top - window_height + min_visible_height
        
        # 限制右边界，保证一部分窗口可见
        if adjusted_x > screen_right - min_visible_width:
            adjusted_x = screen_right - min_visible_width
        
        # 限制下边界，保证一部分窗口可见
        if adjusted_y > screen_bottom - min_visible_height:
            adjusted_y = screen_bottom - min_visible_height
        
        # 边缘吸附效果
        # 左边缘吸附
        if abs(adjusted_x - screen_left) < EDGE_SNAP_DISTANCE:
            adjusted_x = screen_left
        
        # 右边缘吸附（窗口右边缘对齐屏幕右边缘）
        if abs(adjusted_x + window_width - screen_right) < EDGE_SNAP_DISTANCE:
            adjusted_x = screen_right - window_width
        
        # 上边缘吸附
        if abs(adjusted_y - screen_top) < EDGE_SNAP_DISTANCE:
            adjusted_y = screen_top
        
        # 下边缘吸附（窗口下边缘对齐屏幕下边缘）
        if abs(adjusted_y + window_height - screen_bottom) < EDGE_SNAP_DISTANCE:
            adjusted_y = screen_bottom - window_height
        
        return QPoint(adjusted_x, adjusted_y)
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """鼠标释放事件处理
        
        Args:
            event: 鼠标事件
        """
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.is_dragging = False
            self.drag_activated = False
            
            # 停止看门狗定时器
            self.watchdog_timer.stop()
            
            # 计算释放位置
            delta = event.position().toPoint() - self.drag_start_pos
            final_pos = self.window_start_pos + delta
            
            # 限制在屏幕边界内
            screen_geometry = self._get_screen_geometry()
            final_pos = self._constrain_to_screen_boundary(final_pos, screen_geometry)
            
            self.target_pos = final_pos
            
            # 调整释放后的平滑系数，使其有一个舒适的"落地"效果
            self.smoothing_factor = DRAG_SMOOTHING_FACTOR
            
            # 恢复标准更新间隔
            self.smoothing_timer.setInterval(UPDATE_INTERVAL)
            
            # 在释放后让平滑定时器继续运行一小段时间
            QTimer.singleShot(300, self._check_smooth_complete)
            
            # 重置鼠标形状
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            
            # 发送放下信号
            self.dropped.emit(event.position().toPoint())
            
            logger.debug("鼠标释放，拖动结束")
        
        super().mouseReleaseEvent(event)
    
    def _update_position(self) -> None:
        """更新窗口位置（平滑插值）"""
        # 如果位置更新卡住，强制检查拖动状态
        self._check_drag_state()
        
        if not self.is_dragging and self._is_position_close():
            # 如果拖拽结束且位置接近目标，直接设置到目标位置并停止定时器
            self.move(self.target_pos)
            self.current_pos = self.target_pos
            self.smoothing_timer.stop()
            logger.debug("平滑移动完成，定时器停止")
            return
        
        # 计算插值后的新位置
        new_x = self.current_pos.x() + (self.target_pos.x() - self.current_pos.x()) * self.smoothing_factor
        new_y = self.current_pos.y() + (self.target_pos.y() - self.current_pos.y()) * self.smoothing_factor
        
        # 更新当前位置
        self.current_pos = QPoint(int(new_x), int(new_y))
        
        # 确保当前位置仍然在屏幕边界内
        # 这是修复高速滑动问题的关键，确保每次位置更新都检查边界
        if STRICT_BOUNDARY_CHECK:
            screen_geometry = self._get_screen_geometry()
            self.current_pos = self._constrain_to_screen_boundary(self.current_pos, screen_geometry)
        
        # 移动窗口
        self.move(self.current_pos)
    
    def _is_position_close(self) -> bool:
        """检查当前位置是否接近目标位置"""
        dx = abs(self.current_pos.x() - self.target_pos.x())
        dy = abs(self.current_pos.y() - self.target_pos.y())
        return dx <= POSITION_CLOSE_THRESHOLD and dy <= POSITION_CLOSE_THRESHOLD
    
    def _check_smooth_complete(self) -> None:
        """检查平滑移动是否完成"""
        if not self.is_dragging and self._is_position_close():
            self.smoothing_timer.stop()
            logger.debug("平滑移动检查完成，定时器停止")
    
    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """鼠标双击事件处理
        
        Args:
            event: 鼠标事件
        """
        if event.button() == Qt.MouseButton.LeftButton:
            # 确保不会处于拖动状态
            self.is_dragging = False
            self.drag_activated = False
            self.watchdog_timer.stop()
            
            # 发送双击信号
            self.double_clicked.emit(event.position().toPoint())
        
        super().mouseDoubleClickEvent(event)
    
    def resizeEvent(self, event: QResizeEvent) -> None:
        """窗口大小改变事件处理
        
        Args:
            event: 大小改变事件
        """
        # 发送大小改变信号
        self.size_changed.emit(event.size())
        
        super().resizeEvent(event)
    
    def moveEvent(self, event: QMoveEvent) -> None:
        """窗口位置改变事件处理
        
        Args:
            event: 移动事件
        """
        # 发送位置改变信号
        self.position_changed.emit(event.pos())
        
        # 获取事件系统实例
        event_system = EventSystem.get_instance()
        
        # 发送窗口位置变化事件
        event_data = WindowPositionChangedEvent(
            position=self.pos(),
            size=self.size(),
            sender=self
        )
        event_system.dispatch_event(EventType.WINDOW_POSITION_CHANGED, data=event_data)
        logger.debug(f"发送窗口位置变化事件: pos={self.pos()}")
        
        super().moveEvent(event)

    def set_drag_mode(self, mode: str) -> None:
        """设置拖动模式
        
        Args:
            mode: 拖动模式 - "smart", "precise", "smooth"
        """
        valid_modes = ["smart", "precise", "smooth"]
        if mode in valid_modes:
            self.drag_mode = mode
            # 设置模式时立即更新平滑系数和定时器间隔
            self._update_smoothing_factor()
            self._update_timer_interval()
            logger.info(f"拖动模式已设置为: {mode}")

# # 如果直接运行这个文件，则创建一个测试窗口
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     
#     window = MainPetWindow()
#     
#     # 测试用图像（实际上这里可能会因为没有真实路径而报错，但为了演示保留）
#     test_image_path = "assets/images/characters/default/idle/idle_1.png"
#     window.set_image(test_image_path)
#     
#     window.show()
#     
#     sys.exit(app.exec()) 