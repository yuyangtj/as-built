"""
The ticket is the universal interface between work-generators and the team.

It has two halves:

- The *visible half* (`Ticket`) is what the worker sees. Symptoms and asks,
  never origin or cause.
- The *sealed half* (`SealedInfo`) stays with the harness and is used for
  grading the worker's resolution and later for telling the story in the
  replay viewer.

For the spine, both halves are minimal. Real generators will fill the sealed
half with rule references, causal traces, and resolution hooks; for now the
stub generator emits placeholder values.
"""

from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


TicketStatus = Literal["open", "pulled", "resolved", "stuck"]


class Ticket(BaseModel):
    """The visible half — what the worker reads."""

    id: UUID = Field(default_factory=uuid4)
    opened_at: int
    """The tick this ticket was created on."""

    severity: Literal["low", "medium", "high"] = "medium"
    surface: str
    """*Where* the symptom is observed: 'ci', 'dashboard', 'downstream',
    'stakeholder'. Tells the worker where to start looking."""

    body: str
    """Symptom or ask, in natural language. Symptom-only — never the cause."""

    status: TicketStatus = "open"


class SealedInfo(BaseModel):
    """The sealed half — origin, ground truth, grading hook.

    Never given to the worker. Used by the harness to grade the resolution
    and (later) by the postmortem extractor.
    """

    ticket_id: UUID
    origin: str
    """'consequence-engine' or 'exogenous-generator'."""

    origin_detail: dict = Field(default_factory=dict)
    """For consequence tickets: rule id + binding. For exogenous: event kind
    + parameters. Free-form for now."""

    causal_trace: list[UUID] = Field(default_factory=list)
    """Event ids that, taken together, are this ticket's cause. Populated
    later by the real generators; empty in v0 stub."""
