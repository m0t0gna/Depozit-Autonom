import json
import time
from engine.fleet import Fleet
from benchmark.runner import run_case

def compare_allocators(robots=5, ticks=300, jobs=15):
    print(f"--- Rulare Benchmark: {robots} roboti, {jobs} joburi, {ticks} tick-uri ---")
    results = []
    
    for allocator in ['greedy', 'hungarian']:
        start_time = time.time()
        
        # We need to monkey-patch run_case or write our own small loop.
        # Let's write a small evaluation loop to avoid modifying runner.py too much.
        
        fleet = Fleet(robot_count=robots, coordination='window', allocator=allocator)
        
        for t in range(ticks):
            if t % 20 == 0 and len(fleet.tasks) < jobs:
                fleet.random_task()
            fleet.step()
            
        elapsed = time.time() - start_time
        
        deliveries = fleet.completed
        total_wait = sum(r.wait_ticks for r in fleet.robots)
        total_steps = sum(r.steps for r in fleet.robots)
        
        results.append({
            "allocator": allocator,
            "deliveries": deliveries,
            "total_wait_ticks": total_wait,
            "total_steps": total_steps,
            "time_sec": round(elapsed, 2)
        })
        
        print(f"Allocator: {allocator:10} | Livrate: {deliveries}/{jobs} | Pasi: {total_steps} | Asteptare: {total_wait} | Timp: {elapsed:.2f}s")

    return results

if __name__ == '__main__':
    compare_allocators()
