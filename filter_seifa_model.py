'''
Read Open Quake SHARE SEIFA model.
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

TODO: There is some redundancy with the filter of the area source model
in particular the bounding box, and the functions point_source,
area_source, and cmplex_fault coud be externalized to another module,
as well as the global variables GIS, MODEL_FOLDER etc.
Also, instead of a switch made of if/else (lines 128-135) a function
factory (?) could be implemented

'''

import xml.etree.ElementTree as ET
import numpy as np
from shapely.geometry import Point, Polygon
import pickle


def point_source(source):
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

	geom = source.find(URI + "pointGeometry")
	src["geometry"] = {}
	point = geom.find(GIS + "Point")
	coors = point.find(GIS + "pos").text.split()
	lns, lts = [float(x) for x in coors]
	src["geometry"] = [(lns, lts)]

	p = Point(src["geometry"])

	hdd = source.find(URI + "hypoDepthDist")		
	src["hdd"] = [{k:float(v) for k,v in h.attrib.iteritems()} for h in hdd]

	npd = source.find(URI + "nodalPlaneDist")	
	src["npd"] = [{k:float(v) for k,v in n.attrib.iteritems()} for n in npd]

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
	tree = ET.parse(MODEL_FOLDER + "seifa_model.xml") 
	root = tree.getroot()  
	URI = root.tag[:-4]  
	model = root[0]

	sources = []

	for source in model:
		src_type = source.tag.replace(URI,'')

		if  src_type == "pointSource":	
			src, shape = point_source(source)

		elif src_type == "areaSource":
			src, shape = area_source(source)

		else:
			raise ValueError("unknown source type " + src_type)	

		if shape.intersects(bounding_box):
			sources.append(src)

	with open("seifa_sources_italy.pkl", "w") as f:
		pickle.dump(sources, f)


