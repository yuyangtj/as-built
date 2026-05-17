"""
The event log is the source of truth for what happened in a campaign.

Every meaningful action in the system emits one of these. The replay viewer,
the oversight surface, and any later analysis all read from this log.

The schema is deliberately small: a stable core plus a JSON payload for
type-specific details. New event types are added by convention, not by schema
migration — that's intentional, so the system stays cheap to extend during
v0's rapid iteration.
"""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Event(BaseModel):
    """A single thing that happened in the campaign."""

    id: UUID = Field(default_factory=uuid4)
    tick: int
    """Simulated campaign time. The orchestrator's clock counter."""

    wall_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    """When the event was actually emitted. Useful for debugging and for the
    live-deployment 'campaign running since X' surface."""

    type: str
    """A short string identifying what kind of event this is. Not an enum on
    purpose — keep it cheap to add new types as the system grows."""

    actor: str
    """Who or what did this. E.g. 'orchestrator', 'worker:w1', 'generator:exo',
    'generator:consequence', 'harness'. A free-form label."""

    subject: str | None = None
    """What the event is *about*. A ticket id, a component name, a lesson id.
    Lets the viewer group related events into threads. Optional because some
    events (like tick advances) aren't about anything in particular."""

    payload: dict[str, Any] = Field(default_factory=dict)
    """Type-specific data. Documented per type but not enforced at the schema
    level. Keep it JSON-serialisable."""

    caused_by: UUID | None = None
    """Optional pointer to the event that triggered this one. When present, it
    lets the viewer reconstruct causal chains across long campaigns — which
    is most of what makes the system interesting to look at."""
