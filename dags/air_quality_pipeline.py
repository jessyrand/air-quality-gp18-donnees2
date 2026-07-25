from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from src.extract.fetch_last import main as fetch_last
from src.transform.build_clean import main as build_clean
from src.transform.build_warehouse import main as build_warehouse


with DAG(
    dag_id="air_quality_pipeline",
    start_date=datetime(2026, 7, 24),
    schedule="@hourly",
    catchup=False,
    tags=["air-quality"],
) as dag:

    fetch = PythonOperator(
        task_id="fetch_last",
        python_callable=fetch_last,
    )

    clean = PythonOperator(
        task_id="build_clean",
        python_callable=build_clean,
    )

    warehouse = PythonOperator(
        task_id="build_warehouse",
        python_callable=build_warehouse,
    )

    fetch >> clean >> warehouse