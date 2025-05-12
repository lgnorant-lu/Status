"""
---------------------------------------------------------------
File name:                  vector.py
Author:                     Ignorant-lu
Date created:               2025/05/18
Description:                向量工具类，提供二维向量操作
----------------------------------------------------------------

Changed history:            
                            2025/05/18: 初始创建;
----
"""

import math
from typing import Tuple, Union, List


class Vector2D:
    """二维向量类"""
    
    def __init__(self, x: float = 0.0, y: float = 0.0):
        """初始化二维向量
        
        Args:
            x: X坐标
            y: Y坐标
        """
        self.x = float(x)
        self.y = float(y)
    
    def __str__(self) -> str:
        """字符串表示
        
        Returns:
            str: 向量的字符串表示
        """
        return f"Vector2D({self.x}, {self.y})"
    
    def __repr__(self) -> str:
        """代码表示
        
        Returns:
            str: 向量的代码表示
        """
        return f"Vector2D({self.x}, {self.y})"
    
    def __eq__(self, other) -> bool:
        """相等比较
        
        Args:
            other: 比较对象
            
        Returns:
            bool: 是否相等
        """
        if not isinstance(other, Vector2D):
            return False
        return self.x == other.x and self.y == other.y
    
    def __add__(self, other: 'Vector2D') -> 'Vector2D':
        """向量加法
        
        Args:
            other: 另一个向量
            
        Returns:
            Vector2D: 加法结果
        """
        return Vector2D(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Vector2D') -> 'Vector2D':
        """向量减法
        
        Args:
            other: 另一个向量
            
        Returns:
            Vector2D: 减法结果
        """
        return Vector2D(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar: float) -> 'Vector2D':
        """向量与标量乘法
        
        Args:
            scalar: 标量
            
        Returns:
            Vector2D: 乘法结果
        """
        return Vector2D(self.x * scalar, self.y * scalar)
    
    def __rmul__(self, scalar: float) -> 'Vector2D':
        """标量与向量乘法
        
        Args:
            scalar: 标量
            
        Returns:
            Vector2D: 乘法结果
        """
        return self.__mul__(scalar)
    
    def __truediv__(self, scalar: float) -> 'Vector2D':
        """向量除以标量
        
        Args:
            scalar: 标量
            
        Returns:
            Vector2D: 除法结果
        """
        if scalar == 0:
            raise ZeroDivisionError("除数不能为零")
        return Vector2D(self.x / scalar, self.y / scalar)
    
    def __neg__(self) -> 'Vector2D':
        """向量取反
        
        Returns:
            Vector2D: 反向向量
        """
        return Vector2D(-self.x, -self.y)
    
    def magnitude(self) -> float:
        """计算向量长度
        
        Returns:
            float: 向量长度
        """
        return math.sqrt(self.x * self.x + self.y * self.y)
    
    def magnitude_squared(self) -> float:
        """计算向量长度的平方
        
        Returns:
            float: 向量长度的平方
        """
        return self.x * self.x + self.y * self.y
    
    def normalize(self) -> 'Vector2D':
        """归一化向量
        
        Returns:
            Vector2D: 归一化后的向量
        """
        mag = self.magnitude()
        if mag == 0:
            return Vector2D(0, 0)
        return Vector2D(self.x / mag, self.y / mag)
    
    def dot(self, other: 'Vector2D') -> float:
        """向量点积
        
        Args:
            other: 另一个向量
            
        Returns:
            float: 点积结果
        """
        return self.x * other.x + self.y * other.y
    
    def cross(self, other: 'Vector2D') -> float:
        """向量叉积（二维向量的叉积是一个标量）
        
        Args:
            other: 另一个向量
            
        Returns:
            float: 叉积结果
        """
        return self.x * other.y - self.y * other.x
    
    def angle(self, other: 'Vector2D') -> float:
        """计算两向量之间的角度（弧度）
        
        Args:
            other: 另一个向量
            
        Returns:
            float: 角度（弧度）
        """
        dot = self.dot(other)
        mag1 = self.magnitude()
        mag2 = other.magnitude()
        if mag1 == 0 or mag2 == 0:
            return 0
        cos_angle = dot / (mag1 * mag2)
        # 处理浮点数精度问题
        cos_angle = max(-1.0, min(1.0, cos_angle))
        return math.acos(cos_angle)
    
    def distance_to(self, other: 'Vector2D') -> float:
        """计算到另一个向量的距离
        
        Args:
            other: 另一个向量
            
        Returns:
            float: 距离
        """
        return (other - self).magnitude()
    
    def rotate(self, angle: float) -> 'Vector2D':
        """旋转向量（弧度）
        
        Args:
            angle: 旋转角度（弧度）
            
        Returns:
            Vector2D: 旋转后的向量
        """
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return Vector2D(
            self.x * cos_a - self.y * sin_a,
            self.x * sin_a + self.y * cos_a
        )
    
    def to_tuple(self) -> Tuple[float, float]:
        """转换为元组
        
        Returns:
            Tuple[float, float]: (x, y)元组
        """
        return (self.x, self.y) 