# -*- coding: utf-8 -*-
"""
Created on Tue Mar 20 13:24:16 2018

@author: wyatt
"""

###############################################################################
#### LOAD LIST OF ALL SINGLE FAMILY PARCELS ######################
###############################################################################

# Load functions used to read ZTRAX data files. Might need to open file to adjust file paths or function options.
import feather
import pandas as pd
import numpy as np
import os 

os.chdir(r'G:\Zillow')

#Load layout file for ZTrans
layout_ZTrans = pd.read_excel(r'Created\Layout.xlsx', sheetname='ZTrans')
layout_ZAsmt = pd.read_excel(r'Created\Layout.xlsx', sheetname='ZAsmt')


# Function for reading a ZAsmt table with ALL rows and column criterion
def read_ZAsmt_long(state_code, table_name, col_indices):
    path = "G:\\Zillow\\{}\\ZAsmt\\{}.txt".format(state_code, table_name)
    layout_temp = layout_ZAsmt.loc[layout_ZAsmt.TableName=='ut{}'.format(table_name), :].reset_index()
    names=layout_temp['FieldName'][col_indices]
    dtype=layout_temp['PandasDataType'][col_indices].to_dict()
    encoding='ISO-8859-1'
    sep = '|'
    header=None
    quoting=3

    return pd.read_csv(path, quoting=quoting, names=names, dtype=dtype, encoding=encoding, sep=sep, header=header, usecols=col_indices)

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


###############################################################################
# ASSEMBLE ALL SINGLE-FAMILY (RR101) PARCELS -- NOT JUST THOSE THAT HAVE BEEN MORTGAGED -- ALONG WITH HOA STATUS

# Assemble parcels
    # Loop over each state
def all_parcel_list(state):
    # PARCELS
        #  Load list of all parcels from ZAsmt:
    Main_asmt = read_ZAsmt_long(state, "Main", [0,1,49,80,81,82,83])
        # Load building characteristics. Zillow only reports the main structure on each parcel.
    Building_asmt = read_ZAsmt_long(state, "Building", [0,5,14])
        # Merge Main_asmt and Building_asmt
    df = Main_asmt.merge(Building_asmt, on='RowID', how='inner')
        # Restrict to single-family residential parcels
    df = df[df['PropertyLandUseStndCode']=='RR101']  #.str[:2].isin(['RR', 'RI'])] 
    df.drop_duplicates('RowID', inplace=True)
    
     # TRANSACTIONS
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
    Main_ZTrans.loc[Main_ZTrans['pud']>0, 'pud'] = 1 # Set any value above 0 to 1
    Main_ZTrans['condo'] = Main_ZTrans.groupby('ImportParcelID')['condo'].transform(sum)
    Main_ZTrans.loc[Main_ZTrans['condo']>0, 'condo'] = 1
    Main_ZTrans['mortgage'] = Main_ZTrans.groupby('ImportParcelID')['mortgage'].transform(sum)
    # Create a single hoa indicator
    Main_ZTrans['hoa'] = np.where(((Main_ZTrans['pud']==1)|(Main_ZTrans['condo']==1)), 1, 0)
    Main_ZTrans.loc[Main_ZTrans['mortgage']==0, 'hoa'] = np.nan
      
    # Keep list of ever-mortgaged parcels, associated to whether those parcels have ever been mortgaged with an HOA rider
#    Main_ZTrans = Main_ZTrans[Main_ZTrans['mortgage']>0] # Drop transactions from parcels that have never been mortgaged
    Main_ZTrans = Main_ZTrans[['ImportParcelID', 'hoa', 'mortgage']].drop_duplicates() # Keep only these few columns and drop duplicate transactions, reducing the dataframe to a non-duplicated list of parcels that have ever been mortgaged
 
    # Merge 
    df = df.merge(Main_ZTrans, on='ImportParcelID', how='inner')
    df = df.drop('ImportParcelID', axis=1)
    
    # Drop observations from states and counties where HOA status is unobserved
        # Identify county and state from Census block
    df['county'] = df['PropertyAddressCensusTractAndBlock'].str[:5]
    #df['GIS_county'] = "G" + df['county'].str[:2] + "0" + df['county'].str[2:] + "0"
    df['state'] = df['PropertyAddressCensusTractAndBlock'].str[:2]
        # Drop observations where county is not observed
    df = df[df['county'].notnull()]
        # Calculate HOA rates within county and state, and number of transactions per county
    df['county_hoarate'] = df.groupby('county')['hoa'].transform(pd.Series.mean)
    df['state_hoarate'] = df.groupby('state')['hoa'].transform(pd.Series.mean)
    df['county_trans_n'] = df.groupby('county')['hoa'].transform(pd.Series.count)
        # Drop observations from states with no HOAs and from large counties with no HOAs
    df['drop'] = np.where((
            (df['state_hoarate']==0)
            | (
                    (df['county_hoarate']==0)
                     & (df['county_trans_n']>=5000)
            )
            ), 1, 0)
    df = df[df['drop']==0]
    
    # Export relevant columns to file
    df = df.drop(['county_hoarate', 'state_hoarate', 'county_trans_n', 'drop'], axis=1)
    feather.write_dataframe(df, r'G:\Zillow\Created\all_SF_parcels\all_SF_parcels_{}.feather'.format(state))    
    
    
# Run the process above in parallel
from multiprocessing import Pool
state_codes = ['01', '02', '04', '05', '06', '08', '09', '10', '11', '12', '13', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '40', '41', '42', '44', '45', '46', '47', '48', '49', '50', '51', '53', '54', '55', '56']
if __name__ == '__main__':
    Pool(4).map(all_parcel_list, state_codes)
    
'''
# Compile a national file
state_codes = ['01', '02', '04', '05', '06', '08', '09', '10', '11', '12', '13', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '40', '41', '42', '44', '45', '46', '47', '48', '49', '50', '51', '53', '54', '55', '56']
Main = feather.read_dataframe(r'G:\Zillow\Created\all_SF_parcels\all_SF_parcels_30.feather').head(0)
for state in state_codes:  
    temp = feather.read_dataframe(r'G:\Zillow\Created\all_SF_parcels\all_SF_parcels_{}.feather'.format(state))  
    Main = Main.append(temp)
feather.write_dataframe(Main, r'G:\Zillow\Created\all_SF_parcels\all_SF_parcels.feather')
'''


'''
# Export list of counties with coverage
Main = feather.read_dataframe(r'G:\Zillow\Created\all_SF_parcels\all_SF_parcels.feather')
Main.head().info()
export = Main[['county']].drop_duplicates('county')
export['county'] = "G" + export['county'].str[:2] + "0" + export['county'].str[2:] + "0"
'''   