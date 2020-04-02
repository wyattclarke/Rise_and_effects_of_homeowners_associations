# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import pandas as pd

###############################################################################
# Load Redfin listings
rf = pd.read_csv(r'C:\Users\wyatt.clarke\Documents\Research\HOAs\Redfin\csv_data\Downloads\_all_properties.csv', engine='python', usecols=['ZIP', 'HOA/MONTH'])
    # Clean up ZIP codes
rf['ZIP'] = rf['ZIP'].astype(str)
rf['ZIP'] = rf['ZIP'].str.split('-').str[0]
rf['ZIP'] = rf['ZIP'].str.split('.').str[0]
rf['ZIP'] = rf['ZIP'].apply(lambda x: x.zfill(5))
    # Drop listings with no HOA fee or a $0 HOA fee
rf = rf[rf['HOA/MONTH']>0]
rf = rf[rf['HOA/MONTH'].notnull()]

###############################################################################
# Load the crosswalk between ZIP codes and county FIPS codes. Merge to Redfin listings.
xwalk = pd.read_csv(r'C:\Users\wyatt.clarke\Documents\Research\HOAs\Zillow\GIS\zipcode_county_crosswalk.csv', usecols=['ZCTA5', 'GEOID'], engine='python')
xwalk = xwalk.astype(str)
xwalk['ZCTA5'] = xwalk['ZCTA5'].apply(lambda x: x.zfill(5))
xwalk['GEOID'] = xwalk['GEOID'].apply(lambda x: x.zfill(5))
xwalk['GISJOIN'] = "G" + xwalk['GEOID'].str[:2] + "0" + xwalk['GEOID'].str[2:] + "0"
xwalk = xwalk.drop_duplicates('ZCTA5')
rf = rf.merge(xwalk, left_on='ZIP', right_on='ZCTA5', how='inner')

###############################################################################
# Load the crosswalk between state codes and Census divisions. Merge to Redfin listings.
xwalk2 = pd.read_excel(r'C:\Users\wyatt.clarke\Documents\Research\HOAs\Zillow\GIS\division_state_xwalk.xlsx')
rf['state'] = "G" + rf['GEOID'].str[:2]
rf = rf.merge(xwalk2, left_on='state', right_on='state_code', how='inner')

# Calculate county and division median HOA fee. 
rf['co_median'] = rf.groupby('GEOID')['HOA/MONTH'].transform(pd.Series.median)
rf['division_median'] = rf.groupby('division_code')['HOA/MONTH'].transform(pd.Series.median)
    # Drop counties with less than 10 observations.
rf['co_count'] = rf.groupby('GEOID')['HOA/MONTH'].transform(pd.Series.count)
rf = rf[rf['co_count']>=10]
    # Export to file
county_median = rf[['GISJOIN', 'co_median']].drop_duplicates('GISJOIN')
county_median.to_csv(r'C:\Users\wyatt.clarke\Documents\Research\HOAs\Redfin\county_median_HOA_fees.csv', index=False)
division_median = rf[['division_code', 'division_median']].drop_duplicates('division_code')
division_median.to_csv(r'C:\Users\wyatt.clarke\Documents\Research\HOAs\Redfin\division_median_HOA_fees.csv', index=False)