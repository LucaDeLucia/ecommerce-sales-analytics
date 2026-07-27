# Data Dictionary

## `raw/ecommerce_raw.csv` (as exported, before cleaning)

| Column | Type | Description |
|---|---|---|
| `order_id` | string | Unique order identifier |
| `customer_id` | string | Unique customer identifier |
| `order_date` | string (mixed formats) | Date the order was placed |
| `category` | string (inconsistent casing) | Product category |
| `product_name` | string | Product name |
| `unit_price` | float | Price per unit, USD (may include sign errors) |
| `quantity` | int | Units purchased in the order |
| `discount_pct` | int | Discount applied, percent (0–30) |
| `gross_amount` | float | `unit_price * quantity`, pre-discount |
| `shipping_cost` | float (nullable) | Shipping cost charged, USD |
| `net_revenue` | float | `gross_amount` less discount |
| `marketing_channel` | string | Acquisition/marketing channel attributed to the order |
| `payment_method` | string | Payment method used |
| `region` | string (may be blank) | Customer's region |
| `customer_segment` | string (nullable) | Segment recorded at time of order: New / Returning / VIP |
| `returned` | bool | Whether the order was returned |
| `review_score` | float 1–5 (nullable) | Review score left by customer, if any |

## `processed/ecommerce_clean.csv` (post-cleaning)

Same schema as above, plus:

| Column | Type | Description |
|---|---|---|
| `has_review` | bool | Whether `review_score` is present (added instead of imputing a fake score) |

All text fields are standardized; dates are proper `datetime`; duplicates,
negative prices, and blank regions are resolved per the rules documented in
the main `README.md` and notebook §2.

## `exports/customer_rfm_clv.csv`

| Column | Type | Description |
|---|---|---|
| `customer_id` | string | Unique customer identifier |
| `recency` | int | Days since last order (as of snapshot date) |
| `frequency` | int | Number of distinct orders |
| `monetary` | float | Total net revenue from this customer |
| `R`, `F`, `M` | int (1–4) | Quartile scores |
| `RFM_score` | int (3–12) | Sum of R + F + M |
| `segment` | string | Champions / Loyal Customers / Potential Loyalists / At Risk / Hibernating |
| `marketing_channel` | string | Channel attributed to the customer's first order |

## `exports/monthly_summary.csv`

| Column | Type | Description |
|---|---|---|
| `month` | string (YYYY-MM) | Calendar month |
| `orders` | int | Distinct orders placed |
| `revenue` | float | Total net revenue |
| `avg_order_value` | float | Mean net revenue per order |
| `units_sold` | int | Total units sold |

## `exports/orders_dashboard_ready.csv`

Order-level fact table: all columns from `processed/ecommerce_clean.csv`
joined with each customer's `recency`, `frequency`, `monetary`, `segment`,
and K-Means `cluster` — ready to drop straight into Tableau or Power BI.
