# Traffic Signal Metrics

This script fetches traffic signal metrics from the INRIX API and upserts them to Socrata. 

## Usage

```
python inrix_to_socrata.py [-s START_DATE] [-e END_DATE]
```

## Environment Variables
 
Create a `.env` file using the template supplied in `env_template`. Note that the vendor can only provision INRIX API keys 
and requires a subscription.
 
```
# INRIX
INRIX_APP_ID=
INRIX_HASH_TOKEN=
INRIX_AUTH_URL=
INRIX_SIGNALS_URL=

# Socrata
MOVEMENTS_DATASET=8qqy-h6xg
SIGNALS_DATASET=bfmq-ijru
SO_PASS=
SO_TOKEN=
SO_USER=
SO_WEB=datahub.austintexas.gov
```

### Arguments

| Flag              | Description                                         | Default        |
|-------------------|-----------------------------------------------------|----------------|
| `-s`, `--start`   | Start date for the data pull in `YYYY-MM-DD` format | 7 days ago     |
| `-e`, `--end`     | End date for the data pull in `YYYY-MM-DD` format   | Today          |

Both arguments are optional. If omitted, the script defaults to the last 7 days.

### Examples

Run with default date range (last 7 days):
```bash
python inrix_to_socrata.py
```

Specify a start date only (end defaults to today):
```bash
python inrix_to_socrata.py -s 2026-06-01
```

Specify an end date only (start defaults to 7 days before today):
```bash
python inrix_to_socrata.py -e 2026-06-15
```

Specify both dates explicitly:
```bash
python inrix_to_socrata.py -s 2026-06-01 -e 2026-06-30
```

---
 
## Docker
 
If you would like to run this script in a Docker container, follow the instructions below.
 
### Build
 
```bash
docker build -t dts-traffic-signal-metrics:local .
```
 
Then run the container, passing date arguments as needed:
 
```bash
# Default date range (last 7 days)
docker run --env-file .env inrix-to-socrata
 
# Specify a start date
docker run --env-file .env inrix-to-socrata -s 2026-06-01
 
# Specify both dates
docker run --env-file .env inrix-to-socrata -s 2026-06-01 -e 2026-06-30
```

## Data Notes

- Records where `anonymized` is `"true"` are skipped and not uploaded.
- Movement records for intersections or movements not present in the metadata are silently skipped (these are typically excluded movements).
- Uploaded records include a `row_id` field used as the Socrata upsert key, formatted as `{movement_id}_{unix_timestamp}` for movements and `{intersection_id}_{unix_timestamp}` for signals.
