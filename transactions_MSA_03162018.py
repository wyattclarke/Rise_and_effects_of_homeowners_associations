# -*- coding: utf-8 -*-
"""
Created on Thu Mar 15 18:21:42 2018

@author: wyatt
"""

import feather
import pandas as pd

# Load the national file
Main = feather.read_dataframe(r'G:\Zillow\Created\transactions.feather')

cbsa = Main[['cbsacode', 'cbsatitle']].drop_duplicates()
cbsa.to_csv(r'G:\Zillow\Created\msa_list.csv')


Main = Main.drop(['TransId', 'RowID', 'FIPS', 'cbsatitle','YearBuilt_mode'], axis=1)

Main = Main[Main['DataClassStndCode']=='H']
#Main = Main[Main['DocumentDate']>=16425]

# Create list of MSAs
    # Keep clustered observations. 
    # If I apply the criterion to this subset of the data, I ensure regressions will work based on both HOA-indicators for each MSA.
foo = Main[Main['hoa_neigh'].isin([0,1])]
foo = foo[foo['cbsacode'].notnull()]
    # MSA must have at least 1000 clustered observations
foo['count'] = foo.groupby('cbsacode')['cbsacode'].transform(pd.Series.count)
foo = foo[foo['count']>=1000]
    # At least 5% of them must be in an HOA
foo['count'] = foo.groupby('cbsacode')['hoa_neigh'].transform(pd.Series.mean)
foo = foo[foo['count']>=.05]
msa_list = foo[['cbsacode']]
msa_list = msa_list[msa_list['cbsacode'].notnull()]
msa_list = msa_list['cbsacode'].drop_duplicates().tolist()

#msa_list = ["19300"]

# Loop over each MSA to do the following
for msa in msa_list:
    # Save transactions from each MSA
    temp = Main[Main['cbsacode']==msa]
    temp.loc[temp['baths'].isnull(), 'baths'] = 0
    temp.loc[temp['topography'].isnull(), 'topography'] = 'other'
    temp.loc[temp['hoa_neigh'].isnull(), 'hoa_neigh'] = 10    

    
    # Move to the front variables that are excluded from regressions, so they can be referenced by index
    cols = temp.columns.tolist()
    cols.remove('hoa')
    cols.remove('hoa_neigh')
    cols.remove('tract')
    cols.remove('PropertyAddressLatitude')
    cols.remove('PropertyAddressLongitude')
    cols.remove('lprice')
    cols = ['hoa'
            , 'hoa_neigh'
            , 'tract'
            , 'PropertyAddressLatitude'
            , 'PropertyAddressLongitude'
            , 'lprice'] + cols
    temp = temp.loc[:,cols]      
    # Delete variables that are entirely missing or mono-valued for an MSA (will mess up the regression).
    # Again, use the subset of observations that are in a neighborhood, to ensure both regressions work.
    nunique = temp[temp['hoa_neigh'].isin([0,1])].apply(pd.Series.nunique)
    cols_to_drop = nunique[nunique.isin([0,1])].index
    temp = temp.drop(cols_to_drop, axis=1)
    # Write to file    
    feather.write_dataframe(temp, r'G:\Zillow\Created\MSAs\transactions_{}.feather'.format(msa))
    
   
    #temp = feather.read_dataframe(r'G:\Zillow\Created\MSAs\transactions_imputed_13820.feather')

#msa_list.to_csv(r'G:\Zillow\Created\MSAs\msa_list.csv')
Main.info(null_counts=True)
test = Main.head()
