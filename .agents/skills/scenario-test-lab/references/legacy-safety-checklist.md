# Legacy Safety Checklist

Use this checklist before editing any file.

## 1) Mark mutation boundary

- Allowed by default: `tests/**`
- Disallowed by default: all production/legacy code and configuration
- If user says a file is legacy, treat as immutable

## 2) Prefer additive changes

- Create new test files before modifying existing ones
- Keep old scenarios unchanged unless user explicitly asks to replace
- Never run destructive git commands to force clean state

## 3) Confirm scope

- If requested change touches non-test files, stop and ask user
- If ownership of a file is ambiguous, ask once with concrete options

## 4) Verify isolation

- Ensure dummy data lives in temp directory
- Ensure tests do not rely on external mutable production data
- Ensure cleanup runs even when scenario fails

## 5) Run policy

- Use `conda run -n module ...`
- Run conda commands serially (no parallel conda execution)
