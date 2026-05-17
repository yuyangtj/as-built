"""
Fixture-driven generator. Emits hand-crafted tickets in sequence, one per
interval ticks, until the fixture list is exhausted.

Replaces the placeholder stub generator for the real-worker session.
Will be replaced by the real exogenous generator (step 5 in the sequence).
"""

from as_built.fixtures import FIXTURES
from as_built.tickets import SealedInfo, Ticket


class StubGenerator:
    """Emits one fixture ticket every `interval` ticks, in order."""

    def __init__(self, interval: int = 5) -> None:
        self.interval = interval
        self._idx = 0

    def maybe_emit(self, tick: int) -> list[tuple[Ticket, SealedInfo]]:
        if tick == 0 or tick % self.interval != 0:
            return []
        if self._idx >= len(FIXTURES):
            return []
        ticket, sealed = FIXTURES[self._idx]
        # Stamp the real tick — fixtures are built with opened_at=0.
        ticket = ticket.model_copy(update={"opened_at": tick})
        self._idx += 1
        return [(ticket, sealed)]
