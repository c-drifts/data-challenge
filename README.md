# Data Engineering — Technical Assignment

The goal of this assignment is:
- **For you:** To see what type of issues you will be expected to work on at Helu.
- **For us:** To see how you think and approach tasks.

## Problem Statement

A SaaS company sells its app on two different platforms. The CFO needs a financial report that tracks metrics for both platforms (including acquisitions, renewals, and MRR), for each country per month. Currently, the CFO has to analyse the financial reports on each platform separately, which is too time-consuming!

The Data Engineering team is tasked with ingesting subscription events from each platform and outputting a consolidated report. The Analytics team will then build a visualisation for the CFO on top of it.

> **MRR Definition:** The total monthly revenue expected from active subscriptions at the end of each reporting period. Cancelled subscriptions should not contribute to MRR.

---

## Requirements

- Your pipeline should evaluate and fix any data quality issues you identify.
- The consolidated report must include at least the following attributes: `platform`, `subscription_type`, `country`, `acquisitions`, `renewals`, `cancellations`, `mrr_eur`.
- Subscription events and exchange rates should be ingested from the Docker-based API (see [Data Sources](#data-sources) below).
- The report should be stored in a **queryable format** (please document reasons for your storage decision).
- The pipeline should be **idempotent**.

---

## Data Sources

### Starting the Subscription API

Run the following command from the project root to build and start the data API:

```bash
docker compose up --build
```

Verify it's running:
```bash
curl http://localhost:5050/health
```

Once running, the following endpoints are available at `http://localhost:5050`:

| Endpoint | Format | Description |
|----------|--------|-------------|
| `/apfel/subscriptions` | JSON | Apfel platform subscription events |
| `/fenster/subscriptions` | CSV | Fenster platform subscription events |
| `/exchange-rates` | CSV | Exchange rates |
| `/health` | JSON | Health check |

> **Note:** There is no provided schema documentation for these endpoints. Data exploration is part of the exercise.

> If you have problems running or setting up Docker, you can use the CSV source files in the `data/` directory directly instead.

---

## Deliverables

1. **An executable Python (3.10+) solution** that meets all the above requirements.
2. **A schema for the report** should be defined — consider what would make the report meaningful and useful for the CFO.
3. **A README file** that explains:
   - How to run the solution (and any setup required)
   - How to query the report
   - Design decisions you made along the way

Please fork this repository and submit your solution as a link to your fork. You are free to use any libraries you prefer.

### Stretch Goals

These are optional — only if you have time and want to go further:

- Add validation or quality checks on the final report
- Write meaningful tests

---

## Guidelines

- Think of this assessment as a real project at Helu.
- Ensure your code is of **high quality** and follows best design practices. However, there is no need to implement a production-ready, infinitely scalable solution (running the solution locally is sufficient).
- **Quality over completeness.** We would rather see a well-thought-out partial solution than a complete one you can't fully explain. If you run out of time, document your thinking and next steps in the README.
- **Time expectation:** The solution should take around **3 hours**. If it takes longer for any reason, or you don't have enough time for all deliverables, that's no problem! Focus on doing good work on the parts you do complete.
- The problem is intentionally vaguely defined (e.g. what storage to use) — we're interested in how you approach problems and make decisions with limited information.
- **We evaluate understanding over output.** You should be able to explain every part of your code and design choices in a follow-up interview.

Good luck and have fun!

---

## How to Run

### Quick Start

From the project root:

```bash
# 1. One-time setup
python setup.py

# 2. Activate the virtual environment (required in every new terminal session)
source .venv/bin/activate

# 3. Start the data API
docker compose up -d

# 4. Run the pipeline
python src/main.py
```

### Setup (One-time)

```bash
python setup.py
```

This script will:
- Verify Python 3.10+
- Create a virtual environment in `.venv/`
- Install Python dependencies from `requirements.txt` into the virtual environment
- Create SQLite database (`data.db`)
- Initialize database schema
- Provide next steps

### Activate the Virtual Environment

Activate the virtual environment **before any Python command** in this project:

| Task | Command (after activation) |
|------|----------------------------|
| Run pipeline | `python src/main.py` |
| Unit tests | `python tests/test_utils.py` |
| Integration tests | `python tests/test_integration.py` |

**macOS / Linux:**

```bash
source .venv/bin/activate
```

**Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**

```cmd
.venv\Scripts\activate.bat
```

You should see `(.venv)` in your terminal prompt. To deactivate later, run `deactivate`.

> Run `source .venv/bin/activate` again whenever you open a new terminal tab or window.
### Execute the Pipeline

```bash
source .venv/bin/activate
docker compose up -d
python src/main.py
```

The pipeline ingests data from the running API on `http://localhost:5050`.

### Run Tests

```bash
source .venv/bin/activate
python tests/test_utils.py
python tests/test_integration.py
```

See [`tests/README.md`](tests/README.md) for details on what each test covers.

### Output

After execution:
- SQLite database created: `data.db`
- Tables populated:
  - `bronze_apfel`, `bronze_fenster`, `bronze_exchange_rates` (raw data)
  - `silver_apfel`, `silver_fenster` (cleaned data)
  - `gold_report` (final consolidated report)

---

## How to Query the Report

Query the consolidated report using SQLite:

```bash
sqlite3 data.db
```

#### Example Queries

**View all data:**
```sql
SELECT * FROM gold_report;
```

**Filter by country:**
```sql
SELECT platform, subscription_type, month, acquisitions, renewals, cancellations, mrr_eur
FROM gold_report
WHERE country = 'GBR'
ORDER BY month DESC;
```

**MRR by platform and month:**
```sql
SELECT platform, month, SUM(mrr_eur) as total_mrr
FROM gold_report
GROUP BY platform, month
ORDER BY month DESC;
```

**Export to CSV:**
```bash
sqlite3 -header -csv data.db "SELECT * FROM gold_report;" > report.csv
```

---

## Report Schema

### `gold_report` Table

| Column | Type | Description |
|--------|------|-------------|
| `platform` | TEXT | Source platform: "apfel" or "fenster" |
| `subscription_type` | TEXT | Subscription tier: "standard" or "premium" |
| `country` | TEXT | ISO 3166-1 alpha-3 country code (e.g., GBR, USA, DEU) |
| `month` | TEXT | Reporting month in format YYYY-MM |
| `acquisitions` | INTEGER | Count of new subscriptions started in the month |
| `renewals` | INTEGER | Count of subscriptions renewed in the month |
| `cancellations` | INTEGER | Count of subscriptions cancelled in the month |
| `mrr_eur` | REAL | Monthly Recurring Revenue in EUR (sum of active subscriptions at month-end) |

---

## Design Decisions

### 1. **Medallion Architecture (Bronze → Silver → Gold)**

The solution is structured in three layers for clarity, maintainability, and traceability:

- **Bronze Layer:** Raw data ingestion from API/files without transformation
  - Stores exact copies of source data in SQLite
  - Enables debugging and audit trails
  - Acts as immutable source of truth

- **Silver Layer:** Data cleaning, validation, and standardization
  - Normalizes country codes (GB → GBR, USA → USA)
  - Standardizes event types (SUBSCRIPTION_STARTED → "new", SUBSCRIPTION_RENEWED → "renew")
  - Converts USD → EUR using exchange rates
  - Handles data quality issues (see section below)
  - Creates unified schema for both platforms

- **Gold Layer:** Business-ready aggregations
  - Combines both platforms into single report
  - Groups by platform, subscription_type, country, and month
  - Calculates acquisitions, renewals, cancellations, and MRR
  - Final output ready for CFO analysis

**Benefits:** Each layer is independently queryable, allowing data exploration at any stage and easier debugging if issues arise.

### 2. **Storage: SQLite**

**Choice:** SQLite database (`data.db`)

**Rationale:**
- **Queryable:** Meets requirement for queryable format; supports SQL queries without external database
- **Zero setup:** File-based, no server required
- **Lightweight:** Perfect for this scale (local execution)
- **Idempotent:** Tables use `if_exists="replace"` pattern for safe re-runs
- **Portable:** Single file can be shared and queried with any SQLite tool

**Trade-offs:**
- Not suitable for massive datasets (but sufficient for this use case)
- Single-threaded write operations (acceptable for batch pipeline)

**Future enhancement:** Could migrate to PostgreSQL/DuckDB for distributed/concurrent access, but current solution is optimal for scope.

### 3. **Data Quality & Null Handling**

**Identified issues:**
- Apfel: 3 null country_code, 7 null amount
- Fenster: 1 null country_code

**Strategy:**
- Drop rows with null critical fields: `country_code`, `event_type`, `price_eur`
- Log warnings for each null condition detected
- Document in Silver layer how many records were dropped

**TODO:** Engage with business to:
- Understand root cause of nulls
- Determine if amounts can be recovered from other sources
- Define business rules for incomplete records

### 4. **Platform Normalization**

Both Apfel and Fenster have different schemas. Standardization occurs in Silver layer:

| Field | Apfel | Fenster | Normalized |
|-------|-------|---------|-----------|
| Country | `country_code` | `ctry` | `country_code` (ISO 3166-1 alpha-3) |
| Event Type | SUBSCRIPTION_STARTED/RENEWED/CANCELLED | new/renew/cancel | new/renew/cancelled |
| Subscription Type | separate `subscription_type` + `renewal_period` | combined `plan` | (type, period) tuple |
| Currency | EUR | USD | EUR (converted in Silver) |

### 5. **MRR Calculation**

**Definition:** Total monthly revenue from active subscriptions (excluding cancelled).

**Implementation:**
```
MRR = SUM(price_eur) WHERE event_type != "cancelled" GROUPED BY month
```

This ensures cancelled subscriptions don't contribute to monthly recurring revenue.

### 6. **Idempotency**

Pipeline is idempotent — can be re-run without creating duplicates:
- SQLite `to_sql(..., if_exists="replace")` overwrites tables
- No append-only logic; each run replaces entire dataset
- Safe to schedule as recurring job

### 7. **Configuration**

- Data sources (endpoints, fallback files) centralized in `src/utils.py` under `SOURCES_CONFIG`
- API endpoint URLs configurable (currently hardcoded; TODO: move to external config file)
- Mapping tables (country codes, event types) in `src/utils.py` (TODO: move to JSON for better maintainability)

### 8. **Error Handling & Logging**

- API failures gracefully fallback to local CSV files
- All operations wrapped in try-catch with rollback
- Detailed logging at each step (data loaded, rows dropped, etc.)
- TODO: Consider step functions for granular error recovery

---

## Project Structure

```
data-challenge/
├── .venv/                   # Virtual environment (created by setup.py)
├── src/
│   ├── main.py              # Entry point - orchestrates pipeline
│   ├── medallion.py         # Bronze, Silver, Gold layer implementations
│   ├── data_loader.py       # API/file data ingestion with fallback
│   └── utils.py             # Normalization functions & config
├── tests/
│   ├── test_utils.py        # Unit tests
│   └── test_integration.py  # Integration tests
├── data/
│   ├── apfel_subscriptions.csv
│   ├── fenster_subscriptions.csv
│   └── exchange_rates.csv
├── data.db                  # SQLite database (generated after running pipeline)
├── setup.py                 # One-time setup (venv + dependencies + DB)
├── requirements.txt         # Python dependencies
└── README.md

```

