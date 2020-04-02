# -*- coding: utf-8 -*-
"""
Created on Tue Mar 20 11:20:23 2018

@author: wyatt
"""

import pandas as pd
import numpy as np
import feather
import matplotlib.pyplot as plt

# Assemble data
# Load national file of all single-family parcels that have ever transacted
Main = feather.read_dataframe(r'G:\Zillow\Created\all_SF_parcels\all_SF_parcels.feather')
Main = Main.drop(['LegalSubdivisionName', 
                  'PropertyAddressGeoCodeMatchCode', 
                  'PropertyAddressLatitude', 
                  'PropertyAddressLongitude', 
                  'PropertyLandUseStndCode'], axis=1)
# Merge to cluster assignments
cluster = feather.read_dataframe(r'G:\Zillow\Created\clusters.feather')
Main = Main.merge(cluster, on='RowID', how='left')
del cluster
Main.head().info()
# Merge in postal abbreviations for each state
state_abrevs = pd.read_csv(r'C:\Users\wyatt\Research\state_abrevs.csv', nrows=52) 
state_abrevs['state'] = state_abrevs['state'].astype(str).apply(lambda x: x.zfill(2))
Main = Main.merge(state_abrevs, on='state', how='left')
# Merge in MSA (by merging county to an outside list)
FIPS2CSA = pd.read_csv(r'G:\Zillow\cbsa2fipsxw2.csv'
                       , usecols=['cbsacode', 'cbsatitle', 'fipsstatecode', 'fipscountycode']
                       , dtype={'cbsacode': str, 'cbsatitle': str, 'fipsstatecode': str, 'fipscountycode': str})
FIPS2CSA['county'] = FIPS2CSA['fipsstatecode'] + FIPS2CSA['fipscountycode']
Main = Main.merge(FIPS2CSA[['cbsacode', 'county']], on='county', how='left')   
# Merge in Census divisions
divisions = pd.read_excel(r'G:\Zillow\Created\division_state_xwalk.xlsx')
divisions['state'] = divisions['state_code'].str[1:]
Main = Main.merge(divisions[['state', 'division_code']], on='state', how='left')

# HOA EXTENT
###############################################################################
###############################################################################
# Time trend
df = Main[['YearBuilt', 'hoa']].dropna()
df['Single Family Homes'] = df.groupby('YearBuilt')['hoa'].transform(pd.Series.mean)
df = df[df['YearBuilt'].between(1940, 2015)]
df = df.drop_duplicates(['YearBuilt', 'Single Family Homes'])

df_cluster = Main[['YearBuilt', 'hoa_neigh', 'YearBuilt_mode']].dropna()
df_cluster = df_cluster[df_cluster['hoa_neigh'].isin([0,1])]
df_cluster['mode_dist'] = df_cluster['YearBuilt'] - df_cluster['YearBuilt_mode']
df_cluster = df_cluster[df_cluster['mode_dist'].between(-5,5)]
df_cluster['Single Family Homes Built in a New Subdivision'] = df_cluster.groupby('YearBuilt')['hoa_neigh'].transform(pd.Series.mean)
df_cluster = df_cluster[df_cluster['YearBuilt'].between(1940, 2015)]
df_cluster = df_cluster.drop_duplicates(['YearBuilt', 'Single Family Homes Built in a New Subdivision'])


'''df_cluster = Main[['YearBuilt', 'hoa_neigh']].dropna()
df_cluster = df_cluster[df_cluster['hoa_cluster'].isin([0,1])]
df_cluster['Single Family Homes Built in a New Subdivision'] = df_cluster.groupby('YearBuilt')['hoa_cluster'].transform(pd.Series.mean)
df_cluster = df_cluster[df_cluster['YearBuilt'].between(1940, 2015)]
df_cluster = df_cluster.drop_duplicates(['YearBuilt', 'Single Family Homes Built in a New Subdivision'])'''

df = df.merge(df_cluster, on='YearBuilt', how='inner')
df = df.sort_values(by='YearBuilt')

ax = plt.subplot(111)
plt.plot(df['YearBuilt'], df['Single Family Homes'])
plt.plot(df['YearBuilt'], df['Single Family Homes Built in a New Subdivision'])
plt.legend()
plt.savefig(r'G:\Zillow\Created\Figures\hoa_pct_yr.pdf')


###############################################################################
# By county, MSA and Census division
    # MSA
df = Main[['hoa', 'cbsacode']].dropna()
df['hoa_pct'] = df.groupby('cbsacode')['hoa'].transform(pd.Series.mean)
df = df.drop_duplicates('cbsacode')

df1 = Main[['hoa', 'cbsacode', 'YearBuilt']].dropna()
df1 = df1[df1['YearBuilt'].between(2000, 2015)]
df1['hoa_pct_new'] = df1.groupby('cbsacode')['hoa'].transform(pd.Series.mean)
df1 = df1.drop_duplicates('cbsacode')
df = df[['cbsacode', 'hoa_pct']].merge(df1[['cbsacode', 'hoa_pct_new']], on='cbsacode', how='left')
df.to_csv(r'G:\Zillow\Created\Figures\hoa_pct_msa.csv')

    # County
df = Main[['hoa', 'county']].dropna()
df['hoa_pct'] = df.groupby('county')['hoa'].transform(pd.Series.mean)
df = df.drop_duplicates('county')

df1 = Main[['hoa_neigh', 'county', 'YearBuilt', 'YearBuilt_mode']].dropna()
df1 = df1[df1['YearBuilt'].between(2000, 2015)]
df1 = df1[df1['hoa_neigh'].isin([0,1])]
df1['mode_dist'] = df1['YearBuilt'] - df1['YearBuilt_mode']
df1 = df1[df1['mode_dist'].between(-5,5)]
df1['hoa_pct_new'] = df1.groupby('county')['hoa_neigh'].transform(pd.Series.mean)
df1 = df1.drop_duplicates('county')
df = df[['county', 'hoa_pct']].merge(df1[['county', 'hoa_pct_new']], on='county', how='left')

df['GISJOIN'] = "G" + df['county'].str[:2] + "0" + df['county'].str[2:] + "0"
df.to_csv(r'G:\Zillow\Created\Figures\hoa_pct_county.csv')

    # Census division
df = Main[['hoa', 'division_code']].dropna()
df['hoa_pct'] = df.groupby('division_code')['hoa'].transform(pd.Series.mean)
df = df.drop_duplicates('division_code')

df1 = Main[['hoa_neigh', 'division_code', 'YearBuilt', 'YearBuilt_mode']].dropna()
df1 = df1[df1['YearBuilt'].between(2000, 2015)]
df1 = df1[df1['hoa_neigh'].isin([0,1])]
df1['mode_dist'] = df1['YearBuilt'] - df1['YearBuilt_mode']
df1 = df1[df1['mode_dist'].between(-5,5)]
df1['hoa_pct_new'] = df1.groupby('division_code')['hoa_neigh'].transform(pd.Series.mean)
df1 = df1.drop_duplicates('division_code')
df = df[['division_code', 'hoa_pct']].merge(df1[['division_code', 'hoa_pct_new']], on='division_code', how='left')

df['hoa_pct'] = df['hoa_pct'].round(2)*100
df['hoa_pct_new'] = df['hoa_pct_new'].round(2)*100
df.to_csv(r'G:\Zillow\Created\Figures\hoa_pct_division.csv')

# TIED TO CENSUS CHARACTERISTICS
###############################################################################
###############################################################################

# Create summary measures by geoid
Main['geoid'] = Main['PropertyAddressCensusTractAndBlock'].astype(str).str[:9] + Main['PropertyAddressCensusTractAndBlock'].astype(str).str[10:13]
Main['records_n'] = Main.groupby(['geoid'])['RowID'].transform(pd.Series.count)
Main['hoa_geoid'] = Main.groupby(['geoid'])['hoa'].transform(pd.Series.mean)

chars = Main[['geoid', 'hoa_geoid', 'records_n']].dropna().drop_duplicates()
chars = chars[chars['records_n']>=30]

# Merge to Census data
    # Load data
census_chars = pd.read_csv(r'C:\Users\wyatt\Research\Zillow\IPUMS_blockgrp_07012017.csv')
census_chars = census_chars[census_chars['total_pop']>0]
    # Reformat to allow a merge
census_chars['st'] = census_chars['GISJOIN'].str[1:3]
census_chars['co'] = census_chars['GISJOIN'].str[4:7]
census_chars['tract'] = census_chars['GISJOIN'].str[8:12]
census_chars['blkgrp'] = census_chars['GISJOIN'].str[12:15]
census_chars['geoid'] = census_chars['st'] + census_chars['co'] + census_chars['tract'] + census_chars['blkgrp']
census_chars = census_chars.drop(['st', 'co', 'tract', 'blkgrp', 'GISJOIN'], axis=1)
    # Calculate race as a percentage of total population
colors = ['white', 'black', 'asian', 'hispanic', 'other_race']
for color in colors:
    census_chars['{}_geoid'.format(color)] = census_chars['{}'.format(color)] / census_chars['total_pop']
census_chars.info()
    # Merge
chars = chars.merge(census_chars, on='geoid', how='inner')

# Assign weight for hoa and non-hoa characteristics
chars['geoid_hoa_wt'] = chars['total_pop'] * chars['hoa_geoid']
chars['geoid_nonhoa_wt'] = chars['total_pop'] * (1-chars['hoa_geoid'])

# Race
colors_geoid = ['white_geoid', 'black_geoid', 'asian_geoid', 'hispanic_geoid', 'other_race_geoid']
race_hoa = np.average(chars[colors_geoid], axis=0, weights=chars['geoid_hoa_wt'])
race_nonhoa = np.average(chars[colors_geoid], axis=0, weights=chars['geoid_nonhoa_wt'])

# Median income
foo = chars[chars['med_hs_income'].notnull()]
income_hoa = np.average(foo[['med_hs_income']], axis=0, weights=foo['geoid_hoa_wt'])
income_nonhoa = np.average(foo[['med_hs_income']], axis=0, weights=foo['geoid_nonhoa_wt'])

# Racial isolation
isol = pd.DataFrame(columns=colors)
for color in colors:
    chars['{}_hoa_wt'.format(color)]    = chars['{}'.format(color)] *    chars['hoa_geoid']
    chars['{}_nonhoa_wt'.format(color)] = chars['{}'.format(color)] * (1-chars['hoa_geoid'])
    
    isol_hoa    = np.average(chars[colors_geoid], axis=0, weights=chars['{}_hoa_wt'.format(color)])
    isol_nonhoa = np.average(chars[colors_geoid], axis=0, weights=chars['{}_nonhoa_wt'.format(color)])
    
    df = pd.DataFrame([isol_hoa, isol_nonhoa], columns=colors, index=['{}_hoa'.format(color), '{}_nonhoa'.format(color)])
    
    #df_hoa = pd.DataFrame(isol_hoa, columns=['{}'.format(color)])
    #df_nonhoa = pd.DataFrame(isol_nonhoa, columns=['{}'.format(color)])
    
    isol = isol.append(df)
isol.to_csv(r'G:\Zillow\Created\Figures\isolation_index.csv')
    
# PROPERTY CHARACTERISTICS
###############################################################################
###############################################################################
# Load transactions used for regressions
trans = feather.read_dataframe(r'G:\Zillow\Created\transactions.feather')
    #Undo the log transformation of these variables (but don't bother to change the names)
trans[['lprice', 'llota', 'lba', 'lgara', 'loba']] = np.exp(trans[['lprice', 'llota', 'lba', 'lgara', 'loba']])
    # Drop duplicate transactions. I'm only using permanent property characteristics
trans = trans.drop_duplicates('RowID')
    # Merge to Main
Main = Main.merge(trans, on='RowID', how='left')
    # Manually create dummies for deed type
Main['warrantyDeed'] = np.where(Main['deed_type']=='warranty', 1, 0) 
Main['foreclosureDeed'] = np.where(Main['deed_type']=='foreclosure', 1, 0) 
Main['otherDeed'] = np.where(Main['deed_type']=='other', 1, 0) 
    # These variables are treated as dummies in the regression and missing values have been imputed as 0. So drop those observations for descriptive statistics.
Main.loc[Main['bdrms']==0, 'bdrms'] = np.nan
Main.loc[Main['baths']==0, 'baths'] = np.nan
Main.loc[Main['totrms']==0, 'totrms'] = np.nan
Main.loc[Main['llota']==0, 'llota'] = np.nan
    # Some giant outbuildings are screwing things up
Main.loc[Main['loba']>=20000, 'loba'] = np.nan
    # List of variables for which to get HOA-group means        
varlist=['lprice',         
   'DocumentDate',    
   'ageAtSale',
   'lba', 
   'llota', 
   'lgara', 
   'loba', 
   'tax_rate',  
   'ownerocc',  
   'fireplace',  
   'pool',  
   'deck',                         
   'bdrms', 
   'baths', 
   'totrms', 
   'tile_rf', 
   'golf', 
   'waterfrnt', 
   'carpet_fl', 
   'wood_fl',
   'fence',
   'warrantyDeed',
   'foreclosureDeed',
   'otherDeed']   

    # Criteria for whether observations would appear in the regressions
Main['reg_HOA'] = np.where(((Main['YearBuilt']>=1960) & (Main['DocumentDate']>=16425) & (Main['DataClassStndCode']=='H')), 1, 0)
Main['reg_HOA_neigh'] = np.where(((Main['reg_HOA']==1) & (Main['hoa_neigh_x'].isin([0,1]))), 1, 0)
    # Get averages for different groups, append them all into one dataframe, and export to file. Use Excel to arrange them as a LaTeX table.
col1= Main[varlist].groupby(Main['hoa_x']).mean()
col2= Main[varlist].groupby(Main['hoa_neigh_x']).mean()
col3= Main[varlist][Main['reg_HOA']==1].groupby(Main['hoa_x']).mean()
col4= Main[varlist][Main['reg_HOA']==1].groupby(Main['hoa_neigh_x']).mean()
export = col1.append(col2).append(col3).append(col4)
export.to_csv(r'G:\Zillow\Created\property_char_summary_stats.csv')

# Show where parcels are progressively lost by restricting to those built since 1960, transacted since 2005, and being accompanied by a mortgage
# No file is outputted. Just enter the numbers manually into a table.
    # All parcels and those that make the regression
pd.crosstab(Main['hoa_x'], Main['reg_HOA'])
pd.crosstab(Main['hoa_neigh_x'], Main['reg_HOA'])
    # Parcels built post-1960
Main['reg_HOA1'] = np.where(Main['YearBuilt']>=1960, 1, 0)
Main['hoa_x'][Main['reg_HOA1']==1].value_counts()
Main['hoa_neigh_x'][Main['reg_HOA1']==1].value_counts()
    # Parcels built post-1960 and transacted since 2005
Main['reg_HOA2'] = np.where(((Main['YearBuilt']>=1960) & (Main['DocumentDate']>=16425)), 1, 0)
Main['hoa_x'][Main['reg_HOA2']==1].value_counts()
Main['hoa_neigh_x'][Main['reg_HOA2']==1].value_counts()



# Get descriptive statistics for transactions
    # Reload transactions since duplicates were dropped by parcel before
trans = feather.read_dataframe(r'G:\Zillow\Created\transactions.feather')
trans = trans.merge(Main[['RowID', 'YearBuilt']], on='RowID', how='left')
trans = trans[trans['YearBuilt'].notnull()]
trans['reg_HOA'] = np.where(((trans['DocumentDate']>=16425) & (trans['DataClassStndCode']=='H')), 1, 0)
trans['hoa'][trans['reg_HOA']==1].value_counts()
trans['hoa_neigh'][trans['reg_HOA']==1].value_counts()

trans['reg'] = np.where(trans['YearBuilt']>=1960, 1, 0)
trans['post2005'] = np.where(trans['DocumentDate']>=16425, 1, 0)
pd.crosstab(trans['hoa'], trans['post1960'])
pd.crosstab(trans['hoa'], trans['post2005'])
pd.crosstab(trans['hoa'], trans['DataClassStndCode']=='H')


