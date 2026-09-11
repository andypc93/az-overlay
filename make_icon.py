"""Turn assets/logo.png into assets/icon.ico (exe + tray) and a trimmed 256px PNG."""

import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "assets", "logo.png")
ICO = os.path.join(HERE, "assets", "icon.ico")
PNG = os.path.join(HERE, "assets", "logo_256.png")


def main():
    im = Image.open(SRC).convert("RGBA")
    bbox = im.getchannel("A").getbbox()
    if bbox:
        im = im.crop(bbox)
    side = max(im.size)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(im, ((side - im.width) // 2, (side - im.height) // 2))
    square.resize((256, 256), Image.LANCZOS).save(PNG)
    square.save(ICO, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("wrote", PNG, ICO)


if __name__ == "__main__":
    main()
