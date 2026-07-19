<div align="center">

# 👽 AlienMind

**The platform layer of the Alien Ecosystem** — a suite of independently deployable, identity-linked services for how dev teams actually build software.

![FastAPI](https://img.shields.io/badge/FastAPI-async-009688) ![MongoDB](https://img.shields.io/badge/MongoDB-Motor-47A248) ![React](https://img.shields.io/badge/React-Vite-61DAFB) ![License](https://img.shields.io/badge/license-All%20Rights%20Reserved-lightgrey)

[Live Demo](#) · [Walkthrough Video](#) · [Architecture Deep-Dive](./ARCHITECTURE.md)

![AlienMind Dashboard](./docs/screenshot-dashboard.png)

</div>

---

## Contents

- [What This Is](#what-this-is)
- [Features](#features)
- [Engineering Highlights](#engineering-highlights)
- [Tech Stack](#tech-stack)
- [Quickstart](#quickstart)
- [Roadmap](#roadmap)

---

## What This Is

AlienMind isn't shipped as a standalone app — it's the identity and data backbone of the **Alien Ecosystem**, a set of services designed to work together the way real engineering orgs actually operate: one platform owning auth and workspaces, with specialized services plugging into it rather than duplicating it.

This repo *is* that platform layer — workspaces, teams, projects, sprints, and role-based access control for dev teams.

**AlienSupport**, a RAG-based AI support agent, delegates its identity entirely to AlienMind and escalates unresolved queries directly into it as tasks — currently in progress.

A third service, an AI agent orchestration layer, is planned once the first two are live.

Every service is independently deployable and connected only through a shared JWT identity layer — the ecosystem grows by adding services, not by growing this one monolith.

## Features

- **Workspaces** — fully isolated multi-tenant spaces; signup creates your workspace instantly
- **Teams & Projects** — projects span teams, sprints live inside projects, tasks flow through a full status lifecycle
- **Role-scoped experience** — Admin, Manager, and Member each get their own dashboards, pages, and permitted actions, enforced server-side
- **Ownership-aware permissions** — the same user can manage one team, contribute to another, and the UI adapts per resource
- **Admin lifecycle** — capped admin seats, transactional admin transfer, hardened against in-app privilege escalation

## Engineering Highlights

- **Associative-entity multi-tenancy** — `User` is pure identity; `WorkspaceMember` carries role/teams/status per workspace. One human, N workspaces, zero credential duplication.
- **Defense-in-depth RBAC** — role checks at the router dependency layer *and* inside every service function; the service layer never trusts its caller.
- **Per-resource ownership at runtime** — authorization compares the caller against the fetched document, not token claims. No token bloat, no cross-context privilege leakage.
- **Aggregation-driven reads** — every dashboard and list view is a dedicated MongoDB pipeline; no N+1 queries, no client-side joins.
- **Transactions where stakes demand** — admin transfer commits both role swaps atomically or not at all.

→ Full decision log with rejected alternatives and real bug post-mortems: [`ARCHITECTURE.md`](./ARCHITECTURE.md)

## Tech Stack

**Backend** FastAPI · Motor (async MongoDB) · Pydantic v2 · Loguru
**Frontend** React · Vite · Tailwind CSS v4
**Auth** JWT with workspace-scoped tokens

## Quickstart

```bash
git clone https://github.com/prem-ai-dev/AlienMind.git
cd AlienMind
pip install -r requirements.txt
cp .env.example .env   # fill in your values
uvicorn app.main:app --reload
```

## Roadmap

| Version | Scope |
|---|---|
| **v1** ✅ | Multi-tenant workspaces, full RBAC, projects/sprints/tasks, role-scoped dashboards |
| **v2** | Redis caching + token blacklisting, rate limiting, email invites, tier enforcement, WebSocket live sync |
| **v3** | In-app AI agent (hand-built ReAct loop, SSE streaming), AI sprint summaries, MCP integrations |

## License

All rights reserved — publicly viewable for portfolio and evaluation purposes. See [LICENSE](./LICENSE).
