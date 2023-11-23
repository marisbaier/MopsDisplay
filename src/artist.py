"""Manage (tkinter) canvas placement"""

from datetime import datetime
from itertools import cycle
from math import floor
from tkinter import Canvas
from tkinter.font import Font
from typing import Any, Callable, List, Tuple, Union

from . import defines as d
from . import debug
from .config import Event, Poster
from .data import Departure


UPDATE_DEPARTURE_TIMER = debug.TimedCumulative("departure display update")


def fontheight(font: Font) -> int:
    """Get height of font"""
    return font.metrics("linespace")


def lineheight(font: Font) -> int:
    """Get linewidth of font"""
    return int(1.3 * fontheight(font))


def textheight(text: str, font: Font) -> int:
    """Get height of a string in a font"""
    newlines = 1 + text.count("\n")
    return newlines * lineheight(font)


def textwidth(text: str, font: Font) -> int:
    """Get width of a string in a font"""
    return font.measure(text)


# transform x coordinates from a corner to the center
corner2center_x: dict[str, Callable[[int, int], int]] = {
    "nw": lambda x, width: x + width / 2,
    "ne": lambda x, width: x - width / 2,
    "se": lambda x, width: x - width / 2,
    "sw": lambda x, width: x + width / 2,
    "n": lambda x, width: x,
    "e": lambda x, width: x - width / 2,
    "s": lambda x, width: x,
    "w": lambda x, width: x + width / 2,
    "center": lambda x, width: x,
}

# transform x coordinates from the center to a corner
center2corner_x: dict[str, Callable[[int, int], int]] = {
    "nw": lambda x, width: x - width / 2,
    "ne": lambda x, width: x + width / 2,
    "se": lambda x, width: x + width / 2,
    "sw": lambda x, width: x - width / 2,
    "n": lambda x, width: x,
    "e": lambda x, width: x + width / 2,
    "s": lambda x, width: x,
    "w": lambda x, width: x - width / 2,
    "center": lambda x, width: x,
}

# transform y coordinates from a corner to the center
corner2center_y: dict[str, Callable[[int, int], int]] = {
    "nw": lambda y, height: y + height / 2,
    "ne": lambda y, height: y + height / 2,
    "se": lambda y, height: y - height / 2,
    "sw": lambda y, height: y - height / 2,
    "n": lambda y, height: y + height / 2,
    "e": lambda y, height: y,
    "s": lambda y, height: y - height / 2,
    "w": lambda y, height: y,
    "center": lambda y, height: y,
}

# transform y coordinates from the center to a corner
center2corner_y: dict[str, Callable[[int, int], int]] = {
    "nw": lambda y, height: y - height / 2,
    "ne": lambda y, height: y - height / 2,
    "se": lambda y, height: y + height / 2,
    "sw": lambda y, height: y + height / 2,
    "n": lambda y, height: y - height / 2,
    "e": lambda y, height: y,
    "s": lambda y, height: y + height / 2,
    "w": lambda y, height: y,
    "center": lambda y, height: y,
}


def _validate_corner(corner: Union[str, None]) -> str:
    if corner is None:
        return "center"
    if corner in corner2center_x:
        return corner
    raise ValueError(f"Unexpected anchor/corner {corner}")


class Cell:
    """Cell with static size"""

    def __init__(
        self, x: int, y: int, width: int, height: int, anchor: str = None
    ):
        """Cell constructor

        Parameters
        ----------
        x, y: int
            Anchor coordinates
        width, height: int
            Dimensions of cell
        anchor: str, optional
            Specify which point in the cell the coordinates (x, y) describe.
            Defaults to None (center). See anchor for possible values
        """
        self._x = int(x)
        self._y = int(y)
        self._width = int(width)
        self._height = int(height)
        if anchor is None:
            anchor = "center"  # center = default
        self._anchor = _validate_corner(anchor)

    def _corners_differ(self, corner: Union[str, None]) -> bool:
        if corner == self.anchor:
            return False
        return True

    def get_x(self, corner: Union[str, None]) -> int:
        """Get x coordinate of a corner

        Parameters
        ----------
        corner: str
            Which corner to get the coordinate from. None means cell's anchor.
            See anchor for possible values
        """
        corner = _validate_corner(corner)
        x = self.x
        if self._corners_differ(corner):
            x = corner2center_x[self.anchor](x, self.width)
            x = center2corner_x[corner](x, self.width)
        return x

    def set_x(self, x: int, corner: Union[str, None]):
        """Set x coordinate of a corner to the given value

        Parameters
        ----------
        x: int
            x coordinate to place the corner at
        corner: str
            Which corner to get the coordinate from. None means cell's anchor.
            See anchor for possible values
        """
        corner = _validate_corner(corner)
        self.x += x - self.get_x(corner)

    @property
    def x(self) -> int:
        """Anchor coordinate x"""
        return self._x

    @x.setter
    def x(self, x: float):
        self._x = int(x)

    def get_y(self, corner: Union[str, None]) -> int:
        """Get y coordinate of a corner

        Parameters
        ----------
        corner: str
            Which corner to get the coordinate from. None means cell's anchor.
            See anchor for possible values
        """
        corner = _validate_corner(corner)
        y = self.y
        if self._corners_differ(corner):
            y = corner2center_y[self.anchor](y, self.height)
            y = center2corner_y[corner](y, self.height)
        return y

    def set_y(self, y: int, corner: Union[str, None]):
        """Set y coordinate of a corner to the given value

        Parameters
        ----------
        y: int
            y coordinate to place the corner at
        corner: str
            Which corner to get the coordinate from. None means cell's anchor.
            See anchor for possible values
        """
        corner = _validate_corner(corner)
        self.y += y - self.get_y(corner)

    @property
    def y(self) -> int:
        """Anchor coordinate y"""
        return self._y

    @y.setter
    def y(self, y: float):
        self._y = int(y)

    @property
    def width(self) -> int:
        """Cell width"""
        return self._width

    @property
    def height(self) -> int:
        """Cell height"""
        return self._height

    @property
    def anchor(self) -> str:
        """Cell anchor
        Possible values: "nw", "n", "ne", "e", "se", "s", "sw", "w", "center"
        """
        return self._anchor

    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        """Artist bounding box (xmin, ymin, xmax, ymax)"""
        return (
            self.get_x("nw"),
            self.get_y("nw"),
            self.get_x("se"),
            self.get_y("se"),
        )


class Artist(Cell):
    """Artist that draws on a tkinter canvas"""

    def __init__(
        self,
        canvas: Canvas,
        x: int,
        y: int,
        width: int,
        height: int,
        anchor: str = None,
    ):
        """Artist constructor

        Parameters
        ----------
        canvas: tkinter.Canvas
            Canvas to draw on
        x, y: int
            Anchor coordinates
        width, height: int
            Dimensions of cell
        anchor: str, optional
            Specify which point in the cell the coordinates (x, y) describe.
            Defaults to None (center). See anchor for possible values
        """
        super().__init__(x, y, width, height, anchor=anchor)

        self.canvas = canvas
        self._debug_id_border = None
        self._debug_id_anchor = None

    def update_position(self):
        """Perform position update"""

    def draw_debug_outlines(self, depth: int = 0):
        """Draw debug outlines around the artist

        Debug outlines consists of a rectangle around the bounding box and a
        circle at the anchor coordinate

        Parameters
        ----------
        depth: int
            How deep the artist is nested within other artists.
            Determines the outline color
        """
        color = debug.COLORS[depth]
        radius = 5
        self.canvas.create_rectangle(
            *self.bbox, tags="debug_outlines", outline=color
        )
        self.canvas.create_oval(
            self.x - radius,
            self.y - radius,
            self.x + radius,
            self.y + radius,
            tags="debug_outlines",
            fill=color,
        )


class StackArtist(Artist):
    """Vertical stack of artists that move as a union
    Width and height is defines by the artists in the stack
    """

    def __init__(
        self,
        canvas: Canvas,
        x: int,
        y: int,
        anchor: str = None,
        flush: str = None,
        artists: List[Artist] = None,
    ):
        """StackArtist constructor

        Parameters
        ----------
        canvas: tkinter.Canvas
            Canvas to draw on
        x, y: int
            Anchor coordinates
        anchor: str, optional
            Specify which point in the cell the coordinates (x, y) describe.
            Defaults to None (center). See anchor for possible values
        flush: str, optional
            Specify which direction to flush artists inside the stack if they
            have different sizes. Defaults to None (center). See anchor for
            possible values
        artists: list[Artist]
            Artists to stack onto each other
        """
        self.flush = _validate_corner(flush)
        self._artists: List[Artist] = [] if artists is None else artists

        height = sum(a.height for a in self._artists)
        width = (
            max(a.width for a in self._artists)
            if len(self._artists) > 0
            else 0
        )
        super().__init__(canvas, x, y, width, height, anchor=anchor)

    def update_position(self):
        """Perform position update
        Move all artists in the stack accordingly
        """
        x = self.get_x(self.flush)
        y = self.get_y("nw")
        for artist in self._artists:
            artist.set_x(x, self.flush)
            artist.set_y(y, "nw")
            y += artist.height
            artist.update_position()
        return super().update_position()

    def draw_debug_outlines(self, depth: int = 0):
        """Draw debug outlines of the StackArtists and all held artists
        See Artist.draw_debug_outlines for detail
        """
        for artist in self._artists:
            artist.draw_debug_outlines(depth=depth + 1)
        return super().draw_debug_outlines(depth)


class DepartureArtist(Artist):
    """Displays departure information on a canvas
    Includes a line icon, the destination and the time remaining until
    departure
    """

    WIDTH_SPACE = textwidth(" ", d.FONT_DEPARTURE)

    def __init__(self, canvas: Canvas, anchor: str = None):
        """DepartureArtist constructor

        Will be constructed at (0, 0).
        Size is determined by defines.WIDTH_ICON, defines.WIDTH_DIRECTION,
        defines.WIDTH_TIME and defines.FONT_DEPARTURE

        Parameters
        ----------
        canvas: tkinter.Canvas
            Canvas to draw on
        anchor: str, optional
            Specify which point in the cell the coordinates (x, y) describe.
            Defaults to None (center). See anchor for possible values
        """
        # create artist
        width = (
            d.WIDTH_ICON
            + d.WIDTH_DIRECTION
            + d.WIDTH_TIME
            + 2 * self.WIDTH_SPACE
        )
        height = lineheight(d.FONT_DEPARTURE)
        super().__init__(canvas, 0, 0, width, height, anchor=anchor)

        # create contents
        self.last_tripid = None
        self.id_icon = self.canvas.create_image(0, 0, anchor="center")
        self.id_drct = self.canvas.create_text(
            0,
            0,
            text="could not fetch departure",
            anchor="w",
            font=d.FONT_DEPARTURE,
            fill=d.COLOR_ERROR,
        )
        self.id_dots = self.canvas.create_text(
            0, 0, anchor="e", font=d.FONT_DEPARTURE, fill=d.COLOR_TXT
        )
        self.id_time = self.canvas.create_text(
            0, 0, anchor="e", font=d.FONT_DEPARTURE, fill=d.COLOR_TXT
        )

    def update_position(self):
        x = self.get_x("w")
        y = self.get_y("w")
        self.canvas.coords(self.id_icon, x + d.WIDTH_ICON // 2, y)
        x += d.WIDTH_ICON + self.WIDTH_SPACE
        self.canvas.coords(self.id_drct, x, y)
        x += d.WIDTH_DIRECTION
        self.canvas.coords(self.id_dots, x, y)
        x += self.WIDTH_SPACE + d.WIDTH_TIME
        self.canvas.coords(self.id_time, x, y)
        return super().update_position()

    @UPDATE_DEPARTURE_TIMER
    def update_departure(self, departure: Union[Departure, None]):
        """Update displayed departure information

        Parameters
        ----------
        departure: Departure|None
            The departure information to display. None displays an error
        """
        tripid = getattr(departure, "id", None)

        if tripid != self.last_tripid:
            self.last_tripid = tripid
            self.configure_icon(departure)
            self.configure_drct(departure)
        self.configure_time(departure)

    def clear_departure(self):
        """Display an error"""
        self.last_tripid = None
        self.configure_icon(None)
        self.configure_drct(None)
        self.configure_time(None)

    def configure_icon(self, departure: Union[Departure, None]):
        """Change the displayed icon

        Parameters
        ----------
        departure: Departure|None
            The departure information. None displays nothing
        """
        # no deaprture found
        if departure is None:
            self.canvas.itemconfigure(self.id_icon, image=d.ICONS.get("empty"))
            return

        # get icon
        icon = d.ICONS.get(departure.line, None)
        if icon is None:
            icon = d.ICONS.get(departure.product, None)
            print(f"Warning: Fallback icon used for {departure.line}")
        if icon is None:
            icon = d.ICONS.get("default")
            print(f"Warning: Default icon used for {departure.line}")

        # configure
        self.canvas.itemconfigure(self.id_icon, image=icon)

    def configure_drct(self, departure: Union[Departure, None]):
        """Change the displayed direction/destination

        Parameters
        ----------
        departure: Departure|None
            The departure information. None displays an error
        """
        # no departure found
        string = getattr(departure, "direction", None)
        if not isinstance(string, str):
            self.canvas.itemconfigure(
                self.id_drct,
                text="could not fetch departure",
                fill=d.COLOR_ERROR,
            )
            self.canvas.itemconfigure(self.id_dots, text=" ")
            return

        # get display string and dots
        for filt, replacement in d.DIRECTION_FILTER:
            string = string.replace(filt, replacement)

        width_dot = textwidth(".", d.FONT_DEPARTURE)
        available = d.WIDTH_DIRECTION
        occupied = textwidth(string, d.FONT_DEPARTURE)

        if occupied < available:
            # display string fits, fill remainder with dots
            count = (available - occupied) // width_dot
            dots = "." * count if count > 1 else ""
        else:
            # display string does not fit, cut off after last fitting char
            idx = len(string)
            occupied = width_dot
            for i, char in enumerate(string):
                new_occupied = occupied + textwidth(char, d.FONT_DEPARTURE)
                if new_occupied >= available:
                    idx = i
                    break
                occupied = new_occupied
            string = string[:idx] + "."
            dots = ""

        # configure
        self.canvas.itemconfigure(self.id_drct, text=string, fill=d.COLOR_TXT)
        self.canvas.itemconfigure(self.id_dots, text=dots)

    def configure_time(self, departure: Union[Departure, None]) -> str:
        """Change displayed remaining time

        Parameters
        ----------
        departure: Departure|None
            The departure information. None displays nothing
        """
        # no departure found
        if departure is None:
            self.canvas.itemconfigure(self.id_time, text=" ")
            return

        time = (
            "?"
            if departure.time_left is None
            else str(floor(departure.time_left))
        )
        color = d.COLOR_TXT if departure.reachable else d.COLOR_NOTIME
        self.canvas.itemconfigure(self.id_time, text=time, fill=color)


class TitleArtist(Artist):
    """Displays a title on a canvas
    Has 1px width so it can be used without disturbing grid placement
    """

    def __init__(
        self, canvas: Canvas, text: str, font: Font = d.FONT_TITLE, anchor=None
    ):
        """TitleArtist constructor

        Will be constructed at (0, 0)
        Width is 1px, height is determined by font

        Parameters
        ----------
        canvas: tkinter.Canvas
            Canvas to draw on
        text: str
            Text to display
        font: tkinter.Font, optional
            Font to use. Defaults to defines.FONT_TITLE
        anchor: str, optional
            Specify which point in the cell the coordinates (x, y) describe.
            Defaults to None (center). See anchor for possible values
        """
        height = textheight(text, font)
        super().__init__(canvas, 0, 0, 1, height, anchor=anchor)

        self.id_title = self.canvas.create_text(
            0, 0, text=text, anchor=self.anchor, font=font, fill=d.COLOR_TXT
        )

    def update_position(self):
        self.canvas.coords(self.id_title, self.x, self.y)
        return super().update_position()


class EventArtist(Artist):
    """Display event information
    Includes a date and a description
    """

    WIDTH_SPACE = textwidth(" ", d.FONT_EVENT)

    def __init__(self, canvas: Canvas, event: Event, anchor=None):
        """EventArtist constructor

        Will be constructed at (0, 0)
        Size is determined defines.WIDTH_DATE, defines.FONT_EVENT and the
        string event.desc

        Parameters
        ----------
        canvas: tkinter.Canvas
            Canvas to draw on
        event: Event
            The event to display
        anchor: str, optional
            Specify which point in the cell the coordinates (x, y) describe.
            Defaults to None (center). See anchor for possible values
        """
        width = (
            d.WIDTH_DATE
            + self.WIDTH_SPACE
            + textwidth(event.desc, d.FONT_EVENT)
        )
        height = max(
            textheight(event.date, d.FONT_EVENT),
            textheight(event.desc, d.FONT_EVENT),
        )
        super().__init__(canvas, 0, 0, width, height, anchor=anchor)

        self.id_date = self.canvas.create_text(
            0,
            0,
            text=event.date,
            anchor="nw",
            font=d.FONT_EVENT,
            fill=d.COLOR_TXT,
        )
        self.id_desc = self.canvas.create_text(
            0,
            0,
            text=event.desc,
            anchor="nw",
            font=d.FONT_EVENT,
            fill=d.COLOR_TXT,
        )

    def update_position(self):
        x = self.get_x("nw")
        y = self.get_y("nw")
        self.canvas.coords(self.id_date, x, y)
        self.canvas.coords(
            self.id_desc, x + d.WIDTH_DATE + self.WIDTH_SPACE, y
        )
        return super().update_position()


class PosterArtist(Artist):
    """Displays cycling posters"""

    def __init__(self, canvas: Canvas, poster: Poster, anchor=None):
        """PosterArtist constructor

        Will be constructed at (0, 0)
        Size is determined by the largest poster.

        Parameters
        ----------
        canvas: tkinter.Canvas
            Canvas to draw on
        poster: Poster
            Poster to display
        anchor: str, optional
            Specify which point in the cell the coordinates (x, y) describe.
            Defaults to None (center). See anchor for possible values
        """
        width = max(img.width() for img in poster.images)
        height = max(img.height() for img in poster.images)
        super().__init__(canvas, 0, 0, width, height, anchor=anchor)

        self.canvas = canvas
        self.posters = cycle(poster.images)
        self.id_poster = self.canvas.create_image(
            0, 0, image=next(self.posters), anchor="center"
        )

    def update_position(self):
        self.canvas.coords(
            self.id_poster, self.get_x("center"), self.get_y("center")
        )
        return super().update_position()

    def update_poster(self):
        """Cycle to next poster"""
        self.canvas.itemconfigure(self.id_poster, image=next(self.posters))


class ClockArtist(Artist):
    """Displays a digital clock in the format HH:MM"""

    def __init__(self, canvas: Canvas, anchor=None):
        """ClockArtist constructor

        Will be constructed at (0, 0)
        Size is determined by defines.FONT_CLOCK

        Parameters
        ----------
        canvas: tkinter.Canvas
            Canvas to draw on
        anchor: str, optional
            Specify which point in the cell the coordinates (x, y) describe.
            Defaults to None (center). See anchor for possible values
        """
        height = lineheight(d.FONT_CLOCK)
        width = textwidth("00:00", d.FONT_CLOCK)
        super().__init__(canvas, 0, 0, width, height, anchor=anchor)

        self.canvas = canvas
        self.id_time = self.canvas.create_text(
            0, 0, anchor="center", fill=d.COLOR_TXT, font=d.FONT_CLOCK
        )

    def update_position(self):
        self.canvas.coords(
            self.id_time, self.get_x("center"), self.get_y("center")
        )
        return super().update_position()

    def update_clock(self):
        """Update clock to current time"""
        timestr = datetime.now().strftime("%H:%M")
        self.canvas.itemconfigure(self.id_time, text=timestr)


class GridCanvas(Canvas):
    """Canvas that evenly aligns artists in a grid
    Automatically re-aligns artists if the canvas size changes
    """

    def __init__(self, master, flush: str = None, **options):
        """GridCanvas constructor

        Parameters
        ----------
        master: tkinter.Frame
            tkinter frame to create canvas on
        flush: str, optional
            Specify which direction to flush artists inside the grid if they
            have different sizes. Defaults to None (center). See Artist.anchor
            for possible values
        **options
            Keyword arguments passed to tkinter.Canvas.__init__()
        """
        super().__init__(master, **options)
        self.bind("<Configure>", self.on_resize)

        self.flush = _validate_corner(flush)
        self.artists: dict[tuple[int, int], Artist] = {}

    def set(self, row: int, col: int, artist: Artist):
        """Set artist to grid position (row, col)

        Parameters
        ----------
        row: int
            Row to place artist in
        col: int
            Column to place artist in
        artist: Artist
            Artist to place at (row, col)
        """
        self.artists[row, col] = artist

    def get(self, row: int, col: int, *default) -> Union[Artist, Any]:
        """Get artist at grid position (row, col)

        Parameters
        ----------
        row: int
            Row to get artist from
        col: int
            Column to get artist from
        *default:
            Optional default value if (row, col) has no artist

        Return
        ------
        Artist|Any
            The artist at grid position (row, col) or passed default value if
            grid position is empty
        """
        return self.artists.get((row, col), *default)

    def pop(self, row: int, col: int, *default) -> Union[Artist, Any]:
        """Pop artist at grid position (row, col)

        Parameters
        ----------
        row: int
            Row to pop artist from
        col: int
            Column to pop artist from
        *default:
            Optional default value if (row, col) has no artist

        Return
        ------
        Artist|Any
            The artist at grid position (row, col) or passed default value if
            grid position is empty
        """
        return self.artists.pop((row, col), *default)

    def query_size(self):
        """Get minimal row and column sizes (widths, heights) required to place
        the artists in the grid
        """
        widths = []
        heights = []
        for (row, col), artist in self.artists.items():
            while len(widths) <= col:
                widths.append(0)
            while len(heights) <= row:
                heights.append(0)
            widths[col] = max(widths[col], artist.width)
            heights[row] = max(heights[row], artist.height)
        return widths, heights

    @debug.Timed("artist position updates")
    def on_resize(self, event):
        """Canvas resize event callback, evenly space artists"""
        # delete debug outlines, since they will potentially be re-drawn
        self.delete("debug_outlines")

        # calculate size and available padding for evenly spacing artists
        widths, heights = self.query_size()
        padx = (event.width - sum(widths)) / (1 + len(widths))
        pady = (event.height - sum(heights)) / (1 + len(heights))

        # evenly place artists
        y = pady
        for row, height in enumerate(heights):
            x = padx
            for col, width in enumerate(widths):
                # place artist if there is one
                artist = self.artists.get((row, col), None)
                if artist is not None:
                    cell = Artist(self, x, y, width, height, anchor="nw")
                    artist.set_x(cell.get_x(self.flush), self.flush)
                    artist.set_y(cell.get_y(self.flush), self.flush)
                    artist.update_position()

                    # draw debug outlines
                    if debug.DEBUG:
                        cell.draw_debug_outlines(depth=0)
                        artist.draw_debug_outlines(depth=1)
                x += width + padx
            y += height + pady
