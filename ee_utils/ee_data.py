'''
A general class to collect the data from GEE. Each function in the class will be a different dataset, and they share common variables like the start and end date, the projection etc.
'''

import io
import config.ee_init
import ee
from matplotlib import pyplot as plt
import numpy as np
import requests
import shutil
import zipfile
import os
import logging
from utils.utils import get_points_filter, get_ee_task_list, read_json
import math
import random
import time
from numpy.lib import recfunctions as rfn
import h5py
from retry import retry
from multiprocessing import Pool, cpu_count
from datetime import datetime, timedelta
import hashlib

BIOME_LABELS = read_json('./stats/biome_labels.json')
ECOREGION_LABELS = read_json('./stats/eco_labels.json')


class ee_set:
    def __init__(self, tile, cfg, tile_info = None):
        self.tile = tile
        self.crs = ''
        self.start_date = '2017-01-01' # the start date specifies the general time period for the data. The specific date is specified in the function. We consider a 2 year period
        self.end_date = '2020-12-31' # the end date specifies the general time period for the data. The specific date is specified in the function. We consider a 2 year period
        self.s2_date = ''
        self.s2_imageid = ''
        self.id = tile['properties']['tile_id'] 
        self.polygon = ee.Geometry.Polygon(tile['geometry']['coordinates'])
        self.lon = self.polygon.centroid().coordinates().get(0).getInfo()
        self.lat = self.polygon.centroid().coordinates().get(1).getInfo()
        self.biome = BIOME_LABELS[tile['properties']['biome']]
        self.eco_region = ECOREGION_LABELS[tile['properties']['eco_region']]
        self.cfg = cfg  # loading the config file
        self.export_folder = self.cfg.export_folder
        self.image_set = {}
        self.no_data = False
        self.return_dict = {} # dict to store the arr returned by export_pixels NOT USED
        self.img_bands = {} # a dictionary that stores the bands of each dataset acquired
        self.era5_data = {}
        self.proj = None
        self.s2_type = None
        coord_string = f"{self.lat}_{self.lon}"
        self.seed = int(hashlib.sha256(coord_string.encode('utf-8')).hexdigest(), 16) % 10**5
        random.seed(self.seed)


        

        if tile_info is not None:
            self.s2_date = tile_info['S2_DATE']
            self.crs = tile_info['CRS']
            # self.s2_imageid = tile_info['S2_IMAGEID']
            if self.proj is None:
                self.proj = ee.Projection(self.crs).atScale(10)


        # start series of function calls to get the data
        for function_name in cfg.datasets:
            if hasattr(self, function_name) and callable(getattr(self, function_name)):
                if getattr(self, function_name)() is False:
                    logging.error(f"Function {function_name} returned None")

                    if function_name == 'sentinel2':
                        logging.error(f"Skipping tile {self.id}")
                        self.no_data = True
                        break
            else:
                logging.error(f"Function {function_name} does not exist")
            
        


        # merging all the images into one image - comment these lines if you want to export the images seperately
        if not self.no_data:
            merged_image = self.image_set[self.cfg.datasets[0]] 
            for data_name, image in self.image_set.items():
                if data_name == self.cfg.datasets[0]:
                    continue

                if isinstance(image, dict):
                    for extra_info, img in image.items():
                        if img is None:
                            continue
                        merged_image = ee.Image.cat([merged_image, img])
                elif image is None:
                    continue
                else:
                    merged_image = ee.Image.cat([merged_image, image])

            self.image_set = {}
            if tile_info is not None:
                self.image_set['extra'] = merged_image
            else:
                self.image_set['merged'] = merged_image
                    
                    
        if not self.no_data:
            start = time.time()
            try:
                self.export_local_single()
            except Exception as e:
                logging.error(f"Error exporting to local directory: {e}")
                self.no_data = True
            # self.export_local_parallel()
            logging.debug(f"Time taken for exporting all: {time.time() - start}")
            
        


    ################################################################################################################################################################################################
    # THE FOLLOWING SET OF FUNCTIONS ARE FOR GETTING THE DATA FROM GEE. WRITE A NEW FUNCTION FOR EACH DATASET
    # MAKE SURE THE NAME OF THE FUNCTION IS THE SAME AS THE NAME OF THE DATASET IN THE CONFIG FILE
    # FOR EACH FUNCTION YOU RETURN A DICTIONARY WITH THE NAME OF THE DATASET AS THE KEY AND THE IMAGE AS THE VALUE
    ################################################################################################################################################################################################
    def sentinel2(self, cld_threshold = 10):
        '''
        This function gets the sentinel2 data for the tile. The function searches for the least cloudy image in the time period and returns that image. To ensure 
        that the image covers the entire tile, we use a points filter that only selects the images that have the bottom right and top left points of the tile.

        S2 is used as the base image, and hence we get the date and projection from this image. The bands are selected from the config file.
        
        '''
        start = time.time() 

        cfg = self.cfg.sentinel2
        data_name = cfg.name
        bands_l2a = list(cfg.BANDS[0])
        bands_l1c = list(cfg.BANDS[1])
        collection_l2a = cfg.collection[0]
        collection_l1c = cfg.collection[1]


        rnd_year = random.randint(2017, 2020)
        if rnd_year == 2018:
            # we only go up to november 2018 since l2a is global from dec 2018
            s_date = f"{rnd_year}-01-01"
            e_date = f"{rnd_year}-11-30"
        elif rnd_year == 2017 or rnd_year == 2020:
            s_date = f"{rnd_year}-01-01"
            e_date = f"{rnd_year}-12-31"
        elif rnd_year == 2019:
            # we also include dec 2018
            s_date = f"{rnd_year - 1}-12-01"
            e_date = f"{rnd_year}-12-31"

        # random.seed(self.seed)
        if random.randint(0, 1) == 0:
            S2 = ee.ImageCollection(collection_l2a)\
                    .filterBounds(self.polygon)\
                    .filterDate(f"{s_date}", f"{e_date}")\
                    .filterMetadata('CLOUDY_PIXEL_PERCENTAGE', 'less_than', cld_threshold)
            self.s2_type = 'l2a'
            
            if S2.size().getInfo() == 0:
                S2 = ee.ImageCollection(collection_l1c)\
                    .filterBounds(self.polygon)\
                    .filterDate(f"{s_date}", f"{e_date}")\
                    .filterMetadata('CLOUDY_PIXEL_PERCENTAGE', 'less_than', cld_threshold)
                self.s2_type = 'l1c'
        else:
            S2 = ee.ImageCollection(collection_l1c)\
                    .filterBounds(self.polygon)\
                    .filterDate(f"{s_date}", f"{e_date}")\
                    .filterMetadata('CLOUDY_PIXEL_PERCENTAGE', 'less_than', cld_threshold)
            self.s2_type = 'l1c'
            
        # points_filter = get_points_filter(self.polygon, buffer_size = -200)
        # filtered_images = S2.filter(points_filter)

        filtered_images = S2.filter(ee.Filter.contains('.geo', self.polygon.buffer(200)))

        num_filtered_images = filtered_images.size().getInfo()
        if num_filtered_images == 0:
            logging.error('\t No sentinel2 image found for both l1c and l2a')
            return False
        img_list = filtered_images.toList(filtered_images.size())
        random_number = random.randint(0, num_filtered_images - 1)
        sampled_image_full = ee.Image(img_list.get(random_number))
        # Select the desired bands and clip the image
        if self.s2_type == 'l2a':
            if "MSK_CLDPRB" in sampled_image_full.bandNames().getInfo():
                sampled_image = sampled_image_full.select(bands_l2a).clip(self.polygon).float()
            else:
                new_bands = [band for band in bands_l2a if band != 'MSK_CLDPRB']
                bands_l2a = new_bands
                sampled_image = sampled_image_full.select(new_bands).clip(self.polygon).float()
        else:
            sampled_image = sampled_image_full.select(bands_l1c).clip(self.polygon).float()


        try:
            self.s2_date = sampled_image.date().format('YYYY-MM-dd').getInfo()
        except ee.ee_exception.EEException:
            tmp  = ee.Image(img_list.get(random_number))
            logging.error(f"type: {self.s2_type}, num images in collection: {num_filtered_images}")
            logging.error(f"bands: {tmp.bandNames().getInfo()}")

        tmp = sampled_image.select('B4')
        self.proj = tmp.projection()
        self.crs = self.proj.getInfo()['crs']

        logging.debug(f"\t ID: {self.id}\
                \nBiome name: {self.tile['properties']['biome']}\
                \nEco-region name: {self.tile['properties']['eco_region']}\
                \nDate: {self.s2_date}\
                \nProjection: {self.crs}\
                \nLat: {self.lat} Lon: {self.lon}\
                \nPolygon: {self.polygon.getInfo()['coordinates']}\
                \nS2 type:{self.s2_type}"\
                )
        if self.s2_type == 'l2a':
            scl = sampled_image.select(['SCL', 'QA60']).reproject(self.proj)
            sampled_image = sampled_image.select([band for band in bands_l2a if band not in ['SCL', 'QA60']]).resample('bilinear').reproject(self.proj)
            sampled_image = sampled_image.addBands(scl)
        else:
            qa60 = sampled_image.select('QA60').reproject(self.proj)
            sampled_image = sampled_image.select([band for band in bands_l1c if band != 'QA60']).resample('bilinear').reproject(self.proj)
            sampled_image = sampled_image.addBands(qa60)
        self.image_set[data_name] = sampled_image
        self.img_bands[data_name] = sampled_image.bandNames().getInfo()
        logging.debug('\t Sentinel2 image loaded')
        logging.debug(f"Time taken for {data_name}: {time.time() - start}")
        



    def sentinel1(self):
        '''
        This function gets the sentinel1 data for the tile. We already know the date and projection from the sentinel2 image, so we use that to get the sentinel1 image. 
        If the image on that date is not available, we use the closest available image. We use the VV and VH bands from the image for both ascending and descending orbits.

        '''

        start = time.time()
        
        img = (ee.ImageCollection('COPERNICUS/S1_GRD')
                        .filterDate(self.start_date, self.end_date) # gets images in the specified date range
                        .filterBounds(self.polygon) # gets images that have some overlap with the tile
                        .filter(ee.Filter.contains('.geo', self.polygon.buffer(200))) # gets images containing the tile plus some buffer
                        .map(lambda image: image.clip(self.polygon)) # crops to tile
                        .filterMetadata('instrumentMode', 'equals', 'IW') # selects for the interferometric wide swath mode
                        .map(lambda image: image.set('date_difference', image.date().difference(self.s2_date, 'day').abs())) # calculate days off from S2 image
                        .sort('date_difference')) # sort in ascending order by days off


        # getting the ascending and descending images
        img_asc = img.filterMetadata('orbitProperties_pass', 'equals', 'ASCENDING').first()
        img_desc = img.filterMetadata('orbitProperties_pass', 'equals', 'DESCENDING').first()



        # selecting the bands
        try:
            bands_asc = img_asc.bandNames().getInfo()
            if 'angle' in bands_asc:
                bands_asc.remove('angle')
        except ee.ee_exception.EEException:
            logging.debug('\t No ascending image found')
            img_asc = None
        try:
            bands_desc = img_desc.bandNames().getInfo()
            if 'angle' in bands_desc:
                bands_desc.remove('angle')
        except ee.ee_exception.EEException:
            logging.debug('\t No descending image found')
            img_desc = None

        # if angle bands are available, remove them
        img_asc = img_asc.select(bands_asc).float() if img_asc is not None else None
        img_desc = img_desc.select(bands_desc).float() if img_desc is not None else None

        # resampling the image
        if img_asc is not None:
            img_asc = img_asc.resample('bilinear').reproject(self.proj)
        if img_desc is not None:
            img_desc = img_desc.resample('bilinear').reproject(self.proj)
        
        self.image_set[data_name] = {}
        self.image_set[data_name]['asc'] = img_asc
        self.image_set[data_name]['desc'] = img_desc


        self.img_bands[data_name + '_asc'] = bands_asc if img_asc is not None else None
        self.img_bands[data_name + '_desc'] = bands_desc if img_desc is not None else None

        logging.debug('\t Sentinel1 image loaded')
        logging.debug(f"Time taken for {data_name}: {time.time() - start}")



    def aster(self):
        '''
        This function gets the elevation data for the tile. The data usually consists of the elevation, we also compute the slope from the elevation data, and return both.
        '''
        start = time.time()
        cfg = self.cfg.aster # getting the config for aster elevation data
        data_name = cfg.name # the name used to save the image in the image_set dictionary and the export name
        bands = list(cfg.BANDS) # the bands to be selected from the image

        elevation = ee.Image(cfg.collection).clip(self.polygon).select(bands).float()
        slope = ee.Terrain.slope(elevation)
        merge = ee.Image.cat([elevation, slope])

        
        
        # self.image_set[data_name]['elevation'] = elevation
        # self.image_set[data_name]['slope'] = slope
        merge = merge.resample('bilinear').reproject(self.proj)
        self.image_set[data_name] = merge
        self.img_bands[data_name] = merge.bandNames().getInfo()
    
        logging.debug('\t elevation and slope image loaded')
        logging.debug(f"Time taken for {data_name}: {time.time() - start}")


    def era5(self):
        '''
        This function gets the ERA5 data for the tile. The ERA5 is only computed until the mid of 2020, hence we compute the same stats but for the period of 2018 - 2019. As per the world 
        temperature stats, the average temperature from 2018 - 2021 was roughly the same. We compute 3 sets of stats. 1 for the current month, 1 for the previous month, and 1 for the full year.
        '''

        start = time.time()

        cfg = self.cfg.era5 # getting the config for era5
        data_name = cfg.name
        bands = list(cfg.BANDS)

        parts = self.s2_date.split('-')
        year = int(parts[0])
        month = int(parts[1])

        end_date = (datetime(year, month, 1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        end_date = end_date.strftime('%Y-%m-%d')
        if month > 1:
            month = month - 1
            start_date = f"{year}-{month}-01"
        else:
            month = 12
            start_date = f"{year - 1}-{month}-01"

        # getting 2 months in one image collection
        ERA5_monthly = ee.ImageCollection(cfg.collection)\
                .filterDate(start_date, end_date)\
                .map(lambda image: image.clip(self.polygon))\
                .select(bands)\
                .toBands()
        
        
        # getting the year in one image collection - we get exactly one year of stats including the current month.  
        year, month, _ = map(int, self.s2_date.split('-'))

        # Calculate start_date and end_date for the year
        # we subtract 1 from the year to get the previous year 
        start_date = f"{year - 1}-{month}-01"
        end_date = (datetime(year, month, 1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        end_date = end_date.strftime('%Y-%m-%d')


        ERA5_yearly = ee.ImageCollection(cfg.collection)\
                .filterDate(start_date, end_date)\
                .map(lambda image: image.clip(self.polygon))
        

        def compute_yearly(bandName, imageCollection):
            if 'min' in bandName:
                reducer = ee.Reducer.min()
            elif 'max' in bandName:
                reducer = ee.Reducer.max()
            elif 'total' in bandName:
                reducer = ee.Reducer.sum()
            else:
                reducer = ee.Reducer.mean()
            yearly = imageCollection.select(bandName).reduce(reducer)
            return yearly
        
        
        ERA5_yearly_image = ee.ImageCollection([compute_yearly(band, ERA5_yearly) for band in bands]).toBands().float()
        ERA5_combined = ee.Image.cat([ERA5_monthly, ERA5_yearly_image])

        # if for some reason you wish to export them seperately - uncomment the following lines
        # self.image_set[data_name] = {}
        # self.image_set[data_name]['month1'] = ERA5_month1
        # self.image_set[data_name]['month2'] = ERA5_month2
        # self.image_set[data_name]['year'] = ERA5_yearly_image

        center_pixels = ERA5_combined.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=self.polygon,
            scale=10 
        )
        center_pixels = center_pixels.getInfo()

        band_names = ERA5_combined.bandNames().getInfo()

        self.era5_data['month1'] = [center_pixels[band] for band in band_names[:4]]
        self.era5_data['month2'] = [center_pixels[band] for band in band_names[4:8]]
        self.era5_data['year'] = [center_pixels[band] for band in band_names[8:]]


        # ERA5_combined = ERA5_combined.reproject(self.proj)
        # self.image_set[data_name] = ERA5_combined
        
        self.img_bands[data_name] = band_names


        logging.debug('\t ERA5 image loaded')
        logging.debug(f"Time taken for {data_name}: {time.time() - start}")


    def dynamic_world(self):
        '''
        This function gets the dynamic world data for the tile. The dynamic world data is a collection of images with the same name as the sentinel 2 image for that tile. It consist of 9 classes, we add one more to indicate missing
        information. The classes are as follows: 
        0: No data
        1: Water
        2: Trees
        3: Grass
        4: Flooded vegetation
        5: Crops
        6: Shrub and scrub
        7: Built
        8: Bare
        9: Snow and ice

        We choose the label band since that contains which of these labels were chosen.
        '''
        start = time.time()
        cfg = self.cfg.dynamic_world
        data_name = cfg.name
        bands = list(cfg.BANDS)

        year = self.s2_date.split('-')[0]
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        dw_ic = ee.ImageCollection(cfg.collection)\
                .filterBounds(self.polygon)\
                .filterDate(start_date, end_date)\
                .select(bands)
        


        def reclasify(image):
            label = image.select('label')
            label2 = label\
                    .where(image.eq(0), 1)\
                    .where(image.eq(1), 2)\
                    .where(image.eq(2), 3)\
                    .where(image.eq(3), 4)\
                    .where(image.eq(4), 5)\
                    .where(image.eq(5), 6)\
                    .where(image.eq(6), 7)\
                    .where(image.eq(7), 8)\
                    .where(image.eq(8), 9)\
                    .where(image.eq(9), 10)
            
            # replacing the label band with the new label band
            image = image.addBands(label2.rename('label2'))
            image = image.select('label2')
            image = image.rename('label')
            return image
        
        dw_ic = dw_ic.map(reclasify)
        dw_image = dw_ic.mode().clip(self.polygon)
        
        bands = dw_image.bandNames().getInfo()


        if len(bands) == 0:
            logging.debug('\t No dynamic world image found')
            self.image_set[data_name] = None
        else:
            dw_image = dw_image.reproject(self.proj)
            self.image_set[data_name] = dw_image
            self.img_bands[data_name] = dw_image.bandNames().getInfo()
            logging.debug('\t Dynamic world image loaded')



        logging.debug(f"Time taken for {data_name}: {time.time() - start}")

    def canopy_height_eth(self):
        '''
        This function gets the ETH canopy height and standard deviation from the year 2020.
        '''
        start = time.time()
        cfg = self.cfg.canopy_height_eth  # getting the config for canopy_height_eth
        data_name = cfg.name  # the name used to save the image in the image_set dictionary and the export name
        collections = list(cfg.COLLECTIONS)  # the collections with single bands that will be used

        height = ee.Image(collections[0]).clip(self.polygon).float()
        std = ee.Image(collections[1]).clip(self.polygon).float()
        merge = ee.Image.cat([height, std])

        merge = merge.resample('bilinear').reproject(self.proj)
        merge = merge.rename(['height', 'std'])
        self.image_set[data_name] = merge
        self.img_bands[data_name] = merge.bandNames().getInfo()

        logging.debug('\t ETH canopy height and std loaded')
        logging.debug(f"Time taken for {data_name}: {time.time() - start}")

    def esa_worldcover(self):
        '''
        This function gets the esa worldcover data for the tile.
        '''

        start = time.time()
        cfg = self.cfg.esa_worldcover  # getting the config for esa_worldcover
        data_name = cfg.name  # the name used to save the image in the image_set dictionary and the export name
        bands = list(cfg.BANDS)  # the bands to be selected from the image

        dataset = ee.ImageCollection(cfg.collection).first().clip(self.polygon).select(bands)

        dataset = dataset.reproject(self.proj)

        self.image_set[data_name] = dataset
        self.img_bands[data_name] = dataset.bandNames().getInfo()

        logging.debug('\t esa worldcover loaded')
        logging.debug(f"Time taken for {data_name}: {time.time() - start}")

        





    
    ################################################################################################################################################################################################
    # THE FOLLOWING SET OF FUNCTIONS ARE FOR EXPORTING THE ABOVE DATA TO GCS OR LOCAL DIRECTORY
    ################################################################################################################################################################################################

    def export_local_parallel(self):
        '''
        A function that exports the data to the local directory. To make it parallel, we create the number of processes equal to the
        number of datasets. Each process will export one dataset. 
        '''
        start = time.time()
        # Create a process pool with a limited number of processes
        num_processes = min(len(self.image_set), cpu_count())
        with Pool(num_processes) as pool:
            args_list = [(data_name, image) for data_name, image in self.image_set.items()]
            pool.starmap(self.export_local, args_list)
        logging.debug(f"Time taken for exporting all: {time.time() - start}")
        logging.info(f"Exported all images for {self.id}")

    
    @retry(tries=10, delay=1, backoff=2)
    def export_local(self, data_name, image):
        # data_name, image = args_list
        os.makedirs(f"{self.export_folder}/{data_name}", exist_ok=True)
        if isinstance(image, dict):
            for extra_info, img in image.items():
                if img is None:
                    continue
                start = time.time()
                url = img.getDownloadUrl({
                    'name': f"{data_name}_{extra_info}_{self.id}",
                    'scale': 10,
                    'crs': self.crs,
                    'region': self.polygon.getInfo()['coordinates'],
                    'format': 'GeoTIFF',
                    'bands': img.bandNames().getInfo()
                })  
                logging.debug(f"time taken for getting url: {time.time() - start}")
                
                r = requests.get(url, stream=True, verify=False)
                if r.status_code == 200:
                    with open(f"{self.export_folder}/{data_name}/{self.id}_{extra_info}.tif", 'wb') as f:
                        f.write(r.content)
                    logging.debug(f"Downloaded {data_name} to local directory")
                else:
                    logging.debug(f"Error downloading {data_name} to local directory")
            return
        if image is None:
            return
        start = time.time()
        url = image.getDownloadUrl({
            'name': f"{data_name}_{self.id}",
            'scale': 10,
            'crs': self.crs,
            'region': self.polygon.getInfo()['coordinates'],
            'format': 'GeoTIFF',
            'bands': image.bandNames().getInfo()
        })
        logging.debug(f"time taken for getting url: {time.time() - start}")


        r = requests.get(url, stream=True, verify=False)
  

        if r.status_code == 200:
            with open(f"{self.export_folder}/{data_name}/{self.id}.tif", 'wb') as f:
                f.write(r.content)
            logging.debug(f"Downloaded {data_name} to local directory")
        else:
            logging.debug(f"Error downloading {data_name} to local directory")
            return
        
    @retry(tries=10, delay=1, backoff=2)
    def export_local_single(self):
        for data_name, image in self.image_set.items():
            os.makedirs(f"{self.export_folder}/{data_name}", exist_ok=True)
            if isinstance(image, dict):
                for extra_info, img in image.items():
                    if img is None:
                        continue
                    start = time.time()
                    url = img.getDownloadUrl({
                        'name': f"{data_name}_{extra_info}_{self.id}",
                        'scale': 10,
                        'crs': self.crs,
                        'region': self.polygon.getInfo()['coordinates'],
                        'format': 'GeoTIFF',
                        'bands': img.bandNames().getInfo()
                    })  
                    logging.debug(f"time taken for getting url: {time.time() - start}")
                    start = time.time()
                    r = requests.get(url, stream=True, verify=False)
                    if r.status_code == 200:
                        with open(f"{self.export_folder}/{data_name}/{self.id}_{extra_info}.tif", 'wb') as f:
                            f.write(r.content)
                        logging.debug(f"Downloaded {data_name} to local directory")
                        logging.debug(f"time taken for downloading: {time.time() - start}")

                    else:
                        logging.debug(f"Error downloading {data_name} to local directory")
                return
            if image is None:
                return
            start = time.time()
            url = image.getDownloadUrl({
                'name': f"{data_name}_{self.id}",
                'scale': 10,
                'crs': self.crs,
                'region': self.polygon.getInfo()['coordinates'],
                'format': 'GeoTIFF',
                'bands': image.bandNames().getInfo()
            })
            logging.debug(f"time taken for getting url: {time.time() - start}")
            start = time.time()
            r = requests.get(url, stream=True, verify=False)
    

            if r.status_code == 200:
                with open(f"{self.export_folder}/{data_name}/{self.id}.tif", 'wb') as f:
                    f.write(r.content)
                logging.debug(f"Downloaded {data_name} to local directory")
                logging.debug(f"time taken for downloading: {time.time() - start}")
            else:
                logging.debug(f"Error downloading {data_name} to local directory")
                return

                
    def export(self):
        '''
        Export the images to GCS. Sometimes the dictionary has a sub dictionary, for example sentinel1 has ascending and descending orbits, hence we create a sub dictionary for each orbit
        '''
        logging.debug('\t ---- Exporting images to GCS ----')
        for data_name, image in self.image_set.items():
            if isinstance(image, dict):
                for extra_info, img in image.items():
                    if img is None:
                        continue
                    task = ee.batch.Export.image.toCloudStorage(
                        image = img,
                        description = f"{data_name}_{extra_info}_{self.id}",
                        bucket = self.cfg.bucket,
                        fileNamePrefix = self.export_folder + '/' + data_name + '/' + self.id + '_' + extra_info ,
                        region = self.polygon.getInfo()['coordinates'],
                        scale = 10,
                        crs = self.crs,
                        maxPixels = 1e13
                    )
                    task.start()
                    logging.debug(f"\t Exporting {data_name} to GCS")
                    # print(task.status())
                continue
            task = ee.batch.Export.image.toCloudStorage(
                image = image,
                description = f"{data_name}_{self.id}",
                bucket = self.cfg.bucket,
                fileNamePrefix = self.export_folder + '/' + data_name + '/' + self.id,
                region = self.polygon.getInfo()['coordinates'],
                scale = 10,
                crs = self.crs,
                maxPixels = 1e13
            )
            task.start()
            logging.debug(f"\t Exporting {data_name} to GCS")
            
            # print(task.status())


    @retry(tries=10, delay=1, backoff=2)           
    def download_and_process_image(self, image, crs):
        url = image.getDownloadUrl({
            'bands': image.bandNames().getInfo(),
            'region': self.polygon.getInfo()['coordinates'],
            'scale': 10,
            'format': 'NPY'})
        r = requests.get(url)
        np_geotiff = np.load(io.BytesIO(r.content))

        # np_geotiff = np.load(io.BytesIO(geotiff))
        # cropping the image to 128x128
        new_shape = (128, 128)
        old_shape = np_geotiff.shape
        start_x = (old_shape[0] - new_shape[0]) // 2
        start_y = (old_shape[1] - new_shape[1]) // 2
        np_geotiff = np_geotiff[start_x:start_x + new_shape[0], start_y:start_y + new_shape[1]]

        arr = rfn.structured_to_unstructured(np_geotiff[list(np_geotiff.dtype.names)])
        arr = arr.transpose(2, 0, 1)
        return arr, np_geotiff.dtype.names

    def export_pixels(self):
        '''
        This function exports to the local directory using the computePixels functions.  With this code, I am trying to store the np arrays directly into an HDF5 file.
        '''

        # Initialize dictionaries and arrays
        self.return_dict = {}

        for data_name, image in self.image_set.items():
            if isinstance(image, dict):
                if data_name == 'sentinel1':
                    arr = np.full((8, 128, 128), np.nan)
                elif data_name == 'era5':
                    arr = np.full((12, 128, 128), np.nan)
                    c = 0

                for extra_info, img in image.items():
                    if img is None:
                        continue
                    arr_t, bands_downloaded = self.download_and_process_image(img, self.crs)
                    if data_name == 'sentinel1':
                        if extra_info == 'asc':
                            if 'VV' in bands_downloaded:
                                arr[0] = arr_t[bands_downloaded.index('VV')]
                            if 'VH' in bands_downloaded:
                                arr[1] = arr_t[bands_downloaded.index('VH')]
                            if 'HH' in bands_downloaded:
                                arr[2] = arr_t[bands_downloaded.index('HH')]
                            if 'HV' in bands_downloaded:
                                arr[3] = arr_t[bands_downloaded.index('HV')]
                        elif extra_info == 'desc':
                            if 'VV' in bands_downloaded:
                                arr[4] = arr_t[bands_downloaded.index('VV')]
                            if 'VH' in bands_downloaded:
                                arr[5] = arr_t[bands_downloaded.index('VH')]
                            if 'HH' in bands_downloaded:
                                arr[6] = arr_t[bands_downloaded.index('HH')]
                            if 'HV' in bands_downloaded:
                                arr[7] = arr_t[bands_downloaded.index('HV')]

                    if data_name == 'era5':
                        arr[c:c+4] = arr_t
                        c += 4
                self.return_dict[data_name] = arr
            else:
                arr, bands_downloaded = self.download_and_process_image(image, self.crs)
                self.return_dict[data_name] = arr



    


    # def export_pixels(self):
    #     '''
    #     This function also exports to the local directory. It is good for small files, and holds band information. With this code, i am trying to store the np arrays directly into a hdf5 file.
        
    #     '''


    #     for data_name, image in self.image_set.items():
    #         if isinstance(image, dict):
    #             if data_name == 'sentinel1':
    #                 arr = np.full((8, 128, 128), np.nan)
    #             elif data_name == 'era5':
    #                 arr = np.full((12, 128, 128), np.nan)
    #                 c = 0
                
    #             for extra_info, img in image.items():
    #                 if img is None:
    #                     continue
    #                 img = img.resample('bicubic').reproject(crs=self.crs, scale=10)
    #                 proj = ee.Projection(self.crs).atScale(10).getInfo()

    #                 request = {
    #                     'expression': image,
    #                     'fileFormat': 'NPY',
    #                     'grid': {
    #                         'affineTransform': {
    #                             'scaleX': 10,
    #                             'shearX': 0,
    #                             'shearY': 0,
    #                             'scaleY': -10,
    #                         },
    #                         'crsCode': proj['crs'],
    #                     },

    #                 }
    #                 REQUEST = dict(request)
    #                 geotiff = ee.data.computePixels(REQUEST)
    #                 np_geotiff = np.load(io.BytesIO(geotiff))
                    
    #                 # cropping the image to 128x128
    #                 new_shape = (128, 128)
    #                 old_shape = np_geotiff.shape
    #                 start_x = (old_shape[0] - new_shape[0]) // 2
    #                 start_y = (old_shape[1] - new_shape[1]) // 2
    #                 np_geotiff = np_geotiff[start_x:start_x + new_shape[0], start_y:start_y + new_shape[1]]

    #                 arr_t = np_geotiff.view(np.float32).reshape((-1,) + np_geotiff.shape)
    #                 if data_name == 'sentinel1':
    #                     bands = np_geotiff.dtype.names

    #                     if extra_info == 'asc':
    #                         # put the bands in the correct order [VV, VH, HH, HV], if they are present
    #                         if 'VV' in bands:
    #                             arr[0] = arr_t['VV']
    #                         if 'VH' in bands:
    #                             arr[1] = arr_t['VH']
    #                         if 'HH' in bands:
    #                             arr[2] = arr_t['HH']
    #                         if 'HV' in bands:
    #                             arr[3] = arr_t['HV']
    #                     elif extra_info == 'desc':
    #                         if 'VV' in bands:
    #                             arr[4] = arr_t['VV']
    #                         if 'VH' in bands:
    #                             arr[5] = arr_t['VH']
    #                         if 'HH' in bands:
    #                             arr[6] = arr_t['HH']
    #                         if 'HV' in bands:
    #                             arr[7] = arr_t['HV']
    #                 if data_name == 'era5':
    #                     arr[c:c+4] = arr_t
    #                     c += 4

    #             self.return_dict[data_name] = arr


    #         image = image.resample('bicubic').reproject(crs=self.crs, scale=10)
    #         proj = ee.Projection(self.crs).atScale(10).getInfo()

    #         request = {
    #             'expression': image,
    #             'fileFormat': 'NPY',
    #             'grid': {
    #                 'affineTransform': {
    #                     'scaleX': 10,
    #                     'shearX': 0,
    #                     'shearY': 0,
    #                     'scaleY': -10,
    #                 },
    #                 'crsCode': proj['crs'],
    #             },

    #         }

    #         REQUEST = dict(request)
    #         geotiff = ee.data.computePixels(REQUEST)
    #         np_geotiff = np.load(io.BytesIO(geotiff))
            
    #         # cropping the image to 128x128
    #         new_shape = (128, 128)
    #         old_shape = np_geotiff.shape
    #         start_x = (old_shape[0] - new_shape[0]) // 2
    #         start_y = (old_shape[1] - new_shape[1]) // 2
    #         np_geotiff = np_geotiff[start_x:start_x + new_shape[0], start_y:start_y + new_shape[1]]

    #         arr = np_geotiff.view(np.float32).reshape((-1,) + np_geotiff.shape)                
    #         # display_array = rfn.structured_to_unstructured(np_geotiff[['B4', 'B3', 'B2']])/10000
    #         # plt.imshow(display_array)
    #         # plt.show()
    #         self.return_dict[data_name] = arr


    #         exit()
    #         # writing the np to geoTIFF
    #         from osgeo import gdal
    #         import pyproj
    #         from osgeo import osr

    #         upp_left_coords = self.polygon.bounds().coordinates().get(0).getInfo()[3]

    #         source_proj = pyproj.Proj(proj='latlong', datum='WGS84')
    #         target_proj = pyproj.Proj(init=proj['crs'])

    #         print(upp_left_coords)
    #         print(proj['crs'])

    #         upp_left_x, upp_left_y = pyproj.transform(source_proj, target_proj, upp_left_coords[0], upp_left_coords[1])
    #         tranform_var = (upp_left_x, 10, 0, upp_left_y, 0, -10)
    #         driver = gdal.GetDriverByName('GTiff')
    #         GDT_dtype = gdal.GDT_Float32
    #         rows, cols = np_geotiff.shape[0], np_geotiff.shape[1]
    #         band_num = len(np_geotiff.dtype.names)
    #         outRaster = driver.Create('/Users/qbk152/Desktop/codes/global-LR/gdal-test.tif', cols, rows, band_num, GDT_dtype)

    #         outRaster.SetGeoTransform(tranform_var)
    #         for b in range(band_num):
    #             outband = outRaster.GetRasterBand(b + 1)
    #             outband.WriteArray(np_geotiff[np_geotiff.dtype.names[b]])
            

    #         outRasterSRS = osr.SpatialReference()
    #         outRasterSRS.ImportFromEPSG(int(proj['crs'].split(':')[1]))
    #         outRaster.SetProjection(outRasterSRS.ExportToWkt())

    #         outband.FlushCache()
















    






