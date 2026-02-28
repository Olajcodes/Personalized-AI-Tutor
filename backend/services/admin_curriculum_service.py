"""Service layer for admin curriculum ingestion and governance workflows."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from uuid import UUID, uuid5

from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.repositories.admin_curriculum_repo import AdminCurriculumRepository
from backend.schemas.admin_curriculum_schema import (
    ConceptInspectResponse,
    ConceptInspectTopicOut,
    CurriculumIngestionStatusResponse,
    CurriculumUploadRequest,
    CurriculumUploadResponse,
    CurriculumVersionActionRequest,
    CurriculumVersionActionResponse,
    PendingApprovalsResponse,
    TopicConceptMapOut,
    TopicInspectResponse,
    TopicMapPatchRequest,
)
from backend.services.rag_retrieve_service import (
    QdrantRuntimeConfig,
    QdrantVectorStore,
    RagRetrieveServiceError,
)


class AdminCurriculumServiceError(RuntimeError):
    pass


class AdminCurriculumValidationError(ValueError):
    pass


class AdminCurriculumNotFoundError(LookupError):
    pass


@dataclass(frozen=True)
class ChunkedDocument:
    source_id: str
    topic_id: UUID
    topic_title: str
    concept_id: str
    chunks: list[str]


class AdminCurriculumService:
    CHUNK_WORD_SIZE = 190
    CHUNK_OVERLAP_WORDS = 40
    _CHUNK_NAMESPACE = UUID("f5cfde7f-0b62-46bf-bf17-838311a90be4")

    def __init__(self, db: Session):
        self.db = db
        self.repo = AdminCurriculumRepository(db)
        self.vector_store = QdrantVectorStore(
            QdrantRuntimeConfig(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key or None,
                collection=settings.qdrant_collection,
                embedding_model=settings.qdrant_embedding_model,
            )
        )

    @staticmethod
    def _normalize_text(value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip().lower()

    @classmethod
    def _is_heading(cls, line: str) -> bool:
        compact = line.strip()
        if len(compact) < 4 or len(compact) > 100:
            return False
        if compact.isupper() and len(compact.split()) <= 14:
            return True
        return bool(re.match(r"^(chapter|topic|unit|week)\b", compact, flags=re.IGNORECASE))

    @classmethod
    def _chunk_text(cls, text: str) -> list[str]:
        words = text.split()
        if not words:
            return []
        if len(words) <= cls.CHUNK_WORD_SIZE:
            return [" ".join(words)]

        chunks: list[str] = []
        start = 0
        while start < len(words):
            end = min(start + cls.CHUNK_WORD_SIZE, len(words))
            chunks.append(" ".join(words[start:end]))
            if end >= len(words):
                break
            start = max(end - cls.CHUNK_OVERLAP_WORDS, start + 1)
        return chunks

    @classmethod
    def _split_sections(cls, text: str) -> list[str]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return []

        sections: list[str] = []
        buffer: list[str] = []
        for line in lines:
            if cls._is_heading(line) and buffer:
                sections.append("\n".join(buffer))
                buffer = [line]
            else:
                buffer.append(line)
        if buffer:
            sections.append("\n".join(buffer))
        return sections

    @staticmethod
    def _read_docx(path: Path) -> str:
        try:
            from docx import Document
        except ModuleNotFoundError as exc:
            raise AdminCurriculumServiceError(
                "python-docx is not installed. Add `python-docx` to backend dependencies."
            ) from exc

        doc = Document(str(path))
        paragraphs = [paragraph.text.strip() for paragraph in doc.paragraphs if paragraph.text and paragraph.text.strip()]
        return "\n".join(paragraphs)

    @staticmethod
    def _read_text_file(path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="ignore")

    @staticmethod
    def _collect_supported_files(root: Path) -> tuple[list[Path], list[Path]]:
        all_files = [path for path in root.rglob("*") if path.is_file()]
        supported = [path for path in all_files if path.suffix.lower() in {".docx", ".txt"}]
        skipped = [path for path in all_files if path.suffix.lower() not in {".docx", ".txt"}]
        return supported, skipped

    @staticmethod
    def _topic_hint_from_file_name(file_path: Path) -> str:
        stem = file_path.stem.upper()
        tokens = re.split(r"[-_\s]+", stem)
        skip_tokens = {
            "COMPLETE",
            "FIRST",
            "SECOND",
            "THIRD",
            "TERM",
            "SS1",
            "SS2",
            "SS3",
            "SSS1",
            "SSS2",
            "SSS3",
            "MATHEMATICS",
            "MATH",
            "ENGLISH",
            "CIVIC",
            "EDUCATION",
            "NOTES",
            "NOTE",
        }
        filtered = [token for token in tokens if token and token not in skip_tokens]
        if not filtered:
            return stem
        return " ".join(filtered)

    @classmethod
    def _best_topic_match(cls, *, topic_hint: str, topics: list) -> tuple[UUID, str] | None:
        if not topics:
            return None
        normalized_hint = cls._normalize_text(topic_hint)
        if not normalized_hint:
            return None

        best_topic = None
        best_score = -1.0
        for topic in topics:
            title = str(topic.title)
            normalized_title = cls._normalize_text(title)
            score = SequenceMatcher(a=normalized_hint, b=normalized_title).ratio()
            if normalized_hint in normalized_title or normalized_title in normalized_hint:
                score = max(score, 0.92)
            if score > best_score:
                best_score = score
                best_topic = topic

        if best_topic is None or best_score < 0.35:
            return None
        return best_topic.id, str(best_topic.title)

    @classmethod
    def _version_name_default(cls, *, subject: str, sss_level: str, term: int) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"{subject}-{sss_level}-term{term}-{timestamp}"

    def _extract_document_chunks(
        self,
        *,
        file_path: Path,
        scope_topics: list,
    ) -> ChunkedDocument | None:
        if file_path.suffix.lower() == ".docx":
            text = self._read_docx(file_path)
        elif file_path.suffix.lower() == ".txt":
            text = self._read_text_file(file_path)
        else:
            return None

        text = text.strip()
        if not text:
            return None

        topic_hint = self._topic_hint_from_file_name(file_path)
        match = self._best_topic_match(topic_hint=topic_hint, topics=scope_topics)
        if match is None:
            return None
        topic_id, topic_title = match

        chunks: list[str] = []
        sections = self._split_sections(text)
        if not sections:
            sections = [text]
        for section in sections:
            section_chunks = self._chunk_text(section)
            chunks.extend(section_chunks)
        if not chunks:
            return None

        return ChunkedDocument(
            source_id=file_path.name,
            topic_id=topic_id,
            topic_title=topic_title,
            concept_id=str(topic_id),
            chunks=chunks,
        )

    def upload_curriculum(
        self,
        *,
        payload: CurriculumUploadRequest,
        actor_user_id: UUID | None = None,
    ) -> CurriculumUploadResponse:
        source_root = Path(payload.source_root).expanduser().resolve()
        if not source_root.exists() or not source_root.is_dir():
            raise AdminCurriculumValidationError(f"source_root does not exist or is not a directory: {source_root}")

        scope_topics = self.repo.get_scope_topics(
            subject=payload.subject,
            sss_level=payload.sss_level,
            term=payload.term,
        )
        if not scope_topics:
            raise AdminCurriculumValidationError(
                "No topics found for provided scope. Seed topics before curriculum ingestion."
            )

        supported_files, skipped_files = self._collect_supported_files(source_root)
        if not supported_files:
            raise AdminCurriculumValidationError(
                "No supported files found in source_root. Supported extensions: .docx, .txt"
            )

        version_name = payload.version_name or self._version_name_default(
            subject=payload.subject,
            sss_level=payload.sss_level,
            term=payload.term,
        )
        if self.repo.get_curriculum_version_by_name(version_name):
            raise AdminCurriculumValidationError(f"Curriculum version name already exists: {version_name}")

        version = self.repo.create_curriculum_version(
            version_name=version_name,
            subject=payload.subject,
            sss_level=payload.sss_level,
            term=payload.term,
            source_root=str(source_root),
            uploaded_by=actor_user_id,
            status="ingesting",
            source_file_count=len(supported_files),
            metadata_payload={"skipped_extensions": sorted({path.suffix.lower() for path in skipped_files})},
        )
        job = self.repo.create_ingestion_job(
            version_id=version.id,
            created_by=actor_user_id,
            status="parsing",
            current_stage="parsing",
        )
        self.repo.append_ingestion_log(
            job,
            stage="parsing",
            message="Started ingestion",
            extra={"source_root": str(source_root), "supported_files": len(supported_files)},
        )
        self.db.commit()

        try:
            chunk_rows: list[dict] = []
            mapped_topic_ids: set[UUID] = set()
            processed_file_count = 0
            processed_chunks = 0

            for index, file_path in enumerate(supported_files, start=1):
                parsed = self._extract_document_chunks(file_path=file_path, scope_topics=scope_topics)
                if parsed is None:
                    self.repo.append_ingestion_log(
                        job,
                        stage="parsing",
                        message="Skipped file (empty/unmatched topic)",
                        extra={"file": file_path.name},
                    )
                    continue

                processed_file_count += 1
                mapped_topic_ids.add(parsed.topic_id)
                self.repo.upsert_topic_map(
                    version_id=version.id,
                    topic_id=parsed.topic_id,
                    concept_id=parsed.concept_id,
                    prereq_concept_ids=[],
                    confidence=0.75,
                    is_manual_override=False,
                    created_by=actor_user_id,
                )

                for chunk_index, chunk_text in enumerate(parsed.chunks):
                    deterministic_id = uuid5(
                        self._CHUNK_NAMESPACE,
                        f"{version.id}:{parsed.source_id}:{parsed.topic_id}:{chunk_index}",
                    )
                    chunk_payload = {
                        "chunk_id": str(deterministic_id),
                        "source_id": parsed.source_id,
                        "text": chunk_text,
                        "subject": payload.subject,
                        "sss_level": payload.sss_level,
                        "term": payload.term,
                        "topic_id": str(parsed.topic_id),
                        "topic_title": parsed.topic_title,
                        "concept_id": parsed.concept_id,
                        "curriculum_version_id": str(version.id),
                        "approved": False,
                        "chunk_index": chunk_index,
                    }
                    chunk_rows.append({"id": deterministic_id, "text": chunk_text, "payload": chunk_payload})

                processed_chunks += len(parsed.chunks)
                progress = int((index / max(len(supported_files), 1)) * 55)
                self.repo.update_ingestion_job(
                    job,
                    progress_percent=min(progress, 55),
                    processed_files_count=processed_file_count,
                    processed_chunks_count=processed_chunks,
                )

            self.repo.update_ingestion_job(
                job,
                status="embedding",
                current_stage="embedding",
                progress_percent=60,
                processed_files_count=processed_file_count,
                processed_chunks_count=processed_chunks,
            )
            self.repo.append_ingestion_log(
                job,
                stage="embedding",
                message="Embedding and indexing chunks",
                extra={"chunk_count": len(chunk_rows)},
            )

            if chunk_rows:
                self.vector_store.upsert_chunks(chunk_rows)

            topic_ids_list = list(mapped_topic_ids)
            affected_topics = self.repo.set_topics_version(
                topic_ids=topic_ids_list,
                version_id=version.id,
                is_approved=False,
            )

            version_metadata = dict(version.metadata_payload or {})
            version_metadata.update(
                {
                    "processed_files_count": processed_file_count,
                    "processed_chunks_count": processed_chunks,
                    "indexed_at": datetime.now(timezone.utc).isoformat(),
                    "affected_topics": affected_topics,
                }
            )

            self.repo.update_curriculum_version(
                version,
                status="pending_approval" if chunk_rows else "failed",
                metadata_payload=version_metadata,
            )
            self.repo.update_ingestion_job(
                job,
                status="completed" if chunk_rows else "failed",
                current_stage="completed" if chunk_rows else "failed",
                progress_percent=100,
                processed_files_count=processed_file_count,
                processed_chunks_count=processed_chunks,
                error_message=None if chunk_rows else "No indexable chunks produced",
                finished_at=datetime.now(timezone.utc),
            )
            self.db.commit()

            return CurriculumUploadResponse(
                version_id=version.id,
                job_id=job.id,
                status=version.status,
                discovered_files=len(supported_files),
                skipped_files=len(skipped_files),
                processed_chunks=processed_chunks,
            )
        except Exception as exc:
            self.db.rollback()
            persisted_job = self.repo.get_ingestion_job(job.id)
            persisted_version = self.repo.get_curriculum_version(version.id)
            if persisted_job and persisted_version:
                self.repo.update_ingestion_job(
                    persisted_job,
                    status="failed",
                    current_stage="failed",
                    progress_percent=min(persisted_job.progress_percent, 99),
                    error_message=str(exc)[:2000],
                    finished_at=datetime.now(timezone.utc),
                )
                self.repo.update_curriculum_version(persisted_version, status="failed")
                self.db.commit()
            raise AdminCurriculumServiceError(f"Curriculum ingestion failed: {exc}") from exc

    def get_ingestion_status(self, *, job_id: UUID | None = None) -> CurriculumIngestionStatusResponse:
        jobs = self.repo.list_ingestion_jobs(job_id=job_id)
        return CurriculumIngestionStatusResponse(
            jobs=[
                {
                    "id": job.id,
                    "version_id": job.version_id,
                    "status": job.status,
                    "progress_percent": job.progress_percent,
                    "current_stage": job.current_stage,
                    "processed_files_count": job.processed_files_count,
                    "processed_chunks_count": job.processed_chunks_count,
                    "error_message": job.error_message,
                    "created_at": job.created_at,
                    "updated_at": job.updated_at,
                }
                for job in jobs
            ]
        )

    def get_pending_approvals(self) -> PendingApprovalsResponse:
        versions = self.repo.list_pending_approvals()
        return PendingApprovalsResponse(
            versions=[
                {
                    "id": row.id,
                    "version_name": row.version_name,
                    "subject": row.subject,
                    "sss_level": row.sss_level,
                    "term": row.term,
                    "source_file_count": row.source_file_count,
                    "status": row.status,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at,
                }
                for row in versions
            ]
        )

    def inspect_topic(self, *, topic_id: UUID) -> TopicInspectResponse:
        row = self.repo.get_topic_with_subject(topic_id)
        if row is None:
            raise AdminCurriculumNotFoundError(f"Topic not found: {topic_id}")
        topic, subject_slug = row
        maps = self.repo.get_topic_maps(topic_id=topic_id)
        return TopicInspectResponse(
            topic_id=topic.id,
            subject=subject_slug,  # type: ignore[arg-type]
            sss_level=topic.sss_level,  # type: ignore[arg-type]
            term=topic.term,
            title=topic.title,
            is_approved=topic.is_approved,
            curriculum_version_id=topic.curriculum_version_id,
            mappings=[
                TopicConceptMapOut(
                    id=item.id,
                    version_id=item.version_id,
                    topic_id=item.topic_id,
                    concept_id=item.concept_id,
                    prereq_concept_ids=list(item.prereq_concept_ids or []),
                    confidence=float(item.confidence),
                    is_manual_override=item.is_manual_override,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                )
                for item in maps
            ],
        )

    def inspect_concept(self, *, concept_id: str) -> ConceptInspectResponse:
        rows = self.repo.get_concept_maps(concept_id=concept_id)
        if not rows:
            raise AdminCurriculumNotFoundError(f"Concept not found in curriculum mappings: {concept_id}")

        prereq_ids: set[str] = set()
        topics: list[ConceptInspectTopicOut] = []
        for map_row, topic_row, subject_slug in rows:
            for prereq in (map_row.prereq_concept_ids or []):
                prereq_ids.add(str(prereq))
            topics.append(
                ConceptInspectTopicOut(
                    topic_id=topic_row.id,
                    title=topic_row.title,
                    subject=subject_slug,  # type: ignore[arg-type]
                    sss_level=topic_row.sss_level,  # type: ignore[arg-type]
                    term=topic_row.term,
                    confidence=float(map_row.confidence),
                )
            )
        return ConceptInspectResponse(
            concept_id=concept_id,
            prereq_concept_ids=sorted(prereq_ids),
            topics=topics,
        )

    def patch_topic_map(
        self,
        *,
        topic_id: UUID,
        payload: TopicMapPatchRequest,
        actor_user_id: UUID | None = None,
    ) -> TopicInspectResponse:
        topic_row = self.repo.get_topic_with_subject(topic_id)
        if topic_row is None:
            raise AdminCurriculumNotFoundError(f"Topic not found: {topic_id}")
        if self.repo.get_curriculum_version(payload.version_id) is None:
            raise AdminCurriculumNotFoundError(f"Curriculum version not found: {payload.version_id}")

        for item in payload.mappings:
            self.repo.upsert_topic_map(
                version_id=payload.version_id,
                topic_id=topic_id,
                concept_id=item.concept_id,
                prereq_concept_ids=item.prereq_concept_ids,
                confidence=item.confidence,
                is_manual_override=item.is_manual_override,
                created_by=actor_user_id,
            )
        self.db.commit()
        return self.inspect_topic(topic_id=topic_id)

    def approve_version(
        self,
        *,
        version_id: UUID,
        payload: CurriculumVersionActionRequest,
    ) -> CurriculumVersionActionResponse:
        version = self.repo.get_curriculum_version(version_id)
        if version is None:
            raise AdminCurriculumNotFoundError(f"Curriculum version not found: {version_id}")
        if version.status not in {"pending_approval", "approved", "published"}:
            raise AdminCurriculumValidationError(
                f"Version status must be pending_approval|approved|published before publish, got: {version.status}"
            )

        scope_topics = self.repo.get_scope_topics(
            subject=version.subject,
            sss_level=version.sss_level,
            term=version.term,
        )
        topic_ids = [topic.id for topic in scope_topics]
        affected_topics = self.repo.set_topics_version(topic_ids=topic_ids, version_id=version.id, is_approved=True)
        self.repo.update_curriculum_version(
            version,
            status="published",
            approved_by=payload.actor_user_id,
            approved_at=datetime.now(timezone.utc),
        )
        try:
            self.vector_store.set_approval_flag(curriculum_version_id=version.id, approved=True)
        except RagRetrieveServiceError:
            self.db.rollback()
            raise
        self.db.commit()
        return CurriculumVersionActionResponse(
            version_id=version.id,
            status=version.status,  # type: ignore[arg-type]
            affected_topics=affected_topics,
            message="Curriculum version published successfully.",
        )

    def rollback_version(
        self,
        *,
        version_id: UUID,
        payload: CurriculumVersionActionRequest,
    ) -> CurriculumVersionActionResponse:
        version = self.repo.get_curriculum_version(version_id)
        if version is None:
            raise AdminCurriculumNotFoundError(f"Curriculum version not found: {version_id}")

        scope_topics = self.repo.get_scope_topics(
            subject=version.subject,
            sss_level=version.sss_level,
            term=version.term,
        )
        topic_ids = [topic.id for topic in scope_topics]
        affected_topics = self.repo.set_topics_version(topic_ids=topic_ids, version_id=version.id, is_approved=False)
        self.repo.update_curriculum_version(version, status="rolled_back")

        previous = self.repo.get_latest_published_version_for_scope(
            subject=version.subject,
            sss_level=version.sss_level,
            term=version.term,
            exclude_version_id=version.id,
        )
        if previous is not None:
            self.repo.update_curriculum_version(previous, status="published")
            self.repo.set_topics_version(topic_ids=topic_ids, version_id=previous.id, is_approved=True)

        try:
            self.vector_store.set_approval_flag(curriculum_version_id=version.id, approved=False)
        except RagRetrieveServiceError:
            self.db.rollback()
            raise
        self.db.commit()

        return CurriculumVersionActionResponse(
            version_id=version.id,
            status=version.status,  # type: ignore[arg-type]
            affected_topics=affected_topics,
            message="Curriculum version rolled back.",
        )
