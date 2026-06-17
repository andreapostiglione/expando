from expando.benchmark import (
    format_benchmark_report,
    generate_benchmark_matches,
    run_engine_benchmark,
)


def test_generate_benchmark_matches_unique_triggers():
    matches = generate_benchmark_matches(5)
    triggers = [match.triggers[0] for match in matches]
    assert len(set(triggers)) == 5
    assert triggers[0] == ":b0001"


def test_run_engine_benchmark_smoke():
    result = run_engine_benchmark(match_count=100, char_iterations=200, expand_iterations=50)
    assert result.match_count == 100
    assert result.char_ops_per_sec > 0
    assert result.expand_lookup_p50_us > 0
    text = format_benchmark_report(result)
    assert "Matches: 100" in text
    assert "handle_char" in text