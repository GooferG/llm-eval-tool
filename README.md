# LLM Eval Tool

Evaluation framework for testing LLMs on tool/function-calling tasks. Runs the same tasks across multiple models, grades results, and generates comparison reports.

## What it does

- Sends structured tasks to one or more models via LM Studio
- Executes tool calls in an agent loop until the model stops or hits `max_turns`
- Grades each run against configurable checks (right tool? correct args? expected answer?)
- Outputs a markdown summary table + raw JSON

## Requirements

- Python 3.x
- [LM Studio](https://lmstudio.ai) running locally on port `1234`
- At least one model loaded in LM Studio

```bash
pip install -r requirements.txt
```

## Usage

```bash
python run_eval.py
```

Configure models and task directory in `config.yaml`. Results are written to `results/`.

## Task types

| Type | Description |
| ---- | ----------- |
| Single tool call | Model must call one specific tool |
| Sequential tools | Multi-step reasoning across multiple tool calls |
| Refusal | Model should NOT call any tool |

## Output

- `results/report.md` — comparison table (success rate, latency p95, token counts)
- `results/report.json` — raw run data

## Adding tasks

Drop a YAML file in `tasks/`. Each task defines a prompt, `max_turns`, and a list of checks to validate the run.
