"""Compara alocatorii Greedy si Hungarian pe aceleasi scenarii, pe mai multe seed-uri.

Pentru fiecare (scenariu, numar de roboti, seed) ambii alocatori primesc EXACT aceleasi
comenzi: alocatorul nu foloseste generatorul aleator al flotei. Diferentele dintre ei
pot fi deci masurate pe perechi, nu doar prin medii.

Rulare:  python -m benchmark.comparator --seeds 10
"""
import argparse
import csv
import json
from pathlib import Path
from statistics import mean, stdev

from benchmark.runner import run_case

ALLOCATORS = ('greedy', 'hungarian')

# burst: 20 comenzi deodata (stres pentru alocare); steady: o comanda la 5 tick-uri,
# ritm suficient de rapid ca la putini roboti sa se formeze coada.
SCENARIOS = {
    'burst': dict(jobs=20, burst=True, ticks=900),
    'steady': dict(jobs=30, interval=5, ticks=900),
}

# Metrici unde mai mic = mai bine.
METRICS = ('makespan_ticks', 'distance_cells', 'wait_ticks',
           'mean_latency_ticks', 'p95_latency_ticks', 'max_latency_ticks')


def run_grid(robot_counts, seeds, scenarios=SCENARIOS, coordination='window', progress=print):
    """Ruleaza toate combinatiile si returneaza lista de rezultate (fara lista de comenzi)."""
    rows = []
    for name, params in scenarios.items():
        for robots in robot_counts:
            for seed in seeds:
                for allocator in ALLOCATORS:
                    result = run_case(coordination, robots, seed, allocator=allocator, **params)
                    result.pop('scenario')
                    result['scenario_name'] = name
                    rows.append(result)
            progress(f'  gata: {name}, {robots} roboti ({len(seeds)} seed-uri)')
    return rows


def _stats(values):
    values = [v for v in values if v is not None]
    if not values:
        return {'mean': None, 'std': None, 'n': 0}
    return {'mean': mean(values), 'std': stdev(values) if len(values) > 1 else 0.0, 'n': len(values)}


def aggregate(rows):
    """Medie si abatere standard pe seed-uri, per (scenariu, roboti, alocator)."""
    groups = {}
    for row in rows:
        groups.setdefault((row['scenario_name'], row['robots'], row['allocator']), []).append(row)
    result = []
    for (scenario, robots, allocator), group in groups.items():
        entry = {'scenario': scenario, 'robots': robots, 'allocator': allocator,
                 'runs': len(group), 'runs_with_unfinished': sum(r['unfinished'] > 0 for r in group)}
        for metric in METRICS:
            entry[metric] = _stats([r[metric] for r in group])
        result.append(entry)
    return result


def paired_summary(rows):
    """Pentru fiecare seed compara Hungarian cu Greedy: diferenta medie si cate seed-uri castiga.

    diff = hungarian - greedy; negativ inseamna ca Hungarian e mai bun (mai mic = mai bine).
    """
    by_key = {}
    for row in rows:
        by_key[(row['scenario_name'], row['robots'], row['seed'], row['allocator'])] = row
    summary = []
    for scenario, robots in sorted({(r['scenario_name'], r['robots']) for r in rows}):
        seeds = sorted({r['seed'] for r in rows if (r['scenario_name'], r['robots']) == (scenario, robots)})
        entry = {'scenario': scenario, 'robots': robots}
        for metric in METRICS:
            diffs = []
            for seed in seeds:
                g = by_key[(scenario, robots, seed, 'greedy')][metric]
                h = by_key[(scenario, robots, seed, 'hungarian')][metric]
                if g is not None and h is not None:
                    diffs.append(h - g)
            entry[metric] = {
                'mean_diff': mean(diffs) if diffs else None,
                'hungarian_better': sum(d < 0 for d in diffs),
                'tie': sum(d == 0 for d in diffs),
                'hungarian_worse': sum(d > 0 for d in diffs),
                'n': len(diffs),
            }
        summary.append(entry)
    return summary


def write_outputs(rows, outdir):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    csv_path = outdir / 'allocator_runs.csv'
    with csv_path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    json_path = outdir / 'allocator_comparison.json'
    json_path.write_text(json.dumps({
        'version': 1,
        'seeds': sorted({r['seed'] for r in rows}),
        'aggregate': aggregate(rows),
        'paired': paired_summary(rows),
    }, indent=2), encoding='utf-8')
    return csv_path, json_path


def print_report(rows):
    print('\nHungarian fata de Greedy, pe perechi (negativ = Hungarian mai bun):')
    print(f'{"scenariu":8} {"roboti":>6}  {"metrica":19} {"diff medie":>10}  H mai bun / egal / H mai slab')
    for entry in paired_summary(rows):
        for metric in ('makespan_ticks', 'distance_cells', 'mean_latency_ticks', 'max_latency_ticks'):
            m = entry[metric]
            diff = 'n/a' if m['mean_diff'] is None else f'{m["mean_diff"]:+.1f}'
            print(f'{entry["scenario"]:8} {entry["robots"]:>6}  {metric:19} {diff:>10}  '
                  f'{m["hungarian_better"]:>3} / {m["tie"]:>2} / {m["hungarian_worse"]:>2}   (n={m["n"]})')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds', type=int, default=10, help='numar de seed-uri (0..N-1)')
    parser.add_argument('--robots', type=int, nargs='+', default=[3, 5, 8])
    parser.add_argument('--coordination', choices=('window', 'conservative'), default='window')
    parser.add_argument('--out', type=Path, default=Path('artifacts'))
    parser.add_argument('--no-plots', action='store_true')
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error('--seeds trebuie sa fie >= 1')
    print(f'Benchmark alocatori: {args.seeds} seed-uri, roboti {args.robots}, coordonare {args.coordination}')
    rows = run_grid(args.robots, list(range(args.seeds)), coordination=args.coordination)
    csv_path, json_path = write_outputs(rows, args.out)
    print_report(rows)
    print(f'\nDate brute: {csv_path}\nRezumat:    {json_path}')
    if not args.no_plots:
        from benchmark.plots import plot_comparison
        for path in plot_comparison(json_path, args.out):
            print(f'Grafic:     {path}')


if __name__ == '__main__':
    main()
