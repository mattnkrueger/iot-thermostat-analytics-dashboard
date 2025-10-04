import pandas as pd
import json

def process_stream(data_1, data_2) -> pd.DataFrame:
    """
    parsing and constructing of a pandas dataframe from redis stream
    
    (
        <id>-<tag>, 
        {<key1>: <val1>, <key2>: <val2>, ...}
    )

    Inputs:
        data_1:
        [
            ('1758588609', {'sensor_id': '1', 'temperature_c': '32.19'}),
            ('1758588610', {'sensor_id': '1', 'temperature_c': '19.42'}), 
            ('1758588611', {'sensor_id': '1', 'temperature_c': '21.40'})
        ]

        data_2:
        [
            ('1758588609', {'sensor_id': '2', 'temperature_c': '29.43'}), 
            ('1758588610', {'sensor_id': '2', 'temperature_c': '40.11'}), 
            ('1758588611', {'sensor_id': '2', 'temperature_c': 'NaN'})
        ]

    Output:
                date  Sensor 1  Sensor 2
        0  1758588609     32.19     29.43
        1  1758588610     19.42     40.11
        2  1758588611     21.40       NaN
    """
    combined = data_1 + data_2

    records = []
    for id, entry in combined:
        timestamp = id.split("-")[0]
        sensor_id = entry.get("sensor_id")
        raw_temperature_c = entry.get("temperature_c")

        # Convert to float if not missing
        temperature_c = float(raw_temperature_c) if raw_temperature_c not in (None, "", "NaN", "null") else None

        records.append([sensor_id, timestamp, temperature_c])

    df = pd.DataFrame(records, columns=["sensor_id", "timestamp", "temperature_c"])
    df["sensor_id"] = df["sensor_id"].astype(int)
    df["timestamp"] = df["timestamp"].astype(int)

    pivoted = (
        df.pivot(index="timestamp", columns="sensor_id", values="temperature_c")
          .reset_index()
    )

    pivoted.columns.name = None
    pivoted = pivoted.reindex(columns=["timestamp", 1, 2])
    pivoted = pivoted.rename(
        columns={
            "timestamp": "date",
            1: "Sensor 1",
            2: "Sensor 2",
        }
    )

    return pivoted.reset_index(drop=True)

