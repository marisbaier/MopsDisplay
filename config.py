"""
Utility to parse KDL config file for events and stations.
"""
from dataclasses import dataclass
from kdl import parse

doc = None  # pylint: disable=invalid-name

events = []
stations = []

@dataclass
class Event:
    """
    Event dataclass.
    """
    date: str
    text: str

@dataclass
class Station:
    """
    Station dataclass.
    """
    name: str
    station_id: int
    s_bahn: bool
    tram: bool
    bus: bool
    min_time: int
    max_time: int
    min_time_needed: int
    max_departures: int

with open("config.kdl", "r", encoding="utf-8") as file:
    doc = parse(file.read())

    for event in doc.get("events").getAll("event"):  # type: ignore
        events.append(Event(event.get("date").args[0], event.get("text").args[0]))  # type: ignore

    for station in doc.get("stations").getAll("station"):  # type: ignore
        stations.append(Station(
            name=station.get("name").args[0],  # type: ignore
            station_id=int(station.get("station_id").args[0]),  # type: ignore
            s_bahn=bool(station.get("s_bahn").args[0]),  # type: ignore
            tram=bool(station.get("tram").args[0]),  # type: ignore
            bus=bool(station.get("bus").args[0]),  # type: ignore
            min_time=int(station.get("min_time").args[0]),  # type: ignore
            max_time=int(station.get("max_time").args[0]),  # type: ignore
            min_time_needed=int(station.get("min_time_needed").args[0]),  # type: ignore
            max_departures=int(station.get("max_departures").args[0])  # type: ignore
        ))
