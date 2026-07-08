"""
A collection of functions to generate payloads for querying traffic signal data from the INRIX API.

Functions:
    - get_metadata_payload: Generates payload for metadata based on intersections.
    - get_signal_movements_payload: Generates payload for signal movement data for intersections over a specified date.
    - get_signal_metrics_payload: Generates payload for signal metrics data for intersections over a specified date.
"""


def get_metadata_payload(intersections):
    return {
        "fields": [
            {"name": "intersectionId"},
            {"name": "name"},
            {"name": "coordinates"},
            {"name": "movements.id"},
            {"name": "movements.rank"},
            {"name": "movements.turnManeuvers"},
            {"name": "movements.inbound.direction"},
            {"name": "movements.outbound.direction"},
        ],
        "fieldFilters": [
            {
                "name": "intersectionId",
                "operator": "IN_LIST",
                "expressions": intersections,
            }
        ],
        "pageSize": 100,
    }


def get_signal_movements_payload(intersections, start_date):
    return {
        "dateRanges": [{"startDate": start_date, "endDate": start_date}],
        "dimensions": [
            {"name": "intersectionId"},
            {"name": "movementId"},
            {"name": "hourOfDay"},
        ],
        "dimensionFilters": [
            {
                "name": "intersectionId",
                "operator": "IN_LIST",
                "expressions": intersections,
            }
        ],
        "metrics": [
            {"name": "totalVehicleCount"},
            {"name": "throughVehicleCount"},
            {"name": "stopVehicleCount"},
            {"name": "avgTravelTime"},
            {"name": "maxTravelTime"},
            {"name": "avgApproachSpeed"},
            {"name": "maxApproachSpeed"},
            {"name": "avgThroughApproachSpeed"},
            {"name": "maxThroughApproachSpeed"},
            {"name": "avgControlDelay"},
            {"name": "maxControlDelay"},
            {"name": "3MDCount"},
            {"name": "3MDPct"},
            {"name": "POG"},
            {"name": "turnPct"},
            {"name": "LOS"},
            {"name": "anonymized"},
        ],
        "pageSize": 10000,
        "metadata": [{"key": "outputMode", "value": "verbose"}],
    }


def get_signal_metrics_payload(intersections, start_date):
    return {
        "dateRanges": [{"startDate": start_date, "endDate": start_date}],
        "dimensions": [
            {"name": "intersectionId"},
            {"name": "hourOfDay"},
        ],
        "dimensionFilters": [
            {
                "name": "intersectionId",
                "operator": "IN_LIST",
                "expressions": intersections,
            }
        ],
        "metrics": [
            {"name": "totalVehicleCount"},
            {"name": "throughVehicleCount"},
            {"name": "stopVehicleCount"},
            {"name": "avgTravelTime"},
            {"name": "maxTravelTime"},
            {"name": "avgApproachSpeed"},
            {"name": "maxApproachSpeed"},
            {"name": "avgThroughApproachSpeed"},
            {"name": "maxThroughApproachSpeed"},
            {"name": "avgControlDelay"},
            {"name": "maxControlDelay"},
            {"name": "3MDCount"},
            {"name": "3MDPct"},
            {"name": "POG"},
            {"name": "turnPct"},
            {"name": "LOS"},
            {"name": "anonymized"},
        ],
        "pageSize": 10000,
        "metadata": [{"key": "outputMode", "value": "verbose"}],
    }
