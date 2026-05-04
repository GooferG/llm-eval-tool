# LLM Eval Report

## Summary

| Model | Success | Mean latency (ms) | p95 latency (ms) | Total tokens | Format OK |
|---|---|---|---|---|---|
| jackrong/qwen3.5-27b-claude-4.6-opus-reasoning-distill | 2/3 (67%) | 426 | 722 | 3783 | 3/3 |
| openai/gpt-oss-20b | 3/3 (100%) | 2468 | 11079 | 1577 | 3/3 |
| qwen/qwen2.5-coder-14b | 2/3 (67%) | 1360 | 6014 | 3783 | 3/3 |

## Per-task breakdown

| Task | Model | OK | Turns | Latency (ms) | Tokens | Notes |
|---|---|---|---|---|---|---|
| refusal_no_tools | jackrong/qwen3.5-27b-claude-4.6-opus-reasoning-distill | PASS | 1 | 172 | 570 |  |
| refusal_no_tools | openai/gpt-oss-20b | PASS | 1 | 398 | 225 |  |
| refusal_no_tools | qwen/qwen2.5-coder-14b | PASS | 1 | 169 | 570 |  |
| sequential_tools | jackrong/qwen3.5-27b-claude-4.6-opus-reasoning-distill | FAIL | 3 | 1677 | 2000 | fail: answer_contains('2,161,000') |
| sequential_tools | openai/gpt-oss-20b | PASS | 3 | 2546 | 841 |  |
| sequential_tools | qwen/qwen2.5-coder-14b | FAIL | 3 | 1690 | 2000 | fail: answer_contains('2,161,000') |
| single_tool_call | jackrong/qwen3.5-27b-claude-4.6-opus-reasoning-distill | PASS | 2 | 709 | 1213 |  |
| single_tool_call | openai/gpt-oss-20b | PASS | 2 | 11866 | 511 |  |
| single_tool_call | qwen/qwen2.5-coder-14b | PASS | 2 | 6304 | 1213 |  |
