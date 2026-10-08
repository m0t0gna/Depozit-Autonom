from engine.fleet import Fleet
from engine.allocators import GreedyAllocator, HungarianAllocator

def test_greedy_allocator():
    fleet = Fleet(robot_count=3, allocator='greedy')
    assert isinstance(fleet.allocator, GreedyAllocator)
    fleet.add_task((4, 2), (28, 5))
    fleet.step()
    assert any(r.task_id is not None for r in fleet.robots)

def test_hungarian_allocator():
    fleet = Fleet(robot_count=3, allocator='hungarian')
    assert isinstance(fleet.allocator, HungarianAllocator)
    fleet.add_task((4, 2), (28, 5))
    fleet.step()
    assert any(r.task_id is not None for r in fleet.robots)


def test_unknown_allocator_is_rejected():
    import pytest
    with pytest.raises(ValueError):
        Fleet(robot_count=3, allocator='nope')


def _crossed_fleet(allocator):
    """Doi roboti pe o harta goala, alesi astfel incat Greedy sa aleaga prost.

    Robotul 1 e la (0,0), robotul 2 la (10,0). Comanda 1 ridica de la (4,0), comanda 2 de la (0,2).
    Greedy (FIFO) da comanda 1 robotului 1 (4 celule fata de 6), iar comanda 2 ramane robotului 2,
    care e la 12 celule de ea. Hungarian vede ambele comenzi deodata.
    """
    from engine.grid import Grid
    fleet = Fleet(robot_count=2, grid=Grid(30, 20), starts=[(0, 0), (10, 0)],
                  pickups=[(4, 0), (0, 2)], dropoffs=[(28, 5)], allocator=allocator)
    fleet.add_task((4, 0), (28, 5))
    fleet.add_task((0, 2), (28, 5))
    fleet.step()
    return fleet


def test_greedy_makes_the_locally_best_but_globally_worse_choice():
    fleet = _crossed_fleet('greedy')
    assert [t.robot_id for t in fleet.tasks] == [1, 2]


def test_hungarian_minimises_total_pickup_distance():
    fleet = _crossed_fleet('hungarian')
    assert [t.robot_id for t in fleet.tasks] == [2, 1]
