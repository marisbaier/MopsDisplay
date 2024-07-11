"""
MopsDisplay 2.0

Display realtime train departures for nearby stations and upcoming events from the HU calendar.
"""

from itertools import zip_longest
from src import root, defines as d, debug
from src.data import Poster, Station, FETCH_DEPARTURE_TIMER
from src.config import load_data
from src.artist import (
    ClockArtist,
    StackArtist,
    DepartureArtist,
    TitleArtist,
    EventArtist,
    PosterArtist,
    GridCanvas,
    UPDATE_DEPARTURE_TIMER,
)


StationArtist = tuple[Station, list[DepartureArtist]]

STATION_ARTISTS: list[StationArtist] = []
EVENT_ARTISTS: list[EventArtist] = []
POSTER_ARTISTS: list[PosterArtist] = []
CLOCK_ARTISTS: list[ClockArtist] = []


@debug.Timed()
def update_stations():
    """periodically update stations"""
    # reset timers
    FETCH_DEPARTURE_TIMER.reset()
    UPDATE_DEPARTURE_TIMER.reset()

    for station, artists in STATION_ARTISTS:
        update_departures(station, artists)

    FETCH_DEPARTURE_TIMER.readout()
    UPDATE_DEPARTURE_TIMER.readout()
    root.after(d.STATION_UPDATE_TIME, update_stations)


def update_events():
    """periodically update events"""
    # events currently dont update
    root.after(d.EVENT_UPDATE_TIME, update_events)


def update_posters():
    """periodically update posters"""
    for artist in POSTER_ARTISTS:
        artist.update_poster()
    root.after(d.POSTER_UPDATE_TIME, update_posters)


def update_clocks():
    """periodically update clocks"""
    for artist in CLOCK_ARTISTS:
        artist.update_clock()
    root.after(d.CLOCK_UPDATE_TIME, update_clocks)


def update_departures(station: Station, artists: list[DepartureArtist]):
    """update departures of a station"""
    for departure, artist in zip_longest(station.fetch_departures(), artists):
        if artist is None:
            break
        artist.update_departure(departure)


def create_station_artist(
    canvas: GridCanvas, station: Station
) -> StationArtist:
    """Create departures for a station"""

    title_artist = TitleArtist(canvas, station.title, anchor="w")
    departure_artists = [
        DepartureArtist(canvas, anchor="w")
        for _ in range(station.max_departures)
    ]
    stack = StackArtist(
        canvas, 0, 0,
        anchor="w",
        flush="w",
        artists=[title_artist] + departure_artists,
    )

    canvas.set(station.row, station.col, stack)
    return station, departure_artists


def main():
    """main"""
    # define root geometry
    # --------------------
    root.rowconfigure(0, weight=0)
    root.rowconfigure(1, weight=1)
    root.columnconfigure(0, weight=1)
    root.columnconfigure(1, weight=1)

    # load data from config
    # ---------------------
    stations, events, posters = load_data()

    # create stations
    # ---------------
    station_canvas = GridCanvas(
        root,
        flush="w",
        width=d.WIDTH_STATION_CANVAS,
        height=d.HEIGHT_STATION_CANVAS,
        background=d.COLOR_BG_STATION,
        highlightthickness=0,
    )
    station_canvas.grid(row=0, column=0, rowspan=2, sticky="NESW")

    for station in stations:
        artist = create_station_artist(station_canvas, station)
        STATION_ARTISTS.append(artist)

    # create clock and logo
    # ---------------------
    event_canvas = GridCanvas(
        root,
        flush="center",
        width=d.WIDTH_EVENT_CANVAS,
        height=d.HEIGHT_EVENT_CANVAS,
        background=d.COLOR_BG_INFO,
        highlightthickness=0,
    )
    event_canvas.grid(row=1, column=1, sticky="NSEW")

    logo_artist = PosterArtist(event_canvas, Poster(images=[d.LOGO]))
    clock_artist = ClockArtist(event_canvas)
    CLOCK_ARTISTS.append(clock_artist)
    stack = StackArtist(
        event_canvas, 0, 0, artists=[logo_artist, clock_artist]
    )
    event_canvas.set(0, 0, stack)

    # create events
    # -------------
    for event in events:
        event_artist = EventArtist(event_canvas, event)
        EVENT_ARTISTS.append(event_artist)
    title_artist = TitleArtist(
        event_canvas, "nächste Veranstaltungen:",
        font=d.FONT_EVENT,
    )
    event_canvas.set(1, 0, title_artist)

    stack = StackArtist(
        event_canvas, 0, 0,
        anchor="center",
        flush="w",
        artists=EVENT_ARTISTS,
    )
    event_canvas.set(2, 0, stack)

    # create posters
    # --------------
    for row, poster in enumerate(posters):
        artist = PosterArtist(event_canvas, poster)
        event_canvas.set(3 + row, 0, artist)
        POSTER_ARTISTS.append(artist)

    root.after(0, update_stations)
    root.after(0, update_clocks)
    root.after(0, update_posters)
    root.mainloop()


if __name__ == "__main__":
    root.geometry(f"{d.WIDTH_ROOT}x{d.HEIGHT_ROOT}")
    root.attributes("-fullscreen", True)
    main()
