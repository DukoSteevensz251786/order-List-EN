#!/usr/bin/env python3
"""
make_og_images.py — branded 1200x630 social share cards (EN + pt-BR).

Writes og/og-en.png and og/og-pt.png. Palette matches the catalogue:
navy #14294B, blue #2E5496, amber #E8850C. A faint column of real OE part
numbers on the right ties the card to the actual product.

Re-run only if you want to change the artwork; build.py just references the files.
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

REPO = Path(__file__).resolve().parent
OG = REPO / "og"
OG.mkdir(exist_ok=True)

W, H = 1200, 630
NAVY = (20, 41, 75)
BLUE = (46, 84, 150)
BLUE2 = (61, 107, 196)
AMBER = (232, 133, 12)
WHITE = (255, 255, 255)
MIST = (215, 225, 241)   # #D7E1F1
FAINT = (255, 255, 255)

LSB = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
LSR = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


# A few representative real OE numbers for the background motif.
PN_MOTIF = [
    "81.08405-0028", "51.95800-7494", "2N0129620B", "500055710",
    "0004201200", "81.61910-0046", "2E0611775", "504087452",
    "A0004205400", "90915-YZZD4", "81.25902-0508", "51.05500-6073",
    "2996416", "81.50221-6142", "0034205600", "2N0819638",
]

CONTENT = {
    "en": {
        "head1": "Genuine OE",
        "head2": "Truck Parts",
        "sub": "Surplus stock · ships worldwide from the Netherlands",
        "tag": "1,500+ OE line items · prices in EUR",
    },
    "pt": {
        "head1": "Peças Genuínas OE",
        "head2": "de Caminhão",
        "sub": "Estoque excedente · enviamos da Holanda para o mundo",
        "tag": "1.500+ itens OE · preços em EUR",
    },
}
BRAND_ROW = "MAN · VW · Iveco · Mercedes-Benz · Toyota"


def rounded(draw, box, r, fill):
    draw.rounded_rectangle(box, radius=r, fill=fill)


def make(lang):
    c = CONTENT[lang]
    img = Image.new("RGBA", (W, H), NAVY + (255,))
    d = ImageDraw.Draw(img)

    # Diagonal gradient navy -> blue toward bottom-right.
    for y in range(H):
        t = y / H
        r = int(NAVY[0] + (BLUE[0] - NAVY[0]) * t * 0.9)
        g = int(NAVY[1] + (BLUE[1] - NAVY[1]) * t * 0.9)
        b = int(NAVY[2] + (BLUE2[2] - NAVY[2]) * t * 0.9)
        d.line([(0, y), (W, y)], fill=(r, g, b, 255))

    # Faint part-number motif, right third — on its own overlay so alpha works.
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    fmono = font(MONO, 26)
    yy = 40
    for pn in PN_MOTIF:
        od.text((820, yy), pn, font=fmono, fill=(255, 255, 255, 22))
        yy += 36
    img = Image.alpha_composite(img, overlay)
    d = ImageDraw.Draw(img)

    # Left amber accent bar.
    d.rectangle([0, 0, 12, H], fill=AMBER)

    PAD = 70
    # VV mark.
    mark = 92
    rounded(d, [PAD, 66, PAD + mark, 66 + mark], 18, AMBER)
    fvv = font(LSB, 44)
    tb = d.textbbox((0, 0), "VV", font=fvv)
    d.text((PAD + (mark - (tb[2] - tb[0])) / 2, 66 + (mark - (tb[3] - tb[1])) / 2 - 6),
           "VV", font=fvv, fill=NAVY)

    # Wordmark next to mark.
    fword = font(LSB, 30)
    d.text((PAD + mark + 22, 80), "VAN VLIET", font=fword, fill=WHITE)
    fword2 = font(LSR, 24)
    d.text((PAD + mark + 24, 118), "AUTOMOTIVE", font=fword2, fill=MIST)

    # Headline.
    fh = font(LSB, 82)
    d.text((PAD, 220), c["head1"], font=fh, fill=WHITE)
    # second line with amber
    d.text((PAD, 312), c["head2"], font=fh, fill=AMBER)

    # Subhead.
    fsub = font(LSR, 30)
    d.text((PAD, 420), c["sub"], font=fsub, fill=MIST)

    # Amber tag pill.
    ftag = font(LSB, 24)
    tb = d.textbbox((0, 0), c["tag"], font=ftag)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    rounded(d, [PAD, 474, PAD + tw + 36, 474 + th + 26], 10, AMBER)
    d.text((PAD + 18, 474 + 10), c["tag"], font=ftag, fill=NAVY)

    # Brand row bottom.
    fbr = font(LSB, 28)
    d.text((PAD, 560), BRAND_ROW, font=fbr, fill=WHITE)

    out = OG / f"og-{lang}.png"
    img.convert("RGB").save(out, "PNG")
    print(f"  \u2713 {out.relative_to(REPO)}  ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    for lang in ("en", "pt"):
        make(lang)
