"""
v0 stub generator. Emits a placeholder ticket every N ticks so the orchestrator
has something to dispatch. Will be replaced in order by:
  1. The exogenous generator (scripted sampling)
  2. The consequence engine (rule-based, reads platform state)

The interface (`maybe_emit`) is what the real generators will also implement:
called once per tick by the orchestrator, returns zero or more tickets to add
to the backlog.
"""

from as_built.tickets import SealedInfo, Ticket


class StubGenerator:
    """Emits a fake ticket every `interval` ticks."""

    def __init__(self, interval: int = 5) -> None:
        self.interval = interval
        self._counter = 0

    def maybe_emit(self, tick: int) -> list[tuple[Ticket, SealedInfo]]:
        if tick == 0 or tick % self.interval != 0:
            return []
        self._counter += 1
        ticket = Ticket(
            opened_at=tick,
            severity="medium",
            surface="ci",
            body=f"placeholder ticket #{self._counter} from stub generator",
        )
        sealed = SealedInfo(
            ticket_id=ticket.id,
            origin="stub-generator",
            origin_detail={"counter": self._counter},
        )
        return [(ticket, sealed)]
