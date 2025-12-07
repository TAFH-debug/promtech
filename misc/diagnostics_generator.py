import random
import pandas as pd
from faker import Faker

fake = Faker()

methods = ["VIK", "PVK", "MPK", "UZK", "RGK", "TVK", "VIBRO", "MFL", "TFI", "GEO", "UTWM"]
quality_grades = ["удовлетворительно", "допустимо", "требует мер", "недопустимо"]
ml_labels = ["normal", "medium", "high"]

def compute_ml_label(param1, param2, param3, temperature, humidity):
    score = 0

    for p in [param1, param2, param3]:
        if p is None:
            continue
        if p > 15: score += 3
        elif p > 10: score += 2
        elif p > 5: score += 1

    if temperature > 30:
        score += 1
    if humidity > 80:
        score += 1

    if score >= 6:
        return "high"
    elif score >= 3:
        return "medium"
    else:
        return "normal"
    
def generate_record(diag_id, object_id):
    defect_found = random.choice([True, False])
    defect_description = fake.text(max_nb_chars=50) if defect_found else ""

    param1 = round(random.uniform(0.5, 20), 2) if defect_found else None
    param2 = round(random.uniform(0.5, 20), 2) if defect_found else None
    param3 = round(random.uniform(0.5, 20), 2) if defect_found else None

    temperature = round(random.uniform(-20, 40), 2)
    humidity = round(random.uniform(0, 100), 2)
    illumination = round(random.uniform(100, 20000), 2)

    record = {
        "diag_id": diag_id,
        "object_id": object_id,
        "method": random.choice(methods),
        "date": fake.date_between(start_date="-2y", end_date="today"),
        "temperature": temperature,
        "humidity": humidity,
        "illumination": illumination,
        "defect_found": defect_found,
        "defect_description": defect_description,
        "quality_grade": random.choice(quality_grades),
        "param1": param1, 
        "param2": param2,
        "param3": param3,
        "ml_label": random.choice([None, compute_ml_label(param1, param2, param3, temperature, humidity)]),
    }

    return record


def generate_dataset(n_records=1000, object_ids=[]):
    records = []
    for i in range(n_records):
        object_id = random.choice(object_ids)
        records.append(generate_record(i + 1, object_id))

    return pd.DataFrame(records)

object_idx = pd.read_csv("objects.csv")['object_id'].tolist()
# --- Генерация ---
df = generate_dataset(1000, object_idx)
df.to_csv("diagnostic_data.csv", index=False)

print("Generated 1000 rows → diagnostic_data.csv")
print(df.head())
