import pandas as pd
import numpy as np
import os
from scipy.stats import percentileofscore as perc
from simFootballPBP import *
import boto3
from os import environ

s3 = boto3.client('s3')

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
    return "Q%s - %s - %i%s and %i\n%s %s - %s %s\n"%(row['Q'],row['time'],row['down'],num[int(row['down'])-1],row['distance'],row['teamPoss'],puntScore,row['recTeam'],recScore)

def splitline(row):
    string = row.play.split('yards.')
    if len(string) > 1:
        return str(string[0] + 'yards.\n' + string[1])
    elif "BLOCKED" in string[0]:
        split = row.play.split('BLOCKED')
        return str(split[0] + 'BLOCKED\n' + split[1])
    else:
        return row.play
'''
Get PBP
'''
S = 25

sData = []
idList, idDict = getSeasonIDs(S)

print('Season:',S)
print('Games:',len(idList))

print('Gathering PBP...')
for i in idList:
    sData.append(getGameData(S,i,idDict))

sDF = pd.concat(sData)
sDF.to_csv('PBP/S%sPBP.csv'%S)
s3.upload_file('PBP/S%sPBP.csv'%S,'isfl-surrender-bot','PBP/S%sPBP.csv'%S)

print('PBP for S%s saved!'%S)

print('Combining all Seasons...')

for i in range(1,S+1):
    s3.download_file('isfl-surrender-bot','PBP/S%iPBP.csv'%i,'PBP/S%iPBP.csv'%i)

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
NFL = np.load("2009-2019_surrender_indices.npy")
puntDF['recTeam'] = puntDF.apply(lambda row : receiving(row),axis=1)
puntDF['surrenderIndex'] = puntDF.apply(lambda row : surrenderIndex(row),axis=1)
puntDF = puntDF[['S','W','gameID','Q','time','awayTeam','awayScore','homeScore','homeTeam'
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
puntDF['play'] = puntDF['play'].str.replace('Dasistwirklichseinnachname, A.','D, Alex')
puntDF['play'] = puntDF.apply(lambda row : splitline(row), axis = 1)

puntDF = puntDF[['S', 'W', 'gameID', 'Q', 'time', 'awayTeam', 'awayScore', 'homeScore',
       'homeTeam', 'teamPoss', 'recTeam', 'down', 'distance', 'dist2goal', 'puntDist',
       'puntEndLoc', 'surrenderIndex','surrenderRank', 'percentiles', 'NFLpercentiles', 'play',
       'situation','result']]

print('Exporting Surrender DF...')
puntDF.to_csv('surrender.csv')
s3.upload_file('surrender.csv','isfl-surrender-bot','surrender.csv')

print('Done!')

print('Restarting SurrenderBot')
import heroku3
heroku_conn = heroku3.from_key(environ['HEROKU_KEY'])
app = heroku_conn.apps()['surrenderbot']
app.restart()
print('App Restarted!')

print('Checking if new week...')
s3.download_file('isfl-surrender-bot','curSW.csv','curSW.csv')
curSW = pd.read_csv('curSW.csv').iloc[0]

curS = max(testDF.S)
curW = max(testDF[testDF.S == curS].W)
print('S%iW%i'%(curS,curW))

if curSW.S == curS and curSW.W == curW:
    print('No update.')
else:
    print('Tweeting top surrender punts...')
    newSW = pd.DataFrame([[curS,curW]],columns=['S','W'])
    newSW.to_csv('curSW.csv')
    s3.upload_file('curSW.csv','isfl-surrender-bot','curSW.csv')
    import tweepy
    from os import environ

    consumer_key = environ['CONSUMER_KEY']
    consumer_secret = environ['CONSUMER_SECRET']
    access_token = environ['ACCESS_TOKEN']
    access_token_secret = environ['ACCESS_TOKEN_SECRET']

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token,access_token_secret)

    api = tweepy.API(auth)

    def tweetMessage(row):

        # location of ball
        if row.dist2goal < 50:
            loc = "%s %i"%(row.recTeam,row.dist2goal)
        elif row.dist2goal == 50:
            loc = "midfield"
        else:
            loc = "%s %i"%(row.teamPoss,100-row.dist2goal)

        # who has what score
        if row['awayTeam'] == row['teamPoss']:
            puntScore = row['awayScore']
            recScore = row['homeScore']
        else:
            puntScore = row['homeScore']
            recScore = row['awayScore']

        # score string
        if puntScore < recScore:
            rel = "losing"
        elif puntScore > recScore:
            rel = "winning"
        else:
            rel = "tied"

        # percentile string
        percentile = int(row.percentiles)
        mod = percentile%10
        if mod == 1:
            perc = "%ist"%percentile
        elif mod == 2:
            perc = "%ind"%percentile
        elif mod == 3:
            perc = "%ird"%percentile
        else:
            perc = "%ith"%percentile

        # down and distance
        if row.down == 1:
            dW = "%ist"%row.down
        elif row.down == 2:
            dW = "%ind"%row.down
        elif row.down == 3:
            dW = "%ird"%row.down
        else:
            dW = "%ith"%row.down

        # quarter
        if row.Q == 1:
            Q = "%ist"%row.Q
        elif row.Q == 2:
            Q = "%ind"%row.Q
        elif row.Q == 3:
            Q = "%ird"%row.Q
        else:
            Q = "%ith"%row.Q

        string = "In S%i W%i, %s decided to punt to %s from the %s on %s and %i with %s remaining in the %s quarter while %s %i to %i.\n\nWith a Surrender Index of %.2f, this punt ranks at the %s percentile of cowardly punts in ISFL History. Overall, it is ranked #%i all time."%(row.S,row.W,row.teamPoss,row.recTeam,loc,dW,row.distance,row.time,Q,rel,puntScore,recScore,row.surrenderIndex,perc,row.surrenderRank)
        return string

    thisWeek = testDF[(testDF.S == curS) & (testDF.W == curW) & (testDF.percentiles >= 90)].sort_values("percentiles")
    thisWeek['tweet'] = thisWeek.apply(lambda x : tweetMessage(x),axis=1)
    for i in range(len(thisWeek)):
        api.update_status(thisWeek.tweet.iloc[i])

    print('Tweeted!')
print('All Done. Goodbye!')