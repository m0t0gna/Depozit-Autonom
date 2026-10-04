from benchmark import run_case


def test_benchmark_uses_same_workload_for_both_coordinators():
    a = run_case('conservative', ticks=60, jobs=3, interval=10)
    b = run_case('window', ticks=60, jobs=3, interval=10)
    assert a['scenario'] == b['scenario']
    for result in (a, b):
        assert result['submitted'] == 3
        assert result['completed'] + result['unfinished'] == 3
        assert result['vertex_conflicts'] == result['edge_conflicts'] == 0


def test_empty_benchmark_has_no_fake_latency():
    result = run_case(ticks=2, jobs=0)
    assert result['submitted'] == result['completed'] == 0
    assert result['mean_latency_ticks'] is None
    assert result['p95_latency_ticks'] is None
