"""Reusable DLS 26 kit generator.
Builds a 512x512 import-ready PNG from a DLS UV template using any colors.
"""
import os
from PIL import Image, ImageDraw

TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dls_template.png')


def hex2rgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def generate_kit(out_path, primary='#22C55E', secondary='#0C0E10',
                 socks=None, style='home'):
    """Generate a DLS kit PNG.

    primary   -> jersey / sleeves / shorts base color
    secondary -> accents: back panel, chest sash, fang outline
    socks     -> sock color (defaults to secondary)
    style     -> 'home' (back = secondary) or 'away' (back = primary)
    """
    socks = socks or secondary
    im = Image.open(TEMPLATE).convert('RGB')
    W, H = im.size
    px = im.load()
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    od = out.load()

    p = hex2rgb(primary) + (255,)
    s = hex2rgb(secondary) + (255,)
    sk = hex2rgb(socks) + (255,)
    band = p  # sock band uses primary

    for y in range(H):
        for x in range(W):
            r, g, b = px[x, y]
            # background -> transparent
            if r > 215 and g > 215 and b > 215:
                continue
            # thin outlines
            if r < 40 and g < 40 and b < 40:
                od[x, y] = s
                continue
            # back panel (blue guide)
            if b > 150 and r < 70:
                od[x, y] = (p if style == 'away' else s)
                continue
            # socks (salmon guide)
            if r > 200 and g < 185 and b < 185:
                od[x, y] = (band if 392 <= y <= 416 else sk)
                continue
            # front / sleeves / shorts (gray guide) + chest sash
            if 40 <= x <= 240 and 30 <= y <= 220:
                if -8 <= (y - (x * 0.75 + 10)) <= 22:
                    od[x, y] = s
                    continue
            od[x, y] = p

    d = ImageDraw.Draw(out)
    # venom fang emblem (chest front + back)
    d.polygon([(132, 80), (106, 146), (158, 146)], fill=s)
    d.polygon([(132, 92), (116, 140), (148, 140)], fill=p)
    d.polygon([(360, 42), (334, 108), (386, 108)], fill=s)
    d.polygon([(360, 54), (344, 102), (376, 102)], fill=p)

    out.save(out_path)
    return out_path


if __name__ == '__main__':
    generate_kit('dls26_venom_kit.png', '#22C55E', '#0C0E10', '#0C0E10', 'home')
    generate_kit('dls26_venom_kit_away.png', '#0C0E10', '#22C55E', '#22C55E', 'away')
    print('regenerated home + away')
