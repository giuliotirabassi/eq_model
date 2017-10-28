from shapely.geometry import Polygon

max_lon = 20
min_lon = 4
max_lat = 48
min_lat = 35

bounding_box = Polygon([(min_lon, min_lat),
					   (max_lon, min_lat),
					   (max_lon, max_lat),
					   (min_lon, max_lat)])