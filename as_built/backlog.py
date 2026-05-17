"""
The backlog holds open tickets and lets the orchestrator pick the next one
to dispatch. In v0 it's an in-memory list; a real deployment would back it
with Postgres so the campaign survives restarts.

The backlog also owns the sealed half of each ticket. The visible half is
what gets handed to the worker; the sealed half stays here for grading.
"""

from uuid import UUID

from as_built.tickets import SealedInfo, Ticket


# Priority by severity. Lower is higher priority.
_SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}


class Backlog:
    def __init__(self) -> None:
        self._tickets: dict[UUID, Ticket] = {}
        self._sealed: dict[UUID, SealedInfo] = {}

    def add(self, ticket: Ticket, sealed: SealedInfo) -> None:
        self._tickets[ticket.id] = ticket
        self._sealed[ticket.id] = sealed

    def get(self, ticket_id: UUID) -> Ticket:
        return self._tickets[ticket_id]

    def get_sealed(self, ticket_id: UUID) -> SealedInfo:
        return self._sealed[ticket_id]

    def set_status(self, ticket_id: UUID, status) -> None:
        self._tickets[ticket_id].status = status

    def next_open(self) -> Ticket | None:
        """Pick the next ticket to dispatch. Severity then age."""
        opens = [t for t in self._tickets.values() if t.status == "open"]
        if not opens:
            return None
        opens.sort(key=lambda t: (_SEVERITY_RANK[t.severity], t.opened_at))
        return opens[0]

    def count(self, status=None) -> int:
        if status is None:
            return len(self._tickets)
        return sum(1 for t in self._tickets.values() if t.status == status)
