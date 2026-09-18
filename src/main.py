"""
Main entry point for the data pipeline.

Orchestrates the medallion architecture:
Bronze → Silver → Gold

Pipeline is idempotent: each run fully replaces tables (safe for re-runs).

TODO: Implement monthly partitioning for optimization:
- Could process only the current month instead of all data
- Would require adding year_month partition column to tables
- Would enable efficient incremental updates
- Trade-off: added complexity vs. performance gain
"""

from medallion import bronze_layer, silver_layer, gold_layer
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def step_bronze():
    """Step 1: Bronze Layer"""
    logger.info("=== STEP 1: BRONZE LAYER ===")
    try:
        bronze_layer()
        logger.info("Bronze Layer completed")
    except Exception as e:
        logger.error(f"Bronze Layer failed: {e}", exc_info=True)
        raise


def step_silver():
    """Step 2: Silver Layer"""
    logger.info("=== STEP 2: SILVER LAYER ===")
    try:
        silver_layer()
        logger.info("Silver Layer completed")
    except Exception as e:
        logger.error(f"Silver Layer failed: {e}", exc_info=True)
        raise


def step_gold():
    """Step 3: Gold Layer"""
    logger.info("=== STEP 3: GOLD LAYER ===")
    try:
        gold_layer()
        logger.info("Gold Layer completed")
    except Exception as e:
        logger.error(f"Gold Layer failed: {e}", exc_info=True)
        raise


def main():
    """Execute the full pipeline"""
    logger.info("="*60)
    logger.info("Pipeline Start")
    logger.info("="*60)

    try:
        step_bronze()
        step_silver()
        step_gold()

        logger.info("="*60)
        logger.info("Pipeline execution successful!")
        logger.info("="*60)

    except Exception as e:
        logger.error("="*60)
        logger.error(f"Pipeline failed: {e}")
        logger.error("="*60)
        raise


if __name__ == "__main__":
    main()
