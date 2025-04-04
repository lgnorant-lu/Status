# 资源管理系统更新

- **日期**: 2025-04-03
- **类别**: 核心系统, 资源管理
- **负责人**: Ignorant-lu
- **状态**: 已完成

## 概述

本文档记录了资源管理系统的优化和完善过程。资源管理系统是Hollow-ming项目的核心组件之一，负责加载、缓存和管理各类资源，包括图像、音频、字体和数据文件等。本次更新主要实现了与PyQt6的集成，特别是图像和字体资源的实际加载能力，为后续渲染系统的开发提供了基础。

## 实现详情

### 资源加载器 (ResourceLoader)

1. **图像加载功能**:
   - 使用PyQt6的QImage加载图像资源
   - 支持图像缩放（保持宽高比）
   - 支持转换为QPixmap（用于界面显示）
   - 优雅处理PyQt6不可用的情况

2. **字体加载功能**:
   - 使用PyQt6的QFont加载字体资源
   - 支持字体大小和样式设置（粗体、斜体、下划线）
   - 优雅处理字体加载失败的情况

3. **目录扫描优化**:
   - 重构scan_directory方法，提高扫描效率
   - 支持递归/非递归扫描模式
   - 按资源类型组织扫描结果

### 资产管理器 (AssetManager)

1. **与ResourceLoader和Cache的集成**:
   - 解除了之前注释的代码，实现实际功能
   - 适配最新的ResourceLoader接口

2. **资源类型特定方法**:
   - 添加get_image、get_font等便捷方法
   - 保持原有接口的向后兼容性

3. **缓存管理增强**:
   - 添加按资源类型清除缓存的功能
   - 添加获取缓存统计信息的功能

### 缓存系统 (Cache)

1. **缓存管理功能增强**:
   - 添加获取所有缓存键的方法
   - 添加获取已过期键的方法
   - 添加获取缓存项详细信息的方法

2. **统计功能完善**:
   - 完善缓存统计信息收集
   - 提供更详细的缓存使用情况数据

## 技术细节

### 图像加载实现

```python
def _load_image(self, path: str, **kwargs) -> Union[QImage, Dict]:
    """加载图像资源
    
    使用PyQt6加载图像，如果PyQt6不可用则返回占位数据
    """
    if not HAS_PYQT:
        self.logger.warning(f"PyQt6未安装，无法加载图像: {path}")
        return {"path": path, "type": "image", "loaded": False, "error": "PyQt6未安装"}
    
    try:
        # 加载图像
        image = QImage(path)
        
        if image.isNull():
            raise ResourceLoadError(f"无法加载图像: {path}")
        
        # 缩放处理
        scale_width = kwargs.get('scale_width')
        scale_height = kwargs.get('scale_height')
        
        if scale_width and scale_height:
            image = image.scaled(scale_width, scale_height)
        elif scale_width:
            # 保持宽高比
            ratio = image.height() / image.width()
            image = image.scaled(scale_width, int(scale_width * ratio))
        elif scale_height:
            # 保持宽高比
            ratio = image.width() / image.height()
            image = image.scaled(int(scale_height * ratio), scale_height)
        
        # 是否返回QPixmap
        if kwargs.get('as_pixmap', False):
            return QPixmap.fromImage(image)
        
        return image
    except Exception as e:
        self.logger.error(f"加载图像失败: {path}", exc_info=True)
        raise ResourceLoadError(f"加载图像失败: {path}, 错误: {str(e)}") from e
```

### 字体加载实现

```python
def _load_font(self, path: str, size: int = 12, **kwargs) -> Union[QFont, Dict]:
    """加载字体资源
    
    使用PyQt6加载字体，如果PyQt6不可用则返回占位数据
    """
    if not HAS_PYQT:
        self.logger.warning(f"PyQt6未安装，无法加载字体: {path}")
        return {"path": path, "type": "font", "size": size, "loaded": False, "error": "PyQt6未安装"}
    
    try:
        font = QFont()
        font_loaded = font.family() != ""
        
        if not font_loaded:
            font_id = QFont.addApplicationFont(path)
            if font_id == -1:
                self.logger.warning(f"字体加载失败: {path}")
                return {"path": path, "type": "font", "size": size, "loaded": False, "error": "字体加载失败"}
            
            font_families = QFont.applicationFontFamilies(font_id)
            if not font_families:
                self.logger.warning(f"无法获取字体族: {path}")
                return {"path": path, "type": "font", "size": size, "loaded": False, "error": "无法获取字体族"}
            
            font = QFont(font_families[0])
        
        font.setPointSize(size)
        
        # 应用额外参数
        if kwargs.get('bold', False):
            font.setBold(True)
        if kwargs.get('italic', False):
            font.setItalic(True)
        if kwargs.get('underline', False):
            font.setUnderline(True)
        
        return font
    except Exception as e:
        self.logger.error(f"加载字体失败: {path}", exc_info=True)
        return {"path": path, "type": "font", "size": size, "loaded": False, "error": str(e)}
```

## 设计模式

1. **单例模式**:
   - AssetManager实现为单例，确保全局唯一的资源管理入口

2. **策略模式**:
   - ResourceLoader使用策略模式处理不同类型资源的加载逻辑

3. **适配器模式**:
   - 为PyQt6组件提供适配层，使其符合项目资源管理规范

4. **外观模式**:
   - AssetManager作为外观，提供简化的资源访问接口

## 性能考虑

1. **资源缓存**:
   - 使用类型感知的缓存策略，不同资源类型采用不同的缓存生命周期
   - 图像和字体等重资源默认永久缓存
   - 数据和文本等轻资源使用有限生命周期

2. **内存管理**:
   - 实现资源驱逐策略，当缓存满时优先驱逐低频使用的资源
   - 支持手动清除缓存，优化内存使用

## 后续改进计划

1. **异步加载**:
   - 添加异步资源加载支持，避免阻塞主线程
   - 实现加载进度回调机制

2. **资源压缩**:
   - 添加资源压缩/解压缩功能，减少磁盘和内存占用

3. **依赖管理**:
   - 实现资源依赖管理，确保按正确顺序加载资源

4. **资源热重载**:
   - 添加检测文件变化并自动重新加载的功能，便于开发

## 技术债务

1. **音频加载**:
   - 音效和音乐加载功能仍是占位实现，需要在音频系统开发时补充

2. **动画加载**:
   - 动画加载功能仍是占位实现，需要在动画系统开发时补充

3. **测试覆盖**:
   - 需要补充关于新增功能的单元测试

## 相关文档

- [PyQt6 QImage文档](https://doc.qt.io/qt-6/qimage.html)
- [PyQt6 QFont文档](https://doc.qt.io/qt-6/qfont.html)
- [Python资源管理最佳实践](https://realpython.com/python-resources-management/) 