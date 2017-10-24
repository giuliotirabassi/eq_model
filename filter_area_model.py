'''
Read Open Quake SHARE Area Source model.
Select only those sources which might affect Italy,
in this case all the sources intersectinc the bounding box
defined by

	max_lon = 20
	min_lon = 4
	max_lat = 48
	min_lat = 35

Each sources is recasted into a dictionary opbject containing
the necessary ingredients for a subsequent hazard analysis.

The filtered model is stored as list of sources in a pickle file.
'''

import xml.etree.ElementTree as ET
import numpy as np
from shapely.geometry import Polygon
import pickle


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
	src["type"] = src_type

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
	src["type"] = src_type

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

	hdd = source.find(URI + "hypoDepthDist")
	if len(hdd) > 1:
		raise ValueError("weird hyp depth distr")		
	src["hdd"] = {k:float(v) for k,v in hdd[0].attrib.iteritems()}

	npd = source.find(URI + "nodalPlaneDist")
	if len(npd) > 1:
		raise ValueError("weird nodal plane distr")		
	src["npd"] = {k:float(v) for k,v in npd[0].attrib.iteritems()}

	return src, p




if __name__ == "__main__":
	max_lon = 20
	min_lon = 4
	max_lat = 48
	min_lat = 35

	bounding_box = Polygon([(min_lon, min_lat),
						   (max_lon, min_lat),
						   (max_lon, max_lat),
						   (min_lon, max_lat)])

	GIS = "{http://www.opengis.net/gml}"
	MODEL_FOLDER = "SHARE_OQ_input_20140807/source_models/"
	tree = ET.parse(MODEL_FOLDER + "area_source_model.xml") 
	root = tree.getroot()  
	URI = root.tag[:-4]  
	model = root[0]

	sources = []

	for source in model:
		src_type = source.tag.replace(URI,'')

		if  src_type == "complexFaultSource":	
			src, shape = complex_fault(source)

		elif src_type == "areaSource":
			src, shape = area_source(source)

		else:
			raise ValueError("unknown source type " + src_type)	

		# add source only if it intersects the bounding box around Italy
		if shape.intersects(bounding_box):
			sources.append(src)

	with open("area_sources_italy.pkl", "w") as f:
		pickle.dump(sources, f)
