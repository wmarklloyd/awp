# Distribution artifacts

This directory contains generated, self-contained specification bundles. Source documents and schemas remain authoritative as stated by each release.

- `0.4.0/` and `0.5.0/` contain historical bundles.
- `0.6.0/` contains the current stable bundle and checksums.
- `drafts/` contains generated working-draft bundles and is not a release channel.

Generated files must be reproducible from the corresponding builder under `tools/`. A release checksum authenticates byte identity only; it does not establish authorship, safety, or correctness.
