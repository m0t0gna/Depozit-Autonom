"""Praf pixel art la viraje; strict vizual, determinist si limitat in memorie."""
from collections import deque
from functools import lru_cache
import pygame

LIFETIME_MS = 460
MAX_PUFFS = 96


@lru_cache(maxsize=5)
def puff_sprite(stage):
    s = pygame.Surface((11, 11), pygame.SRCALPHA)
    alpha = (155, 135, 100, 65, 25)[stage]
    radius = (2, 3, 4, 4, 3)[stage]
    color = (159, 147, 126, alpha)
    light = (245, 231, 200, alpha)
    pygame.draw.rect(s, color, (5 - radius, 4, radius * 2, 4))
    pygame.draw.rect(s, color, (3, 5 - radius, 4, radius * 2))
    pygame.draw.rect(s, light, (4 - radius // 2, 3, radius + 1, 2))
    if stage >= 2:
        s.set_at((9, 2), light)
        s.set_at((1, 8), color)
    return pygame.transform.scale(s, (22, 22))


class TurnDust:
    def __init__(self):
        self.puffs = deque(maxlen=MAX_PUFFS)

    def expire(self, now):
        while self.puffs and now - self.puffs[0][0] >= LIFETIME_MS:
            self.puffs.popleft()

    def emit(self, cell, incoming, outgoing, now):
        self.expire(now)
        cross = incoming[0] * outgoing[1] - incoming[1] * outgoing[0]
        side = -1 if cross > 0 else 1
        nx, ny = -incoming[1] * side, incoming[0] * side
        for i in range(3):
            # Pe exteriorul curbei, in spatele senilelor.
            ox = nx * (7 + i * 3) - incoming[0] * (i * 3)
            oy = ny * (7 + i * 3) - incoming[1] * (i * 3)
            self.puffs.append((now, cell, ox, oy, nx * (6 + i * 2) - incoming[0] * 4,
                               ny * (6 + i * 2) - incoming[1] * 4 - 5))

    def draw(self, screen, now, origin, cell_size):
        self.expire(now)
        for born, cell, ox, oy, vx, vy in self.puffs:
            age = max(0, now - born) / LIFETIME_MS
            stage = min(4, int(age * 5))
            x = origin[0] + (cell[0] + .5) * cell_size + ox + vx * age
            y = origin[1] + (cell[1] + .5) * cell_size + oy + vy * age
            screen.blit(puff_sprite(stage), (round(x) - 11, round(y) - 11))
