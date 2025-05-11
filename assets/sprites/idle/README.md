# Idle 占位动画帧说明

本目录下为桌宠MVP阶段使用的占位Idle动画帧，共8帧，命名为frame_01.png ~ frame_08.png。

- 每帧尺寸建议：64x64 像素
- 内容：简单色块+帧编号或"Knight"字样
- 用于MVP开发与测试，后续可直接替换为正式美术资源

如需批量生成可用Python PIL脚本：
```python
from PIL import Image, ImageDraw, ImageFont
for i in range(8):
    img = Image.new('RGBA', (64, 64), (200, 200, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([8, 8, 56, 56], fill=(100+i*10, 100, 200, 255))
    draw.text((20, 24), f'{i+1}', fill=(0,0,0,255))
    img.save(f'frame_{i+1:02d}.png')
```
