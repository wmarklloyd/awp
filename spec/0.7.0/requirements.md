# Draft requirement registry

The generated [`requirements.json`](requirements.json) inventories lines in the AWP 0.7.0 release that contain uppercase BCP 14 requirement terms. Release identifiers have the form `AWP-<DOCUMENT>-NNN` and are frozen for this source order.

These identifiers are review aids and do not replace normative prose. Each entry identifies the source line and may contain more than one requirement; cross-record semantics remain governed by the release text and schemas.

Regenerate the inventory with:

```bash
python tools/build_requirements_registry.py
```
