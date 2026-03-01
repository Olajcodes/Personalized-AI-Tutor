from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from backend.schemas.admin_curriculum_schema import CurriculumUploadRequest
from backend.services.admin_curriculum_service import (
    AdminCurriculumService,
    AdminCurriculumValidationError,
)


def test_upload_curriculum_rejects_invalid_source_root():
    service = AdminCurriculumService(db=object())
    payload = CurriculumUploadRequest(
        subject="math",
        sss_level="SSS1",
        term=1,
        source_root="Z:/path/that/does/not/exist",
    )
    with pytest.raises(AdminCurriculumValidationError):
        service.upload_curriculum(payload=payload, actor_user_id=uuid4())


def test_collect_supported_files_handles_docx_and_txt(tmp_path: Path):
    (tmp_path / "one.docx").write_bytes(b"fake")
    (tmp_path / "two.txt").write_text("hello", encoding="utf-8")
    (tmp_path / "three.pdf").write_bytes(b"fake")

    supported, skipped = AdminCurriculumService._collect_supported_files(tmp_path)
    supported_names = sorted(path.name for path in supported)
    skipped_names = sorted(path.name for path in skipped)

    assert supported_names == ["one.docx", "two.txt"]
    assert skipped_names == ["three.pdf"]


def test_extract_document_chunks_builds_scoped_concepts(tmp_path: Path):
    topic_id = uuid4()
    topic = SimpleNamespace(id=topic_id, title="Linear Equations")

    text_file = tmp_path / "linear_equations_notes.txt"
    text_file.write_text(
        "LINEAR EQUATIONS\n"
        "Definition and examples.\n"
        "\n"
        "SIMULTANEOUS EQUATIONS\n"
        "Elimination and substitution methods.\n",
        encoding="utf-8",
    )

    service = AdminCurriculumService(db=object())
    parsed = service._extract_document_chunks(
        file_path=text_file,
        scope_topics=[topic],
        subject="math",
        sss_level="SSS1",
        term=1,
    )

    assert parsed is not None
    assert parsed.topic_id == topic_id
    assert parsed.concept_sections
    assert all(section.concept_id.startswith("math:sss1:t1:") for section in parsed.concept_sections)
    assert all(section.chunks for section in parsed.concept_sections)


def test_get_ingestion_status_maps_repository_rows(monkeypatch):
    service = AdminCurriculumService(db=object())
    now = datetime.now(timezone.utc)
    fake_job = SimpleNamespace(
        id=uuid4(),
        version_id=uuid4(),
        status="completed",
        progress_percent=100,
        current_stage="completed",
        processed_files_count=3,
        processed_chunks_count=42,
        error_message=None,
        created_at=now,
        updated_at=now,
    )
    monkeypatch.setattr(service.repo, "list_ingestion_jobs", lambda job_id=None: [fake_job])

    out = service.get_ingestion_status()
    assert len(out.jobs) == 1
    assert out.jobs[0].status == "completed"
    assert out.jobs[0].processed_chunks_count == 42
