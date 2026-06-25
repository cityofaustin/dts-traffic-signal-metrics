# Traffic Signal Metrics

This script fetches traffic signal metrics from the INRIX API and upserts them into a Socrata data portal dataset. 

## Usage

```
python inrix_to_socrata.py [-s START_DATE] [-e END_DATE]
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

## Data Notes

- Records where `anonymized` is `"true"` are skipped and not uploaded.
- Movement records for intersections or movements not present in the metadata are silently skipped (these are typically excluded movements).
- Uploaded records include a `row_id` field used as the Socrata upsert key, formatted as `{movement_id}_{unix_timestamp}` for movements and `{intersection_id}_{unix_timestamp}` for signals.
