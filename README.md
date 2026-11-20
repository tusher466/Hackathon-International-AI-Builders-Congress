# Factory Brain - Full-Stack AI Operations Layer for Connected Factory

**Merged project: Backend (FastAPI + LangGraph) + Frontend (React + Vite) serving as single deployable system.**

Backend ingests sensor streams (SECOM, TURBO, BOSCH), detects anomalies/degradation/defects, and hands alerts to a LangGraph multi-agent system (Monitor, Diagnosis [RAG], Planner, Action, Supervisor) that diagnoses root cause using RAG over technical manuals, plans response, generates repair instructions, and opens tickets. Every decision is explainable with reasoning trace and citations. High-risk actions require human approval.

Frontend is an industrial, flat, matte UI for connected factories that improves throughput and uptime through agentic orchestration and sensor ingestion.

## Merged Architecture Overview

```
Sensors (SECOM, TURBO, BOSCH) -> Stream Simulator -> Consumer -> Cleaner -> Ring Buffer + Timeseries DB
                                        |
                                   Feature Extractor (sliding window 30, PCA for SECOM)
                                        |
                            Detection: Anomaly (IF), RUL (RF), Defect (RF) -> AlertBuilder
                                        |
                                   Alert -> Agent Graph
                                        |
  Monitor -> Supervisor -> Diagnosis (RAG) -> Supervisor -> Planner -> Supervisor -> Action -> END
                                        |                 |                |
                                   Evidence         Plan + Impact    Ticket + Approval
                                                                        |
                                                                   EventBus -> WebSocket / Dashboard (React)
                                                                        |
                                                                   Metrics / Health
                                                                        |
                                                            FastAPI serves:
                                                            - /api/v1/* (REST)
                                                            - /ws/live + /api/v1/ws/live (WebSocket)
                                                            - /assets + /index.html (Frontend dist)
```

Full-stack serving:
- Backend FastAPI at `http://localhost:8000` serves both API (`/api/v1/*`) and frontend static files (`/assets/*`, `/index.html` SPA fallback) when `frontend/dist` or `Fontend/dist` exists.
- Frontend dev server (Vite) at `http://localhost:3000` proxies `/api` and `/ws` to backend for hot reload dev.
- Optional separate deployment via nginx (frontend Dockerfile) or merged single-port deployment.

## Folder Structure (Merged)

```
E:/Backend/
├── api/                  # FastAPI routes (machines, alerts, agents, control, extended: oee, bottlenecks, chat, audit-log, websocket)
├── agents/               # LangGraph agents: monitor, diagnosis, planner, action, supervisor, graph, llm, prompts
├── actions/              # Ticketing, approval, notifier
├── config/settings.py    # Pydantic settings (all env vars)
├── core/pipeline.py      # Main ingestion -> detection -> agent orchestration
├── ingestion/            # Schemas, cleaner, feature_extractor, stream_simulator, consumer
├── detection/            # Anomaly, RUL, Defect models, AlertBuilder
├── knowledge/            # Vector store (Chroma), retriever, ingest_docs
├── storage/              # SQLAlchemy models, repositories, timeseries ring buffer
├── data/manuals/         # 8 markdown manuals + failure_logs.jsonl
├── models/               # Trained *.joblib (anomaly, rul, defect, pca) + metrics.json
├── scripts/              # train_models.py, run_demo.py, inject_fault.py
├── tests/                # pytest tests
├── frontend/             # Merged frontend (proper name, React + Vite)
│   ├── src/
│   │   ├── api/client.js (auto-detects prod vs dev base URL, WS URL)
│   │   ├── api/endpoints.js (with fallback to mock)
│   │   ├── api/mock/ (mockData + mockServer with MockSocket)
│   │   ├── components/ (agents, alerts, audit, chat, common, machines, oee, pipeline, tickets, help)
│   │   ├── pages/ (CommandCenter, Machines, MachineDetail, AskFactory, AgentActions, Alerts, AlertDetail, Approvals, Tickets, Knowledge, Simulator, Impact, GuidedDemo, HowItWorks)
│   │   ├── hooks/ (useMachines, useAlerts, useLiveSocket, useOee, useBottlenecks, useChat, useAuditLog...)
│   │   ├── layout/ (AppShell, Sidebar, TopBar)
│   │   ├── store/liveStore.js (zustand-like live store)
│   │   └── utils/ (outcomes + format)
│   ├── dist/ (built frontend, served by backend)
│   ├── vite.config.js (proxy /api and /ws to backend)
│   ├── nginx.conf (for docker separate frontend)
│   ├── package.json
│   └── .env.example
├── Fontend/              # Legacy folder (kept for backward compat, same code as frontend)
├── Dockerfile.backend    # Backend docker (serves frontend dist if present)
├── Dockerfile.frontend   # Frontend docker (nginx serving dist + proxy)
├── docker-compose.yml    # Merged compose: mosquitto, backend (merged), frontend optional profile
├── Makefile              # Unified make targets for backend + frontend
├── requirements.txt
└── .env.example          # Backend env vars
```

## Quick Start - Full Stack (Single Command)

### Option 1: Without Docker (Recommended for quick start, merged single port 8000)

```bash
# Backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
make full-install           # installs backend pip + frontend npm
make train                  # generates models/*.joblib (synthetic if datasets missing)
make ingest-docs            # auto-ingest on startup if empty, but manual ensures count
make full-run               # builds frontend to frontend/dist + runs backend with reload, serves UI at http://localhost:8000

# Then:
# - UI: http://localhost:8000 (Command Center)
# - API: http://localhost:8000/api/v1/health
# - WS: ws://localhost:8000/ws/live (or ws://localhost:8000/api/v1/ws/live alias)
```

### Option 2: Frontend Dev + Backend Separate (Hot reload)

```bash
# Terminal 1 - Backend
make install && make train && make run
# Backend at http://localhost:8000

# Terminal 2 - Frontend
cd frontend
npm install
npm run dev
# Frontend at http://localhost:3000 with proxy to backend (vite.config.js proxy)
# It auto-detects dev mode and uses http://localhost:8000/api/v1 and ws://localhost:8000/ws/live
```

### Option 3: Docker Merged

```bash
# Merged deployment: backend serves frontend at :8000
docker-compose up backend mosquitto -d
# Build frontend first so backend has dist:
cd frontend && npm run build && cd ..
docker-compose up backend --build -d

# Visit http://localhost:8000

# Separate frontend + backend via nginx (frontend on :3000, backend on :8000)
docker-compose --profile separate-frontend up --build
# Frontend http://localhost:3000, backend http://localhost:8000
```

## Environment Variables

### Backend (.env.example at root)

| Variable | Default | Description |
|---|---|---|
| STREAM_BACKEND | memory | mqtt or memory queue fallback |
| SIM_RATE_HZ | 2.0 | Simulator replay rate |
| AUTO_START_STREAM | true | Start simulator on startup |
| MQTT_HOST | localhost | MQTT broker host |
| MQTT_PORT | 1883 | MQTT broker port |
| LLM_MODE | mock | mock or real (needs ANTHROPIC_API_KEY) |
| ANTHROPIC_API_KEY |  | Anthropic key for real LLM |
| LLM_MODEL | claude-3-5-sonnet-20241022 | Model name |
| DATABASE_URL | sqlite:///./data/factory_brain.db | SQLite URL |
| CHROMA_PERSIST_PATH | ./data/chroma | Chroma dir |
| EMBEDDING_MODEL | all-MiniLM-L6-v2 | sentence-transformers model |
| RING_BUFFER_SIZE | 500 | Last N readings per machine in memory |
| ANOMALY_THRESHOLD_* | 0.3,0.5,0.7,0.85 | Anomaly severity thresholds |
| RUL_CRITICAL,HIGH,MEDIUM | 20,50,100 | RUL thresholds |
| DEFECT_PROB_* | 0.3,0.5,0.7,0.85 | Defect prob thresholds |
| ALERT_COOLDOWN_READINGS | 10 | De-duplication cooldown |
| HEALTH_WEIGHT_* | 0.4,0.35,0.15,0.1 | Health score weights |
| MAX_CONCURRENT_AGENT_RUNS | 5 | Semaphore |
| MAX_AGENT_ITERATIONS | 8 | Supervisor max loops |
| RETRIEVAL_K | 5 | RAG chunks |
| API_KEY |  | Optional X-API-Key protection |
| CORS_ORIGINS | * | CORS |

### Frontend (frontend/.env.example)

| Variable | Default | Description |
|---|---|---|
| VITE_API_BASE_URL | http://localhost:8000/api/v1 | REST base. In prod merged use /api/v1 or auto-detect |
| VITE_WS_URL | ws://localhost:8000/ws/live | WS URL, supports both /ws/live and /api/v1/ws/live |
| VITE_API_KEY |  | Same as backend API_KEY if set |
| VITE_USE_MOCK | false | true = use mock when backend unreachable (demo), false = real only |

For production merged deployment, frontend client auto-detects:
- If VITE_API_BASE_URL not set and window.location.port is 3000 (vite dev) -> uses http://localhost:8000/api/v1
- Else -> uses `${window.location.origin}/api/v1` (relative, same origin)
- WS auto-detects protocol (ws/wss) and uses /ws/live on same host.

## API Endpoints (Merged)

Base: `/api/v1`
All original endpoints plus new ones for frontend:

| Method | Path | Description |
|---|---|---|
| GET | /machines | List with health score |
| GET | /machines/{id} | Detail |
| GET | /machines/{id}/readings?limit=&sensors= | Recent readings |
| GET | /machines/{id}/health-history | Health series |
| GET | /alerts?status=&severity=&machine_id=&limit=&offset= | List alerts |
| GET | /alerts/{alert_id} | Alert + diagnosis, plan, ticket |
| POST | /alerts/{alert_id}/acknowledge | Acknowledge |
| GET | /decisions/{alert_id}/trace | Full reasoning trace with citations |
| GET | /decisions | List recent decisions |
| GET | /approvals/pending | Pending approvals |
| POST | /approvals/{alert_id}/approve | Approve |
| POST | /approvals/{alert_id}/reject | Reject |
| GET | /tickets | List tickets |
| GET | /tickets/{id} | Ticket detail |
| PATCH | /tickets/{id} | Update status/assigned_to |
| POST | /knowledge/search | RAG search |
| POST | /knowledge/reingest | Re-ingest manuals |
| POST | /control/stream/start | Start simulator |
| POST | /control/stream/stop | Stop |
| POST | /control/stream/pause | Pause |
| POST | /control/stream/resume | Resume |
| POST | /control/inject-fault | Inject fault |
| POST | /control/reset | Reset runtime state |
| GET | /metrics/impact | Aggregated metrics (downtime, defects, energy) |
| GET | /metrics/oee | **NEW** OEE overall + per_line {availability, performance, quality, oee} |
| GET | /bottlenecks | **NEW** Bottleneck machines [{line_id, machine_id, reason, units_lost_per_hour, since}] |
| POST | /chat | **NEW** RAG chat {question, history, machine_type} -> {answer, citations[{index, source, section, doc_type, excerpt, score}], related_alert_ids} |
| GET | /audit-log?actor_type=&event_type=&machine_id=&alert_id=&limit=&offset= | **NEW** Audit log from traces + approvals + tickets |
| GET | /health | Liveness + deps |
| WS | /ws/live | WebSocket live events (recommended) |
| WS | /api/v1/ws/live | WebSocket alias (legacy compatibility) |

### WebSocket Event Catalog

Envelope `{type, ts, payload}`

| type | Sample payload |
|---|---|
| reading | {"machine_id":"TURBO-01","ts":"...","sensors":{"s7":1.2}} |
| health_update | {"machine_id":"TURBO-01","health_score":42,"status":"critical"} |
| alert_created | {"alert_id":"uuid","machine_id":"TURBO-01","severity":"critical","alert_type":"degradation"} |
| agent_step | {"agent":"diagnosis","input_summary":"...","output_summary":"...","reasoning":"...","duration_ms":120} |
| diagnosis_ready | {"alert_id":"...","diagnosis":{"root_cause":"HPC degradation","confidence":0.78},"citations":["[1] turbofan_maintenance.md"]} |
| plan_ready | {"alert_id":"...","plan":{"action_type":"stop_machine","risk_level":"high","requires_approval":true}} |
| approval_required | {"alert_id":"...","ticket_id":"...","action_type":"stop_machine","risk_level":"high"} |
| ticket_updated | {"ticket_id":"...","alert_id":"...","status":"awaiting_approval"} |
| fault_injected | {"machine_id":"TURBO-01","fault_type":"degradation","magnitude":2.0} |
| decision_ready | {"alert_id":"...","final_state":{...}} |
| reset | {"message":"pipeline reset"} |
| ping | Heartbeat every 30s |

## Frontend Routes

- `/` - Command Center: OEE (real), bottleneck, health scores, active alerts, pipeline flow, agent activity, KPI cards
- `/machines` - Machines list with filter/search grid/table toggle
- `/machines/:id` - Machine detail: health gauge + why status, sensor charts (live WS), forecast RUL/defect prob
- `/ask` - Ask Factory chat: sourced answers with clickable citations, insufficient evidence warning
- `/actions` - Agent actions: Pending work orders, History, Audit log (filter, CSV export)
- `/alerts` - Alerts list with severity/status filters, live table
- `/alerts/:alertId` - Alert detail: stepper, What happened, Trace, Diagnosis (citations), Plan, Repair Instructions, sticky approve bar
- `/approvals` - Pending approvals
- `/tickets`, `/tickets/:ticketId` - Tickets list kanban toggle, detail with status stepper and safety callout
- `/knowledge` - Search manuals/failure logs
- `/simulator` - Stream controls Start/Pause/Resume/Stop, inject fault form with presets, live chain panel, Reset
- `/impact` - Downtime avoided, defects prevented, energy saved, charts
- `/demo` - 8-step wizard with Run this step and live What happened panel
- `/how-it-works` - Interactive architecture diagram + FAQ

## Workflow for Verification

1. `make full-install && make train && make frontend-build && make run`
   - Backend at http://localhost:8000 serves frontend + API
   - `GET /api/v1/health` reports OK
2. Visit http://localhost:8000 - Command Center shows OEE, machines, alerts (real backend, not mock because VITE_USE_MOCK=false)
3. `POST /api/v1/control/inject-fault` on TURBO-01 produces alert -> monitor escalation -> diagnosis with citations -> plan -> ticket, visible via `GET /decisions/{alert_id}/trace` and live WS
4. Approval flow: requires_approval=true stays awaiting_approval until approve, then resumes
5. New endpoints:
   - `GET /api/v1/metrics/oee` returns real OEE computed from DB
   - `GET /api/v1/bottlenecks` returns bottleneck based on lowest health
   - `POST /api/v1/chat` with `{"question":"Why did Line 3 stop at 2 AM?"}` returns sourced answer with citations (fallback knows this question)
   - `GET /api/v1/audit-log` returns audit from traces + approvals
6. Frontend dev mode: `cd frontend && npm run dev` -> http://localhost:3000 proxies to backend, live charts via WS
7. `make test` passes with mock mode + synthetic data (backend tests)

## What Was Fixed in Merge

1. **Missing backend endpoints implemented**: `routes_extended.py` adds OEE (computed from machines health), bottlenecks (lowest health + open alerts), chat (RAG retriever + LLM mock/real + fallback for known questions), audit-log (assembles from DecisionTrace, Approval, Ticket tables).
2. **WebSocket dual support**: Original `/ws/live` plus alias `/api/v1/ws/live` so frontend both old (`/api/v1/ws/live`) and new (`/ws/live`) work.
3. **Frontend serving**: `api/main.py` now detects frontend dist in `frontend/dist` or `Fontend/dist`, mounts `/assets`, and SPA fallback serves `index.html` for all non-api routes. Single port deployment.
4. **Frontend API client fixed**: Auto-detects production vs dev. In prod (same origin) uses `/api/v1` and `/ws/live` with correct ws/wss protocol. Adds missing `patch` method. Vite proxy for `/api` and `/ws`.
5. **Folder normalization**: Proper `frontend/` folder created alongside legacy `Fontend/` (typo). Both contain same code; Dockerfile and main.py check both locations. New code uses `frontend/`.
6. **Docker merged**: `docker-compose.yml` includes mosquitto, backend (serves frontend), and optional frontend separate service with nginx proxying API/WS to backend.
7. **Makefile unified**: Targets for `frontend-install`, `frontend-build`, `full-install`, `full-build`, `full-run`, docker helpers.
8. **Env examples updated**: Frontend `.env.example` now defaults to `ws://localhost:8000/ws/live` (correct) and `VITE_USE_MOCK=false` for real backend usage. Documents auto-detect behavior.

## How to Run Tests

```bash
pytest -v tests/
# Frontend build test
cd frontend && npm run build
```

## Troubleshooting (Merged)

- **Frontend shows Demo data badge**: Means WS connection failed after 3 retries and fell back to MockSocket. Check backend running at 8000, and WS URL. In prod merged, WS URL auto is `ws://localhost:8000/ws/live` or `wss://yourhost/ws/live`. Ensure backend CORS allows frontend origin.
- **OEE returns mock**: When no machines in DB yet (before stream started), endpoint returns fallback mock OEE similar to frontend mockData. After stream starts and machines registered, real OEE computed.
- **Chat insufficient evidence**: Retrieval scores low <0.15 triggers insufficient warning. Ensure manuals ingested: `make ingest-docs` or POST /knowledge/reingest?reset=true. Vector store count in /health should be >0.
- **Port 8000 in use**: Change `uvicorn api.main:app --port 8001` and set VITE_API_BASE_URL accordingly.
- **Node_modules huge**: `make clean` removes dist and node_modules.

## Future Improvements

- Multi-stage Docker for backend that builds frontend inside (currently COPY dist, requires pre-build; can be changed to build in Dockerfile)
- Add authentication for frontend routes via API_KEY
- Persist audit log to dedicated table instead of assembling from traces
- Add real line_id to MachineORM meta_json for accurate OEE per_line grouping
