import discord
from discord.ext import commands
import json
import sqlite3
import random
import datetime
import locale
import sheets
import os

with open('config.json') as json_data_file:
    data = json.load(json_data_file)

if not os.path.exists('db/tabletop.db') or not os.path.exists('db/gta.db') or not os.path.exists('db/quotes.db'):
    print("Databases do not exist. Please run setup.py first!")
    exit()
    
bot = commands.Bot(command_prefix=data["command_prefix"], description=data["description"])
# maybe usefull later:
#bot.remove_command("help")

ttsConn = sqlite3.connect('db/tabletop.db')
quotesConn = sqlite3.connect('db/quotes.db')
gtaConn = sqlite3.connect('db/gta.db')

quotesCur = quotesConn.cursor()
ttsCur = ttsConn.cursor()
gtaCur = gtaConn.cursor()

locale.setlocale(locale.LC_ALL, 'German_Germany')
  
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.command(aliases=["ttssiegeimmonat", "tabletopwinsinmonth", "tabletopsiegeimmonat"])
async def ttswinsinmonth(month : int = None, player : str = ""):
    """ Returns all players who won a game in a certain month and the amount of wins
        If player is given, return the wins in that month of that player"""
    if month == None:
        await bot.say('```!ttswinsinmonth <month> [game]```')
    else:
        s = '```'
        if player != "":
            s += "Gewinne fuer Spieler '" + player + "'"
        else:
            s += 'Gewinne pro Spieler'
        s += " im Monat '%s'\n" % datetime.date(1900,month, 1).strftime('%B')
        s += '| {:20s}| {:10s}|\n'.format('Name', 'Wins')
        s += ('-' * 35)
        s += '\n'
        for row in ttsCur.execute("""Select player.name, count(player.name)
                                    from played
                                    join player on playerId = player.rowid
                                    join game on gameId = game.rowid
                                    where strftime('%m', date(playdate)) = '""" + str(month).zfill(2) + """'
                                        AND player.name like '%""" + player + """%'
                                        AND rank = 1
                                    group by player.name"""):
            s += '| {:20s}| {:10s}|\n'.format(str(row[0]), str(row[1]))
        s += '```'
        await bot.say(s)

@bot.command(aliases = ["ttsspielervonspiel", "tabletopplayersofgame"])
async def ttsplayersofgame(game : str = None):
    """ Returns all players who played a certain game """
    if game == None:
        await bot.say('```!ttsplayersofgame <game>```')
    else:
        s = "```Spieler des Spieles " + game + ":\n"
        first = True
        # TODO: check which games exist for that pattern, like in winpercent function
        for row in ttsCur.execute("""Select player.name
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

@bot.command(aliases = ["ttssiegprozent", "tabletopwinpercent", "tabletopsiegprozent"])
async def ttswinpercent(player : str = None, game : str = ""):
    """ Returns the winpercent of a player. If game is given, it returns the winpercent for that game """
    """ TODO: Maybe have "all" as playername for winpercent of all players? """
    if player == None:
        await bot.say('```!ttswinpercent <player> [game]```')
    else:
        s = "```Winpercent for player " + player + ""
        gameName = ""
        if game != "":
            try:
                # check if the game exists
                # if multiple games have been found, print an error with information
                errMsg = "```Es wurden mehrere Spiele fuer den Namen '" + game + "' gefunden:\n"
                error = False
                for row in ttsCur.execute("""Select game.name
                                    from game
                                    where LOWER(game.name) like '%""" + game.lower() + """%'
                                    group by game.name"""):
                      
                    if error == True:
                        errMsg += "'" + row[0] + "', "
                    else:
                        if gameName != "":
                            error = True
                            errMsg += "'" + gameName + "', "
                            errMsg += "'" + row[0] + "', "
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
            ttsCur.execute("""Select count(player.name)
                                from played
                                join player on played.playerid = player.rowid
                                join game on played.gameid = game.rowid
                                where LOWER(player.name) like '%""" + player.lower() + """%'
                                    AND LOWER(game.name) like '%""" + gameName + """%'
                                    AND played.rank = 1
                                    AND played.iscoop = 'False'
                                group by player.name""")

            wins = int(ttsCur.fetchone()[0])
        except:
            wins = 0
            
        try:
            # get number of games played
            ttsCur.execute("""Select count(*)
                                    from played
                                    join player on played.playerid = player.rowid
                                    join game on played.gameid = game.rowid
                                    where LOWER(player.name) like '%""" + player.lower() + """%'
                                        AND LOWER(game.name) like '%""" + gameName + """%'
                                        AND played.iscoop = 'False'""")
            games = int(ttsCur.fetchone()[0])
            winpercent = 100/games*wins
            s += str(round(winpercent,2)) + "% (" + str(games) + " Spiele, " + str(wins) + " Siege)"
            s += "```"
            await bot.say(s)
        except:
            await bot.say("Keine Eintraege fuer Spieler " + player + " gefunden :persevere:")


@bot.command(aliases=["ttssiege", "ttsgewinne", "tabletopwins", "tabletopsiege", "tabletopgewinne"])
async def ttswins(player : str = None, game : str = ""):
    """ Returns how many wins a player has """
    """ If game is given, returns the wins for that game """
    if player == None:
        await bot.say('```!ttswins <player> [game]```')
    else:
        gameName = ""
        if game != "":
            try:
                # check if the game exists
                # if multiple games have been found, print an error with information
                # TODO: put this into a seperate function, is needed multiple times
                errMsg = "```Es wurden mehrere Spiele fuer den Namen '" + game + "' gefunden:\n"
                error = False
                for row in ttsCur.execute("""Select game.name
                                    from game
                                    where LOWER(game.name) like '%""" + game.lower() + """%'
                                    group by game.name"""):
                      
                    if error == True:
                        errMsg += "'" + row[0] + "', "
                    else:
                        if gameName != "":
                            error = True
                            errMsg += "'" + gameName + "', "
                            errMsg += "'" + row[0] + "', "
                        else:
                            gameName = row[0]
                if error == True:
                    errMsg += "```"
                    await bot.say(errMsg)
                    return
            except Exception as e:
                # Something went wrong, maybe print a better error
                print(e)
                await bot.say("Something went wrong :(")
                return
                     
        try:
            # get number of wins
            ttsCur.execute("""Select count(player.name)
                                from played
                                join player on played.playerid = player.rowid
                                join game on played.gameid = game.rowid
                                where LOWER(player.name) like '%""" + player.lower() + """%'
                                    AND LOWER(game.name) like '%""" + gameName + """%'
                                    AND played.rank = 1
                                    AND played.iscoop = 'False'
                                group by player.name""")

            wins = int(ttsCur.fetchone()[0])
        except:
            wins = 0
            
        s = "```Spieler '" + player + "' hat " + str(wins) + " Siege"
        if gameName != "":
            s += " im Spiel '" + gameName + "'"
        s += "```"
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
        await bot.say("Kein Zitat von '%s' gefunden.\nHier nimm ein :ice_cream: stattdessen." % name)

@bot.command(pass_context=True, aliases=["addzitat"])
async def addquote(ctx, quote : str = None, name : str = None):
    """ Adds one quote to the database. Adds the person who issued the command to the table """
    if quote == None or name == None:
        await bot.say('```!addquote "<quote>" "<name>"```')
    else:
        quotesCur.execute("""INSERT INTO quotes (quote, name, addedBy) VALUES ('%s', '%s', '%s')""" % (quote, name, ctx.message.author))
        quotesConn.commit()
        await bot.say("Zitat hinzugefuegt")

@bot.command(pass_context=True)
async def test(ctx):
    """ Testing some permission stuff """
    await bot.say("author: " + str(ctx.message.author))
    #for role in ctx.message.author.roles:
    #    await bot.say("rolle: " + str(role.name))
    await bot.say("ist admin: " + str(ctx.message.author.server_permissions.administrator))

    
@bot.command()
async def gtaracewins(player : str = None):
    """ Returns the number of race wins of a player """
    if player == None:
        await bot.say('```!gtaracewins <player>```')
    else:
        gtaCur.execute("""Select COALESCE(count(*),0)
                            from raced
                            join player on player.rowid = raced.playerid
                            where rank = 1 AND
                                LOWER(player.name) like '%""" + player + """%'""")
        row = gtaCur.fetchone()
        await bot.say('```Spieler %s hat %s Rennen gewonnen```' % (player, row[0]))
  
@bot.command()
async def gtavehicles(vehicle : str = ""):
    """ Returns top 7 used vehicles """
    s = "```"
    if vehicle == "":
        s += "Die 7 meistverwendetsten Fahrzeuge\n"
        s += ('-' * 35)
        s += "\n"
        s += "| {:20s}| {:10s}|\n".format("Vehicle", "Anzahl")
        s += ('-' * 35)
        s += "\n"

    for row in gtaCur.execute("""Select vehicle, count(*) from (
                                    Select vehicle
                                    from raced
                                    where isdsq = 'False'
                                        AND vehicle like '%"""+vehicle+"""%'
                                    group by raceid, vehicle
                                )
                                group by vehicle
                                order by 2 desc
                                limit 7"""):
        if vehicle == "":
            s += '| {:20s}| {:10s}|\n'.format(str(row[0]), str(row[1]))
        else:
            s += 'Das Fahrzeug %s wurde %s mal verwendet.\n' % (row[0], row[1])
    s += '```'
    await bot.say(s)
  
@bot.command()
async def gtaplaylistwins():
    """ Returns a list of players who won a playlist """
    s = "```"
    s += "| {:20s}| {:10s}|\n".format("Spieler", "Siege")
    s += ('-' * 35)
    s += "\n"
    for row in gtaCur.execute("""
                    Select playername, count(*) as wins from
                        ( Select * from
                            ( Select playlistid, x.name as playlistname, player.name as playername, sum(points) as points from
                                ( Select *,
                                        CASE
                                        WHEN isdsq = 'True' OR isdnf = 'True' THEN 0
                                        WHEN rank = 1 THEN 15
                                        WHEN rank = 2 THEN 12
                                        WHEN rank = 3 THEN 10
                                        WHEN rank BETWEEN 4 AND 10 THEN 12 - rank
                                        ELSE 1
                                        END as points from
                                    playlist
                                    join race on race.playlistid = playlist.rowid
                                    join raced on raced.raceid = race.rowid
                                ) as x
                                join player on playerid = player.rowid
                                    group by playlistid, x.name, playername
                                    order by playlistid asc, points desc
                            ) group by playlistid
                              having max(points)
                        ) group by playername
                    order by wins desc"""):
        s += '| {:20s}| {:10s}|\n'.format(str(row[0]), str(row[1]))
    s += '```'
    await bot.say(s)
    
@bot.command()
async def updatetabletop():   
    try:
        global ttsCur
        global ttsConn
        ttsCur.close()
        ttsConn.close()
        await bot.say("Updating Tabletop Database ...")
        tts = sheets.Tabletop(True, True)
        tts.update_database()
        await bot.say("Update finished!")
    except Exception as e:
        print(e)
        await bot.say("Error, check log :robot:")
        
    try:
        ttsConn = sqlite3.connect('db/tabletop.db')
        ttsCur = ttsConn.cursor()
    except Exception as e:
        print(e)

@bot.command()
async def updategta():
    try:
        global gtaCur
        global gtaConn
        await bot.say("Updating Gta Database ...")
        gtaCur.close()
        gtaConn.close()
        gta = sheets.Gtasheet(True, True)
        gta.update_database()
        await bot.say("Update finished!")
    except Exception as e:
        print(e)
        await bot.say("Error, check log :robot:")

    try:
        gtaConn = sqlite3.connect('db/gta.db')
        gtaCur = gtaConn.cursor()
    except Exception as e:
        print(e)

@bot.command(pass_context=True)
async def friends(ctx):
    user = discord.utils.get(ctx.message.server.members, name = 'Lefty')
    await bot.say(":robot: My only friend is " + user.mention)
        
bot.run(data["token"])