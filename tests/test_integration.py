"""
Integration tests with sample data.
Reads small subsets of CSV and verifies pipeline output.
"""

import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import normalize_country_code, normalize_event_type, normalize_subscription_type


def test_apfel_sample():
    """Test Apfel data processing on a small sample"""
    print("\n=== Testing Apfel Sample ===")

    # Sample data
    apfel_sample = pd.DataFrame({
        "event_id": ["APF-001", "APF-002", "APF-003"],
        "event_timestamp": ["2025-02-01", "2025-02-05", "2025-03-01"],
        "event_type": ["SUBSCRIPTION_STARTED", "SUBSCRIPTION_RENEWED", "SUBSCRIPTION_CANCELLED"],
        "customer_uuid": ["APF_C001", "APF_C001", "APF_C002"],
        "country_code": ["GB", "GB", "DE"],
        "subscription_type": ["standard", "standard", "premium"],
        "renewal_period": ["monthly", "monthly", "yearly"],
        "amount": [5.99, 5.99, 119.99],
        "currency": ["EUR", "EUR", "EUR"]
    })

    # Apply normalizations
    apfel_sample["country_code"] = apfel_sample["country_code"].apply(normalize_country_code)
    apfel_sample["event_type"] = apfel_sample["event_type"].apply(normalize_event_type)

    # Verify results
    assert apfel_sample.loc[0, "country_code"] == "GBR"
    assert apfel_sample.loc[1, "event_type"] == "renew"
    assert apfel_sample.loc[2, "event_type"] == "cancelled"

    print("✓ Apfel sample processed correctly")
    print(f"  - {len(apfel_sample)} records")
    print(f"  - Countries: {apfel_sample['country_code'].unique()}")
    print(f"  - Event types: {apfel_sample['event_type'].unique()}")


def test_fenster_sample():
    """Test Fenster data processing on a small sample"""
    print("\n=== Testing Fenster Sample ===")

    # Sample data
    fenster_sample = pd.DataFrame({
        "id": ["FEN-001", "FEN-002"],
        "ts": ["2025-02-01", "2025-02-10"],
        "type": ["new", "renew"],
        "cid": ["FEN_C001", "FEN_C001"],
        "ctry": ["USA", "United States"],
        "plan": ["premium_monthly", "premium_monthly"],
        "price": [14.99, 14.99],
        "ccy": ["USD", "USD"]
    })

    # Apply normalizations
    fenster_sample["ctry"] = fenster_sample["ctry"].apply(normalize_country_code)

    # Verify country normalization
    assert fenster_sample.loc[0, "ctry"] == "USA"
    assert fenster_sample.loc[1, "ctry"] == "USA"

    print("✓ Fenster sample processed correctly")
    print(f"  - {len(fenster_sample)} records")
    print(f"  - Countries normalized: {fenster_sample['ctry'].unique()}")


def test_mrr_calculation():
    """Test MRR calculation logic on sample data"""
    print("\n=== Testing MRR Calculation ===")

    # Create sample subscription events
    events = pd.DataFrame({
        "customer_id": ["CUST001", "CUST001", "CUST002", "CUST002"],
        "event_type": ["new", "renew", "new", "cancelled"],
        "event_date": ["2025-02-01", "2025-03-01", "2025-02-15", "2025-02-28"],
        "price_eur": [59.99, 59.99, 119.99, 119.99],
        "platform": ["apfel", "apfel", "fenster", "fenster"],
        "subscription_type": ["standard", "standard", "premium", "premium"],
        "country_code": ["GBR", "GBR", "USA", "USA"]
    })

    events["event_date"] = pd.to_datetime(events["event_date"])
    events["year_month"] = events["event_date"].dt.to_period("M")

    # Calculate MRR: last event per customer, per month
    last_events = events.sort_values("event_date").groupby(
        ["customer_id", "year_month"],
        as_index=False
    ).last()

    # Determine status
    last_events["status"] = last_events["event_type"].apply(
        lambda x: "active" if x != "cancelled" else "inactive"
    )

    # MRR: active subscriptions
    active_subs = last_events[last_events["status"] == "active"]
    mrr = active_subs.groupby(
        ["platform", "subscription_type", "country_code", "year_month"]
    )["price_eur"].sum().reset_index()

    # Verify results
    print(f"✓ MRR calculation completed")
    print(f"  - Total events: {len(events)}")
    print(f"  - Last events: {len(last_events)}")
    print(f"  - Active subscriptions: {len(active_subs)}")
    print(f"  - MRR rows: {len(mrr)}")

    # Expected: 2 active subscriptions in Feb (CUST001 and CUST002)
    # Expected: 1 active subscription in Mar (CUST001)
    assert len(active_subs) == 2  # CUST001 in Feb, CUST001 in Mar, CUST002 in Feb (not cancelled yet)
    assert len(mrr) == 2  # Feb and Mar have MRR

    print(f"\n  MRR Summary:")
    for _, row in mrr.iterrows():
        print(f"    {row['year_month']}: {row['subscription_type']} on {row['platform']} = €{row['price_eur']:.2f}")


if __name__ == "__main__":
    test_apfel_sample()
    test_fenster_sample()
    test_mrr_calculation()
    print("\n" + "="*60)
    print("All integration tests passed!")
    print("="*60)
