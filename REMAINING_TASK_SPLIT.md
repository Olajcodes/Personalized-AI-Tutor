# Mastery AI Remaining Task Split (Phased + Lane File Ownership)

Last updated: 2026-02-25

## 1) How To Use This Document

1. Team works section by section in order.
2. Do not start next section until current section test gate passes.
3. In each section, assign one engineer per lane:
4. Lane A: migrations + models
5. Lane B: schemas + repositories + services
6. Lane C: endpoints + router wiring
7. Lane D: tests + README test instructions
8. Lane D does not wait for all lanes to finish. Lane D starts early with test skeletons and contract tests, then completes integration tests after Lane C merges.

## 2) Current Completed Scope

Implemented and available now:
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

Uncovered major scope:
- Part 3, 6, 7, 8, 9, 10, 11
- Internal APIs: `/internal/postgres/*`, `/internal/graph/*`, `/internal/rag/*`

---

## :white_check_mark: Section 1 (P0) Baseline Hardening and Contract Lock [COMPLETED]

Endpoints covered:
- `POST /api/v1/learning/activity/log`
- `GET /api/v1/students/stats`
- `GET /api/v1/students/leaderboard`
- `PUT /api/v1/users/{user_id}/preferences` (alias added)
- `GET /api/v1/system/health` (component checks)

Lane file ownership (already delivered):

Lane A:
- `backend/alembic/versions/0005_activity_tracking_tables.py`
- `backend/models/activity.py`
- `backend/alembic/env.py` (model import)

Lane B:
- `backend/schemas/activity_schema.py`
- `backend/repositories/activity_repo.py`
- `backend/services/activity_service.py`
- `backend/core/config.py` (optional dependency settings)

Lane C:
- `backend/endpoints/student_learning_activity.py`
- `backend/endpoints/users.py`
- `backend/endpoints/system.py`
- `backend/main.py`

Lane D:
- `backend/tests/unit/test_activity_service.py`
- `backend/tests/unit/test_section1_endpoints.py`
- `backend/tests/unit/test_system_health.py`
- `backend/README.md`
- `README.md`

Section 1 test gate:
- `python -m alembic -c backend/alembic.ini upgrade head`
- `python -m pytest -q backend/tests`

---

## Section 2 (P0) Sessions + Internal Postgres Contracts

Status: In progress (`Lane B` and `Lane D` completed; `Lane A` and `Lane C` pending).

Endpoints in this section:
- `POST /api/v1/tutor/sessions/start`
- `GET /api/v1/tutor/sessions/{session_id}/history`
- `POST /api/v1/tutor/sessions/{session_id}/end`
- `GET /api/v1/internal/postgres/profile`
- `GET /api/v1/internal/postgres/history`
- `POST /api/v1/internal/postgres/quiz-attempt`
- `GET /api/v1/internal/postgres/class-roster`

Lane A (create/modify files) [PENDING]:
- `backend/alembic/versions/0006_tutor_sessions_and_history.py`
- `backend/models/tutor_session.py`
- `backend/models/tutor_message.py`
- `backend/models/internal_quiz_attempt.py`
- `backend/alembic/env.py` (import new models)

Lane B (create/modify files) [:white_check_mark: COMPLETED]:
- :white_check_mark: `backend/schemas/tutor_session_schema.py`
- :white_check_mark: `backend/schemas/internal_postgres_schema.py`
- :white_check_mark: `backend/repositories/tutor_session_repo.py`
- :white_check_mark: `backend/repositories/internal_postgres_repo.py`
- :white_check_mark: `backend/services/tutor_session_service.py`
- :white_check_mark: `backend/services/internal_postgres_service.py`

Lane C (create/modify files) [PENDING]:
- `backend/endpoints/tutor_sessions.py`
- `backend/endpoints/internal_postgres.py`
- `backend/main.py` (include new routers)

Lane D (create/modify files) [:white_check_mark: COMPLETED]:
- :white_check_mark: `backend/tests/unit/test_tutor_session_service.py`
- :white_check_mark: `backend/tests/unit/test_internal_postgres_service.py`
- :white_check_mark: `backend/tests/unit/test_tutor_sessions_endpoints.py`
- :white_check_mark: `backend/tests/unit/test_internal_postgres_endpoints.py`
- :white_check_mark: `backend/tests/integration/test_section2_sessions_flow.py`
- :white_check_mark: `backend/README.md` (section 2 smoke test block)

Section 2 test gate:
1. Start returns `session_id`.
2. History returns ordered messages.
3. End closes session and stores summary.
4. Internal postgres endpoints return contract payloads.

---

## Section 3 (P0) Graph Internal APIs + Diagnostic and Path Core

Endpoints in this section:
- `GET /api/v1/internal/graph/context`
- `POST /api/v1/internal/graph/update-mastery`
- `POST /api/v1/learning/diagnostic/start`
- `POST /api/v1/learning/diagnostic/submit`
- `POST /api/v1/learning/path/next`

Lane A (create/modify files):
- `backend/alembic/versions/0007_diagnostic_state_tables.py`
- `backend/models/diagnostic.py`
- `backend/models/diagnostic_attempt.py`
- `backend/alembic/env.py` (import new models)

Lane B (create/modify files):
- `backend/schemas/diagnostic_schema.py`
- `backend/schemas/learning_path_schema.py`
- `backend/schemas/internal_graph_schema.py`
- `backend/repositories/diagnostic_repo.py`
- `backend/services/diagnostic_service.py`
- `backend/services/learning_path_service.py`
- `backend/services/graph_client_service.py`

Lane C (create/modify files):
- `backend/endpoints/diagnostic.py`
- `backend/endpoints/learning_path.py`
- `backend/endpoints/internal_graph.py`
- `backend/main.py` (include new routers)

Lane D (create/modify files):
- `backend/tests/unit/test_diagnostic_service.py`
- `backend/tests/unit/test_learning_path_service.py`
- `backend/tests/unit/test_internal_graph_contracts.py`
- `backend/tests/unit/test_diagnostic_endpoints.py`
- `backend/tests/unit/test_learning_path_endpoints.py`
- `backend/tests/integration/test_section3_diagnostic_flow.py`
- `backend/README.md` (section 3 smoke test block)

Section 3 test gate:
1. Diagnostic start returns `diagnostic_id`, `concept_targets`, `questions`.
2. Diagnostic submit returns baseline updates and recommended start topic.
3. Path next returns topic recommendation + prereq gaps.

---

## Section 4 (P0) Quiz Lifecycle (Generate, Submit, Results)

Endpoints in this section:
- `POST /api/v1/learning/quizzes/generate`
- `POST /api/v1/learning/quizzes/{quiz_id}/submit`
- `GET /api/v1/learning/quizzes/{quiz_id}/results`

Lane A (create/modify files):
- `backend/alembic/versions/0008_quiz_tables.py`
- `backend/models/quiz.py`
- `backend/models/quiz_question.py`
- `backend/models/quiz_attempt.py`
- `backend/models/quiz_answer.py`
- `backend/alembic/env.py` (import new models)

Lane B (create/modify files):
- `backend/schemas/quiz_schema.py`
- `backend/repositories/quiz_repo.py`
- `backend/services/quiz_generate_service.py`
- `backend/services/quiz_submit_service.py`
- `backend/services/quiz_results_service.py`
- `backend/services/graph_mastery_update_service.py`
- `ai-core/core_engine/orchestration/quiz_engine.py`
- `ai-core/core_engine/api_contracts/quiz_schemas.py`

Lane C (create/modify files):
- `backend/endpoints/quizzes.py`
- `backend/main.py` (include quiz router)
- `ai-core/main.py` (add internal quiz generation endpoint if needed)

Lane D (create/modify files):
- `backend/tests/unit/test_quiz_generate_service.py`
- `backend/tests/unit/test_quiz_submit_service.py`
- `backend/tests/unit/test_quiz_results_service.py`
- `backend/tests/unit/test_quiz_endpoints.py`
- `backend/tests/integration/test_section4_quiz_flow.py`
- `ai-core/tests/unit/test_quiz_engine.py`
- `backend/README.md` (section 4 smoke test block)

Section 4 test gate:
1. Generate respects `difficulty`, `purpose`, `num_questions`.
2. Submit stores attempt and returns score/xp.
3. Submit triggers internal graph update payload.
4. Results returns concept breakdown + remediation recommendation.

---

## Section 5 (P0) Tutor AI + Mastery Dashboard MVP

Endpoints in this section:
- `POST /api/v1/tutor/chat`
- `POST /api/v1/tutor/hint`
- `POST /api/v1/tutor/explain-mistake`
- `GET /api/v1/learning/mastery`
- `POST /api/v1/learning/mastery-check/submit`

Lane A (create/modify files):
- `backend/alembic/versions/0009_mastery_dashboard_tables.py`
- `backend/models/mastery_snapshot.py`
- `backend/models/student_badge.py`
- `backend/alembic/env.py` (import new models)

Lane B (create/modify files):
- `backend/schemas/tutor_schema.py`
- `backend/schemas/mastery_schema.py`
- `backend/repositories/mastery_repo.py`
- `backend/services/tutor_orchestration_service.py`
- `backend/services/mastery_dashboard_service.py`
- `ai-core/core_engine/orchestration/tutor_engine.py` (request/response alignment)
- `ai-core/core_engine/api_contracts/schemas.py` (if additional fields needed)

Lane C (create/modify files):
- `backend/endpoints/tutor.py`
- `backend/endpoints/mastery.py`
- `backend/main.py` (include new routers)
- `ai-core/main.py` (add callable HTTP endpoints if backend invokes ai-core over HTTP)

Lane D (create/modify files):
- `backend/tests/unit/test_tutor_orchestration_service.py`
- `backend/tests/unit/test_mastery_dashboard_service.py`
- `backend/tests/unit/test_tutor_endpoints.py`
- `backend/tests/unit/test_mastery_endpoints.py`
- `backend/tests/integration/test_section5_tutor_mastery_flow.py`
- `ai-core/tests/unit/test_tutor_engine.py`
- `backend/README.md` (section 5 smoke test block)

Section 5 test gate:
1. Tutor chat returns `assistant_message`, `citations`, `actions`, `recommendations`.
2. Hint and explain-mistake return scoped responses.
3. Mastery endpoint supports `view=concept|topic`.
4. Mastery-check submit updates mastery.

---

## Section 6 (P1) Teacher Intelligence (Basic MVP)

Endpoints in this section:
- `GET /api/v1/teachers/classes`
- `POST /api/v1/teachers/classes`
- `POST /api/v1/teachers/classes/{class_id}/enroll`
- `DELETE /api/v1/teachers/classes/{class_id}/enroll/{student_id}`
- `GET /api/v1/teachers/classes/{class_id}/dashboard`
- `GET /api/v1/teachers/classes/{class_id}/heatmap`
- `GET /api/v1/teachers/classes/{class_id}/alerts`
- `GET /api/v1/teachers/classes/{class_id}/students/{student_id}/timeline`
- `POST /api/v1/teachers/assignments`
- `POST /api/v1/teachers/interventions`

Lane A (create/modify files):
- `backend/alembic/versions/0010_teacher_intelligence_tables.py`
- `backend/models/teacher_class.py`
- `backend/models/class_enrollment.py`
- `backend/models/teacher_assignment.py`
- `backend/models/teacher_intervention.py`
- `backend/alembic/env.py` (import new models)

Lane B (create/modify files):
- `backend/schemas/teacher_schema.py`
- `backend/repositories/teacher_repo.py`
- `backend/services/teacher_service.py`
- `backend/services/teacher_analytics_service.py`

Lane C (create/modify files):
- `backend/endpoints/teachers.py`
- `backend/main.py` (include teacher router)

Lane D (create/modify files):
- `backend/tests/unit/test_teacher_service.py`
- `backend/tests/unit/test_teacher_analytics_service.py`
- `backend/tests/unit/test_teachers_endpoints.py`
- `backend/tests/integration/test_section6_teacher_flow.py`
- `backend/README.md` (section 6 smoke test block)

Section 6 test gate:
1. Teacher can create/enroll/manage class.
2. Dashboard/heatmap/alerts/timeline return valid data.
3. RBAC denies non-teacher users.

---

## Section 7 (P1) Admin Curriculum + Governance + Internal RAG + Deep Health

Endpoints in this section:
- `POST /api/v1/admin/curriculum/upload`
- `GET /api/v1/admin/curriculum/ingestion-status`
- `GET /api/v1/admin/curriculum/pending-approvals`
- `GET /api/v1/admin/curriculum/topics/{topic_id}`
- `GET /api/v1/admin/curriculum/concepts/{concept_id}`
- `PUT /api/v1/admin/curriculum/topics/{topic_id}/map`
- `POST /api/v1/admin/curriculum/versions/{version_id}/approve`
- `POST /api/v1/admin/curriculum/versions/{version_id}/rollback`
- `GET /api/v1/admin/governance/metrics`
- `GET /api/v1/admin/governance/hallucinations`
- `POST /api/v1/admin/governance/hallucinations/{id}/resolve`
- `POST /api/v1/internal/rag/retrieve`
- `GET /api/v1/system/health` (deep checks)

Lane A (create/modify files):
- `backend/alembic/versions/0011_admin_curriculum_governance_tables.py`
- `backend/models/curriculum_ingestion_job.py`
- `backend/models/curriculum_version.py`
- `backend/models/curriculum_topic_map.py`
- `backend/models/governance_hallucination.py`
- `backend/alembic/env.py` (import new models)

Lane B (create/modify files):
- `backend/schemas/admin_curriculum_schema.py`
- `backend/schemas/governance_schema.py`
- `backend/schemas/internal_rag_schema.py`
- `backend/repositories/admin_curriculum_repo.py`
- `backend/repositories/governance_repo.py`
- `backend/services/admin_curriculum_service.py`
- `backend/services/governance_service.py`
- `backend/services/rag_retrieve_service.py`
- `backend/services/system_health_service.py`
- `ai-core/core_engine/rag/retriever.py` (real retrieval implementation)

Lane C (create/modify files):
- `backend/endpoints/admin_curriculum.py`
- `backend/endpoints/admin_governance.py`
- `backend/endpoints/internal_rag.py`
- `backend/endpoints/system.py` (deep checks)
- `backend/main.py` (include new routers)

Lane D (create/modify files):
- `backend/tests/unit/test_admin_curriculum_service.py`
- `backend/tests/unit/test_governance_service.py`
- `backend/tests/unit/test_internal_rag_endpoint.py`
- `backend/tests/unit/test_system_health_endpoint.py`
- `backend/tests/integration/test_section7_admin_flow.py`
- `backend/README.md` (section 7 smoke test block)

Section 7 test gate:
1. Upload returns `job_id`.
2. Ingestion status progression works.
3. Approve/rollback workflow works.
4. Internal RAG retrieve returns chunk list payload.
5. Deep health reports Postgres/Redis/Neo4j/Vector/LLM.

---

## Section 8 (Release Gate) E2E Validation and Demo Freeze

No new business endpoints. This section finalizes integration quality.

Lane A (create/modify files):
- `backend/scripts/seed_demo_data.py`
- `backend/scripts/reset_demo_state.py`

Lane B (create/modify files):
- `ai-core/scripts/smoke_test_question.py` (final contract version)
- `backend/services/demo_validation_service.py` (optional helper)

Lane C (create/modify files):
- `README.md` (final MVP API matrix)
- `backend/README.md` (full cross-team smoke procedures)
- `ai-core/README.md` (runtime + endpoint docs)

Lane D (create/modify files):
- `backend/tests/integration/test_e2e_student_flow.py`
- `backend/tests/integration/test_e2e_teacher_flow.py`
- `backend/tests/integration/test_e2e_admin_flow.py`
- `ai-core/tests/unit/test_scoped_retrieval.py`
- `ai-core/tests/unit/test_prereq_query.py`

Section 8 test gate:
1. Student E2E passes.
2. Teacher E2E passes.
3. Admin E2E passes.
4. README smoke tests are reproducible by any teammate.

---

## 3) Endpoint-to-Section Coverage Map

Section 2:
- Part 3 + internal postgres endpoints.

Section 3:
- Part 6 + internal graph endpoints.

Section 4:
- Part 7.

Section 5:
- Part 8 + Part 9.

Section 6:
- Part 10.

Section 7:
- Part 11 + internal rag + deep Part 12.

Section 8:
- Final integration and release-quality validation.

## 4) PR Requirements Per Lane

Every PR must include:
- endpoints changed
- files added/modified
- migration revision ID (if any)
- sample request/response
- exact test command and output
