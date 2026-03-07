# Vercel Motivation

Use this note when explaining why this workspace keeps both persistent `AGENTS.md` guidance and a dedicated progress-note skill.

## External Motive

- Vercel reported that a compact `AGENTS.md` docs index outperformed skills in their agent evals because it removed the decision of whether to load the guidance at all.
- Their result was not "skills are useless"; it was that broad, recurring behavior is more reliable when always present, while explicit workflow packaging still has value.
- Vercel's Agent Resources docs also treat markdown resources, reusable skills, and end-to-end CLI workflows as separate but complementary tools.
- The Vercel skills project describes skills as reusable instruction sets that extend an agent with specialized, repeatable procedures.

## Local Modification

- Put always-on repo behavior in `AGENTS.md`.
- Put repeatable progress-note creation in `$progress-md-workflow`.
- Encode the local file naming rule directly in the skill script: `YYMMDD-HHMM-subject.md`.
- Encode the local note structure directly in the skill: problem, work, validation, future improvements.
- Prefer a new progress note over mutating older notes unless the user explicitly asks for an update.

## Source Links

- Vercel blog: `AGENTS.md` outperforms skills in our agent evals
  - https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals
- Vercel docs: Agent Resources
  - https://vercel.com/docs/agent-resources
- Vercel Labs: Skills
  - https://github.com/vercel-labs/skills
