#!/usr/bin/env python3
"""Generate canonical KASO human-readable publications with repository naming/layout rules."""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


ROOT_DEFAULT = Path(__file__).resolve().parents[1]
PUBLICATION_PREFIX = "KASO Data Catalog - Technical & Diagnostic Reference - "
LAYOUT_VERSION = "1.0"
VERSION_RE = re.compile(r"^(\d+)\.(\d+)$")

PUBLICATIONS = {
    "cestovne-prikazy": {
        "subject_sk": "cestovné príkazy",
        "generator": "tools/generate_cp_publication.py",
        "revisions": "catalog/transport/cestovne-prikazy/revisions.yaml",
    },
    "vydajky": {
        "subject_sk": "výdajky",
        "generator": "tools/generate_vyd_publication.py",
        "revisions": "catalog/warehouse/vydajky/revisions.yaml",
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_version(root: Path, config: dict) -> str:
    revisions = yaml.safe_load((root / config["revisions"]).read_text(encoding="utf-8"))
    records = revisions.get("records") or []
    versions = []
    for record in records:
        value = str(record.get("contract_version") or "")
        match = VERSION_RE.fullmatch(value)
        if match:
            versions.append(((int(match.group(1)), int(match.group(2))), value))
    if not versions:
        raise RuntimeError(f"Missing x.y contract_version in {config['revisions']}")
    return max(versions, key=lambda item: item[0])[1]


def publication_basename(config: dict, version: str) -> str:
    return f"{PUBLICATION_PREFIX}{config['subject_sk']} v{version}"


def run_domain_generator(root: Path, config: dict, temporary_output: Path) -> tuple[Path, Path, Path]:
    subprocess.run(
        [
            sys.executable,
            str(root / config["generator"]),
            "--root",
            str(root),
            "--output-dir",
            str(temporary_output),
        ],
        cwd=root,
        check=True,
    )
    docx = list(temporary_output.glob("*.docx"))
    pdf = list(temporary_output.glob("*.pdf"))
    manifests = list(temporary_output.glob("*.manifest.yaml"))
    if len(docx) != 1 or len(pdf) != 1 or len(manifests) != 1:
        raise RuntimeError(
            f"Domain generator {config['generator']} must emit exactly one DOCX, one PDF and one manifest"
        )
    return docx[0], pdf[0], manifests[0]


def generate_one(root: Path, slug: str, output_root: Path) -> tuple[Path, Path, Path]:
    config = PUBLICATIONS[slug]
    version = current_version(root, config)
    basename = publication_basename(config, version)
    target_dir = output_root / slug
    target_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as temporary:
        temporary_output = Path(temporary)
        source_docx, source_pdf, source_manifest = run_domain_generator(root, config, temporary_output)

        target_docx = target_dir / f"{basename}.docx"
        target_pdf = target_dir / f"{basename}.pdf"
        target_manifest = target_dir / f"{basename}.manifest.yaml"
        shutil.copyfile(source_docx, target_docx)
        shutil.copyfile(source_pdf, target_pdf)

        manifest = yaml.safe_load(source_manifest.read_text(encoding="utf-8"))
        manifest["contract_version"] = version
        manifest["publication_layout_version"] = LAYOUT_VERSION
        manifest["publication_slug"] = slug
        manifest["publication_title"] = basename
        manifest["publication_orchestrator"] = "tools/generate_publication.py"
        manifest["artifacts"] = [
            {
                "path": (Path("generated") / slug / target_docx.name).as_posix(),
                "sha256": sha256(target_docx),
            },
            {
                "path": (Path("generated") / slug / target_pdf.name).as_posix(),
                "sha256": sha256(target_pdf),
            },
        ]
        target_manifest.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False, width=110),
            encoding="utf-8",
        )

    return target_docx, target_pdf, target_manifest


def same_generated_file(generated_path: Path, expected_path: Path) -> bool:
    if not expected_path.is_file():
        return False
    if generated_path.name.endswith(".manifest.yaml"):
        return yaml.safe_load(generated_path.read_text(encoding="utf-8")) == yaml.safe_load(
            expected_path.read_text(encoding="utf-8")
        )
    return generated_path.read_bytes() == expected_path.read_bytes()


def check_one(root: Path, slug: str) -> None:
    expected_dir = root / "generated" / slug
    with tempfile.TemporaryDirectory() as temporary:
        generated = generate_one(root, slug, Path(temporary))
        mismatches = []
        for generated_path in generated:
            expected_path = expected_dir / generated_path.name
            if not same_generated_file(generated_path, expected_path):
                mismatches.append(expected_path.as_posix())
        if mismatches:
            raise SystemExit("Generated publication differs: " + ", ".join(mismatches))
    print(f"PASS: {slug} publication artifacts are deterministic and current")


def selected_publications(value: str) -> list[str]:
    if value == "all":
        return list(PUBLICATIONS)
    return [value]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("publication", choices=[*PUBLICATIONS, "all"])
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    publications = selected_publications(args.publication)
    if args.check:
        for slug in publications:
            check_one(root, slug)
        return

    output_root = (args.output_root or root / "generated").resolve()
    for slug in publications:
        for path in generate_one(root, slug, output_root):
            print(path)


if __name__ == "__main__":
    main()
