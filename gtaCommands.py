import discord
import sqlite3
from discord.ext import commands
import strawpoll
import asyncio
import datetime
import sheets
import logging
import os
import random

class Gta(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.gtaConn = sqlite3.connect('db/gta.db')
        self.gtaCur = self.gtaConn.cursor()
        self.logger = logging.getLogger('bot')

    @commands.command()
    async def gtavehicles(self, ctx, vehicle : str = ""):
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
        foundVehicle = False
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
            foundVehicle = True
        s += '```'
        if not foundVehicle:
            s = 'Das Fahrzeug \"' + vehicle + '\" wurde noch nie gefahren'
        await ctx.send(s)

    async def rammertest(self):
        outChan = "gta5"
        voiceChan = "GTA 5"
        for channel in self.bot.get_all_channels():
            if(channel.guild.name == "Unterwasserpyromanen" and outChan == channel.name):
                chan = channel
        for channel in self.bot.get_all_channels():
            if(channel.guild.name == "Unterwasserpyromanen" and voiceChan in channel.name):
                #await chan.send("rammer test")
                #####
                """Startet einen Strawpoll Vote für den Rammer des Tages. Verwendet werden dafür alle User des angegebenen Voicechannels"""
                now = datetime.datetime.now()
                api = strawpoll.API()
                options = []
                nicknameMapping = {}
                fairGefahrenStr = "Alle sind fair gefahren ☺"
                extraOptions = ""
                hours = 2
                if "," in extraOptions:
                    for o in extraOptions.split(","):
                        options.append(o)
                elif extraOptions != "":
                    options.append(extraOptions)
                
                #for channel in ctx.guild.channels:
                #    if chan in channel.name: 
                for member in channel.members:
                    name = str(member).split("#")[0]
                    options.append(name)
                    nicknameMapping[name] = member
                print(options)
                if len(options) >= 1:  
                    options.append(fairGefahrenStr)
                    poll = strawpoll.Poll("Rammer des Tages " + now.strftime("%Y-%m-%d"), options)
                    poll.multi = True
                    poll = await api.submit_poll(poll)
                    await chan.send(file=discord.File("media/RammerDesTages.png"))
                    #await ctx.send("Jetzt Abstimmen für den Rammer des Tages!")
                    await chan.send(poll.url)
                    
                    ####
                    try:
                        for c in self.bot.get_all_channels():
                            if(c.guild.name == "Unterwasserpyromanen" and "GTA 5" in c.name):
                                vc = await c.connect()
                                await asyncio.sleep(5)
                                rammersoundspath = '/home/pi/workspace/AllstarBot/media/rammerdestages'
                                rammersounds = []
                                # r=root, d=directories, f = files
                                for r, d, f in os.walk(rammersoundspath):
                                    for file in f:
                                        rammersounds.append(file)
                                rammersoundfile = random.choice(rammersounds)
                                vc.play(discord.FFmpegPCMAudio(rammersoundspath+'/'+rammersoundfile), after=lambda e: print('done', e))
                                while vc.is_playing():
                                    await asyncio.sleep(5)
                                # disconnect after the player has finished
                                vc.stop()
                                await vc.disconnect()
                    except Exception as e:
                        self.logger.error("fehler beim Rammer des Tages")
                        self.logger.error(str(e))
                    ####
                    
                    # log poll url into a file
                    with open("polls.txt", "a") as pollfile:
                        pollfile.write(poll.url)
                        pollfile.write("\n")
                        if(hours > 0 and hours <= 24):
                            self.logger.info("waiting for " + str(3600 * hours) + " seconds for vote end")
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
                                await chan.send("OH MEIN GOTT! Diesmal sind alle fair gefahren! :tada: ")
                            elif(printWonder and numberOfWinners > 0):
                                gratulateMsg += ". Es gab auch " + str(votes) + " Stimmen, dass alle fair gefahren sind :thumbsup:"
                                await chan.send(gratulateMsg)
                            else:
                                await chan.send(gratulateMsg)
                else:
                    await chan.send("Konnte die Umfrage nicht anlegen. Zu wenige Leute im Channel " + chan.name)
                #####
                # todo: rammerdestages funktion umbauen, damit sie von hier aus aufgerufen werden kann

    @commands.command()
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
        
        for channel in ctx.guild.channels:
            if chan in channel.name: 
                for member in channel.members:
                    name = str(member).split("#")[0]
                    options.append(name)
                    nicknameMapping[name] = member
        if len(options) >= 2:  
            options.append(fairGefahrenStr)
            poll = strawpoll.Poll("Rammer des Tages " + now.strftime("%Y-%m-%d"), options)
            poll.multi = True
            poll = await api.submit_poll(poll)
            await ctx.send(file=discord.File("media/RammerDesTages.png"))
            #await ctx.send("Jetzt Abstimmen für den Rammer des Tages!")
            await ctx.send(poll.url)
            
            ####
            try:
                for c in self.bot.get_all_channels():
                    if(c.guild.name == "Unterwasserpyromanen" and "GTA 5" in c.name):
                        vc = await c.connect()
                        await asyncio.sleep(5)
                        rammersoundspath = '/home/pi/workspace/AllstarBot/media/rammerdestages'
                        rammersounds = []
                        # r=root, d=directories, f = files
                        for r, d, f in os.walk(rammersoundspath):
                            for file in f:
                                rammersounds.append(file)
                        rammersoundfile = random.choice(rammersounds)
                        vc.play(discord.FFmpegPCMAudio(rammersoundspath+'/'+rammersoundfile), after=lambda e: print('done', e))
                        while vc.is_playing():
                            await asyncio.sleep(5)
                        # disconnect after the player has finished
                        vc.stop()
                        await vc.disconnect()
            except Exception as e:
                self.logger.error("fehler beim Rammer des Tages")
                self.logger.error(str(e))
            ####
            
            # log poll url into a file
            with open("polls.txt", "a") as pollfile:
                pollfile.write(poll.url)
                pollfile.write("\n")
                if(hours > 0 and hours <= 24):
                    self.logger.debug("waiting for " + str(3600 * hours) + " seconds")
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
                        await ctx.send("OH MEIN GOTT! Diesmal sind alle fair gefahren! :tada: ")
                    elif(printWonder and numberOfWinners > 0):
                        gratulateMsg += ". Es gab auch " + str(votes) + " Stimmen, dass alle fair gefahren sind :thumbsup:"
                        await ctx.send(gratulateMsg)
                    else:
                        await ctx.send(gratulateMsg)
        else:
            await ctx.send("Konnte die Umfrage nicht anlegen. Zu wenige Leute im Channel " + chan)

    @commands.command()
    async def gtaracewins(self, ctx, player : str = None):
        """Anzahl der Rennsiege eines Spielers"""
        #Returns the number of race wins of a player
        if player == None:
            await ctx.send('```!gtaracewins <player>```')
        else:
            self.gtaCur.execute("""Select COALESCE(count(*),0), player.name
                            from raced
                            join player on player.rowid = raced.playerid
                            where rank = 1 AND
                                LOWER(player.name) like '%""" + player + """%'""")
            row = self.gtaCur.fetchone()
            await ctx.send('```cs\nSpieler "%s" hat %s Rennen gewonnen.```' % (row[1], row[0]))

    @commands.command()
    async def gtaplaylistwins(self, ctx):
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
        await ctx.send(s)

    @commands.command()
    async def gtaplaylist(self, ctx, playlist : str = ""):
        """Ergebnisse einer bestimmten Playliste"""
        
        if playlist == "":
            await ctx.send("```!gtaplaylist <playlist>```")
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
            await ctx.send(s)

    @commands.command()
    async def gtaplayerstatsfull(self, ctx, player : str):
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
                await ctx.author.send(s)
                s = "```ml\n"
                i= 0
        if(i != 0):
            s += "```"
            await ctx.author.send(s)
            await ctx.send(ctx.author.mention + "Resultate übermittelt :envelope_with_arrow: ")
        elif(emptyResult == True):
            await ctx.send(ctx.author.mention + "Keine Statistik für Spieler " + player + " gefunden.")


    @commands.command()
    async def gtaplayerstats(self, ctx, player : str):
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

        await ctx.send(embed=embed)

    @commands.command()
    async def updategta(self, ctx, delete : bool = False, create : bool = False):
        """Updatet die GTA Datenbank"""
        try:
            global gtaCur
            global gtaConn
            await ctx.send("Updating Gta Database ...")
            #gtaCur.close()
            #gtaConn.close()
            gta = sheets.Gtasheet(delete, create, True, self.gtaConn)
            gta.update_database()
            await ctx.send("Update finished!")
        except Exception as e:
            self.logger.error(e)
            await ctx.send("Error, check log :robot:")

        try:
            self.gtaConn = sqlite3.connect('db/gta.db')
            self.gtaCur = self.gtaConn.cursor()
        except Exception as e:
            self.logger.error(e)

    @commands.command()
    async def pointezeit(self, ctx, time = ""):
        userPointe = discord.utils.get(self.bot.get_all_members(), id=368113080741265408)
        msg = "Juhu, "
        if userPointe == None:
            msg += "Pointeblanc"
        else:
            msg += userPointe.mention
        msg += " ist hier! Jetzt geht die Party ab!"
        await ctx.send(msg) 
        for channel in self.bot.get_all_channels():
            if(channel.guild.name == "Unterwasserpyromanen" and "GTA 5" in channel.name):
                try:
                    vc = await channel.connect()
                    vc.play(discord.FFmpegPCMAudio('/home/pi/workspace/AllstarBot/media/pointeblanc_1.mp3'), after=lambda e: print('done', e))
                    while vc.is_playing():
                        await asyncio.sleep(3)
                    # disconnect after the player has finished
                    vc.stop()
                    await vc.disconnect()
                except Exception as e:
                    self.logger.error(e)

    @commands.command()
    async def gtaplayerlist(self, ctx):
        outStr = "Folgende Spieler haben bereits am GTA Donnerstag teilgenommen: "
        for row in self.gtaCur.execute("""Select distinct name from player"""):
            outStr += row[0] + ", "
        outStr = outStr[:-2] # remove last comma
        await ctx.send(outStr)
        

    @commands.command()
    async def gta2018(self, ctx):
        await ctx.send("http://allstar-bot.com/gta2018/")