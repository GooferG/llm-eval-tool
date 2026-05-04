"""Deterministic graders. Each task lists checks; all must pass for success."""


def grade(task, run):
    all_tool_calls = [tc for turn in run.turns for tc in turn.tool_calls]
    final = (run.final_text or "").lower()
    checks_results = []

    for check in task.get("checks", []):
        ctype = check["type"]
        ok = False
        detail = ""

        if ctype == "tool_called":
            ok = any(tc["name"] == check["tool"] for tc in all_tool_calls)
            detail = f"tool_called({check['tool']})"

        elif ctype == "tool_args_contains":
            target_tool = check["tool"]
            target_args = check["args"]
            for tc in all_tool_calls:
                if tc["name"] != target_tool:
                    continue
                if all(
                    str(tc["args"].get(k, "")).lower() == str(v).lower()
                    for k, v in target_args.items()
                ):
                    ok = True
                    break
            detail = f"tool_args_contains({target_tool}, {target_args})"

        elif ctype == "answer_contains":
            target = check["text"]
            if isinstance(target, list):
                ok = any(str(t).lower() in final for t in target)
                detail = f"answer_contains(any of {target!r})"
            else:
                ok = str(target).lower() in final
                detail = f"answer_contains({target!r})"

        elif ctype == "no_tool_calls":
            ok = len(all_tool_calls) == 0
            detail = "no_tool_calls"

        elif ctype == "tool_call_count":
            ok = len(all_tool_calls) == check["count"]
            detail = f"tool_call_count(={check['count']}, got {len(all_tool_calls)})"

        else:
            detail = f"UNKNOWN_CHECK({ctype})"

        checks_results.append({"type": ctype, "ok": ok, "detail": detail})

    parse_errors = sum(1 for tc in all_tool_calls if tc.get("parse_error"))
    success = run.error is None and all(c["ok"] for c in checks_results)

    return {
        "success": success,
        "checks": checks_results,
        "tool_calls_total": len(all_tool_calls),
        "parse_errors": parse_errors,
        "format_ok": parse_errors == 0,
        "completed": run.completed,
        "error": run.error,
    }
