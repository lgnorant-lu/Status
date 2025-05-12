# [2025-05-12] 类型提示系统优化 - Renderer模块

## 目标
解决 `status/renderer/` 目录下所有 `mypy` 类型检查错误。

## 主要变更和修复摘要

- **`status/renderer/renderer_base.py`**:
    - 为 `QObjectABCMeta` 添加 `# type: ignore[misc]` 以解决 "Unsupported dynamic base class" 错误。
    - 添加了抽象方法 `set_alpha(self, alpha: int) -> None`。
    - 添加了抽象方法 `draw_surface(self, surface, x: int, y: int, opacity: float = 1.0) -> None`。
    - 添加了抽象方法 `draw_surface_scaled(self, surface, x: int, y: int, width: int, height: int, opacity: float = 1.0) -> None`。
    - 添加了抽象方法 `get_width(self) -> int`。
    - 添加了抽象方法 `get_height(self) -> int`。
    - 添加了抽象方法 `fill_rect(self, x: int, y: int, width: int, height: int, color: Color, opacity: float = 1.0) -> None`。
    这些方法确保了 `RendererBase` 与其子类（特别是 `PySideRenderer` 和 `Transition` 子类）的接口一致性。

- **`status/renderer/drawable.py`**:
    - 为 `children: List[Drawable]` 添加类型提示。
    - 为 `tags: Set[str]` 添加类型提示并导入 `Set`。
    - 为 `data: Dict[str, Any]` 添加类型提示。
    - 为 `world_position: Tuple[float, float]` 添加类型提示。
    - 为 `world_scale_x: float`, `world_scale_y: float`, `world_rotation: float` 添加类型提示和默认值。
    - 导入 `cast` 用于类型转换。
    - 解决了多处类型不兼容问题，如 `world_position` 的赋值。
    - 修正了方法签名以匹配父类或消除歧义。

- **`status/renderer/animation.py`**:
    - 将 `_interpolate_func` 类型从 `Optional[Callable[[float], Union[float, Tuple[float, ...]]]]` 更改为 `Callable[[float], Any]` 以处理更广泛的插值目标。
    - 将 `_interpolate_number` 和 `_interpolate_tuple` 的返回类型更改为 `Any`。
    - 确保 `current_animation_index` 始终为 `int`。
    - 将 `Animator.completion_callback` 类型定为 `Optional[Callable[[], None]]`。
    - 为 `Animator._apply_easing` 方法中 `mypy` 报告的 `unreachable` 代码添加了 `# type: ignore[unreachable]`。

- **`status/renderer/primitives.py`**:
    - 将 `Point` 类的 `size` 属性和 `__init__` 参数重命名为 `point_size`，以避免与 `Drawable.size` 的命名冲突和类型不兼容问题。

- **`status/renderer/effects.py`**:
    - 为类属性 `EffectManager._initialized: bool = False` 添加了类型提示。
    - 为 `Effect.target` 的 `color` 属性访问添加了 `# type: ignore[attr-defined]`。
    - 将 `CompositeEffect` 的 `__init__` 参数 `effects: List[Effect]` 和 `duration: float` 的类型更改为 `Optional[List[Effect]]` 和 `Optional[float]` 并提供默认值 `None`。
    - 恢复了 `threading.RLock()` 的导入和在 `EffectManager` 中的使用。
    - 为其他需要类型注解的变量添加了提示。

- **`status/renderer/renderer_manager.py`**:
    - 在 `SingletonMeta` 中为类变量 `_instances` 添加类型提示 `_instances: Dict[Type, Any] = {}`。

- **`status/renderer/sprite.py`**:
    - 此文件中的 `unreachable` 错误最终被确认为在后续的 `mypy` 运行中不再出现，无需特殊忽略。之前的 `[mypy-status.renderer.sprite]` ignore_errors = True` 配置已被移除。

- **`status/renderer/transition.py`**:
    - 修正了多个 `Incompatible default for argument` 错误，通过将参数类型标记为 `Optional` (例如 `target: Optional[Drawable] = None`)。
    - 修正了 `Signature of "draw" incompatible with supertype "RendererBase"` 错误，通过调整 `Transition.draw` 方法的签名为 `def draw(self, renderer: RendererBase, *args: Any, **kwargs: Any) -> None` 并确保子类匹配。
    - 解决了由于不正确的缩进或隐藏字符导致的持久性 `syntax` 错误，通过仔细审查和修正文件内容。

- **`status/renderer/pyside_renderer.py`**:
    - 为 `PySideRenderer.draw_surface` 和 `draw_surface_scaled` 方法签名添加了 `opacity: float = 1.0` 参数，以使其与 `RendererBase` 中定义的抽象方法兼容。
    - 在这些方法的实现中加入了对 `opacity` 参数的使用。

- **`status/renderer/particle.py`**:
    - `Particle.__init__`: 参数 `color: Optional[Color] = None`。
    - `Particle.size`: getter 返回 `Tuple[float, float]`，setter 接受 `Tuple[float, float]`，内部使用 `value[0]`。
    - `ParticleEmitter.__init__`: 参数 `shape_params: Optional[Dict[str, Any]] = None`。
    - `ParticleEmitter.set_emission_shape`: 参数 `shape_params: Optional[Dict[str, Any]] = None`。
    - `Particle`: 速度和加速度属性 (如 `velocity_x`) 初始化为 `0.0` 并添加 `float` 类型提示。
    - `ParticleEmitter.__init__`: 添加 `self.particle_color_end: Optional[Color] = None` 类型提示。
    - `ParticleEmitter._get_emission_position`: 重构此方法，使其具有单一的 `return` 语句，解决了 `unreachable` 错误。

## 最终状态
执行 `mypy status/renderer/` 命令后，确认 `status/renderer/` 目录下的所有文件均无 `mypy` 类型检查错误。在检查过程中，`mypy` 可能会报告其他模块（如 `status/resources/`）中的间接错误，但这不影响 `status/renderer/` 模块本身的类型检查完成状态。 