"""Markdown report generator."""

import statistics


def _fmt(n, places=0):
    if n is None:
        return "-"
    return f"{n:.{places}f}"


def generate(results):
    """results: list of {model, task_id, run, grade}."""
    models = sorted({r["model"] for r in results})
    tasks = sorted({r["task_id"] for r in results})

    lines = ["# LLM Eval Report", ""]

    # ---- Summary table ----
    lines += [
        "## Summary",
        "",
        "| Model | Success | Mean latency (ms) | p95 latency (ms) | Total tokens | Format OK |",
        "|---|---|---|---|---|---|",
    ]
    for m in models:
        rs = [r for r in results if r["model"] == m]
        n = len(rs)
        succ = sum(1 for r in rs if r["grade"]["success"])
        latencies = [t.latency_ms for r in rs for t in r["run"].turns]
        mean_lat = statistics.mean(latencies) if latencies else 0
        p95_lat = (
            statistics.quantiles(latencies, n=20)[-1] if len(latencies) >= 20 else max(latencies, default=0)
        )
        total_tokens = sum(t.prompt_tokens + t.completion_tokens for r in rs for t in r["run"].turns)
        fmt_ok = sum(1 for r in rs if r["grade"]["format_ok"])
        lines.append(
            f"| {m} | {succ}/{n} ({succ / n:.0%}) | {_fmt(mean_lat)} | {_fmt(p95_lat)} | {total_tokens} | {fmt_ok}/{n} |"
        )

    # ---- Per-task breakdown ----
    lines += [
        "",
        "## Per-task breakdown",
        "",
        "| Task | Model | OK | Turns | Latency (ms) | Tokens | Notes |",
        "|---|---|---|---|---|---|---|",
    ]
    for t in tasks:
        for m in models:
            r = next((x for x in results if x["model"] == m and x["task_id"] == t), None)
            if not r:
                continue
            run, g = r["run"], r["grade"]
            success = "PASS" if g["success"] else "FAIL"
            turns = len(run.turns)
            total_lat = sum(turn.latency_ms for turn in run.turns)
            tokens = sum(turn.prompt_tokens + turn.completion_tokens for turn in run.turns)
            notes = []
            if run.error:
                notes.append(f"ERR: {run.error[:80]}")
            for c in g["checks"]:
                if not c["ok"]:
                    notes.append(f"fail: {c['detail']}")
            if g["parse_errors"]:
                notes.append(f"{g['parse_errors']} parse_error(s)")
            note_str = "; ".join(notes) if notes else ""
            lines.append(f"| {t} | {m} | {success} | {turns} | {_fmt(total_lat)} | {tokens} | {note_str} |")

    return "\n".join(lines) + "\n"
