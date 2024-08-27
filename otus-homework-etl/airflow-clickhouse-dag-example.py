import os

import airflow
from airflow import DAG
from airflow_clickhouse_plugin.sensors.clickhouse import ClickHouseSensor
from airflow_clickhouse_plugin.operators.clickhouse import ClickHouseOperator

DAG_ID = os.path.basename(__file__).split(".")[0]

with DAG(
    dag_id=DAG_ID,
    description="Testing DAG to check clickhouse integration",
    default_args={
        "owner": "r88_vladimir",
    },
    catchup=False,
    schedule_interval=None,
    start_date=airflow.utils.dates.days_ago(1),
    max_active_runs=1,
    tags=["testing"],
) as dag:

    click_sensor = ClickHouseSensor(
        task_id='poke_records_count',
        sql="SELECT count() FROM airflow_integration_example",
        clickhouse_conn_id='clickhouse_130',
        retries=1
    )

    click_inserter = ClickHouseOperator(
        task_id='create_record_via_airflow',
        sql='''
            INSERT INTO airflow_integration_example VALUES(1, 'airflow')
        ''',
        clickhouse_conn_id='clickhouse_130',
    )

    click_sensor >> click_inserter
