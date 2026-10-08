"""Benchmark reproductibil, fara Pygame: compara coordonatorii pe aceleasi comenzi."""
import argparse
import json
import math
from pathlib import Path
from statistics import mean
from time import perf_counter

from engine.fleet import Fleet


def run_case(coordination='window', robots=5, seed=42, ticks=600, jobs=20, interval=20,
             allocator='greedy', burst=False):
    """Ruleaza un scenariu si returneaza metricile.

    burst=True: toate comenzile apar la tick 0 (test de stres pentru alocare).
    makespan_ticks: tick-ul ultimei livrari, sau None daca au ramas comenzi nelivrate.
    """
    if ticks < 1 or jobs < 0 or interval < 1:
        raise ValueError('ticks/interval trebuie sa fie pozitive; jobs >= 0.')
    fleet = Fleet(robot_count=robots, seed=seed, coordination=coordination, allocator=allocator)
    if burst:
        for _ in range(jobs):
            fleet.random_task()
    vertex_conflicts = edge_conflicts = 0
    max_step_ms = 0.0
    started = perf_counter()
    for index in range(ticks):
        if not burst and index % interval == 0 and len(fleet.tasks) < jobs:
            fleet.random_task()
        before = [r.pos for r in fleet.robots]
        step_start = perf_counter()
        fleet.step()
        max_step_ms = max(max_step_ms, (perf_counter() - step_start) * 1000)
        after = [r.pos for r in fleet.robots]
        for i in range(len(after)):
            for j in range(i + 1, len(after)):
                vertex_conflicts += after[i] == after[j]
                edge_conflicts += after[i] == before[j] and after[j] == before[i]
    elapsed = perf_counter() - started
    latencies = sorted(t.completed_tick - t.created_tick for t in fleet.tasks if t.status == 'completed')
    unfinished = len(fleet.tasks) - fleet.completed
    makespan = max((t.completed_tick for t in fleet.tasks if t.status == 'completed'), default=None)
    return {
        'coordination': coordination, 'allocator': allocator, 'burst': burst,
        'robots': robots, 'seed': seed, 'ticks': ticks,
        'requested_jobs': jobs, 'interval': interval,
        'submitted': len(fleet.tasks), 'completed': fleet.completed,
        'unfinished': unfinished,
        'makespan_ticks': makespan if unfinished == 0 and fleet.tasks else None,
        'throughput_per_tick': fleet.completed / ticks,
        'mean_latency_ticks': mean(latencies) if latencies else None,
        'p95_latency_ticks': latencies[math.ceil(.95 * len(latencies)) - 1] if latencies else None,
        'max_latency_ticks': latencies[-1] if latencies else None,
        'distance_cells': sum(r.steps for r in fleet.robots),
        'wait_ticks': sum(r.wait_ticks for r in fleet.robots),
        'vertex_conflicts': vertex_conflicts, 'edge_conflicts': edge_conflicts,
        'window_replans': fleet.coordinator.replans, 'fallbacks': fleet.coordinator.fallbacks,
        'elapsed_seconds': round(elapsed, 6), 'max_step_ms': round(max_step_ms, 3),
        'scenario': [[list(t.pickup), list(t.dropoff)] for t in fleet.tasks],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--coordination', choices=('window', 'conservative', 'all'), default='all')
    parser.add_argument('--robots', type=int, choices=range(3, 9), default=5)
    parser.add_argument('--seeds', type=int, nargs='+', default=[42])
    parser.add_argument('--ticks', type=int, default=600)
    parser.add_argument('--jobs', type=int, default=20)
    parser.add_argument('--interval', type=int, default=20)
    parser.add_argument('--output', type=Path, default=Path('artifacts/benchmark.json'))
    args = parser.parse_args()
    if args.ticks < 1 or args.jobs < 0 or args.interval < 1:
        parser.error('ticks/interval trebuie sa fie pozitive; jobs >= 0')
    modes = ('conservative', 'window') if args.coordination == 'all' else (args.coordination,)
    results = []
    for seed in args.seeds:
        for mode in modes:
            result = run_case(mode, args.robots, seed, args.ticks, args.jobs, args.interval)
            results.append(result)
            print(f'{mode:12} seed={seed}: {result["completed"]}/{result["submitted"]} livrari, '
                  f'asteptari={result["wait_ticks"]}, conflicte='
                  f'{result["vertex_conflicts"] + result["edge_conflicts"]}, '
                  f'timp={result["elapsed_seconds"]:.3f}s')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({'version': 1, 'results': results}, indent=2), encoding='utf-8')
    print(f'Raport: {args.output.resolve()}')


if __name__ == '__main__':
    main()
