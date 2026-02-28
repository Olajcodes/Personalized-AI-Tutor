# Mastery AI Remaining Task Split (Phased + Lane File Ownership)

Last updated: 2026-02-28

Legend:
- `[✅]` complete and correct
- `[🟡]` partial / blocked
- `[❌]` not done

## 1) How To Use This Document

1. Team works section by section in order.
2. Do not start next section until current section test gate passes.
3. In each section, assign one engineer per lane:
4. Lane A: migrations + models.
5. Lane B: schemas + repositories + services.
6. Lane C: endpoints + router wiring.
7. Lane D: tests + README test instructions.
8. Lane D starts early with test skeletons and contract tests, then finalizes integration tests after Lane C merge.

## 2) Current Completed Scope

Implemented and currently mounted:
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `PUT /api/v1/auth/password`
- `POST /api/v1/students/profile/setup`
- `GET /api/v1/students/profile`
- `PUT /api/v1/students/profile`
- `PUT /api/v1/students/users/{user_id}/preferences`
- `PUT /api/v1/users/{user_id}/preferences`
- `GET /api/v1/metadata/subjects`
- `GET /api/v1/metadata/levels`
- `GET /api/v1/learning/topics`
- `GET /api/v1/learning/topics/{topic_id}/lesson`
- `POST /api/v1/learning/activity/log`
- `GET /api/v1/students/stats`
- `GET /api/v1/students/leaderboard`
- `GET /api/v1/system/health`
- `POST /api/v1/tutor/sessions/start`
- `GET /api/v1/tutor/sessions/{session_id}/history`
- `POST /api/v1/tutor/sessions/{session_id}/end`
- `GET /api/v1/internal/postgres/profile`
- `GET /api/v1/internal/postgres/history`
- `POST /api/v1/internal/postgres/quiz-attempt`
- `GET /api/v1/internal/postgres/class-roster`
- `POST /api/v1/learning/diagnostic/start`
- `POST /api/v1/learning/diagnostic/submit`
- `POST /api/v1/learning/path/next`
- `GET /api/v1/learning/path/map/visual`
- `GET /api/v1/internal/graph/context`
- `POST /api/v1/internal/graph/update-mastery`
- `POST /api/v1/learning/quizzes/generate`
- `POST /api/v1/learning/quizzes/{quiz_id}/submit`
- `GET /api/v1/learning/quizzes/{quiz_id}/results`

Not yet completed end-to-end:
- Part 7, 8, 9, 11
- Internal APIs: `/internal/rag/*`

---

## [✅] Section 1 (P0) Baseline Hardening and Contract Lock [COMPLETED]

Lane A:
- [✅] `backend/alembic/versions/0005_activity_tracking_tables.py`
- [✅] `backend/models/activity.py`
- [✅] `backend/alembic/env.py`

Lane B:
- [✅] `backend/schemas/activity_schema.py`
- [✅] `backend/repositories/activity_repo.py`
- [✅] `backend/services/activity_service.py`
- [✅] `backend/core/config.py`

Lane C:
- [✅] `backend/endpoints/student_learning_activity.py`
- [✅] `backend/endpoints/users.py`
- [✅] `backend/endpoints/system.py`
- [✅] `backend/main.py` - CORS middleware added and configured via `CORS_ORIGINS` for frontend access.

Lane D:
- [✅] `backend/tests/unit/test_activity_service.py`
- [✅] `backend/tests/unit/test_section1_endpoints.py`
- [✅] `backend/tests/unit/test_system_health.py`
- [✅] `backend/README.md`
- [✅] `README.md`

Section 1 test gate:
- [✅] `python -m pytest -q backend/tests` (passes)

---

## [✅] Section 2 (P0) Sessions + Internal Postgres Contracts [COMPLETED]

Endpoints in scope:
- `POST /api/v1/tutor/sessions/start`
- `GET /api/v1/tutor/sessions/{session_id}/history`
- `POST /api/v1/tutor/sessions/{session_id}/end`
- `GET /api/v1/internal/postgres/profile`
- `GET /api/v1/internal/postgres/history`
- `POST /api/v1/internal/postgres/quiz-attempt`
- `GET /api/v1/internal/postgres/class-roster`

Lane A (migrations + models):
- [✅] `backend/alembic/versions/0008_tutor_sessions_and_history.py`
- [✅] `backend/models/tutor_session.py`
- [✅] `backend/models/tutor_message.py`
- [✅] `backend/models/internal_quiz_attempt.py`
- [✅] `backend/alembic/env.py` (imports updated for new models)

Lane B (schemas + repos + services):
- [✅] `backend/schemas/tutor_session_schema.py`
- [✅] `backend/schemas/internal_postgres_schema.py`
- [✅] `backend/repositories/tutor_session_repo.py`
- [✅] `backend/repositories/internal_postgres_repo.py`
- [✅] `backend/services/tutor_session_service.py`
- [✅] `backend/services/internal_postgres_service.py`

Lane C (endpoints + wiring):
- [✅] `backend/endpoints/tutor_sessions.py` - corrected service/repository dependency wiring.
- [✅] `backend/endpoints/internal_postgres.py` - normalized endpoint file and correct wiring.
- [✅] `backend/main.py` - updated router import.

Lane D (tests + docs):
- [✅] `backend/tests/unit/test_tutor_session_service.py`
- [✅] `backend/tests/unit/test_internal_postgres_service.py`
- [✅] `backend/tests/unit/test_tutor_sessions_endpoints.py`
- [✅] `backend/tests/unit/test_internal_postgres_endpoints.py`
- [✅] `backend/tests/integration/test_section2_sessions_flow.py`
- [✅] `backend/README.md` (section 2 smoke block present)

Section 2 test gate:
- [✅] API paths mounted.
- [✅] Service and endpoint tests passing in suite.

---

## [✅] Section 3 (P0) Graph Internal APIs + Diagnostic and Path Core [COMPLETED]

Lane A:
- [✅] `backend/alembic/versions/0007_diagnostic_state_tables.py`
- [✅] `backend/models/diagnostic.py`
- [✅] `backend/models/diagnostic_attempt.py`
- [✅] `backend/alembic/versions/0010_graph_mastery_tracking.py`
- [✅] `backend/models/student_concept_mastery.py`
- [✅] `backend/models/mastery_update_event.py`
- [✅] `backend/alembic/env.py` (section 3 model imports added)

Lane B:
- [✅] `backend/schemas/diagnostic_schema.py` - normalized request/response contract finalized.
- [✅] `backend/schemas/learning_path_schema.py` - normalized request/response contract finalized.
- [✅] `backend/schemas/internal_graph_schema.py` - context + update contracts aligned to normalized API spec.
- [✅] `backend/repositories/diagnostic_repo.py` - implemented scope validation, topic resolution, and diagnostic persistence.
- [✅] `backend/repositories/graph_repo.py` - added mastery state/event persistence helpers.
- [✅] `backend/services/diagnostic_service.py` - implemented question generation, grading, mastery baseline updates, and recommendation logic.
- [✅] `backend/services/learning_path_service.py` - implemented mastery/prerequisite-driven next-topic selection.
- [✅] `backend/services/graph_client_service.py` - implemented internal graph context + mastery update flows backed by Postgres.

Lane C:
- [✅] `backend/endpoints/diagnostic.py` - production error mapping and service wiring.
- [✅] `backend/endpoints/learning_path.py` - production error mapping and service wiring (`/next` + `/map/visual`).
- [✅] `backend/endpoints/internal_graph.py` - normalized query params, db wiring, and validation handling.
- [✅] `backend/main.py` - section 3 routers mounted under `/api/v1`.

Lane D:
- [✅] `backend/tests/unit/test_diagnostic_service.py`
- [✅] `backend/tests/unit/test_learning_path_service.py`
- [✅] `backend/tests/unit/test_internal_graph_contracts.py`
- [✅] `backend/tests/unit/test_diagnostic_endpoints.py` (active; routes mounted)
- [✅] `backend/tests/unit/test_learning_path_endpoints.py` (active; routes mounted)
- [✅] `backend/tests/integration/test_section3_diagnostic_flow.py` (active route gate)
- [✅] `backend/README.md` section 3 smoke steps updated

---

## [✅] Section 4 (P0) Quiz Lifecycle (Generate, Submit, Results) [COMPLETED]

Lane A:
- [✅] `backend/alembic/versions/0009_quiz_tables.py` - migration exists (revision number is `0009`, not `0008`).
- [✅] `backend/alembic/versions/0011_add_concept_id_to_quiz_questions.py` - adds persisted `concept_id` to `quiz_questions` with backfill + index.
- [✅] `backend/models/quiz.py` - reserved-name issue corrected (`metadata` -> `extra_metadata` mapped to `metadata` column).
- [✅] `backend/models/quiz_question.py` - persisted `concept_id` added and indexed for mastery/recommendation flows.
- [✅] `backend/models/quiz_attempt.py` - aligned with submit/results flow (`raw_answers`, status, score, time fields).
- [✅] `backend/models/quiz_answer.py`
- [✅] `backend/alembic/env.py` imports for quiz models are present.

Lane B:
- [✅] `backend/schemas/quiz_schema.py` - final contract cleanup completed (strict fields + term bounds for mastery payloads).
- [✅] `backend/repositories/quiz_repo.py` - persists `concept_id`, normalizes options, validates IDs, and supports topic existence checks.
- [✅] `backend/services/quiz_generate_service.py` - strict ai-core error mapping + transaction commit/rollback + DB question ID response fix.
- [✅] `backend/services/quiz_submit_service.py` - grading/activity/graph flow committed transactionally; concept mapping normalized with safe fallback.
- [✅] `backend/services/quiz_results_service.py` - `_get_topic_for_concept()` implemented with topic parsing + fallback mapping.
- [✅] `backend/services/graph_mastery_update_service.py` - retry/timeout handling and normalized payload dispatch are implemented.
- [✅] `ai_core/core_engine/orchestration/quiz_engine.py` - deterministic curriculum-scoped generator/insights implemented (no placeholder stubs).
- [✅] `ai_core/core_engine/api_contracts/quiz_schemas.py` - request/response contracts aligned for backend->ai-core integration.

Lane C:
- [✅] `backend/endpoints/quizzes.py` - corrected route prefix to `/learning/quizzes` and fixed async/db wiring.
- [✅] `backend/main.py` quiz router mount
- [✅] `ai_core/main.py` exposes section 4 quiz HTTP endpoints (`POST /quiz/generate`, `GET /quiz/{quiz_id}/attempt/{attempt_id}/insights`) and CORS middleware.

Lane D:
- [✅] `backend/tests/unit/test_quiz_generate_service.py`
- [✅] `backend/tests/unit/test_quiz_submit_service.py`
- [✅] `backend/tests/unit/test_quiz_results_service.py`
- [✅] `backend/tests/unit/test_quiz_endpoints.py`
- [✅] `backend/tests/integration/test_section4_quiz_flow.py` - Postgres integration flow is runnable via `TEST_DATABASE_URL`.
- [✅] `ai_core/tests/unit/test_quiz_engine.py`
- [✅] `backend/README.md` section-4 smoke block

---

## [✅] Section 5 (P0) Tutor AI + Mastery Dashboard MVP [COMPLETED]

Lane A:
- [✅] `backend/alembic/versions/0018_mastery_dashboard_tables.py` - created mastery snapshot/badge tables with constraints and indexes.
- [✅] `backend/models/mastery_snapshot.py` - ORM model added for daily mastery snapshot payloads.
- [✅] `backend/models/student_badge.py` - ORM model added for gamification badge awards.
- [✅] `backend/alembic/env.py` imports for mastery models - imports updated.

Lane B:
- [✅] `backend/schemas/tutor_schema.py` - added chat/hint/explain request-response contracts.
- [✅] `backend/schemas/mastery_schema.py` - added mastery dashboard and snapshot contracts.
- [✅] `backend/repositories/mastery_repo.py` - added concept/topic mastery, streak/badge, snapshot persistence methods.
- [✅] `backend/services/tutor_orchestration_service.py` - added ai-core tutor orchestration client with validated fallback behavior.
- [✅] `backend/services/mastery_dashboard_service.py` - added mastery dashboard aggregation + MVP badge award logic.
- [✅] `ai_core/core_engine/orchestration/tutor_engine.py` - aligned with section-5 contracts via `run_tutor_chat`, `run_tutor_hint`, `run_tutor_explain_mistake`.
- [✅] `ai_core/core_engine/api_contracts/schemas.py` - section-5 tutor contract models added/aligned.

Lane C:
- [✅] `backend/endpoints/tutor.py` - chat/hint/explain endpoints added with auth + session ownership validation.
- [✅] `backend/endpoints/mastery.py` - `/learning/mastery` endpoint added with student ownership checks.
- [✅] `backend/main.py` tutor/mastery router mount completed.
- [✅] `ai_core/main.py` callable tutor HTTP endpoints added: `/tutor/chat`, `/tutor/hint`, `/tutor/explain-mistake`.

Lane D:
- [✅] `backend/tests/unit/test_tutor_orchestration_service.py`
- [✅] `backend/tests/unit/test_mastery_dashboard_service.py`
- [✅] `backend/tests/unit/test_tutor_endpoints.py`
- [✅] `backend/tests/unit/test_mastery_endpoints.py`
- [✅] `backend/tests/integration/test_section5_tutor_mastery_flow.py` (runs with `TEST_DATABASE_URL`; skipped safely when unset)
- [✅] `ai_core/tests/unit/test_tutor_engine.py`
- [✅] `backend/README.md` section-5 smoke block

---

## [✅] Section 6 (P1) Teacher Intelligence (Basic MVP) [COMPLETED]

Lane A:
- [✅] `backend/alembic/versions/0019_teacher_intelligence_tables.py` - additive migration with constraints/indexes for class, enrollment, assignment, and intervention tables.
- [✅] `backend/models/teacher_class.py`
- [✅] `backend/models/class_enrollment.py`
- [✅] `backend/models/teacher_assignment.py`
- [✅] `backend/models/teacher_intervention.py`
- [✅] `backend/alembic/env.py` imports

Lane B:
- [✅] `backend/schemas/teacher_schema.py`
- [✅] `backend/repositories/teacher_repo.py`
- [✅] `backend/services/teacher_service.py`
- [✅] `backend/services/teacher_analytics_service.py`

Lane C:
- [✅] `backend/endpoints/teachers.py` - full teacher class, analytics, assignment, and intervention endpoints with role/ownership validation.
- [✅] `backend/main.py` teacher router mount

Lane D:
- [✅] `backend/tests/unit/test_teacher_service.py`
- [✅] `backend/tests/unit/test_teacher_analytics_service.py`
- [✅] `backend/tests/unit/test_teachers_endpoints.py`
- [✅] `backend/tests/integration/test_section6_teacher_flow.py` (runs with `TEST_DATABASE_URL`; skipped safely when unset)
- [✅] `backend/README.md` section-6 smoke block

---

## [❌] Section 7 (P1) Admin Curriculum + Governance + Internal RAG + Deep Health [NOT STARTED]

Lane A:
- [❌] `backend/alembic/versions/0013_admin_curriculum_governance_tables.py`
- [❌] `backend/models/curriculum_ingestion_job.py`
- [❌] `backend/models/curriculum_version.py`
- [❌] `backend/models/curriculum_topic_map.py`
- [❌] `backend/models/governance_hallucination.py`
- [❌] `backend/alembic/env.py` imports

Lane B:
- [❌] `backend/schemas/admin_curriculum_schema.py`
- [❌] `backend/schemas/governance_schema.py`
- [❌] `backend/schemas/internal_rag_schema.py`
- [❌] `backend/repositories/admin_curriculum_repo.py`
- [❌] `backend/repositories/governance_repo.py`
- [❌] `backend/services/admin_curriculum_service.py`
- [❌] `backend/services/governance_service.py`
- [❌] `backend/services/rag_retrieve_service.py`
- [❌] `backend/services/system_health_service.py`
- [🟡] `ai_core/core_engine/rag/retriever.py` exists but not yet wired to backend internal-rag contract

Lane C:
- [❌] `backend/endpoints/admin_curriculum.py`
- [❌] `backend/endpoints/admin_governance.py`
- [❌] `backend/endpoints/internal_rag.py`
- [🟡] `backend/endpoints/system.py` exists (basic health only); deep dependency checks still pending
- [❌] `backend/main.py` section-7 router mount

Lane D:
- [❌] `backend/tests/unit/test_admin_curriculum_service.py`
- [❌] `backend/tests/unit/test_governance_service.py`
- [❌] `backend/tests/unit/test_internal_rag_endpoint.py`
- [❌] `backend/tests/unit/test_system_health_endpoint.py`
- [❌] `backend/tests/integration/test_section7_admin_flow.py`
- [❌] `backend/README.md` section-7 smoke block

---

## [🟡] Section 8 (Release Gate) E2E Validation and Demo Freeze [PARTIAL PREP]

Lane A:
- [❌] `backend/scripts/seed_demo_data.py`
- [❌] `backend/scripts/reset_demo_state.py`

Lane B:
- [✅] `ai_core/scripts/smoke_test_question.py`
- [❌] `backend/services/demo_validation_service.py`

Lane C:
- [✅] `README.md`
- [✅] `backend/README.md`
- [✅] `ai_core/README.md`

Lane D:
- [❌] `backend/tests/integration/test_e2e_student_flow.py`
- [❌] `backend/tests/integration/test_e2e_teacher_flow.py`
- [❌] `backend/tests/integration/test_e2e_admin_flow.py`
- [✅] `ai_core/tests/unit/test_scoped_retrieval.py`
- [✅] `ai_core/tests/unit/test_prereq_query.py`

---

## 3) Test Snapshot (Current)

- [✅] `python -m pytest -q backend/tests` -> `75 passed, 3 skipped`
- [✅] `python -m pytest -q ai_core/tests` -> `11 passed`

---

## 4) Cleanup Notes and Flags

- [✅] `backend/endpoints/test.py` deleted (legacy prototype, unused).
- [✅] `backend/endpoints/database_setup.sql` deleted (misplaced SQL DDL, superseded by Alembic).
- [✅] `backend/endpoints/internal_postgres_service.py` deleted and replaced by `backend/endpoints/internal_postgres.py`.
- [✅] `backend/core/ai_core_client.py` enforces response contract validation and supports configurable fallback policy (`AI_CORE_ALLOW_FALLBACK`).
- [✅] `backend/repositories/quiz_repo.py`, `backend/services/quiz_generate_service.py`, `backend/services/quiz_submit_service.py`, `backend/services/quiz_results_service.py` now persist `concept_id`, commit transactions, and map recommendation topics.
- [✅] `backend/schemas/quiz_schema.py` and `ai_core/core_engine/api_contracts/quiz_schemas.py` are aligned for section-4 quiz contracts.
- [✅] `backend/tests/integration/test_section4_quiz_flow.py` is runnable with `TEST_DATABASE_URL` (PostgreSQL).
- [✅] `backend/pyproject.toml`, `ai_core/pyproject.toml` updated with `asyncio_default_fixture_loop_scope = "function"` to remove pytest-asyncio deprecation warnings.
- [✅] Neo4j topic->concept relationship standardized to `COVERS`; legacy `MAPS_TO` cleanup is built into `backend/scripts/seed_neo4j_graph.py`.
- [🟡] Local-only artifacts (`test.db`, `**/__pycache__/`, `**/.pytest_cache/`) are not necessary for source control; keep them ignored and clean periodically.
- [✅] `test.db` removed from local workspace; continue keeping it untracked.

---

## 5) PR Requirements Per Lane

Every PR must include:
- endpoints changed
- files added/modified
- migration revision ID (if any)
- sample request/response
- exact test command and output


