# Architecture

## Overview

The project implements an automated ETL pipeline for collecting hourly air quality data, transforming it into a clean dataset, and loading it into a PostgreSQL data warehouse.

---

# Technology Stack

| Component | Technology | Justification |
|-----------|------------|---------------|
| Programming Language | Python 3.13 | Provides a rich ecosystem for data processing and ETL development. |
| Data Source | Open-Meteo Air Quality API | Free, reliable, and provides hourly air quality observations for multiple locations. |
| Orchestrator | GitHub Actions | Automates ETL execution without requiring dedicated infrastructure or self-hosted schedulers. |
| Data Storage | CSV files | Stores raw, cleaned, and warehouse exports for traceability and reproducibility. |
| Database | Neon PostgreSQL | Managed PostgreSQL service suitable for hosting the dimensional data warehouse. |
| Data Warehouse | Star Schema | Separates dimensions and facts to support analytical queries efficiently. |
| Dependency Management | uv | Fast and reproducible Python dependency management. |

---

# Architecture

```text
               GitHub Actions
                      │
                      ▼
              Extract (Open-Meteo)
                      │
                      ▼
             Raw CSV Storage
                      │
                      ▼
              Data Cleaning
                      │
                      ▼
             Clean CSV Dataset
                      │
                      ▼
          Star Schema Warehouse
                      │
                      ▼
             Neon PostgreSQL
```

---

# Execution Modes

## Historical Backfill

The backfill workflow rebuilds the entire warehouse from historical observations starting on **2026-01-01**.

```
fetch_history
        ↓
build_clean
        ↓
backfill
        ↓
Neon PostgreSQL
```

## Hourly Pipeline

The scheduled workflow retrieves the latest hourly observations and updates the warehouse incrementally.

```
fetch_last
        ↓
build_clean
        ↓
build_warehouse
        ↓
Neon PostgreSQL
```

---

# Design Decisions

- GitHub Actions was selected to automate the ETL pipeline without maintaining an orchestration server.
- CSV files are kept as intermediate storage to improve traceability and simplify debugging.
- PostgreSQL was chosen to implement the dimensional warehouse using a relational model.
- Incremental loading with PostgreSQL upserts preserves historical data while preventing duplicate records.