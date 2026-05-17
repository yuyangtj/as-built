"""
Postgres-backed event store.

Two responsibilities: create the schema, and append events durably. Reads come
later (the replay viewer will want them); for the spine, append-and-tail is
enough.

Design notes:
- Events are immutable once written. If a correction is needed, write a new
  event that supersedes — don't UPDATE.
- The `payload` is stored as JSONB so we can query into it later without
  migrations.
- A single index on (tick, id) gives us ordered replay; an index on subject
  gives us per-ticket / per-component threading.
"""

import json
import os
from contextlib import contextmanager
from typing import Iterator

import psycopg

from as_built.events import Event


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY,
    tick BIGINT NOT NULL,
    wall_time TIMESTAMPTZ NOT NULL,
    type TEXT NOT NULL,
    actor TEXT NOT NULL,
    subject TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    caused_by UUID
);

CREATE INDEX IF NOT EXISTS events_tick_idx ON events (tick, wall_time);
CREATE INDEX IF NOT EXISTS events_subject_idx ON events (subject)
    WHERE subject IS NOT NULL;
CREATE INDEX IF NOT EXISTS events_type_idx ON events (type);
"""


def _dsn() -> str:
    """Read the Postgres DSN from env, with a sensible local default."""
    return os.environ.get(
        "AS_BUILT_PG_DSN",
        "postgresql://as_built:as_built@localhost:5433/as_built",
    )


@contextmanager
def _conn() -> Iterator[psycopg.Connection]:
    """Open a connection. Short-lived; for v0 that's fine."""
    with psycopg.connect(_dsn()) as c:
        yield c


def init() -> None:
    """Create the events table if it doesn't exist. Idempotent."""
    with _conn() as c:
        with c.cursor() as cur:
            cur.execute(SCHEMA_SQL)
        c.commit()


def append(event: Event) -> None:
    """Persist one event. The hot path of the system."""
    with _conn() as c:
        with c.cursor() as cur:
            cur.execute(
                """
                INSERT INTO events
                    (id, tick, wall_time, type, actor, subject, payload, caused_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                """,
                (
                    event.id,
                    event.tick,
                    event.wall_time,
                    event.type,
                    event.actor,
                    event.subject,
                    json.dumps(event.payload),
                    event.caused_by,
                ),
            )
        c.commit()


def tail(n: int = 20) -> list[Event]:
    """Return the most recent N events, oldest first. For CLI inspection."""
    with _conn() as c:
        with c.cursor() as cur:
            cur.execute(
                """
                SELECT id, tick, wall_time, type, actor, subject, payload, caused_by
                FROM events
                ORDER BY tick DESC, wall_time DESC
                LIMIT %s
                """,
                (n,),
            )
            rows = cur.fetchall()
    rows.reverse()  # oldest first reads nicer
    return [
        Event(
            id=r[0],
            tick=r[1],
            wall_time=r[2],
            type=r[3],
            actor=r[4],
            subject=r[5],
            payload=r[6],
            caused_by=r[7],
        )
        for r in rows
    ]
