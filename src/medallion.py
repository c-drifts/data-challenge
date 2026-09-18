"""
Medallion Architecture for Subscription Data Pipeline
Layers: Bronze (raw) → Silver (cleaned) → Gold (business-ready)

Storage: Currently using SQLite for persistence.
TODO: Implement query optimization with indexing for better performance at scale.
For now, SQLite is sufficient for this use case.
"""

import sqlite3
import logging
import pandas as pd
from data_loader import fetch_data
from utils import SOURCES_CONFIG

logger = logging.getLogger(__name__)

DB_PATH = "data.db"


def _get_db_connection(db_path=DB_PATH):
    """Get SQLite connection"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def bronze_layer():
    """
    Bronze Layer: Ingest raw data from sources
    - Load Apfel subscriptions (CSV from API or file)
    - Load Fenster subscriptions (CSV from API or file)
    - Load Exchange rates (CSV from API or file)

    Saves raw dataframes to SQLite without transformation.
    """
    conn = _get_db_connection()

    try:
        for source_name, config in SOURCES_CONFIG.items():
            logger.info(f"Loading {source_name}...")

            fallback_format = config.get("fallback_format", None)
            df = fetch_data(
                config["endpoint"],
                config["fallback_file"],
                config["format"],
                fallback_format
            )

            table_name = f"bronze_{source_name}"
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            logger.info(f"Saved {len(df)} rows to {table_name}")

        conn.commit()
        logger.info("Bronze layer completed successfully")

    except Exception as e:
        conn.rollback()
        logger.error(f"Bronze layer failed: {e}")
        raise
    finally:
        conn.close()


def silver_layer():
    """
    Silver Layer: Clean, validate, and standardize data
    - Normalize country codes
    - Standardize event types
    - Normalize subscription types
    - Validate data quality
    - Convert currencies to EUR
    - Handle deduplication

    Saves cleaned dataframes to SQLite.
    """
    from utils import normalize_country_code, normalize_event_type, normalize_subscription_type

    conn = _get_db_connection()

    try:
        logger.info("Reading bronze data...")
        bronze_apfel = pd.read_sql("SELECT * FROM bronze_apfel", conn)
        bronze_fenster = pd.read_sql("SELECT * FROM bronze_fenster", conn)
        bronze_rates = pd.read_sql("SELECT * FROM bronze_exchange_rates", conn)

        # Process Apfel
        logger.info("Processing Apfel data...")
        apfel_silver = _process_apfel(bronze_apfel, bronze_rates)
        apfel_silver.to_sql("silver_apfel", conn, if_exists="replace", index=False)
        logger.info(f"Saved {len(apfel_silver)} rows to silver_apfel")

        # Process Fenster
        logger.info("Processing Fenster data...")
        fenster_silver = _process_fenster(bronze_fenster, bronze_rates)
        fenster_silver.to_sql("silver_fenster", conn, if_exists="replace", index=False)
        logger.info(f"Saved {len(fenster_silver)} rows to silver_fenster")

        conn.commit()
        logger.info("Silver layer completed successfully")

    except Exception as e:
        conn.rollback()
        logger.error(f"Silver layer failed: {e}")
        raise
    finally:
        conn.close()


def _process_apfel(df, rates_df):
    """
    Process and normalize Apfel data.

    TODO: Investigate null values with business:
    - country_code nulls (3 records) - Are these data entry errors or incomplete data?
    - amount nulls (7 records) - Can we recover these amounts from another source?
    Consider developing a recovery strategy or defining business rules for these cases.
    """
    import pandas as pd
    from utils import normalize_country_code, normalize_event_type, normalize_subscription_type

    df = df.copy()
    initial_count = len(df)

    # Quality checks - data quality logging
    country_nulls = df["country_code"].isnull().sum()
    amount_nulls = df["amount"].isnull().sum()

    if country_nulls > 0:
        logger.warning(f"Apfel: {country_nulls} records with null country_code")
    if amount_nulls > 0:
        logger.warning(f"Apfel: {amount_nulls} records with null amount")


    # Remove records with null critical fields before normalization
    # (NaN values conflict with string normalization functions)
    df = df.dropna(subset=["country_code", "amount"])


    # Normalize fields
    df["country_code"] = df["country_code"].apply(normalize_country_code)
    df["event_type"] = df["event_type"].apply(normalize_event_type)
    df[["subscription_type", "renewal_period"]] = df.apply(
        lambda row: pd.Series(normalize_subscription_type(row["subscription_type"], row["renewal_period"])),
        axis=1
    )

    # Add platform
    df["platform"] = "apfel"

    # Standardize columns
    df["event_date"] = pd.to_datetime(df["event_timestamp"]).dt.date
    df["price_eur"] = df["amount"]  # Already in EUR
    #df["currency"] = "EUR"

    # Select relevant columns
    silver_cols = [
        "platform",
        "event_type",
        "subscription_type",
        "renewal_period",
        "country_code",
        "event_date",
        "price_eur",
        "currency",
        "event_id",
        "event_timestamp",
        "customer_uuid"
    ]

    df_clean = df[silver_cols].dropna(subset=["country_code", "event_type", "price_eur"])
    # Rename customer_uuid for consistency
    df_clean = df_clean.rename(columns={"customer_uuid": "customer_id"})
    dropped_count = initial_count - len(df_clean)

    if dropped_count > 0:
        logger.info(f"Apfel: Dropped {dropped_count} records due to missing critical fields")

    return df_clean


def _process_fenster(df, rates_df):
    """
    Process and normalize Fenster data.

    TODO: Investigate null values with business:
    - ctry nulls (1 record) - Can we determine the country from other fields?
    Consider developing a recovery strategy or defining business rules for these cases.
    """
    import pandas as pd
    from utils import normalize_country_code, normalize_event_type, normalize_subscription_type

    df = df.copy()
    initial_count = len(df)

    # Quality checks - data quality logging
    country_nulls = df["ctry"].isnull().sum()

    if country_nulls > 0:
        logger.warning(f"Fenster: {country_nulls} records with null ctry (country)")
        # Remove records with null critical fields before normalization
        # (NaN values conflict with string normalization functions)
        df = df.dropna(subset=["ctry"])

    # Normalize fields
    df["ctry"] = df["ctry"].apply(normalize_country_code)
    df["type"] = df["type"].apply(normalize_event_type)
    df[["subscription_type", "renewal_period"]] = df["plan"].str.lower().apply(
        lambda x: pd.Series(normalize_subscription_type(x))
    )

    # Add platform
    df["platform"] = "fenster"

    # Standardize columns
    df["event_date"] = pd.to_datetime(df["ts"]).dt.date

    # Convert USD to EUR via merge with exchange rates
    df["month"] = pd.to_datetime(df["ts"]).dt.strftime("%Y-%m")
    rates_copy = rates_df.copy()
    rates_copy["month"] = pd.to_datetime(rates_copy["date"]).dt.strftime("%Y-%m")

    df = df.merge(rates_copy[["month", "rate_to_eur"]], on="month", how="left")
    df["exchange_rate"] = df["rate_to_eur"].fillna(0.92)  # Default fallback
    df["price_eur"] = df["price"] * df["exchange_rate"]

    # TODO: For very large datasets, could optimize with dict lookup (O(1)) instead of merge (O(n))
    # Trade-off: dict is faster but less readable; merge is clearer and sufficient for current scale

    # Select relevant columns
    silver_cols = [
        "platform",
        "type",
        "subscription_type",
        "renewal_period",
        "ctry",
        "event_date",
        "price_eur",
        "ccy",
        "id",
        "ts",
        "cid"
    ]

    # Rename to match Apfel
    rename_map = {
        "type": "event_type",
        "ctry": "country_code",
        "ccy": "currency",
        "id": "event_id",
        "ts": "event_timestamp",
        "cid": "customer_id"
    }

    df_clean = df[silver_cols].rename(columns=rename_map).dropna(subset=["country_code", "event_type", "price_eur"])
    dropped_count = initial_count - len(df_clean)

    if dropped_count > 0:
        logger.info(f"Fenster: Dropped {dropped_count} records due to missing critical fields")

    return df_clean


def gold_layer():
    """
    Gold Layer: Generate consolidated business report
    - Merge Apfel and Fenster data
    - Group by: platform, subscription_type, country, month
    - Calculate: acquisitions, renewals, cancellations, mrr_eur (with state tracking)

    Saves final queryable report to SQLite.
    """
    conn = _get_db_connection()

    try:
        logger.info("Reading silver data...")
        silver_apfel = pd.read_sql("SELECT * FROM silver_apfel", conn)
        silver_fenster = pd.read_sql("SELECT * FROM silver_fenster", conn)

        # Combine both platforms
        logger.info("Combining Apfel and Fenster data...")
        combined = pd.concat([silver_apfel, silver_fenster], ignore_index=True)

        # Extract month from event_date
        combined["event_date"] = pd.to_datetime(combined["event_date"])
        combined["year_month"] = combined["event_date"].dt.to_period("M")

        # Step 1: Calculate event counts (acquisitions, renewals, cancellations)
        logger.info("Aggregating event counts by platform, subscription_type, country, month...")
        acquisitions = combined[combined["event_type"] == "new"].groupby(
            ["platform", "subscription_type", "country_code", "year_month"],
            as_index=False
        ).size()
        acquisitions.columns = ["platform", "subscription_type", "country", "month", "acquisitions"]

        renewals = combined[combined["event_type"] == "renew"].groupby(
            ["platform", "subscription_type", "country_code", "year_month"],
            as_index=False
        ).size()
        renewals.columns = ["platform", "subscription_type", "country", "month", "renewals"]

        cancellations = combined[combined["event_type"] == "cancelled"].groupby(
            ["platform", "subscription_type", "country_code", "year_month"],
            as_index=False
        ).size()
        cancellations.columns = ["platform", "subscription_type", "country", "month", "cancellations"]

        # Merge all event counts
        report = acquisitions.merge(renewals, on=["platform", "subscription_type", "country", "month"], how="outer").fillna(0)
        report = report.merge(cancellations, on=["platform", "subscription_type", "country", "month"], how="outer").fillna(0)

        # Step 2: Get last event per customer, per month
        logger.info("Calculating MRR with subscription state tracking...")
        combined_sorted = combined.sort_values("event_date")
        last_events = combined_sorted.groupby(
            ["customer_id", "year_month"],
            as_index=False
        ).last()

        # Step 3: Determine subscription status
        last_events["status"] = last_events["event_type"].apply(
            lambda x: "active" if x != "cancelled" else "inactive"
        )

        # Step 4: Calculate MRR (sum of active subscriptions)
        active_subs = last_events[last_events["status"] == "active"]
        mrr_df = active_subs.groupby(
            ["platform", "subscription_type", "country_code", "year_month"],
            as_index=False
        )["price_eur"].sum()
        mrr_df.columns = ["platform", "subscription_type", "country", "month", "mrr_eur"]

        # Merge MRR with event counts
        report = report.merge(mrr_df, on=["platform", "subscription_type", "country", "month"], how="outer").fillna(0)

        # Select final columns for report
        final_cols = [
            "platform",
            "subscription_type",
            "country",
            "month",
            "acquisitions",
            "renewals",
            "cancellations",
            "mrr_eur"
        ]

        report = report[final_cols].copy()
        report["month"] = report["month"].astype(str)  # Convert Period to string for SQLite
        report["acquisitions"] = report["acquisitions"].astype(int)
        report["renewals"] = report["renewals"].astype(int)
        report["cancellations"] = report["cancellations"].astype(int)

        # Save to SQLite (idempotent - replace all)
        report.to_sql("gold_report", conn, if_exists="replace", index=False)
        logger.info(f"Saved {len(report)} rows to gold_report")

        conn.commit()
        logger.info("Gold layer completed successfully")

    except Exception as e:
        conn.rollback()
        logger.error(f"Gold layer failed: {e}")
        raise
    finally:
        conn.close()
