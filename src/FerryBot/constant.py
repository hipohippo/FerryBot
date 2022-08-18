from enum import Enum

import sympy.geometry as gm

BUS_POSITOIN_API = "https://services.saucontds.com/tds-map/nyw/nywvehiclePositions.do?"
MAP_TRANSLATION_API = "https://services.saucontds.com/tds-map/nyw/nywmapTranslation.do?"


class ROUTE(Enum):
    # weekend/off peak
    R_44_57 = 90
    R_34_GREEN = 93

    # weekday peak manhattan
    R_50 = 22
    R_42 = 21
    R_57 = 32
    R_34 = 1

    # weekday offpeak
    R_50_57 = 34
    R_34_42 = 36

    # NJ morning
    R_CI = 51  #
    R_NEBLVD = 53


class COORD:
    COORD_50 = {
        5: (40.758547, -73.977167),
        6: (40.759859, -73.980451),
        7: (40.761089, -73.983248),
        8: (40.762264, -73.986099),
    }

    COORD_49 = {
        5: (40.757909, -73.977639),
        6: (40.759244, -73.980869),
        7: (40.760443, -73.983653),
        8: (40.761671, -73.986551),
    }

    ST_49 = gm.Line(gm.Point(*COORD_49[7]), gm.Point(*COORD_49[6]))
    ST_50 = gm.Line(gm.Point(*COORD_50[7]), gm.Point(*COORD_50[6]))

    AVE_7 = gm.Line(gm.Point(*COORD_50[7]), gm.Point(*COORD_49[7]))
    AVE_8 = gm.Line(gm.Point(*COORD_50[8]), gm.Point(*COORD_49[8]))

    ST_DISTANCE_TOLERANCE = 0.5 * gm.Point(*COORD_49[7]).distance(gm.Point(*COORD_50[7])).evalf()
