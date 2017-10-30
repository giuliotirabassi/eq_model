'''
library to convert OQ xml formatted sources into more digestible ones

'''

import numpy as np
from shapely.geometry import Polygon, Point, LineString


GIS = "{http://www.opengis.net/gml}"
URI = '{http://openquake.org/xmlns/nrml/0.4}'


def edge_geometry(edge):
	points = [float(x) for x in edge.find(GIS + "posList").text.split()]
	lns = points[0::3]
	lts = points[1::3]
	dps = points[2::3]
	if len(set(dps)) > 1:
		raise ValueError("Too many depth values for source " + source.get("id"))
	line = zip(lns, lts)
	return {"depth": dps[0], "points": line}


def complex_fault(source):
	src = source.attrib.copy()
	src["type"] = source.tag.replace(URI,'')

	mfd = source.find(URI + "incrementalMFD") 
	min_mag = float(mfd.attrib["minMag"])
	bw = float(mfd.attrib["binWidth"])
	rates = [float(r) for r in mfd[0].text.split()]
	magnitudes = min_mag + (np.arange(len(rates)) * 0.5) * bw
	src["mfd"] = zip(magnitudes, rates)

	aspect_ratio = float(source.find(URI + "ruptAspectRatio").text)
	src["asp_rat"] = aspect_ratio
	
	rake = float(source.find(URI + "rake").text)
	src["rake"] = rake

	geom = source.find(URI + "complexFaultGeometry")
	src["geometry"] = {}
	topedge = geom.find(URI + "faultTopEdge").find(GIS + "LineString")
	bottomedge = geom.find(URI + "faultBottomEdge").find(GIS + "LineString")
	src["geometry"]["top"] = edge_geometry(topedge)
	src["geometry"]["bottom"] = edge_geometry(bottomedge)

	poly_points =  src["geometry"]["top"]["points"] + src["geometry"]["bottom"]["points"][::-1]
	p = Polygon(poly_points)

	return src, p


def area_source(source):
	src = source.attrib.copy()
	src["type"] =  source.tag.replace(URI,'')

	mfd = source.find(URI + "incrementalMFD") 
	min_mag = float(mfd.attrib["minMag"])
	bw = float(mfd.attrib["binWidth"])
	rates = [float(r) for r in mfd[0].text.split()]
	magnitudes = min_mag + (np.arange(len(rates)) * 0.5) * bw
	src["mfd"] = zip(magnitudes, rates)

	aspect_ratio = float(source.find(URI + "ruptAspectRatio").text)
	src["asp_rat"] = aspect_ratio	

	geom = source.find(URI + "areaGeometry")
	src["geometry"] = {}
	poly = geom.find(GIS + "Polygon")
	if len(poly) > 1:
		raise ValueError("This polygon has holes")
	perimeter = poly.find(GIS + "exterior").find(GIS + "LinearRing").find(GIS + "posList")
	points = [float(x) for x in perimeter.text.split()]
	lns = points[0::2]
	lts = points[1::2]
	src["geometry"] = zip(lns, lts)

	p = Polygon(src["geometry"])

	updpt = float(geom.find(URI + "upperSeismoDepth").text)
	lwdpt = float(geom.find(URI + "lowerSeismoDepth").text)
	src["depth"] = (updpt, lwdpt)

	hdd = source.find(URI + "hypoDepthDist")
	if len(hdd) > 1:
		raise ValueError("weird hyp depth distr")		
	src["hdd"] = {k:float(v) for k,v in hdd[0].attrib.iteritems()}

	npd = source.find(URI + "nodalPlaneDist")
	if len(npd) > 1:
		raise ValueError("weird nodal plane distr")		
	src["npd"] = {k:float(v) for k,v in npd[0].attrib.iteritems()}

	return src, p


def point_source(source):
	src = source.attrib.copy()
	src["type"] =  source.tag.replace(URI,'')

	mfd = source.find(URI + "incrementalMFD") 
	min_mag = float(mfd.attrib["minMag"])
	bw = float(mfd.attrib["binWidth"])
	rates = [float(r) for r in mfd[0].text.split()]
	magnitudes = min_mag + (np.arange(len(rates)) * 0.5) * bw
	src["mfd"] = zip(magnitudes, rates)

	aspect_ratio = float(source.find(URI + "ruptAspectRatio").text)
	src["asp_rat"] = aspect_ratio	

	geom = source.find(URI + "pointGeometry")
	src["geometry"] = {}
	point = geom.find(GIS + "Point")
	coors = point.find(GIS + "pos").text.split()
	lns, lts = [float(x) for x in coors]
	src["geometry"] = [(lns, lts)]

	p = Point(src["geometry"])

	updpt = float(geom.find(URI + "upperSeismoDepth").text)
	lwdpt = float(geom.find(URI + "lowerSeismoDepth").text)
	src["depth"] = (updpt, lwdpt)

	hdd = source.find(URI + "hypoDepthDist")		
	src["hdd"] = [{k:float(v) for k,v in h.attrib.iteritems()} for h in hdd]

	npd = source.find(URI + "nodalPlaneDist")	
	src["npd"] = [{k:float(v) for k,v in n.attrib.iteritems()} for n in npd]

	return src, p


def line_geometry(edge):
	points = [float(x) for x in edge.find(GIS + "posList").text.split()]
	lns = points[0::2]
	lts = points[1::2]
	line = zip(lns, lts)
	return line


def simple_fault(source):
	src = source.attrib.copy()
	src["type"] =  source.tag.replace(URI,'')

	mfd = source.find(URI + "truncGutenbergRichterMFD") 
	min_mag = float(mfd.attrib["minMag"])
	max_mag = float(mfd.attrib["maxMag"])
	a = float(mfd.attrib["aValue"])
	b = float(mfd.attrib["bValue"])
	mgs = np.linspace(min_mag, max_mag, 30)
	bw = mgs[1] - mgs[0]
	rate = lambda mag_lo: 10 ** (a - b * mag_lo) - 10 ** (a - b * (mag_lo + bw))
	rates = [rate(m) for m in mgs[0:-1]]
	magnitudes = mgs[0:-1] + 0.5 * bw
	src["mfd"] = zip(magnitudes, rates)

	aspect_ratio = float(source.find(URI + "ruptAspectRatio").text)
	src["asp_rat"] = aspect_ratio
	
	rake = float(source.find(URI + "rake").text)
	src["rake"] = rake	

	geom = source.find(URI + "simpleFaultGeometry")
	line = geom.find(GIS + "LineString")
	points = line_geometry(line)
	src["geometry"] = points

	p = LineString(src["geometry"])

	updpt = float(geom.find(URI + "upperSeismoDepth").text)
	lwdpt = float(geom.find(URI + "lowerSeismoDepth").text)
	src["depth"] = (updpt, lwdpt)

	dip = float(geom.find(URI + "dip").text)
	src["dip"] = dip

	return src, p
