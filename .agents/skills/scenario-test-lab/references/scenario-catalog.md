# Scenario Catalog

Use these patterns to extend scenario suites like S6/S7 safely.

## Naming

- Use key format: `S<number>_<short_name>`
- Keep keys immutable once committed
- Keep title concise and behavior-focused

## Core patterns

1. Duplicate serial + same date -> ambiguous error
2. Duplicate serial + different dates -> date-directed success
3. Backup duplicate + `skip` policy -> skip + continue
4. Backup duplicate + `error` policy -> error + continue
5. Mixed batch -> success/skip/error all in one run

## Extended patterns

6. Triple-row same serial with partial date match
7. Backup has renamed file; ID->serial reverse lookup should detect duplicate
8. Unknown serial in filename should error and not block others
9. Existing renamed file in target folder should trigger conflict-resolution path
10. Region mapping missing should fail copy stage but keep prior stage outcomes

## Scenario quality gates

- Define input files (`.agd`, `.gt3x`) explicitly
- Define subject rows with wear dates explicitly
- Define expected status counts (`success`, `skip`, `error`)
- Define expected final filenames and unchanged originals
- Define required log tokens for evidence

## Agent delegation template

- Agent A: data shape and edge case intent
- Agent B: expected outputs and assertions
- Agent C: anti-overlap review and missing-edge review
