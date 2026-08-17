# /agents — Project Memory & Planning

This folder is the single source of truth for project history, decisions, and progress. Any human or AI agent picking up this project should read `CONTEXT.md` first, then check the other files as needed.

## Files

| File | Purpose | Update when |
|---|---|---|
| `CONTEXT.md` | Fast orientation — what this project is, stack, current state | Rarely — only when the fundamentals shift |
| `IMPLEMENTATION_PLAN.md` | Ordered, step-wise roadmap with dependencies | When scope/sequencing changes |
| `CHECKLIST.md` | Granular tickable tasks per phase | Every work session |
| `DECISIONS.md` | Why we chose X over Y, for every important call | Whenever a non-trivial decision is made |
| `CHANGES.md` | What was actually built/changed, tied to a decision | After every major change ships |

## Workflow for an agent (human or AI) starting a session
1. Read `CONTEXT.md` — orient in under a minute.
2. Check `CHECKLIST.md` — see what's next / in progress.
3. Check `IMPLEMENTATION_PLAN.md` — confirm the step you're on and its dependencies.
4. Do the work.
5. Log it:
   - Made a non-trivial call? → new entry in `DECISIONS.md`
   - Shipped something? → new entry in `CHANGES.md`
   - Finished a task? → tick it in `CHECKLIST.md`

## ID convention
- Decisions: `D-001`, `D-002`, ...
- Changes: `C-001`, `C-002`, ...
- Cross-reference IDs across files instead of duplicating explanations (e.g. a CHANGES entry links back to the DECISIONS entry that justified it).
