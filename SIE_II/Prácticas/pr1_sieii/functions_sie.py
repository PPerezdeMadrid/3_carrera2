import functions_framework
from google.cloud import bigquery, storage
import pandas as pd
import numpy as np
# Triggered by a change in a storage bucket
@functions_framework.cloud_event
def cargar_datos_a_bq(cloud_event):
    data = cloud_event.data

    event_id = cloud_event["id"]
    event_type = cloud_event["type"]

    bucket = data["bucket"]
    name = data["name"]
    metageneration = data["metageneration"]
    timeCreated = data["timeCreated"]
    updated = data["updated"]

    print(f"Event ID: {event_id}")
    print(f"Event type: {event_type}")
    print(f"Bucket: {bucket}")
    print(f"File: {name}")
    #print(f"Metageneration: {metageneration}")
    #print(f"Created: {timeCreated}")
    #print(f"Updated: {updated}")

    bq_client = bigquery.Client()
    cliente_gcs = storage.Client()
    
    # 1. job_config
    job_config = bigquery.LoadJobConfig()

    ## 2. Autodetect = True. Especificando el esquema
    job_config.autodetect = True
    
    ## 3. Como es csv: decimos que obvie la primera fila y que el formato es CSV (por defecto, es CSV).

    job_config.skip_leading_rows=1
    job_config.source_format=bigquery.SourceFormat.CSV
    
    ## 4. Tipo de escritura
    job_config.write_disposition = 'WRITE_TRUNCATE'
    uri = 'gs://'+bucket+'/'+name
    table_ref = 'ceu_dataset1.'+name.replace('.csv','') ##Dataset.nombre_de_la_clase


    load_job = bq_client.load_table_from_uri(uri, table_ref, job_config=job_config)\


    print("Comenzando job {}".format(load_job.job_id))
    load_job.result()  # Espera a que la tabla esté subida
    print("Job terminado")
    print('Errores?')
    print(load_job.errors)


"""
gcloud functions deploy "nombre de tu función" \
>>     --runtime python39 \
>>     --trigger-bucket pr1_sie2 \
>>     --entry-point gcs_to_bigquery \
>>     --memory 128MB \
>>     --timeout 540s \
>>     --source ./ \
>>     --allow-unauthenticated

IMPORTANTE --> REQUIREMENTS.TXT

"""

"""
functions_framework
pandas
google.cloud.bigquery
google.cloud.storage

"""