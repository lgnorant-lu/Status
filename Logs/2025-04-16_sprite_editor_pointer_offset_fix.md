# [2025-04-16] Sprite Editor 画布指针偏移修复与显示逻辑统一

## 背景
在 Sprite Mask Editor 工具的手绘/擦除等操作中，用户反馈存在鼠标指针与实际绘制/擦除位置明显偏移的问题，尤其在窗口缩放、平移或控件宽高比与图像不一致时尤为明显。

## 变更内容
- 统一了 tools/sprite_editor/widgets.py 中 update_pix、update_pix_for_grabcut、update_pix_for_watershed 三个方法的 pixmap 绘制逻辑，无论缩放/平移与否，均采用控件大小背景、手动计算居中+偏移的方式绘制，确保与 widget_to_image_coords 坐标换算逻辑严格一致。
- 移除了原有的 scaled() 分支，避免了 letterbox/pillarbox 造成的坐标不一致。
- 相关方法均已适配，保证所有显示模式下鼠标操作与实际绘制/擦除位置完全一致。

## 影响范围
- tools/sprite_editor/widgets.py
- Sprite Mask Editor 的所有蒙版编辑、GrabCut、Watershed 等交互模式

## 验证建议
1. 启动 Sprite Mask Editor，加载任意图片。
2. 在不同缩放、平移状态下，使用画笔/橡皮工具绘制/擦除，观察鼠标指针与实际效果是否一致。
3. 尝试 GrabCut、Watershed 等高级模式，验证所有模式下坐标一致性。
4. 特别关注窗口宽高比与图像不一致时的表现。

## 相关提交
- [sprite_editor] 修复画布指针偏移，统一所有显示模式下的pixmap绘制逻辑，确保与坐标换算一致 