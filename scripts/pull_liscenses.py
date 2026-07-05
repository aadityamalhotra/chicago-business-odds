import os
from sodapy import Socrata
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

client = Socrata(
    "data.cityofchicago.org",
    os.getenv("SOCRATA_APP_TOKEN"),
    timeout=60
)

DATASET_ID = "r5kz-chrr"
BATCH_SIZE = 50000
CHECKPOINT_EVERY = 5  # save to disk every 5 batches (~250k rows)

FIELDS = [
    "account_number", "site_number", "legal_name", "doing_business_as_name",
    "license_number", "license_id",
    "license_code", "license_description",
    "application_type", "license_status", "license_status_change_date",
    "date_issued", "expiration_date",
    "ward", "community_area", "community_area_name", "location"
]

os.makedirs("data/raw", exist_ok=True)

all_rows = []
offset = 0
batch_num = 0

while True:
    batch = client.get(
        DATASET_ID,
        select=",".join(FIELDS),
        limit=BATCH_SIZE,
        offset=offset,
        order=":id"
    )
    if not batch:
        break
    all_rows.extend(batch)
    batch_num += 1
    print(f"Pulled {len(all_rows):,} rows so far...")
    offset += BATCH_SIZE

    if batch_num % CHECKPOINT_EVERY == 0:
        pd.DataFrame.from_records(all_rows).to_parquet(
            "data/raw/business_licenses.parquet", index=False
        )
        print(f"  Checkpoint saved at {len(all_rows):,} rows.")

# Final save, guaranteed to run even if the last checkpoint was mid-batch
df = pd.DataFrame.from_records(all_rows)
df.to_parquet("data/raw/business_licenses.parquet", index=False)
print(f"Done. {len(df):,} total rows saved.")
