# Enter your script here.


#%%capture
#!pip install contextily==0.99.0

#--------------------------------------------------------------
import civis
import os
import sys
import pandas as pd
from matplotlib import pyplot as plt
import numpy as np
import seaborn as sns
import civis.io
import zipfile
import geopandas as gpd
from shapely.geometry import Point,multipoint
from shapely.ops import nearest_points
import itertools
from scipy import stats
#import contextily as ctx
from fiona.crs import from_epsg
import warnings
warnings.filterwarnings('ignore')
from sqlalchemy import create_engine


import matplotlib
#%matplotlib inline

#--------------------------------------------------------------
print('This code started')
#conn = create_engine('redshift+psycopg2://dokeowo@host.amazonaws.com:5439/database')
#print('This is 0 after python', sys.argv[0], 'and type is:', type(sys.argv[0]))
#print('This is 1 after python', sys.argv[1], 'and type is:', type(int(sys.argv[1])))
#print('This is 2 after python', sys.argv[2], 'and type is:', type(float(sys.argv[2])))
#print('This is 3 after python', sys.argv[3], 'and type is:', type(sys.argv[3]))
#print('This is 3 after python', sys.argv[4], 'and type is:', type(sys.argv[4]))

#table_01 = '''fed.task6_civis_estimate_serious_damage_leftjoin_hud__demographics'''
table_01 = sys.argv[1]
ref_01   = int(sys.argv[2])
table_02 = sys.argv[3]
ref_02   = int(sys.argv[4])
ref_prj = int(sys.argv[5])
table_out = sys.argv[6]

#table_02 = '''dev.high_water_rescue'''
# ref_01 = 4326
# ref_02 = 4326
#ref_prj = 32615
#table = os.environ["table_01"]
#table2 = os.environ["table_02"]
#print('This is table 01:' , table)
#print('This is table 02:' ,table2)
#print('This type table 01:' ,type(table))
#print('This type table 02:' ,type(table2))
#--------------------------------------------------------------

# record level data 

unmatched_query= '''

    
    SELECT
     userdefinedfltyid,
      latitude as latitude_ref,
      longitude as longitude_ref,serious_damage_bucket__hazus,flood_zone_type__hazus,
      neighborhood__hazus
    FROM ''' + table_01 + ''' as ia
    WHERE data_boolean__hud=0
    
    ORDER BY userdefinedfltyid

'''

unmatched_query_table = civis.io.read_civis_sql(
    unmatched_query,"City of Houston",use_pandas=True
)


print(unmatched_query)

# 1b) Convert the imported unmatched table to GeoDataFrame
unmatched_query_geo = gpd.GeoDataFrame(unmatched_query_table)
unmatched_query_geo['point'] = unmatched_query_geo.apply(lambda x: Point(x['longitude_ref'],x['latitude_ref']), axis = 1)
unmatched_query_geo['geometry'] = unmatched_query_geo.point

# 1c) Convert umatched point -unmatched_query_geo from Geographic to UTM Zone 15N
unmatched_query_geo_crs = unmatched_query_geo
# Assign WGS 84 Coordinate System
unmatched_query_geo_crs.crs = from_epsg(ref_01)
# Project from WGS to Projected Coordinate System
unmatched_query_geo_prj = unmatched_query_geo_crs.to_crs(epsg=32615)



#--------------------------------------------------------------
# record level data 

highwater_query= '''
SELECT
     
        objectid_1,
        lat as latitude,
        long as longitude


FROM ''' + table_02 + ''' as h

   
ORDER BY h.objectid_1

'''
print('This code completed')
highwater_table = civis.io.read_civis_sql(
    highwater_query,"City of Houston",use_pandas=True
)


print(highwater_query)
#You may uncomment this
#highwater_table.head()


# 2b) Convert the imported matched point to GeoDataFrame
highwater_geo = gpd.GeoDataFrame(highwater_table)
highwater_geo['point'] = highwater_geo.apply(lambda x: Point(x['longitude'],x['latitude']), axis = 1)
highwater_geo['geometry'] = highwater_geo.point

# 4c) Convert highwater point -highwater_geo from Geographic to UTM Zone 15N
#print(debris_geo.crs)
highwater_geo_crs = highwater_geo
# Assign WGS 84 Coordinate System
highwater_geo_crs.crs = from_epsg(ref_02)
print(highwater_geo.crs)
#Project from WGS to Projected Coordinate System
highwater_geo_prj = highwater_geo.to_crs(epsg=32615)
highwater_geo_prj.head()

# Step II: Spatial indexing in GeoPandas (kdTree) to find the nearest neighbor
from scipy.spatial import cKDTree 

# 1b) Define function for kdTree

def ckdnearest(gdA, gdB, bcol):   
    nA = np.array(list(zip(gdA.geometry.x, gdA.geometry.y)) )
    nB = np.array(list(zip(gdB.geometry.x, gdB.geometry.y)) )
    btree = cKDTree(nB)
    dist, idx = btree.query(nA,k=1)
    df = pd.DataFrame.from_dict({'distance': dist.astype(float),
                             'ID_of_NearestPoint' : gdB.loc[idx, bcol].values })
    return df


# 2) Estimate Nearest Distance of unmatched points to events:

# 2c) highwater rescues
nearest_highwater =ckdnearest(unmatched_query_geo_prj, highwater_geo_prj,'objectid_1')

#..................................................................
#create table dr.optimal authorization dokeowo;

optimalproimity = civis.io.dataframe_to_civis(nearest_highwater, "City of Houston",table_out)
optimalproimity.result()
print('I got to the last line')
