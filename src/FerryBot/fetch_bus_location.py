import asyncio
from typing import Tuple, List, Callable

import httpx
import numpy as np
import sympy.geometry as gm
from httpx import Response

from FerryBot.constant import BUS_POSITOIN_API, MAP_TRANSLATION_API, ROUTE, COORD


async def fetch_bus_loc(timestamp: int, route: ROUTE) -> Response:
    result = await httpx.AsyncClient().get(BUS_POSITOIN_API, params={"id": route.value, "time": timestamp})
    return result


async def fetch_bus_loc_conversion(route: ROUTE) -> Response:
    conversion = await httpx.AsyncClient().get(MAP_TRANSLATION_API, params={"id": route.value})
    return conversion


def convert_bus_coordinate(bus_result: Response, conversion: Response) -> Tuple[int, List[dict]]:
    """

    :param timestamp:  epoch time
    :param route: Route
    :return: for each bus, return a dictionary {"id": bus_id, "direction": direction, latitude: "latitude", "longitude": longitude}
    """
    # epoch_now = 1000 * pd.Timestamp.utcnow().timestamp()
    ## do not use now().timestamp() - that's incorrect
    ## should be consistent with the output of javascript function new Date().getTime()

    conversion = conversion.json()

    if bus_result.status_code != 200:
        return bus_result.status_code, []
    else:
        buses = bus_result.json()
        locations = []
        for bus in buses:
            bus_id = bus["o"]
            longitude = float((bus["x"] - 0.5) * conversion["mapConversionX"] + conversion["mapBoundsMinX"])
            latitude = float(conversion["mapBoundsMaxY"] - (bus["y"] - 0.5) * conversion["mapConversionY"])
            direction = (float(bus["i"]) / 54) * 10.0  # counterclock wise angles from north.
            locations.append({"id": bus_id, "angle": direction, "latitude": latitude, "longitude": longitude})
        return bus_result.status_code, locations


def locate_bus_on_street(bus_location: gm.Point) -> dict:
    """

    :return:  if a bus is on 49/50 st, return
                  True, on 49, between x and x+1 Ave, closer to x
                  True, on 50, between x and x+1 Ave, closer to x+1
              otherwise
                  False
    """
    # 1 intersection
    dynamic_line = gm.Line(bus_location, slope=COORD.AVE_7.slope)

    intersect_49: gm.Point2D = dynamic_line.intersection(COORD.ST_49)[0]
    intersect_50: gm.Point2D = dynamic_line.intersection(COORD.ST_50)[0]

    distance_49 = intersect_49.distance(bus_location).evalf()
    distance_50 = intersect_50.distance(bus_location).evalf()

    if distance_49 >= COORD.ST_DISTANCE_TOLERANCE and distance_50 >= COORD.ST_DISTANCE_TOLERANCE:
        return {"on49or50": False, "st": None, "range_left": None, "range_right": None, "closer_to": None}
    else:
        if distance_49 < distance_50:
            actual_st = 49
            coords = COORD.COORD_49
            actual_point: gm.Point2D = intersect_49
        else:
            actual_st = 50
            coords = COORD.COORD_50
            actual_point = intersect_50

    # 2 now we have located the bus on street.
    # left or right is the natural side, i.e. 7 is on the left and 5 on the right
    if actual_point.y >= coords[5][1]:
        range_left = 5
        range_right = 1
        closer_to = 5

    if actual_point.y <= coords[8][1]:
        range_left = 12
        range_right = 8
        closer_to = 8

    for ave in range(5, 8):
        if coords[ave][1] >= actual_point.y >= coords[ave + 1][1]:
            range_left = ave + 1
            range_right = ave
            closer_to = ave if actual_point.y >= (coords[ave + 1][1] + coords[ave][1]) / 2 else ave + 1
            break
    return {
        "on49or50": True,
        "st": actual_st,
        "range_left": range_left,
        "range_right": range_right,
        "closer_to": closer_to,
    }


def get_direction(angle: float) -> str:
    if angle <= 30 or angle >= 210:
        return "WEST"
    else:
        return "EAST"


def locate_buses_on_street(buses: List[dict]) -> List[dict]:
    for bus in buses:
        location_analysis = locate_bus_on_street(gm.Point(bus["latitude"], bus["longitude"]))
        bus.update(location_analysis)
        bus["direction"] = get_direction(bus["angle"])
    return buses


def compose_notification(bus: dict) -> str:
    return f"Bus toward {bus.get('direction', '')} on {bus.get('st', '')}. Now between {bus.get('range_left', '')} and {bus.get('range_right', '')}, closer to {bus.get('closer_to', '')}"


def bus_notify_filter_testonly(bus: dict) -> bool:
    return bus["st"] == 49 and bus["direction"] == "WEST" and 5 <= bus["range_left"] <= 7


async def fetch_main(apply_filter: bool, bus_notify_filter: Callable[[dict], bool]):
    bus_result, conversion = await asyncio.gather(fetch_bus_loc(0, ROUTE.R_50), fetch_bus_loc_conversion(ROUTE.R_50))
    status, buses = convert_bus_coordinate(bus_result, conversion)
    buses_with_street = locate_buses_on_street(buses)
    return [compose_notification(bus) for bus in buses_with_street if (not apply_filter) or bus_notify_filter(bus)]


if __name__ == "__main__":
    print(asyncio.run(fetch_main(False, bus_notify_filter_testonly)))
