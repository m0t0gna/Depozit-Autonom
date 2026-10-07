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
