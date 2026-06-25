# K80 Release Artifact Manifest

K80 adds `release-manifest`, a reproducibility metadata command for draft
release handoff:

```bash
python -m sp63_core release-manifest \
  --output-dir reports/release_manifest_smoke \
  --version 0.9.0-rc1 \
  --json
```

The command writes:

- `release_artifact_manifest.json`;
- `release_artifact_manifest.md`;
- `VERSION.txt`.

The manifest records version, git branch, git commit, generation time, key
artifact paths, file sizes, and SHA256 checksums.

This command does not publish a release, certify designs, change formulas,
change material values, implement UI, or make ML project-ready. Engineer review
and deterministic SP63 checks remain mandatory.
