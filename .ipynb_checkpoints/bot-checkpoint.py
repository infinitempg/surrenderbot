import os
import random
from os import environ
import pandas as pd
import tabulate
import discord
from discord.ext import commands
from tabulate import tabulate

puntDF = pd.read_csv('surrender.csv')

TOKEN = environ['DISCORD_TOKEN']

bot = commands.Bot(command_prefix='s!')

class GameStats:
    
    @bot.command(name='game', help='Get surrender index for a game ID.')
    async def game(ctx, game_id: int):
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

        await ctx.send("All 90th percentile punts from game %s (%i total):"%(game_id, len(gameDF)))
        for i in range(len(gameDF)):
            embed=discord.Embed(title=gameDF['play'].iloc[i],color=0xff7b00)
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/685587194861060146/731295955982483547/ISFL_logo_2000px.png")
            embed.set_author(name="S%i - %s @ %s (%i/%i)"%(gameDF['S'].iloc[i],gameDF['awayTeam'].iloc[i],gameDF['homeTeam'].iloc[i],i+1,len(gameDF)),
                             url="%s/Boxscores/%s.html"%(urlprefix,game_id))
            embed.add_field(name="Game Situation", value=gameDF['situation'].iloc[i], inline=False)
    #         embed.add_field(name=Punt, value=gameDF['play'].iloc[i], inline=False)
            embed.add_field(name="Surrender Index", value=round(gameDF['surrenderIndex'].iloc[i],3), inline=False)
            embed.add_field(name="Overall Rank", value=gameDF['surrenderRank'].iloc[i], inline=True)
            embed.add_field(name="Percentile", value=round(gameDF['percentiles'].iloc[i],3), inline=True)
            embed.set_footer(text="SurrenderBot, by infinitempg")
            await ctx.send(embed=embed)
        return
    
class AllTime:
    '''
    Look up all-time surrender punt statistics
    '''
    @bot.command(name='top', help='List of top Surrender Punts')
    async def top(ctx):
        top5DF = puntDF.head(5)
        top5DF = top5DF.rename(columns={'situation':'Game Situation','play':'Punt','surrenderIndex':"Index",'surrenderRank':'Rank','percentiles':"Perc."})
        table = tabulate(top5DF[['Rank','S','Game Situation', 'Punt','Index']],headers='keys',tablefmt='simple',showindex=False)
        await ctx.send("Top 5 All-Time Surrender Punts")
        await ctx.send("```%s```"%table)
        return
    
    @bot.command(name='topS', help='List of top Surrender Punts by Season')
    async def topS(ctx, S = int):
        
        if S not in puntDF.S.unique():
            await ctx.send("Season not found.")
            return
        
        top5DF = puntDF[puntDF.S == S].head(5)
        top5DF = top5DF.rename(columns={'situation':'Game Situation','play':'Punt','surrenderIndex':"Index",'surrenderRank':'Rank','percentiles':"Perc."})
        table = tabulate(top5DF[['Rank','Game Situation', 'Punt','Index']],headers='keys',tablefmt='simple',showindex=False)
        await ctx.send("Top 5 Surrender Punts in S%i"%S)
        await ctx.send("```%s```"%table)
        return
    
    @bot.command(name='topT', help='List of top Surrender Punts by Team')
    async def topS(ctx, team = str):
        
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
            
        top5DF = puntDF[puntDF.teamPoss == teamT].head(5)
        top5DF = top5DF.rename(columns={'situation':'Game Situation','play':'Punt','surrenderIndex':"Index",'surrenderRank':'Rank','percentiles':"Perc."})
        table = tabulate(top5DF[['Rank','S','Game Situation', 'Punt','Index']],headers='keys',tablefmt='simple',showindex=False)
        await ctx.send("Top 5 Surrender Punts in S%i"%S)
        await ctx.send("```%s```"%table)
        return

bot.add_cog(GameStats())
bot.add_cog(AllTime())
bot.run(TOKEN)