# MopsDisplay 2.0
Display realtime train departures for nearby stations and upcoming events from the HU calendar.

## Setup
```bash
pip install -r requirements.txt
python ./__main__.py
```
(the target system runs python 3.9)

## Configuration
The config file `./data/config.kdl` defines the content that is displayed.<br>
The source file `./src/defines.py` defines the size and font of the content.

## Contribution
Open a GitHub issue/pull-request to request/suggest features or reach out to one of the authors at SBZ MoPS.

## API
The application uses https://v6.bvg.transport.rest/, a free wrapper for the BVG API limited to 100 requests per second

## Working principle
| file | purpose |
| ---- | ------- |
| `config.kdl` | define the content that is displayed |
| `debug.py` | provide debug and benchmark tools |
| `defines.py` | define display properties and source paths |
| `config.py` | read the config file and creates dataclasses from it |
| `data.py` | define these dataclasses and their utility (includes the BVG API requests) |
| `artist.py` | position things on a (tkinter) canvas |
| `__main__.py` | build the tkinter application |

The config file `./data/config.kdl` is parsed to create Event, Poster and Station objects.

### Artists
The application uses a custom GridCanvas to place Artists. These artists manage the position and content updates of everything displayed in the application.

### Stations
Station objects are placed on a GridCavas according to their row/col attributes<br>
Typically only stations in the first column have a title. The latter columns show departures of the same station, but with different directions. The implementation treats each as a single station.<br>
Stations periodically fetch departures from the API and update the displayed information.

### Logo, Events and Posters
The MoPS-logo, events and posters are placed below each other on a different GridCanvas than the stations.<br>
Posters periodically cycle through their images.
