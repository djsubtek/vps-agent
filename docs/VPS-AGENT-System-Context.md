# VPS-Agent / OpenClaw System Context

## Purpose

This document is the persistent technical briefing for the VPS-Agent and OpenClaw environment. It is intended to give any future engineer, agent, or LLM enough context to understand the system quickly, work safely, and continue development without rediscovering basic architectural decisions.

The environment is designed as an autonomous but controlled AI development platform running on a VPS. The goal is not only to chat with models, but to create an operational system that can plan, write code, review changes, run diagnostics, and later support controlled repository and deployment workflows.

The platform is centered around OpenClaw as orchestrator. OpenClaw acts as the operating layer for agents, tools, sessions, policies, and guardrails. Coding capability is delegated to Codex through the ACP runtime. The overall design principle is:

**Codex thinks, OpenClaw controls.**

This means model intelligence is externalized to the coding model, while execution, auditability, role separation, and safety remain within the OpenClaw system.

---

## High-Level Goals

The system exists to support a long-term autonomous developer environment with the following objectives:

1. Reliable multi-agent orchestration on a VPS
2. Controlled use of OpenAI models for planning and coding
3. Safe command execution with explicit allowlists
4. Persistent operational context that survives sessions
5. Debuggability and rollback safety
6. Later expansion into repository automation, testing, and deployment

This is not a toy setup. It is meant to become a stable, reusable engineering platform.

---

## Core System Architecture

At the highest level, the architecture consists of four layers.

### 1. Infrastructure Layer

The base system is a Linux VPS. OpenClaw runs inside Docker on this VPS. The repository for the broader agent system lives under `/opt/vps-agent`.

Core characteristics:

- VPS-based Linux environment
- Dockerized runtime
- Persistent repository and documentation
- Git-backed workflow
- Controlled reverse proxy and service architecture around the wider project

### 2. Orchestration Layer

OpenClaw is the orchestration engine. It is responsible for:

- handling agent sessions
- spawning subagents
- routing tasks
- exposing tools
- enforcing tool restrictions
- maintaining session history and execution structure

This is the layer that makes the environment agentic rather than just model-based.

### 3. Model Layer

The model layer uses OpenAI models. The routing goal is:

- non-coding tasks use a lower-cost general model such as `openai/gpt-5-mini`
- coding tasks use `openai/gpt-5-codex`

This separation is important for both cost and behavior. Planning and orchestration should remain lightweight unless more reasoning is needed. Coding should be delegated specifically to Codex.

### 4. Tooling / Execution Layer

The execution layer includes OpenClaw tools such as:

- `sessions_spawn`
- `sessions_history`
- `exec`
- filesystem or workspace access where enabled

This is the layer where the system turns from a conversational assistant into an operational engineering agent.

---

## Current Conceptual Diagram

```text
User
  ↓
OpenClaw Main Agent
  ↓
Task Routing / Planning
  ↓
Subagent Spawn (ACP Runtime)
  ↓
Developer / Codex
  ↓
QA / Review
  ↓
Release / Operational Gate
  ↓
Exec / Filesystem / Repo Actions
```

In the current stage, not all stages are fully enabled end-to-end, but this is the intended control flow.

---

## Design Principles

Several design principles define how changes should be made.

### Minimal Invasiveness

Changes should be as small as possible. The system should not be broadly refactored when a targeted fix is sufficient. Existing working behavior must be preserved.

### Backup Before Change

Before changing configuration, runtime settings, or policy files, always create a backup. Rollback instructions should always be available.

### Separation of Thinking and Acting

The model may generate plans and code, but execution should happen through OpenClaw tools, not through uncontrolled direct side paths.

### Safety Through Policy

The `exec` tool must remain constrained by explicit allowlists. Broad shell access should not be granted globally.

### Role Separation

Different agent roles should have distinct responsibilities. Planning, coding, review, and release should not collapse into one unrestricted agent.

### Persistent Context

Operational knowledge should live in repo documentation, not only in ephemeral chat history.

---

## Main Components in Detail

## OpenClaw Gateway

OpenClaw is the system entry point for agent orchestration. It manages sessions, subagent spawning, tools, runtime mappings, and policies.

OpenClaw is not merely a frontend to a model. Its value is in:

- structured delegation
- policy-controlled execution
- repeatable task flows
- inspectable session structure
- runtime abstraction

The gateway should remain the central control plane.

## ACP Runtime

The ACP runtime is used for spawned coding subagents. This runtime is the bridge between OpenClaw session orchestration and Codex execution.

Observed behavior indicates:

- non-coding routing can work independently of ACP
- coding subagents are spawned through ACP
- ACP runtime must be configured and enabled
- spawned subagent visibility and persistence require additional session policy support

This runtime is a critical part of the system. If ACP is missing or misconfigured, coding delegation fails even if OpenAI provider configuration exists.

## Codex

Codex is the coding engine. It should be used only through the OpenClaw architecture, not as an independent bypass path.

Correct usage:

```text
OpenClaw → ACP runtime → Codex → output → OpenClaw tools / sessions
```

Incorrect usage:

```text
Agent or script → direct Codex CLI or unmanaged model call
```

The first pattern preserves guardrails. The second weakens system architecture.

## Exec Tool

The `exec` tool enables command execution from agents. This is one of the most powerful parts of the system and must remain constrained.

Current intended policy model:

- basic diagnostic commands are allowed
- dangerous commands remain blocked
- later, operational commands can be enabled only for dedicated roles
- command access should prefer full path allowlists where possible

The `exec` layer is what enables real system diagnostics and eventually controlled DevOps operations.

---

## Model Routing Strategy

The routing strategy should remain explicit and intentional.

### Non-Coding

Use a smaller and cheaper model for:

- planning
- explanation
- orchestration
- structured summaries
- control logic

Suggested default:

- `openai/gpt-5-mini`

### Coding

Use Codex for:

- code generation
- refactoring
- implementation tasks
- code-aware transformations

Suggested coding model:

- `openai/gpt-5-codex`

### Optional Future Planning Tier

If planning becomes more complex, a higher-capability non-coding model can be introduced for orchestrator or QA tasks.

Potential split:

- Orchestrator: `openai/gpt-5`
- Developer: `openai/gpt-5-codex`
- QA: `openai/gpt-5`
- Release: `openai/gpt-5-mini`

This should only be introduced when there is enough operational value to justify cost.

---

## Agent Roles

The target architecture uses persistent roles. These roles should be stored in configuration and not simulated only through prompting.

## 1. Orchestrator

Role:

- receives the top-level request
- breaks the work into steps
- decides whether to delegate
- routes to coding, QA, or release paths
- enforces structured workflow

The orchestrator should not be the unrestricted do-everything agent. Its main job is planning and control.

## 2. Developer

Role:

- performs implementation tasks
- writes code
- suggests patches
- operates as the main coding subagent

This role should be backed by Codex through ACP runtime.

## 3. QA

Role:

- reviews code
- checks correctness
- proposes test cases
- identifies weak spots and regressions
- validates whether output is production-ready

This role should remain more conservative and ideally read-only.

## 4. Release

Role:

- determines readiness for merge or deploy
- checks operational impact
- enforces final restrictions before runtime changes
- eventually manages controlled git/docker actions

This role should be the only path toward broader operational actions.

---

## Target Multi-Agent Workflow

The target workflow should look like this:

```text
User Request
  ↓
Orchestrator
  ↓
Developer (Codex)
  ↓
QA
  ↓
Release Gate
  ↓
Optional Exec / Git / Docker / Deploy
```

This gives four benefits:

1. clear reasoning flow
2. better traceability
3. cleaner safety boundaries
4. future scalability for autonomous pipelines

---

## Current Technical Findings

The following points summarize the important technical observations from the setup process so far.

### Exec Works

The `exec` tool is operational. Commands such as `pwd`, `ls`, and some explicitly allowlisted commands run successfully.

### Exec Is Restricted by Allowlist

Commands outside the allowlist are denied with `allowlist miss`. This is correct behavior.

### Execution Context

Execution currently occurs as unprivileged user `node`. This is good from a security perspective.

### Non-Coding Routing Works

OpenClaw can handle non-coding tasks through the default model.

### Coding Spawn Works

Subagents can be spawned for coding through ACP runtime.

### Agent-to-Agent Visibility Required Explicit Enablement

Cross-agent access to history required explicit enabling. This means that spawned child output is not automatically available unless session policies permit it.

### Remaining Runtime-Side Issue

There has been evidence that spawned Codex child output may appear in logs but not be persisted correctly into the session history store. If confirmed, that is a runtime-layer issue rather than an infrastructure problem.

This distinction matters because it changes the next troubleshooting path.

---

## Important Paths

These paths are essential for operation and debugging.

### Repository

```text
/opt/vps-agent
```

This is the main project repository and should contain documentation and persistent context.

### Documentation

```text
/opt/vps-agent/docs
```

This should hold architecture docs, operational guides, test procedures, and role descriptions.

### OpenClaw Config Inside Container / Runtime Context

```text
~/.openclaw/openclaw.json
```

Depending on runtime and mount behavior, this may resolve inside the OpenClaw container environment.

### OpenClaw Workspace

```text
~/.openclaw/workspace
```

This is the workspace context for OpenClaw tasks.

### Docker Compose

```text
/opt/vps-agent/docker-compose.yml
```

This is the main compose entry point for restarting or controlling the OpenClaw service stack.

---

## Documentation Strategy

The system should keep its operational memory in the repository.

Recommended files:

- `docs/project-context.md`
- `docs/system-architecture.md`
- `docs/operations.md`
- `docs/testing.md`
- `docs/agent-roles.md`

### Why this matters

Without documentation:

- context is trapped in chat threads
- future models start nearly blind
- debugging repeats old work
- architectural intent is lost

With documentation:

- future LLMs can onboard quickly
- Codex can act with better context
- changes are reviewable and versioned
- architecture becomes durable

---

## Testing Strategy

Testing should proceed in layers, from safest to most integrated.

## 1. Smoke Tests

These verify the minimal operational chain.

Examples:

- spawn coding subagent with task `return READY`
- verify child session creation
- verify child output persistence
- verify visibility through session tools

## 2. Coding Tests

These verify the coding path itself.

Examples:

- generate `add(a, b)`
- generate two minimal tests
- verify visibility and syntactic plausibility

## 3. Role Tests

These validate role separation.

Examples:

- orchestrator produces a plan
- developer writes code
- QA reviews code
- release states deployment prerequisites

## 4. End-to-End Dry Runs

These validate the whole chain without making changes.

Examples:

- plan a tiny feature
- generate implementation through developer subagent
- pass output to QA
- pass QA result to release gate
- produce PASS/FAIL summary

## 5. Operational Tool Tests

Only after the above are stable, test operational capabilities such as:

- git status
- reading repo files
- dry-run docker commands

These should be tightly scoped and role-bound.

---

## Guardrails and Safety Rules

These rules should remain stable unless there is a strong reason to change them.

### Always Back Up Before Config Changes

Any modification to config should start with a timestamped backup.

### Prefer Read-Only First

When diagnosing, prefer read-only tools and commands first.

### Expand Tool Access in Phases

Do not enable broad tool powers all at once. Start with diagnostics, then role-specific operational commands, then later controlled deployment access.

### Use Full Paths in Allowlists

Where possible, allow exact binaries with full paths rather than loose shell command names.

### Keep Dangerous Commands Blocked

These should remain blocked unless there is a narrowly justified reason:

- `sudo`
- `systemctl`
- `kill`
- `pkill`
- `rm`
- `mv`
- `chmod`
- `chown`
- `ssh`
- `curl`
- `wget`

### Separate Main and Subagent Execution

If supported safely, subagents should be more isolated than the main agent.

---

## Recommended Roadmap

The next stages of system evolution should be deliberate.

## Phase 1. Stabilize Current Runtime

- ensure ACP runtime stays stable
- fix child output persistence if needed
- verify agent-to-agent visibility
- complete end-to-end dry-run testing

## Phase 2. Persist Roles

- create persistent orchestrator, developer, QA, and release roles
- verify role assignment and tool boundaries

## Phase 3. Expand Ops Tooling Carefully

- allow `git`, `jq`, and selected `docker` commands only for release or ops role
- keep main agent restricted

## Phase 4. Repo-Aware Workflows

- generate files in workspace
- review diffs
- validate repository state
- later commit and push through gated path

## Phase 5. Controlled Deployment Path

- dry-run deploy logic
- release approval steps
- rollback-aware execution

## Phase 6. Self-Improvement Loop

Longer term, the platform should support:

- bug discovery
- patch generation
- review
- test planning
- release gating

This would move the system from a helpful agent stack to a genuine autonomous engineering system.

---

## What Success Looks Like

The target end state is not merely “OpenClaw runs.” The target is a system where:

- OpenClaw reliably orchestrates work
- Codex handles implementation
- QA validates results
- Release controls operational changes
- commands execute under policy
- documentation gives durable memory
- each improvement is testable and reversible

At that point the stack becomes a dependable engineering platform instead of an experimental toolchain.

---

## Current Status Summary

At the time of writing, the environment has already achieved important milestones:

- OpenClaw is running in Docker
- basic `exec` command execution works
- command allowlist behavior is functioning
- ACP runtime can spawn coding subagents
- non-coding routing works
- architecture direction is correct

The main remaining technical focus is validating and, if necessary, fixing child session output persistence so that multi-agent workflows can be completed end-to-end.

That is an implementation maturity issue, not a conceptual architecture failure.

---

## Operating Philosophy for Future Changes

For all future work on this system, the following operating philosophy should apply:

1. understand first
2. verify second
3. change minimally
4. keep rollback ready
5. document every stable insight
6. only then expand capability

This principle is especially important in AI-driven systems, where it is easy to add power faster than control.

---

## Final Summary

This project is building a durable autonomous development environment on a VPS using OpenClaw as orchestrator and Codex as the coding engine. The architecture is intentionally layered, policy-driven, and designed for safe expansion.

The key architectural statement remains:

**OpenClaw is the operating system. Codex is the coding engine.**

As long as that separation is maintained, the system can grow into a powerful and reliable multi-agent engineering platform.
