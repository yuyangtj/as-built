select
    p.payment_id,
    p.merchant_id,
    m.merchant_name,
    m.country,
    m.category,
    p.amount,
    p.currency,
    round(p.amount * fx.rate_to_eur, 2) as amount_eur,
    p.settled_at
from {{ ref('stg_payments') }} as p
left join {{ ref('stg_merchants') }} as m
    on p.merchant_id = m.merchant_id
left join {{ ref('raw_fx_rates') }} as fx
    on p.currency = fx.currency
