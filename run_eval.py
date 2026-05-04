"""Entry point. Run with: python run_eval.py
Optional: --config path/to/config.yaml --out path/to/report.md
         --skip-warmup        skip the per-model warmup pass
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

from eval.adapters import LMStudioAdapter
from eval.grader import grade
from eval.report import generate
from eval.runner import run_task


def load_tasks(tasks_dir):
    tasks = []
    for f in sorted(Path(tasks_dir).glob("*.yaml")):
        t = yaml.safe_load(f.read_text(encoding="utf-8"))
        t.setdefault("id", f.stem)
        tasks.append(t)
    return tasks


def serialize_run(r):
    return {
        "model": r["model"],
        "task_id": r["task_id"],
        "grade": r["grade"],
        "completed": r["run"].completed,
        "error": r["run"].error,
        "final_text": r["run"].final_text,
        "served_models": list({t.served_model for t in r["run"].turns if t.served_model}),
        "turns": [
            {
                "text": t.text,
                "tool_calls": t.tool_calls,
                "latency_ms": t.latency_ms,
                "prompt_tokens": t.prompt_tokens,
                "completion_tokens": t.completion_tokens,
                "finish_reason": t.finish_reason,
                "served_model": t.served_model,
                "error": t.error,
            }
            for t in r["run"].turns
        ],
    }


def preflight(adapter, requested_models):
    """Check LM Studio is reachable and report any model-ID mismatches."""
    print("Pre-flight: checking LM Studio...")
    available = adapter.list_models()
    if isinstance(available, dict) and "error" in available:
        print(f"  ERROR: cannot reach LM Studio: {available['error']}", file=sys.stderr)
        print("  Start LM Studio's server (Developer tab -> Start Server, port 1234).", file=sys.stderr)
        sys.exit(1)

    print(f"  LM Studio reports {len(available)} model(s):")
    for m in available:
        print(f"    - {m}")

    missing = [m for m in requested_models if m not in available]
    if missing:
        print("\n  WARNING: the following models in config.yaml are NOT in LM Studio's model list:", file=sys.stderr)
        for m in missing:
            print(f"    - {m}", file=sys.stderr)
        print("  LM Studio may auto-load them via JIT, or it may silently route to a different model.", file=sys.stderr)
        print("  Check Developer tab -> Settings -> 'Just-In-Time Model Loading'.\n", file=sys.stderr)
    else:
        print("  All requested models present.\n")


def warmup(adapter, models):
    """Force-load each model. Catches load errors before the timed eval starts."""
    print("Warmup: forcing model load for steady-state latency...")
    for m in models:
        print(f"  {m}...", end=" ", flush=True)
        result = adapter.warmup(m)
        if result.error:
            print(f"FAILED [{result.error[:80]}]")
        else:
            served = result.served_model
            mismatch = f"  !! served by {served!r}" if served and served != m else ""
            print(f"loaded in {result.latency_ms:.0f} ms{mismatch}")
    print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--out", default="results/report.md")
    parser.add_argument("--skip-warmup", action="store_true")
    args = parser.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    adapter = LMStudioAdapter(base_url=cfg.get("base_url", "http://localhost:1234/v1"))
    tasks = load_tasks(cfg.get("tasks_dir", "tasks"))
    models = cfg["models"]

    if not tasks:
        print("No tasks found.", file=sys.stderr)
        sys.exit(1)

    preflight(adapter, models)
    if not args.skip_warmup:
        warmup(adapter, models)

    print(f"Running {len(tasks)} tasks x {len(models)} models = {len(tasks) * len(models)} runs\n")

    results = []
    for model in models:
        print(f"=== {model} ===")
        for task in tasks:
            print(f"  {task['id']}...", end=" ", flush=True)
            run = run_task(adapter, model, task)
            g = grade(task, run)
            results.append({"model": model, "task_id": task["id"], "run": run, "grade": g})

            served = {t.served_model for t in run.turns if t.served_model}
            mismatch = served and not any(s == model for s in served)

            mark = "PASS" if g["success"] else "FAIL"
            extras = []
            if run.error:
                extras.append(run.error[:60])
            elif not g["success"]:
                fails = [c["detail"] for c in g["checks"] if not c["ok"]]
                if fails:
                    extras.append(fails[0])
            if mismatch:
                extras.append(f"served by {sorted(served)}")
            extra_str = f"  [{'; '.join(extras)}]" if extras else ""
            print(f"{mark}{extra_str}")
        print()

    # Detect cross-model output collisions (same final_text across different models)
    by_text = {}
    for r in results:
        key = (r["task_id"], r["run"].final_text or "")
        by_text.setdefault(key, []).append(r["model"])
    collisions = [(k, ms) for k, ms in by_text.items() if len({m for m in ms}) > 1 and k[1]]
    if collisions:
        print("WARNING: identical final answers across different models (likely served by same loaded model):")
        for (task_id, _text), ms in collisions:
            print(f"  task {task_id}: {sorted(set(ms))}")
        print()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(generate(results), encoding="utf-8")
    print(f"Report:      {out}")

    raw = out.with_suffix(".json")
    raw.write_text(
        json.dumps([serialize_run(r) for r in results], indent=2, default=str),
        encoding="utf-8",
    )
    print(f"Raw results: {raw}")


if __name__ == "__main__":
    main()
