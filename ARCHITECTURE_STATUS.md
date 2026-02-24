# ARCHITECTURE_STATUS

## Projektziel
ai.pagesmaker.com als kontrollierter Agent-Host.

## Aktueller technischer Stand
- Containerisiertes Multi-Service Setup auf Docker Compose.
- Control-Service als zentrale Steuerung/Operatorkonsole.
- Orchestrator/Backend als Ausführungs- und Zustandsservice.

## Docker Compose Setup
- Services: `control`, `backend`, optional `ollama`.
- Shared Volume für SQLite-Daten (`/data`).

## FastAPI + Jinja2 + HTMX
- FastAPI als API- und UI-Server.
- Jinja2 für serverseitiges Rendering.
- HTMX für UI-Interaktionen ohne Voll-Reload.

## SQLite
- Shared SQLite-Datenbank.
- Control nutzt `control_*` Tabellen.
- Orchestrator nutzt eigene Tabellen.

## Caddy HTTPS
- TLS-Termination über Caddy vor den Services.

## GitHub CI/CD
- CI für Smoke/Qualitätstests.
- CD über Merge + Deploy-Workflow.

## Ollama lokal (qwen2.5:3b)
- Standard-LLM lokal via Ollama.
- Modell: `qwen2.5:3b`.

## Codex CLI via OAuth
- Codex CLI Zugriff über OAuth.

## Aktueller Projektphasenstand
- Phase 7 aktiv.

## Was funktioniert stabil
- Control UI und Auth-Flow.
- Runs/Events/Artifacts Persistenz.
- Smoke/Release/Rollback Skripte.

## Bekannte offene Punkte
- CI Smoke-Workflow final in Repo committen.
- Weitere Observability-Verbesserungen.

## Nächste Phase
- Hardening der Deploy-Gates und Runbooks.
- Erweiterte Monitoring-Checks.

## Guardrail-Prinzip
- Keine autonomen Root-Aktionen ohne Guard.
- Änderungen streng begrenzt und auditierbar.

## Guard Enforcement in Orchestrator
- Write-Flow im Orchestrator wendet Patches via `git apply` an und staged die Änderungen.
- Vor jedem Commit wird `python3 -m guard.cli pre-commit` im Repo-Root ausgeführt.
- Commits passieren nur bei Guard-OK; Fehler werden als Blocker behandelt.
- Nach dem Commit läuft `python3 -m guard.cli pre-pr` als Gate für PR-Erstellung.
- PR-Preparation ist aktuell ein Stub mit klarer Schnittstelle für spätere GitHub-Integration.
- Guard nutzt ausschließlich die bestehende `autonomy.yml` (version 1) als Policy-Quelle.
