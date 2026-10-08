"""Grafice pentru comparatia de alocatori, citite din allocator_comparison.json.

Rulare:  python -m benchmark.plots artifacts/allocator_comparison.json
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use('Agg')  # fara fereastra: functioneaza si pe server / in CI
import matplotlib.pyplot as plt  # noqa: E402

# Culorile paletei proiectului (ui/pixel_art.py: TEAL si TERRA), scrise ca hex ca sa
# nu importam Pygame intr-un modul de benchmark.
COLORS = {'greedy': '#457165', 'hungarian': '#B25B41'}
TITLES = {
    'makespan_ticks': 'Timp până la ultima livrare (tick-uri)',
    'distance_cells': 'Distanță totală parcursă (celule)',
    'mean_latency_ticks': 'Latență medie a comenzilor (tick-uri)',
    'max_latency_ticks': 'Cea mai lungă așteptare (tick-uri)',
}
SCENARIO_NAMES = {'burst': 'burst: 20 de comenzi deodată', 'steady': 'steady: o comandă la 5 tick-uri'}


def plot_comparison(json_path, outdir):
    """Genereaza cate un grafic (4 panouri) pentru fiecare scenariu. Intoarce caile fisierelor."""
    data = json.loads(Path(json_path).read_text(encoding='utf-8'))
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    n_seeds = len(data['seeds'])
    paths = []
    for scenario in sorted({e['scenario'] for e in data['aggregate']}):
        entries = [e for e in data['aggregate'] if e['scenario'] == scenario]
        robots = sorted({e['robots'] for e in entries})
        fig, axes = plt.subplots(1, len(TITLES), figsize=(4.2 * len(TITLES), 3.8))
        for ax, (metric, title) in zip(axes, TITLES.items()):
            width = 0.38
            for offset, allocator in ((-width / 2, 'greedy'), (width / 2, 'hungarian')):
                means, stds = [], []
                for count in robots:
                    entry = next(e for e in entries if e['robots'] == count and e['allocator'] == allocator)
                    stats = entry[metric]
                    means.append(stats['mean'] or 0)
                    stds.append(stats['std'] or 0)
                ax.bar([i + offset for i in range(len(robots))], means, width, yerr=stds, capsize=3,
                       color=COLORS[allocator], label=allocator.capitalize(), edgecolor='#433A39')
            ax.set_xticks(range(len(robots)), [str(r) for r in robots])
            ax.set_xlabel('roboți')
            ax.set_title(title, fontsize=10)
            ax.grid(axis='y', alpha=0.3)
            ax.set_axisbelow(True)
        axes[0].legend(frameon=False)
        unfinished = sum(e['runs_with_unfinished'] for e in entries)
        note = f' ({unfinished} rulări cu comenzi nelivrate)' if unfinished else ''
        fig.suptitle(f'Greedy vs. Hungarian — {SCENARIO_NAMES.get(scenario, scenario)}; '
                     f'medie ± abatere standard pe {n_seeds} seed-uri{note}', fontsize=11)
        fig.tight_layout()
        path = outdir / f'allocators-{scenario}.png'
        fig.savefig(path, dpi=130)
        plt.close(fig)
        paths.append(path)
    return paths


if __name__ == '__main__':
    source = Path(sys.argv[1] if len(sys.argv) > 1 else 'artifacts/allocator_comparison.json')
    for result in plot_comparison(source, source.parent):
        print(result)
