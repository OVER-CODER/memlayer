# Frontend Architecture Audit — MemLayer

## Executive Summary
The MemLayer frontend is a modern React application built using the Next.js 15 App Router. It serves as the primary cognitive observatory for the MemLayer runtime, providing visibility into semantic retrieval, memory lineage, and context compilation.

## 1. Technical Stack
- **Framework**: Next.js 15.1.4 (App Router)
- **State Management**: Zustand (Client-side runtime state)
- **Data Fetching**: TanStack React Query (Server state management & polling)
- **HTTP Client**: Axios
- **UI/Styling**: Tailwind CSS, Framer Motion (Animations), Lucide React (Icons)
- **Visualizations**: React Flow (Lineage graphs), Recharts (Telemetry dashboards)
- **Language**: TypeScript

## 2. Framework & Routing
- **App Router**: Utilizes the `app/` directory for routing and server components.
- **Routing Structure**:
  - `/`: Overview dashboard
  - `/workspaces`: Workspace management
  - `/console`: Runtime telemetry and coordination console
  - `/governance`: Lineage and audit trail views
  - `/compiler`: Pipeline analysis and assembly visualization

## 3. API Layer & Connectivity
- **Client**: `lib/api.ts` defines the `apiClient` using Axios.
- **Base URL**: Currently hardcoded to `http://localhost:8000/api`. Needs to be updated to `NEXT_PUBLIC_API_URL` for production.
- **Endpoint Pattern**:
  - `/api/workspaces`: Core workspace CRUD (Backend prefix: `/api/workspaces`)
  - `/api/console`: Extended runtime observability (Backend prefix: `/api/console`)
- **Note**: There is a potential path duplication issue in `lib/api.ts` (e.g., `apiClient.post('/api/workspaces')` against a base URL already ending in `/api`).

## 4. Authentication & Security Invariants
- **Auth assumptions**: Currently relies on the backend's `AuthenticationMiddleware`.
- **Tenant Isolation**: Front-end state (Zustand) tracks `selectedWorkspace`. API requests must propagate tenant-scoped headers if enforced by the backend (currently using deterministic defaults).
- **Environment Config**: Relies on `.env.local` for development. Needs `NEXT_PUBLIC_API_URL` for Vercel.

## 5. Deployment Readiness
- **Framework**: Next.js (Standard Vercel deployment)
- **Build Command**: `next build`
- **TypeScript**: Strict mode enabled.
- **Telemetry**: Integrated via `/console/telemetry` endpoints.
- **Replay**: Integrated via `/console/telemetry/coordination-traces` and React Flow.

## 6. Identified Risks & Remediation
- **Hardcoded URLs**: `lib/api.ts` must be refactored to use environment variables.
- **Path Duplication**: API paths need alignment with backend router prefixes.
- **Hydration Errors**: Next.js 15 strictness may trigger hydration issues with dynamic runtime data; needs verification.
- **CORS**: Production backend (`onrender.com`) must allow origins from the Vercel deployment. (Already verified as `allow_origins=["*"]` in `app/main.py`).

---
**Audit Complete**: Ready for STEP 2 (Environment Config).
