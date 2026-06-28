from __future__ import annotations

import pathlib

from PIL import Image, ImageDraw, ImageFilter


ROOT = pathlib.Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)


def make_icon(size: int = 256) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    margin = int(size * 0.08)
    box = [margin, margin, size - margin, size - margin]
    draw.rounded_rectangle(box, radius=int(size * 0.18), fill=(10, 12, 14, 255), outline=(170, 18, 42, 255), width=int(size * 0.035))

    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.arc([45, 45, 211, 211], 18, 342, fill=(210, 30, 55, 220), width=10)
    glow = glow.filter(ImageFilter.GaussianBlur(2))
    image.alpha_composite(glow)

    draw = ImageDraw.Draw(image)
    center = size // 2
    red = (205, 18, 45, 255)
    white = (238, 241, 244, 255)
    steel = (112, 124, 136, 255)

    draw.ellipse([54, 54, 202, 202], outline=red, width=9)
    draw.ellipse([91, 91, 165, 165], outline=white, width=5)
    draw.line([center, 42, center, 86], fill=white, width=5)
    draw.line([center, 170, center, 214], fill=white, width=5)
    draw.line([42, center, 86, center], fill=white, width=5)
    draw.line([170, center, 214, center], fill=white, width=5)
    draw.ellipse([121, 121, 135, 135], fill=red)

    gear_center = (176, 176)
    gear_r = 34
    tooth_r = 43
    for angle in range(0, 360, 45):
        import math

        radians = math.radians(angle)
        x = gear_center[0] + math.cos(radians) * tooth_r
        y = gear_center[1] + math.sin(radians) * tooth_r
        draw.rounded_rectangle([x - 7, y - 7, x + 7, y + 7], radius=3, fill=steel)
    draw.ellipse([gear_center[0] - gear_r, gear_center[1] - gear_r, gear_center[0] + gear_r, gear_center[1] + gear_r], fill=steel, outline=white, width=3)
    draw.ellipse([gear_center[0] - 13, gear_center[1] - 13, gear_center[0] + 13, gear_center[1] + 13], fill=(10, 12, 14, 255), outline=white, width=2)

    return image


if __name__ == "__main__":
    icon = make_icon()
    icon.save(ASSETS / "app.png")
    icon.save(ASSETS / "app.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(ASSETS / "app.ico")
