import pandas as pd
import random

center = (51.1801, 71.446)

amount = 1000
datal = []
for i in range(amount):
    data = {
        'object_id': i,
        'object_name': f'Object{i}',
        'object_type': 'pipeline section',
        'pipeline_id': 'MT-01',
        'lat': center[0] + (i * 0.0001) + (random.random()) / 10000,
        'lon': center[1] + (i * 0.0001) + (random.random()) / 10000,
        'year': 2000 + (i % 21),
        'material': 'Steel-200' if i % 2 == 0 else 'Concrete',
        'created_at': f'2023-01-01',
        'updated_at': f'2023-06-01'
    }
    datal.append(data)

for i in range(amount):
    data = {
        'object_id': i + amount,
        'object_name': f'Object{i}',
        'object_type': 'pipeline section',
        'pipeline_id': 'MT-02',
        'lat': center[0] + (i * 0.0001) + (random.random()) / 10000,
        'lon': center[1] - 0.01 - (i * 0.0001) + (random.random()) / 10000,
        'year': 2000 + (i % 21),
        'material': 'Steel-200' if i % 2 == 0 else 'Concrete',
        'created_at': f'2023-01-01',
        'updated_at': f'2023-06-01'
    }
    datal.append(data)

for i in range(100):
    data = {
        'object_id': i + amount * 2,
        'object_name': f'Object{i}',
        'object_type': 'crane',
        'pipeline_id': 'MT-02',
        'lat': center[0] + (i * 0.0001) + (random.random()) / 10000,
        'lon': center[1] - 0.01 - (i * 0.0001) + (random.random()) / 10000,
        'year': 2000 + (i % 21),
        'material': 'Steel-200' if i % 2 == 0 else 'Concrete',
        'created_at': f'2023-01-01',
        'updated_at': f'2023-06-01'
    }
    datal.append(data)

df=pd.DataFrame(datal)
df.to_csv('objects.csv', index=False)


