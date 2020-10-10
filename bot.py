import os
import random
from os import environ
import pandas as pd
import tabulate
import discord
from discord.ext import commands
from tabulate import tabulate
import boto3

s3 = boto3.client('s3')

s3.download_file('isfl-surrender-bot','surrender.csv','surrender.csv')
puntDF = pd.read_csv('surrender.csv')

TOKEN = environ['DISCORD_TOKEN']

bot = commands.Bot(command_prefix='s!')

bot.remove_command('help')

@bot.command(name='help', help='Help')
async def help(ctx):
    embed=discord.Embed(title=" ", color=0xff9500)
    embed.set_author(name="Commands for Surrender Bot")
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/685587194861060146/731295955982483547/ISFL_logo_2000px.png")
    embed.add_field(name="Game Commands", value="`s!game [gameID]`", inline=True)
    embed.add_field(name="All-Time Records", value="`s!top`", inline=True)
    embed.add_field(name="Season Records", value="`s!topS [season #]`", inline=True)
    embed.add_field(name="Team Records", value="`s!topTeam [Team Initials]`", inline=True)
    await ctx.send(embed=embed)
    return
   
@bot.command(name='gameID', help='Get surrender index for a game ID.')
async def gameID(ctx, game_id: int):
    gameDF = puntDF[(puntDF.gameID == game_id) & (puntDF.percentiles >= 90)]

    if len(gameDF) < 1:
        await ctx.send("Error - Game Not Found")
        return
    
    num = gameDF['S'].iloc[0]
    if num < 10:
        strnum = '0' + str(num)
    elif num >= 10:
        strnum = str(num)
    if num < 24:
        urlprefix = "http://sim-football.com/indexes/NSFLS%s"%strnum
    else:
        urlprefix = "http://sim-football.com/indexes/ISFLS%s"%strnum

    await ctx.send("All 90th percentile punts from %i (%i total):"%(game_id, len(gameDF)))
    
    gameDF = gameDF.rename(columns={'situation':'Game Situation','play':'Punt',
                                    'surrenderIndex':"Index",'surrenderRank':'Rank',
                                    'percentiles':"Perc."})
    if len(gameDF) <= 10:
        table = tabulate(gameDF[['Game Situation', 'Punt','Index','Rank','Perc.']],headers='keys',tablefmt='simple',showindex=False)
        await ctx.send("```%s```"%table)
    else:
        game1DF, game2DF = np.split(gameDF, [int(.5*len(gameDF))])
        table1 = tabulate(game1DF[['Game Situation', 'Punt','Index','Rank','Perc.']],headers='keys',tablefmt='simple',showindex=False)
        table2 = tabulate(game2DF[['Game Situation', 'Punt','Index','Rank','Perc.']],headers='keys',tablefmt='simple',showindex=False)
        await ctx.send("```%s```"%table1)
        await ctx.send("```%s```"%table2)
        
#     for i in range(len(gameDF)):
#         embed=discord.Embed(title=gameDF['play'].iloc[i],color=0xff7b00)
#         embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/685587194861060146/731295955982483547/ISFL_logo_2000px.png")
#         embed.set_author(name="S%i - %s @ %s (%i/%i)"%(gameDF['S'].iloc[i],gameDF['awayTeam'].iloc[i],gameDF['homeTeam'].iloc[i],i+1,len(gameDF)),
#                          url="%s/Boxscores/%s.html"%(urlprefix,game_id))
#         embed.add_field(name="Game Situation", value=gameDF['situation'].iloc[i], inline=False)
# #         embed.add_field(name=Punt, value=gameDF['play'].iloc[i], inline=False)
#         embed.add_field(name="Surrender Index", value=round(gameDF['surrenderIndex'].iloc[i],3), inline=False)
#         embed.add_field(name="Overall Rank", value=gameDF['surrenderRank'].iloc[i], inline=True)
#         embed.add_field(name="Percentile", value=round(gameDF['percentiles'].iloc[i],3), inline=True)
#         embed.set_footer(text="SurrenderBot, by infinitempg")
#         await ctx.send(embed=embed)
    return
  
@bot.command(name='top', help='List of top Surrender Punts')
async def top(ctx):
    top5DF = puntDF.head(10)
    top5DF = top5DF.rename(columns={'situation':'Game Situation','play':'Punt','surrenderIndex':"Index",'surrenderRank':'Rank','percentiles':"Perc."})
    table = tabulate(top5DF[['Rank','S','Game Situation', 'Punt','Index']],headers='keys',tablefmt='simple',showindex=False)
    await ctx.send("Top 10 All-Time Surrender Punts")
    await ctx.send("```%s```"%table)
    return

@bot.command(name='topS', help='List of top Surrender Punts by Season')
async def topS(ctx, S: int):

    if S not in puntDF.S.unique():
        await ctx.send("Season not found.")
        return

    top5DF = puntDF[puntDF.S == S].head(10)
    top5DF = top5DF.rename(columns={'situation':'Game Situation','play':'Punt','surrenderIndex':"Index",'surrenderRank':'Rank','percentiles':"Perc."})
    table = tabulate(top5DF[['Rank','Game Situation', 'Punt','Index']],headers='keys',tablefmt='simple',showindex=False)
    await ctx.send("Top 10 Surrender Punts in S%i"%S)
    await ctx.send("```%s```"%table)
    return

@bot.command(name='topTeam', help='List of top Surrender Punts by Team')
async def topTeam(ctx, team: str):

    if team == 'ARI':
        teamT = 'AZ'
    elif team == 'NYS':
        teamT = 'NY'
    elif team == 'NOLA':
        teamT = 'NO'
    elif team not in ['BAL','YKW','COL','AZ','OCO','SJS','PHI','NO','CHI','AUS','SAR','HON','BER','NY']:
        await ctx.send('Team not found.')
        return
    else:
        teamT = team

    top5DF = puntDF[puntDF.teamPoss == teamT].head(10)
    top5DF = top5DF.rename(columns={'situation':'Game Situation','play':'Punt','surrenderIndex':"Index",'surrenderRank':'Rank','percentiles':"Perc."})
    table = tabulate(top5DF[['Rank','S','Game Situation', 'Punt','Index']],headers='keys',tablefmt='simple',showindex=False)
    await ctx.send("Top 10 Surrender Punts for %s"%team)
    await ctx.send("```%s```"%table)
    return

bot.run(TOKEN)