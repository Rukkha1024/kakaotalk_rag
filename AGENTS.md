# AGENTS.md

Portable setup instructions for the patched `kakaocli` workflow in this repo.

## Default install path

When the user asks to install or set up KakaoTalk access from this repo on a Mac:

1. From the repo root, run `./install-kakaocli`.
2. Use `./kakaocli-local` for `status`, `auth`, `login`, and raw CLI diagnostics.
3. Use `./query-kakao` for evidence-backed KakaoTalk lookups and summaries.

## Safety

- Do not default to the Homebrew or `PATH` `kakaocli` for this repo.
- Do not run `send`, `sync --follow`, or `harvest` unless the user explicitly asks.
- If setup is blocked, report the exact manual step:
  KakaoTalk install/login, `Full Disk Access`, or `Accessibility`.

## Notes

- The repo-local wrappers resolve paths relative to the copied repo, so they should
  work even when the repo is cloned to a different directory.
- `query-kakao` uses the repo-local `.venv` Python under the hood.
