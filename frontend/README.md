# Mastery AI Frontend (Vite + React)

Production-oriented frontend for the Mastery AI platform, connected to the existing FastAPI backend and ai-core services.

## Stack
- Vite + React + TypeScript
- Axios API client
- TanStack Query (provider ready)
- Framer Motion (page transitions)
- Lucide icons
- Recharts (available for analytics visuals)

## Environment
Create `.env` from `.env.example`:

```bash
cp .env.example .env
```

Required variable:

```env
VITE_BACKEND_BASE_URL=https://your-backend.onrender.com
```

## Run Local
```bash
npm install
npm run dev
```

## Build
```bash
npm run build
npm run preview
```

## Implemented Functional Areas

## 1) Auth
- Register (`POST /api/v1/auth/register`)
- Login (`POST /api/v1/auth/login`)
- Password change (`PUT /api/v1/auth/password`)

## 2) Student Studio
- Profile setup/read/update preference endpoints
- Topics and lesson retrieval
- Diagnostic start/submit, learning path next/map visual
- Quiz generate/submit/results
- Tutor session start/chat/history/end
- Tutor hint and mistake explanation
- Activity logging + stats + mastery + leaderboard

## 3) Teacher Intelligence
- Class list/create
- Enroll/remove student
- Dashboard, heatmap, alerts, student timeline
- Assignments and interventions

## 4) Admin Ops
- Curriculum upload
- Ingestion status + pending approvals
- Topic/concept inspection + mapping update
- Approve/rollback curriculum version
- Governance metrics + hallucination resolve

## 5) Integration Lab
- Internal Postgres contract endpoints
- Internal Graph contract endpoints
- Internal RAG retrieve endpoint

## Notes
- Frontend uses JWT from login response and injects `Authorization: Bearer <token>` on requests.
- `user_id` in token/session is used as `student_id` where required.
- All API calls are real; no mocked backend data is used.
