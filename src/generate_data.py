"""
generate_data.py
-----------------
Generates a realistic, intentionally-messy e-commerce transactions dataset
for the purpose of demonstrating a full data-cleaning + analysis workflow.

The dataset simulates ~2 years of online retail orders (Jan 2023 - Dec 2024)
across multiple product categories, regions, marketing channels and customer
segments, with realistic seasonality (Nov/Dec holiday spike, summer lull),
and deliberately injected data-quality issues:
    - missing values (customer info, review scores, shipping cost)
    - duplicate rows
    - inconsistent text casing / whitespace
    - a handful of outlier / negative values
    - mixed date formats in a small subset of rows

Run:
    python src/generate_data.py
Output:
    data/raw/ecommerce_raw.csv
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

RNG = np.random.default_rng(42)

N_ORDERS = 18000
N_CUSTOMERS = 4200

START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2024, 12, 31)

REGIONS = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East & Africa"]
REGION_WEIGHTS = [0.38, 0.28, 0.20, 0.09, 0.05]

CATEGORIES = {
    "Electronics": ["Wireless Earbuds", "Smartwatch", "Bluetooth Speaker", "Laptop Stand", "USB-C Hub", "Phone Case"],
    "Home & Kitchen": ["Air Fryer", "Coffee Maker", "Knife Set", "Throw Blanket", "Desk Lamp", "Storage Bins"],
    "Apparel": ["Running Shoes", "Denim Jacket", "Yoga Pants", "Wool Sweater", "Graphic Tee", "Rain Jacket"],
    "Beauty & Personal Care": ["Face Serum", "Hair Dryer", "Electric Toothbrush", "Perfume", "Makeup Palette"],
    "Sports & Outdoors": ["Yoga Mat", "Camping Tent", "Water Bottle", "Resistance Bands", "Hiking Backpack"],
    "Toys & Games": ["Board Game", "Puzzle 1000pc", "RC Car", "Building Blocks Set", "Plush Toy"],
    "Office Supplies": ["Ergonomic Chair", "Notebook Set", "Wireless Mouse", "Desk Organizer", "Whiteboard"],
}

CATEGORY_PRICE_RANGE = {
    "Electronics": (25, 220),
    "Home & Kitchen": (15, 180),
    "Apparel": (12, 90),
    "Beauty & Personal Care": (8, 70),
    "Sports & Outdoors": (10, 150),
    "Toys & Games": (8, 60),
    "Office Supplies": (10, 260),
}

MARKETING_CHANNELS = ["Organic Search", "Paid Search", "Email", "Social Media", "Referral", "Direct"]
CHANNEL_WEIGHTS = [0.24, 0.20, 0.14, 0.19, 0.09, 0.14]

PAYMENT_METHODS = ["Credit Card", "PayPal", "Debit Card", "Gift Card", "Buy Now Pay Later"]
PAYMENT_WEIGHTS = [0.44, 0.24, 0.16, 0.06, 0.10]

CUSTOMER_SEGMENTS = ["New", "Returning", "VIP"]

def seasonal_weight(d: datetime) -> float:
    """Return a multiplier that boosts Nov/Dec (holiday) and dips in summer."""
    month = d.month
    if month in (11, 12):
        return 2.4
    if month == 1:
        return 1.3  # New Year sales
    if month in (6, 7, 8):
        return 0.75
    return 1.0

def build_customers(n):
    first_names = ["James","Mary","Robert","Patricia","John","Jennifer","Michael","Linda","David","Elizabeth",
                   "William","Barbara","Richard","Susan","Joseph","Jessica","Thomas","Sarah","Charles","Karen",
                   "Priya","Wei","Fatima","Carlos","Yuki","Ahmed","Sofia","Liam","Noah","Emma","Olivia","Mateus"]
    last_names = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez",
                  "Chen","Kumar","Nguyen","Silva","Khan","Kim","Ali","Muller","Rossi","Dubois"]

    customers = []
    for i in range(1, n + 1):
        signup_date = START_DATE + timedelta(days=int(RNG.integers(0, (END_DATE - START_DATE).days - 30)))
        customers.append({
            "customer_id": f"CUST{i:05d}",
            "first_name": RNG.choice(first_names),
            "last_name": RNG.choice(last_names),
            "region": RNG.choice(REGIONS, p=REGION_WEIGHTS),
            "signup_date": signup_date,
            "segment": RNG.choice(CUSTOMER_SEGMENTS, p=[0.45, 0.42, 0.13]),
        })
    return pd.DataFrame(customers)

def random_date_between(start, end):
    delta = (end - start).days
    day_offset = int(RNG.integers(0, max(delta, 1)))
    return start + timedelta(days=day_offset)

def weighted_date(start, end, n_samples=1):
    """Sample dates with seasonal weighting via rejection-free CDF approach."""
    all_days = pd.date_range(start, end, freq="D")
    weights = np.array([seasonal_weight(d) for d in all_days], dtype=float)
    weights /= weights.sum()
    chosen = RNG.choice(all_days, size=n_samples, p=weights)
    return chosen

def generate_orders(customers_df):
    order_dates = weighted_date(START_DATE, END_DATE, N_ORDERS)
    rows = []
    cat_names = list(CATEGORIES.keys())

    for i in range(N_ORDERS):
        order_date = pd.Timestamp(order_dates[i])
        cust = customers_df.iloc[RNG.integers(0, len(customers_df))]

        # Customer can't order before they signed up
        if order_date < cust["signup_date"]:
            order_date = cust["signup_date"] + timedelta(days=int(RNG.integers(0, 30)))
            if order_date > END_DATE:
                order_date = pd.Timestamp(END_DATE)

        category = RNG.choice(cat_names)
        product = RNG.choice(CATEGORIES[category])
        low, high = CATEGORY_PRICE_RANGE[category]
        unit_price = round(RNG.uniform(low, high), 2)
        quantity = int(RNG.choice([1, 1, 1, 2, 2, 3, 4], p=[0.42, 0.001, 0.279, 0.15, 0.001, 0.049, 0.1]))
        # normalize probs above quickly below to avoid float errors
        discount_pct = RNG.choice([0, 0, 0, 5, 10, 15, 20, 25, 30], p=[0.35,0.001,0.049,0.15,0.15,0.12,0.09,0.06,0.03])
        channel = RNG.choice(MARKETING_CHANNELS, p=CHANNEL_WEIGHTS)
        payment = RNG.choice(PAYMENT_METHODS, p=PAYMENT_WEIGHTS)

        gross = round(unit_price * quantity, 2)
        discount_amt = round(gross * (discount_pct / 100), 2)
        shipping_cost = round(RNG.uniform(2.5, 12.0), 2) if RNG.random() > 0.18 else np.nan  # missing sometimes
        net_revenue = round(gross - discount_amt, 2)

        returned = RNG.random() < (0.045 if category != "Apparel" else 0.09)
        review_score = RNG.integers(1, 6) if RNG.random() > 0.35 else np.nan  # lots of orders have no review

        rows.append({
            "order_id": f"ORD{100000+i}",
            "customer_id": cust["customer_id"],
            "order_date": order_date,
            "category": category,
            "product_name": product,
            "unit_price": unit_price,
            "quantity": quantity,
            "discount_pct": discount_pct,
            "gross_amount": gross,
            "shipping_cost": shipping_cost,
            "net_revenue": net_revenue,
            "marketing_channel": channel,
            "payment_method": payment,
            "region": cust["region"],
            "customer_segment": cust["segment"],
            "returned": returned,
            "review_score": review_score,
        })

    return pd.DataFrame(rows)

def inject_messiness(df: pd.DataFrame) -> pd.DataFrame:
    """Deliberately dirty the data to mimic a real-world export."""
    df = df.copy()

    # 1. Duplicate ~1% of rows
    dupe_idx = RNG.choice(df.index, size=int(len(df) * 0.012), replace=False)
    df = pd.concat([df, df.loc[dupe_idx]], ignore_index=True)

    # 2. Inconsistent category casing / whitespace on a subset
    messy_idx = RNG.choice(df.index, size=int(len(df) * 0.03), replace=False)
    def mess_category(v):
        choice = RNG.integers(0, 3)
        if choice == 0:
            return v.upper()
        elif choice == 1:
            return f"  {v.lower()}  "
        return v
    df.loc[messy_idx, "category"] = df.loc[messy_idx, "category"].apply(mess_category)

    # 3. A few negative / zero unit prices (data entry errors)
    err_idx = RNG.choice(df.index, size=15, replace=False)
    df.loc[err_idx, "unit_price"] = -df.loc[err_idx, "unit_price"]

    # 4. Missing customer_segment for a small chunk
    seg_missing_idx = RNG.choice(df.index, size=int(len(df) * 0.02), replace=False)
    df.loc[seg_missing_idx, "customer_segment"] = np.nan

    # 5. Mixed date formatting: store some order_dates as strings in a different format
    df["order_date"] = df["order_date"].astype(str)
    alt_fmt_idx = RNG.choice(df.index, size=int(len(df) * 0.05), replace=False)
    df.loc[alt_fmt_idx, "order_date"] = pd.to_datetime(df.loc[alt_fmt_idx, "order_date"]).dt.strftime("%d/%m/%Y")

    # 6. A handful of completely blank region entries
    region_blank_idx = RNG.choice(df.index, size=10, replace=False)
    df.loc[region_blank_idx, "region"] = ""

    # 7. Shuffle row order like a real export wouldn't be sorted
    df = df.sample(frac=1, random_state=7).reset_index(drop=True)

    return df

def main():
    customers = build_customers(N_CUSTOMERS)
    orders = generate_orders(customers)
    messy = inject_messiness(orders)

    out_path = "data/raw/ecommerce_raw.csv"
    messy.to_csv(out_path, index=False)
    print(f"Wrote {len(messy):,} rows to {out_path}")
    print(messy.isna().sum())

if __name__ == "__main__":
    main()
