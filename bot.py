import os
import random
from os import environ
import pandas as pd
import tabulate
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
    gameDF = puntDF[puntDF.gameID == game_id]
    gameDF = gameDF.rename(columns = {'surrenderIndex':'Score','surrenderRank':'Rank'})
    table = tabulate(gameDF[['situation', 'play','Score','Rank']],headers='keys',tablefmt='simple',showindex=False)
    await ctx.send('**%s @ %s - S%s**'%(gameDF['awayTeam'].iloc[0],gameDF['homeTeam'].iloc[0],gameDF['S'].iloc[0]))
    await ctx.send("```%s```"%table)

bot.run(TOKEN)