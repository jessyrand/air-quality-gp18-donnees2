# Project Report — Donnees2

## 1. Team Working Method

The project was carried out by a team of four members, relying on a shared Git repository (`air-quality-gp18-donnees2`) with a `dev → main` branching strategy. Each feature was developed on a dedicated branch and then integrated via a pull request, allowing for review before merging into `main`.

The work was organized by pipeline layer: extraction, transformation, storage (warehouse), and orchestration/CI. This split allowed each member to work in parallel on relatively independent modules, while sharing a common data model defined at the start of the project (a star schema with `dim_city`, `dim_time`, and `fact_aqi`).

Regular check-ins were used to verify consistency between pipeline stages, particularly when moving from raw data to cleaned data, and then to the warehouse.

## 2. Task Breakdown

Mihaja: part of the extraction team, responsible for collecting raw data from the Open-Meteo API (`fetch_last`, `fetch_history`).

Mayah: part of the transformation team, responsible for cleaning and consolidating the dataset (`build_clean`, `merge_history`).

Koloina: part of the warehouse team, responsible for designing and implementing the warehouse layer: star schema, PostgreSQL loading (`build_warehouse.py`).

Jessy: part of the CI/CD and reliability team, responsible for setting up automation (GitHub Actions), fixing bugs (PostgreSQL surrogate keys, paths, backfill), and deployment.

This breakdown follows the ETL pipeline logic: the data extracted by Mihaja feeds into the cleaning done by Mayah, whose output is loaded into the warehouse built by Koloina, with the whole process automated and made reliable by Jessy.

## 3. Challenges Encountered and Solutions

### 3.1 Choice of Orchestrator: From Airflow to GitHub Actions

An initial approach to pipeline automation was explored using Apache Airflow (setting up a custom environment and a backfill DAG). This solution proved too heavy to deploy and maintain for the project's needs, mainly due to the complexity of configuring the associated Docker environment.

The team therefore chose to migrate to GitHub Actions, which is native to the repository and much simpler to operate: a scheduled workflow (hourly cron) automatically triggers the `fetch_last`, `build_clean`, and `build_warehouse` steps, with no additional infrastructure to manage. The outdated Airflow and Docker configurations were then removed from the repository to keep the codebase consistent.

### 3.2 Making Database Loading Reliable

Incremental data loading carried a risk of duplicates on every pipeline run. This was solved by implementing a PostgreSQL upsert mechanism (`ON CONFLICT DO NOTHING`) on the natural keys of each dimension, ensuring that data already present is never reinserted.

### 3.3 Reliability of the Scheduled Trigger

The team observed that GitHub Actions does not guarantee an exact-time execution for scheduled workflows: depending on service load, triggering can be delayed by several tens of minutes, since scheduled jobs are placed in a queue shared across all platform users. The cron is still configured for hourly triggering, but actual execution depends on GitHub runner availability. This was documented as a known limitation of the system rather than a bug to fix.

### 3.4 Paths and Environments

Several adjustments were needed to make the scripts behave identically both locally and in the GitHub Actions execution environment, in particular resolving data paths relative to the project root directory rather than the script's execution directory.

## 4. Justified Technical Choices

- **Language and package manager:** Python with `uv`, for fast and reproducible dependency management, with a lock file (`uv.lock`) ensuring an identical environment across team members and the automated pipeline.
- **Data source:** the Open-Meteo Air Quality API, chosen for being free, requiring no authentication key, and offering fine-grained hourly coverage for the five tracked cities (Antananarivo, Paris, Tokyo, Sydney, New York).
- **Modeling:** a star schema (`dim_city`, `dim_time`, `fact_aqi`) rather than a flat table, to clearly separate descriptive dimensions from measurements, facilitate aggregations, and limit data duplication.
- **Database:** PostgreSQL hosted on Neon, offering free managed hosting, automatic compute scaling, and simple integration with SQLAlchemy for the application layer.
- **Orchestration:** GitHub Actions rather than Airflow, for the reasons detailed in section 3.1 — simple integration with the existing repository and no infrastructure to maintain.
- **Loading:** an upsert mechanism via SQLAlchemy rather than simple inserts, to make the pipeline idempotent and safely replayable without risk of duplicates.