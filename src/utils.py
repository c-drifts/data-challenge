"""Utility functions for data normalization and configuration"""

# TODO: Move mappings to JSON config files for better maintainability
# This would allow updates without redeploying code
# Example: config/country_codes.json, config/event_types.json, etc.

# TODO: Move SOURCES_CONFIG to external JSON config file for better maintainability
SOURCES_CONFIG = {
    "apfel": {
        "endpoint": "http://localhost:5050/apfel/subscriptions",
        "fallback_file": "data/apfel_subscriptions.csv",
        "format": "json",
        "fallback_format": "csv"  # API: JSON, File: CSV
    },
    "fenster": {
        "endpoint": "http://localhost:5050/fenster/subscriptions",
        "fallback_file": "data/fenster_subscriptions.csv",
        "format": "csv"
    },
    "exchange_rates": {
        "endpoint": "http://localhost:5050/exchange-rates",
        "fallback_file": "data/exchange_rates.csv",
        "format": "csv"
    }
}

COUNTRY_CODE_MAPPING = {
    "GB": "GBR",
    "DE": "DEU",
    "FR": "FRA",
    "IT": "ITA",
    "ES": "ESP",
    "US": "USA",
    "USA": "USA",
    "UNITED STATES": "USA",
    "GBR": "GBR",
    "UNITED KINGDOM": "GBR",
}

EVENT_TYPE_MAPPING = {
    "SUBSCRIPTION_STARTED": "new",
    "SUBSCRIPTION_RENEWED": "renew",
    "SUBSCRIPTION_CANCELLED": "cancelled",
    "new": "new",
    "renew": "renew",
    "cancel": "cancelled",
    "cancelled": "cancelled",
}

SUBSCRIPTION_TYPE_MAPPING = {
    "standard_monthly": ("standard", "monthly"),
    "standard_yearly": ("standard", "yearly"),
    "premium_monthly": ("premium", "monthly"),
    "premium_yearly": ("premium", "yearly"),
}


def normalize_country_code(code):
    """Normalize country codes"""
    if not code:
        return None
    normalized = COUNTRY_CODE_MAPPING.get(code.upper(), code.upper())
    return normalized


def normalize_event_type(event_type):
    """Normalize event types across platforms"""
    if not event_type:
        return None
    normalized = EVENT_TYPE_MAPPING.get(event_type.upper(), event_type.lower())
    return normalized


def normalize_subscription_type(sub_type, renewal_period=None):
    """
    Normalize subscription type to (type, period) tuple
    Handles both Apfel (separate fields) and Fenster (combined) formats
    """
    if not sub_type:
        return None

    sub_type_lower = sub_type.lower()

    # If already in combined format (e.g., "premium_monthly")
    if "_" in sub_type_lower:
        return SUBSCRIPTION_TYPE_MAPPING.get(sub_type_lower, sub_type_lower)

    # If separate fields (Apfel format)
    if renewal_period:
        key = f"{sub_type_lower}_{renewal_period.lower()}"
        return SUBSCRIPTION_TYPE_MAPPING.get(key, (sub_type_lower, renewal_period.lower()))

    return None
