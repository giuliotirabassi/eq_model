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
import pickle
from bounding_box import bounding_box
from sources import complex_fault, area_source, URI


if __name__ == "__main__":
	
	MODEL_FOLDER = "SHARE_OQ_input_20140807/source_models/"
	tree = ET.parse(MODEL_FOLDER + "area_source_model.xml") 
	root = tree.getroot()  
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
