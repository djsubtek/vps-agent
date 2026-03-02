# AI Infrastructure Master Documentation
## Project: ai.pagesmaker.com

### Generated: 2026-03-01T17:34:30.040325 UTC

------------------------------------------------------------------------

# EXECUTIVE TECHNICAL SUMMARY

This document provides a full technical briefing of the AI
infrastructure running on the Hostinger KVM2 VPS.

It is designed to: - Fully brief another LLM system - Onboard a senior
DevOps engineer instantly - Provide rollback and recovery guarantees -
Document architecture decisions and failure modes

The system has previously been fully operational including: - OpenClaw
Gateway - OpenAI Provider - WebSocket pairing - Reverse proxy via
Caddy - Token authentication - CI/CD deployment

------------------------------------------------------------------------

# 1. SERVER ENVIRONMENT

## VPS

-   Provider: Hostinger
-   Plan: KVM2
-   RAM: 8GB
-   OS: Ubuntu 24.04
-   Docker: v2 (compose plugin)
-   Git enabled
-   Path of repository:

/opt/vps-agent

------------------------------------------------------------------------

# 2. CURRENT ARCHITECTURE OVERVIEW

Client ↓ Caddy (Reverse Proxy) ↓ OpenClaw Gateway (port 8080) ↓ OpenAI
API

Control UI: localhost:8082

------------------------------------------------------------------------

# 3. DOCKER COMPOSE ARCHITECTURE

Core services:

-   backend
-   control
-   openclaw
-   caddy

Ollama is currently removed in OpenAI-only mode.

------------------------------------------------------------------------

# 4. OPENCLAW GATEWAY CONFIGURATION

Startup command:

node dist/index.js gateway --bind lan --port 8080 --allow-unconfigured

Important constraints:

Valid bind values: - lan - loopback - tailnet - auto - custom

Invalid: - 0.0.0.0

------------------------------------------------------------------------

# 5. NETWORK DESIGN

## Internal Docker Network

Docker bridge network used. Service name resolution via Docker DNS.

openclaw reachable as: openclaw:8080

------------------------------------------------------------------------

# 6. PORT STRATEGY

8080 → Gateway (public via Caddy) 8082 → Control UI (localhost only)

------------------------------------------------------------------------

# 7. CADDY CONFIGURATION

Minimal working configuration:

:80 { reverse_proxy openclaw:8080 }

------------------------------------------------------------------------

# 8. ENVIRONMENT VARIABLES

OPENCLAW_PROVIDER=openai OPENCLAW_MODEL=gpt-5-mini
OPENCLAW_GATEWAY_TOKEN=`<secure>`{=html}
OPENCLAW_BASE_URL=https://ai.pagesmaker.com/

------------------------------------------------------------------------

# 9. HEALTH & VALIDATION

Standard validation sequence:

docker compose ps docker compose logs --tail=200 openclaw curl
http://127.0.0.1:8080/health docker compose exec caddy wget
http://openclaw:8080/health

------------------------------------------------------------------------

# 10. COMMON FAILURE MODES

## 1. 502 Bad Gateway

Cause: OpenClaw not listening on expected port.

## 2. Connection reset

Cause: Invalid bind or crash during startup.

## 3. Restart loop

Cause: Invalid CLI flag.

## 4. Token / Origin block

Cause: Mismatched base URL or missing token.

------------------------------------------------------------------------

# 11. ROLLBACK PROTOCOL

Before changes:

cp docker-compose.yml docker-compose.backup.\$(date +%s)

After change:

docker compose config

If broken:

mv docker-compose.backup.TIMESTAMP docker-compose.yml docker compose up
-d

------------------------------------------------------------------------

# 12. DEBUGGING METHODOLOGY

1.  Validate YAML
2.  Validate container status
3.  Validate internal port
4.  Validate docker network resolution
5.  Validate reverse proxy
6.  Validate provider

One change at a time.

------------------------------------------------------------------------

# 13. SECURITY MODEL

-   Token-based gateway access
-   Control UI local-only
-   Reverse proxy termination
-   No direct expose of 8082
-   TLS handled by Caddy

------------------------------------------------------------------------

# 14. CI/CD FLOW

GitHub repo: djsubtek/vps-agent

Deployment: - Push to main - GitHub Actions - SSH into VPS - docker
compose up -d

------------------------------------------------------------------------

# 15. TAILSCALE IMPACT ANALYSIS

Tailscale modifies network interfaces. OpenClaw bind mode must remain
compatible. Do not mix bind=lan with incorrect network assumptions.

------------------------------------------------------------------------

# 16. PROVIDER STRATEGY

Current: OpenAI (gpt-5-mini)

Future option: Switch provider via environment variable only. Do not
change architecture.

------------------------------------------------------------------------

# 17. LESSONS LEARNED

Primary instability causes were:

-   Simultaneous config edits
-   Port mismatch (18789 vs 8080)
-   Invalid bind argument
-   Config override conflicts
-   YAML corruption via regex edits

New rule: Single change, test, rollback capability.

------------------------------------------------------------------------

# 18. FULL SYSTEM TRANSFER PROMPT

You are working inside a Docker-based AI infrastructure running on
Ubuntu 24.04 at /opt/vps-agent.

OpenClaw is used as a gateway and runs:

node dist/index.js gateway --bind lan --port 8080 --allow-unconfigured

Reverse proxy handled by Caddy. Provider: OpenAI gpt-5-mini. Token
authentication enabled.

Work minimal-invasively. Always provide rollback instructions. Never
refactor working components.

------------------------------------------------------------------------

# 19. ADVANCED DEBUG PROMPT

Analyze this infrastructure like a senior DevOps engineer. Identify
misconfigurations without speculative changes. Provide only validated
modifications. Preserve operational state.

------------------------------------------------------------------------

# 20. FUTURE PHASES

Phase 6/7: - Autonomous UI - Agent role separation - Budget
enforcement - Controlled self-optimization

------------------------------------------------------------------------

# 21. OPERATIONAL RUNBOOK

Restart only OpenClaw: docker compose up -d --force-recreate openclaw

Full restart: docker compose down docker compose up -d

------------------------------------------------------------------------

# 22. RECOVERY PLAN

If complete failure:

1.  Restore last working compose
2.  Remove orphan containers
3.  Restart minimal OpenClaw only
4.  Validate health
5.  Add services incrementally

------------------------------------------------------------------------

# 23. SYSTEM STATE CHECKLIST

☐ Docker running ☐ Compose valid ☐ OpenClaw listening ☐ Health endpoint
reachable ☐ Caddy proxy working ☐ Token validated

------------------------------------------------------------------------

# 24. ARCHITECTURE GUARANTEE PRINCIPLES

-   Minimal complexity
-   Explicit ports
-   No hidden config overrides
-   Explicit environment variables
-   Deterministic startup commands

------------------------------------------------------------------------

# 25. CONCLUSION

The infrastructure is stable when:

-   OpenClaw binds correctly
-   Ports are aligned
-   Reverse proxy matches upstream
-   Provider configured cleanly
-   Changes are incremental

This document can be used to fully reconstruct, debug, or migrate the
entire system.

------------------------------------------------------------------------

END OF MASTER DOCUMENT
