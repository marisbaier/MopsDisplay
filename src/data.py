"""Define dataclasses that are imported from the config file and manage API 
requests to obtain departure informations"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator, List, Union
from dateutil import parser as dateparser
from PIL.ImageTk import PhotoImage
import requests
from . import debug


session = requests.Session()
FETCH_DEPARTURE_TIMER = debug.TimedCumulative(name="fetch departures")


@dataclass(frozen=True)
class Event:
    """Event data

    Attributes
    ----------
    date: str
        Date of the event
    desc: str
        Short desription of the event (may include newline characters)
    """

    date: str
    desc: str


@dataclass(frozen=True)
class Poster:
    """Poster data

    Attributes
    ----------
    images: list[tkinter.PhotoImage]
        List of tkinter.PhotoImages to cycle through
    """

    images: list[PhotoImage]

    def __post_init__(self):
        # ensure that images is a list
        if not isinstance(self.images, (list, tuple)):
            object.__setattr__(self, "images", [self.images])


@dataclass(frozen=True)
class DirectionsAndProducts:
    """Directions and products to fetch from BVG API, used in Station

    Attributes
    ----------
    directions: list[str]
        List of station ids. A direction of a departure is given as the station
        id of a station it stops at after departing.
    S: bool, optional
        Wether to fetch suburban lines (S-Bahn). Defaults to False
    U: bool, optional
        Wether to fetch subway lines (U-Bahn). Defaults to False
    T: bool, optional
        Wether to fetch tram lines. Defaults to False
    B: bool, optional
        Wether to fetch bus lines. Defaults to False
    F: bool, optional
        Wether to fetch ferry lines. Defaults to False
    E: bool, optional
        Wether to fetch express lines (IC/ICE). Defaults to False
    R: bool, optional
        Wether to fetch regional lines (RE/RB). Defaults to False
    """

    directions: list[str]
    S: bool = False
    U: bool = False
    T: bool = False
    B: bool = False
    F: bool = False
    E: bool = False
    R: bool = False

    def __post_init__(self):
        # ensure that directions is a list
        if not isinstance(self.directions, (list, tuple)):
            object.__setattr__(self, "directions", [self.directions])


@dataclass(frozen=True)
class Station:
    """Station data

    Attributes
    ----------
    row: int
        Which row in the canvas grid to position the station at
    col: int
        Which column in the canvas grid to position the station at
    title: str
        Station title to display
    id: str
        Station API id
    max_departures: int
        Number of departures to display (and fetch per direction)
    min_time: float
        Minimal time left (in minutes) for a departure to be fetched
    max_time: float
        Maximum time left (in minutes) for a departure to be fetched
    time_needed: float
        Approximate time needed to reach the station (in minutes)
    start_night: str
        Time at which departure fetching switches to the night options
        (in 24h format "HH:MM:SS")
    stop_night: str
        Time at which departure fetching switches back to day options
        (in 24h format "HH:MM:SS")
    day: DirectionsAndProducts, optional
        Day options for departure fetching. Defaults to None (no fetching)
    night: DirectionsAndProducts, optional
        Night options for departure fetching. Defaults to None (no fetching)
    """

    row: int
    col: int
    title: str
    id: str
    max_departures: int

    min_time: float
    max_time: float
    time_needed: float

    start_night: str
    stop_night: str

    day: DirectionsAndProducts = None
    night: DirectionsAndProducts = None

    @property
    def is_night(self) -> bool:
        """Return True if night options should be active"""
        start = dateparser.parse(self.start_night)
        stop = dateparser.parse(self.stop_night)
        now = datetime.now()
        return time_is_between(start, now, stop)

    def get_urls(self) -> Iterator[str]:
        """Get BVG API url for every direction"""
        dap = self.night if self.is_night else self.day
        if dap is None:
            return []

        for direction in dap.directions:
            yield (
                f"https://v6.bvg.transport.rest/stops/{self.id}/departures?"
                f"direction={direction}&"
                f"when=in+{self.min_time}+minutes&"
                f"duration={self.max_time-self.min_time}&"
                f"results={self.max_departures}&"
                f"suburban={dap.S}&"
                f"subway={dap.U}&"
                f"tram={dap.T}&"
                f"bus={dap.B}&"
                f"ferry={dap.F}&"
                f"express={dap.E}&"
                f"regional={dap.R}"
            )

    def fetch_departures(self) -> List[Departure]:
        """Fetch departures from BVG API"""

        departures = []
        for url in self.get_urls():
            for departure_data in self._fetch_raw_departure_data(url):
                try:
                    departure = self._create_departure(departure_data)
                except Exception as e:
                    print(departure_data)
                    raise e
                if departure is None:
                    continue
                departures.append(departure)
        # do not use heapq.merge(), because it uses __eq__ (reserved for
        # Departure id comparison). sort() supposedly competes in speed by
        # detection of order trends: https://stackoverflow.com/a/38340755
        departures = list(dict.fromkeys(departures))  # duplicate filter
        departures.sort()
        return departures

    @FETCH_DEPARTURE_TIMER
    def _fetch_raw_departure_data(self, url: str):
        response = session.get(url, timeout=30_000)
        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError:
            data = {"departures": []}
        return data.get("departures", [])

    def _create_departure(self, data: dict) -> Union[Departure, None]:
        """Departure factory, return None if data has an error"""
        # resolve unexpected api departure time outputs
        timestr = data["when"]
        if timestr is None:
            return None
        time = time_left(timestr)
        if time < self.min_time:
            return None

        reachable = time > self.time_needed
        line = data["line"]

        departure = Departure(
            id=data["tripId"],
            line=line["id"],
            direction=data["direction"],
            time_left=time,
            delay=data["delay"],
            product=line["product"],
            reachable=reachable,
        )
        return departure


@dataclass(frozen=True)
class Departure:
    """Departure data

    Attributes
    ----------
    id: str
        API trip id
    line: str
        Name of the line (for example "s46")
    direction: str
        Direction of the trip. Not to be confused with the station ids in
        DirectionsAndProducts.directions
    time_left: float
        Time left (in minutes) until departing
    delay: float
        Delay of the departure (in minutes)
    product: str
        Product of the trip, see optional arguments of DirectionsAndProducts
    reachable: bool
        Wether the departure is reachable by foot

    Notes
    -----
    Departures can sort (<, <=, >, >=) according to the time_left argument
    Departures are equal (==, hash) if their id arguments are equal
    """

    id: str
    line: str
    direction: str
    time_left: float
    delay: float
    product: str  # suburban, subway, tram, bus, ferry, express, regional
    reachable: bool

    # sorting
    def __lt__(self, other: Departure):
        return self.time_left < other.time_left

    def __le__(self, other: Departure):
        return self.time_left <= other.time_left

    def __gt__(self, other: Departure):
        return self.time_left > other.time_left

    def __ge__(self, other: Departure):
        return self.time_left >= other.time_left

    # id comparison
    def __eq__(self, other: Departure) -> bool:
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


def time_is_between(
    start: Union[datetime, str],
    time: Union[datetime, str],
    stop: Union[datetime, str],
):
    """Check if time is between start and stop (considers midnight clock wrap)

    the 7 possible cases:
    time_is_between("06:00:00", "10:00:00", "18:00:00") # True
    time_is_between("06:00:00", "02:00:00", "18:00:00") # False
    time_is_between("06:00:00", "20:00:00", "18:00:00") # False
    time_is_between("18:00:00", "10:00:00", "6:00:00") # False
    time_is_between("18:00:00", "02:00:00", "6:00:00") # True
    time_is_between("18:00:00", "20:00:00", "6:00:00") # True
    time_is_between("10:00:00", Any, "10:00:00") # ValueError
    """
    if isinstance(start, str):
        start = dateparser.parse(start)
    if isinstance(time, str):
        time = dateparser.parse(time)
    if isinstance(stop, str):
        stop = dateparser.parse(stop)

    if start == stop:
        raise ValueError(f"Cannot resolve ambiguous time span {start}->{stop}")

    A = start < stop
    B = start < time
    C = time < stop
    return (B and C) if A else (B or C)


def time_left(timestr: Union[str, None]) -> int:
    """Parse string and calculate remaining time in minutes"""
    dep = dateparser.parse(timestr)
    time = dep - datetime.now(dep.tzinfo)
    return time.total_seconds() / 60
