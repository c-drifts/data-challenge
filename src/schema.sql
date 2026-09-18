-- Medallion Architecture Schema
-- DDL for all tables used in the data pipeline

-- ==================== BRONZE LAYER ====================

-- Raw Apfel subscription events (JSON from API or CSV)
CREATE TABLE IF NOT EXISTS bronze_apfel (
    event_id TEXT NOT NULL,
    event_timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    customer_uuid TEXT,
    customer_email TEXT,
    customer_created_at TEXT,
    country_code TEXT,
    region TEXT,
    city TEXT,
    postal_code TEXT,
    subscription_type TEXT NOT NULL,
    renewal_period TEXT,
    currency TEXT NOT NULL,
    amount REAL,
    tax_amount REAL,
    discount_code TEXT,
    affiliate_id TEXT,
    device_type TEXT,
    app_version TEXT,
    session_id TEXT,
    internal_ref TEXT,
    processing_status TEXT
);

-- Raw Fenster subscription events (CSV from API or file)
CREATE TABLE IF NOT EXISTS bronze_fenster (
    id TEXT NOT NULL,
    ts TEXT NOT NULL,
    type TEXT NOT NULL,
    cid TEXT,
    mail TEXT,
    signup_ts TEXT,
    ctry TEXT,
    state TEXT,
    zip TEXT,
    plan TEXT NOT NULL,
    ccy TEXT NOT NULL,
    price REAL NOT NULL,
    tax REAL,
    vat_id TEXT,
    campaign_src TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    browser TEXT,
    os TEXT,
    screen_res TEXT,
    lang TEXT,
    tz TEXT,
    legacy_flag TEXT,
    migrated_from TEXT,
    batch_id TEXT,
    row_hash TEXT
);

-- Exchange rates for currency conversion
CREATE TABLE IF NOT EXISTS bronze_exchange_rates (
    date TEXT NOT NULL,
    currency TEXT NOT NULL,
    rate_to_eur REAL NOT NULL
);

-- ==================== SILVER LAYER ====================

-- Cleaned and normalized Apfel data
CREATE TABLE IF NOT EXISTS silver_apfel (
    platform TEXT NOT NULL,
    event_type TEXT NOT NULL,
    subscription_type TEXT,
    renewal_period TEXT,
    country_code TEXT NOT NULL,
    event_date TEXT NOT NULL,
    price_eur REAL NOT NULL,
    currency TEXT NOT NULL,
    event_id TEXT NOT NULL,
    event_timestamp TEXT NOT NULL
);

-- Cleaned and normalized Fenster data
CREATE TABLE IF NOT EXISTS silver_fenster (
    platform TEXT NOT NULL,
    event_type TEXT NOT NULL,
    subscription_type TEXT,
    renewal_period TEXT,
    country_code TEXT NOT NULL,
    event_date TEXT NOT NULL,
    price_eur REAL NOT NULL,
    currency TEXT NOT NULL,
    event_id TEXT NOT NULL,
    event_timestamp TEXT NOT NULL
);

-- ==================== GOLD LAYER ====================

-- Final consolidated business report
CREATE TABLE IF NOT EXISTS gold_report (
    platform TEXT NOT NULL,
    subscription_type TEXT,
    country TEXT NOT NULL,
    month TEXT NOT NULL,
    acquisitions INTEGER DEFAULT 0,
    renewals INTEGER DEFAULT 0,
    cancellations INTEGER DEFAULT 0,
    mrr_eur REAL NOT NULL
);

-- ==================== INDEXES (Optional - Future Optimization) ====================

-- TODO: Add indexes for common query patterns when performance becomes critical
-- CREATE INDEX idx_gold_report_country ON gold_report(country);
-- CREATE INDEX idx_gold_report_month ON gold_report(month);
-- CREATE INDEX idx_gold_report_platform ON gold_report(platform);
-- CREATE INDEX idx_silver_apfel_country ON silver_apfel(country_code);
-- CREATE INDEX idx_silver_fenster_country ON silver_fenster(country_code);
