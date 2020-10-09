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
    
@bot.command(name='game', help='Get surrender index for a game ID.')
async def game(ctx, game_id: int):
    gameDF = puntDF[(puntDF.gameID == game_id) & (puntDF.percentiles >= 90)]
    
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
        embed.add_field(name="Surrender Index", value=gameDF['surrenderIndex'].iloc[i], inline=False)
        embed.add_field(name="Overall Rank", value=gameDF['surrenderRank'].iloc[i], inline=True)
        embed.add_field(name="Percentile", value=round(gameDF['percentiles'].iloc[i],3), inline=True)
        embed.set_footer(text="SurrenderBot, by infinitempg")
        await ctx.send(embed=embed)


bot.run(TOKEN)