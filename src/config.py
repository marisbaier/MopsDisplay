"""Read the config file and convert its content to dataclasses"""

from pathlib import Path
from typing import List, Tuple, Type

import kdl
from PIL.ImageTk import PhotoImage

from . import defines as d
from .data import Station, DirectionsAndProducts, Event, Poster


def strip(x):
    """Strip tuple/list if there is only one element"""
    if isinstance(x, (tuple, list)):
        if len(x) == 1:
            return x[0]
    return x


# pylint: disable=unused-argument
def kdl2poster(string: kdl.String, raw: kdl.ParseFragment) -> PhotoImage:
    """Convert kdl string to an image path relative to defines.POSTER_PATH"""
    path = d.POSTER_PATH / string.value
    path = path.resolve()

    if not path.is_file():
        raise ValueError(f"Could not find file {path}")
    return d.load_image(path, d.WIDTH_POSTER, d.HEIGHT_POSTER)


# pylint: disable=unused-argument
def reduce_node(node: kdl.Node, raw: kdl.ParseFragment) -> kdl.Node:
    """Reduce the node depth of a kdl node
    Dump the args and child nodes of a kdl node's children into a new kdl node
    """
    args = node.args
    nodes = []
    for child_node in node.nodes:
        args.append(strip(child_node.args))
        nodes += child_node.nodes
    return kdl.Node(name=node.name, args=args, nodes=nodes)


class NodeConverter:
    """Convert the arguments and children of a kdl node into a class
    instance and ship it in a new node"""

    def __init__(self, cls: Type):
        """NodeConverter constructor

        Parameters
        ----------
        cls: class
            The class to create from node args and children
        """
        self.cls = cls

    def __call__(self, node: kdl.Node, raw: kdl.ParseFragment):
        """Actual converter function"""
        args = node.args
        kwargs = {node.name: strip(node.args) for node in node.nodes}
        return kdl.Node(node.name, args=[self.cls(*args, **kwargs)])


def load_config(path: Path):
    """Load a kdl document from path"""
    parse_config = kdl.ParseConfig(
        valueConverters={"poster": kdl2poster},
        nodeConverters={
            "station": NodeConverter(Station),
            "day": NodeConverter(DirectionsAndProducts),
            "night": NodeConverter(DirectionsAndProducts),
            "event": NodeConverter(Event),
            "poster": NodeConverter(Poster),
            "stations": reduce_node,
            "events": reduce_node,
            "posters": reduce_node,
        },
    )

    with open(path, "r", encoding="utf-8") as file:
        doc = kdl.parse(file.read(), config=parse_config)
    return doc


def load_data() -> Tuple[List[Station], List[Event], List[Poster]]:
    """Load stations, events and posters from kdl config

    Returns
    -------
    stations: list[Station]
        Parsed Station instances
    events: list[Events]
        Parsed Event instances
    posters: list[Poster]
        Parsed Poster instances
    """
    doc = load_config(d.CONFIG_PATH)

    stations = doc.get("stations")
    if stations is None:
        raise ValueError("Node 'stations' not found")

    events = doc.get("events")
    if events is None:
        raise ValueError("Node 'events' not found")

    posters = doc.get("posters")
    if posters is None:
        raise ValueError("Node 'posters' not found")

    return stations.args, events.args, posters.args
