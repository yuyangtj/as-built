# as-built

An opinionated data platform with a biography. A campaign-mode simulation where one or more agents operate a real dbt/DuckDB platform over a long horizon, with work arriving from stakeholders (exogenous) and from the platform's own past decisions catching up with it (endogenous). The platform grows and matures as the campaign runs; what it becomes is the project's actual deliverable.

See `docs/design-story.md` for the *why* behind the design choices.

## Status

**v0 — spine.** Just the tick loop, event log, stub work generator, stub worker. No real platform yet, no real agents, no real consequences. The point is to get the loop turning end-to-end before replacing any piece with its real implementation.

## Running locally

You need Python 3.11+, Postgres, and `uv` (or pip).

```bash
# Start a local Postgres in Docker
docker compose up -d

# Install dependencies
uv sync

# Initialise the event log schema
uv run as-built init

# Run a short campaign (50 ticks, stub worker)
uv run as-built run --ticks 50
```

Events go to Postgres in the `as_built` database. Inspect them with:

```bash
uv run as-built tail
```

## What gets built next

The spine is in place. Replace stubs one at a time:

1. Real worker contract over a real dbt project (DuckDB, a couple of models)
2. Consequence engine (Spectrum identifier-length rule first)
3. Exogenous generator (scripted sampling)
4. Memory store
5. Schema registry adoption — the v0 climax
6. Replay viewer reading the event log

See `docs/scope.md` for the explicit v0 ceiling.
