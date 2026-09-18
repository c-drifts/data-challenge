"""
Unit tests for normalization functions
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import normalize_country_code, normalize_event_type, normalize_subscription_type


def test_normalize_country_code():
    """Test country code normalization"""
    assert normalize_country_code("GB") == "GBR"
    assert normalize_country_code("DE") == "DEU"
    assert normalize_country_code("USA") == "USA"
    assert normalize_country_code("United Kingdom") == "GBR"
    assert normalize_country_code("United States") == "USA"
    assert normalize_country_code(None) is None
    print("✓ test_normalize_country_code passed")


def test_normalize_event_type():
    """Test event type normalization"""
    assert normalize_event_type("SUBSCRIPTION_STARTED") == "new"
    assert normalize_event_type("SUBSCRIPTION_RENEWED") == "renew"
    assert normalize_event_type("SUBSCRIPTION_CANCELLED") == "cancelled"
    assert normalize_event_type("new") == "new"
    assert normalize_event_type("renew") == "renew"
    assert normalize_event_type(None) is None
    print("✓ test_normalize_event_type passed")


def test_normalize_subscription_type():
    """Test subscription type normalization"""
    # Combined format (Fenster style)
    assert normalize_subscription_type("standard_monthly") == ("standard", "monthly")
    assert normalize_subscription_type("premium_yearly") == ("premium", "yearly")

    # Separate fields (Apfel style)
    assert normalize_subscription_type("standard", "monthly") == ("standard", "monthly")
    assert normalize_subscription_type("premium", "yearly") == ("premium", "yearly")

    # None handling
    assert normalize_subscription_type(None) is None
    print("✓ test_normalize_subscription_type passed")


if __name__ == "__main__":
    test_normalize_country_code()
    test_normalize_event_type()
    test_normalize_subscription_type()
    print("\nAll unit tests passed!")
