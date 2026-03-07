---
name: progress-md-workflow
description: Create or update timestamped progress markdown notes for ongoing technical work. Use when the user asks to make a progress md, create a session note, write a work log, document what was broken and what was done, summarize validation, or capture next improvements. Best for `progress/*.md` files and workflows that require file names like `YYMMDD-HHMM-subject.md`.
---

# Progress Md Workflow

## Overview

Create a new progress note with a deterministic file name and a consistent evidence-first structure.
Use the bundled script to scaffold the file first, then fill it with repository-specific facts, validations, and next improvements.

## Workflow

### 1. Gather the facts first

- Read the user request, the target repo's existing `progress/` notes, recent commits, and the validation outputs that matter.
- Extract the concrete answers to these questions before writing:
  - What was broken or missing?
  - What was changed in this milestone?
  - How was it verified?
  - What still needs improvement?
- If the user asked for a new note, prefer creating a new file instead of rewriting an existing progress note.
- If the user asked to update an existing `.md` file, also use [$md-style-preserving-edit](/Users/alice/Documents/codex/.agents/skills/md-style-preserving-edit/SKILL.md).

### 2. Create the file with the project naming rule

- Use `scripts/new_progress_note.py` to create the file.
- Default naming rule: `YYMMDD-HHMM-subject.md`.
- Normalize `subject` to lowercase hyphen-case ASCII.
- Put the file in the closest relevant `progress/` directory unless the user specifies another location.
- For this workspace, Kakao Live RAG notes usually belong in `/Users/alice/Documents/codex/kakaocli-patched/progress`.

### 3. Fill the required sections

Keep the note concise, but always cover these sections:

- `## Goal`
- `## What Was The Problem`
- `## What Was Done`
- `## Validation`
- `## Future Improvements`

Add these when they materially help:

- `## Design Motive`
- `## Artifacts`
- `## References`

Writing rules:

- Explain the state transition, not just the file diff.
- Name the failure mode explicitly.
- Tie validations to exact commands, counts, hashes, or commit ids when they are high-signal.
- Keep bullets flat and scannable.
- Avoid changelog spam and avoid copying terminal output unless the output itself is the evidence.

### 4. Apply the Vercel-inspired split correctly

- Use `AGENTS.md` for persistent repository-wide behavior that should apply on every turn.
- Use this skill for the explicit, repeatable progress-note workflow.
- Do not rely on the skill alone for behaviors that must always happen.
- Read `references/vercel-motivation.md` when you need the rationale or need to explain why this split exists.

### 5. Report the result

- Return the file path you created or updated.
- Summarize the note in 1-3 lines: problem, work, next.
- If the note is in a git repo, commit it when the repo instructions require commits.

## Resources

### scripts/

- `scripts/new_progress_note.py`
  - Scaffold a new note with the required file name format and standard sections.
  - Use `conda run -n module python` to execute it in this workspace.

### references/

- `references/vercel-motivation.md`
  - Read when the user asks why the workflow uses both `AGENTS.md` and a skill.
  - Use it when adapting this workflow to another repo.

## Example Invocation

```bash
conda run -n module python /Users/alice/Documents/codex/.agents/skills/progress-md-workflow/scripts/new_progress_note.py \
  --output-dir /Users/alice/Documents/codex/kakaocli-patched/progress \
  --subject live-rag-codex-autostart
```

Then edit the generated file with the collected evidence from the current task.
