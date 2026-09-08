"""Maintainer helpers for refreshing the bundled OpenAPI document."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, TypeGuard

_PADS_COLLECTION_PATH = "/api/pads/"
_PADS_ITEM_PATH = "/api/pads/{id}"


def _is_object_mapping(value: object, /) -> TypeGuard[dict[object, object]]:
    """Return whether a JSON value is an object mapping."""
    return isinstance(value, dict)


def _as_string_key_mapping(value: object, /) -> dict[str, Any] | None:  # pyrefly: ignore [explicit-any]
    """Return a mapping when ``value`` is a JSON object."""
    if not _is_object_mapping(value):
        return None
    return {key: item for key, item in value.items() if isinstance(key, str)}


def apply_postman_corrections(spec: dict[str, Any]) -> list[str]:  # pyrefly: ignore [explicit-any]
    """Move a misplaced ``PUT`` onto ``/api/pads/{id}``.

    Postman exports have historically placed the modify-pad ``PUT`` under
    the ``/api/pads/`` collection path instead of ``/api/pads/{id}``.

    Args:
        spec: An OpenAPI document dictionary.

    Returns:
        Human-readable notes describing applied corrections.
    """
    notes: list[str] = []
    paths_value = spec.get("paths")
    if not _is_object_mapping(paths_value):
        return notes
    collection_value = paths_value.get(_PADS_COLLECTION_PATH)
    if not _is_object_mapping(collection_value):
        return notes
    put_operation: object | None = collection_value.pop("put", None)
    if put_operation is None:
        return notes
    target_value = paths_value.get(_PADS_ITEM_PATH)
    if not _is_object_mapping(target_value):
        paths_value[_PADS_ITEM_PATH] = {"put": put_operation}
        notes.append(
            f"Replaced non-object {_PADS_ITEM_PATH} and installed PUT",
        )
        return notes
    if "put" in target_value:
        notes.append(
            f"Removed duplicate PUT from {_PADS_COLLECTION_PATH}; "
            f"{_PADS_ITEM_PATH} already defines put",
        )
        return notes
    target_value["put"] = put_operation
    notes.append(
        f"Moved PUT from {_PADS_COLLECTION_PATH} to {_PADS_ITEM_PATH}",
    )
    return notes


def run_sync(*, arguments: list[str], repo_root: Path) -> int:
    """Run the OpenAPI sync entry point.

    Args:
        arguments: Command-line arguments excluding the program name.
        repo_root: Repository root used for the default output path.

    Returns:
        Process exit code.
    """
    default_target = repo_root / "openapi.json"
    parser = argparse.ArgumentParser(
        description=(
            "Normalize a Postman-exported CoderPad OpenAPI document "
            "and write it to the repository openapi.json."
        ),
    )
    _ = parser.add_argument(
        "source",
        type=Path,
        help="Path to a Postman-exported OpenAPI JSON file",
    )
    _ = parser.add_argument(
        "--target",
        type=Path,
        default=default_target,
        help=f"Output path (default: {default_target})",
    )
    args = parser.parse_args(args=arguments)
    loaded = json.loads(s=args.source.read_text(encoding="utf-8"))  # pyrefly: ignore [unknown-argument-type]
    spec = _as_string_key_mapping(loaded)
    if spec is None:
        message = "OpenAPI document root must be a JSON object"
        raise SystemExit(message)
    notes = apply_postman_corrections(spec=spec)
    args.target.write_text(
        data=json.dumps(obj=spec, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    for note in notes:
        _ = sys.stderr.write(f"{note}\n")
    if not bool(notes):
        _ = sys.stderr.write("No Postman path corrections needed.\n")
    _ = sys.stderr.write(
        "Keep empirically observed response variants documented in "
        "docs/source/openapi-spec.rst and covered by fixtures.\n",
    )
    _ = sys.stdout.write(f"{args.target}\n")
    return 0
