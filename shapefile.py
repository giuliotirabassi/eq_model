from shapely.geometry import Polygon
import pandas as pd
from scipy.interpolate import interp1d
import json
import numpy as np

df = pd.read_csv("/Users/giuliotirabassi/Downloads/output-10-hcurves-csv/CentralItaly_PGA_PoEat50years.csv")


groups = df.groupby(["LocationID"])

data = []
for locid, g in groups:
    f = interp1d(g["PoE"].values, g["PGA [g]"].values)
    data.append([locid, f(0.02)])

newdf = pd.DataFrame(data=data, columns=["LocationID", "PGA2pc50y"])
latlondf = df[["LocationID","Latitude", "Longitude"]].drop_duplicates()

hazmapdf = pd.merge(latlondf, newdf, left_on=u"LocationID", right_on=u"LocationID")

RESOLUTION = 0.01

dx = RESOLUTION / 2.

pga_bins = {
    n: "{}-{}".format(
        0.1*n, 
        0.1*(n+1)
    ) for n in range(10)
}

polygons = []
for i in hazmapdf.index:
    latitude, longitude = hazmapdf.loc[i,["Latitude", "Longitude"]]
    corners = [
        (longitude - dx, latitude - dx),
        (longitude + dx, latitude - dx),
        (longitude + dx, latitude + dx),
        (longitude - dx, latitude + dx),
        ]
    pga = float(hazmapdf.loc[i,"PGA2pc50y"])
    l = int(pga * 10)
    p = Polygon(corners)
    polygons.append([l, pga_bins[l], p])

united_polygons = {}
for pgabin in pga_bins:
    u = Polygon()
    polys = [p for l, b, p in polygons if l == pgabin]
    for p in polys:
        u = u.union(p)
    united_polygons[pgabin] = u


features = []
for binp, p in united_polygons.iteritems():
    if len(p.bounds)==0:
        continue
    if p.type == "Polygon":
        coordinates = [p.boundary.coords[:]]
    else:
        coordinates = [[pp.boundary.coords[:]] if pp.boundary.type=="LineString" else [ppp.coords[:] for ppp in pp.boundary] for pp in p]
    label = pga_bins[binp]
    centerpga = np.mean([float(x) for x in label.split("-")])

    feature = {
          "type": "Feature",
          "geometry": {
            "type": p.type,
            "coordinates": coordinates
          },
          "properties": {
            "pga": label,
            "id":binp,
            "centerpga":centerpga
          }
        }
    features.append(feature)

geojson = {
        "crs": {
      "type": "EPSG",
      "properties": { 
         "code": 4326,
         "coordinate_order": [1, 0]
      }
    },
      "type": "FeatureCollection",
      "features":features
  }

with open("hazard_map.geojson", "w") as file_:
    json.dump(geojson, file_)

