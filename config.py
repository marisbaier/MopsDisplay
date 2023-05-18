"""
Utility to parse KDL config file for events and stations.
"""
from dataclasses import dataclass
from kdl import parse

doc = None  # pylint: disable=invalid-name

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

    events = [
        Event(**{
            child.name: child.args[0]
            for child in event.nodes
        })
        for event in doc.get("events").getAll("event")  # type: ignore
    ]

    stations = [
        Station(**{
            child.name: int(arg) if isinstance((arg := child.args[0]), float) else arg  # type: ignore
            for child in station.nodes
        })
        for station in doc.get("stations").getAll("station")  # type: ignore
    ]