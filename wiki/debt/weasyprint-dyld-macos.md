---
title: WeasyPrint can't find pango/cairo dylibs at runtime on macOS Apple Silicon
type: debt
severity: low
status: mitigated
filed: 2026-05-27
sources: [app/pdf_tools.py, run_agent.sh, reset_and_run.sh]
updated: 2026-05-27
---

# WeasyPrint pango/cairo dylib path on macOS Apple Silicon

Surfaced during smoke run 2026-05-27 — T7 failed both attempts with:

```
WeasyPrint could not import some external libraries. Please carefully follow the installation steps before reporting an issue:
https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation
```

## Description

`brew install pango cairo` installs dylibs to `/opt/homebrew/lib/` on Apple Silicon. macOS dynamic linker doesn't include `/opt/homebrew/lib` in its default search path for Python processes launched without Homebrew shim. WeasyPrint's `cffi` bindings fail to load `libgobject-2.0`, `libcairo`, `libpango` etc → T7 hard-fails.

Verified the libs are present:

```
$ ls /opt/homebrew/lib/libpango* /opt/homebrew/lib/libcairo*
# All present
```

Verified the fix unblocks WeasyPrint:

```
$ DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib .venv/bin/python -c "from weasyprint import HTML; print('weasyprint OK')"
weasyprint OK
```

## Mitigation

`run_agent.sh` + `reset_and_run.sh` now export:

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib:${DYLD_FALLBACK_LIBRARY_PATH:-}
```

before invoking `app.main`. T7 now succeeds end-to-end via the shipped runner scripts.

## Impact

Users invoking `python -m app.main` directly (without the runner scripts) on macOS Apple Silicon hit the failure. Behavior is correct — T7 fails clearly, retries cap=2, escalates `needs_human` per [[debt/3-attempt-cap-may-be-low]] config. Pipeline doesn't corrupt state.

Linux + macOS Intel + dockerized: unaffected.

## Open follow-ups

- README §Setup could include a note: "On macOS Apple Silicon, use `./run_agent.sh` rather than calling `python -m app.main` directly (sets `DYLD_FALLBACK_LIBRARY_PATH` for WeasyPrint)."
- Long-term cleaner fix: set the env var inside `pdf_tools.export_pdf` before importing weasyprint, or via a tiny `app/_macos_dyld.py` that runs on import. Both have downsides (side-effects on import; would need to detect macOS). Current shell-level fix is the cleanest place.

## Related

- [[modules/pdf-tools]]
- [[decisions/adr-8-t7-wiring]]
