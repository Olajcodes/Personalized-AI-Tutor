# Mastery AI Remaining Task Split (Phased + Lane File Ownership)

Last updated: 2026-02-26

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

Not yet completed end-to-end:
- Part 6, 7, 8, 9, 10, 11
- Internal APIs: `/internal/graph/*`, `/internal/rag/*`

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
- [✅] `backend/main.py`

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

## [🟡] Section 3 (P0) Graph Internal APIs + Diagnostic and Path Core [PARTIAL]

Lane A:
- [✅] `backend/alembic/versions/0007_diagnostic_state_tables.py`
- [✅] `backend/models/diagnostic.py`
- [✅] `backend/models/diagnostic_attempt.py`
- [✅] `backend/alembic/env.py` (imports for diagnostic models are present)

Lane B:
- [🟡] `backend/schemas/diagnostic_schema.py` - exists; corrected minor Pydantic v2 deprecation usage. Still needs normalized contract alignment (`term` and submit response key names).
- [🟡] `backend/schemas/learning_path_schema.py` - exists; request/response fields are not yet aligned to normalized API contract.
- [🟡] `backend/schemas/internal_graph_schema.py` - corrected to normalized update payload shape; context schema is still placeholder-level.
- [🟡] `backend/repositories/diagnostic_repo.py` - exists but methods are stubs (`pass`); needs DB implementation.
- [🟡] `backend/services/diagnostic_service.py` - exists but returns mock values; needs grading, persistence, and recommendation logic.
- [🟡] `backend/services/learning_path_service.py` - exists but static return; needs prerequisite/mastery-driven logic.
- [🟡] `backend/services/graph_client_service.py` - exists as placeholder; needs real Neo4j/internal graph integration.

Lane C:
- [🟡] `backend/endpoints/diagnostic.py` exists and imports resolve, but currently serves mock-backed service output.
- [🟡] `backend/endpoints/learning_path.py` exists and imports resolve, but currently serves mock-backed service output.
- [🟡] `backend/endpoints/internal_graph.py` exists and imports resolve, but currently uses placeholder graph client output.
- [✅] `backend/main.py` intentionally keeps section 3 routers unmounted until section 3 logic is production-ready.

Lane D:
- [✅] `backend/tests/unit/test_diagnostic_service.py` (active contract test; module now exists)
- [✅] `backend/tests/unit/test_learning_path_service.py` (active contract test; module now exists)
- [✅] `backend/tests/unit/test_internal_graph_contracts.py` (active contract test; normalized payload check enabled)
- [✅] `backend/tests/unit/test_diagnostic_endpoints.py` (skip-ready until Lane C mounts section 3 routes)
- [✅] `backend/tests/unit/test_learning_path_endpoints.py` (skip-ready until Lane C mounts section 3 routes)
- [✅] `backend/tests/integration/test_section3_diagnostic_flow.py` (skip-ready route gate test)
- [✅] `backend/README.md` section 3 smoke steps added

---

## [🟡] Section 4 (P0) Quiz Lifecycle (Generate, Submit, Results) [PARTIAL]

Lane A:
- [✅] `backend/alembic/versions/0009_quiz_tables.py` - migration exists (revision number is `0009`, not `0008`).
- [🟡] `backend/models/quiz.py` - exists; minor reserved-name issue corrected (`metadata` -> `extra_metadata` mapped to `metadata` column).
- [🟡] `backend/models/quiz_question.py` - exists; still missing some contract-critical fields expected by current service logic.
- [🟡] `backend/models/quiz_attempt.py` - exists; still needs field alignment with submit/results lifecycle expectations.
- [✅] `backend/models/quiz_answer.py`
- [✅] `backend/alembic/env.py` imports for quiz models are present.

Lane B:
- [🟡] `backend/schemas/quiz_schema.py` - exists; partially aligned and needs final contract cleanup.
- [🟡] `backend/repositories/quiz_repo.py` - minor import issues corrected; major model/field mapping mismatches remain.
- [🟡] `backend/services/quiz_generate_service.py` - exists; currently uses temporary ai-core stub, not real integration.
- [🟡] `backend/services/quiz_submit_service.py` - import issue corrected; major async/field alignment work remains.
- [🟡] `backend/services/quiz_results_service.py` - exists; depends on assumptions not yet guaranteed by repository/model layer.
- [🟡] `backend/services/graph_mastery_update_service.py` - exists; needs production retry/error handling and contract hardening.
- [🟡] `ai-core/core_engine/orchestration/quiz_engine.py` - import path corrected; implementation is still mock-only.
- [🟡] `ai-core/core_engine/api_contracts/quiz_schemas.py` - exists; requires strict parity validation with backend contract.

Lane C:
- [❌] `backend/endpoints/quizzes.py`
- [❌] `backend/main.py` quiz router mount
- [🟡] `ai-core/main.py` exists but does not expose section 4 HTTP endpoints yet.

Lane D:
- [❌] `backend/tests/unit/test_quiz_generate_service.py`
- [❌] `backend/tests/unit/test_quiz_submit_service.py`
- [❌] `backend/tests/unit/test_quiz_results_service.py`
- [❌] `backend/tests/unit/test_quiz_endpoints.py`
- [❌] `backend/tests/integration/test_section4_quiz_flow.py`
- [❌] `ai-core/tests/unit/test_quiz_engine.py`
- [❌] `backend/README.md` section-4 smoke block

---

## [❌] Section 5 (P0) Tutor AI + Mastery Dashboard MVP [NOT STARTED]

Lane A:
- [❌] `backend/alembic/versions/0010_mastery_dashboard_tables.py`
- [❌] `backend/models/mastery_snapshot.py`
- [❌] `backend/models/student_badge.py`
- [❌] `backend/alembic/env.py` imports for mastery models

Lane B:
- [❌] `backend/schemas/tutor_schema.py`
- [❌] `backend/schemas/mastery_schema.py`
- [❌] `backend/repositories/mastery_repo.py`
- [❌] `backend/services/tutor_orchestration_service.py`
- [❌] `backend/services/mastery_dashboard_service.py`
- [🟡] `ai-core/core_engine/orchestration/tutor_engine.py` exists but not integrated to backend contracts yet
- [🟡] `ai-core/core_engine/api_contracts/schemas.py` exists but needs section-5 contract alignment

Lane C:
- [❌] `backend/endpoints/tutor.py`
- [❌] `backend/endpoints/mastery.py`
- [❌] `backend/main.py` tutor/mastery router mount
- [❌] `ai-core/main.py` callable endpoints for tutor flows (if HTTP integration path is chosen)

Lane D:
- [❌] `backend/tests/unit/test_tutor_orchestration_service.py`
- [❌] `backend/tests/unit/test_mastery_dashboard_service.py`
- [❌] `backend/tests/unit/test_tutor_endpoints.py`
- [❌] `backend/tests/unit/test_mastery_endpoints.py`
- [❌] `backend/tests/integration/test_section5_tutor_mastery_flow.py`
- [❌] `ai-core/tests/unit/test_tutor_engine.py`
- [❌] `backend/README.md` section-5 smoke block

---

## [❌] Section 6 (P1) Teacher Intelligence (Basic MVP) [NOT STARTED]

Lane A:
- [❌] `backend/alembic/versions/0011_teacher_intelligence_tables.py`
- [❌] `backend/models/teacher_class.py`
- [❌] `backend/models/class_enrollment.py`
- [❌] `backend/models/teacher_assignment.py`
- [❌] `backend/models/teacher_intervention.py`
- [❌] `backend/alembic/env.py` imports

Lane B:
- [❌] `backend/schemas/teacher_schema.py`
- [❌] `backend/repositories/teacher_repo.py`
- [❌] `backend/services/teacher_service.py`
- [❌] `backend/services/teacher_analytics_service.py`

Lane C:
- [❌] `backend/endpoints/teachers.py`
- [❌] `backend/main.py` teacher router mount

Lane D:
- [❌] `backend/tests/unit/test_teacher_service.py`
- [❌] `backend/tests/unit/test_teacher_analytics_service.py`
- [❌] `backend/tests/unit/test_teachers_endpoints.py`
- [❌] `backend/tests/integration/test_section6_teacher_flow.py`
- [❌] `backend/README.md` section-6 smoke block

---

## [❌] Section 7 (P1) Admin Curriculum + Governance + Internal RAG + Deep Health [NOT STARTED]

Lane A:
- [❌] `backend/alembic/versions/0012_admin_curriculum_governance_tables.py`
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
- [🟡] `ai-core/core_engine/rag/retriever.py` exists but not yet wired to backend internal-rag contract

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
- [✅] `ai-core/scripts/smoke_test_question.py`
- [❌] `backend/services/demo_validation_service.py`

Lane C:
- [✅] `README.md`
- [✅] `backend/README.md`
- [✅] `ai-core/README.md`

Lane D:
- [❌] `backend/tests/integration/test_e2e_student_flow.py`
- [❌] `backend/tests/integration/test_e2e_teacher_flow.py`
- [❌] `backend/tests/integration/test_e2e_admin_flow.py`
- [✅] `ai-core/tests/unit/test_scoped_retrieval.py`
- [✅] `ai-core/tests/unit/test_prereq_query.py`

---

## 3) Test Snapshot (Current)

- [✅] `python -m pytest -q backend/tests` -> `38 passed, 3 skipped`
- [✅] `python -m pytest -q ai-core/tests` -> `6 passed`

---

## 4) Cleanup Notes and Flags

- [✅] `backend/endpoints/test.py` deleted (legacy prototype, unused).
- [✅] `backend/endpoints/database_setup.sql` deleted (misplaced SQL DDL, superseded by Alembic).
- [✅] `backend/endpoints/internal_postgres_service.py` deleted and replaced by `backend/endpoints/internal_postgres.py`.
- [🟡] `backend/core/ai_core_client.py` is a temporary local stub to unblock imports; replace with real ai-core HTTP client integration in section 4.
- [🟡] `backend/repositories/quiz_repo.py`, `backend/services/quiz_generate_service.py`, `backend/services/quiz_submit_service.py`, `backend/services/quiz_results_service.py` are present but not production-ready due model/contract mismatches.

---

## 5) PR Requirements Per Lane

Every PR must include:
- endpoints changed
- files added/modified
- migration revision ID (if any)
- sample request/response
- exact test command and output

