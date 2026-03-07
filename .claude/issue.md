# Issues

- 2026-03-07: `kakaocli status` and `kakaocli login --status` still time out on this Mac during non-interactive verification, even though `kakaocli auth` succeeds and the repo-local query path works.
- 2026-03-07: In non-login shells, `python3` may resolve to the macOS system Python 3.9, which is too old for the pinned Live RAG `fastapi` dependency unless the installer switches to Homebrew Python 3.10+.
