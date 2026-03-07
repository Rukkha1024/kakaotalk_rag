## Work Procedure
1. **Plan the changes**: Before making any code modifications, create a detailed plan outlining what will be changed and why
2. **Get user confirmation**: Present the plan to the user and wait for explicit confirmation before proceeding
3. **Modify code**: Make the necessary code changes according to the confirmed plan
4. **Git Commit**: Commit changes with a Korean commit message that reflects the user's intent, at least **5 lines** long.
5. **Run and Verify**: Execute the code and perform MD5 checksum comparison between new outputs and reference files if pipelines or logic were changed.
6. **Finalize**: Clearly specify which skills were used in the final response. Remove unnecessary files and folders.

----
# Codebase Rule

- Do not restore or roll back files/code that you did not modify yourself. Never attempt to "fix" or revert changes in files unrelated to your current task, including using `git checkout`.
- Use `polars` then `pandas` library. 
- Leverage Parallel Agent Execution: use multiple agents to handle different parts of the task concurrently. Proactively launch multiple independent tasks (search, read, validation) simultaneously to reduce turnaround time.
- use UTF-8 with BOM (`utf-8-sig`) by default.
- Unless instructed otherwise, completely replace old logic for bug fixes, but ask the user whether to retain existing logic when adding new features.
- use `$md-style-preserving-edit`, `$copy-editing`  skills when editting .md file.
- Use `$progress-md-workflow` when the user asks to create or update a timestamped progress markdown note or work log.
- Use `$readme-update-only` skill when the user asks to revise, refresh, reorganize, or maintain README content, or when the user explicitly types `$readme-update-only`. Rather than explaining the code itself, write for those who may not know how to code. Focus on execution commands and the overall workflow of the project.
- Python Files: Write a docstring of 7 lines or fewer explaining the core function and logic. Keep it concise so that anyone opening the file can immediately understand its purpose.
- Use $kakaocli-safe-ops for KakaoTalk tasks on this Mac. For non-Kakao tasks, do not use kakaocli or its skill. Never send messages to other people without my explicit confirmation.
- For KakaoTalk information requests, first run `conda run -n module python /Users/alice/Documents/codex/kakaocli-patched/tools/live_rag/query.py --json --query-text "<request>"`.
- The Live RAG query entrypoint must ensure the launchd-backed webhook server and sync follower are running before answering.
- Ground KakaoTalk answers in retrieved chat evidence whenever the query returns hits.


## Architecture Rule

| Principle | Description |
|-----------|-------------|
| **Domain Isolation** | `src/` is divided into domain-specific folders. When requesting a feature from AI, only the relevant domain folder is provided as context, preventing hallucination and code interference. |
| **Pipeline ↔ Analysis Separation** | `scripts/` (data pipeline) and `analysis/` (statistical analysis) operate in completely separate contexts. Analysis code depends solely on the pipeline's final output file. |
| **Centralized Configuration** | All parameters are managed in YAML files under `configs/`, eliminating hard-coded values. |
| **Explicit Execution Order** | Script filenames carry numeric prefixes to make pipeline flow immediately apparent. |

----
# ExecPlans
When writing complex features or significant refactors, use an ExecPlan (as described in .agent/PLANS.md) from design to implementation.

## Phase 1: Requirements Discovery
Use `.agents/REQUIREMENTS_TEMPLATE.md` to guide a discovery session with the user. Ask questions in batches of 3-5. If answers are vague, push back. Do NOT proceed until the user confirms the completed brief.

## Phase 2: Plan Authoring
Write an ExecPlan(`.agents\execplans`, korean & english ver.) per `.agents/PLANS.md`. Present it to the user. Do NOT implement until the user approves.

## Phase 3: Implementation
Follow the approved ExecPlan. Proceed through milestones autonomously without prompting the user. Keep all living document sections up to date. Commit frequently. If blocked, stop and ask.


----
# Codebase andrej-karpathy Rules 

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

