"""Human-readable README helpers for engineering review report packages."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REVIEW_README_FILENAME = "README_REVIEW.md"
_UNKNOWN = "unknown"


def build_review_readme_for_single_bundle(
    *,
    bundle_path: Path,
    manifest_path: Path,
) -> str:
    """Build a review README for one generated design report bundle."""
    bundle = Path(bundle_path)
    manifest = _load_json_object(Path(manifest_path))
    strength_status = _manifest_value(manifest, "strength_status")
    serviceability_status = _manifest_value(manifest, "serviceability_status")
    overall_status = _manifest_value(manifest, "overall_status")

    lines = [
        "# Engineering Review Package",
        "",
        "requires engineer review = true",
        "",
        "## Purpose of archive",
        "",
        (
            "This archive is a draft-MVP deterministic SP63 report package for "
            "engineering review. It is intended to make the generated report, "
            "inputs, checksums, validation commands, and limitations visible in one place."
        ),
        "",
        "## Archive contents",
        "",
        "- `input.json` - input data used to reproduce the report.",
        "- `report.md` - Markdown calculation report.",
        "- `report.json` - machine-readable report payload.",
        "- `report.html` - static HTML rendering of the report.",
        "- `manifest.json` - SHA256 manifest and reproducibility metadata.",
        "- `README_REVIEW.md` - this engineering review guide.",
        "",
        "## How to validate archive",
        "",
        "```bash",
        f"python -m sp63_core report-archive-validate --path {bundle} --json",
        "```",
        "",
        "## How to validate ZIP",
        "",
        "```bash",
        f"python -m sp63_core report-archive-zip --path {bundle} --output {bundle}.zip --json",
        "```",
        "",
        "## How to reproduce report from input.json",
        "",
        "```bash",
        f"python -m sp63_core design-report --input-json {bundle / 'input.json'} "
        f"--bundle-output {bundle}",
        "```",
        "",
        "## File locations",
        "",
        f"- input: `{bundle / 'input.json'}`",
        f"- Markdown report: `{bundle / 'report.md'}`",
        f"- JSON report: `{bundle / 'report.json'}`",
        f"- HTML report: `{bundle / 'report.html'}`",
        f"- manifest: `{manifest_path}`",
        f"- review README: `{bundle / REVIEW_README_FILENAME}`",
        "",
        "## Final statuses",
        "",
        f"- strength_status: `{strength_status}`",
        f"- serviceability_status: `{serviceability_status}`",
        f"- overall_status: `{overall_status}`",
        "",
        *_warning_section(),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_review_readme_for_batch_archive(
    *,
    archive_path: Path,
    manifest_path: Path,
    index_json_path: Path,
) -> str:
    """Build a root review README for a batch design report archive."""
    archive = Path(archive_path)
    manifest = _load_json_object(Path(manifest_path))
    index = _load_json_object(Path(index_json_path))
    overall_status = _manifest_value(manifest, "overall_status")
    strength_status = _batch_status_summary(index, "strength_status")
    serviceability_status = _batch_status_summary(index, "serviceability_status")

    lines = [
        "# Engineering Review Package",
        "",
        "requires engineer review = true",
        "",
        "## Purpose of archive",
        "",
        (
            "This batch archive is a draft-MVP deterministic SP63 review package "
            "for several rectangular design report bundles. It supports human review "
            "of inputs, generated reports, batch indexes, manifests, and checksums."
        ),
        "",
        "## Archive contents",
        "",
        "- `index.md` - human-readable batch index.",
        "- `index.json` - machine-readable batch index and case list.",
        "- `manifest.json` - root SHA256 manifest and reproducibility metadata.",
        "- `case_###/input.json` - input data for each case.",
        "- `case_###/report.md` - Markdown report for each case.",
        "- `case_###/report.json` - machine-readable report payload for each case.",
        "- `case_###/report.html` - static HTML report for each case.",
        "- `case_###/manifest.json` - case-level SHA256 manifest.",
        "- `README_REVIEW.md` - this engineering review guide.",
        "",
        "## How to validate archive",
        "",
        "```bash",
        f"python -m sp63_core report-archive-validate --path {archive} --batch --json",
        "```",
        "",
        "## How to validate ZIP",
        "",
        "```bash",
        "python -m sp63_core report-archive-zip "
        f"--path {archive} --output {archive}.zip --batch --json",
        "```",
        "",
        "## How to reproduce report from input.json",
        "",
        "Use the case-level `input.json` files stored inside the archive:",
        "",
        "```bash",
        "python -m sp63_core design-report "
        f"--input-json {archive / 'case_001' / 'input.json'} "
        f"--bundle-output {archive / 'case_001_reproduced'}",
        "```",
        "",
        "For the full batch, rerun `design-report-batch` with the original input JSON directory.",
        "",
        "## File locations",
        "",
        f"- index markdown: `{archive / 'index.md'}`",
        f"- index JSON: `{index_json_path}`",
        f"- root manifest: `{manifest_path}`",
        f"- root review README: `{archive / REVIEW_README_FILENAME}`",
        "- case inputs: `case_###/input.json`",
        "- case reports: `case_###/report.md`, `case_###/report.json`, `case_###/report.html`",
        "- case manifests: `case_###/manifest.json`",
        "",
        "## Final statuses",
        "",
        f"- strength_status: `{strength_status}`",
        f"- serviceability_status: `{serviceability_status}`",
        f"- overall_status: `{overall_status}`",
        "",
        *_warning_section(),
    ]
    return "\n".join(lines).rstrip() + "\n"


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _manifest_value(manifest: dict[str, Any], field_name: str) -> str:
    value = manifest.get(field_name)
    return str(value) if value is not None else _UNKNOWN


def _batch_status_summary(index: dict[str, Any], field_name: str) -> str:
    cases = index.get("cases")
    if not isinstance(cases, list):
        return _UNKNOWN
    counts: dict[str, int] = {}
    for case in cases:
        if not isinstance(case, dict):
            continue
        value = str(case.get(field_name) or _UNKNOWN)
        counts[value] = counts.get(value, 0) + 1
    if not counts:
        return _UNKNOWN
    return ", ".join(f"{key}: {counts[key]}" for key in sorted(counts))


def _warning_section() -> list[str]:
    return [
        "## Warnings and limitations",
        "",
        "- This is a draft-MVP engineering review package.",
        "- The package requires engineer review before any project use.",
        "- Material verification is required if an engineer-filled verification CSV "
        "was not applied.",
        "- External validation is a separate workflow and must be completed by an engineer.",
        "- ML advisory-only outputs are not design checks.",
        "- deterministic SP63 checks mandatory for every engineering decision.",
        "- ZIP packaging and manifest checksums do not certify the calculation.",
        "- Full SP 63 text is not included in this repository or archive.",
    ]
