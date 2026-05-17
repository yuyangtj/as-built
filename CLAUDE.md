# Working with Claude Code on `as-built`

This doc orients an LLM pair-programmer (Claude Code or similar) that has just opened this repo. It is *not* a design document — for that, read `docs/design-story.md` first; it explains why the system is shaped the way it is. This doc is about how to *work* in the codebase.

---

## What this project is, in one paragraph

A campaign-mode simulation of a data platform operated by agents. The platform is the protagonist; agents are the medium through which a viewer encounters its biography. Work arrives from a sampling-based exogenous generator (stakeholder requests, upstream events) and from a rule-based consequence engine (the platform's own past decisions catching up with it). Every action emits an event to a Postgres-backed event log, which a replay viewer will later render. The whole thing is designed as a portfolio piece — depth over breadth, demo-readability is a first-class concern.

## Where things stand right now

The **spine** is implemented: tick loop, event log, stub generator, stub worker. It runs end-to-end. Every other component is either designed (in `docs/design-story.md`) or unwritten.

The work pattern is **replace stubs one at a time** with real implementations. Do not introduce new components ahead of their slot in the sequence. The sequence is:

1. *(done)* spine: orchestrator, event log, stub generator, stub worker
2. **next**: real platform skeleton — bare dbt project on DuckDB, a couple of source-modelled tables, a CSV "dashboard"
3. real worker — LLM-driven, action-vocabulary contract, operates on the dbt project
4. real consequence engine — Spectrum identifier-length rule first
5. real exogenous generator — scripted sampling with preconditions
6. memory store — simplified 4-field schema, semantic retrieval
7. schema registry adoption — the v0 climax
8. replay viewer — separate concern, reads from event log only

## Conventions that matter

These came out of design conversations and are not negotiable without going back to the design story:

**Event log is the source of truth.** Every meaningful action emits an event. If a component does something the replay viewer would want to render, it must emit an event. If you find yourself adding internal state to a component that isn't reflected in the log, stop and reconsider.

**Events are immutable.** Never UPDATE an event row. If something needs correcting, write a new event.

**The five-step tick order is locked.** `_advance_clock → _solicit_work → _dispatch → _step_workers → handle_completions`. Reordering changes the meaning of timestamps in the replay. Don't reorder without a design conversation.

**One worker step per tick.** The worker emits exactly one action per tick. This gives the replay viewer a readable rhythm. Resist the urge to let a worker "run to completion" within a tick.

**Tickets have two halves.** The visible half (`Ticket`) is what the worker sees. The sealed half (`SealedInfo`) stays with the harness. Never leak sealed info into the worker's context, even accidentally — diagnosis is supposed to happen blind.

**Stubs stay stubs until their slot.** The stub generator/worker exist so the loop can run end-to-end before any real component is built. Don't extend the stubs with quasi-real behaviour; replace them when their slot arrives.

**Memory is not in v0's spine.** Don't introduce it as a side dependency. It arrives as its own replacement, after the real worker.

**No new event types without a comment.** When adding an event type, add a short comment near the emission point describing what the payload contains. The schema is intentionally not enum-enforced; the discipline is documentation, not types.

## The next session: real platform skeleton

This is the next replacement. Its goal is to give the (still-stubbed) worker something real to operate on, so that the *session after this* can swap in a real LLM worker without also having to build a platform at the same time.

**Scope:**

- A `platform/` directory at the repo root containing a real dbt project.
- DuckDB as the warehouse, file-based (the .duckdb file lives in `platform/`).
- A handful of seed CSV files standing in for upstream sources.
- 2–3 dbt models: staging, an intermediate join, a mart.
- A "dashboard" implemented as a CSV file output from the mart on every build (using a dbt post-hook or a small Python wrapper).
- A `Platform` class in `as_built/platform.py` that knows how to: list models, read a model's SQL, run `dbt build`, read the dashboard CSV. This is the future worker's read/write surface.

**Not in scope this session:**

- Anything that resembles a "real worker." The stub stays.
- Any consequence rules. The platform should be bug-free at v0 start; bugs come from the worker's own actions later.
- A schema registry. That's the v0 climax, not the foundation.
- Anything fancy in the dbt project (snapshots, complex jinja, packages). Keep it boring.

**Quality bar:**

- `dbt build` runs cleanly from a fresh checkout in under 10 seconds.
- The CSV dashboard appears at a known path after a build.
- The `Platform` class is small (under ~150 lines) and has one obvious way to do each thing.

**One design decision to surface before coding:** the `Platform` class is the read/write surface for a worker that doesn't yet exist. There's a temptation to design it richly now, anticipating worker needs. Resist this. Build the minimum surface that a stub worker could use to inspect and modify the dbt project (`list_models`, `read_model`, `write_model`, `build`, `read_dashboard`). When the real worker arrives, *it* will tell us what other affordances are needed.

## How to ask the human good questions

The human (Yang) is a working data engineer at Klarna; treat his domain knowledge as senior. He prefers depth over breadth, dislikes premature abstraction, and is alert to scope creep — this project has explicit out-of-scope items (see `docs/scope.md` once written, or the design story).

When a fork appears that wasn't anticipated in the design:

- *If it's a small, local decision* (variable name, file layout within a module): just make it; don't ask.
- *If it might affect the contract between components* (event schema, ticket shape, the orchestrator's tick order): stop and surface it. Ask explicitly. These decisions belong in chat with the human, not in code.
- *If it's a domain decision* (which dbt patterns to use, what counts as realistic platform structure): defer to the human; he knows more than you do here.

When in doubt, lean toward asking. Re-litigating a contract decision in code is much more expensive than asking up front.

## Working style preferences

- Small commits over big ones. One logical change per commit.
- Comment the *why*, not the *what*. The code mostly explains itself; the design rationale doesn't.
- Tests come *after* a piece is real, not for stubs. Write tests for the platform interface, not for the stub worker.
- Prefer standard library and small dependencies. The full dependency list should be readable in one screen.
- Python 3.11+, type hints throughout, pydantic for any data with a schema.

## Things this doc does *not* cover

- Long-term architecture. See `docs/design-story.md`.
- Why we chose campaign mode, B-mode, schema registry as first component, etc. See `docs/design-story.md`.
- Implementation details of components that haven't been built yet. Those get their own design conversations as their slot arrives; trying to spec them now produces stale plans.

If something feels under-specified, that's likely because it hasn't been designed yet — surface it, don't invent it.
