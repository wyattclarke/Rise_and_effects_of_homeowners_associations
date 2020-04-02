# -*- coding: utf-8 -*-
"""
Created on Thu Feb 15 17:15:00 2018

@author: wyatt
"""

# Load functions used to read ZTRAX data files. Might need to open file to adjust file paths or function options.
#exec(open(r'C:\Users\wyatt\Research\Zillow\ReadZTRAX.py').read())
import pandas as pd
import numpy as np
import os 
import feather

os.chdir(r'G:\Zillow')

#Load layout file for ZTrans
layout_ZTrans = pd.read_excel(r'Created\Layout.xlsx', sheetname='ZTrans')
layout_ZAsmt = pd.read_excel(r'Created\Layout.xlsx', sheetname='ZAsmt')

# LOAD FUNCTIONS FOR READING ZTRAX TABLES
# Function for reading a Ztrans table with row and column criteria
def read_ZTrans(state_code, table_name, col_indices, row_crit_field, row_crit_content):
    path = "G:\\Zillow\\{}\\ZTrans\\{}.txt".format(state_code, table_name)
    layout_temp = layout_ZTrans.loc[layout_ZTrans.TableName=='ut{}'.format(table_name), :].reset_index()
    names=layout_temp['FieldName'][col_indices]
    dtype=layout_temp['PandasDataType'][col_indices].to_dict()
    encoding='ISO-8859-1'
    sep = '|'
    header=None
    quoting=3
    chunksize=500000

    iter = pd.read_csv(path, quoting=quoting, names=names, dtype=dtype, encoding=encoding, sep=sep, header=header, usecols=col_indices, iterator=True, chunksize=chunksize)
    return pd.concat([chunk[(chunk[row_crit_field].isin(row_crit_content))] for chunk in iter])

# Function for reading a ZAsmt table with row and column criteria
def read_ZAsmt(state_code, table_name, col_indices, row_crit_field, row_crit_content):
    path = "G:\\Zillow\\{}\\ZAsmt\\{}.txt".format(state_code, table_name)
    layout_temp = layout_ZAsmt.loc[layout_ZAsmt.TableName=='ut{}'.format(table_name), :].reset_index()
    names=layout_temp['FieldName'][col_indices]
    dtype=layout_temp['PandasDataType'][col_indices].to_dict()
    encoding='ISO-8859-1'
    sep = '|'
    header=None
    quoting=3
    chunksize=500000

    iter = pd.read_csv(path, quoting=quoting, names=names, dtype=dtype, encoding=encoding, sep=sep, header=header, usecols=col_indices, iterator=True, chunksize=chunksize)
    return pd.concat([chunk[(chunk[row_crit_field].isin(row_crit_content))] for chunk in iter])

# Function for reading a Ztrans table with ALL rows and column criterion
def read_ZTrans_long(state_code, table_name, col_indices):
    path = "G:\\Zillow\\{}\\ZTrans\\{}.txt".format(state_code, table_name)
    layout_temp = layout_ZTrans.loc[layout_ZTrans.TableName=='ut{}'.format(table_name), :].reset_index()
    names=layout_temp['FieldName'][col_indices]
    dtype=layout_temp['PandasDataType'][col_indices].to_dict()
    encoding='ISO-8859-1'
    sep = '|'
    header=None
    quoting=3

    return pd.read_csv(path, quoting=quoting, names=names, dtype=dtype, encoding=encoding, sep=sep, header=header, usecols=col_indices)


# Define function for mashing up a record for each unique parcel from a state   
def parcel_list(state):
    #for state in state_codes:
        ######################################################################################################
    # CREATE LIST OF PARCELS THAT HAVE EVER BEEN MORTGAGED
    # List of all transactions
    Main_ZTrans = read_ZTrans_long(state, 'Main', [0,4,89,90]) # uniq ID, transaction type, pud and condo riders
    PropertyInfo = read_ZTrans_long(state, 'PropertyInfo', [0,64]) # cross reference to assessment records
    Main_ZTrans = Main_ZTrans.merge(PropertyInfo, on=['TransId'], how='left')
    Main_ZTrans = Main_ZTrans[Main_ZTrans['ImportParcelID'].notnull()] # Drop observations with no Assessor Parcel Number
    del PropertyInfo
    
    # Recode the PUD and Condo variables to be 0/1 indicators. Add an indicator for being a mortgage record.
    Main_ZTrans['pud'] = np.where(Main_ZTrans['PlannedUnitDevelopmentRiderFlag'].notnull(), 1, 0)
    Main_ZTrans['condo'] = np.where(Main_ZTrans['CondominiumRiderFlag'].notnull(), 1, 0)
    Main_ZTrans['mortgage'] = np.where(Main_ZTrans['DataClassStndCode'].isin(['H', 'M']), 1, 0) # H: deed with concurrent mortgage, M: mortgage
    
    # Group by parcel to create an indicator of whether that parcel has ever been associated with an HOA or been mortgaged
    Main_ZTrans['pud'] = Main_ZTrans.groupby('ImportParcelID')['pud'].transform(sum) # Count instances of PUD rider on property
    #Main_ZTrans.loc[Main_ZTrans['pud']>0, 'pud'] = 1 # Set any value above 0 to 1
    Main_ZTrans['condo'] = Main_ZTrans.groupby('ImportParcelID')['condo'].transform(sum)
    #Main_ZTrans.loc[Main_ZTrans['condo']>0, 'condo'] = 1
    Main_ZTrans['mortgage'] = Main_ZTrans.groupby('ImportParcelID')['mortgage'].transform(sum)
    
    # Keep list of ever-mortgaged parcels, associated to whether those parcels have ever been mortgaged with an HOA rider
#    Main_ZTrans = Main_ZTrans[Main_ZTrans['mortgage']>0] # Drop transactions from parcels that have never been mortgaged
    Main_ZTrans = Main_ZTrans[['ImportParcelID', 'pud', 'condo', 'mortgage']].drop_duplicates() # Keep only these few columns and drop duplicate transactions, reducing the dataframe to a non-duplicated list of parcels that have ever been mortgaged
    transactions = Main_ZTrans['ImportParcelID'].tolist() # Create list of ever-mortaged parcels, used below to limit which assessed parcels to load
    
    ############################################################################################################
    # MATCH TO THE ASSESSED CHARACTERSITICS OF THOSE PARCELS
    # Add housing characteristics from ZAsmt_Building
        #  Load list of all parcels from ZAsmt:
    Main = read_ZAsmt(state, "Main", [0,1,2,3,26,29,38,49,68,70,74,80,81,82,83], 'ImportParcelID', transactions)
        # Create list to link ZAsmt_Main to ZAsmt_Building
    parcels = Main['RowID'].drop_duplicates().tolist()   
    
    # Upload the Building spreadsheet
        # Load building characteristics. Zillow only reports the main structure on each parcel.
    Building = read_ZAsmt(state, "Building", [0,1,2,5,10,12,14,18,19,25,29,31,32,35,37], 'RowID', parcels)
        # Create a dummy for being owner occupied
    Building['ownerocc'] = np.where(Building['OccupancyStatusStndCode'].notnull(), 1, 0)
        # Convert build quality grades to integer values
    Building['buildquality'] = Building['BuildingQualityStndCode'].replace({'A+': 1, 'A': 2, 'A-': 3, 'B+': 4, 'B': 5, 'B-': 6, 'C+': 7, 'C': 8, 'C-': 9, 'D+': 10, 'D': 11, 'D-': 12, 'F': 13, 'E+': 13, 'E': 13, 'E-': 13})  
    # Rename variable for the total number of rooms
    Building['totrms'] = Building['TotalRooms']    
    # Rename variable for the number of bedrooms
    Building['bdrms'] = Building['TotalBedrooms']
        # Compute the number of baths, as the sum of full and half baths
    Building['baths'] = Building['TotalCalculatedBathCount'] #FullBath'].astype(float) + 0.5*Building['HalfBath'].astype(float)
        # Fireplace
    Building['fireplace'] = np.where(((Building['FireplaceFlag'].notnull()) | (Building['FireplaceNumber'].notnull())), 1, 0)
        # Tile roof
    Building['tile_rf'] = np.where(Building['RoofCoverStndCode']=='TL', 1, 0)
        # Trim unnecessary columns and merge to the main spreadsheet, which includes sale price
    Building = Building.drop(['OccupancyStatusStndCode', 'BuildingQualityStndCode', 'TotalRooms', 'RoofCoverStndCode', 'TotalBedrooms', 'TotalCalculatedBathCount', 'FireplaceFlag', 'FireplaceNumber'], axis=1) 
    Building = Building.drop_duplicates('RowID')
    Main = Main.merge(Building, on='RowID', how='inner')
    del Building
    
    # Upload the spreadsheet of assessed value
    Value = read_ZAsmt(state, 'Value', [0,1,2,3], 'RowID', parcels)
    Main = Main.merge(Value[['RowID', 'TotalAssessedValue']].drop_duplicates('RowID'), on='RowID', how='left')
    Main['tax_rate'] = Main['TaxAmount'] / Main['TotalAssessedValue']
    Main.loc[~Main['tax_rate'].between(0,.1), 'tax_rate'] = np.nan
    del Value
    
    # Upload the spreadsheet of lot site appeal codes assessed value
    LotSiteAppeal = read_ZAsmt(state, 'LotSiteAppeal', [0,1], 'RowID', parcels)
    LotSiteAppeal['waterfrnt'] = np.where(LotSiteAppeal['LotSiteAppealStndCode'].isin(['VWL', 'VWO', 'VWR', 'WFB', 'WFC', 'WFS']), 1, np.nan)
    Main = Main.merge(LotSiteAppeal[['RowID', 'waterfrnt']].drop_duplicates('RowID'), on='RowID', how='left')   
    LotSiteAppeal['golf'] = np.where(LotSiteAppeal['LotSiteAppealStndCode'].isin(['GLF']), 1, np.nan)
    Main = Main.merge(LotSiteAppeal[['RowID', 'golf']].drop_duplicates('RowID'), on='RowID', how='left')
    del LotSiteAppeal
    
    # Upload the spreadsheet of building area. Use total area, which is the only consistently reported quantity.
    BuildingAreas = read_ZAsmt(state, 'BuildingAreas', [0,1,2,3,4], 'RowID', parcels)
    BuildingAreas['BuildingAreaSqFt'] = BuildingAreas['BuildingAreaSqFt'].astype(float)
    BuildingAreas = BuildingAreas[BuildingAreas['BuildingAreaSequenceNumber']==1]
    BuildingAreas = BuildingAreas[BuildingAreas['BuildingAreaStndCode'].isin(['BAB', 'BAE', 'BAF', 'BAG', 'BAH', 'BAJ', 'BAL', 'BAT', 'BLF'])]
    BuildingAreas = BuildingAreas.sort_values(by='BuildingAreaSqFt', ascending=False)
    BuildingAreas = BuildingAreas[['RowID', 'BuildingAreaSqFt']].drop_duplicates('RowID')
    Main = Main.merge(BuildingAreas, on='RowID', how='left')
    del BuildingAreas
    
    # Upload the spreadsheet of interior flooring
    InteriorFlooring = read_ZAsmt(state, 'InteriorFlooring', [0,1,2], 'RowID', parcels)
    InteriorFlooring['carpet_fl'] = np.where(InteriorFlooring['InteriorFlooringTypeStndCode'].isin(['CP']), 1, np.nan)
    Main = Main.merge(InteriorFlooring[['RowID', 'carpet_fl']].drop_duplicates('RowID'), on='RowID', how='left')   
    InteriorFlooring['wood_fl'] = np.where(InteriorFlooring['InteriorFlooringTypeStndCode'].isin(['WD']), 1, np.nan)
    Main = Main.merge(InteriorFlooring[['RowID', 'wood_fl']].drop_duplicates('RowID'), on='RowID', how='left')       
    del InteriorFlooring
    
    # Upload the spreadsheet of exterior wall
    ExteriorWall = read_ZAsmt(state, 'ExteriorWall', [0,1,2], 'RowID', parcels)
    ExteriorWall = ExteriorWall.drop_duplicates('RowID')
    ExteriorWall['extwall'] = np.where(ExteriorWall['ExteriorWallStndCode'].isin(['BL', 'CB', 'CC']), 'block', 
     np.where(ExteriorWall['ExteriorWallStndCode'].isin(['BR', 'BV', 'MY', 'RK']), 'brick',
              np.where(ExteriorWall['ExteriorWallStndCode'].isin(['WD', 'WG', 'WS']), 'wood', 
                       np.where(ExteriorWall['ExteriorWallStndCode'].isin(['ST']), 'stucco', 
                                np.where(ExteriorWall['ExteriorWallStndCode'].isin(['SD']), 'siding', 
              'other')))))
    Main = Main.merge(ExteriorWall[['RowID', 'extwall']], on='RowID', how='left')
    Main.loc[Main['extwall'].isnull(), 'extwall'] = 'none'
    del ExteriorWall
    
    # Upload the spreadsheet of garages. Use the number of cars per garage.
    Garage = read_ZAsmt(state, 'Garage', [0,1,2,3,4,5], 'RowID', parcels)
    Garage_sqft = Garage[Garage['GarageAreaSqFt'].notnull()].drop_duplicates('RowID')[['RowID', 'GarageAreaSqFt']]
    Main = Main.merge(Garage_sqft, on='RowID', how='left')
    Garage_cars = Garage[Garage['GarageNoOfCars'].notnull()].drop_duplicates('RowID')[['RowID', 'GarageNoOfCars']]
    Main = Main.merge(Garage_cars, on='RowID', how='left')
    del Garage
    del Garage_sqft
    del Garage_cars
    
    # Upload the spreadsheet of "Extra Features". The only type of feature frequently reported for this subsample is a wood deck.
    ExtraFeature = read_ZAsmt(state, 'ExtraFeature', [0,1,2,3], 'RowID', parcels)
    ExtraFeature['deck'] = np.where(ExtraFeature['ExtraFeaturesStndCode'].isin(['DCK', 'DKS', 'WDD']), 1, np.nan)
    Main = Main.merge(ExtraFeature[['RowID', 'deck']].drop_duplicates('RowID'), on='RowID', how='left')
    ExtraFeature['fence'] = np.where(ExtraFeature['ExtraFeaturesStndCode'].str[:2]=='FN', 1, np.nan)
    Main = Main.merge(ExtraFeature[['RowID', 'fence']].drop_duplicates('RowID'), on='RowID', how='left')    
    del ExtraFeature
    
    # Upload the Pool spreadsheet.
    Pool = read_ZAsmt(state, 'Pool', [0,1,2,3], 'RowID', parcels)
    Pool['pool'] = np.where(Pool['PoolStndCode'].isin(['POL', 'SHP']), 1, 0)
    Pool = Pool.drop_duplicates('RowID')[['RowID', 'pool']]
    Main = Main.merge(Pool, on='RowID', how='left')
    del Pool
    
    # Load list of outbuildings
    Oby = read_ZAsmt(state, 'Oby', [0,1,2,3,4], 'RowID', parcels)
    Oby['oby_sqft'] = Oby['OBYAreaSqFt'].astype(float)
    Oby['oby_sqft'] = Oby.groupby(['RowID'])['oby_sqft'].transform(sum)
    Oby = Oby.drop_duplicates('RowID')[['RowID', 'oby_sqft']]
    Main = Main.merge(Oby, on='RowID', how='left')
    del Oby
    
    # Merge to the transaction data
    Main = Main.merge(Main_ZTrans, on='ImportParcelID', how='right')
    
    # Drop parcels with bad quality or missing geocodes
  #  Main = Main[Main['PropertyAddressLongitude'].notnull()]
  #  Main = Main[Main['PropertyAddressLatitude'].notnull()] 
  #  Main = Main[Main['PropertyAddressGeoCodeMatchCode']=="Y"] 
    
    # Count number of parcels geocoded to the same location, to determine whether parcels are single family
   # Main['location_count'] = Main.groupby(['PropertyAddressLatitude', 'PropertyAddressLongitude'])['RowID'].transform(pd.Series.count)
    # Keep single-family houses built after 1960
    Main = Main[Main['YearBuilt']>=1960]
    Main = Main[Main['PropertyLandUseStndCode']=='RR101']
  #  Main = Main[Main['location_count']==1]
 
    # Designate Census tract, for fixed effects. Add a count of parcels per county, for weighting.
    Main['tract'] = Main['PropertyAddressCensusTractAndBlock'].astype(str).str[:9]
    Main = Main[Main['tract'].notnull()]
    Main['FIPS_count'] = Main.groupby('FIPS')['FIPS'].transform(pd.Series.count)
   
    # Convert NaN to 0 for some variables, assuming that a missing value means the house doesn't have that feature
    Main.loc[Main['GarageAreaSqFt'].isnull(), 'GarageAreaSqFt'] = 0
    Main.loc[Main['GarageNoOfCars'].isnull(), 'GarageNoOfCars'] = 0
    Main.loc[Main['pool'].isnull(), 'pool'] = 0
    Main.loc[Main['deck'].isnull(), 'deck'] = 0
    Main.loc[Main['golf'].isnull(), 'golf'] = 0
    Main.loc[Main['waterfrnt'].isnull(), 'waterfrnt'] = 0  
    Main.loc[Main['carpet_fl'].isnull(), 'carpet_fl'] = 0
    Main.loc[Main['wood_fl'].isnull(), 'wood_fl'] = 0  
    Main.loc[Main['fence'].isnull(), 'fence'] = 0  
    Main.loc[Main['oby_sqft'].isnull(), 'oby_sqft'] = 0  # Set missing to zero
    
    # Drop parcels missing the number of bedrooms
    Main = Main[Main['bdrms'].notnull()]   
    
    # Create variables for MSA (by merging FIPS county to an outside list)
    FIPS2CSA = pd.read_csv(r'G:\Zillow\cbsa2fipsxw2.csv'
                           , usecols=['cbsacode', 'cbsatitle', 'fipsstatecode', 'fipscountycode']
                           , dtype={'cbsacode': str, 'cbsatitle': str, 'fipsstatecode': str, 'fipscountycode': str})
    FIPS2CSA['FIPS'] = FIPS2CSA['fipsstatecode'] + FIPS2CSA['fipscountycode']
    Main = Main.merge(FIPS2CSA, on='FIPS', how='left')    
    
    # Keep relevant variables
    Main = Main[['RowID'
                 , 'PropertyFullStreetAddress'
                 , 'PropertyZip'
                 , 'LotSizeSquareFeet'
                 , 'NoOfBuildings'
                 , 'NoOfUnits'
                 , 'YearBuilt'
                 , 'LegalSubdivisionName'
                 , 'FIPS'
                 , 'PropertyLandUseStndCode'
                 , 'ImportParcelID'
                 , 'pud'
                 , 'condo'
                 , 'mortgage'
                 , 'HeatingTypeorSystemStndCode'
                 , 'AirConditioningTypeorSystemStndCode'
                 , 'fireplace'
                 , 'ownerocc'
                 , 'buildquality'
                 , 'bdrms'
                 , 'baths'
                 , 'BuildingAreaSqFt'
                 , 'GarageAreaSqFt'
                 , 'GarageNoOfCars'
                 , 'deck'
                 , 'pool'
                 , 'oby_sqft'
                 , 'PropertyAddressLatitude'
                 , 'PropertyAddressLongitude'
                 , 'tract'
                 , 'cbsacode'
                 , 'cbsatitle'
                 , 'tax_rate'
                 , 'LotSiteTopographyStndCode'
                 , 'totrms'
                 , 'tile_rf'
                 , 'golf'
                 , 'waterfrnt'
                 , 'carpet_fl'
                 , 'wood_fl'
                 , 'extwall'
                 , 'fence'
                 ]]
    # Export to file
    feather.write_dataframe(Main, r'G:\Zillow\Created\evermort_parcels_{}.feather'.format(state))   
    #Main = feather.read_dataframe(r'G:\Zillow\Created\evermort_parcels.feather')
    
    
    ####################################################
    parcels = feather.read_dataframe(r'G:\Zillow\Created\evermort_parcels_{}.feather'.format(state))
    parcels = parcels[['ImportParcelID'
                       , 'RowID'
                       , 'cbsacode'
                       , 'cbsatitle'
                       , 'FIPS'
                       , 'BuildingAreaSqFt'
                       , 'GarageAreaSqFt'
                       , 'oby_sqft'
                       , 'LotSizeSquareFeet'
                       , 'YearBuilt'
                       , 'pud'
                       , 'condo'
                       , 'ownerocc'
                       , 'fireplace'
                       , 'pool'
                       , 'deck'
                       , 'bdrms'
                       , 'baths'
                       , 'tract'
                       , 'PropertyAddressLatitude'
                       , 'PropertyAddressLongitude'
                       , 'tax_rate'
                       , 'LotSiteTopographyStndCode'
                       , 'totrms'
                       , 'tile_rf'
                       , 'golf'
                       , 'waterfrnt'
                       , 'carpet_fl'
                       , 'wood_fl'
                       , 'extwall'
                       , 'fence']]
    parcels_ref = parcels['ImportParcelID'].astype(str).drop_duplicates().tolist()

    # Load transactions involving those parcels
    PropertyInfo = read_ZTrans(state, 'PropertyInfo', [0,64], 'ImportParcelID', parcels_ref)   
    transactions_ref = PropertyInfo['TransId'].drop_duplicates().tolist()  
    Main_ZTrans = read_ZTrans(state, 'Main', [0,4,6,16,17,24,25,30,33,34,89,90], 'TransId', transactions_ref)
     
    # Merge together
    trans = PropertyInfo.merge(Main_ZTrans, on='TransId', how='inner')
    trans = trans.merge(parcels, on='ImportParcelID', how='inner')
   
    #Trim the sample
        # Keep transactions with prices in reasonable range
    trans = trans[trans['SalesPriceAmount'].between(1000, 5000000)]    
        # Drop sales prices that transfer only a partial interest or other nonsense
    trans = trans[~trans['SalesPriceAmountStndCode'].isin(['CU', 'CM', 'CN', 'CP', 'CU', 'DL', 'EP', 'ST'])]
        # Drop sales between family member (non "arm's length" transactions)
    trans = trans[~trans['IntraFamilyTransferFlag'].notnull()]    
        # Transform RecordingDate to RecordingYear
    trans['RecordingYear'] = trans['RecordingDate'].str[:4].astype(float)
        # Keep D:Deed and H:Deed with concurrent mortgage (excludes F:Foreclosure and M:Mortgage)
    trans = trans[trans['DataClassStndCode'].isin(['D', 'H'])] 
    
    # Do additional transformations on the data
        # Drop houses with more than 2 acres of land
    trans = trans[trans['LotSizeSquareFeet']<=87120] 
        # Drop exceptionally big houses
    trans = trans[trans['BuildingAreaSqFt'].between(1,15000)]
        # Count the number of recorded sales per parcel
    trans['sales_count'] = trans.groupby('ImportParcelID')['ImportParcelID'].transform(pd.Series.count)
        # Combine the PUD and condo indicators into a single HOA indicator
    trans['hoa'] = np.where(trans['pud'] + trans['condo']>0, 1, 0)
        # Compute age at sale, based on year built. Exclude parcel sales that occured before the current building was built.
    trans['ageAtSale'] = trans['RecordingYear'] - trans['YearBuilt'].astype(float)
    trans.loc[trans['ageAtSale']<0, 'ageAtSale'] = np.nan 
        # In cases where DocumentDate is missing, substitute Recording Date. Document date is generally better, but recording date is always available.
    trans.loc[trans['DocumentDate'].isnull(), 'DocumentDate'] = trans['RecordingDate']
    import datetime
    trans['DocumentDate'] = pd.to_datetime(trans['DocumentDate']) - datetime.date(1960, 1, 1)
    trans['DocumentDate'] = trans['DocumentDate'].astype('timedelta64[D]')

    # Calculate log transformations for the regressions
    trans['lprice'] =  np.log(trans['SalesPriceAmount'])
    trans['lba'] =  np.log(trans['BuildingAreaSqFt'] + 1)
    trans['llota'] =  np.log(trans['LotSizeSquareFeet'] + 1)
    trans['lgara'] =  np.log(trans['GarageAreaSqFt'] + 1)
    trans['loba'] = np.log(trans['oby_sqft'] + 1)
    
    # Create fewer factors
    trans['deed_type'] = np.where(trans['DocumentTypeStndCode'].isin(['WRDE', 'SPWD', 'CPDE']), 'warranty', 
         np.where(trans['DocumentTypeStndCode'].isin(['TRFC', 'BSDE', 'SHDE', 'FCDE', 'LDCR', 'DELU', 'COCA', 'TXDE', 'JGFC']), 'foreclosure', 
                  'other'))
    trans['topography'] = np.where(trans['LotSiteTopographyStndCode'].isin(['MT', 'SW', 'BR', 'MR', 'RK']), 'other',
         trans['LotSiteTopographyStndCode'])
    trans['totrms'] = np.where(trans['totrms']>=10, 10, trans['totrms'])    
    trans['bdrms'] = np.where(trans['bdrms']>=6, 6, trans['bdrms']) 
    trans['baths'] = np.where(trans['baths']>=5, 5, trans['baths']) 
    

    trans.drop(inplace=True, axis=1, labels=['ImportParcelID'
                                             , 'YearBuilt'
                                             , 'RecordingDate'
                                             , 'RecordingYear'
                                             , 'SalesPriceAmount'
                                             , 'SalesPriceAmountStndCode'
                                             , 'IntraFamilyTransferFlag'
                                             , 'AssessmentLandUseStndCode'
                                             , 'OccupancyStatusStndCode'
                                             , 'CondominiumRiderFlag'
                                             , 'PlannedUnitDevelopmentRiderFlag'
                                             , 'LotSizeSquareFeet'
                                             , 'BuildingAreaSqFt'
                                             , 'GarageAreaSqFt'
                                             , 'oby_sqft'
                                             , 'sales_count'
                                             , 'pud'
                                             , 'condo'
                                             , 'DocumentTypeStndCode'
                                             , 'LotSiteTopographyStndCode'])    

    # Format columns to prepare for regressions
    # Format as numeric
    numeric = ['lprice'
               , 'DocumentDate'
               , 'llota'
               , 'lba'
               , 'lgara'
               , 'loba'
               , 'ageAtSale'
               , 'PropertyAddressLatitude'
               , 'PropertyAddressLongitude'
               , 'tax_rate']
    trans[numeric] = trans[numeric].astype(float)   
    # Format as factor variables
    factor = ['hoa'
              , 'DataClassStndCode'
              , 'deed_type'
              , 'ownerocc'
              , 'fireplace'
              , 'pool'
              , 'deck'
              , 'bdrms'
              , 'baths'
              , 'tract'
              , 'topography'
              , 'totrms'
              , 'tile_rf'
              , 'golf'
              , 'waterfrnt'
              , 'carpet_fl'
              , 'wood_fl'
              , 'extwall'
              , 'fence']
    for col in factor:
        trans[col] = trans[col].astype('category')
    # Drop any row where one of these variables is null (rather than imputing with MICE)        
    nonnull = ['FIPS'
               , 'lprice'
               , 'hoa'
               , 'DocumentDate'
               , 'DataClassStndCode'
               , 'deed_type'
               , 'tract'
               , 'PropertyAddressLongitude'
               , 'PropertyAddressLatitude']
    trans = trans.dropna(subset=nonnull)               
    
    feather.write_dataframe(trans, r'G:\Zillow\Created\transactions_{}.feather'.format(state))
    
    ####################################################
    
    
    
         
    return


# Run the process above in parallel
from multiprocessing import Pool
state_codes = ['01', '02', '04', '05', '06', '08', '09', '10', '11', '12', '13', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '40', '41', '42', '44', '45', '46', '47', '48', '49', '51', '53', '54', '55', '56']
if __name__ == '__main__':
    Pool(8).map(parcel_list, state_codes)


# Compile a national file and merge to measure of HOA status within cluster
'''
Main = feather.read_dataframe(r'G:\Zillow\Created\evermort_parcels_30.feather').head(0)
for state in state_codes:  
    temp = feather.read_dataframe(r'G:\Zillow\Created\evermort_parcels_{}.feather'.format(state))  
    Main = Main.append(temp)
cluster = feather.read_dataframe(r'G:\Zillow\Created\clusters.feather')
Main = Main.merge(cluster, on='RowID', how='left')
feather.write_dataframe(Main, r'G:\Zillow\Created\evermort_parcels.feather')
'''


