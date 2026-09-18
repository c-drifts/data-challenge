# Tests

Tests to verify pipeline correctness. **Not included in production deployment.**

## Running Tests

### Unit Tests (Normalization functions)

```bash
python test_utils.py
```

Tests:
- `test_normalize_country_code()` — Verify country code mapping (GB → GBR, etc.)
- `test_normalize_event_type()` — Verify event type mapping (SUBSCRIPTION_STARTED → "new")
- `test_normalize_subscription_type()` — Verify subscription type parsing

### Integration Tests (Sample data)

```bash
python test_integration.py
```

Tests:
- `test_apfel_sample()` — Process Apfel sample data and verify normalization
- `test_fenster_sample()` — Process Fenster sample data and verify country mapping
- `test_mrr_calculation()` — Verify MRR calculation logic on sample events

#### Test Data

Small sample datasets:
- **Apfel:** 3 records (STARTED, RENEWED, CANCELLED)
- **Fenster:** 2 records (new, renew)
- **Events:** 4 records to test MRR state tracking

#### Expected Results

**MRR Test:**
```
February 2025:
  - CUST001 (apfel, standard, GBR): €59.99 (status: active)
  - CUST002 (fenster, premium, USA): €119.99 (status: active - not cancelled yet)

March 2025:
  - CUST001 (apfel, standard, GBR): €59.99 (status: active after renewal)
```

Total MRR: 2 rows (Feb and Mar with active subscriptions)

## Notes

- Tests use small, manually crafted datasets for easy verification
- They verify core business logic without full pipeline setup
- Integration tests simulate the MRR calculation with state tracking
