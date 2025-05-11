from PIL import Image, ImageDraw
import os

os.makedirs('.', exist_ok=True)

for i in range(8):
    img = Image.new('RGBA', (64, 64), (200, 200, 255, 255))
    draw = ImageDraw.Draw(img)
    # 彩色方块随帧变化
    draw.rectangle([8, 8, 56, 56], fill=(100+i*15, 120, 200, 255))
    # 帧编号
    draw.text((24, 24), f'{i+1}', fill=(0,0,0,255))
    img.save(f'frame_{i+1:02d}.png')
