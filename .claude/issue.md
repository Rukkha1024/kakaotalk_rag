# Issues

- 2026-03-07: KakaoTalk setup guidance had been split across repo AGENTS files and multiple skill locations, so copying only one skill would not reliably preserve the full install workflow on another Mac.
- 2026-03-07: `kakaocli status` and `kakaocli login --status` can still time out on this Mac during non-interactive verification, even when `kakaocli auth` and `query-kakao` succeed.
- 2026-03-07: Duplicate `kakaocli` skill definitions existed in `.agents/skills`, `kakaocli-patched/skills`, and `/Users/alice/.codex/skills`, which made the canonical location ambiguous for this workspace.
