select
    merchant_id,
    merchant_name,
    country,
    category,
    count(payment_id)               as payment_count,
    round(sum(amount_eur), 2)       as total_revenue_eur,
    round(avg(amount_eur), 2)       as avg_payment_eur,
    count(distinct settled_at)      as active_days,
    min(settled_at)                 as first_settlement,
    max(settled_at)                 as last_settlement
from {{ ref('int_settled_amounts') }}
group by 1, 2, 3, 4
order by total_revenue_eur desc
