import json
import time
import random
from engine.fleet import Fleet

def compare_allocators(robots=5, ticks=300, jobs=20):
    print(f"--- Rulare Benchmark STRESS TEST: {robots} roboti, {jobs} joburi SIMULTANE ---")
    results = []
    
    # Generate same random tasks for both
    rng = random.Random(42)
    pickups = [(4, 2), (12, 2), (20, 2), (4, 8), (12, 8), (20, 8)]
    dropoffs = [(28, 5), (28, 11), (28, 17)]
    pairs = [(a, b) for a in pickups for b in dropoffs if a != b]
    task_list = [rng.choice(pairs) for _ in range(jobs)]
    
    for allocator in ['greedy', 'hungarian']:
        start_time = time.time()
        
        fleet = Fleet(robot_count=robots, coordination='window', allocator=allocator)
        
        # Add all tasks at tick 0 (burst)
        for pickup, dropoff in task_list:
            fleet.add_task(pickup, dropoff)
        
        for t in range(ticks):
            fleet.step()
            
        elapsed = time.time() - start_time
        
        deliveries = fleet.completed
        total_wait = sum(r.wait_ticks for r in fleet.robots)
        total_steps = sum(r.steps for r in fleet.robots)
        
        print(f"Allocator: {allocator:10} | Livrate: {deliveries:2}/{jobs} | Pasi: {total_steps:3} | Asteptare: {total_wait:2} | Timp: {elapsed:.2f}s")

if __name__ == '__main__':
    compare_allocators()
