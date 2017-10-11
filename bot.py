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

@bot.command()
async def playersofgame(game : str):
    """ Returns all players who played a certain game """
    s = "```Spieler des Spieles " + game + ":\n"
    first = True
    # TODO: check which games exist for that pattern, like in winpercent function
    for row in c.execute("""Select player.name
                                from played
                                join player on played.playerid = player.rowid
                                join game on played.gameid = game.rowid
                                where LOWER(game.name) like '%""" + game.lower() + """%'
                                group by player.name"""):
        if first == False:
            s += ", "
        else:
            first = False
        s += row[0]
    s += "```"
    await bot.say(s)

@bot.command()
async def winpercent(player : str, game : str = ""):
    """ Returns the winpercent of a player. If game is given, it returns the winpercent for that game """
    """ TODO: Maybe have "all" as playername for winpercent of all players? """
    s = "```Winpercent for player " + player + ""
    gameName = ""
    if game != "":
        try:
            # check if the game exists
            # if multiple games have been found, print an error with information
            errMsg = "```Es wurden mehrere Spiele fuer den Namen '" + game + "' gefunden:\n"
            error = False
            for row in c.execute("""Select game.name
                                from game
                                where LOWER(game.name) like '%""" + game.lower() + """%'
                                group by game.name"""):
                  
                if error == True:
                    errMsg += row[0] + "\n"
                else:
                    if gameName != "":
                        error = True
                        errMsg += gameName + "\n"
                        errMsg += row[0] + "\n"
                    else:
                        gameName = row[0]
            if error == True:
                errMsg += "```"
                await bot.say(errMsg)
                return
            s += " im Spiel " + gameName
        except:
            # Something went wrong, maybe print a better error
            await bot.say("Something went wrong :(")
            return
                 
    s += ":\n"
    try:
        # get number of wins
        c.execute("""Select count(player.name)
                            from played
                            join player on played.playerid = player.rowid
                            join game on played.gameid = game.rowid
                            where LOWER(player.name) like '%""" + player.lower() + """%'
                                AND LOWER(game.name) like '%""" + gameName + """%'
                                AND played.rank = 1
                                AND played.iscoop = 'False'
                            group by player.name""")

        wins = int(c.fetchone()[0])
    except:
        wins = 0
        
    try:
        # get number of games played
        c.execute("""Select count(*)
                                from played
                                join player on played.playerid = player.rowid
                                join game on played.gameid = game.rowid
                                where LOWER(player.name) like '%""" + player.lower() + """%'
                                    AND LOWER(game.name) like '%""" + gameName + """%'
                                    AND played.iscoop = 'False'""")
        games = int(c.fetchone()[0])
        winpercent = 100/games*wins
        s += str(round(winpercent,2)) + "% (" + str(games) + " Spiele, " + str(wins) + " Siege)"
        s += "```"
        await bot.say(s)
    except:
        await bot.say("Keine Eintraege fuer Spieler " + player + " gefunden :persevere:")

#async def winpercentgame(player : str, game : str = ""):



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
        await bot.say("Kein Zitat von '%s' gefunden.\nHier nimm ein :ice_cream: stattdessen." % name)
    
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