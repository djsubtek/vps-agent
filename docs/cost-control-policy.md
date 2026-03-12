# Cost Control Policy for Builder Mode

Summary:
This policy reduces API usage and keeps autonomous runs lightweight by restricting memory, enforcing stage-based execution, performing diff-first checks, and setting conservative run limits.

Memory flush:
- After each completed task, retain only: goal, result, changed files, next step. Discard detailed interaction history before the next run.

Stage-based workflow:
- PLAN -> BUILD -> REVIEW -> DONE
- Pass minimal context between stages (only what's required for that stage).

Diff-first workflow:
- Before BUILD, compute a repo diff and list affected files.
- If no relevant changes, skip build stage.

Run limits:
- max planning rounds: 2
- max retries: 1
- max subagent spawns per task: 2
- If any limit is exceeded, stop and return short status only.
