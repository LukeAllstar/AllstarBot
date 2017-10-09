import discord
from discord.ext import commands
import json
import sqlite3
import random

with open('config.json') as json_data_file:
    data = json.load(json_data_file)

bot = commands.Bot(command_prefix=data["command_prefix"], description=data["description"])

conn = sqlite3.connect('tabletop.db')
quotesConn = sqlite3.connect('quotes.db')


quotesCur = quotesConn.cursor()
c = conn.cursor()

#quotesCur.execute('''CREATE TABLE quotes(quote, name, addedBy)''')
#quotesCur.execute('''INSERT INTO quotes VALUES('Achtung ich drehe um!', 'Bob Bobson', 'Luke Allstar')''')
#quotesCur.execute('''INSERT INTO quotes VALUES('test 111', 'Luke Allstar', 'Luke Allstar')''')
#quotesCur.execute('''INSERT INTO quotes VALUES('test 333', 'Luke Allstar', 'Luke Allstar')''')
#quotesCur.execute('''INSERT INTO quotes VALUES('test 222', 'Luke Allstar', 'Luke Allstar')''')
#quotesCur.execute('''INSERT INTO quotes VALUES('Man kann nie zu viel Boost haben', 'Headdy', 'Luke Allstar')''')
#quotesCur.execute('''INSERT INTO quotes VALUES('Gerade war ich Erster, jetzt bin ich Letzter.', 'ParaSaint', 'Luke Allstar')''')
#quotesConn.commit()
  
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

#@bot.command()
#async def test():
#    await bot.say('Allstar Bot is up and running!')

@bot.command()
async def player_win_month(month : int):
    """ Returns all players who won a game in a certain month and the amount of wins """
    s = '```'
    s += 'Gewinne pro Spieler im Monat #%s' % month
    s += '| {:20s}| {:10s}|\n'.format('Name', 'Wins')
    s += ('-' * 35)
    s += '\n'
    for row in c.execute("""Select player.name, count(player.name)
                                from played
                                join player on playerId = player.rowid
                                join game on gameId = game.rowid
                                where strftime('%m', date(playdate)) = '""" + str(month).zfill(2) + """'
                                    AND rank = 1
                                group by player.name"""):
        s += '| {:20s}| {:10s}|\n'.format(str(row[0]), str(row[1]))
    s += '```'
    await bot.say(s)
    
#@bot.command()
#async def phil():
#    await bot.say('Der schoenste Oesterreicher :flag_at:')

@bot.command(aliases=["zitat"])
async def quote(name : str = ""):
    """ Selects a random quote from the database.
    If a name parameter is given it searches for a quote from that person"""
    
    quotesCur.execute("""SELECT quote, name from quotes 
                            WHERE ROWID IN
                                (Select ROWID from quotes
                                    where LOWER(name) like '%"""+name.lower()+"""%' 
                                    ORDER BY RANDOM() LIMIT 1)""")
    row = quotesCur.fetchone()
    if(row != None):
        await bot.say('```\"%s\" - %s```' % (row[0], row[1]))
    else:
        await bot.say("Kein Zitat von der Person %s gefunden." % name)
    
@bot.command(pass_context=True, aliases=["addzitat"])
async def addquote(ctx, quote : str, name : str):
    """ Adds one quote to the database. adds the person who issued the command to the table """
    quotesCur.execute("""INSERT INTO quotes (quote, name, addedBy) VALUES ('%s', '%s', '%s')""" % (quote, name, ctx.message.author))
    quotesConn.commit()
    await bot.say("Zitat hinzugefuegt")

@bot.command(pass_context=True)
async def test(ctx):
    """ Testing some permission stuff """
    #await bot.say(ctx.message)
    await bot.say(ctx.message.author)
    await bot.say(ctx.message.author.roles)
    await bot.say(ctx.message.author.server_permissions.administrator)
    
    
    
bot.run(data["token"])