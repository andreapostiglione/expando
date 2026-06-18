from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable
from unittest.mock import patch

from . import __version__
from .app_context import AppContext
from .config import AppConfig, ConfigBundle, Match, compile_matches
from .engine import ExpansionEngine
from .i18n import t
from .injector import InjectorSettings, TextInjector


@dataclass
class BenchmarkResult:
    match_count: int
    compile_ms: float
    reload_ms: float
    char_iterations: int
    char_ops_per_sec: float
    char_latency_p50_us: float
    char_latency_p95_us: float
    char_latency_p99_us: float
    expand_iterations: int
    expand_lookup_p50_us: float
    expand_lookup_p95_us: float
    expand_lookup_p99_us: float


def generate_benchmark_matches(count: int) -> list[Match]:
    width = max(4, len(str(count)))
    return [
        Match(
            triggers=[f":b{index:0{width}d}"],
            replace=f"snippet-{index}",
        )
        for index in range(1, count + 1)
    ]


def _percentile_us(samples_us: list[float], percentile: float) -> float:
    if not samples_us:
        return 0.0
    ordered = sorted(samples_us)
    rank = max(0, min(len(ordered) - 1, int(round((percentile / 100) * (len(ordered) - 1)))))
    return ordered[rank]


def _time_call(callback: Callable[[], None], iterations: int) -> list[float]:
    samples: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        callback()
        elapsed_us = (time.perf_counter() - start) * 1_000_000
        samples.append(elapsed_us)
    return samples


def run_engine_benchmark(
    *,
    match_count: int = 1000,
    char_iterations: int = 10_000,
    expand_iterations: int = 2_000,
) -> BenchmarkResult:
    if match_count < 1:
        raise ValueError("match_count must be at least 1")
    if char_iterations < 1 or expand_iterations < 1:
        raise ValueError("iterations must be at least 1")

    matches = generate_benchmark_matches(match_count)
    context = AppContext(name="Benchmark")

    compile_start = time.perf_counter()
    compile_matches(matches)
    compile_ms = (time.perf_counter() - compile_start) * 1000

    config = ConfigBundle(app=AppConfig(respect_secure_input=False), matches=matches)
    injector = TextInjector(InjectorSettings())
    engine = ExpansionEngine(config=config, injector=injector)

    engine.injector.inject = lambda text, **kwargs: None  # type: ignore[method-assign]
    engine.injector.delete_chars = lambda count: None  # type: ignore[method-assign]

    with patch(
        "expando.engine.get_frontmost_context",
        return_value=context,
    ), patch("expando.engine.is_secure_input_active", return_value=False), patch(
        "expando.engine.render_match_interactive",
        side_effect=lambda match, **kwargs: match.replace,
    ):
        reload_start = time.perf_counter()
        engine.reload(config)
        reload_ms = (time.perf_counter() - reload_start) * 1000

        def feed_char() -> None:
            engine.handle_char("x")

        char_samples = _time_call(feed_char, char_iterations)
        char_total_s = sum(char_samples) / 1_000_000
        char_ops_per_sec = char_iterations / char_total_s if char_total_s > 0 else 0.0

        target = matches[match_count // 2]
        trigger = target.triggers[0]
        prefix = trigger[:-1]
        last_char = trigger[-1]

        def lookup_expand() -> None:
            engine.clear_buffer()
            for char in prefix:
                engine.handle_char(char)
            engine.handle_char(last_char)

        expand_samples = _time_call(lookup_expand, expand_iterations)

    return BenchmarkResult(
        match_count=match_count,
        compile_ms=compile_ms,
        reload_ms=reload_ms,
        char_iterations=char_iterations,
        char_ops_per_sec=char_ops_per_sec,
        char_latency_p50_us=_percentile_us(char_samples, 50),
        char_latency_p95_us=_percentile_us(char_samples, 95),
        char_latency_p99_us=_percentile_us(char_samples, 99),
        expand_iterations=expand_iterations,
        expand_lookup_p50_us=_percentile_us(expand_samples, 50),
        expand_lookup_p95_us=_percentile_us(expand_samples, 95),
        expand_lookup_p99_us=_percentile_us(expand_samples, 99),
    )


def format_benchmark_report(result: BenchmarkResult) -> str:
    lines = [
        f"{t('benchmark.matches')}: {result.match_count}",
        f"{t('benchmark.compile')}: {result.compile_ms:.2f} ms",
        f"{t('benchmark.reload')}: {result.reload_ms:.2f} ms",
        (
            f"{t('benchmark.handle_char')}: "
            f"{result.char_ops_per_sec:,.0f} {t('benchmark.ops_per_sec')} "
            f"{result.char_iterations:,} {t('benchmark.iterations')}"
        ),
        (
            f"{t('benchmark.handle_char_latency')}: "
            f"p50 {result.char_latency_p50_us:.1f} µs, "
            f"p95 {result.char_latency_p95_us:.1f} µs, "
            f"p99 {result.char_latency_p99_us:.1f} µs"
        ),
        (
            f"{t('benchmark.expand_lookup')} ({result.expand_iterations:,} "
            f"{t('benchmark.iterations')}): "
            f"p50 {result.expand_lookup_p50_us:.1f} µs, "
            f"p95 {result.expand_lookup_p95_us:.1f} µs, "
            f"p99 {result.expand_lookup_p99_us:.1f} µs"
        ),
    ]
    return "\n".join(lines)


DEFAULT_SPARKLE_HELPER_WARN_MS = 15_000


def resolve_sparkle_helper_warn_ms(override: int | None = None) -> int | None:
    import os

    if override is not None:
        return override
    raw = os.environ.get("EXPANDO_SPARKLE_HELPER_WARN_MS", "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def sparkle_helper_latency_slow(
    helper_check_ms: float | None,
    warn_ms: int | None,
) -> bool:
    return (
        helper_check_ms is not None
        and warn_ms is not None
        and helper_check_ms > warn_ms
    )


@dataclass
class SparkleBenchmarkResult:
    sparkle_available: bool
    app_bundle: str | None
    helper_path: str | None
    framework_present: bool
    appcast_fetch_ms: float
    helper_check_ms: float | None
    appcast_entries: int
    latest_version: str | None
    current_version: str
    update_available: bool


def run_sparkle_update_benchmark(*, feed_url: str | None = None) -> SparkleBenchmarkResult:
    from .sparkle_native import (
        measure_sparkle_helper_check_ms,
        resolve_distribution_app_bundle,
        sparkle_available,
        sparkle_framework_path,
        sparkle_helper_path,
    )
    from .updater import fetch_appcast, latest_update, parse_appcast
    from .version_utils import is_newer, normalize_version

    current = normalize_version(__version__)
    bundle = resolve_distribution_app_bundle()
    helper = sparkle_helper_path(bundle) if bundle is not None else None
    framework_present = (
        sparkle_framework_path(bundle) is not None if bundle is not None else False
    )

    fetch_ms = 0.0
    entries = 0
    latest_version: str | None = None
    update_available = False
    try:
        fetch_start = time.perf_counter()
        xml_text = fetch_appcast(feed_url)
        fetch_ms = (time.perf_counter() - fetch_start) * 1000
        updates = parse_appcast(xml_text)
        entries = len(updates)
        latest = latest_update(updates)
        if latest is not None:
            latest_version = latest.version
            update_available = is_newer(latest.version, current)
    except Exception:
        fetch_ms = fetch_ms or 0.0

    helper_check_ms: float | None = None
    if sparkle_available():
        helper_check_ms = measure_sparkle_helper_check_ms()

    return SparkleBenchmarkResult(
        sparkle_available=sparkle_available(),
        app_bundle=str(bundle) if bundle is not None else None,
        helper_path=str(helper) if helper is not None else None,
        framework_present=framework_present,
        appcast_fetch_ms=fetch_ms,
        helper_check_ms=helper_check_ms,
        appcast_entries=entries,
        latest_version=latest_version,
        current_version=current,
        update_available=update_available,
    )


def format_sparkle_benchmark_report(
    result: SparkleBenchmarkResult,
    *,
    warn_ms: int | None = None,
) -> str:
    lines = [
        t("benchmark.sparkle.title"),
        f"{t('benchmark.sparkle.available')}: {t('doctor.yes') if result.sparkle_available else t('doctor.no')}",
    ]
    if result.app_bundle:
        lines.append(f"{t('benchmark.sparkle.bundle')}: {result.app_bundle}")
    if result.helper_path:
        lines.append(f"{t('benchmark.sparkle.helper')}: {result.helper_path}")
    lines.append(
        f"{t('benchmark.sparkle.framework')}: "
        f"{t('doctor.yes') if result.framework_present else t('doctor.no')}"
    )
    lines.append(
        f"{t('benchmark.sparkle.appcast_fetch')}: {result.appcast_fetch_ms:.2f} ms "
        f"({result.appcast_entries} {t('benchmark.sparkle.entries')})"
    )
    if result.helper_check_ms is not None:
        lines.append(
            f"{t('benchmark.sparkle.helper_check')}: {result.helper_check_ms:.2f} ms"
        )
        if sparkle_helper_latency_slow(result.helper_check_ms, warn_ms):
            lines.append(
                t("benchmark.sparkle.helper_slow").format(
                    ms=f"{result.helper_check_ms:.2f}",
                    threshold=warn_ms,
                )
            )
    else:
        lines.append(
            f"{t('benchmark.sparkle.helper_check')}: {t('benchmark.sparkle.none')}"
        )
    lines.append(
        f"{t('benchmark.sparkle.versions')}: "
        f"{result.current_version} → {result.latest_version or t('benchmark.sparkle.none')}"
    )
    lines.append(
        f"{t('benchmark.sparkle.update_available')}: "
        f"{t('doctor.yes') if result.update_available else t('doctor.no')}"
    )
    return "\n".join(lines)