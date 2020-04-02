# -*- coding: utf-8 -*-
"""
Created on Fri Feb 16 18:12:44 2018

@author: wyatt

""" 

###############################################################################
#### GROUP INTO CLUSTERS TO BETTER INFER TRUE HOA STATUS ######################
###############################################################################

# Load functions used to read ZTRAX data files. Might need to open file to adjust file paths or function options.
import feather
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt


# PARCELS
# Load national file of all single-family parcels that have ever transacted
df = feather.read_dataframe(r'G:\Zillow\Created\all_SF_parcels\all_SF_parcels.feather')

# Drop observations that are missing essential information for clustering
df = df[df['PropertyAddressLongitude'].notnull()]
df = df[df['PropertyAddressLatitude'].notnull()]
df = df[df['county'].notnull()]
df = df[df['YearBuilt'].notnull()]
 
'''
# Optionally, take a sample of counties
# 500 counties is about a 20% sample
store = df
sample = df[['county']].drop_duplicates()
sample = sample.sample(500)
df = df.merge(sample, on='county', how='inner')
'''

###############################################################################
# CREATE CLUSTERS
    # Set parameters. Housing built within a n-year span, with a core of at least X houses located within Y meters of eachother
hundredmeters = 0.00089831 # 100 M = 0.00089831 decimal degrees
cluster_mincore = 5 # At least this many houses in the core cluster
clust_dist = hundredmeters * .75 # Houses must be within this many meters of eachother
year_penalty = 0.5 # A year difference in yearbuilt is penalized by this proportion of the clust_dist
df['YearBuilt_distance'] = df['YearBuilt'] * clust_dist * year_penalty # Scales each year to be 75 meters from its neighbor
    # Create empty dataframes to populate later
df['cluster'] = np.nan
df['cluster_count'] = 0
    # The actual clustering part
X = df[['PropertyAddressLongitude', 'PropertyAddressLatitude', 'YearBuilt_distance']].values   
db = DBSCAN(eps=clust_dist, min_samples=cluster_mincore).fit(X)   # Calculates distance in 3D space, where the third dimension is year scaled so that each year is 75 meters from its neighbors 
df['cluster'] = db.labels_ 


###############################################################################
# CALCULATE PERCENT HOA WITHIN CLUSTER
    # Count the observations in each cluster
df['cluster_count'] = df[df['cluster'].notnull()].groupby('cluster')['RowID'].transform(pd.Series.count)    
    # Designate which parcels make for a fair comparison
df['include'] = 1
df.loc[df['cluster']==-1, 'include'] = 0
df.loc[df['cluster_count'].isnull(), 'include'] = 0
df.loc[df['cluster_count']<5, 'include'] = 0
    # Calculate the share of parcels within a cluster for which we have at least one mortgage record that has an HOA rider. 
    # The percentage is applied to ALL parcels in the cluster, including those without a mortgage record.
df.loc[df['include']==0, 'cluster'] = -1
df['cluster_pcthoa'] =df.groupby('cluster')['hoa'].transform(pd.Series.mean)

# SET CUTOFFS FOR WHICH CLUSTERS TO CONSIDER AS HOAS
df.loc[df['cluster']==-1, 'cluster_pcthoa'] = np.nan
df['hoa_cluster'] = np.nan
df.loc[df['cluster_pcthoa'].between(0,.2), 'hoa_cluster'] = 0
df.loc[df['cluster_pcthoa'].between(.2,.6), 'hoa_cluster'] = 9
df.loc[df['cluster_pcthoa'].between(.6,1), 'hoa_cluster'] = 1
df.loc[df['hoa_cluster'].isnull(), 'hoa_cluster'] = 10


###############################################################################
# CALCULATE PERCENT HOA WITHIN SUBDIVISION
    # Assign the subdivision name "drop" for any observation that has no subdivision, no county, or no YearBuilt
df.loc[df['county'].isnull(), 'LegalSubdivisionName'] = 'drop'
df.loc[df['LegalSubdivisionName'].isnull(), 'LegalSubdivisionName'] = 'drop'
    # Assign the subdivision name "drop" for any subdivision of less than 5 houses
df['subdiv_n'] = df.groupby(['county', 'LegalSubdivisionName'])['RowID'].transform(pd.Series.count)
df.loc[df['subdiv_n']<5, 'LegalSubdivisionName'] = 'drop'
    # Calculate the share of parcels within a cluster for which we have at least one mortgage record that have an HOA rider
df['subdiv_pcthoa'] = df.groupby(['county', 'LegalSubdivisionName'])['hoa'].transform(pd.Series.mean)
    # Group cluster members by within-cluster percentage of HOA riders   
df.loc[df['LegalSubdivisionName']=='drop', 'subdiv_pcthoa'] = np.nan
df['hoa_subdiv'] = np.nan
df.loc[df['subdiv_pcthoa'].between(0,.2), 'hoa_subdiv'] = 0
df.loc[df['subdiv_pcthoa'].between(.2,.6), 'hoa_subdiv'] = 9
df.loc[df['subdiv_pcthoa'].between(.6,1), 'hoa_subdiv'] = 1
df.loc[df['hoa_subdiv'].isnull(), 'hoa_subdiv'] = 10

# Calculate modal Year Built in each subdivision
mode = df[['county', 'LegalSubdivisionName', 'YearBuilt']].dropna()
mode['count'] = mode.groupby(['county', 'LegalSubdivisionName', 'YearBuilt'])['county'].transform(pd.Series.count)
mode = mode.sort_values(by=['county', 'LegalSubdivisionName', 'count'], ascending=False)
mode = mode.drop_duplicates(['county', 'LegalSubdivisionName'])
mode = mode.rename(columns={'YearBuilt': 'YearBuilt_mode'})
df = df.merge(mode, on=['county', 'LegalSubdivisionName'], how='left')


###############################################################################
# COMBINE THE CLUSTER AND SUBDIVSION METHODS
# Accept an HOA status assignment from either method as long as they don't contradict
df['hoa_neigh'] = np.where((
                                    ((df['hoa_cluster']==1) & (df['hoa_subdiv']!=0)) |
                                    ((df['hoa_subdiv']==1) & (df['hoa_cluster']!=0))
                                    ), 1, 
                            np.where((
                                    ((df['hoa_cluster']==0) & (df['hoa_subdiv']!=1)) |
                                    ((df['hoa_subdiv']==0) & (df['hoa_cluster']!=1))
                                    ), 0, 9)
                                    )


###############################################################################
'''
# Save histograms to file
ax = df['subdiv_pcthoa'].hist()
vals = ax.get_xticks()
plt.title("Percent of houses with an HOA rider in subdivisions")
ax.set_xticklabels(['{:3.0f}%'.format(x*100) for x in vals])
ax.yaxis.set_visible(False)
plt.grid(False)
fig = ax.get_figure()
fig.savefig(r'G:\Zillow\Created\Figures\subdiv_pcthoa.pdf')

ax = df['cluster_pcthoa'].hist()
vals = ax.get_xticks()
plt.title("Percent of houses with an HOA rider in DBSCAN clusters")
ax.set_xticklabels(['{:3.0f}%'.format(x*100) for x in vals])
ax.yaxis.set_visible(False)
plt.grid(False)
fig = ax.get_figure()
fig.savefig(r'G:\Zillow\Created\Figures\cluster_pcthoa.pdf')

                            
# Generate crosstabs and histograms to compare the different ways of assigning HOA status
    # Show coverage of the two methods
pd.crosstab(df['hoa_subdiv'], df['hoa_cluster'])
    # Show rates of agreement for the two methods
test = df[df['hoa_subdiv'].isin([0,1])]
test = test[test['hoa_cluster'].isin([0,1])]
pd.crosstab(test['hoa_subdiv'], test['hoa_cluster']) #, normalize=True)
    # False positives
df.loc[df['hoa'].isnull(), 'hoa'] = 9
pd.crosstab(df['hoa'], df['hoa_neigh'])


pd.crosstab(df['hoa_subdiv'][df['hoa']==1], df['hoa_cluster'][df['hoa']==1])
pd.crosstab(df['hoa_subdiv'][df['hoa']==0], df['hoa_cluster'][df['hoa']==0])
pd.crosstab(df['hoa_subdiv'][df['hoa'].isnull()], df['hoa_cluster'][df['hoa'].isnull()])

df['hoa'][df['hoa_cluster'].notnull()].value_counts()
'''
# EXPORT RELEVANT COLUMNS TO FILE
feather.write_dataframe(df[['RowID', 'hoa_cluster', 'hoa_subdiv', 'hoa_neigh', 'YearBuilt_mode']], r'G:\Zillow\Created\clusters.feather')
del df


#df = feather.read_dataframe(r'G:\Zillow\Created\clusters.feather')
