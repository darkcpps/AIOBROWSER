"""Compose the per-tab renders into single contact-sheet images."""
from PIL import Image, ImageDraw, ImageFont

TABS = [
    ("games", "Games"),
    ("search", "Search"),
    ("software", "Software"),
    ("patcher", "Steam Patcher"),
    ("downloader", "Downloaders"),
    ("emulators", "Emulators"),
    ("downloads", "Downloads"),
    ("info", "Information"),
    ("settings", "Settings"),
]

TILE_W = 600
CAP_H = 26
PAD = 10
BG = (12, 12, 18)


def _font(size=16):
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def build_sheet(theme, tabs, out_path, cols=3):
    tiles = []
    for key, label in tabs:
        try:
            img = Image.open(f"/workspace/shots/{theme}__{key}.png").convert("RGB")
        except FileNotFoundError:
            continue
        ratio = TILE_W / img.width
        img = img.resize((TILE_W, int(img.height * ratio)), Image.LANCZOS)
        tile = Image.new("RGB", (TILE_W, img.height + CAP_H), BG)
        tile.paste(img, (0, CAP_H))
        draw = ImageDraw.Draw(tile)
        draw.text((8, 5), f"{label}", fill=(230, 230, 240), font=_font(16))
        tiles.append(tile)

    if not tiles:
        return

    tile_h = max(t.height for t in tiles)
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new(
        "RGB",
        (cols * TILE_W + (cols + 1) * PAD, rows * tile_h + (rows + 1) * PAD),
        BG,
    )
    for i, tile in enumerate(tiles):
        r, c = divmod(i, cols)
        x = PAD + c * (TILE_W + PAD)
        y = PAD + r * (tile_h + PAD)
        sheet.paste(tile, (x, y))

    sheet.save(out_path)
    print("wrote", out_path, sheet.size)


build_sheet("default", TABS, "/workspace/shots/contact_default.png", cols=3)

theme_tabs = [("settings", "Midnight Purple"), ("settings", "Aurora Borealis"), ("settings", "Black Gold")]
themes = ["default", "aurora_borealis", "black_gold"]
tiles = []
for theme, label in zip(themes, [t[1] for t in theme_tabs]):
    img = Image.open(f"/workspace/shots/{theme}__settings.png").convert("RGB")
    ratio = TILE_W / img.width
    img = img.resize((TILE_W, int(img.height * ratio)), Image.LANCZOS)
    tile = Image.new("RGB", (TILE_W, img.height + CAP_H), BG)
    tile.paste(img, (0, CAP_H))
    ImageDraw.Draw(tile).text((8, 5), label, fill=(230, 230, 240), font=_font(16))
    tiles.append(tile)
tile_h = max(t.height for t in tiles)
sheet = Image.new("RGB", (3 * TILE_W + 4 * PAD, tile_h + 2 * PAD), BG)
for i, tile in enumerate(tiles):
    sheet.paste(tile, (PAD + i * (TILE_W + PAD), PAD))
sheet.save("/workspace/shots/contact_themes.png")
print("wrote /workspace/shots/contact_themes.png", sheet.size)
