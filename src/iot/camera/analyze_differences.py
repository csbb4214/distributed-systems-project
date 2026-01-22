#!/usr/bin/env python3
import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# -------- helpers --------

def load_jsonl(path: Path) -> List[dict]:
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out

def ns_to_ms(ns: int) -> float:
    return ns / 1_000_000.0

def percentile_nearest_rank(values: List[float], p: float) -> Optional[float]:
    if not values:
        return None
    v = sorted(values)
    k = max(0, min(len(v) - 1, math.ceil(p * len(v)) - 1))
    return v[k]

def stats(values: List[float]) -> Dict[str, Optional[float]]:
    if not values:
        return {"count": 0, "avg": None, "p50": None, "p90": None, "p99": None, "min": None, "max": None}
    return {
        "count": len(values),
        "avg": sum(values) / len(values),
        "p50": percentile_nearest_rank(values, 0.50),
        "p90": percentile_nearest_rank(values, 0.90),
        "p99": percentile_nearest_rank(values, 0.99),
        "min": min(values),
        "max": max(values),
    }

def fmt(x: Optional[float]) -> str:
    return "-" if x is None else f"{x:,.2f}"

def delta_ms(ts: Dict[str, int], start: str, end: str) -> Optional[float]:
    if start not in ts or end not in ts:
        return None
    try:
        a = int(ts[start])
        b = int(ts[end])
    except Exception:
        return None
    return ns_to_ms(b - a)

def avg(values: List[float]) -> Optional[float]:
    return None if not values else (sum(values) / len(values))

# -------- analysis --------
# Wir werten bewusst sowohl wall-clock ns (time.time_ns / currentTimeMillis*1e6)
# als auch mono ns (monotonic_ns / System.nanoTime) aus, aber:
# - *_mono nur innerhalb derselben Maschine sinnvoll
# - wall-clock über Maschinen nur sinnvoll bei NTP-Sync (negatives = Hinweis auf Skew)

METRICS = [
    # End-to-End (wall)
    ("E2E wall (iot_capture -> iot_alarm_received)", "iot_capture", "iot_alarm_received"),

    # !!! NEW: the "missing" part that explains multi-second E2E
    ("IoT->Edge wait/transport wall (iot_capture -> edge_received)", "iot_capture", "edge_received"),

    # Edge intern (wall + mono)
    ("Edge preprocess wall (edge_received -> edge_filtered)", "edge_received", "edge_filtered"),
    ("Edge preprocess mono (edge_received_mono -> edge_filtered_mono)", "edge_received_mono", "edge_filtered_mono"),

    # Edge -> Cloud Transport (wall)  (über Maschinen!)
    ("Edge->Cloud transport wall (edge_sent -> cloud_received)", "edge_sent", "cloud_received"),

    # Cloud interne Pipeline (wall + mono)
    ("Cloud queue-ish wall (cloud_received -> ml_request_start)", "cloud_received", "ml_request_start"),
    ("Cloud queue-ish mono (cloud_received_mono -> ml_request_start_mono)", "cloud_received_mono", "ml_request_start_mono"),

    ("ML service wall (ml_request_start -> ml_request_end)", "ml_request_start", "ml_request_end"),
    ("ML service mono (ml_request_start_mono -> ml_request_end_mono)", "ml_request_start_mono", "ml_request_end_mono"),

    ("Cloud decide/publish wall (cloud_decision -> alarm_published)", "cloud_decision", "alarm_published"),
    ("Cloud decide/publish mono (cloud_decision_mono -> alarm_published_mono)", "cloud_decision_mono", "alarm_published_mono"),

    # Cloud -> IoT (über Maschinen!)
    ("Cloud->IoT alert wall (alarm_published -> iot_alarm_received)", "alarm_published", "iot_alarm_received"),
]

def analyze(path: Path) -> None:
    traces = load_jsonl(path)
    print("=" * 100)
    print(f"File: {path.name}")
    print(f"Traces: {len(traces)}")

    # collect
    values: Dict[str, List[float]] = {name: [] for (name, _, _) in METRICS}
    negatives: Dict[str, int] = {name: 0 for (name, _, _) in METRICS}
    missing: Dict[str, int] = {name: 0 for (name, _, _) in METRICS}

    for t in traces:
        ts = (t.get("timestamps") or {})
        for name, a, b in METRICS:
            d = delta_ms(ts, a, b)
            if d is None:
                missing[name] += 1
                continue
            if d < 0:
                negatives[name] += 1
                # trotzdem aufnehmen? -> nein, weil Skew / Timebase-Mismatch
                continue
            values[name].append(d)

    # print table
    header = (
        f"{'metric':<62} | {'count':>6} | {'avg':>10} | {'p50':>10} | {'p90':>10} | {'p99':>10} | "
        f"{'min':>10} | {'max':>10} | {'neg':>5} | {'miss':>5}"
    )
    print(header)
    print("-" * len(header))

    for name, _, _ in METRICS:
        st = stats(values[name])
        print(
            f"{name:<62} | {st['count']:6d} | {fmt(st['avg']):>10} | {fmt(st['p50']):>10} | "
            f"{fmt(st['p90']):>10} | {fmt(st['p99']):>10} | {fmt(st['min']):>10} | {fmt(st['max']):>10} | "
            f"{negatives[name]:5d} | {missing[name]:5d}"
        )

    # Bottleneck-Hinweis (nach avg und p99, ohne E2E)
    candidates = [m for m in METRICS if not m[0].startswith("E2E")]

    avg_best = None
    p99_best = None
    for name, _, _ in candidates:
        st = stats(values[name])
        if st["avg"] is not None:
            if avg_best is None or st["avg"] > avg_best[1]:
                avg_best = (name, st["avg"])
        if st["p99"] is not None:
            if p99_best is None or st["p99"] > p99_best[1]:
                p99_best = (name, st["p99"])

    print("\nBottleneck (nur aus nicht-negativen Deltas):")
    if avg_best:
        print(f"- Highest AVG : {avg_best[0]} = {avg_best[1]:,.2f} ms")
    else:
        print("- Highest AVG : -")
    if p99_best:
        print(f"- Highest P99 : {p99_best[0]} = {p99_best[1]:,.2f} ms")
    else:
        print("- Highest P99 : -")

    # Clock-Skew Warnung
    skew_metrics = [name for (name, _, _) in METRICS if negatives[name] > 0]
    if skew_metrics:
        print("\nHinweis: Negative Deltas entdeckt (Clock-Skew / Timebase-Mismatch wahrscheinlich) bei:")
        for n in skew_metrics:
            print(f"  - {n}: neg={negatives[n]}")

    # -------- NEW: Unaccounted E2E gap (avg) --------
    # This helps confirm that the multi-second E2E is dominated by IoT->Edge waiting/queueing.
    name_e2e = "E2E wall (iot_capture -> iot_alarm_received)"
    name_iot_edge = "IoT->Edge wait/transport wall (iot_capture -> edge_received)"
    name_edge_prep = "Edge preprocess wall (edge_received -> edge_filtered)"
    name_edge_cloud = "Edge->Cloud transport wall (edge_sent -> cloud_received)"
    name_cloud_q = "Cloud queue-ish wall (cloud_received -> ml_request_start)"
    name_ml = "ML service wall (ml_request_start -> ml_request_end)"
    name_cloud_pub = "Cloud decide/publish wall (cloud_decision -> alarm_published)"
    name_cloud_iot = "Cloud->IoT alert wall (alarm_published -> iot_alarm_received)"

    e2e = avg(values.get(name_e2e, []))
    iot_edge = avg(values.get(name_iot_edge, []))
    edge_prep = avg(values.get(name_edge_prep, []))
    edge_cloud = avg(values.get(name_edge_cloud, []))
    cloud_q = avg(values.get(name_cloud_q, []))
    ml = avg(values.get(name_ml, []))
    cloud_pub = avg(values.get(name_cloud_pub, []))
    cloud_iot = avg(values.get(name_cloud_iot, []))

    parts = [iot_edge, edge_prep, edge_cloud, cloud_q, ml, cloud_pub, cloud_iot]
    if e2e is not None and all(p is not None for p in parts):
        total_parts = sum(p for p in parts if p is not None)
        gap = e2e - total_parts
        print("\nE2E decomposition (avg):")
        print(f"- E2E avg:                 {e2e:,.2f} ms")
        print(f"- Sum(measured parts) avg: {total_parts:,.2f} ms")
        print(f"- Unaccounted gap avg:     {gap:,.2f} ms")
        if iot_edge is not None:
            share = (iot_edge / e2e) * 100.0 if e2e > 0 else 0.0
            print(f"- IoT->Edge share of E2E:  {share:,.2f} %")
    else:
        print("\nE2E decomposition (avg): skipped (missing one or more required metrics).")

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_differences.py <file1.jsonl> [file2.jsonl ...]")
        sys.exit(1)

    for p in sys.argv[1:]:
        analyze(Path(p))

if __name__ == "__main__":
    main()
