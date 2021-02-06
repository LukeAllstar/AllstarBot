import discord
from discord.ext import commands
import json
import sqlite3
import random
import datetime
import locale
import sheets
import os
import setup
import strawpoll
import asyncio
import aiohttp
import datetime
import logging

class Gif(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.gifsConn = sqlite3.connect('db/gifs.db')
        self.gifsCur = self.gifsConn.cursor()
        self.logger = logging.getLogger('bot')

    @commands.command(aliases=["addGif", "addgyf", "addGyf"])
    async def addgif(self, ctx, url, game : str = "", comment : str = "", id : int = None):
        """Adds a gif to the database"""
        if url == None:
            await ctx.send('```!addGif "<url>" "<game>" "<comment>"```')
        else:
            self.logger.debug(ctx.author)
            self.logger.debug(ctx.author.name)
            self.logger.debug(ctx.author.id)
            self.gifsCur.execute("""INSERT INTO gifs (url, game, comment, addedBy, addedOn) VALUES (?, ?, ?, ?, current_timestamp)""", (url, game, comment, ctx.author.id))
            lastid = self.gifsCur.lastrowid
            if id != None:
                self.gifsCur.execute("""Select ROWID from gifs where ROWID = %s""" % (id))
                row = self.gifsCur.fetchone()
                if row != None:
                    self.gifsCur.execute("""INSERT INTO comboGifs (id1, id2) VALUES (%d, %d)""" % (lastid, id))
                else:
                    await ctx.send("Konnte kein Gif mit der id %d finden. Gif wurde **nicht** hinzugefügt!" % id)
                    return
            self.gifsConn.commit()
            # get the inserted gif and format it
            outMessage = await self.formatGifWithId(lastid)
            try:
                await ctx.message.delete()
                gifMsg = await ctx.send(outMessage)
                # default "upvote"
                await gifMsg.add_reaction('👍')
                # after sending the message update the entry to save the message id and the channel id
                self.gifsCur.execute("""UPDATE gifs SET messageId = '%s', channelId = '%s' WHERE ROWID = %s""" % (gifMsg.id, gifMsg.channel.id, lastid))
                self.gifsConn.commit()
            except discord.Forbidden as e:
                # when we don't have permissions to replace the message just print out a confirmation
                message = await ctx.send("Gif hinzugefuegt")        
                await asyncio.sleep(6)
                await message.delete()

    async def formatGifWithId(self, gifid : int):
        self.gifsCur.execute("""SELECT url, game, comment, addedBy, ROWID from gifs
                                WHERE ROWID = %s""" % (gifid))
        row = self.gifsCur.fetchone()
        return await self.formatGif(row[0], row[1], row[2], row[3], row[4])
        
    async def formatGif(self, url, game, comment, addedBy, gifid):
        outStr = '```ml\n'
        if(comment != ""):
            outStr += '#%d: "%s"\n' % (gifid, comment)
        else:
            outStr += '#%d \n' % (gifid)
        
        if(game != ""):
            outStr += "Spiel: " + game + "\n" 
        if(addedBy != ""):
            user = await self.bot.fetch_user(addedBy)
            title = ['Dr. ', 'Meister ', 'Sir ', 'Mr. ', 'Lady ', 'Senor ', 'Der ', 'Das ', 'Die ', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
            # addedBy contains discord userid like Pacman#1234
            outStr += "Von " + random.choice(title) + user.name
        outStr += '```'
        outStr += url
        
        # search for combo gifs
        for comboRow in self.gifsCur.execute("""Select id1, id2 from comboGifs
                                            where id2 = %s
                                            OR id1 = %s""" % (gifid, gifid)):
            if comboRow[0] == gifid:
                comboId = comboRow[1]
            else:
                comboId = comboRow[0]
            gifsCur2 = self.gifsConn.cursor()
            gifsCur2.execute("""Select url, comment, addedBy from gifs WHERE ROWID = %s """ % comboId)
            comboGif = gifsCur2.fetchone()
            if comboGif != None:
                user = await self.bot.fetch_user(int(comboGif[2]))
                outStr += '\n```ml\n'
                outStr += 'Das ist ein Combo Gif!\n'
                outStr += 'Von: %s\n' % user.name
                outStr += '#%d: "%s"' % (comboId, comboGif[1])
                outStr += '```'
                outStr += comboGif[0]
        return outStr
            
    @commands.command(aliases=["gifs", "showgif", "gyf"])
    async def gif(self, ctx, search : str = ""):
        """Zeigt ein Gif aus der Datenbank an.
        Wird ein Suchbegriff angegeben, wird zu diesem Begriff ein zufälliges Gif ausgewählt.
        Ist der Suchbegriff eine Zahl, wird das Gif mit der ID dieser Zahl ausgegeben.
        Wird kein Suchbegriff angegeben, wird ein zufälliges Gif angezeigt."""
        # Search for addedBy, game and comment
        try:
            # id suche
            id = int(search)
            self.gifsCur.execute("""SELECT url, game, comment, addedBy, ROWID, messageId, channelId from gifs
                            WHERE ROWID = """ + search)
        except ValueError:
            # string suche
            self.gifsCur.execute("""SELECT url, game, comment, addedBy, ROWID, messageId, channelId from gifs
                                WHERE ROWID IN
                                    (Select ROWID from gifs
                                        where """ #LOWER(addedBy) like '%"""+search.lower()+"""%' OR 
                                        """LOWER(game) like '%"""+search.lower()+"""%' OR
                                            LOWER(comment) like '%""" + search.lower() + """%'
                                        ORDER BY RANDOM() LIMIT 1)""")
        row = self.gifsCur.fetchone()
        
        if(row != None):
            outStr = await self.formatGif(row[0], row[1], row[2], row[3], row[4])
            
            msg = await ctx.send(outStr)
            if(row[5] != None and row[6] != None):
                await self.addReactions(msg, row[5], row[6])
        else:
            await ctx.send("Kein Gif zu '%s' gefunden.\nStattdessen gibt es :cake:." % search)        

    @commands.command(aliases=["gifstat"])
    async def gifstats(self, ctx):
        self.gifsCur.execute("""Select count(*) from gifs""")
        row = self.gifsCur.fetchone()
        self.logger.info("gifstats anzahl gifs: " + str(row[0]))
        
        s = '```ml\n'
        s += "Anzahl an Gifs: " + str(row[0]) + "\n\n"
        s += "| {:<30.29}| {:8s}|\n".format("User","Anzahl")
        s += ('-' * 43)
        s += "\n"
        count = 0
        othersCount = 0
        for row in self.gifsCur.execute("""SELECT addedBy, count(*)
                            from gifs
                            group by addedBy
                            order by 2 desc"""):
            count += 1
            self.logger.info("gifstats " + row[0] + " - " + str(row[1]))
            if(count <= 10):
                user = await self.bot.fetch_user(int(row[0]))
                self.logger.info("gifstats " + str(user.name))
                s += "| {:<30.29}| {:<8}|\n".format(user.name, row[1])
            else:
                othersCount += int(row[1])
            
        if(othersCount > 0):
            s += "| {:<30.29}| {:<8}|\n".format("Restliche", othersCount)
        
        s += '```\n'
        s += '```ml\n'
        s += "| {:<30.29}| {:8s}|\n".format("Spiel","Anzahl")
        s += ('-' * 43)
        s += "\n"

        count = 0
        othersCount = 0
        for row in self.gifsCur.execute("""SELECT game, count(*)
                            from gifs
                            group by game
                            order by 2 desc"""):
            count += 1
            self.logger.info("gifstats " + str(row[0]) + " - " + str(row[1]))
            if(count <= 10):
                s += "| {:<30.29}| {:<8}|\n".format(row[0].split("#")[0], row[1])
            else:
                othersCount += int(row[1])

        if(othersCount > 0):
            s += "| {:<30.29}| {:<8}|\n".format("Restliche", othersCount)       

        s += '```'
        await ctx.send(s)
        
    @commands.command(aliases=["addcombo", "addcombogif"])
    async def combogif(self, ctx, id1 : int, id2 : int):
        # verify that both ids exist
        self.gifsCur.execute("""Select ROWID from gifs where ROWID = %s""" % (id1))
        row = self.gifsCur.fetchone()
        if(row == None):
            notfound = True
            
        self.gifsCur.execute("""Select ROWID from gifs where ROWID = %s""" % (id2))
        row = self.gifsCur.fetchone()
        if(row == None):
            notfound = True
            
        if(notfound):
            await ctx.send("Keine Gifs zu den beiden IDs gefunden" % (id1, id2))
        else:
            self.gifsCur.execute("""INSERT INTO comboGifs (id1, id2) VALUES (%d, %d)""" % (id1, id2))
            self.gifsConn.commit()
            await ctx.send("Gifs #%s und #%s wurden zu einem ComboGif vereint :yin_yang: " % (id1, id2))



    @commands.command(aliases=["listgifs", "listgif", "searchgifs"])
    async def searchgif(self, ctx, searchterm : str = ""):
        await ctx.send("Die Gif Suche findest du hier: https://www.allstar-bot.com/bot/gifsearch/ :robot:")
         
    #@commands.command(aliases=["listgifs", "listgif", "searchgifs"])
    #async def searchgif(self, ctx, searchterm : str = ""):
    #    """Zeigt ein Gif aus der Datenbank an"""
    #    # Search for gifs and show a list
    #    foundgif = False
    #    initStr = '```ml\n'
    #    initStr += "Folgende Gifs wurden gefunden:\n"
    #    initStr += "| {:6}| {:<15s}| {:<45s}| {:<10s}\n".format("ID","Spieler","Name", "Spiel")
    #    initStr += ('-' * 84)
    #    initStr += "\n"
    #    outStr = initStr
    #    outStr = '```ml\n'
    #    outStr += "Folgende Gifs wurden gefunden:\n"
    #    outStr += "| {:6}| {:<15s}| {:<45s}| {:<10s}\n".format("ID","Spieler","Name", "Spiel")
    #    outStr += ('-' * 84)
    #    outStr += "\n"
    #    counter = 0
    #    for gif in self.gifsCur.execute("""Select game, comment, addedBy, ROWID from gifs
    #                                where """ #LOWER(addedBy) like '%""" + searchterm.lower() + """%' OR 
    #                                    """LOWER(game) like '%""" + searchterm.lower() + """%' OR
    #                                    LOWER(comment) like '%""" + searchterm.lower() + """%'"""):
    #        outStr += "| {:6}| {:<15.16}| {:<45.44}| {:<10.10s}\n".format("#"+str(gif[3]), str(gif[2]).split("#")[0], str(gif[1]), str(gif[0]))
    #        foundgif = True
    #        counter += 1
    #        if(counter % 20 == 0):
    #            outStr += '```'
    #            await ctx.author.send(outStr)
    #            outStr = initStr
    #    outStr += '```'
    #    if(foundgif):
    #        if(counter <= 7):
    #            await ctx.send(outStr)
    #        else:
    #            await ctx.send(ctx.author.mention + "Resultate übermittelt :envelope_with_arrow: ")
    #            await ctx.author.send(outStr)
    #    else:
    #        await ctx.send("Kein Gif zu '" + searchterm + "' gefunden :sob:")
        
    @commands.command()
    async def deletegif(self, ctx, id):
        """Löscht ein Gif mit der angegebenen ID. Kann nur vom ersteller gelöscht werden."""
        self.gifsCur.execute("""Select addedBy, url, messageId, channelId from gifs
                            where ROWID = """ + id)
        row = self.gifsCur.fetchone()
        
        if(row != None):
            if(str(ctx.author.id) == str(row[0])):
                # delete original message if possible
                if(row[2] != None and row[3] != None):
                    self.logger.info("deleting message - " + str(row[0]) + ", " + str(row[2]) + ", " + str(row[3]))
                    channel = discord.utils.get(self.bot.get_all_channels(), id=int(row[3]))
                    origMsg = await channel.fetch_message(int(row[2]))
                    await origMsg.delete()
                    self.logger.debug("deleted message")
            
                self.gifsCur.execute("""Delete from gifs
                                    where ROWID = """ + id)
                self.gifsConn.commit()
                # remove Combogif
                # TODO: recursive?
                self.gifsCur.execute("""Delete from comboGifs
                                    where id1 = """ + id + """
                                    OR id2 = """ + id)
                self.gifsConn.commit()
                with open("deletedgifs.txt", "a") as pollfile:
                    pollfile.write("Deleting gif #" + row[0] + " - " + row[1])
                    pollfile.write("\n")
                await ctx.send("Gif #" + id + " gelöscht :put_litter_in_its_place: ")
                
            else:
                await ctx.send(":no_entry_sign: " + ctx.author.mention + " Du bist nicht berechtigt Gif #" + id +" zu löschen :no_entry_sign:")
        else:
            ctx.send("Gif mit der ID #" + id + " nicht gefunden.")

    async def addReactions(self, msg, origMsgId, channelId):
        channel = discord.utils.get(self.bot.get_all_channels(), id=int(channelId))
        origMsg = await channel.fetch_message(int(origMsgId))
        for reaction in origMsg.reactions:
            try:
                await msg.add_reaction(reaction.emoji)
            except:
                self.logger.error("error in addReactions for reaction: " + str(reaction.emoji))


    async def gifOfTheMonth(self):
        """ posts the gif with the most upvotes to some predefined channels """
        postTo = {}
        # this is hardcoded atm. maybe i'll move this to a config file in the future .. but probably not
        postTo["Lukes Playground"] = "test"
        postTo["Unterwasserpyromanen"] = "bot-ecke"
        gifsOfTheWeek = []
        gifOfTheWeek = []
        mostReactionsOTM = []
        mostVotes = 0
        mostReactions = 0
        self.logger.debug("searching for the gif of the month")
        # find the gif of the current week
        for gif in self.gifsCur.execute("""Select game, comment, addedBy, date(addedOn), messageId, channelId, ROWID, url """ +
                        """from gifs """+
                        """where date(addedOn) >  date(date('now', '-3 day'), '-1 month')"""):
            if(gif[4] != None and gif[5] != None):
                gifChannel = discord.utils.get(self.bot.get_all_channels(), id=int(gif[5]))
                try:
                    cache_msg = await gifChannel.fetch_message(int(gif[4]))
                except:
                    self.logger.error("can't read gif id " + str(gif[5]) + ".")
                    continue
                reactionCount = 0
                for reaction in cache_msg.reactions:
                    if(reaction.emoji == '👍'):
                        if(reaction.count > mostVotes):
                            gifsOfTheWeek = []
                            mostVotes = reaction.count
                        
                        if(reaction.count == mostVotes):
                            gifsOfTheWeek.append(gif)
                    #self.logger.debug("message: " + str(cache_msg) + " - #reactions: " + str(len(cache_msg.reactions)) + " - reactions: ") 
                    reactionCount += reaction.count
                if(reactionCount > mostReactions):
                    mostReactionsOTM = []
                    mostReactions = reactionCount
                if(reactionCount == mostReactions):
                    mostReactionsOTM.append(gif)
        
        msg = ""
        if(len(gifsOfTheWeek) == 0):
            msg = "Dieses mal gibt es leider kein Gif des Monats :("
        if(len(gifsOfTheWeek) > 1):
            gifOfTheWeek = random.choice(gifsOfTheWeek)

            msg="Diesen Monat gab es einen Gleichstand zwischen den Gifs "
            first = True
            for gif in gifsOfTheWeek:
                if(first):
                    first = False
                else:
                    msg += ", "
                msg += "#"+str(gif[6])
        else:
            gifOfTheWeek = gifsOfTheWeek[0]

        with open("gifsOfTheMonth.txt", "a") as gotwfile:
            gotwfile.write(datetime.datetime.today().date().isoformat())
            gotwfile.write(":")
            if(len(gifOfTheWeek) > 0):
                gotwfile.write(str(gifOfTheWeek[6]))
            else:
                gotwfile.write("none")
            gotwfile.write("\n")
            
        # now post it to every channel that was configured
        for channel in self.bot.get_all_channels():
            if(channel.guild.name in postTo):
                # find the correct channel
                if(postTo[channel.guild.name] == channel.name):
                    await channel.send("**GIF DES MONATS**")
                    if(msg != ""):
                        await channel.send(msg)

                    # Gif of the Month (most upvotes)
                    await channel.send("Das Gif des Monats mit "+ str(mostVotes) +" 👍 ist Gif #"+str(gifOfTheWeek[6]))
                    gifMsg = await self.formatGifWithId(gifOfTheWeek[6])
                    gotmMsg = await channel.send(gifMsg)
                    await self.addReactions(gotmMsg, gifOfTheWeek[4], gifOfTheWeek[5])
                    mostReactionsWinner=mostReactionsOTM[0]
                    # Most Reactions
                    await channel.send("Das Gif mit den meisten Reaktionen des Monats ist Gif #"+str(mostReactionsWinner[6]) + " mit " + str(mostReactions) + " Reaktionen!")
                    gifMsg = await self.formatGifWithId(mostReactionsWinner[6])
                    mostReactionsMsg = await channel.send(gifMsg)
                    await self.addReactions(mostReactionsMsg, mostReactionsWinner[4], mostReactionsWinner[5])