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

    def formatGifWithId(self, id : int):
        self.gifsCur.execute("""SELECT url, game, comment, addedBy, ROWID from gifs
                                WHERE ROWID = %s""" % (id))
        row = self.gifsCur.fetchone()
        return self.formatGif(row[0], row[1], row[2], row[3], row[4])
        
    def formatGif(self, url, game, comment, addedBy, id):
        outStr = '```ml\n'
        if(comment != ""):
            outStr += '#%d: "%s"\n' % (id, comment)
        else:
            outStr += '#%d \n' % (id)
        
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
                                            OR id1 = %s""" % (id, id)):
            if comboRow[0] == id:
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