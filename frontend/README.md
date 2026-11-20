# Factory Brain - AI Operations Layer Frontend

An industrial, flat, matte UI for connected factories that improves throughput and uptime through agentic orchestration and sensor ingestion.

## Quick Start

```bash
npm install
npm run dev
```

Runs fully in mock mode with no backend required (`VITE_USE_MOCK=true` default). Visit http://localhost:3000

## Environment Variables

See `.env.example`:

- `VITE_API_BASE_URL` - REST API base, default `http://localhost:8000/api/v1`
- `VITE_WS_URL` - WebSocket URL, default `ws://localhost:8000/api/v1/ws/live`
- `VITE_API_KEY` - Optional API key for X-API-Key header
- `VITE_USE_MOCK` - `true` to use built-in mock server and mock WebSocket emitter. If backend unreachable, auto-falls back to mock with "Demo data" badge.

With backend running, pages use real endpoints. Four new endpoints fall back gracefully:

- `GET /metrics/oee` -> `{availability, performance, quality, oee, per_line:[]}`
- `GET /bottlenecks` -> `[{line_id, machine_id, reason, units_lost_per_hour, since}]`
- `POST /chat` -> `{answer, citations:[{index, source, section, doc_type, excerpt, score}], related_alert_ids?[]}`
- `GET /audit-log` -> `[{id, ts, actor_type: "ai"|"human", actor, event_type, alert_id, ticket_id, machine_id, summary, details}]`

If these return 404 or network error, mock data shown with "Demo data" tag where applicable.

## Routes

- `/` - Live overview (Command Center): OEE, bottleneck, health scores, active alerts, pipeline flow, agent activity, KPI cards
- `/machines` - Machines list with filter/search grid/table toggle
- `/machines/:id` - Machine detail: health gauge + why status, sensor charts (live WS), forecast card RUL/defect prob with confidence bar, anomaly explainer plain language
- `/ask` - Ask the Factory chat: sourced answers with clickable citations, sources panel, insufficient evidence warning, suggested questions
- `/actions` - Agent actions: tabs Pending work orders (WorkOrderCard with approve/reject outcome preview), History, Audit log (filter, CSV export, expand reasoning)
- `/alerts` - Alerts list with severity/status filters, live table, mini stepper
- `/alerts/:alertId` - Alert detail: summary, story stepper, tabs What happened, Agent Trace, Diagnosis (citations), Plan (impact estimates), Repair Instructions, Ticket + sticky approve bar
- `/approvals` - Pending approvals standalone (same as Pending tab)
- `/tickets`, `/tickets/:ticketId` - Tickets list with kanban toggle, detail with status stepper and safety callout
- `/knowledge` - Search manuals/failure logs, highlighted terms, similarity bar
- `/simulator` - Stream controls Start/Pause/Resume/Stop, inject fault form with presets, live chain panel, Reset danger confirm
- `/impact` - Downtime avoided, defects prevented, energy saved big numbers, charts alerts by severity, auto vs human, estimates explanation
- `/demo` - 8-step wizard with Run this step and live What happened panel
- `/how-it-works` - Interactive architecture diagram clickable blocks + FAQ accordion
- `*` - 404

## Component Overview

- `layout/AppShell.jsx` - Sidebar + TopBar + scrollable content + Tour + Glossary + Toasts
- `layout/Sidebar.jsx` - Collapsible nav with icons, subtitles, pending badge
- `layout/TopBar.jsx` - Live indicator, health pill, theme toggle, floor mode toggle, Glossary, Tour button
- `layout/PageHeader.jsx` - Title, purpose line, collapsible What can I do here? bullets
- `components/common/` - Card (8px radius, 1px border), Badge, StatusDot/SeverityBadge (icon+label color-blind safe), InfoTip (popover), OutcomeButton (outcome preview popover + confirm dialog), Toast, EmptyState, Skeleton, Tabs, Drawer, CopyButton, KeyValue, BigNumber (36-48px mono)
- `components/pipeline/PipelineFlow.jsx` - Flat stepped diagram Sensors→Detection→Diagnosis→Planning→Action→Ticket with static connectors + small dash animation, no glow
- `components/oee/` - OeeSummary (big OEE + 3 gauges + per-line expandable), OeeGauge, BottleneckCard (orange left border, units lost per hour)
- `components/machines/` - MachineCard, HealthGauge (circular), SensorChart (recharts live), HealthHistoryChart, ForecastCard (RUL/defect prob + confidence bar), AnomalyExplainer (plain + raw toggle)
- `components/alerts/` - AlertFeed, AlertRow, SeverityBadge, TopSensorsBar (deviation bars)
- `components/agents/` - AgentTimeline, AgentStepCard (Monitor eye, Diagnosis search, Planner route, Action wrench, Supervisor shield - neutral steel icons), ReasoningBlock, CitationList (expand excerpt + insufficient evidence warning), PlanCard, ImpactEstimateCard, WorkOrderCard (If approve/If reject outcome panels + large approve orange + reject outline)
- `components/chat/` - ChatPanel, ChatMessage (AI tag orange), SourceChip (clickable [1]), SourceDrawer, SuggestedQuestions
- `components/audit/` - AuditTable, AuditEntryRow (expand details), AuditFilters + Export CSV
- `components/tickets/` - TicketCard, TicketStatusStepper, RepairInstructions (safety critical callout, LOTO reminder, expected result per step, copy/print)
- `components/help/` - GlossaryDrawer, GuidedTour (6 steps), HowItWorksDiagram

## Theme Variables

Defined in `src/index.css` as CSS variables, mapped in `tailwind.config.js`:

Dark (default):
- --bg #14171A (60%)
- --surface #1C2024 (card)
- --border #2A2F35 (30%)
- --text-primary #ECEEF0, --text-muted #8E979F
- --accent #FF6B1A (10%) safety orange - ONLY for primary buttons, selected nav/tabs, AI actions, bottleneck highlight
Light:
- --bg #F4F5F6, --surface #FFFFFF, --text-primary #14171A, --accent #D9500B (darker for AA contrast)

Status colors ONLY for status, both themes AA-adjusted, always paired with icon+label:
- healthy #22C55E (check), warning #FACC15 (triangle), critical #EF4444 (octagon/x), offline #64748B (dash)
- info uses neutral steel

Typography: Inter UI, JetBrains Mono for sensor values, IDs, timestamps, logs, tabular numbers everywhere. Floor display mode toggle scales key numbers 115% and padding.

Shape: 8px radius cards, 1px subtle borders, no shadows or only border change on hover. 8px spacing grid.

Motion: minimal ≤150ms fades, slow blink live dot no glow, value changes without count-up, respects prefers-reduced-motion.

## Outcome Texts Location

All outcome previews and info tooltips central:

- `src/utils/outcomes.js` - `outcomes` object: approve, reject, injectFault, startStream, pauseStream, resumeStream, stopStream, reset, ask, exportCsv each with preview array of plain steps. Example: Approve -> "The agents resume, the ticket moves to In Progress, the technician is notified."
- `src/utils/outcomes.js` - `infoTips` object: healthScore, oee, anomalyScore, confidence, bottleneck, rul, impact, oeeAvailability, oeePerformance, oeeQuality each with title+plain formula/content what is good vs bad.

Every action button uses OutcomeButton with these previews (popover on hover/focus, dialog on click). Every metric badge has InfoTip.

## Backend Contract

Existing endpoints used via `src/api/endpoints.js` with fallback to mock:

- GET /machines, /machines/{id}, /machines/{id}/readings
- GET /alerts, /alerts/{id}, /decisions/{alert_id}/trace
- GET /approvals/pending, POST /approvals/{id}/approve|reject
- GET /tickets, /tickets/{id}
- POST /knowledge/search, POST /control/stream/*, POST /control/inject-fault, POST /control/reset, GET /metrics/impact, GET /health
- New: GET /metrics/oee, GET /bottlenecks, POST /chat, GET /audit-log

WebSocket envelope `{type, ts, payload}` events: reading, health_update, alert_created, agent_step, diagnosis_ready, plan_ready, approval_required, ticket_updated, fault_injected, oee_update, bottleneck_update, audit_entry

`useLiveSocket` auto-reconnect exponential backoff, Live/Reconnecting/Offline indicator in TopBar, dispatches into liveStore which merges into React Query caches (live charts update without full refetch).

## Mock Mode

If `VITE_USE_MOCK=true` or backend unreachable after 3 retries, built-in mock:

- `src/api/mock/mockData.js` - 10 machines, 4 alerts, traces, diagnoses, plans, tickets, knowledge base, OEE, bottlenecks, impact, audit log
- `src/api/mock/mockServer.js` - mockApi implements all endpoints with delay, MockSocket emitter every 1s for readings + health_update + occasional agent steps, injectFault creates alert + audit entry, control start/pause/etc just updates state
- TopBar shows "Demo data" badge when active, OeeSummary and BottleneckCard also show demo tag
- Full incident simulation: inject fault -> chart changes in 1s -> alert_created → agent steps → diagnosis_ready → plan_ready → approval_required → ticket → audit

## Self-Explanatory UI Rules Implemented

1. Page header with title + one-line purpose + collapsible "What can I do here?" 2-4 bullets on EVERY page
2. OutcomeButton shows OUTCOME PREVIEW before running (hover popover + confirm dialog list): If you click this: 1)... etc.
3. Every metric/badge/score has InfoTip (i) with what it measures, how calculated, good vs bad
4. After every action toast with RESULT + link where to see it
5. Friendly empty states explaining what will appear and how to make it appear
6. Plain words + Glossary drawer top bar + technical terms (RUL, anomaly score, OEE, RAG) inline short explanation
7. Cause-and-effect chain Sensor→Detection→Diagnosis→Plan→Action→Ticket each step clickable and explained in PipelineFlow and HowItWorks

No glow, no neon, no gradients, no glassmorphism, no heavy shadows, no blur. Flat matte graphite-and-steel, safety orange accent only for primary buttons, selected nav/tabs, AI tag, bottleneck highlight.

## Build

```bash
npm run build
npm run preview
```

Clean build no console errors. Code splitting per route via React.lazy + Suspense.

## Assumptions / Simplicity Choices

- Used `zustand`-like custom store for live data (no external zustand dep) to keep bundle minimal and meet allowed libs list. Implemented with `useSyncExternalStore` for reactive updates.
- Simplified sensor mapping: vibration, temperature, current default for all types, plus bearing, torque, chamber_pressure selectable via selector; if machine type lacks sensor, mapped to closest available with selector.
- Chat API falls back to example answers for known questions ("Line 3 stop" etc) else generic RAG-style answer with citations; insufficient evidence simulated for nonsense queries containing "unicorn" or "xyz".
- OEE per_line expandable table simple, bottleneck single biggest constraint shown with orange left border as spec.
- Simulator stream state local + mock; real backend control endpoints expected same behavior.
- Glossary and Tour completion persisted in localStorage.
- Floor display mode implemented as body class scaling font-size 115% and big-number 1.4em and card padding 1.5rem per spec "scales key numbers and spacing up".
- Focus rings orange outline for keyboard nav, visible via :focus-visible.
- Responsive: Sidebar collapses to icons (64px) with toggle, tables become scrollable, touch targets min 44px via OutcomeButton min-h-44px.
- No other UI kits built components yourself as required.
