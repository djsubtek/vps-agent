# SYSTEM_CONTEXT

## Server
- Hostinger KVM2
- Ubuntu 24.04
- Nur `python3` verfügbar

## Repo-Pfad
- `/opt/vps-agent`

## Domain
- `ai.pagesmaker.com`

## Routing
- `/control` separater Service

## Datenbank
- Shared SQLite, separate `control_*` Tabellen
- `conn.row_factory = sqlite3.Row` darf niemals entfernt werden

## LLM Architektur
- Default lokal via Ollama
- API-Eskalation nur kontrolliert

## Deployment Flow
- Branch → PR → CI → Merge → Deploy

## Sicherheitsprinzip
- Keine autonomen Root-Aktionen ohne Guard
- Budget- und File-Change-Limits vorgesehen

## Zielarchitektur Phase 7
- Stabiler Smoke-Test als CI/Deploy-Gate
- Reproduzierbare Release- und Rollback-Flows
- Klare Observability- und Guardrail-Strukturen
