#!/usr/bin/env python3
"""把自绘 SVG 渲成 PNG 预览,用于 Read 工具目检(看字是否溢出、框是否重叠):
    python3 svg2png.py images/c3_x.svg [out.png]
默认输出:SVG 所在卡根目录(往上找 card.json)的 work/test/<同名>.png;找不到卡根就写在 SVG 旁边 <同名>.preview.png。
用 playwright chromium 截图,宽度取 SVG viewBox。"""
import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

src = pathlib.Path(sys.argv[1]).resolve()
if len(sys.argv) > 2:
    out = pathlib.Path(sys.argv[2]).resolve()
else:
    root = next((d for d in src.parents if (d / "card.json").is_file()), None)
    out = (root / "work" / "test" / (src.stem + ".png")) if root else src.with_suffix(".preview.png")
out.parent.mkdir(parents=True, exist_ok=True)
s = src.read_text(encoding="utf-8")
m = re.search(r'viewBox="\s*[-\d.]+\s+[-\d.]+\s+([\d.]+)\s+([\d.]+)', s)
w, h = (int(float(m.group(1))), int(float(m.group(2)))) if m else (1200, 700)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
    pg.set_content('<html><body style="margin:0;background:#fff"><div id="w" style="width:%dpx">%s</div></body></html>' % (w, s))
    pg.wait_for_timeout(300)
    pg.locator("#w").screenshot(path=str(out))
    b.close()
print(out)
