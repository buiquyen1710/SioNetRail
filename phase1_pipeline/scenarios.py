from __future__ import annotations

from typing import Dict, List


def scenario_type(config: Dict) -> str:
    return str(config.get("scenario", {}).get("type", "open_railway"))


def is_tunnel_scenario(config: Dict) -> bool:
    return scenario_type(config) == "straight_tunnel"


def active_base_station(config: Dict) -> Dict:
    if "base_station" in config:
        return config["base_station"]
    stations = config.get("base_stations", [])
    if not stations:
        raise KeyError("No base station configuration found.")
    active_index = int(config.get("simulation", {}).get("active_base_station_index", 0))
    active_index = max(0, min(active_index, len(stations) - 1))
    return stations[active_index]


def all_base_stations(config: Dict) -> List[Dict]:
    stations = []
    if "base_stations" in config:
        stations.extend(config["base_stations"])
    elif "base_station" in config:
        stations.append(config["base_station"])
    extra = config.get("portal_base_stations", [])
    for station in extra:
        if station not in stations:
            stations.append(station)
    return stations
