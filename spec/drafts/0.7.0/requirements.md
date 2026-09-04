# Draft requirement registry

The generated [`requirements.json`](requirements.json) inventories lines in the 0.7.0 working draft that contain uppercase BCP 14 requirement terms. Draft identifiers have the form `AWP-<DOCUMENT>-NNN` and are deterministic for the current source order.

These identifiers are review aids while 0.7.0 remains a working draft. Before release, each normative requirement must be reviewed for atomicity, assigned a stable identifier in the source text, mapped to conformance roles and fixtures, and frozen. The generated inventory does not replace normative prose and may include a line containing more than one requirement.

Regenerate the inventory with:

```bash
python tools/build_requirements_registry.py
```
