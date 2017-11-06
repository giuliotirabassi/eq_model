import numpy as np


KM_TO_DEGREES = 0.0089932  # 1 degree == 111 km


def deg_to_rads(trigonometric_func):
	def new_trig_func(*args):
		rads = [deg * np.pi / 180. for deg in args]
		return trigonometric_func(*rads)
	return new_trig_func


@deg_to_rads
def cos(x):
	return np.cos(x)


@deg_to_rads
def sin(x):
	return np.sin(x)


def angular_distance(km, lat):
    """Return the angular distance of two points at the given latitude"""
    return km * KM_TO_DEGREES / cos(lat)


def rotate(point, angle):
	x, y = point
	new_x = cos(angle) * x + sin(angle) * y
	new_y = -sin(angle) * x + cos(angle) * y
	return (new_x, new_y)


def magnitude_scale_relationship(magnitude, rake):
    """
    Wells and Coppersmith magnitude -- rupture area relationships,
    see 1994, Bull. Seism. Soc. Am., pages 974-2002.
    Implements only median area

    The values are a function of both magnitude and rake.
    Setting the rake to ``None`` causes their "All" rupture-types
    to be applied.

    to get length and width:
    		area = magnitude_scale_relaionship
            rup_length = math.sqrt(area * rupture_aspect_ratio)
			rup_width = area / rup_length
    """
    assert rake is None or -180 <= rake <= 180, "rake is fucked"
    if rake is None:
        # their "All" case
        area = 10.0 ** (-3.49 + 0.91 * magnitude)
    elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
        # strike slip
        area =  10.0 ** (-3.42 + 0.90 * magnitude)
    elif rake > 0:
        # thrust/reverse
        area =  10.0 ** (-3.99 + 0.98 * magnitude)
    else:
        # normal
        area =  10.0 ** (-2.87 + 0.82 * magnitude)
    return area


def generate_ruptures(src, mg):
    hypln, hyplt = src["geometry"][0]

    ar = src["asp_rat"]

    if len(src["hdd"]) > 1:
    	raise ValueError("ops")
    dpt = src["hdd"][0]['depth']

    ruptures = []
    for npd in src["npd"]:
        strike = npd["strike"]
        dip = npd["dip"]
        rake = npd["rake"]

        area = magnitude_scale_relationship(mg, rake)
        lg = np.sqrt(area * ar)
        wd = area / lg
        (updpt, lwdpt) = src["depth"]
        if wd > updpt - lwdpt:
            lg = area / (lwdpt - updpt)
            wd_up = dpt - updpt
            wd_dw = lwdpt - dpt
        else:
            ratio_up = (dpt - updpt) / (lwdpt - updpt)
            wd_up = ratio_up * wd
            ratio_dw = (lwdpt - dpt) / (lwdpt - updpt)
            wd_dw = ratio_dw * wd

        dip_proj_up = wd_up * cos(dip)
        dip_proj_dw = wd_dw * cos(dip)
        top = dpt - wd_up * sin(dip)
        bottom = dpt + wd_dw * sin(dip)

        dx_left = - angular_distance(dip_proj_up, hyplt)
        dx_right = angular_distance(dip_proj_dw, hyplt)
        dy = angular_distance(lg / 2., hyplt)
        corners = [
                (dx_left, -dy),
                (dx_right, -dy),
                (dx_right, dy),
                (dx_left, dy)
                ]
        depths = (top, bottom, bottom, top)
        rupture_proj = [rotate(p, strike) for p in corners]
        rp = [(lon + hypln, lat + hyplt) for lon, lat in rupture_proj]
        rupture = zip(rp, depths)

        ruptures.append({"shape":rupture, "prob":npd["probability"]})
    return ruptures


def generate_all_ruptures(src):
    ruptures = []
    for mg, rt in src['mfd']:
        rups = generate_ruptures(src, mg)
        for rp in rups:
            adj_rt = rt * rp["prob"]
            ruptures.append(
                {"magn": mg,
                "shape": rp["shape"],
                "rate": adj_rt,
                "region": src["tectonicRegion"]}
                )
    return ruptures




