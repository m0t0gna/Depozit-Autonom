"""astar.py - algoritmul A* pe grid.

Ideea: pastram o "lista de asteptare" (open) cu celulele de explorat, ordonata
dupa  f = g + h  unde:
  g = costul real parcurs de la start pana la celula
  h = estimarea (euristica) a distantei ramase pana la tinta
Mereu explorezi celula cu f minim, adica cea mai "promitatoare".
Cu o euristica admisibila (nu supraestimeaza niciodata), A* gaseste drumul optim.
"""
import heapq
import itertools


def heuristic(a, b):
    """Distanta Manhattan: |dx| + |dy|. Admisibila pentru miscare pe 4 directii."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(grid, start, goal):
    """Returneaza (drum, celule_explorate). drum = None daca nu exista cale."""
    # Heap-ul compara tupluri; daca f e egal ar compara celulele intre ele.
    # Contorul "tie-breaker" evita asta si pastreaza ordinea inserarii.
    counter = itertools.count()
    open_heap = [(heuristic(start, goal), next(counter), start)]

    came_from = {start: None}   # de unde am ajuns in fiecare celula (pt. reconstruirea drumului)
    g_cost = {start: 0}         # cel mai bun cost cunoscut pana la fiecare celula
    closed = set()              # celule deja procesate
    explored = []               # doar pentru vizualizare: ordinea explorarii

    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        if current in closed:   # intrare veche/duplicat in heap -> o sarim
            continue
        closed.add(current)
        explored.append(current)

        if current == goal:
            return _reconstruct(came_from, goal), explored

        for nb in grid.neighbors(current):
            new_g = g_cost[current] + 1        # fiecare pas costa 1
            if nb not in g_cost or new_g < g_cost[nb]:   # drum mai bun gasit
                g_cost[nb] = new_g
                came_from[nb] = current
                f = new_g + heuristic(nb, goal)
                heapq.heappush(open_heap, (f, next(counter), nb))

    return None, explored       # open s-a golit fara sa gasim tinta: nu exista drum


def _reconstruct(came_from, goal):
    """Mergem inapoi de la tinta la start folosind came_from, apoi inversam."""
    path = []
    cell = goal
    while cell is not None:
        path.append(cell)
        cell = came_from[cell]
    path.reverse()
    return path
