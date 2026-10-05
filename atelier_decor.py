"""Detalii pur vizuale de atelier. Nu ocupa celule si nu folosesc RNG-ul flotei."""
from functools import lru_cache
import pygame
from pixel_art import pixel_text


@lru_cache(maxsize=12)
def workshop_floor(width, height, homes, exits):
    """Beton cald, uzura rara si marcaje vopsite; fara grila de navigatie."""
    s = pygame.Surface((width * 30, height * 30))
    s.fill((231, 219, 190))
    w, h = s.get_size()
    # Diferente foarte mici intre placi mari, fara contur de celula.
    for y in range(0, h, 90):
        for x in range(0, w, 120):
            tone = (x // 120 * 7 + y // 90 * 13) % 3
            pygame.draw.rect(s, ((231, 219, 190), (233, 221, 193), (229, 217, 189))[tone], (x, y, 120, 90))
    # Granulatie determinista, rara; nu pulseaza la fiecare cadru.
    for y in range(12, h - 10, 18):
        for x in range(12, w - 10, 22):
            seed = (x * 73856093 ^ y * 19349663) & 0xffff
            if seed % 5 == 0:
                color = (220, 207, 179) if seed % 2 else (241, 229, 202)
                pygame.draw.rect(s, color, (x + seed % 7, y + seed % 9, 2 + seed % 3, 1))
    # Bordura vopsita pe podea; niciun perete nou.
    pygame.draw.rect(s, (216, 203, 174), (0, 0, w, h), 6)
    pygame.draw.rect(s, (240, 228, 201), (6, 6, w - 12, h - 12), 2)
    for x in (13, w - 16):
        for y in (13, h - 16):
            pygame.draw.rect(s, (195, 185, 158), (x, y, 3, 3))
    # Baze numerotate si mici colturi de parcare vopsite.
    for index, (x, y) in enumerate(homes):
        px, py = x * 30, y * 30
        color = (181, 186, 153)
        for dx, dy, rw, rh in ((-4, -3, 9, 2), (-4, -3, 2, 9), (25, 31, 9, 2), (32, 25, 2, 8)):
            pygame.draw.rect(s, color, (px + dx, py + dy, rw, rh))
        tag = pixel_text(f'{index + 1:02d}', 1, (158, 160, 133))
        s.blit(tag, (px + 10, py + 39))
    for index, (x, y) in enumerate(exits):
        px, py = x * 30, y * 30
        pygame.draw.rect(s, (214, 213, 177), (px - 52, py - 8, 82, 46))
        # Sageti scurte vopsite, distincte de punctele traseelor.
        for offset in (26, 40):
            for step in range(3):
                pygame.draw.rect(s, (175, 183, 148), (px - offset + step * 2, py + 10 + step * 2, 2, 2))
                pygame.draw.rect(s, (175, 183, 148), (px - offset + step * 2, py + 18 - step * 2, 2, 2))
        s.blit(pixel_text(f'IESIRE {chr(65 + index)}', 1, (151, 164, 134)), (px - 50, py + 44))
    # Estampila estompata: identitate, nu tinta sau obiect de joc.
    if w >= 420 and h >= 300:
        word = pixel_text('ATELIER', 3, (214, 202, 174))
        s.blit(word, (w // 2 - word.get_width() // 2, h // 2 - 12))
        sub = pixel_text('MICUL DEPOZIT', 1, (206, 195, 167))
        s.blit(sub, (w // 2 - sub.get_width() // 2, h // 2 + 20))
    return s


@lru_cache(maxsize=1)
def desk_plant():
    """Planta pixel art, exclusiv in panoul lateral, in afara hartii."""
    s = pygame.Surface((18, 22), pygame.SRCALPHA)
    def box(color, rect):
        pygame.draw.rect(s, color, rect)
    box((201, 183, 148), (3, 20, 13, 2))
    box((90, 117, 81), (8, 4, 2, 13))
    for x, y, color in ((3, 3, (120, 155, 104)), (9, 1, (149, 173, 115)),
                         (10, 7, (111, 145, 98)), (2, 9, (144, 169, 110))):
        box(color, (x, y, 5, 4))
        box(color, (x + 1, y - 1, 3, 6))
    box((139, 89, 67), (4, 15, 10, 5))
    box((193, 131, 91), (3, 14, 12, 2))
    box((219, 166, 118), (5, 16, 2, 3))
    return pygame.transform.scale(s, (36, 44))
