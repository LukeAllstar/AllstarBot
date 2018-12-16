import discord
import sqlite3
from discord.ext import commands
import asyncio
import datetime
import sheets

class Tabletop:

    def __init__(self, bot):
        self.bot = bot
        self.ttsConn = sqlite3.connect('db/tabletop.db')
        self.ttsCur = self.ttsConn.cursor()


    @commands.command(aliases=["ttssiegeimmonat", "tabletopwinsinmonth", "tabletopsiegeimmonat"])
    async def ttswinsinmonth(self, month : int = None, player : str = ""):
        """Tabletop Siege eines Monats"""
        #Returns all players who won a game in a certain month and the amount of wins
        #If player is given, return the wins in that month of that player
        if month == None:
            await self.bot.say('```!ttswinsinmonth <month> [game]```')
        else:
            s = '```ml\n'
            if player != "":
                s += "Gewinne fuer Spieler '" + player + "'"
            else:
                s += 'Gewinne pro Spieler'
            s += " im Monat '%s'\n" % datetime.date(1900,month, 1).strftime('%B')
            s += '| {:20s}| {:10s}|\n'.format('Name', 'Wins')
            s += ('-' * 35)
            s += '\n'
            for row in self.ttsCur.execute("""Select player.name, count(player.name)
                                        from played
                                        join player on playerId = player.rowid
                                        join game on gameId = game.rowid
                                        where strftime('%m', date(playdate)) = '""" + str(month).zfill(2) + """'
                                            AND player.name like '%""" + player + """%'
                                            AND rank = 1
                                        group by player.name"""):
                s += '| {:20s}| {:10s}|\n'.format(str(row[0]), str(row[1]))
            s += '```'
            await self.bot.say(s)

    @commands.command(aliases = ["ttsspielervonspiel", "tabletopplayersofgame"])
    async def ttsplayersofgame(self, game : str = None):
        """Spieler die ein bestimmtes Tabletop Spiel bereits gespielt haben"""
        #Returns all players who played a certain game
        if game == None:
            await self.bot.say('```!ttsplayersofgame <game>```')
        else:
            s = "```Spieler des Spieles " + game + ":\n"
            first = True
            # TODO: check which games exist for that pattern, like in winpercent function
            for row in self.ttsCur.execute("""Select player.name
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
            await self.bot.say(s)

    @commands.command(aliases = ["ttssiegprozent", "tabletopwinpercent", "tabletopsiegprozent"])
    async def ttswinpercent(self, player : str = None, game : str = ""):
        """Siegesrate eines Spielers"""
        #Returns the winpercent of a player. If game is given, it returns the winpercent for that game
        #TODO: Maybe have "all" as playername for winpercent of all players?
        if player == None:
            await self.bot.say('```!ttswinpercent <player> [game]```')
        else:
            s = "```Winpercent for player " + player + ""
            gameName = ""
            if game != "":
                try:
                    # check if the game exists
                    # if multiple games have been found, print an error with information
                    errMsg = "```Es wurden mehrere Spiele fuer den Namen '" + game + "' gefunden:\n"
                    error = False
                    for row in self.ttsCur.execute("""Select game.name
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
                        await self.bot.say(errMsg)
                        return
                    s += " im Spiel " + gameName
                except:
                    # Something went wrong, maybe print a better error
                    await self.bot.say("Something went wrong :(")
                    return
                        
            s += ":\n"
            try:
                # get number of wins
                self.ttsCur.execute("""Select count(player.name)
                                    from played
                                    join player on played.playerid = player.rowid
                                    join game on played.gameid = game.rowid
                                    where LOWER(player.name) like '%""" + player.lower() + """%'
                                        AND LOWER(game.name) like '%""" + gameName + """%'
                                        AND played.rank = 1
                                        AND played.iscoop = 'False'
                                    group by player.name""")

                wins = int(self.ttsCur.fetchone()[0])
            except:
                wins = 0
                
            try:
                # get number of games played
                self.ttsCur.execute("""Select count(*)
                                        from played
                                        join player on played.playerid = player.rowid
                                        join game on played.gameid = game.rowid
                                        where LOWER(player.name) like '%""" + player.lower() + """%'
                                            AND LOWER(game.name) like '%""" + gameName + """%'
                                            AND played.iscoop = 'False'""")
                games = int(self.ttsCur.fetchone()[0])
                winpercent = 100/games*wins
                s += str(round(winpercent,2)) + "% (" + str(games) + " Spiele, " + str(wins) + " Siege)"
                s += "```"
                await self.bot.say(s)
            except:
                await self.bot.say("Keine Eintraege fuer Spieler " + player + " gefunden :persevere:")


    @commands.command(aliases=["ttssiege", "ttsgewinne", "tabletopwins", "tabletopsiege", "tabletopgewinne"])
    async def ttswins(self, player : str = None, game : str = ""):
        """Tabletop Siege eines Spielers"""
        #Returns how many wins a player has
        #If game is given, returns the wins for that game
        if player == None:
            await self.bot.say('```!ttswins <player> [game]```')
        else:
            gameName = ""
            if game != "":
                try:
                    # check if the game exists
                    # if multiple games have been found, print an error with information
                    # TODO: put this into a seperate function, is needed multiple times
                    errMsg = "```Es wurden mehrere Spiele fuer den Namen '" + game + "' gefunden:\n"
                    error = False
                    for row in self.ttsCur.execute("""Select game.name
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
                        await self.bot.say(errMsg)
                        return
                except Exception as e:
                    # Something went wrong, maybe print a better error
                    print(e)
                    await self.bot.say("Something went wrong :(")
                    return
                        
            try:
                # get number of wins
                self.ttsCur.execute("""Select count(player.name)
                                    from played
                                    join player on played.playerid = player.rowid
                                    join game on played.gameid = game.rowid
                                    where LOWER(player.name) like '%""" + player.lower() + """%'
                                        AND LOWER(game.name) like '%""" + gameName + """%'
                                        AND played.rank = 1
                                        AND played.iscoop = 'False'
                                    group by player.name""")

                wins = int(self.ttsCur.fetchone()[0])
            except:
                wins = 0
                
            s = "```Spieler '" + player + "' hat " + str(wins) + " Siege"
            if gameName != "":
                s += " im Spiel '" + gameName + "'"
            s += "```"
            await self.bot.say(s)

    @commands.command()
    async def updatetabletop(self, delete : bool = False, create : bool = False):
        """Updatet die Tabletop Datenbank"""
        try:
            global ttsCur
            global ttsConn
            await self.bot.say("Updating Tabletop Database ...")
            #self.ttsCur.close()
            #self.ttsConn.close()
            tts = sheets.Tabletop(delete, create, True, self.ttsConn)
            tts.update_database()
            await self.bot.say("Update finished!")
        except Exception as e:
            print(e)
            await self.bot.say("Error, check log :robot:")
            
        try:
            self.ttsConn = sqlite3.connect('db/tabletop.db')
            self.ttsCur = self.ttsConn.cursor()
        except Exception as e:
            print(e)