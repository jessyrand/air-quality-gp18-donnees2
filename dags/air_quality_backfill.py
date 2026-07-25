from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from src.extract.fetch_history import main as fetch_history


with DAG(
    dag_id="air_quality_backfill",
    description="Backfill historical air quality data",
    start_date=datetime(2026, 7, 24),
    schedule=None,
    catchup=False,
    tags=["air-quality", "backfill"],
) as dag:

    fetch_history_task = PythonOperator(
        task_id="fetch_history",
        python_callable=fetch_history,
    )