import discord
import sqlite3
from discord.ext import commands
import strawpoll
import asyncio
import datetime
import sheets

class Gta:

    def __init__(self, bot):
        self.bot = bot
        self.gtaConn = sqlite3.connect('db/gta.db')
        self.gtaCur = self.gtaConn.cursor()

    @commands.command()
    async def gtavehicles(self, vehicle : str = ""):
        """Meistverwendesten Fahrzeuge"""
        #Returns top 7 used vehicles
        s = "```ml\n"
        if vehicle == "":
            s += "Die 7 meistverwendetsten Fahrzeuge\n"
            s += ('-' * 35)
            s += "\n"
            s += "| {:20s}| {:10s}|\n".format("Fahrzeug", "Anzahl")
            s += ('-' * 35)
            s += "\n"

        for row in self.gtaCur.execute("""Select vehicle, count(*) from (
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
                s += 'Das Fahrzeug "%s" wurde %s mal verwendet.\n' % (row[0], row[1])
        s += '```'
        await self.bot.say(s)

    @commands.command(pass_context=True)
    async def rammerdestages(self, ctx, chan:str = "GTA", extraOptions:str = "", hours : int = 2):
        """Startet einen Strawpoll Vote für den Rammer des Tages. Verwendet werden dafür alle User des angegebenen Voicechannels"""
        now = datetime.datetime.now()
        api = strawpoll.API()
        options = []
        nicknameMapping = {}
        fairGefahrenStr = "Alle sind fair gefahren ☺"
        if "," in extraOptions:
            for o in extraOptions.split(","):
                options.append(o)
        elif extraOptions != "":
            options.append(extraOptions)
        
        for channel in ctx.message.server.channels:
            if chan in channel.name: 
                for member in channel.voice_members:
                    name = str(member).split("#")[0]
                    options.append(name)
                    nicknameMapping[name] = member
        if len(options) >= 2:  
            options.append(fairGefahrenStr)
            poll = strawpoll.Poll("Rammer des Tages " + now.strftime("%Y-%m-%d"), options)
            poll.multi = True
            poll = await api.submit_poll(poll)
            await self.bot.upload("media/RammerDesTages.png")
            #await self.bot.say("Jetzt Abstimmen für den Rammer des Tages!")
            await self.bot.say(poll.url)
            # log poll url into a file
            with open("polls.txt", "a") as pollfile:
                pollfile.write(poll.url)
                pollfile.write("\n")
                if(hours > 0 and hours <= 24):
                    #print("waiting for " + str(3600 * hours) + " seconds")
                    await asyncio.sleep(3600*hours)
                    # retrieve poll and print the winner(s)
                    resultPoll = await api.get_poll(poll.url)
                    orderedResults = resultPoll.results()
                    i = 0
                    votes = orderedResults[0][1]
                    winners = []
                    printWonder = False
                    
                    while(len(orderedResults) > i and votes == orderedResults[i][1]):
                        winners.append(orderedResults[i][0])
                        i = i + 1
                    
                    numberOfWinners = len(winners)
                    if(fairGefahrenStr in winners):
                        numberOfWinners -= 1
                        printWonder = True
                    
                    if(numberOfWinners == 1):
                        gratulateMsg = "Der Rammer des Tages ist "
                    else:
                        gratulateMsg = "Die Rammer des Tages sind "
                    first = True
                    
                    for winner in winners:
                        if(not first):
                            if(numberOfWinners == 2):
                                gratulateMsg += " und "
                            else:
                                gratulateMsg += ", "
                    
                        if(winner == fairGefahrenStr):
                            printWonder = True
                        elif(winner in nicknameMapping):
                            gratulateMsg += nicknameMapping[winner].mention
                        else:
                            # not a user, might be and extra option
                            gratulateMsg += winner
                        first = False
                    gratulateMsg += " mit " + str(votes) + " Stimmen"
                    if(printWonder and numberOfWinners == 0):
                        await self.bot.say("OH MEIN GOTT! Diesmal sind alle fair gefahren! :tada: ")
                    elif(printWonder and numberOfWinners > 0):
                        gratulateMsg += ". Es gab auch " + str(votes) + " Stimmen, dass alle fair gefahren sind :thumbsup:"
                        await self.bot.say(gratulateMsg)
                    else:
                        await self.bot.say(gratulateMsg)
        else:
            await self.bot.say("Konnte die Umfrage nicht anlegen. Zu wenige Leute im Channel " + chan)

    @commands.command()
    async def gtaracewins(self,player : str = None):
        """Anzahl der Rennsiege eines Spielers"""
        #Returns the number of race wins of a player
        if player == None:
            await self.bot.say('```!gtaracewins <player>```')
        else:
            self.gtaCur.execute("""Select COALESCE(count(*),0), player.name
                            from raced
                            join player on player.rowid = raced.playerid
                            where rank = 1 AND
                                LOWER(player.name) like '%""" + player + """%'""")
            row = self.gtaCur.fetchone()
            await self.bot.say('```cs\nSpieler "%s" hat %s Rennen gewonnen.```' % (row[1], row[0]))

    @commands.command()
    async def gtaplaylistwins(self):
        """Listet welcher Spieler wieviele Playlisten gewonnen hat"""
        s = "```ml\n"
        s += "| {:20s}| {:8s}|\n".format("Spieler", "Siege")
        s += ('-' * 33)
        s += "\n"
        for row in self.gtaCur.execute("""
                        Select playername, count(playername) as wins
                        from playerstats
                        where rank = 1
                        group by playername
                        order by wins desc"""):
            s += '| {:20s}| {:8s}|\n'.format(str(row[0]), str(row[1]))
        s += '```'
        await self.bot.say(s)

    @commands.command()
    async def gtaplaylist(self, playlist : str = ""):
        """Ergebnisse einer bestimmten Playliste"""
        
        if playlist == "":
            await self.bot.say("```!gtaplaylist <playlist>```")
        else:
            s = "```ml\n"
            s += "Ergebnis Playlist %s\n\n" % playlist
            s += "| {:5}| {:20s}| {:6s}|\n".format("Rang","Spieler", "Punkte")
            s += ('-' * 38)
            s += "\n"
            rank = 1
            prevPoints = -1
            for row in self.gtaCur.execute("""
                            Select player.name, sum(points) as points from (
                                Select *,
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
                                    where playlist.name='"""+playlist+"""'
                                ) as x
                                join player on playerid = player.rowid
                                group by player.name
                                    order by points desc"""):
                if prevPoints == row[1]:
                    rankMod += 1
                else:
                    rankMod = 0
                s += "| {:5}| {:20s}| {:6s}|\n".format(str(rank-rankMod),str(row[0]), str(row[1]))
                prevPoints = row[1]
                rank += 1
            s += "```"
            await self.bot.say(s)

    @commands.command()
    async def gtaplayerstatsfull(self, player : str):
        """Alle Platzierungen in allen Playlisten eines Spielers.
        Der angegebene Name muss der Nickname aus GTA sein"""
        i = 0
        emptyResult = True
        s = "```ml\n"
        s += "Spieler Statistik für %s\n\n" % player
        s += "| {:10}| {:8s}| {:12s}|\n".format("Playlist", "Punkte", "Platzierung")
        s += ('-' * 37)
        s += "\n"
        for row in self.gtaCur.execute("""
                            with tt(playlistid, playlistname, playername, points) as (
                                                    Select playlistid, x.name as playlistname, player.name as playername, sum(points) as points from
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
                                                            order by playlistid asc, points desc)
                        Select s.playlistid, s.playlistname, s.playername, s.points, (
                                Select count(*)+1 
                                    from tt as my 
                                    where my.points > s.points and my.playlistid = s.playlistid) as rank
                        from tt as s
                                    where playername=lower('"""+player+"""')
                                    order by rank asc, points desc"""):
            s += "| {:10}| {:8s}| {:12s}|\n".format(str(row[1]), str(row[3]), str(row[4]))
            i += 1
            emptyResult = False
            if(i >= 15):
                s += "```"
                await self.bot.whisper(s)
                s = "```ml\n"
                i= 0
        if(i != 0):
            s += "```"
            await self.bot.whisper(s)
            await self.bot.reply("Resultate übermittelt :envelope_with_arrow: ")
        elif(emptyResult == True):
            await self.bot.reply("Keine Statistik für Spieler " + player + " gefunden.")


    @commands.command()
    async def gtaplayerstats(self, player : str):
        """Diverse Statistiken zu dem Spieler.
            Der angegebene Spieler muss so geschrieben sein, wie der GTA ingame Nickname."""
        first = True
        embed = discord.Embed(title="**Statistiken für " + player + "**", colour=discord.Colour(0xf59402), timestamp=datetime.datetime.utcnow())

        # Anzahl Playlisten
        for row in self.gtaCur.execute("""
                        Select count(*)
                        from playerstats
                        where playername = LOWER('"""+player+"""')"""):
            embed.add_field(name="Anzahl Playlisten", value="**"+str(row[0])+"**", inline=True)

        # Playlisten gewonnen
        for row in self.gtaCur.execute("""
                        Select count(*)
                        from playerstats
                        where playername = LOWER('"""+player+"""')
                        and rank = 1"""):
            embed.add_field(name="Playlisten gewonnen", value="**"+str(row[0])+"**", inline=True)

        # Anzahl Rennen
        for row in self.gtaCur.execute("""
                        Select count(*)
                        from player
                        join raced on player.ROWID = raced.playerid
                        where player.name = LOWER('"""+player+"""')"""):
            embed.add_field(name="Anzahl Rennen", value="**"+str(row[0])+"**", inline=True)

        # Rennen gewonnen
        for row in self.gtaCur.execute("""
                            Select COALESCE(count(*),0), player.name
                                from raced
                                join player on player.rowid = raced.playerid
                                where rank = 1 AND
                                        LOWER(player.name) like '%""" + player + """%'"""):
            embed.add_field(name="Rennen Gewonnen", value="**"+str(row[0])+"**", inline=True)

        # Beste Punktezahl
        mostPoints = 0
        mostPointsPlaylists = ""
        first = True
        for row in self.gtaCur.execute("""
                        Select playlistname, points
                        from playerstats
                        where playername = LOWER('"""+player+"""')
                        and points = (Select max(points) from playerstats where playername = LOWER('"""+player+"""'))"""):
            if(first):
                mostPoints = row[1]
            else:
                mostPointsPlaylists += ", "            
            mostPointsPlaylists += str(row[0])
            first = False
        embed.add_field(name="Meisten Punkte", value="**" + str(mostPoints) + "** (in ``" + mostPointsPlaylists + "``)", inline=True)
            
        # Schlechteste Punktezahl
        first = True
        leastPoints = 0
        leastPointsPlaylists = ""
        for row in self.gtaCur.execute("""
                        Select playlistname, points
                        from playerstats
                        where playername = LOWER('"""+player+"""')
                        and points = (Select min(points) from playerstats where playername = LOWER('"""+player+"""'))"""):
            if(first):
                leastPoints = row[1]
            else:
                leastPointsPlaylists += ", "            
            leastPointsPlaylists += str(row[0])
            first = False   
        embed.add_field(name="Wenigste Punkte", value="**" + str(leastPoints) + "** (in ``" + leastPointsPlaylists + "``)", inline=True)

        # Bester Rang
        for row in self.gtaCur.execute("""Select playername, count(playername) as wins
                        from playerstats
                        where rank = 1
                            AND playername = LOWER('"""+player+"""')
                        group by playername
                        order by wins desc"""):
            numberwins = row[1]

        first = True
        bestPlaylists = ""
        for row in self.gtaCur.execute("""
                        Select playlistname, rank
                        from playerstats
                        where playername = LOWER('"""+player+"""')
                        and rank = (Select min(rank) from playerstats where playername = LOWER('"""+player+"""'))"""):
            if(first):
                #s += "Bester Rang: "
                #s += str(row[1])
                #s += "\n    in diesen " + str(numberwins) + " Playlisten: "
                embed.add_field(name="Bester Rang", value="**"+str(row[1])+"**", inline=False)
            else:
                bestPlaylists += ", "            
            bestPlaylists += str(row[0])
            first = False
        embed.add_field(name="Bester Rang in diesen Playlisten", value ="``" + bestPlaylists + "``")
        
        # Schlechtester Rang
        worstPlaylists = ""
        first = True
        for row in self.gtaCur.execute("""
                        Select playlistname, rank
                        from playerstats
                        where playername = LOWER('"""+player+"""')
                        and rank = (Select max(rank) from playerstats where playername = LOWER('"""+player+"""'))"""):
            if(first):
                embed.add_field(name="Schlechtester Rang", value="**" + str(row[1]) + "** ", inline=False)
            else:
                worstPlaylists += ", "            
            worstPlaylists += str(row[0])
            first = False
        embed.add_field(name="Schlechtester Rang in diesen Playlisten", value ="``" + worstPlaylists + "``")

        await self.bot.say(embed=embed)

    @commands.command()
    async def updategta(self, delete : bool = False, create : bool = False):
        """Updatet die GTA Datenbank"""
        try:
            global gtaCur
            global gtaConn
            await self.bot.say("Updating Gta Database ...")
            #gtaCur.close()
            #gtaConn.close()
            gta = sheets.Gtasheet(delete, create, True, self.gtaConn)
            gta.update_database()
            await self.bot.say("Update finished!")
        except Exception as e:
            print(e)
            await self.bot.say("Error, check log :robot:")

        try:
            self.gtaConn = sqlite3.connect('db/gta.db')
            self.gtaCur = self.gtaConn.cursor()
        except Exception as e:
            print(e)
