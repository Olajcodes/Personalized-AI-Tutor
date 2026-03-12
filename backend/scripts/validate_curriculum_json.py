"""Validate canonical curriculum JSON files before ingestion."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from backend.services.admin_curriculum_service import (
    AdminCurriculumService,
    AdminCurriculumValidationError,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CURRICULUM_ROOT = REPO_ROOT / "docs" / "Curriculum_in_json"


def validate_curriculum_json_root(source_root: Path) -> dict[str, list[str] | int]:
    root = source_root.expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise AdminCurriculumValidationError(f"source_root does not exist or is not a directory: {root}")

    json_files = sorted(root.rglob("*.json"))
    if not json_files:
        raise AdminCurriculumValidationError(f"No curriculum JSON files found under: {root}")

    errors: list[str] = []
    warnings: list[str] = []
    seen_scope_slug: dict[tuple[str, str, int, str], list[str]] = defaultdict(list)

    for file_path in json_files:
        try:
            payload = AdminCurriculumService._normalize_json_topic_payload(file_path)
        except AdminCurriculumValidationError as exc:
            errors.append(f"{file_path}: {exc}")
            continue

        topic_slug = str(payload.get("topic_slug") or "").strip().lower()
        scope_key = (
            str(payload.get("subject") or "").strip().lower(),
            str(payload.get("sss_level") or "").strip(),
            int(payload.get("term") or 0),
            topic_slug,
        )
        seen_scope_slug[scope_key].append(str(file_path))

        learning_objectives = list(payload.get("learning_objectives") or [])
        sections = list(payload.get("sections") or [])
        keywords = list(payload.get("keywords") or [])

        if not learning_objectives:
            warnings.append(f"{file_path}: missing learning_objectives")
        if len(sections) < 2:
            warnings.append(f"{file_path}: only {len(sections)} section(s); richer topic structure is preferred")
        if not keywords:
            warnings.append(f"{file_path}: missing keywords")

        for section in sections:
            heading = str(section.get("heading") or "").strip()
            content = str(section.get("content") or "").strip()
            if len(content) < 60:
                warnings.append(
                    f"{file_path}: section '{heading or 'untitled'}' is very short ({len(content)} chars)"
                )

    for scope_key, paths in seen_scope_slug.items():
        if len(paths) > 1:
            subject, sss_level, term, topic_slug = scope_key
            errors.append(
                "duplicate topic_slug in same scope "
                f"({subject} {sss_level} term {term} / {topic_slug}): {', '.join(paths)}"
            )

    return {
        "file_count": len(json_files),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate canonical curriculum JSON files")
    parser.add_argument("--source-root", default=str(DEFAULT_CURRICULUM_ROOT))
    parser.add_argument("--strict-warnings", action=argparse.BooleanOptionalAction, default=False)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = validate_curriculum_json_root(Path(args.source_root))

    print(f"Validated JSON files: {result['file_count']}")
    print(f"Errors: {result['error_count']}")
    print(f"Warnings: {result['warning_count']}")

    if result["errors"]:
        print("Errors:")
        for entry in result["errors"]:
            print(f"  - {entry}")

    if result["warnings"]:
        print("Warnings:")
        for entry in result["warnings"]:
            print(f"  - {entry}")

    if result["errors"] or (args.strict_warnings and result["warnings"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
