select
    merchant_id,
    merchant_name,
    country,
    category
from {{ ref('raw_merchants') }}
