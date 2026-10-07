"""Sprite-uri originale pe o grila 15x15. Fara imagini externe sau filtrare.

Toate sprite-urile se maresc nearest-neighbor, la multipli intregi. Randarea
este memorata; animatia nu modifica starea determinista a simulatorului.
"""
from functools import lru_cache
import pygame

INK = (67, 58, 57)
PAPER = (246, 234, 209)
CREAM = (255, 248, 228)
MUTED = (131, 115, 96)
LINE = (195, 174, 142)
TEAL = (69, 113, 101)
TERRA = (178, 91, 65)
COLORS = ((113, 165, 140), (220, 156, 96), (158, 141, 186), (116, 166, 183),
          (205, 131, 136), (188, 176, 102), (151, 180, 123), (184, 145, 119))
NAMES = ('PIP', 'MOMO', 'LUNA', 'OTTO', 'COCO', 'NORI', 'TOTO', 'MILO')


def shade(color, amount):
    return tuple(max(0, min(255, c + amount)) for c in color)


def enlarged(surface, scale):
    return pygame.transform.scale(surface, (surface.get_width() * scale, surface.get_height() * scale))


@lru_cache(maxsize=256)
def robot_sprite(index, scale=2, facing='down', blink=False, stride=0, carrying=False):
    s = pygame.Surface((15, 15), pygame.SRCALPHA)
    body = COLORS[index % len(COLORS)]
    def box(color, rect):
        pygame.draw.rect(s, color, rect)
    box((88, 69, 55, 45), (2, 13, 12, 2))
    box(INK, (7, 0, 1, 3))
    box(shade(body, 35), (6, 0, 3, 1))
    box(INK, (2, 5, 2, 8))
    box(INK, (11, 5, 2, 8))
    box(shade(INK, 22), (2, 6 + stride % 2, 1, 2))
    box(shade(INK, 22), (12, 9 - stride % 2, 1, 2))
    box(INK, (4, 2, 7, 12))
    box(INK, (3, 3, 9, 10))
    box(body, (4, 3, 7, 9))
    box(shade(body, 35), (4, 3, 7, 1))
    box(shade(body, -25), (4, 11, 7, 2))
    box(INK, (4, 5, 7, 5))
    dx = -1 if facing == 'left' else 1 if facing == 'right' else 0
    if facing == 'up':
        box(shade(body, -20), (5, 5, 5, 4))
        box(INK, (6, 6, 3, 1))
        box(INK, (6, 8, 3, 1))
    else:
        box((224, 235, 201), (5 + dx, 6, 1, 1 if blink else 2))
        box((224, 235, 201), (8 + dx, 6, 1, 1 if blink else 2))
        box((171, 198, 157), (6, 9, 2, 1))
    box(CREAM, (6, 11, 3, 1))
    if carrying:
        box(INK, (5, 10, 7, 5))
        box((197, 142, 84), (6, 10, 5, 4))
        box((244, 210, 146), (8, 10, 1, 4))
        box((247, 230, 186), (6, 11, 1, 1))
    return enlarged(s, scale)


@lru_cache(maxsize=32)
def tile_sprite(kind, variant=0, scale=2):
    s = pygame.Surface((15, 15), pygame.SRCALPHA)
    def box(color, rect):
        pygame.draw.rect(s, color, rect)
    floor = (231, 219, 190)
    s.fill(floor)
    if kind == 'wall':
        box((183, 170, 140), (1, 3, 14, 12))
        box(INK, (1, 1, 13, 12))
        box((153, 151, 133), (2, 2, 11, 10))
        box((195, 191, 165), (2, 2, 11, 2))
        box((113, 115, 103), (2, 7, 11, 1))
        box((113, 115, 103), (7, 4, 1, 3))
        box((113, 115, 103), (5, 8, 1, 4))
    if kind == 'shelf':
        box((190, 173, 140), (1, 13, 14, 2))
        box(INK, (1, 1, 13, 13))
        box((137, 93, 67), (2, 2, 11, 11))
        box((196, 143, 89), (2, 2, 11, 1))
        box((86, 68, 57), (2, 3, 11, 4))
        box((86, 68, 57), (2, 8, 11, 4))
        for x, y, c in ((3, 3, (197, 146, 87)), (8, 3, (143, 158, 108)),
                         (3, 8, (192, 126, 99)), (8, 8, (203, 165, 107))):
            box(c, (x, y, 4, 4))
            box(shade(c, 35), (x, y, 4, 1))
            box(CREAM, (x + 1, y + 2, 2, 1))
        box((192, 139, 89), (2, 7, 11, 1))
        box((70, 58, 51), (2, 13, 2, 1))
        box((70, 58, 51), (11, 13, 2, 1))
    elif kind in ('pickup', 'dropoff', 'home'):
        color = (199, 156, 87) if kind == 'pickup' else TEAL if kind == 'dropoff' else (134, 152, 132)
        box(shade(color, -20), (1, 1, 13, 13))
        box(shade(color, 50), (2, 2, 11, 11))
        for x in (2, 6, 10):
            box(color, (x, 12, 2, 1))
        if kind == 'home':
            for rect in ((7, 4, 2, 2), (6, 6, 2, 2), (7, 7, 2, 2), (6, 9, 2, 2)):
                box(CREAM, rect)
        elif kind == 'dropoff':
            for rect in ((4, 6, 6, 2), (8, 4, 2, 2), (10, 6, 2, 2), (8, 8, 2, 2)):
                box(CREAM, rect)
        else:
            box(INK, (4, 4, 7, 6))
            box((221, 174, 105), (5, 4, 5, 5))
            box(CREAM, (7, 4, 1, 5))
    return enlarged(s, scale)


# Un mic alfabet bitmap original, folosit la titluri si numerele statiilor.
GLYPHS = {
    'A': ('01110','10001','10001','11111','10001','10001','10001'),
    'B': ('11110','10001','10001','11110','10001','10001','11110'),
    'C': ('01111','10000','10000','10000','10000','10000','01111'),
    'D': ('11110','10001','10001','10001','10001','10001','11110'),
    'E': ('11111','10000','10000','11110','10000','10000','11111'),
    'F': ('11111','10000','10000','11110','10000','10000','10000'),
    'G': ('01111','10000','10000','10111','10001','10001','01110'),
    'H': ('10001','10001','10001','11111','10001','10001','10001'),
    'I': ('111','010','010','010','010','010','111'),
    'J': ('00111','00010','00010','00010','10010','10010','01100'),
    'K': ('10001','10010','10100','11000','10100','10010','10001'),
    'L': ('10000','10000','10000','10000','10000','10000','11111'),
    'M': ('10001','11011','10101','10101','10001','10001','10001'),
    'N': ('10001','11001','10101','10011','10001','10001','10001'),
    'O': ('01110','10001','10001','10001','10001','10001','01110'),
    'P': ('11110','10001','10001','11110','10000','10000','10000'),
    'Q': ('01110','10001','10001','10001','10101','10010','01101'),
    'R': ('11110','10001','10001','11110','10100','10010','10001'),
    'S': ('01111','10000','10000','01110','00001','00001','11110'),
    'T': ('11111','00100','00100','00100','00100','00100','00100'),
    'U': ('10001','10001','10001','10001','10001','10001','01110'),
    'V': ('10001','10001','10001','10001','10001','01010','00100'),
    'W': ('10001','10001','10001','10101','10101','10101','01010'),
    'X': ('10001','10001','01010','00100','01010','10001','10001'),
    'Y': ('10001','10001','01010','00100','00100','00100','00100'),
    'Z': ('11111','00001','00010','00100','01000','10000','11111'),
    '0': ('111','101','101','101','101','101','111'),
    '1': ('010','110','010','010','010','010','111'),
    '2': ('111','001','001','111','100','100','111'),
    '3': ('111','001','001','111','001','001','111'),
    '4': ('101','101','101','111','001','001','001'),
    '5': ('111','100','100','111','001','001','111'),
    '6': ('111','100','100','111','101','101','111'),
    '7': ('111','001','001','010','010','010','010'),
    '8': ('111','101','101','111','101','101','111'),
    '9': ('111','101','101','111','001','001','111'),
    '-': ('000','000','000','111','000','000','000'),
    '.': ('0','0','0','0','0','0','1'),
    ':': ('0','1','0','0','1','0','0'),
    '/': ('001','001','010','010','010','100','100'),
    '?': ('111','001','010','010','000','010','000'),
    ' ': ('000',) * 7,
}


@lru_cache(maxsize=256)
def pixel_text(text, scale=2, color=INK):
    glyphs = [GLYPHS.get(c, GLYPHS['?']) for c in text.upper()]
    width = sum(len(g[0]) + 1 for g in glyphs) * scale
    s = pygame.Surface((max(1, width), 7 * scale), pygame.SRCALPHA)
    x = 0
    for glyph in glyphs:
        for y, row in enumerate(glyph):
            for dx, dot in enumerate(row):
                if dot == '1':
                    pygame.draw.rect(s, color, ((x + dx) * scale, y * scale, scale, scale))
        x += len(glyph[0]) + 1
    return s


@lru_cache(maxsize=4)
def crate_sprite(scale=2):
    s = pygame.Surface((15, 15), pygame.SRCALPHA)
    pygame.draw.rect(s, (171, 149, 109, 80), (3, 11, 11, 3))
    pygame.draw.rect(s, INK, (3, 3, 10, 10))
    pygame.draw.rect(s, (197, 142, 84), (4, 4, 8, 8))
    pygame.draw.rect(s, (233, 187, 118), (4, 4, 8, 2))
    pygame.draw.rect(s, CREAM, (7, 4, 2, 8))
    pygame.draw.rect(s, INK, (10, 9, 1, 2))
    return enlarged(s, scale)
