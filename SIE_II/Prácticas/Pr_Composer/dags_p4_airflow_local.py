import os.path
from airflow import models
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta, date
from airflow.contrib.operators import gcs_to_bq
from airflow.contrib.operators import bigquery_to_gcs
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator

from airflow.utils.dates import days_ago
from datetime import datetime, timedelta, date
import pandas as pd
from airflow.contrib.sensors.file_sensor import FileSensor

## Nuestro proyecto
gcs_project = 'plenary-anvil-141110'
dataset = 'clase'
## Bucket de GCS. La ruta /home/airflow/gcs/ está mapeada al bucket que se va a generar cuando creamos nuestro Composer
gcs_airflow = 'europe-west1-micluster-7fa5d0a8-bucket'

tabla_resultado = 'elscoring'


def flag_file (flagfile):
    file = open(flagfile, "w+")
    file.write("Ejecutado \n")
    file.close()

def get_path (filepath):
    existe = os.path.exists(filepath)
    if existe:
        return 'end'
    else:
        return 'start'


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(3),
    'schedule_interval': "5 * * * *",
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'catchup': True,
    'retry_delay': timedelta(minutes=2),
    'project_id': gcs_project
}


## Bucket de GCS. La ruta /home/airflow/gcs/ está mapeada al bucket que se va a generar cuando creamos nuestro Composer

# Define DAG: Set ID and assign default args and schedule interval
with models.DAG( 'prueba_airflow_local_p4_escritura_bq',
        default_args=default_args
) as mydag:
    start_time = datetime.now()
    year, week_num, day_of_week = start_time.isocalendar()

    semana_actual = 'W-{0}-{1}'.format(year, week_num)

    t_begin = DummyOperator(task_id="begin", dag=mydag)
    t_end = DummyOperator(task_id = 'end', dag=mydag)
    t_hub_start = DummyOperator(task_id="start", dag=mydag)

    t_condicion = BranchPythonOperator(task_id='continue_branch', dag=mydag, python_callable=get_path,
                                       op_kwargs={
                                           'filepath': "/home/airflow/gcs/data/flag_file_" + semana_actual + ".txt"})

    t1_fichero_existe = FileSensor(task_id="comprobar_scoring_ejecutado",
                                   poke_interval=30,
                                   filepath='/home/airflow/gcs/data/results/prediccion.csv', dag=mydag)

    ## Las rutas se podían haber cargado de un fichero de configuración. Al ser un ejercicio conceptual, lo dejo así.

    t_3_flag = PythonOperator(
            task_id='create_flag',
            python_callable=flag_file,
            op_kwargs={'flagfile': "/home/airflow/gcs/data/flag_file_"+semana_actual+".txt"
                    },
            dag=mydag
        )

    t_2_actualizar_a_bq_de_gcs= gcs_to_bq.GoogleCloudStorageToBigQueryOperator(
    task_id='escribir_a_bq',
    bucket=gcs_airflow,
    source_objects=['data/results/prediccion.csv'],
    destination_project_dataset_table="{}.{}.{}".format(gcs_project,dataset,tabla_resultado), # esto tiene q ser informacion_final_linekalk
    
    schema_fields=[
        {"name":"id" ,"type":"STRING"},
        {"name":"score" ,"type": "STRING"}
        ]
            ,
        skip_leading_rows = 1,
        source_format='CSV',
        field_delimiter = ',',
        autodetect = False,
        ignore_unknown_values=True,
    write_disposition='WRITE_TRUNCATE', 
    dag=mydag)


    ################################################################# ESTABLECEMOS DEPENDENCIAS ############################################################################################################################################################################


    t_begin  >> t1_fichero_existe>>t_condicion
    t_condicion>>t_hub_start
    t_condicion>>t_end
    t_hub_start>>t_2_actualizar_a_bq_de_gcs>>t_3_flag>>t_end

  ##########################################################################################################################################################################################################################################################################