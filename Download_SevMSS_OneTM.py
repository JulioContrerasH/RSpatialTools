# !pip install git+https://github.com/csaybar/cubo.git@ee-support --upgrade

import ee
import cubo
import pathlib
import numpy as np
import xarray as xr
import rioxarray
import geopandas as gpd
from datetime import datetime

ee.Authenticate(auth_mode='localhost')
ee.Initialize(project="ee-julius013199")

OUTPUTFOLDER = "dataset_mss_tm"
pathlib.Path(OUTPUTFOLDER).mkdir(parents=True, exist_ok=True)

metadata = gpd.read_file("db/points.geojson")
metadata["ROI_ID"] = ["ROI_%05d" % i for i in range(len(metadata))]


mss_collections = [
    'LANDSAT/LM04/C02/T1',
    'LANDSAT/LM04/C02/T2',
    'LANDSAT/LM05/C02/T1',
    'LANDSAT/LM05/C02/T2',
]

tm_collections = [
    'LANDSAT/LT05/C02/T1_TOA',
    'LANDSAT/LT05/C02/T2_TOA',
    'LANDSAT/LT04/C02/T1_TOA',
    'LANDSAT/LT04/C02/T2_TOA',
]


for index, row in metadata.iterrows():

    if index == 0 or index == 1:
        continue


    print("Processing ROI: %s" % row["ROI_ID"])

    roi_path = pathlib.Path(OUTPUTFOLDER) / row["ROI_ID"]
    roi_path.mkdir(parents=True, exist_ok=True)

    lon, lat = row.geometry.x, row.geometry.y

    point = ee.Geometry.Point(lon, lat)

    mss_ids = []
    for collection in mss_collections:
        images = ee.ImageCollection(collection).filterBounds(point)
        ids = images.aggregate_array('system:index').getInfo()
        ids_full = [collection + '/' + s for s in ids]
        mss_ids.extend(ids_full)

    tm_id = None
    for collection in tm_collections:
        images = ee.ImageCollection(collection).filterBounds(point)
        id_list = images.aggregate_array('system:index').getInfo()
        ids_full = [collection + '/' + s for s in id_list]
        if id_list:  # Si hay imágenes en esta colección, tomar la primera ID y terminar el bucle
            tm_id = ids_full[0]
            break

    for i in range(len(mss_ids)):

        if mss_ids:
            mss_id = mss_ids[i]  # Tomar el primer ID de MSS como ejemplo
            mss_img = ee.Image(mss_id)

        name_sec = mss_img.get("system:time_start").getInfo() 
        datetime_object = datetime.utcfromtimestamp(name_sec / 1000)
        formatted_date = datetime_object.strftime('%Y_%m_%d')

        if tm_id:
            tm_img = ee.Image(tm_id)

        name_sec_2 = tm_img.get("system:time_start").getInfo() 
        datetime_object2 = datetime.utcfromtimestamp(name_sec_2 / 1000)
        formatted_date2 = datetime_object2.strftime('%Y_%m_%d')

        da_mss = cubo.ee.create(
            lat=lat,
            lon=lon,
            collection=mss_img,
            bands=["B1", "B2", "B3", "B4"],
            edge_size=1024//2,
            band_projection=1
        )

        da_tm = cubo.ee.create(
            lat=lat,
            lon=lon,
            collection=tm_img,
            bands=["B1", "B2", "B3", "B4", "B5", "B6", "B7"],
            edge_size=1024,
            band_projection=3
        )

        da_mss.rio.write_crs(da_mss.attrs["epsg"], inplace=True)
        download_mss = da_mss.squeeze()

        reflectance_mult = np.array([
            mss_img.get("REFLECTANCE_MULT_BAND_1").getInfo(),
            mss_img.get("REFLECTANCE_MULT_BAND_2").getInfo(),
            mss_img.get("REFLECTANCE_MULT_BAND_3").getInfo(),
            mss_img.get("REFLECTANCE_MULT_BAND_4").getInfo()
        ])

        reflectance_add = np.array([
            mss_img.get("REFLECTANCE_ADD_BAND_1").getInfo(),
            mss_img.get("REFLECTANCE_ADD_BAND_2").getInfo(),
            mss_img.get("REFLECTANCE_ADD_BAND_3").getInfo(),
            mss_img.get("REFLECTANCE_ADD_BAND_4").getInfo()
        ])

        new_download_mss = download_mss.copy().astype("float32")
        for x in range(4):
            new_download_mss[x] = download_mss[x]*reflectance_mult[x] + reflectance_add[x]
        new_download_mss = new_download_mss*10000
        new_download_mss = new_download_mss.astype("uint16")
        
        new_download_mss.rio.to_raster(
            roi_path / ("mss_" + formatted_date + ".tif"),
            dtype="uint16",
            tiled=True,
            blockxsize=256,
            blockysize=256,
            bigtiff=True,
            compress="lzw"        
        )

        file_path_tm = roi_path / ("tm_" + formatted_date2 + ".tif")

        if file_path_tm.exists():
            pass

        da_tm.rio.write_crs(da_tm.attrs["epsg"], inplace=True)
        download_tm = (da_tm.squeeze() * 10000).astype("uint16")
        download_tm.rio.to_raster(
            file_path_tm,
            dtype="uint16",
            tiled=True,
            blockxsize=256,
            blockysize=256,
            bigtiff=True,
            compress="lzw"
        )
