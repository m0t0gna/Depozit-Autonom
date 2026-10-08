from benchmark.runner import run_case


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


def test_allocators_receive_identical_workload():
    greedy = run_case(ticks=40, jobs=4, interval=5, allocator='greedy')
    hungarian = run_case(ticks=40, jobs=4, interval=5, allocator='hungarian')
    assert greedy['scenario'] == hungarian['scenario']
    assert greedy['allocator'] == 'greedy' and hungarian['allocator'] == 'hungarian'


def test_burst_submits_everything_at_tick_zero_and_reports_makespan():
    result = run_case(robots=5, ticks=600, jobs=6, burst=True)
    assert result['submitted'] == 6
    assert result['unfinished'] == 0
    assert 0 < result['makespan_ticks'] <= 600
    assert result['makespan_ticks'] == result['max_latency_ticks']  # toate create la tick 0


def test_makespan_is_none_when_jobs_are_left_unfinished():
    result = run_case(robots=3, ticks=5, jobs=10, burst=True)
    assert result['unfinished'] > 0
    assert result['makespan_ticks'] is None
