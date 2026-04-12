# Interactive Planning Pattern

> A reusable pattern for collaborative implementation planning between a human and an AI coding assistant. Produces higher-quality plans than solo planning by surfacing decisions and insights at the moment they emerge.

**Author:** Eyal Nof
**Date:** 2026-03-27
**Origin:** Discovered during the structural contextual embeddings planning session. The pattern was not designed in advance — it emerged from the instruction "enter plan mode, but use AskUserQuestion when you need help with decisions and when insights emerge mid-planning."

---

## The Problem

Standard AI planning has two failure modes:

1. **Solo planning** — the AI disappears into plan mode, explores the codebase, makes assumptions about ambiguous decisions, and returns with a finished plan. The human reviews it, finds 3-4 things they'd have chosen differently, the plan gets revised, and a round-trip is wasted.

2. **Over-consultation** — the AI asks about every decision before starting, front-loading 10 questions the human can't meaningfully answer without seeing the codebase context. The human guesses, the AI plans around those guesses, and the plan doesn't fit the code.

Both fail because **the best time to make a decision is when the context for that decision becomes visible** — not before exploration (too early) and not after the plan is written (too late).

---

## The Pattern

**Enter plan mode with an interactive contract:**

> "Enter plan mode. While planning, use AskUserQuestion when you hit decision points or when non-obvious insights emerge that should be integrated."

The AI then:
1. **Explores the codebase** (read-only, as normal in plan mode)
2. **Surfaces decisions in real-time** when it finds a fork in the design — presents options with tradeoffs discovered FROM the code, not hypothetical
3. **Surfaces insights** when exploration reveals something the human didn't know — a reusable service, a schema mismatch, a simpler path
4. **Incorporates answers immediately** into the evolving plan
5. **Writes the final plan** with all decisions already resolved

---

## When to Use It

| Situation | Solo planning | Interactive planning |
|-----------|--------------|---------------------|
| Simple, clear task (fix a bug, add a field) | Use this | Overkill |
| Multiple valid approaches, user has preferences | Wastes a round-trip | **Use this** |
| Large scope, many files, architectural decisions | Plan will have wrong assumptions | **Use this** |
| Codebase has surprises (schema mismatches, reusable services) | Discoveries buried in plan footnotes | **Use this — insights surface live** |
| User is the domain expert, AI is the code expert | AI guesses wrong about domain | **Use this — user guides domain decisions** |

---

## How to Invoke It

### The instruction

```
Enter plan mode. While planning, use AskUserQuestion when:
1. You hit a decision point with multiple valid approaches
2. A non-obvious insight emerges that changes the design
3. You discover something in the codebase the user should know about
```

### What AskUserQuestion should look like during planning

**Decision point example:**
```
The NAI service has detect_schema() that auto-detects SQLite KGs.
This means ctx-kg.db could be loaded directly — but the schemas
differ (from_node/to_node vs source/target). Options:

1. New CtxKGService (separate, clean)
2. Extend NAI with schema mapping (reuse, but fragile)
3. Thin wrapper over Python script (zero duplication)
```

**Insight example:**
```
While exploring the backend, I found that the existing
NAI service already has a 4-weight scoring formula
(embedding + text + graph + intent). Your ctx-to-kg.py
uses 3 weights (text + embedding + graph). Should we
align them or keep them separate?
```

### What AskUserQuestion should NOT be

- "Does this plan look good?" — that's what ExitPlanMode is for
- "Should I continue?" — just continue
- "Do you want me to explore more?" — use judgment, explore if needed
- Questions with obvious answers — only ask when the AI genuinely can't determine the right choice from code alone

---

## The Contract

| Role | Responsibility |
|------|---------------|
| **AI** | Explore thoroughly, surface decisions WITH context (not abstract), present tradeoffs from code reality, incorporate answers into evolving plan |
| **Human** | Make domain/preference decisions, flag when the AI is overthinking, redirect if exploration goes off-track |
| **Both** | Build the plan together — it's a conversation, not a handoff |

---

## Why It Works

1. **Decisions are made with maximum context.** The AI has just read the relevant code. The human has just seen the tradeoffs. Neither is guessing.

2. **Insights are actionable immediately.** When the AI discovers a reusable service mid-exploration, it asks "should we use this?" — and the answer reshapes the plan before it's written.

3. **The plan arrives pre-approved.** Every decision was made collaboratively. The final plan has no surprises. ExitPlanMode becomes a formality, not a negotiation.

4. **It's faster than solo + revision cycles.** One interactive pass replaces 2-3 solo-plan-then-revise cycles.

---

## Example: Real Session (2026-03-27)

Planning 5 features for structural contextual embeddings integration.

**Questions surfaced during planning:**

| # | Question | Why it mattered |
|---|----------|----------------|
| 1 | Should /ctx -search run Python script or read DB directly? | Portability vs integration — script approach won because the skill must be project-agnostic |
| 2 | Pick benchmark repos now or at execution time? | Flexibility — deferred to execution time |
| 3 | Extend NAI or build CtxKGService? | Schema mismatch discovered mid-exploration changed the recommendation from "extend NAI" to "new service" |
| 4 | Standalone spec or chapter in existing doc? | Scope — standalone won for publishability |
| 5 | NAI has auto-detect schema — leverage it? | Insight: simpler integration path than expected, but schema differences made it fragile |
| 6 | Heuristic .ctx gen vs AI-generated for benchmark? | Cost — chose both: heuristic baseline + AI comparison |

**Result:** 5-phase plan with all decisions resolved, no revision needed. Plan approved on first pass.

---

## Reuse Template

Copy-paste this instruction when starting a complex planning session:

```
Enter plan mode. This is interactive planning, not solo planning:
- When you hit a decision point with multiple valid approaches, ask me
- When a non-obvious insight emerges during exploration, surface it
- When you discover something in the codebase I should know about, tell me
- Build the plan WITH me, not FOR me
```
