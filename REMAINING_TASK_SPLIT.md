# Mastery AI Remaining Task Split (Phased, Dependency-Ordered)

Last updated: 2026-02-25

## 1) Current Repo Snapshot

### Implemented in repo now
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `PUT /api/v1/auth/password`
- `POST /api/v1/students/profile/setup`
- `GET /api/v1/students/profile`
- `PUT /api/v1/students/profile`
- `PUT /api/v1/students/users/{user_id}/preferences`
- `GET /api/v1/metadata/subjects`
- `GET /api/v1/metadata/levels`
- `GET /api/v1/learning/topics`
- `GET /api/v1/learning/topics/{topic_id}/lesson`
- `POST /api/v1/learning/activity/log`
- `GET /api/v1/students/stats`
- `GET /api/v1/students/leaderboard`
- `GET /api/v1/system/health` (basic)

### Partially complete / needs hardening
- Section 1 items were completed in this branch:
- activity/stats tables now managed by Alembic (`0005_activity_tracking`)
- normalized preferences alias route added (`PUT /users/{user_id}/preferences`)
- README mounted-route list refreshed
- `/system/health` upgraded to component checks

### Not implemented yet (major uncovered scope)
- Part 3: Tutor sessions + chat history
- Part 6: Diagnostic + learning path
- Part 7: Quizzes generate/submit/results
- Part 8: Mastery dashboard + mastery-check
- Part 9: Tutor AI endpoints
- Part 10: Teacher intelligence
- Part 11: Admin curriculum + governance
- Internal APIs (`/internal/postgres/*`, `/internal/graph/*`, `/internal/rag/*`)
- System health deep dependency checks (Postgres/Redis/Neo4j/Vector/LLM)

## 2) Execution Rules (to avoid waiting/conflicts)

1. Work section-by-section in order. Do not start next section until current section test gate passes.
2. For each section, assign file ownership lanes as fixed roles: Lane A (migrations + models), Lane B (schemas + services + repositories), Lane C (endpoints + wiring), Lane D (tests + README updates).
3. Use one migration owner per section to avoid Alembic conflicts.
4. Every section must include Swagger smoke steps, `pytest` command, and sample payloads/responses in README.

## 3) Section Plan (Priority + Dependencies + Test Gates)

## Section 1 (P0): Baseline Hardening and Contract Lock

Status: Complete in branch `Olasquare` as of 2026-02-25.

### Objective
Stabilize what already exists so future sections build on a reliable base.

### In scope
- Harden Part 4 persistence (activity/stats tables via Alembic).
- Contract alignment for preferences route: keep existing `PUT /students/users/{user_id}/preferences` and add normalized `PUT /users/{user_id}/preferences` as an alias to the same service.
- Expand `/system/health` to include dependency checks (at least Postgres).
- Update root README "Currently Mounted Routes".

### Parallel lanes
- Lane A: add migration for `activity_logs`, `daily_activity_summary`, `student_stats` with FK to `users.id`.
- Lane B: move activity logic from raw SQL-only style into repository/service with validation and auth checks.
- Lane C: add normalized preferences route alias and keep backward compatibility.
- Lane D: add endpoint tests for activity log/stats/leaderboard + health.

### Dependency
No dependency. This is the first gate.

### Test gate (must pass before Section 2)
1. `python -m alembic -c backend/alembic.ini upgrade head` succeeds on clean DB.
2. `POST /api/v1/learning/activity/log` increments `GET /api/v1/students/stats`.
3. Both preferences paths work and return same result.
4. `GET /api/v1/system/health` returns component statuses.
5. `python -m pytest -q backend/tests` passes.

## Section 2 (P0): Sessions and Internal Postgres Contracts

### Objective
Implement stateful tutoring sessions and stable internal contracts used by AI/Graph teams.

### In scope
- `POST /tutor/sessions/start`
- `GET /tutor/sessions/{session_id}/history`
- `POST /tutor/sessions/{session_id}/end`
- `GET /internal/postgres/profile`
- `GET /internal/postgres/history`
- `POST /internal/postgres/quiz-attempt`
- `GET /internal/postgres/class-roster` (stub allowed, real schema in Section 6)

### Parallel lanes
- Lane A: migrations/models for sessions, messages/history, session summary fields.
- Lane B: service/repo for session lifecycle and history retrieval.
- Lane C: public + internal endpoint wiring.
- Lane D: integration tests for start -> history -> end.

### Dependency
Section 1 completed.

### Test gate
1. Start session returns `session_id`.
2. History endpoint returns ordered messages for that session.
3. End session sets `ended_at` and stores time/cost summary.
4. Internal profile/history endpoints return normalized payloads for mocks.
5. Backend tests pass.

## Section 3 (P0): Graph Internal APIs + Diagnostic/Path Core

### Objective
Deliver prerequisite/mastery graph contracts and baseline adaptive planning.

### In scope
- `GET /internal/graph/context`
- `POST /internal/graph/update-mastery`
- `POST /learning/diagnostic/start`
- `POST /learning/diagnostic/submit`
- `POST /learning/path/next`

### Parallel lanes
- Lane A: graph contract schemas + request/response validators.
- Lane B: Neo4j adapter layer with fallback mock mode for local testing.
- Lane C: diagnostic/path public endpoints using internal graph contracts.
- Lane D: tests for diagnostic lifecycle + prereq gap response.

### Dependency
Section 2 completed (internal profile/session context available).

### Test gate
1. Diagnostic start returns deterministic `diagnostic_id`, `concept_targets`, `questions`.
2. Diagnostic submit returns baseline mastery updates and recommended topic.
3. Path next returns `recommended_topic_id`, `reason`, `prereq_gaps`.
4. Internal graph endpoints validate full normalized contract payload.
5. Backend tests pass.

## Section 4 (P0): Quiz Lifecycle (Generate -> Submit -> Results)

### Objective
Ship full quiz flow with objective grading and mastery-update handoff.

### In scope
- `POST /learning/quizzes/generate`
- `POST /learning/quizzes/{quiz_id}/submit`
- `GET /learning/quizzes/{quiz_id}/results`

### Parallel lanes
- Lane A: migrations/models for quizzes, quiz_questions, attempts, answers.
- Lane B: AI quiz generation + result insights (ai-core adapter).
- Lane C: submit endpoint (grading, XP award, activity logging, internal graph update call).
- Lane D: tests for end-to-end quiz flow and idempotency.

### Dependency
Section 3 completed (requires `update-mastery` internal endpoint).

### Test gate
1. Generate returns quiz with requested `num_questions`, `difficulty`, `purpose`.
2. Submit stores attempt, returns score and xp.
3. Submit triggers internal graph update with expected payload.
4. Results endpoint returns concept breakdown + remediation recommendation.
5. Backend + ai-core tests pass.

## Section 5 (P0): Tutor AI and Mastery Dashboard MVP

### Objective
Deliver tutoring loop and learner-facing mastery dashboard.

### In scope
- `POST /tutor/chat`
- `POST /tutor/hint`
- `POST /tutor/explain-mistake`
- `GET /learning/mastery`
- `POST /learning/mastery-check/submit`

### Parallel lanes
- Lane A: backend<->ai-core adapter and payload mapping (`sss_level`, term, subject).
- Lane B: tutor endpoints with citation/recommendation/action response shape.
- Lane C: mastery aggregation endpoint (Postgres streak/badges + graph mastery slice).
- Lane D: tests for chat response contract + mastery filters.

### Dependency
Sections 2 to 4 completed.

### Test gate
1. Tutor chat works with active `session_id` and returns citations/actions.
2. Hint and explain-mistake return scoped responses.
3. Mastery endpoint returns view=`concept|topic` payload with streak and badges.
4. Mastery-check submit updates mastery in lightweight mode.
5. E2E smoke: session start -> chat -> quiz -> mastery reflects update.

## Section 6 (P1): Teacher Intelligence (Basic MVP)

### Objective
Deliver class-level monitoring with actionable alerts.

### In scope
- `GET /teachers/classes`
- `POST /teachers/classes`
- `POST /teachers/classes/{class_id}/enroll`
- `DELETE /teachers/classes/{class_id}/enroll/{student_id}`
- `GET /teachers/classes/{class_id}/dashboard`
- `GET /teachers/classes/{class_id}/heatmap`
- `GET /teachers/classes/{class_id}/alerts`
- `GET /teachers/classes/{class_id}/students/{student_id}/timeline`
- `POST /teachers/assignments`
- `POST /teachers/interventions`

### Parallel lanes
- Lane A: class/roster/assignment/intervention schema + migrations.
- Lane B: dashboard/alerts aggregations from activity + mastery data.
- Lane C: heatmap/timeline merge from graph + relational slices.
- Lane D: role-based access tests (`teacher` only).

### Dependency
Sections 3 to 5 completed.

### Test gate
1. Teacher can create class and enroll students.
2. Dashboard shows class KPIs and completion distribution.
3. Heatmap returns concept mastery matrix for class.
4. Alerts returns inactivity/decline/prereq-failure signals.
5. Non-teacher role is denied.

## Section 7 (P1): Admin Curriculum MVP + System Reliability

### Objective
Deliver content governance and deployment-safe curriculum version control.

### In scope
- `POST /admin/curriculum/upload`
- `GET /admin/curriculum/ingestion-status`
- `GET /admin/curriculum/pending-approvals`
- `GET /admin/curriculum/topics/{topic_id}`
- `GET /admin/curriculum/concepts/{concept_id}`
- `PUT /admin/curriculum/topics/{topic_id}/map`
- `POST /admin/curriculum/versions/{version_id}/approve`
- `POST /admin/curriculum/versions/{version_id}/rollback`
- `GET /admin/governance/metrics`
- `GET /admin/governance/hallucinations`
- `POST /admin/governance/hallucinations/{id}/resolve`
- `POST /internal/rag/retrieve`
- Deep health checks in `/system/health`

### Parallel lanes
- Lane A: ingestion job/version tables + status state machine.
- Lane B: curriculum mapping and version approve/rollback endpoints.
- Lane C: internal RAG retrieve endpoint + governance metrics wiring.
- Lane D: admin RBAC tests + ingestion smoke tests.

### Dependency
Sections 1 to 6 completed.

### Test gate
1. Upload creates `job_id`; status transitions parse -> chunk -> embed -> ready.
2. Approve marks version live; rollback restores previous live version.
3. Internal RAG retrieve returns filtered chunks payload.
4. Governance endpoints return non-empty metrics structure.
5. `/system/health` reports Postgres/Redis/Neo4j/Vector/LLM connectivity.

## Section 8 (Release Gate): E2E Validation and Demo Freeze

### Objective
Lock a demo-safe MVP with deterministic test flows for student, teacher, and admin.

### In scope
- Final smoke scripts and test fixtures for shared DB.
- End-to-end test docs for all MVP MUST flows.
- PR cleanup and branch freeze criteria.

### Test gate
1. Student flow: register/login -> profile -> diagnostic -> quiz -> tutor chat -> mastery.
2. Teacher flow: class create/enroll -> heatmap -> alerts -> timeline.
3. Admin flow: upload -> ingestion status -> approve -> rollback.
4. All tests pass in CI/local and documented in README.

## 4) Endpoint-to-Section Mapping (Uncovered Scope)

- Section 2: Part 3 + internal postgres endpoints.
- Section 3: Part 6 + internal graph endpoints.
- Section 4: Part 7.
- Section 5: Part 8 + Part 9.
- Section 6: Part 10.
- Section 7: Part 11 + internal rag + deep Part 12.
- Section 8: final integration and sign-off.

## 5) Notes for Team Lead Assignment

1. Keep all work inside the active section only.
2. Assign engineers by lane (A/B/C/D) per section to avoid file conflicts.
3. Do one merge per lane, then run section test gate, then move to next section.
4. Require each PR to include endpoint list changed, migration ID (if any), Swagger test payload/response, and exact test command output.
