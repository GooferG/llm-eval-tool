"""Agent loop: send prompt, execute tool calls, feed results back, repeat."""

import json
from dataclasses import dataclass, field

from . import tools


@dataclass
class TaskRun:
    model: str
    task_id: str
    turns: list = field(default_factory=list)  # list[TurnResult]
    final_text: str | None = None
    completed: bool = False
    error: str | None = None


def run_task(adapter, model, task):
    messages = []
    if "system" in task:
        messages.append({"role": "system", "content": task["system"]})
    messages.append({"role": "user", "content": task["prompt"]})

    run = TaskRun(model=model, task_id=task["id"])
    max_turns = task.get("max_turns", 5)
    tool_schemas = tools.TOOL_SCHEMAS if task.get("tools_enabled", True) else None

    for _ in range(max_turns):
        result = adapter.chat(model, messages, tools=tool_schemas)
        run.turns.append(result)

        if result.error:
            run.error = result.error
            return run

        if result.tool_calls:
            messages.append({
                "role": "assistant",
                "content": result.text or "",
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["args"]),
                        },
                    }
                    for tc in result.tool_calls
                ],
            })
            for tc in result.tool_calls:
                output = tools.execute(tc["name"], tc["args"])
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(output),
                })
        else:
            run.final_text = result.text
            run.completed = True
            return run

    return run  # exhausted turns without final answer
