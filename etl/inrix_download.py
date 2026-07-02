import argparse
from datetime import datetime, timedelta, time
import logging
import os
import requests
from sodapy import Socrata

from inrix_payloads import (
    get_metadata_payload,
    get_signal_metrics_payload,
    get_signal_movements_payload,
)
from utils import get_logger

# INRIX Secrets
APP_ID = os.getenv("INRIX_APP_ID")
HASH_TOKEN = os.getenv("INRIX_HASH_TOKEN")
AUTH_URL = os.getenv("INRIX_AUTH_URL")
SIGNALS_URL = os.getenv("INRIX_SIGNALS_URL")

# Socrata Secrets
SO_WEB = os.getenv("SO_WEB")
SO_TOKEN = os.getenv("SO_TOKEN")
SO_USER = os.getenv("SO_USER")
SO_PASS = os.getenv("SO_PASS")
SIGNALS_DATASET = os.getenv("SIGNALS_DATASET")
MOVEMENTS_DATASET = os.getenv("MOVEMENTS_DATASET")

soda_client = Socrata(
    SO_WEB,
    SO_TOKEN,
    username=SO_USER,
    password=SO_PASS,
    timeout=60,
)

# Directions formatting for movements
DIRECTIONS = {
    "E": "eastbound",
    "N": "northbound",
    "S": "southbound",
    "W": "westbound",
}


def authenticate_inrix_api():
    """
    Gets temporary auth token for INRIX API
    returns: token (str)
    """
    response = requests.get(
        f"{AUTH_URL}/appToken?appId={APP_ID}&hashToken={HASH_TOKEN}"
    )
    response.raise_for_status()
    data = response.json()
    token = data.get("result").get("token")
    return token


def get_intersections_list(headers, start_date, end_date):
    """
    Gets list of intersection IDs available for the given date range
    :param headers: HTTP headers for the API request
    :param start_date: Start date string in YYYY-MM-DD format
    :param end_date: End date string in YYYY-MM-DD format
    :return: list of intersection IDs
    """
    response = requests.get(
        f"{SIGNALS_URL}/metrics/intersections/availability?startDate={start_date}&endDate={end_date}&intersectionOutputMode=all",
        headers=headers,
    )
    response.raise_for_status()
    data = response.json()
    intersections = data.get("data")[0]["intersectionIds"]
    return intersections


def get_signal_metadata(headers, intersections):
    """
    Gets metadata for each intersection
    :param headers: HTTP headers for the API request
    :param intersections: list of intersection IDs
    :return: metadata_output: dict of intersection IDs and their metadata
    """
    # Request data
    payload = get_metadata_payload(intersections)
    response = requests.post(
        f"{SIGNALS_URL}/metadata/intersections", headers=headers, json=payload
    )
    response.raise_for_status()
    data = response.json()
    signals = data["data"]

    # Handling pagination
    if len(signals) < data["totalCount"]:
        offset = 0
        while data["data"]:
            offset += 100
            payload["offset"] = offset
            response = requests.post(
                f"{SIGNALS_URL}/metadata/intersections", headers=headers, json=payload
            )
            response.raise_for_status()
            data = response.json()
            signals += data["data"]

    # Creating output dict
    metadata_output = {}
    for metadata in signals:
        movements = {}
        for movement in metadata["movements"]:
            movement_metadata = {
                "approach": DIRECTIONS[movement["inbound"]["direction"]],
                "turn_type": movement["turnManeuvers"],
                "movement": DIRECTIONS[movement["inbound"]["direction"]]
                + " "
                + movement["turnManeuvers"],
            }
            movements[movement["id"]] = movement_metadata

        row = {
            "intersection_id": metadata["intersectionId"],
            "intersection_name": metadata["name"],
            "intersection_location": f"POINT ({metadata['coordinates'][0]['lon']} {metadata['coordinates'][0]['lat']})",
            "movements": movements,
        }
        metadata_output[metadata["intersectionId"]] = row
    return metadata_output


def get_metrics(dates, intersections, metadata, headers, query):
    """
    Gets metrics json data for every intersection for the given dates
    :param dates: list of dates to get metrics for
    :param intersections: list of intersection IDs
    :param metadata: dict of intersection IDs and their associated metadata
    :param headers: HTTP headers for the API request
    :param query: "signals" or "movements"
    :return: None
    """
    for date in dates:
        start = date.strftime("%Y-%m-%d")
        if query == "signals":
            payload = get_signal_metrics_payload(
                intersections=intersections, start_date=start
            )
        elif query == "movements":
            payload = get_signal_movements_payload(
                intersections=intersections, start_date=start
            )
        response = requests.post(
            f"{SIGNALS_URL}/metrics/intersections", headers=headers, json=payload
        )
        response.raise_for_status()
        data = response.json().get("data")
        records = data.get("records")
        if "nextCursor" in data:
            while "nextCursor" in data:
                cursor = data.get("nextCursor")
                payload["nextCursor"] = cursor
                response = requests.post(
                    f"{SIGNALS_URL}/metrics/intersections",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json().get("data")
                records += data.get("records")
        format_metrics(records, start, date, metadata, query)


def format_metrics(records, start, date, metadata, query):
    """
    Reformats the metrics json data into a format that can be uploaded to Socrata
    :param records: Raw data from the API
    :param start: Date in string format
    :param date: Date in datetime format
    :param metadata: dict of intersection IDs and their associated metadata
    :param query: "signals" or "movements"
    :return: None
    """
    reformatted = []
    for row in records:
        if row["anonymized"] == "false":
            # API sends string 'false', we have to convert to bool for socrata API
            row["anonymized"] = False
            row["date"] = start
            row["datetime"] = datetime.combine(date, time()).replace(
                hour=int(row["hourOfDay"])
            )
            int_id = row["intersectionId"]

            # Get metadata for this intersection
            if int_id not in metadata:
                continue
            meta = metadata[int_id]

            if query == "movements":
                if row["movementId"] not in meta["movements"]:
                    # Sometimes we get data for movements that are "excluded", this ignores them.
                    continue
            row.update(meta)

            row["row_id"] = (
                row["intersectionId"] + "_" + str(int(row["datetime"].timestamp()))
            )

            if query == "movements":
                # Unique ID for this entry
                row["row_id"] = (
                    row["movementId"] + "_" + str(int(row["datetime"].timestamp()))
                )

                # Movement names/metadata
                row["movement"] = row["movements"][row["movementId"]]["movement"]
                row["approach"] = row["movements"][row["movementId"]]["approach"]
                row["turn_type"] = row["movements"][row["movementId"]]["turn_type"]
                row["movement_id"] = row["movementId"]
                row.pop("movementId")

            row.pop("intersectionId")
            row.pop("movements")
            row["datetime"] = row["datetime"].strftime("%Y-%m-%dT%H:%M:%S")
            reformatted.append(row)

    logger.info(f"Sending {query} data from: {start} to socrata")
    if query == "signals":
        res = records_to_socrata(reformatted, SIGNALS_DATASET)
    elif query == "movements":
        res = records_to_socrata(reformatted, MOVEMENTS_DATASET)
    logger.info("--------")


def records_to_socrata(records, dataset, batch_size=10000):
    """
    Upserts records to socrata in batches
    :param records: list of records to upsert
    :param dataset: dataset resource ID
    :param batch_size: number of records to upsert per batch (default 10,000)
    """
    total = len(records)

    for start in range(0, total, batch_size):
        batch = records[start:start + batch_size]
        soda_res = soda_client.upsert(dataset, batch)
        logger.info(f"Batch {start // batch_size + 1} ({start}-{start + len(batch) - 1} of {total - 1}):")
        logger.info(soda_res)


def main():
    # Fallback dates if no args are supplied
    today = datetime.today().date()
    seven_days_ago = today - timedelta(days=7)

    # Argument parsing
    parser = argparse.ArgumentParser(description="Fetch INRIX signal metrics and upload to Socrata.")
    parser.add_argument("-s", "--start", default=seven_days_ago.strftime("%Y-%m-%d"), help="Start date in YYYY-MM-DD format (default: 7 days ago)")
    parser.add_argument("-e", "--end", default=today.strftime("%Y-%m-%d"), help="End date in YYYY-MM-DD format (default: today)")
    args = parser.parse_args()

    # Validate date formats
    try:
        start = datetime.strptime(args.start, "%Y-%m-%d").date()
        end = datetime.strptime(args.end, "%Y-%m-%d").date()
    except ValueError as e:
        parser.error(f"Invalid date format: {e}")

    if end <= start:
        parser.error("end date must be after start date")

    logger.info(f"Start date: {args.start}, End date: {args.end}")
    token = authenticate_inrix_api()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    intersections = get_intersections_list(headers, args.start, args.end)
    metadata = get_signal_metadata(headers, intersections)

    dates = [start + timedelta(days=i) for i in range((end - start).days + 1)]

    # First, get metrics by signal
    get_metrics(dates, intersections, metadata, headers, query="signals")
    # Next, get metrics by movement
    get_metrics(dates, intersections, metadata, headers, query="movements")


if __name__ == "__main__":
    logger = get_logger(
        __name__,
        level=logging.INFO,
    )

    main()
