from shapely.geometry import Polygon
import pandas as pd
from scipy.interpolate import interp1d
import json

df = pd.read_csv("/Users/giuliotirabassi/Downloads/output-10-hcurves-csv/CentralItaly_PGA_PoEat50years.csv")


groups = df.groupby(["LocationID"])

data = []
for locid, g in groups:
    f = interp1d(g["PoE"].values, g["PGA [g]"].values, fillvalues=[])
    data.append([locid, f(0.02)])

newdf = pd.DataFrame(data=data, columns=["LocationID", "PGA2pc50y"])
latlondf = df[["LocationID","Latitude", "Longitude"]].drop_duplicates()

hazmapdf = pd.merge(latlondf, newdf, left_on=u"LocationID", right_on=u"LocationID")

RESOLUTION = 0.01

dx = RESOLUTION / 2.
features = []
for i in hazmapdf.index:
    latitude, longitude = hazmapdf.loc[i,["Latitude", "Longitude"]]
    corners = [
        (longitude - dx, latitude - dx),
        (longitude + dx, latitude - dx),
        (longitude + dx, latitude + dx),
        (longitude - dx, latitude + dx),
        ]
    feature = {
          "type": "Feature",
          "geometry": {
            "type": "Polygon",
            "coordinates": [corners]
          },
          "properties": {
            "pga": float(hazmapdf.loc[i,"PGA2pc50y"]),
            "id":hazmapdf.loc[i,"LocationID"],
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

