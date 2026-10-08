import json

from benchmark.comparator import aggregate, paired_summary, run_grid, write_outputs
from benchmark.plots import plot_comparison

SMALL = {'burst': dict(jobs=4, burst=True, ticks=300), 'steady': dict(jobs=4, interval=5, ticks=300)}


def _rows():
    return run_grid([3], [0, 1], scenarios=SMALL, progress=lambda *_: None)


def test_grid_runs_every_combination_without_conflicts():
    rows = _rows()
    assert len(rows) == 2 * 1 * 2 * 2  # scenarii x roboti x seed-uri x alocatori
    assert all(r['vertex_conflicts'] == r['edge_conflicts'] == 0 for r in rows)
    assert all('scenario' not in r for r in rows)  # lista de comenzi nu se pastreaza


def test_aggregate_and_paired_summary_shapes():
    rows = _rows()
    assert len(aggregate(rows)) == 2 * 1 * 2
    for entry in paired_summary(rows):
        stats = entry['distance_cells']
        assert stats['hungarian_better'] + stats['tie'] + stats['hungarian_worse'] == stats['n'] == 2


def test_outputs_and_plots_are_written(tmp_path):
    csv_path, json_path = write_outputs(_rows(), tmp_path)
    assert csv_path.read_text(encoding='utf-8').startswith('coordination,')
    assert json.loads(json_path.read_text(encoding='utf-8'))['seeds'] == [0, 1]
    pngs = plot_comparison(json_path, tmp_path)
    assert {p.name for p in pngs} == {'allocators-burst.png', 'allocators-steady.png'}
    assert all(p.stat().st_size > 5000 for p in pngs)
