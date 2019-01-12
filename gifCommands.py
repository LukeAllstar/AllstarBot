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

class Gif:

    def __init__(self, bot):
        self.bot = bot
        self.gifsConn = sqlite3.connect('db/gifs.db')
        self.gifsCur = self.gifsConn.cursor()

    @commands.command(pass_context=True, aliases=["addGif", "addgyf", "addGyf"])
    async def addgif(self, ctx, url, game : str = "", comment : str = "", id : int = None):
        """Adds a gif to the database"""
        if url == None:
            await self.bot.say('```!addGif "<url>" "<game>" "<comment>"```')
        else:
            self.gifsCur.execute("""INSERT INTO gifs (url, game, comment, addedBy, addedOn) VALUES ('%s', '%s', '%s', '%s', current_timestamp)""" % (url, game, comment, ctx.message.author))
            lastid = self.gifsCur.lastrowid
            if id != None:
                self.gifsCur.execute("""Select ROWID from gifs where ROWID = %s""" % (id))
                row = self.gifsCur.fetchone()
                if row != None:
                    self.gifsCur.execute("""INSERT INTO comboGifs (id1, id2) VALUES (%d, %d)""" % (lastid, id))
                else:
                    await self.bot.say("Konnte kein Gif mit der id %d finden. Gif wurde **nicht** hinzugefügt!" % id)
                    return
            self.gifsConn.commit()
            # get the inserted gif and format it
            outMessage = self.formatGifWithId(lastid)
            try:
                await self.bot.delete_message(ctx.message)
                gifMsg = await self.bot.say(outMessage)
                # after sending the message update the entry to save the message id and the channel id
                self.gifsCur.execute("""UPDATE gifs SET messageId = '%s', channelId = '%s' WHERE ROWID = %s""" % (gifMsg.id, gifMsg.channel.id, lastid))
                self.gifsConn.commit()
            except discord.Forbidden as e:
                # when we don't have permissions to replace the message just print out a confirmation
                message = await self.bot.say("Gif hinzugefuegt")        
                await asyncio.sleep(6)
                await self.bot.delete_message(message)

    def formatGifWithId(self, gifid : int):
        self.gifsCur.execute("""SELECT url, game, comment, addedBy, ROWID from gifs
                                WHERE ROWID = %s""" % (gifid))
        row = self.gifsCur.fetchone()
        return self.formatGif(row[0], row[1], row[2], row[3], row[4])
        
    def formatGif(self, url, game, comment, addedBy, gifid):
        outStr = '```ml\n'
        if(comment != ""):
            outStr += '#%d: "%s"\n' % (gifid, comment)
        else:
            outStr += '#%d \n' % (gifid)
        
        if(game != ""):
            outStr += "Spiel: " + game + "\n" 
        if(addedBy != ""):
            title = ['Dr. ', 'Meister ', 'Sir ', 'Mr. ', 'Lady ', 'Senor ', 'Der ', 'Das ', 'Die ', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
            # addedBy contains discord userid like Pacman#1234
            outStr += "Von " + random.choice(title) + addedBy.split("#")[0]
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
                outStr += '\n```ml\n'
                outStr += 'Das ist ein Combo Gif!\n'
                outStr += 'Von: %s\n' % comboGif[2].split("#")[0]
                outStr += '#%d: "%s"' % (comboId, comboGif[1])
                outStr += '```'
                outStr += comboGif[0]
        return outStr
            
    @commands.command(aliases=["gifs", "showgif", "gyf"])
    async def gif(self, search : str = ""):
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
            outStr = self.formatGif(row[0], row[1], row[2], row[3], row[4])
            
            msg = await self.bot.say(outStr)
            if(row[5] != None and row[6] != None):
                await self.addReactions(msg, row[5], row[6])
        else:
            await self.bot.say("Kein Gif zu '%s' gefunden.\nStattdessen gibt es :cake:." % search)        

    @commands.command()
    async def gifstats(self):
        self.gifsCur.execute("""Select count(*) from gifs""")
        row = self.gifsCur.fetchone()
        
        s = '```ml\n'
        s += "Anzahl an Gifs: %s\n\n" % row[0]
        s += "| {:<30.29}| {:8s}|\n".format("User","Anzahl")
        s += ('-' * 43)
        s += "\n"
        for row in self.gifsCur.execute("""SELECT addedBy, count(*)
                            from gifs
                            group by addedBy
                            order by 2 desc"""):
            s += "| {:<30.29}| {:<8}|\n".format(row[0].split("#")[0], row[1])
        s += '```\n'
        s += '```ml\n'
        s += "| {:<30.29}| {:8s}|\n".format("Spiel","Anzahl")
        s += ('-' * 43)
        s += "\n"
        for row in self.gifsCur.execute("""SELECT game, count(*)
                            from gifs
                            group by game
                            order by 2 desc"""):
            s += "| {:<30.29}| {:<8}|\n".format(row[0].split("#")[0], row[1])
        s += '```'
        await self.bot.say(s)
        
    @commands.command(aliases=["addcombo", "addcombogif"])
    async def combogif(self, id1 : int, id2 : int):
        # verify that both ids exist
        self.gifsCur.execute("""Select ROWID from gifs where ROWID = %s""" % (id1))
        row = self.gifsCur.fetchone()
        if row == None:
            notfound = True
            
        self.gifsCur.execute("""Select ROWID from gifs where ROWID = %s""" % (id2))
        row = self.gifsCur.fetchone()
        if row == None:
            notfound = True
            
        self.gifsCur.execute("""INSERT INTO comboGifs (id1, id2) VALUES (%d, %d)""" % (id1, id2))
        self.gifsConn.commit()
        await self.bot.say("Gifs #%s und #%s wurden zu einem ComboGif vereint :yin_yang: " % (id1, id2))
        
    @commands.command(aliases=["listgifs", "listgif", "searchgifs"])
    async def searchgif(self, searchterm : str = ""):
        """Zeigt ein Gif aus der Datenbank an"""
        # Search for gifs and show a list
        foundgif = False
        initStr = '```ml\n'
        initStr += "Folgende Gifs wurden gefunden:\n"
        initStr += "| {:6}| {:<15s}| {:<45s}| {:<10s}\n".format("ID","Spieler","Name", "Spiel")
        initStr += ('-' * 84)
        initStr += "\n"
        outStr = initStr
        outStr = '```ml\n'
        outStr += "Folgende Gifs wurden gefunden:\n"
        outStr += "| {:6}| {:<15s}| {:<45s}| {:<10s}\n".format("ID","Spieler","Name", "Spiel")
        outStr += ('-' * 84)
        outStr += "\n"
        counter = 0
        for gif in self.gifsCur.execute("""Select game, comment, addedBy, ROWID from gifs
                                    where """ #LOWER(addedBy) like '%""" + searchterm.lower() + """%' OR 
                                        """LOWER(game) like '%""" + searchterm.lower() + """%' OR
                                        LOWER(comment) like '%""" + searchterm.lower() + """%'"""):
            outStr += "| {:6}| {:<15.16}| {:<45.44}| {:<10.10s}\n".format("#"+str(gif[3]), str(gif[2]).split("#")[0], str(gif[1]), str(gif[0]))
            foundgif = True
            counter += 1
            if(counter % 20 == 0):
                outStr += '```'
                await self.bot.whisper(outStr)
                outStr = initStr
        outStr += '```'
        if(foundgif):
            if(counter <= 7):
                await self.bot.say(outStr)
            else:
                await self.bot.reply("Resultate übermittelt :envelope_with_arrow: ")
                await self.bot.whisper(outStr)
        else:
            await self.bot.say("Kein Gif zu '" + searchterm + "' gefunden :sob:")
        
    @commands.command(pass_context=True)
    async def deletegif(self, ctx, id):
        """Löscht ein Gif mit der angegebenen ID. Kann nur vom ersteller gelöscht werden."""
        self.gifsCur.execute("""Select addedBy, url, messageId, channelId from gifs
                            where ROWID = """ + id)
        row = self.gifsCur.fetchone()
        
        if(row != None):
            if(str(ctx.message.author) == str(row[0])):
                # delete original message if possible
                if(row[2] != None and row[3] != None):
                    print("deleting message")
                    channel = discord.utils.get(self.bot.get_all_channels(), id=row[3])
                    origMsg = await self.bot.get_message(channel, row[2])
                    await self.bot.delete_message(origMsg)
                    print("deleted message")
            
                # TODO: combo gifs löschen
                self.gifsCur.execute("""Delete from gifs
                                    where ROWID = """ + id)
                self.gifsConn.commit()
                with open("deletedgifs.txt", "a") as pollfile:
                    pollfile.write("Deleting gif #" + row[0] + " - " + row[1])
                    pollfile.write("\n")
                await self.bot.say("Gif #" + id + " gelöscht :put_litter_in_its_place: ")
                
            else:
                await self.bot.say(":no_entry_sign: " + ctx.message.author.mention + " Du bist nicht berechtigt Gif #" + id +" zu löschen :no_entry_sign:")
        else:
            self.bot.say("Gif mit der ID #" + id + " nicht gefunden.")

    async def addReactions(self, msg, origMsgId, channelId):
        channel = discord.utils.get(self.bot.get_all_channels(), id=channelId)
        origMsg = await self.bot.get_message(channel, origMsgId)
        for reaction in origMsg.reactions:
            try:
                await self.bot.add_reaction(msg, reaction.emoji)
            except:
                print("unknown reaction: " + str(reaction.emoji))


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
        
        # find the gif of the current week
        for gif in self.gifsCur.execute("""Select game, comment, addedBy, date(addedOn), messageId, channelId, ROWID, url """ +
                        """from gifs """+
                        """where date(addedOn) >  date(date('now', '-2 day'), '-1 month')"""):
            if(gif[4] != None and gif[5] != None):
                gifChannel = discord.utils.get(self.bot.get_all_channels(), id=gif[5])
                cache_msg = await self.bot.get_message(gifChannel, gif[4])
                reactionCount = 0
                for reaction in cache_msg.reactions:
                    if(reaction.emoji == '👍'):
                        if(reaction.count > mostVotes):
                            gifsOfTheWeek = []
                            mostVotes = reaction.count
                        
                        if(reaction.count == mostVotes):
                            gifsOfTheWeek.append(gif)
                    #print("message: " + str(cache_msg) + " - #reactions: " + str(len(cache_msg.reactions)) + " - reactions: ") 
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
            if(channel.server.name in postTo):
                # find the correct channel
                if(postTo[channel.server.name] == channel.name):
                    await self.bot.send_message(channel, "**GIF DES MONATS**")
                    if(msg != ""):
                        await self.bot.send_message(channel, msg)

                    # Gif of the Month (most upvotes)
                    await self.bot.send_message(channel, "Das Gif des Monats mit "+ str(mostVotes) +" 👍 ist Gif #"+str(gifOfTheWeek[6]))
                    gifMsg = self.formatGifWithId(gifOfTheWeek[6])
                    gotmMsg = await self.bot.send_message(channel, gifMsg)
                    await self.addReactions(gotmMsg, gifOfTheWeek[4], gifOfTheWeek[5])
                    mostReactionsWinner=mostReactionsOTM[0]
                    # Most Reactions
                    await self.bot.send_message(channel, "Das Gif mit den meisten Reaktionen des Monats ist Gif #"+str(mostReactionsWinner[6]) + " mit " + str(mostReactions) + " Reaktionen!")
                    gifMsg = self.formatGifWithId(mostReactionsWinner[6])
                    mostReactionsMsg = await self.bot.send_message(channel, gifMsg)
                    await self.addReactions(mostReactionsMsg, mostReactionsWinner[4], mostReactionsWinner[5])