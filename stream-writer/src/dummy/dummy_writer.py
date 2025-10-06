import time
import json
import random

from src.setup.task_queue import celery_client
from src.setup.redis_client import r

def dummy_stream_record(sensor_id:str, timestamp:int):
    status = r.get(f"virtual:{sensor_id}:status")

    temp_c = random.uniform(25,35) if status == "ON" else None

    entry = {
        "sensor_id":sensor_id,
        "temperature_c":json.dumps(temp_c)
    }

    r.xadd(f"readings:{sensor_id}", entry, id=timestamp, maxlen=300)

    celery_client.send_task(
        "insert_record", 
        kwargs={
            "sensor_id":sensor_id,
            "timestamp":timestamp,
            "temperature_c":temp_c
        }
    )

def dummy_writer(r, celery_client):
    r.set("virtual:1:status", "ON")
    r.set("virtual:2:status", "ON")

    while True:
        timestamp = int(time.time())

        dummy_stream_record(sensor_id="1", timestamp=timestamp)
        dummy_stream_record(sensor_id="2", timestamp=timestamp)
            
        time.sleep(1)
