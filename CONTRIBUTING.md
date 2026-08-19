# Contributing to Berth-Scheduler

## Setup

```bash
pip install -e ".[dev]"
```

## Style

- `ruff check src tests` must pass.
- Type hints on public functions.

## Tests

- `pytest -q` must pass.
- New solver features need a head-to-head comparison test against FCFS.

## Scope

This is a scheduling *bench*, not a full terminal-operations system.
Contributions should stay within berth allocation + quay-crane assignment.
