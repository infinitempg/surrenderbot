import pandas as pd
import numpy as np
from simFootballPBP import *

S = 25

sData = []
idList = getSeasonIDs(S)

print('Season:',S)
print('Games:',len(idList))

print('Gathering PBP...')
for i in idList:
    sData.append(getGameData(S,i))

sDF = pd.concat(sData)
sDF.to_csv('PBP/S%sPBP.csv'%S)

print('PBP for S%s saved!'%S)

print('Combining all Seasons...')
import os
allDF = pd.concat([pd.read_csv('PBP/%s'%p) for p in next(os.walk('PBP'))[2] if '.csv' in p])
allDF = allDF.reset_index().sort_values('S')
allDF.to_csv('allPBP.csv')
print('Done!')