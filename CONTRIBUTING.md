# Contributing to AWP

AWP is an exploratory protocol project. Contributions are welcome as issues, conformance fixtures, implementation reports, security analyses, editorial corrections, or protocol proposals.

## Before proposing a normative change

1. Identify the affected family, modules, schemas, and conformance roles.
2. State the problem and the observable interoperability or safety consequence.
3. Describe alternatives and compatibility impact.
4. Add or update valid and invalid fixtures with expected diagnostics.
5. Record consequential decisions in `docs/decisions/`.

Normative changes are made only in a working-draft directory. Released specification files, schemas, bundles, and tags are immutable. Corrections to a release are documented as errata or issued under a new version.

## Validation

Install the pinned validation dependency and run the repository checks:

```bash
python -m pip install -r requirements-dev.txt
python tools/validate_spec_examples.py
python tools/validate_spec_0_4.py
python tools/validate_spec_0_5.py
python tools/validate_spec_0_6.py
python tools/validate_spec_0_7.py
python tools/validate_conformance.py
python tools/check_markdown_links.py
python tools/verify_workstate_artifacts.py
python -m unittest discover -s tests -v
```

Generated bundles must be rebuilt and committed with their source changes. Pull requests should explain which requirements and fixtures establish correctness.

## Editorial standard

Normative requirements use BCP 14 terms only where necessary. Claims of determinism, interoperability, security, or implementation maturity require a defined procedure and evidence. Model-generated critiques are informative research inputs and are not peer review.
