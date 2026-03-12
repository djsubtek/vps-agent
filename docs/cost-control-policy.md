# Cost Control Policy (Operational)

Principles:
- Memory flush: after each completed task, keep only goal, result, changed files, next step.
- Stage-based execution: PLAN → BUILD → REVIEW → DONE; pass minimal context between stages.
- Diff-first: compute affected files and skip build if no relevant changes.
- Run limits: planning rounds ≤2, retries ≤1, subagent spawns ≤2.
- Minimal responses: STATUS / RESULT / NEXT only.
- Truncated tool output: limit lines returned from tools.
- Close child sessions after task completion.

Usage: keep this file updated in repo docs and enforce in Builder Mode runtime.
