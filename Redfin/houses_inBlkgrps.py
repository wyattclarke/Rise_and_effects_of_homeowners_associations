# -*- coding: utf-8 -*-
"""
Created on Sat Jul  1 18:47:57 2017

@author: wyatt.clarke
"""
import arcpy
import pandas as pd

# Associate Redfin houses to their blockgroup
# Set ArcPy environment settings
arcpy.env.workspace = r'C:\Users\wyatt.clarke\Documents\ArcGIS\Projects\HOAs\HOAs.gdb'
arcpy.env.overwriteOutput = True

# Display Redfin latlon points
arcpy.management.MakeXYEventLayer(r"C:\Users\wyatt.clarke\Documents\Research\HOAs\Redfin\csv_data\Downloads\_all_properties.csv", "LONGITUDE", "LATITUDE", "_all_properties_Layer", "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]];-400 -400 1000000000;-100000 10000;-100000 10000;8.98315284119521E-09;0.001;0.001;IsHighPrecision", None)

# Convert points to a feature in ArcGIS
arcpy.management.CopyFeatures("_all_properties_Layer", r"C:\Users\wyatt.clarke\Documents\ArcGIS\Projects\HOAs\HOAs.gdb\_all_properties_feature", None, None, None, None)

# Join points to Census shapefile of blockgroups
arcpy.analysis.SpatialJoin("_all_properties_feature", "C:\Users\wyatt.clarke\Documents\Research\HOAs\Redfin\Shapefiles\US_blck_grp_2010.shp", r"C:\Users\wyatt.clarke\Documents\ArcGIS\Projects\HOAs\HOAs.gdb\_all_properties_feature_inBlkgrps", "JOIN_ONE_TO_ONE", "KEEP_ALL", 'SALE_TYPE "SALE TYPE" true true false 8000 Text 0 0,First,#,_all_properties_feature,SALE_TYPE,0,8000;SOLD_DATE "SOLD DATE" true true false 8000 Text 0 0,First,#,_all_properties_feature,SOLD_DATE,0,8000;PROPERTY_TYPE "PROPERTY TYPE" true true false 8000 Text 0 0,First,#,_all_properties_feature,PROPERTY_TYPE,0,8000;ADDRESS "ADDRESS" true true false 8000 Text 0 0,First,#,_all_properties_feature,ADDRESS,0,8000;CITY "CITY" true true false 8000 Text 0 0,First,#,_all_properties_feature,CITY,0,8000;STATE "STATE" true true false 8000 Text 0 0,First,#,_all_properties_feature,STATE,0,8000;ZIP "ZIP" true true false 8000 Text 0 0,First,#,_all_properties_feature,ZIP,0,8000;PRICE "PRICE" true true false 8 Double 0 0,First,#,_all_properties_feature,PRICE,-1,-1;BEDS "BEDS" true true false 8 Double 0 0,First,#,_all_properties_feature,BEDS,-1,-1;BATHS "BATHS" true true false 8 Double 0 0,First,#,_all_properties_feature,BATHS,-1,-1;LOCATION "LOCATION" true true false 8000 Text 0 0,First,#,_all_properties_feature,LOCATION,0,8000;SQUARE_FEET "SQUARE FEET" true true false 8 Double 0 0,First,#,_all_properties_feature,SQUARE_FEET,-1,-1;LOT_SIZE "LOT SIZE" true true false 8 Double 0 0,First,#,_all_properties_feature,LOT_SIZE,-1,-1;YEAR_BUILT "YEAR BUILT" true true false 8 Double 0 0,First,#,_all_properties_feature,YEAR_BUILT,-1,-1;DAYS_ON_MARKET "DAYS ON MARKET" true true false 8 Double 0 0,First,#,_all_properties_feature,DAYS_ON_MARKET,-1,-1;F__SQUARE_FEET "$/SQUARE FEET" true true false 8 Double 0 0,First,#,_all_properties_feature,F__SQUARE_FEET,-1,-1;HOA_MONTH "HOA/MONTH" true true false 8 Double 0 0,First,#,_all_properties_feature,HOA_MONTH,-1,-1;STATUS "STATUS" true true false 8000 Text 0 0,First,#,_all_properties_feature,STATUS,0,8000;NEXT_OPEN_HOUSE_START_TIME "NEXT OPEN HOUSE START TIME" true true false 8000 Text 0 0,First,#,_all_properties_feature,NEXT_OPEN_HOUSE_START_TIME,0,8000;NEXT_OPEN_HOUSE_END_TIME "NEXT OPEN HOUSE END TIME" true true false 8000 Text 0 0,First,#,_all_properties_feature,NEXT_OPEN_HOUSE_END_TIME,0,8000;URL__SEE_http___www_redfin_com_buy_a_home_comparative_market_ana "URL (SEE http://www_redfin_com/buy-a-home/comparative-market-analysis FOR INFO ON PRICING)" true true false 8000 Text 0 0,First,#,_all_properties_feature,URL__SEE_http___www_redfin_com_buy_a_home_comparative_market_ana,0,8000;SOURCE "SOURCE" true true false 8000 Text 0 0,First,#,_all_properties_feature,SOURCE,0,8000;MLS_ "MLS#" true true false 8000 Text 0 0,First,#,_all_properties_feature,MLS_,0,8000;MLS1 "MLS#" true true false 8000 Text 0 0,First,#,_all_properties_feature,MLS1,0,8000;INTERESTED "INTERESTED" true true false 8000 Text 0 0,First,#,_all_properties_feature,INTERESTED,0,8000;LATITUDE "LATITUDE" true true false 8 Double 0 0,First,#,_all_properties_feature,LATITUDE,-1,-1;LONGITUDE "LONGITUDE" true true false 8 Double 0 0,First,#,_all_properties_feature,LONGITUDE,-1,-1;HOA_YN "HOA_YN" true true false 8000 Text 0 0,First,#,_all_properties_feature,HOA_YN,0,8000;STATEFP10 "STATEFP10" true true false 2 Text 0 0,First,#,US_blck_grp_2010,STATEFP10,0,2;COUNTYFP10 "COUNTYFP10" true true false 3 Text 0 0,First,#,US_blck_grp_2010,COUNTYFP10,0,3;TRACTCE10 "TRACTCE10" true true false 6 Text 0 0,First,#,US_blck_grp_2010,TRACTCE10,0,6;BLKGRPCE10 "BLKGRPCE10" true true false 1 Text 0 0,First,#,US_blck_grp_2010,BLKGRPCE10,0,1;GEOID10 "GEOID10" true true false 12 Text 0 0,First,#,US_blck_grp_2010,GEOID10,0,12;NAMELSAD10 "NAMELSAD10" true true false 13 Text 0 0,First,#,US_blck_grp_2010,NAMELSAD10,0,13;MTFCC10 "MTFCC10" true true false 5 Text 0 0,First,#,US_blck_grp_2010,MTFCC10,0,5;FUNCSTAT10 "FUNCSTAT10" true true false 1 Text 0 0,First,#,US_blck_grp_2010,FUNCSTAT10,0,1;ALAND10 "ALAND10" true true false 14 Double 0 14,First,#,US_blck_grp_2010,ALAND10,-1,-1;AWATER10 "AWATER10" true true false 14 Double 0 14,First,#,US_blck_grp_2010,AWATER10,-1,-1;INTPTLAT10 "INTPTLAT10" true true false 11 Text 0 0,First,#,US_blck_grp_2010,INTPTLAT10,0,11;INTPTLON10 "INTPTLON10" true true false 12 Text 0 0,First,#,US_blck_grp_2010,INTPTLON10,0,12;GISJOIN "GISJOIN" true true false 15 Text 0 0,First,#,US_blck_grp_2010,GISJOIN,0,15;Shape_area "Shape_area" true true false 19 Double 0 0,First,#,US_blck_grp_2010,Shape_area,-1,-1;Shape_len "Shape_len" true true false 19 Double 0 0,First,#,US_blck_grp_2010,Shape_len,-1,-1', "INTERSECT", None, None)

# Export the Redfin blockgroup merge to a csv
arcpy.management.CopyRows("_all_properties_feature_inBlkgrps", r"C:\Users\wyatt.clarke\Documents\Research\HOAs\Redfin\houses_inBlkgrps.csv", None)
