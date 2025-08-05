import pandas as pd
from datetime import timedelta

timestamps = []
data = pd.read_csv("train_numeric.csv")

if 'Response' not in data.columns:
    print("Error: 'Response' column not found.")
    exit()

if 'synthetic_timestamp' not in data.columns:
    start = pd.to_datetime("2021-01-01 00:00:00")
    
    for i in range(len(data)):
        new_time = start + timedelta(seconds=i)
        timestamps.append(new_time)

    data['synthetic_timestamp'] = timestamps
    
else:
    print("Timestamp column already exists.")

print(data[['Response', 'synthetic_timestamp']].head())

# Save new file
data.to_csv("train_numeric_timestamp.csv", index=False)
print("Saved with timestamps.")
