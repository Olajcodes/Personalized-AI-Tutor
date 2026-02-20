# ai-core (MVP)

Minimal AI core engine for the **Personalized AI Tutor** capstone MVP.

## What this service does (MVP scope)
- Curriculum-scoped tutoring: **JSS1–JSS3**, **Term 1–3**
- RAG retrieval with strict metadata filters + citations
- Basic Neo4j prerequisite lookups
- Basic mastery updates
- Minimal safety guardrails (refusal + prompt-injection hygiene)
- Minimal observability (structured logs + token/cost counters)

## Main entrypoint
FastAPI should call:

`core_engine.orchestration.tutor_engine.handle_question(...)`

That function performs, in order:
1) Resolve curriculum scope (allowed topics/LOs)
2) Retrieve grounded chunks (RAG) with strict filters
3) Optionally query prerequisite chain (Neo4j) for remediation hints
4) Call LLM and return a cited response
5) Log request + cost; apply minimal mastery update

## Notes
- Ingestion pipelines live outside ai-core (admin pipeline).
- Multi-agent LangGraph orchestration is deferred to stretch goals.
