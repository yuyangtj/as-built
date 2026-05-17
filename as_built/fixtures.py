"""
Hand-crafted fixture tickets for smoke testing the real LLM worker.

# DELETE WHEN EXOGENOUS LANDS
# These fixtures exist only until the real exogenous generator (step 5) and
# consequence engine (step 4) are implemented. At that point this file and
# the fixture generator referencing it can be removed.

Each ticket is a realistic situation the worker can plausibly attempt using
only the current platform (stg_payments, stg_merchants, int_settled_amounts,
mart_revenue_summary, dashboard.csv).
"""

from as_built.tickets import SealedInfo, Ticket


def _make(
    severity: str,
    surface: str,
    body: str,
    fixture_id: str,
) -> tuple[Ticket, SealedInfo]:
    ticket = Ticket(
        opened_at=0,  # stamped with the real tick by the generator
        severity=severity,
        surface=surface,
        body=body,
    )
    sealed = SealedInfo(
        ticket_id=ticket.id,
        origin="fixture",
        origin_detail={"fixture_id": fixture_id},
    )
    return ticket, sealed


FIXTURES: list[tuple[Ticket, SealedInfo]] = [
    # 1. Easy happy path — add a column to the mart.
    _make(
        severity="low",
        surface="stakeholder",
        body=(
            "The BI team wants a new column on the revenue dashboard: "
            "the number of distinct settlement dates per merchant, which "
            "they're calling 'active_days'. They need it for a cohort "
            "analysis they're building. Please add it to the mart summary."
        ),
        fixture_id="add_active_days_column",
    ),
    # 2. Pending payments investigation — diagnosis tests the stg filter.
    _make(
        severity="medium",
        surface="dashboard",
        body=(
            "Finance spotted payment pay_005 (TechHub Berlin, SEK, status=pending) "
            "and wants to know whether it is being included in the revenue dashboard. "
            "They're worried that pending payments are leaking into settled revenue totals. "
            "Please investigate and confirm — or fix — the pipeline's handling of pending payments."
        ),
        fixture_id="pending_payments_investigation",
    ),
    # 3. FX conversion sanity check — worker needs to trace the join.
    _make(
        severity="medium",
        surface="dashboard",
        body=(
            "A stakeholder is questioning London Finserv's dashboard total (mer_004). "
            "They have three GBP payments and the EUR totals look higher than a rough "
            "manual calculation. Please verify that the GBP-to-EUR conversion rate is "
            "being applied correctly and that the fx join isn't creating duplicate rows."
        ),
        fixture_id="fx_conversion_check",
    ),
    # 4. Open-ended — country grouping consistency check.
    _make(
        severity="low",
        surface="downstream",
        body=(
            "The downstream data team groups the mart by country and sums total_revenue_eur. "
            "Their France aggregate (Parisian Boutique + Lyon Essentials) comes out to 1077.74 EUR, "
            "matching the two rows in the dashboard CSV, but they expected a single France row "
            "and suspect there might be a double-count somewhere. "
            "Please verify the mart aggregation and confirm whether the downstream query approach is sound."
        ),
        fixture_id="france_country_totals",
    ),
]
