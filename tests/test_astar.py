from engine.grid import Grid, make_warehouse
from engine.astar import astar

def test_straight_line():
    path, _ = astar(Grid(5, 5), (0, 0), (4, 0))
    assert len(path) == 5

def test_goes_around_wall():
    g = Grid(5, 5)
    g.blocked |= {(2, 0), (2, 1), (2, 2), (2, 3)}
    path, _ = astar(g, (0, 0), (4, 0))
    assert path and all(g.is_free(c) for c in path)
    assert len(path) == 13          # 4 jos + 4 dreapta + 4 sus... = 12 pasi + start

def test_no_path():
    g = Grid(5, 5)
    g.blocked |= {(1, 0), (1, 1), (0, 1)}
    path, _ = astar(g, (0, 0), (4, 4))
    assert path is None

def test_warehouse_reachable():
    g = make_warehouse()
    path, _ = astar(g, (1, 1), (28, 18))
    assert path is not None

if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("OK", name)
#ccccc