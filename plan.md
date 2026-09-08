# 📋 BUILD PLAN — DIRECTOR'S CUT

> **⚠️ READ THIS FIRST IF YOU ARE AN AGENT (CLINE/GEMINI/CLAUDE) RESUMING WORK.**
> This file is the single source of truth for build progress. Follow the "Resume Protocol" in §1 before doing anything.

---

## 1. Resume Protocol (for agents)

1. **Read this whole file.** All state lives in the task table (§4) and the Blocker Log (§6).
2. **Trust but verify**: every completed task `[x]` has a **Verify command**. Re-run the verify commands for the last 2–3 completed tasks to confirm state actually exists on disk/in the cloud. Do NOT skip re-verification — a previous session may have died mid-task.
3. **Find the first `[ ]` (unchecked) task** in dependency order and execute **only that task** (plus its verification).
4. On completion: mark `[x]`, update "Last completed" in §5, commit with message `task T<x.y>: <short desc>`, then proceed to the next task.
5. If a task fails: do NOT mark it done. Log the failure in §6 (Blocker Log) with the error and a suggested fix, commit, and stop if blocked.
6. **Never re-do a verified task.** Never invent state that isn't verified.

**Status legend**: `[ ]` not started · `[~]` in progress (see Blocker Log) · `[x]` done & verified · `[-]` skipped (reason in Blocker Log)

**Environment facts** (fill/update as discovered):
- OS: macOS · Working dir: `/Users/sahil/Desktop/HACKATHON/director-cut`
- Repo: git-initialized, LICENSE committed (MIT)
- GCP project: `_SET_ME_` · Region: `us-central1` (set in `.env`, see T0.2)

---

## 2. Phase Overview

| Phase | Name | Goal | Tasks |
|---|---|---|---|
| 0 | Bootstrap | Env, secrets, project scaffolding | T0.1–T0.5 |
| 1 | Broadcast Simulator | Mock encoder/CDN + metrics/logs + control API | T1.1–T1.5 |
| 2 | Grafana + MCP | Dashboards, alert rules, Grafana MCP wired & verified | T2.1–T2.4 |
| 3 | Agent Crew (ADK) | All 6 agents, tools, session state, local run | T3.1–T3.7 |
| 4 | Governance Layer | IAM policy tiers, forced authz, blocked path | T4.1–T4.3 |
| 5 | Cloud Integration | BigQuery post-mortems, runbook RAG, Cloud Tasks | T5.1–T5.3 |
| 6 | Deploy & Demo | Agent Engine deploy, Cloud Run UI, video, submission | T6.1–T6.5 |

---

## 3. Target Repo Structure

```
director-cut/
├── README.md                  # done
├── plan.md                    # done (this file)
├── LICENSE                    # done (MIT)
├── .env.example               # T0.2
├── requirements.txt           # T0.3
├── simulator/
│   ├── docker-compose.yml     # T1.1 (prom, loki, grafana, workers, control-api)
│   ├── prometheus/prometheus.yml
│   ├── loki/loki-config.yml
│   ├── grafana/provisioning/  # datasources + dashboards + alert rules
│   ├── workers/encoder.py     # T1.2
│   ├── workers/cdn.py         # T1.2
│   ├── control_api/main.py    # T1.3 (FastAPI: /requeue /drain /flip-cdn /inject-failure)
│   └── scenarios/failures.py  # T1.4 (scripted failure injections)
├── mcp/
│   └── grafana_mcp_config.json# T2.3
├── agents/
│   ├── director_agent/
│   │   ├── agent.py           # T3.1 root LlmAgent + sub_agents
│   │   ├── sub_agents/
│   │   │   ├── sensor_agent.py        # T3.2
│   │   │   ├── root_cause_agent.py    # T3.3
│   │   │   ├── remediation_agent.py   # T3.4 + T4.2
│   │   │   └── escalation_agent.py    # T4.3
│   │   ├── tools/
│   │   │   ├── grafana_tools.py       # T3.5 (MCP toolkit wiring)
│   │   │   ├── policy_tools.py        # T4.1 (check_authorization)
│   │   │   ├── remediation_tools.py   # T3.6 (execute via Cloud Tasks)
│   │   │   └── rag_tools.py           # T5.2 (search_runbooks)
│   │   └── prompts.py
│   └── deployment.py          # T6.1 (Agent Engine)
├── policy/
│   └── iam_policy.yaml        # T4.1 (tier catalog)
├── ui/
│   ├── main.py                # T6.2 (Cloud Run war-room UI)
│   └── templates/
├── tests/
│   ├── test_simulator.py      # T1.5
│   ├── test_policy.py         # T4.1
│   └── e2e_demo.py            # T6.3 (scripted golden + blocked path)
└── docs/
    └── architecture.md        # optional polish
```

## 4. Task Tracker

> Agents: update the Status column in place. Only mark `[x]` after the Verify command passes.

### Phase 0 — Bootstrap
| ID | Task | Files | Depends | Status | Verify command |
|---|---|---|---|---|---|
| T0.1 | Create scaffolding dirs + `.gitignore` (`.env`, `__pycache__`, `.venv`) | dirs above | — | `[x]` | `ls agents/director_agent tools 2>/dev/null; cat .gitignore` |
| T0.2 | Create `.env.example` + load `.env` (GCP_PROJECT_ID, REGION, GRAFANA_URL, GRAFANA_SA_TOKEN, GOOGLE_API_KEY) | `.env.example` | T0.1 | `[x]` | `grep -c "GCP_PROJECT_ID" .env.example` |
| T0.3 | `requirements.txt`: `google-cloud-aiplatform[agent_engines,adk]>=1.101.0`, `fastapi`, `uvicorn`, `requests`, `prometheus-client`, `mcp`, `pyyaml`, `pytest` | `requirements.txt` | T0.1 | `[x]` | `pip install -r requirements.txt && python -c "import google.adk"` |
| T0.4 | GCP setup: enable APIs (aiplatform, run, bigquery, cloudtasks, secretmanager, discoveryengine); create service account `director-cut-agent`; grant roles; document in `docs/gcp-setup.md` | `docs/gcp-setup.md` | T0.2 | `[x]` | `gcloud services list --enabled \| grep aiplatform` |
| T0.5 | Initial git commit of scaffolding | — | T0.1 | `[x]` | `git log --oneline \| head -3` |

### Phase 1 — Broadcast Simulator
| ID | Task | Files | Depends | Status | Verify command |
|---|---|---|---|---|---|
| T1.1 | `docker-compose.yml`: Prometheus, Loki, Grafana (provisioned datasources), control-api, 3 encoder workers + 2 cdn workers | `simulator/docker-compose.yml` | T0.3 | `[x]` | `docker compose -f simulator/docker-compose.yml up -d && docker compose -f simulator/docker-compose.yml ps` |
| T1.2 | Workers: emit `frames_dropped`, `encode_latency_seconds`, `cdn_p99_latency_ms`, `buffer_ratio` to Prometheus push endpoint + structured JSON logs to Loki; healthy baseline behavior | `simulator/workers/*` | T1.1 | `[x]` | `curl -s http://localhost:9090/api/v1/query?query=frames_dropped_total \| grep result` |
| T1.3 | Control API (FastAPI, :8080): `POST /inject-failure/{scenario}`, `POST /requeue/{node}`, `POST /drain/{node}`, `POST /flip-cdn`, `GET /health` — mutations flip worker behavior | `simulator/control_api/main.py` | T1.1 | `[x]` | `curl -s localhost:8080/health` |
| T1.4 | Failure scenarios: `encoder_frame_drop` (single node, Tier-1) and `cdn_multi_region` (global, Tier-3 blocked) — deterministic, scripted | `simulator/scenarios/failures.py` | T1.2 | `[x]` | `curl -X POST localhost:8080/inject-failure/encoder_frame_drop` then Prom query shows spike |
| T1.5 | Grafana provisioning: dashboard JSON (4 panels) + alert rule `encoder_frame_drop` (fires when frames_dropped rate > threshold 30s) + `cdn_multi_region_latency` | `simulator/grafana/provisioning/*` | T1.2 | `[x]` | Grafana UI :3000 shows dashboard + 2 alert rules in "Firing" after injection |
| T1.6 | `tests/test_simulator.py`: smoke tests (health, inject → metric spike → requeue → recovery) | `tests/test_simulator.py` | T1.4 | `[x]` | `pytest tests/test_simulator.py -v` |

### Phase 2 — Grafana MCP Integration (PARTNER PROOF)
| ID | Task | Files | Depends | Status | Verify command |
|---|---|---|---|---|---|
| T2.1 | Run Grafana MCP server (docker, `mcp/grafana-mcp`) pointed at local Grafana with service-account token in Secret Manager | `mcp/grafana_mcp_config.json` | T1.5, T0.4 | `[ ]` | MCP tool call `list_alert_rules` returns the 2 rules |
| T2.2 | Write `grafana_tools.py` wrapping MCP toolkit for ADK (`McpToolset`): expose query_prometheus, query_loki_logs, list_alert_rules, get_alert_status, write_annotation | `agents/director_agent/tools/grafana_tools.py` | T2.1 | `[ ]` | `python -c "from agents.director_agent.tools.grafana_tools import get_grafana_toolset; print(len(get_grafana_toolset()))"` |
| T2.3 | Manual MCP round-trip test script proving runtime Grafana calls (this is the "imported and called in code" evidence — screenshot for Devpost) | `tests/test_grafana_mcp.py` | T2.2 | `[ ]` | `pytest tests/test_grafana_mcp.py -v` |
| T2.4 | Commit + push Phase 1–2 | — | T2.3 | `[ ]` | `git log --oneline -1` |

### Phase 3 — Agent Crew (ADK)
| ID | Task | Files | Depends | Status | Verify command |
|---|---|---|---|---|---|
| T3.1 | Director root agent: `LlmAgent` with 4 sub-agents, deterministic instruction pipeline in `prompts.py`, session state keys: `incident_report`, `root_cause_report`, `authz_decision`, `ticket` | `agents/director_agent/agent.py`, `prompts.py` | T2.2 | `[ ]` | `adk web agents/` loads; chat "status" responds |
| T3.2 | Sensor Agent: sub-agent using grafana MCP tools + `get_incident_context` python tool; writes `IncidentReport` dict to state | `sub_agents/sensor_agent.py` | T3.1 | `[ ]` | adk web: inject failure → state contains `incident_report` |
| T3.3 | Root-Cause Agent: sub-agent with Loki/Prom range-query tools + placeholder `search_runbooks` (stub until T5.2); writes `RootCauseReport` | `sub_agents/root_cause_agent.py` | T3.1 | `[ ]` | adk web: after sensor step, state has `root_cause_report` with evidence list |
| T3.4 | Remediation Agent: sub-agent with `check_authorization` + `execute_remediation` + `write_grafana_annotation`; remediation catalog is a fixed enum in `remediation_tools.py` | `sub_agents/remediation_agent.py`, `tools/remediation_tools.py` | T3.1 | `[ ]` | adk web: forced authz call appears in trace before any execution |
| T3.5 | Wire end-to-end local golden path: inject → detect → diagnose → (stub authz APPROVED) → requeue → recovery → annotation | `tests/e2e_local.py` | T3.2–T3.4 | `[ ]` | `python tests/e2e_local.py` exits 0, metric recovers |
| T3.6 | Commit + push Phase 3 | — | T3.5 | `[ ]` | `git log --oneline -1` |

### Phase 4 — Governance Layer (the money moment)
| ID | Task | Files | Depends | Status | Verify command |
|---|---|---|---|---|---|
| T4.1 | `policy/iam_policy.yaml`: remediation catalog with tiers (T1 auto, T2 approve+notify, T3 block) + `policy_tools.check_authorization` pure-Python evaluator (no LLM) + unit tests | `policy/iam_policy.yaml`, `tools/policy_tools.py`, `tests/test_policy.py` | T3.4 | `[ ]` | `pytest tests/test_policy.py -v` |
| T4.2 | Hook Studio Head gate into Remediation Agent: forced `check_authorization` before `execute_remediation`; BLOCKED path routes to escalation | update `remediation_agent.py` | T4.1 | `[ ]` | adk web: propose GLOBAL_CDN_FLIP → trace shows BLOCKED |
| T4.3 | Escalation Agent: `create_incident_ticket` tool → writes pre-filled ticket JSON to `tickets/` + HTTP webhook stub; blocked-path e2e test | `sub_agents/escalation_agent.py`, `tests/e2e_blocked.py` | T4.2 | `[ ]` | `python tests/e2e_blocked.py` produces ticket JSON with block reason |
| T4.4 | Commit + push Phase 4 | — | T4.3 | `[ ]` | `git log --oneline -1` |

### Phase 5 — Cloud Integration
| ID | Task | Files | Depends | Status | Verify command |
|---|---|---|---|---|---|
| T5.1 | BigQuery dataset `director_cut`, table `post_mortems`; tool `write_post_mortem` called by Director after each incident | `tools/bigquery_tools.py` | T0.4, T3.5 | `[ ]` | `bq query "SELECT count(*) FROM director_cut.post_mortems"` after a run |
| T5.2 | Runbook RAG: seed `docs/runbooks/*.md` (5 docs incl. "frame drop loop" playbook), create Vertex AI Search data store, implement `search_runbooks` tool replacing T3.3 stub | `docs/runbooks/`, `tools/rag_tools.py` | T0.4 | `[ ]` | `pytest tests/test_rag.py` returns frame-drop runbook |
| T5.3 | Cloud Tasks queue → simulator control API (replace direct HTTP calls); agent SA has minimal IAM roles | update `remediation_tools.py` | T3.4, T0.4 | `[ ]` | inject → task executes → control API logs show Cloud Tasks origin |
| T5.4 | Commit + push Phase 5 | — | T5.3 | `[ ]` | `git log --oneline -1` |

### Phase 6 — Deploy & Demo
| ID | Task | Files | Depends | Status | Verify command |
|---|---|---|---|---|---|
| T6.1 | Deploy ADK agent to Vertex AI Agent Engine (`agents/deployment.py`); store remote agent ID in `.env` | `agents/deployment.py` | T5.x | `[ ]` | `python agents/deployment.py --test "status"` returns live response |
| T6.2 | War-room UI on Cloud Run: incident timeline, agent reasoning trace, Grafana panel embeds, ticket queue with human "Approve fix" button | `ui/` | T6.1 | `[ ]` | `gcloud run services describe director-cut-ui` → open URL |
| T6.3 | Scripted e2e demo driver `tests/e2e_demo.py`: runs Scenario A then Scenario B with clean timing for recording | `tests/e2e_demo.py` | T6.2 | `[ ]` | run once locally against cloud agent, full green |
| T6.4 | Record 3-min demo video (beats in README §4), upload YouTube public | — | T6.3 | `[ ]` | URL in README §6 checklist |
| T6.5 | Final: README checklist complete, repo public, Devpost form (Grafana Labs track) submitted | — | T6.4 | `[ ]` | manual review of README §6 |

---

## 5. Progress Snapshot (update after every task)

- **Last completed task**: **T1.5** — Grafana dashboard + 2 alert rules provisioned, both reach Firing (verified 2026-09-08)
- **Next task to execute**: **T1.6** (simulator smoke tests)
- **Last verified by (model/session)**: this session (Cline, 2026-09-08)
- **Build started**: 2026-09-08

---

## 6. Blocker Log (append-only; never delete entries)

| Date | Task | Error / Blocker | Suggested fix | Status |
|---|---|---|---|---|
| _— | _— | _— | _— | _— |

---

## 7. Decisions Log (architecture choices agents must respect)

1. **Grafana MCP is the only observability access path** for agents — no direct Prometheus/Loki HTTP calls from agent code (keeps partner integration load-bearing).
2. **`check_authorization` is a forced function call** — must appear in every remediation trace before execution. Never bypass.
3. **Remediation catalog is a fixed enum** in `remediation_tools.py` / `iam_policy.yaml`. Agents select, never invent.
4. **Studio Head gate is pure Python** (deterministic), not an LLM call.
5. **Simulator first, cloud second** — everything must work locally via docker-compose before cloud integration.
6. All secrets via Secret Manager / `.env` (git-ignored). Never commit tokens.

## 8. Time-boxed Fallbacks

If running low on time/credits, cut in this order (keep demo intact):
1. Cut T5.3 (Cloud Tasks) → keep direct HTTP to control API.
2. Cut T6.2 UI polish → use `adk web` dev UI + Grafana screen-share for the video.
3. Cut T5.2 real RAG → keep stub runbook matcher (note it in README).
4. **Never cut**: T2.x (Grafana MCP runtime proof), T4.x (IAM gate + blocked path), T6.4 (video) — these are the win conditions.
