select
    payment_id,
    merchant_id,
    cast(amount as decimal(12, 2)) as amount,
    currency,
    status,
    cast(settled_at as date) as settled_at
from {{ ref('raw_payments') }}
where status = 'settled'
