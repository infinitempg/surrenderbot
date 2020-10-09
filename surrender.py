import pandas as pd
import numpy as np
import os
from scipy.stats import percentileofscore as perc
from simFootballPBP import *

'''
Functions
'''

def scoreDiff(row):
    if row['recTeam'] == row['awayTeam']:
        return row['homeScore'] - row['awayScore']
    else:
        return row['awayScore'] - row['homeScore']

def secSinceHalf(row):
    return 1800 - int(row['totTime'])

def fieldPosScore(row):
    if row['dist2goal'] >= 60:
        return 1.0
    elif row['dist2goal'] >= 50:
        return 1.1 ** (40 - row['dist2goal'])
    else:
        return 1.1**10 * 1.2**(50 - row['dist2goal'])

def distScore(row):
    if int(row['distance']) >= 10:
        return 0.2
    elif 7 <= row['distance'] <= 9:
        return 0.4
    elif 4 <= row['distance'] <= 6:
        return 0.6
    elif 2 <= row['distance'] <= 3:
        return 0.8
    else:
        return 1.0

def scoreDiffMult(pointdiff):
    if pointdiff > 0:
        return 1
    elif pointdiff == 0:
        return 2
    elif pointdiff < -8:
        return 3
    else:
        return 4

def timeMult(row):
    sec = secSinceHalf(row)
    PD = scoreDiff(row)
    
    if PD <= 0 and sec >= 0:
        return ((sec * 0.001)**3) + 1.
    else:
        return 1.

def surrenderIndex(row):
    pd = scoreDiff(row)
    return fieldPosScore(row) * distScore(row) * scoreDiffMult(pd) * timeMult(row)

def receiving(row):
    if row['teamPoss'] == row['homeTeam']:
        return row['awayTeam']
    else:
        return row['homeTeam']
    
def touchback(row):
    if 'Touchback' in row['play']:
        return "Touchback"
    elif 'No return' in row['play']:
        return "No return"
    else:
        return "Returned"

def puntDist(row):
    if 'BLOCKED' in row.play:
        return 0
    elif 'Touchback' in row.play:
        return row.dist2goal - 20
    else:
        return int(row.play.split('of ')[-1].split(' yards')[0])
    
def stringify(row):
    num = ['st','nd','rd','th']
    if row['awayTeam'] == row['teamPoss']:
        puntScore = row['awayScore']
        recScore = row['homeScore']
    else:
        puntScore = row['homeScore']
        recScore = row['awayScore']
    return "Q%s - %s - %i%s and %i\n%s %s - %s %s"%(row['Q'],row['time'],row['down'],num[int(row['down'])-1],row['distance'],row['teamPoss'],puntScore,row['recTeam'],recScore)



'''
Get PBP
'''
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
# allDF.to_csv('allPBP.csv')

print('Getting Punts...')
puntDF = allDF[allDF['play'].str.contains('Punt ')]

print('Done!')

'''
Surrender Punts
'''

print('Cleaning up PuntDF...')
NFL = np.load("2009-2018_surrender_indices.npy")
puntDF['recTeam'] = puntDF.apply(lambda row : receiving(row),axis=1)
puntDF['surrenderIndex'] = puntDF.apply(lambda row : surrenderIndex(row),axis=1)
puntDF = puntDF[['S','gameID','Q','time','awayTeam','awayScore','homeScore','homeTeam'
                 ,'teamPoss','recTeam','down','distance','side','dist2goal','surrenderIndex','play']]
puntDF = puntDF.sort_values('surrenderIndex',ascending=False)
puntDF['NFLpercentiles'] = puntDF.apply(lambda row : perc(NFL,row['surrenderIndex']),axis=1)
puntDF['percentiles'] = puntDF.apply(lambda row : perc(puntDF['surrenderIndex'],row['surrenderIndex']),axis=1)
puntDF['result'] = puntDF.apply(lambda row : touchback(row),axis = 1)
puntDF['scoreDiff'] = puntDF.apply(lambda row : scoreDiff(row),axis = 1)
puntDF['puntDist'] = puntDF.apply(lambda row : puntDist(row),axis = 1)
puntDF['puntEndLoc'] = puntDF['dist2goal'] - puntDF['puntDist']
puntDF['surrenderRank'] = puntDF.surrenderIndex.rank(method='max',ascending=False).astype('int')
puntDF['situation'] = puntDF.apply(lambda row : stringify(row), axis = 1)

puntDF = puntDF[['S', 'gameID', 'Q', 'time', 'awayTeam', 'awayScore', 'homeScore',
       'homeTeam', 'teamPoss', 'recTeam', 'down', 'distance', 'dist2goal', 'puntDist',
       'puntEndLoc', 'surrenderIndex','surrenderRank', 'percentiles', 'NFLpercentiles', 'play',
       'situation','result']]

print('Exporting Surrender DF...')
puntDF.to_csv('surrender.csv')

print('Done!')