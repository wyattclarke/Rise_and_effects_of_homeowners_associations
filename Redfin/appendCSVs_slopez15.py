# -*- coding: utf-8 -*-
"""
Created on Mon Jun  5 22:37:18 2017

@author: wyatt.clarke
"""

import os
import glob

os.chdir(r'C:\Users\wyatt.clarke\Documents\Research\HOAs\Redfin\csv_data\Downloads')

interesting_files = glob.glob(os.getcwd() + "/*.csv")

header_saved = False
with open('_all_properties.csv','w') as fout:
    for filename in interesting_files:
        with open(filename) as fin:
            header = next(fin)
            if not header_saved:
                fout.write(header)
                header_saved = True
            for line in fin:
                fout.write(line)
                
import pandas as pd
df = pd.read_csv('_all_properties.csv')
                
df['HOA_YN'] = df['HOA/MONTH'].notnull()
df.to_csv('_all_properties.csv', index=False)

df[['YEAR BUILT', 'PROPERTY TYPE', 'HOA/MONTH', 'HOA_YN', 'LATITUDE', 'LONGITUDE']].to_csv('delete.csv', index=False)
