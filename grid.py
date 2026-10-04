"""grid.py - harta depozitului.

Harta e un grid (o matrice de celule). Fiecare celula e fie libera, fie blocata
(raft sau obstacol). Coordonatele sunt tupluri (x, y): x = coloana, y = randul.
"""


class Grid:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # Retinem doar celulele BLOCATE, intr-un set: verificarea
        # "e blocata?" costa O(1), iar harta goala nu ocupa memorie.
        self.blocked = set()

    def in_bounds(self, cell):
        x, y = cell
        return 0 <= x < self.width and 0 <= y < self.height

    def is_free(self, cell):
        return self.in_bounds(cell) and cell not in self.blocked

    def neighbors(self, cell):
        """Vecinii accesibili: sus, jos, stanga, dreapta (fara diagonale)."""
        x, y = cell
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (x + dx, y + dy)
            if self.is_free(nxt):
                yield nxt

    def toggle(self, cell):
        """Pune sau scoate un obstacol (folosit la click cu mouse-ul)."""
        if not self.in_bounds(cell):
            return
        if cell in self.blocked:
            self.blocked.remove(cell)
        else:
            self.blocked.add(cell)


def make_warehouse(width=30, height=20):
    """Construieste un depozit simplu: randuri de rafturi cu culoare intre ele."""
    grid = Grid(width, height)
    # Blocuri de rafturi: 2 randuri late, separate de culoare de 2 celule.
    for row_start in (3, 9, 15):
        for y in range(row_start, row_start + 2):
            for x in range(4, width - 4):
                # lasam goluri la fiecare 8 celule ca sa se poata trece dintr-un culoar in altul
                if (x - 4) % 8 != 7:
                    grid.blocked.add((x, y))
    return grid
