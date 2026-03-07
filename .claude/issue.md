# Issues

- 2026-03-07: The default `PATH` or Homebrew `kakaocli` on this Mac can still resolve to the upstream build, while reliable KakaoTalk access depends on the local patched binary in `/Users/alice/Documents/codex/kakaocli-patched/.build/release/kakaocli`.
- 2026-03-07: The global `kakaocli-safe-ops` skill and the repo AI integration docs had drifted apart, so agent routing for information queries vs raw diagnostics was ambiguous.
- 2026-03-07: `/Users/alice/Documents/codex/kakaocli-patched/.build/release/kakaocli status` and `auth` still hung during smoke verification on this Mac, even though `login --status` and the Live RAG query path responded successfully.
