# -*- coding: utf-8 -*-
"""
Created on Sat Jul  1 19:09:36 2017

@author: wyatt.clarke
"""

############ Calculate average Redfin reported HOA fee per block group.

import pandas as pd
import os 

os.chdir(r'C:\Users\wyatt.clarke\Documents\Research\HOAs\Redfin')

# Load
redfin = pd.read_csv('houses_inBlkgrps.csv')

# Keep only houses with an HOA fee
redfin = redfin[redfin['HOA_MONTH'].notnull()]

# Calculate the number of HOA houses per blockgroup and the average fee paid by those houses
redfin['counter'] = 1
redfin['redfinHOA_N'] = redfin.groupby(['GISJOIN'])['counter'].transform(sum)
redfin['HOA_mo_blkgrp_avg'] = redfin.groupby(['GISJOIN'])['HOA_MONTH'].transform(sum) / redfin['redfinHOA_N']

# Keep relevant columns and one record per blockgroup
redfin = redfin[['HOA_mo_blkgrp_avg', 'redfinHOA_N', 'GISJOIN']].drop_duplicates()

# Export to a CSV file
redfin.to_csv(r'HOAfee_avg_inBlkgrp.csv', index=False)