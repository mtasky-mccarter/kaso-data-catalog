#!/usr/bin/env python3
"""Validate the minimal KASO Codex handoff contract.

This checker validates engineering completeness only. It does not validate Oracle
or business truth and must not be used to manufacture semantic approval.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml


REQUIRED_PATHS = [
    "schema_version",
    "kind",
    "handoff_id",
    "status",
    "repository.name",
    "repository.base_branch",
    "repository.base_commit",
    "scope.domain",
    "scope.slug",
    "scope.oracle_objects",
    "scope.authoritative_environment",
    "scope.canonical_path",
    "target.maturity",
    "target.documentation_version",
    "target.breaking_change",
    "semantic_contract.approved",
    "backlog.blocking_count",
    "acceptance.unresolved_refs",
    "acceptance.duplicate_global_ids",
    "execution.standard",
    "repository_actions.merge_only_with_green_ci",
]


def get_path(data, dotted):
    cur = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None, False
        cur = cur[part]
    return cur, True


def is_placeholder(value):
    if isinstance(value, str):
        stripped = value.strip()
        return stripped.startswith("<") and stripped.endswith(">")
    if isinstance(value, list):
        return any(is_placeholder(v) for v in value)
    if isinstance(value, dict):
        return any(is_placeholder(v) for v in value.values())
    return False


def validate(data):
    errors = []
    warnings = []

    for path in REQUIRED_PATHS:
        value, present = get_path(data, path)
        if not present:
            errors.append(f"missing required field: {path}")
        elif value in (None, "", []):
            errors.append(f"empty required field: {path}")
        elif is_placeholder(value):
            errors.append(f"unresolved placeholder in required field: {path}")

    if data.get("kind") != "codex-handoff":
        errors.append("kind must be 'codex-handoff'")
    if data.get("status") != "READY_FOR_CODEX_HANDOFF":
        errors.append("status must be READY_FOR_CODEX_HANDOFF")

    scope = data.get("scope") or {}
    if scope.get("authoritative_environment") != "MC":
        warnings.append("authoritative_environment is not MC; verify explicit exception")

    semantic = data.get("semantic_contract") or {}
    if semantic.get("approved") is not True:
        errors.append("semantic_contract.approved must be true")

    backlog = data.get("backlog") or {}
    blocking_count = backlog.get("blocking_count")
    if not isinstance(blocking_count, int) or blocking_count < 0:
        errors.append("backlog.blocking_count must be a non-negative integer")
    target = data.get("target") or {}
    if target.get("maturity") == "AGENT-READY" and blocking_count != 0:
        errors.append("AGENT-READY requires backlog.blocking_count = 0")

    acceptance = data.get("acceptance") or {}
    for key in ("unresolved_refs", "duplicate_global_ids"):
        value = acceptance.get(key)
        if not isinstance(value, int) or value < 0:
            errors.append(f"acceptance.{key} must be a non-negative integer")

    execution = data.get("execution") or {}
    if execution.get("standard") != "docs/codex-execution-standard-v3.md":
        warnings.append("execution.standard is not the v3 standard path")

    publication = data.get("publication") or {}
    if publication.get("enabled") is True:
        for key in ("slug", "subject_sk", "output_dir", "generator_command"):
            value = publication.get(key)
            if value in (None, "") or is_placeholder(value):
                errors.append(f"publication enabled but publication.{key} is unresolved")

    if is_placeholder(data):
        warnings.append("handoff still contains template placeholders outside required fields")

    return errors, warnings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("handoff", type=Path)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    try:
        data = yaml.safe_load(args.handoff.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"HANDOFF BLOCKED: file not found: {args.handoff}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"HANDOFF BLOCKED: cannot parse YAML: {exc}", file=sys.stderr)
        return 2

    if not isinstance(data, dict):
        print("HANDOFF BLOCKED: handoff root must be a mapping", file=sys.stderr)
        return 2

    errors, warnings = validate(data)

    if args.summary:
        summary = {
            "handoff_id": data.get("handoff_id"),
            "status": data.get("status"),
            "domain": (data.get("scope") or {}).get("domain"),
            "slug": (data.get("scope") or {}).get("slug"),
            "target_maturity": (data.get("target") or {}).get("maturity"),
            "documentation_version": (data.get("target") or {}).get("documentation_version"),
            "blocking_count": (data.get("backlog") or {}).get("blocking_count"),
            "errors": len(errors),
            "warnings": len(warnings),
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        for warning in warnings:
            print(f"WARNING: {warning}")

    if errors:
        for error in errors:
            print(f"HANDOFF BLOCKED: {error}", file=sys.stderr)
        return 2

    if not args.summary:
        print("PASS: Codex handoff is structurally ready for engineering intake.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
