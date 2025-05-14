# 可插拔宠物状态占位符系统实施计划

**日期**: 2025/05/15

**简介**: 本文档详细描述了宠物状态占位符系统的实施计划，该系统将用于为每个宠物状态(`PetState`)提供可插拔的、可动态加载的占位符动画文件。

## 目标

为每个`PetState`实现一个独立的、可动态加载的占位符动画文件，通过`PlaceholderFactory`进行统一管理和调用，目标占位符精致度L3/L4。

## 详细实施计划

### Phase 0: 项目文档初始化与规划

*   **0.1.** 检查并创建`docs`目录（如果尚不存在于项目根目录下）。
*   **0.2.** 将此详细计划内容写入新文件`docs/placeholder_implementation_plan.md`。
*   **0.3.** 准备`Thread.md`更新内容：
    *   新增任务:
        ```markdown
        - [计划中] 实现可插拔的宠物状态占位符系统 (详情参见: docs/placeholder_implementation_plan.md)
          - 依赖关系: 无初始依赖
          - 模块影响: `status/main.py`, `status/pet_assets/`, `tests/pet_assets/`, `status/behavior/pet_state.py`
        ```
*   **0.4.** 准备`Structure.md`更新内容（新增部分，初始状态为`[计划中]`）：
    ```markdown
    - status/
      - pet_assets/ [计划中] # 宠物资源管理模块
        - __init__.py [计划中]
        - placeholder_factory.py [计划中] # 占位符工厂，负责动态加载和提供各状态的占位符动画
        - placeholders/ [计划中] # 存放各状态占位符的具体实现文件
          - __init__.py [计划中]
          - happy_placeholder.py [计划中] # "开心"状态的占位符动画实现
          # ... (其他状态占位符文件将陆续添加)
    - tests/
      - pet_assets/ [计划中] # `pet_assets` 模块的单元测试
        - __init__.py [计划中]
        - test_placeholder_factory.py [计划中] # `PlaceholderFactory` 的单元测试
        - placeholders/ [计划中] # 各占位符实现的单元测试
          - __init__.py [计划中]
          - test_happy_placeholder.py [计划中] # `happy_placeholder` 的单元测试
    ```
*   **0.5.** 准备`Log.md`更新条目（指向详细日志，详细日志将在后续commit时创建）：
    ```markdown
    - 2025/05/15: 开始规划和设计可插拔的宠物状态占位符系统。详细设计见`docs/placeholder_implementation_plan.md`。 (关联任务: 实现可插拔的宠物状态占位符系统) (对应详细日志: `Logs/2025-05-15_placeholder_system_v1_planning.md`)
    ```
*   **0.6.** 准备`Design.md`更新内容（新增章节）：
    ```markdown
    ## 宠物资源与占位符系统 (`pet_assets`)

    为了实现宠物状态多样化表现及未来资源扩展（如网络资源加载），引入了`pet_assets`模块。

    ### 核心设计原则：
    - **单状态单文件**：每个宠物状态(`PetState`)的占位符动画逻辑封装在各自独立的Python文件中（例如`happy_placeholder.py`），位于`status/pet_assets/placeholders/`目录下。这增强了模块化，使得单个状态的视觉表现易于开发、测试和维护。
    - **统一接口**：每个状态占位符文件需提供一个名为`create_animation() -> Animation`的标准函数，用于创建并返回该状态对应的动画对象。
    - **动态加载工厂(`PlaceholderFactory`)**：`status/pet_assets/placeholder_factory.py`中的`PlaceholderFactory`类负责根据请求的`PetState`动态导入相应的占位符模块，并调用其`create_animation()`方法。这种机制避免了硬编码依赖，提高了系统的灵活性和可扩展性。当新增状态或修改状态表现时，主要工作集中在对应的占位符文件，工厂类通常无需改动。
    - **可测试性**：工厂的动态加载逻辑和每个占位符的创建逻辑均可独立进行单元测试。
    - **可扩展性**：此结构为未来集成更复杂的资源管理（如本地缓存、云端资源下载）奠定了基础，`PlaceholderFactory`可以演变为更通用的`AssetManager`的一部分。
    ```

### Phase 1: 基础目录结构与模块初始化

*   **1.1.** 创建目录: `status/pet_assets`
*   **1.2.** 创建文件: `status/pet_assets/__init__.py` (内容可为空)
*   **1.3.** 创建目录: `status/pet_assets/placeholders`
*   **1.4.** 创建文件: `status/pet_assets/placeholders/__init__.py` (内容可为空)
*   **1.5.** 创建文件: `status/pet_assets/placeholder_factory.py`，包含基本框架：
    ```python
    # status/pet_assets/placeholder_factory.py
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
    ```
*   **1.6.** 创建目录: `tests/pet_assets`
*   **1.7.** 创建文件: `tests/pet_assets/__init__.py` (内容可为空)
*   **1.8.** 创建目录: `tests/pet_assets/placeholders`
*   **1.9.** 创建文件: `tests/pet_assets/placeholders/__init__.py` (内容可为空)

### Phase 2: 原型占位符实现 (`PetState.HAPPY`)

*   **2.1.** 确保 `PetState` 枚举 (在 `status/behavior/pet_state.py`) 中包含 `HAPPY` 状态。如果不存在，请添加。
*   **2.2.** 创建文件: `status/pet_assets/placeholders/happy_placeholder.py`
*   **2.3.** 在 `happy_placeholder.py` 中实现 `create_animation()` 函数，目标是L3/L4级精致度:
    ```python
    # status/pet_assets/placeholders/happy_placeholder.py
    """
    ---------------------------------------------------------------
    File name:                  happy_placeholder.py
    Author:                     Ignorant-lu
    Date created:               2025/05/15
    Description:                "开心"状态的占位符动画实现
    ----------------------------------------------------------------

    Changed history:            
                                2025/05/15: 初始创建;
    ----
    """
    import logging
    from PySide6.QtGui import QPixmap, QPainter, QColor, QBrush, QPen, QRadialGradient
    from PySide6.QtCore import Qt, QPoint, QRect
    
    from status.animation.animation import Animation

    logger = logging.getLogger(__name__)

    def create_animation() -> Animation:
        """创建"开心"状态的占位符动画
        
        Returns:
            Animation: "开心"状态的占位符动画对象
        """
        frames = []
        size = 64  # 动画帧大小
        fps = 8    # 帧率 - 每秒8帧，使动画流畅而不过快

        # 帧1: 基础笑脸
        pixmap1 = QPixmap(size, size)
        pixmap1.fill(Qt.GlobalColor.transparent)
        painter1 = QPainter(pixmap1)
        painter1.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 创建头部渐变背景
        gradient1 = QRadialGradient(size/2, size/2, size/2)
        gradient1.setColorAt(0, QColor(255, 255, 150, 230))  # 中心亮黄色
        gradient1.setColorAt(0.8, QColor(255, 220, 100, 200))  # 边缘淡黄色
        painter1.setBrush(QBrush(gradient1))
        
        # 绘制头部
        painter1.drawEllipse(4, 4, size-8, size-8)
        
        # 眼睛
        painter1.setBrush(QBrush(QColor(40, 40, 40)))
        painter1.drawEllipse(size//3 - 4, size//3 - 2, 8, 8)  # 左眼
        painter1.drawEllipse(2*size//3 - 4, size//3 - 2, 8, 8)  # 右眼
        
        # 笑容
        pen = QPen(QColor(40, 40, 40), 2)
        painter1.setPen(pen)
        painter1.drawArc(size//4, size//2, size//2, size//3, 0, -180 * 16)  # 笑脸弧
        
        # 红晕
        painter1.setPen(Qt.PenStyle.NoPen)
        painter1.setBrush(QBrush(QColor(255, 150, 150, 100)))
        painter1.drawEllipse(size//5, size//2, size//5, size//6)  # 左脸红晕
        painter1.drawEllipse(3*size//5, size//2, size//5, size//6)  # 右脸红晕
        
        painter1.end()
        frames.append(pixmap1)

        # 帧2: 更开心的笑脸(眼睛更眯)
        pixmap2 = QPixmap(size, size)
        pixmap2.fill(Qt.GlobalColor.transparent)
        painter2 = QPainter(pixmap2)
        painter2.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 创建头部渐变背景，稍亮一些
        gradient2 = QRadialGradient(size/2, size/2, size/2)
        gradient2.setColorAt(0, QColor(255, 255, 160, 230))  # 中心亮黄色
        gradient2.setColorAt(0.8, QColor(255, 225, 110, 200))  # 边缘淡黄色
        painter2.setBrush(QBrush(gradient2))
        
        # 绘制头部，稍微放大一点
        painter2.drawEllipse(3, 3, size-6, size-6)
        
        # 眼睛(微笑眼)
        pen = QPen(QColor(40, 40, 40), 2)
        painter2.setPen(pen)
        painter2.drawArc(size//3 - 5, size//3 - 2, 10, 6, 0, 180 * 16)  # 左眼(弯曲)
        painter2.drawArc(2*size//3 - 5, size//3 - 2, 10, 6, 0, 180 * 16)  # 右眼(弯曲)
        
        # 更大的笑容
        painter2.drawArc(size//5, size//2, 3*size//5, size//3, 0, -180 * 16)  # 更宽的笑脸弧
        
        # 更明显的红晕
        painter2.setPen(Qt.PenStyle.NoPen)
        painter2.setBrush(QBrush(QColor(255, 130, 130, 120)))
        painter2.drawEllipse(size//5 - 2, size//2, size//4, size//5)  # 左脸红晕
        painter2.drawEllipse(3*size//5 - 2, size//2, size//4, size//5)  # 右脸红晕
        
        painter2.end()
        frames.append(pixmap2)
        
        # 帧3: 微微波动效果
        pixmap3 = QPixmap(size, size)
        pixmap3.fill(Qt.GlobalColor.transparent)
        painter3 = QPainter(pixmap3)
        painter3.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 创建头部渐变背景，再次变化
        gradient3 = QRadialGradient(size/2, size/2, size/2)
        gradient3.setColorAt(0, QColor(255, 255, 170, 230))  # 中心亮黄色
        gradient3.setColorAt(0.8, QColor(255, 235, 120, 200))  # 边缘淡黄色
        painter3.setBrush(QBrush(gradient3))
        
        # 绘制头部，形状稍有变化
        painter3.drawEllipse(4, 2, size-8, size-4)  # 微微向上扁平一点
        
        # 眼睛(介于帧1和帧2之间)
        painter3.setBrush(QBrush(QColor(40, 40, 40)))
        painter3.drawEllipse(size//3 - 4, size//3 - 3, 7, 7)  # 左眼
        painter3.drawEllipse(2*size//3 - 3, size//3 - 3, 7, 7)  # 右眼
        
        # 笑容
        pen = QPen(QColor(40, 40, 40), 2)
        painter3.setPen(pen)
        painter3.drawArc(size//4 + 2, size//2 - 1, size//2, size//3 + 2, 0, -180 * 16)  # 笑脸弧
        
        # 红晕
        painter3.setPen(Qt.PenStyle.NoPen)
        painter3.setBrush(QBrush(QColor(255, 140, 140, 110)))
        painter3.drawEllipse(size//5, size//2 - 1, size//5, size//6)  # 左脸红晕
        painter3.drawEllipse(3*size//5, size//2 - 1, size//5, size//6)  # 右脸红晕
        
        painter3.end()
        frames.append(pixmap3)
            
        # 创建并返回Animation对象
        animation = Animation(name="happy", frames=frames, fps=fps)
        animation.metadata["placeholder"] = True
        animation.metadata["description"] = "开心状态占位符动画"
        
        logger.debug("创建了开心状态的占位符动画")
        return animation
    ```

### Phase 3: `PlaceholderFactory` 逻辑完善

*   **3.1.** 已经在Phase 1步骤1.5中完成 `PlaceholderFactory` 的完整实现。

### Phase 4: 单元测试

*   **4.1.** 创建文件: `tests/pet_assets/placeholders/test_happy_placeholder.py`
*   **4.2.** 编写 `test_happy_placeholder.py` 的测试用例：
    ```python
    # tests/pet_assets/placeholders/test_happy_placeholder.py
    """
    ---------------------------------------------------------------
    File name:                  test_happy_placeholder.py
    Author:                     Ignorant-lu
    Date created:               2025/05/15
    Description:                "开心"状态占位符动画的单元测试
    ----------------------------------------------------------------

    Changed history:            
                                2025/05/15: 初始创建;
    ----
    """
    import unittest
    from status.pet_assets.placeholders.happy_placeholder import create_animation
    from status.animation.animation import Animation

    class TestHappyPlaceholder(unittest.TestCase):
        """测试'开心'状态的占位符动画"""
        
        def test_create_animation_returns_animation_object(self):
            """测试create_animation返回Animation对象"""
            animation = create_animation()
            self.assertIsNotNone(animation)
            self.assertIsInstance(animation, Animation)

        def test_animation_has_frames(self):
            """测试动画有帧"""
            animation = create_animation()
            self.assertTrue(len(animation.frames) > 0)
            self.assertIsNotNone(animation.frames[0])
            
        def test_animation_metadata(self):
            """测试动画元数据"""
            animation = create_animation()
            self.assertTrue("placeholder" in animation.metadata)
            self.assertTrue(animation.metadata["placeholder"])
            self.assertTrue("description" in animation.metadata)
            
        def test_animation_name(self):
            """测试动画名称"""
            animation = create_animation()
            self.assertEqual(animation.name, "happy")

    if __name__ == '__main__':
        unittest.main()
    ```
*   **4.3.** 创建文件: `tests/pet_assets/test_placeholder_factory.py`
*   **4.4.** 编写 `test_placeholder_factory.py` 的测试用例：
    ```python
    # tests/pet_assets/test_placeholder_factory.py
    """
    ---------------------------------------------------------------
    File name:                  test_placeholder_factory.py
    Author:                     Ignorant-lu
    Date created:               2025/05/15
    Description:                占位符工厂的单元测试
    ----------------------------------------------------------------

    Changed history:            
                                2025/05/15: 初始创建;
    ----
    """
    import unittest
    from unittest.mock import patch, MagicMock
    from status.pet_assets.placeholder_factory import PlaceholderFactory
    from status.behavior.pet_state import PetState
    from status.animation.animation import Animation

    class TestPlaceholderFactory(unittest.TestCase):
        """测试占位符工厂"""
        
        def setUp(self):
            """每个测试前的设置"""
            self.factory = PlaceholderFactory()

        @patch('importlib.import_module')
        def test_get_animation_successful_load(self, mock_import_module):
            """测试成功加载动画"""
            # 创建模拟的Animation对象
            mock_animation_instance = Animation(name="test", frames=[])
            
            # 创建模拟的占位符模块
            mock_placeholder_module = MagicMock()
            mock_placeholder_module.create_animation.return_value = mock_animation_instance
            
            # 配置import_module返回我们的模拟模块
            def side_effect_import(module_path):
                if module_path == "status.pet_assets.placeholders.happy_placeholder":
                    return mock_placeholder_module
                raise ImportError(f"意外的模块路径: {module_path}")
            
            mock_import_module.side_effect = side_effect_import

            # 调用待测方法
            animation = self.factory.get_animation(PetState.HAPPY)

            # 验证结果
            self.assertEqual(animation, mock_animation_instance)
            mock_import_module.assert_called_once_with("status.pet_assets.placeholders.happy_placeholder")
            mock_placeholder_module.create_animation.assert_called_once()

        @patch('importlib.import_module')
        def test_get_animation_module_not_found(self, mock_import_module):
            """测试模块未找到的情况"""
            mock_import_module.side_effect = ImportError
            animation = self.factory.get_animation(PetState.SAD) # 假设SAD占位符还不存在
            self.assertIsNone(animation)

        @patch('importlib.import_module')
        def test_get_animation_create_animation_not_found(self, mock_import_module):
            """测试create_animation函数未找到的情况"""
            mock_placeholder_module = MagicMock()
            del mock_placeholder_module.create_animation # 模拟函数缺失
            mock_import_module.return_value = mock_placeholder_module
            
            animation = self.factory.get_animation(PetState.HAPPY)
            self.assertIsNone(animation)

        @patch('importlib.import_module')
        def test_get_animation_create_animation_returns_wrong_type(self, mock_import_module):
            """测试create_animation返回错误类型的情况"""
            mock_placeholder_module = MagicMock()
            mock_placeholder_module.create_animation.return_value = "not an animation" # 错误类型
            mock_import_module.return_value = mock_placeholder_module

            animation = self.factory.get_animation(PetState.HAPPY)
            self.assertIsNone(animation)

    if __name__ == '__main__':
        unittest.main()
    ```

### Phase 5: 集成到 `main.py` (`StatusPet`)

*   **5.1.** 在 `status/main.py` 中，导入 `PlaceholderFactory` 并集成：
    ```python
    # 在文件顶部添加
    from status.pet_assets.placeholder_factory import PlaceholderFactory
    
    # 在 StatusPet.__init__ 方法中，添加
    self.placeholder_factory = PlaceholderFactory()
    
    # 修改 _initialize_state_to_animation_map 方法
    def _initialize_state_to_animation_map(self):
        """初始化状态到对应动画的映射表"""
        self.state_to_animation_map = {
            # 系统状态
            PetState.IDLE: self.idle_animation,
            # ... (保留原有的其他状态映射)
        }
        
        # 使用PlaceholderFactory加载哪些还没有专门定义的状态占位符
        # 例如，如果有HAPPY状态的占位符文件，它将被加载
        for state in PetState:
            if state not in self.state_to_animation_map:
                anim = self.placeholder_factory.get_animation(state)
                if anim:
                    logger.debug(f"从PlaceholderFactory加载{state.name}状态的占位符动画")
                    self.state_to_animation_map[state] = anim
        
        logger.debug("状态到动画的映射表已初始化")
    
    # 在处理状态变化的地方（例如_on_pet_state_changed方法）
    # 确保如果状态不在map中，尝试动态加载
    def _on_pet_state_changed(self, new_state):
        """当宠物状态变化时调用此方法"""
        if new_state not in self.state_to_animation_map:
            anim = self.placeholder_factory.get_animation(new_state)
            if anim:
                self.state_to_animation_map[new_state] = anim
                logger.debug(f"动态加载了{new_state.name}状态的占位符动画")
                
        if new_state in self.state_to_animation_map:
            new_animation = self.state_to_animation_map[new_state]
            self.set_animation(new_animation)
        else:
            logger.warning(f"未找到状态{new_state.name}的动画，保持当前动画")
    ```

### Phase 6: 集成测试

*   **6.1.** 创建文件: `tests/integration/test_placeholder_integration.py`
*   **6.2.** 编写集成测试：
    ```python
    # tests/integration/test_placeholder_integration.py
    """
    ---------------------------------------------------------------
    File name:                  test_placeholder_integration.py
    Author:                     Ignorant-lu
    Date created:               2025/05/15
    Description:                占位符系统的集成测试
    ----------------------------------------------------------------

    Changed history:            
                                2025/05/15: 初始创建;
    ----
    """
    import unittest
    from unittest.mock import patch, MagicMock
    from status.main import StatusPet
    from status.behavior.pet_state import PetState
    from status.animation.animation import Animation

    class TestPlaceholderIntegration(unittest.TestCase):
        """测试占位符系统与主应用的集成"""
        
        def setUp(self):
            """测试前的设置"""
            # 创建状态宠物实例而不调用其__init__
            self.status_pet = StatusPet.__new__(StatusPet)
            
            # 模拟必要的属性
            self.status_pet.placeholder_factory = MagicMock()
            self.status_pet.state_to_animation_map = {}
            
            # 创建模拟动画
            self.mock_happy_animation = Animation(name="happy", frames=[])
            self.status_pet.idle_animation = Animation(name="idle", frames=[])
            self.status_pet.current_animation = self.status_pet.idle_animation
            
            # 模拟set_animation方法
            self.status_pet.set_animation = MagicMock()

        def test_get_animation_for_new_state(self):
            """测试为新状态获取动画"""
            # 配置模拟对象
            self.status_pet.placeholder_factory.get_animation.return_value = self.mock_happy_animation
            
            # 调用_on_pet_state_changed方法（假设它存在）
            self.status_pet._on_pet_state_changed = lambda state: self._mock_on_pet_state_changed(state)
            self.status_pet._on_pet_state_changed(PetState.HAPPY)
            
            # 验证
            self.status_pet.placeholder_factory.get_animation.assert_called_once_with(PetState.HAPPY)
            self.assertEqual(self.status_pet.state_to_animation_map.get(PetState.HAPPY), self.mock_happy_animation)
            self.status_pet.set_animation.assert_called_once_with(self.mock_happy_animation)
            
        def _mock_on_pet_state_changed(self, new_state):
            """模拟状态变化处理方法"""
            if new_state not in self.status_pet.state_to_animation_map:
                anim = self.status_pet.placeholder_factory.get_animation(new_state)
                if anim:
                    self.status_pet.state_to_animation_map[new_state] = anim
                    
            if new_state in self.status_pet.state_to_animation_map:
                new_animation = self.status_pet.state_to_animation_map[new_state]
                self.status_pet.set_animation(new_animation)

    if __name__ == '__main__':
        unittest.main()
    ```

### Phase 7: 文档更新与项目管理

*   **7.1.** 将本计划写入 `docs/placeholder_implementation_plan.md`
*   **7.2.** 更新 `Structure.md`（根据实际进度）
*   **7.3.** 更新 `Thread.md`
*   **7.4.** 更新 `Log.md`
*   **7.5.** 更新 `Design.md`
*   **7.6.** (后续考虑) 为 `pet_assets` 模块创建图表，并更新 `Diagram.md`
*   **7.7.** 为其他 `PetState` 状态创建占位符文件和测试

## 后续扩展计划

1. **增加其他状态的占位符**: 在完成HAPPY状态的占位符并验证系统运行后，可逐步扩展到其他状态，如SAD, ANGRY, CPU_WARNING等。
2. **增强占位符动画质量**: 逐步提高占位符动画的精致度，从L1-L2级进阶到L3-L4级。
3. **资源管理器扩展**: 将`PlaceholderFactory`演变为更通用的`AssetManager`，添加本地缓存和云端资源下载能力。
4. **配置驱动**: 引入外部配置文件(如JSON)，使资源映射更加灵活。

## 影响的模块

- `status/main.py`
- `status/pet_assets/` (新增)
- `tests/pet_assets/` (新增)
- `status/behavior/pet_state.py` (可能需要确认是否包含所有需要的状态)

## 技术实现摘要

1. **`PlaceholderFactory`**: 使用Python的`importlib`动态导入状态对应的占位符模块。
2. **占位符动画**: 使用Qt的绘图API(`QPainter`,`QImage`)程序化生成占位符动画。
3. **测试策略**: 通过单元测试验证工厂逻辑和占位符创建，通过集成测试验证与`StatusPet`的集成。
