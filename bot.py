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

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.command(name='99', help='Responds with a random quote from Brooklyn 99')
async def nine_nine(ctx):
    brooklyn_99_quotes = [
        'I\'m the human form of the 💯 emoji.',
        'Bingpot!',
        (
            'Cool. Cool cool cool cool cool cool cool, '
            'no doubt no doubt no doubt no doubt.'
        ),
    ]

    response = random.choice(brooklyn_99_quotes)
    await ctx.send(response)
    
@bot.command(name='roll_dice', help='Simulates rolling dice.')
async def roll(ctx, number_of_dice: int, number_of_sides: int):
    dice = [
        str(random.choice(range(1, number_of_sides + 1)))
        for _ in range(number_of_dice)
    ]
    await ctx.send(', '.join(dice))
    
@bot.command(name='game', help='Get surrender index for a game ID.')
async def game(ctx, game_id: int):
    gameDF = puntDF[(puntDF.gameID == game_id) & (puntDF.percentiles >= 90)]
    await ctx.send("All 90th percentile punts from game %s (%i total):"%(len(gameDF),game_id))
    for i in range(len(gameDF)):
        embed=discord.Embed(title=gameDF['play'].iloc[i],color=0xff7b00)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/685587194861060146/731295955982483547/ISFL_logo_2000px.png")
        embed.set_author(name="S%i - %s @ %s (%i/%i)"%(gameDF['S'].iloc[i],gameDF['awayTeam'].iloc[i],gameDF['homeTeam'].iloc[i],i,len(gameDF)))
        embed.add_field(name="Game Situation", value=gameDF['situation'].iloc[i], inline=False)
#         embed.add_field(name=Punt, value=gameDF['play'].iloc[i], inline=False)
        embed.add_field(name="Score", value=gameDF['surrenderIndex'].iloc[i], inline=False)
        embed.add_field(name="Overall Rank", value=gameDF['surrenderRank'].iloc[i], inline=True)
        embed.add_field(name="Percentile", value=round(gameDF['percentiles'].iloc[i],3), inline=True)
        embed.set_footer(text="SurrenderBot by infinitempg")
        await ctx.send(embed=embed)


bot.run(TOKEN)