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
import threading
import logging
from logging.handlers import TimedRotatingFileHandler
from gtaCommands import Gta
from tabletopCommands import Tabletop
from gifCommands import Gif
from aiohttp import web
from collections import defaultdict

# LOGGING
logger = logging.getLogger('bot')

log_format = "[%(levelname)-5.5s] %(asctime)s - %(message)s"
formatter = logging.Formatter(log_format)

logging.basicConfig(level=logging.INFO, format=log_format, datefmt='%d-%m-%y %H:%M:%S')
logname = "logs/allstar_bot.log"
handler = TimedRotatingFileHandler(logname, when="midnight", interval=2)
handler.suffix = "%Y%m%d"
handler.setFormatter(formatter)
logger.addHandler(handler)

OPUS_LIBS = ['libopus-0.x86.dll', 'libopus-0.x64.dll', 'libopus-0.dll', 'libopus.so.0', 'libopus.0.dylib']


def load_opus_lib(opus_libs=OPUS_LIBS):
    if discord.opus.is_loaded():
        return True

    for opus_lib in opus_libs:
        try:
            discord.opus.load_opus(opus_lib)
            return
        except OSError:
            pass

        raise RuntimeError('Could not load an opus lib. Tried %s' % (', '.join(opus_libs)))

load_opus_lib(OPUS_LIBS)

# BOT CONFIG
with open('config.json') as json_data_file:
    data = json.load(json_data_file)

if not os.path.exists('db/tabletop.db') or not os.path.exists('db/gta.db') or not os.path.exists('db/quotes.db') or not os.path.exists('db/gifs.db'):
    logger.info("Databases do not exist. Running setup!")
    setup.setup()

def token():
    '''Returns your token wherever it is'''
    if data.get('token') == "<token>":
        if not os.environ.get('TOKEN'):
            logger.error("Error retrieving token.")
            exit()
    else:
        token = data.get('token').strip('\"')
    return os.environ.get('TOKEN') or token
        
# DISCORD BOT
bot = commands.Bot(command_prefix=data["command_prefix"], description=data["description"])
# maybe usefull later:


# GIFS
gifs = Gif(bot)

# SQLITE
quotesConn = sqlite3.connect('db/quotes.db')
botConn = sqlite3.connect('db/bot.db') # general bot db -> quotes should be moved there to
quotesCur = quotesConn.cursor()
botCur = botConn.cursor()

@bot.event
async def on_ready():
    logger.info('Logged in as')
    logger.info(bot.user.name)
    logger.info(bot.user.id)
    logger.info('------')

# remove the default help command
bot.remove_command("help")

@bot.command()
async def help():
    await bot.reply("Die Hilfe für die Befehle findest du hier: http://allstar-bot.com/commands/")

#@bot.command
#async def help(category : str = ""):
#    helptext = "```"
#    category = category.lower()
#    if category == "":
#        helptext += "Bitte eine Kategorie angeben\n"
#        helptext += "!help <Kategorie>"
#        helptext += "Kategorien:"
#        helptext += "   tts"
#        helptext += "   gta"
#        helptext += "   general"
#    elif category == "tts":
#        helptext += "
#    elif category == "gta":
#    elif category == "general":
#    else:
#        
#    helptext += "```"

@bot.command(aliases=["zitat"])
async def quote(name : str = ""):
    """Zitat eines Communitymitglieds"""
    #Selects a random quote from the database.
    #If a name parameter is given it searches for a quote from that person
    quotesCur.execute("""SELECT quote, name from quotes 
                            WHERE ROWID IN
                                (Select ROWID from quotes
                                    where LOWER(name) like '%"""+name.lower()+"""%' 
                                    ORDER BY RANDOM() LIMIT 1)""")
    row = quotesCur.fetchone()
    if(row != None):
        await bot.say('>>> %s\n- %s' % (row[0], row[1]))
    else:
        await bot.say("Kein Zitat von '%s' gefunden.\nHier nimm ein :ice_cream: stattdessen." % name)

@bot.command(pass_context=True, aliases=["addzitat"])
async def addquote(ctx, quote : str = None, name : str = None):
    """Neues Zitat erstellen"""
    # Adds one quote to the database. Adds the person who issued the command to the table
    if quote == None or name == None:
        await bot.say('```!addquote "<quote>" "<name>"```')
    else:
        quotesCur.execute("""INSERT INTO quotes (quote, name, addedBy) VALUES ('%s', '%s', '%s')""" % (quote, name, ctx.message.author))
        quotesConn.commit()
        try:
            outMessage = '>>> ' # Discord Multiline Quote
            outMessage += quote
            outMessage += '\n'
            outMessage += '- ' + name
            await bot.delete_message(ctx.message)
            await bot.say("Neues Zitat von " + ctx.message.author.name + " hinzugefügt.")
            await bot.say(outMessage)
        except discord.Forbidden as e:
            await bot.say("Zitat hinzugefuegt")
        
@bot.command(pass_context=True)
async def friends(ctx):
    """Freunde!"""
    user = discord.utils.get(ctx.message.server.members, name = 'Lefty')
    await bot.say(":robot: My only friend is " + user.mention)
        

   
"""   
@bot.command(pass_context=True)
async def testupload(ctx, text):
    logger.debug(text)
    logger.debug(ctx.message)
    logger.debug(ctx.message.attachments)
    logger.debug(ctx.message.attachments[0]['url'])
    content = await get(ctx.message.attachments[0]['url'])
    write_to_file("media/audio/test.mp3", content)
    
    #urllib.request.urlretrieve(ctx.message.attachments[0]['url'], "media/audio/test.mp3")

# a helper coroutine to perform GET requests:
@asyncio.coroutine
def get(*args, **kwargs):
    response = yield from aiohttp.request('GET', *args, **kwargs)
    return (yield from response.read())
    
# get content and write it to file
def write_to_file(filename, content):
    f = open(filename, 'wb')
    f.write(content)
    f.close()
"""

@bot.command(aliases=["istesdonnerstag", "istheutedonnerstag", "istodaythursday"])
async def isitthursday():
    if(datetime.datetime.today().weekday() == 3):
        await bot.say("yes")
    else:
        await bot.say("no")

###########################
### Roles #################
###########################

@bot.command(pass_context=True, aliases=["joinrole"])
async def joingroup(ctx, *groups):
    member = ctx.message.author
    
    for group in groups:
        botCur.execute("""SELECT server, name from allowedroles 
                                WHERE server = '""" + member.server.name + """'
                                AND LOWER(name) = LOWER('""" + group + """')
                                """)
        row = botCur.fetchone()
        if(row != None):
            role = discord.utils.get(member.server.roles, name=row[1])
            await bot.add_roles(member, role)
            await bot.reply("Du wurdest zur Gruppe " + row[1] + " hinzugefügt!")
        else:
            await bot.reply("Die Gruppe '" + group + "' ist nicht erlaubt.")

@bot.command(pass_context=True, aliases=["leaverole"])
async def leavegroup(ctx, group):
    member = ctx.message.author
    botCur.execute("""SELECT server, name from allowedroles 
                            WHERE server = '""" + member.server.name + """'
                            AND LOWER(name) = LOWER('""" + group + """')
                            """)
    row = botCur.fetchone()
    if(row == None):
        await bot.reply("Diese Gruppe ist nicht erlaubt")
    elif(group.lower() in [y.name.lower() for y in member.roles]):
        role = discord.utils.get(member.server.roles, name=row[1])
        await bot.remove_roles(member, role)
        await bot.reply("Du wurdest aus der Gruppe " + row[1] + " entfernt!")
    else:
        await bot.reply("Du bist nicht in dieser Gruppe")
        
@bot.command(pass_context=True, aliases=["roles", "rollen", "gruppen"])
async def groups(ctx):
    member = ctx.message.author
    msg = "Du bist derzeit in folgenden Gruppen: \n"
    
    memberRoles = [y.name.lower() for y in member.roles]

    for group in botCur.execute("""SELECT name from allowedroles 
                                WHERE server = '""" + member.server.name + """'
                                """):
        if (group[0].lower() in memberRoles):
            msg += group[0]
            msg += ", "
    msg = msg[:-2] # remove last comma
    await bot.say(msg)

@bot.command(pass_context=True, aliases=["showmembers", "members"])
async def groupmembers(ctx, group = ""):
    if group == "":
        await bot.reply("Die Gruppen und die dazugehörigen Mitglieder findest du hier: http://allstar-bot.com/groupmembers/")
    else:
        # Mitglieder einer bestimmten Gruppe ausgeben
        member = ctx.message.author
        members = ctx.message.server.members
        memberList = []
        msg = "Derzeit sind folgende Personen in der Gruppe "

        botCur.execute("""SELECT server, name from allowedroles 
                                WHERE server = '""" + member.server.name + """'
                                AND LOWER(name) = LOWER('""" + group + """')
                                """)
        row = botCur.fetchone()
        if(row == None):
            await bot.reply("Diese Gruppe ist nicht erlaubt")
        else:
            # iterate through server members and check their roles
            for currentMember in members:
                memberRoles = [y.name.lower() for y in currentMember.roles]
                if (group.lower() in memberRoles):
                    memberList.append(currentMember)
                    continue

            msg += row[1] + ":\n"
            for currentMember in memberList:
                msg += currentMember.name + ", "

            msg = msg[:-2]  # remove last comma
            await bot.reply(msg)

async def getGroupMembers(servername):
    groupmembers = defaultdict(list)
    groups = await getGroupsOfServer(servername)
    for server in bot.servers:
        if(server.name == servername):
            for group in groups:
                for member in server.members:
                    memberRoles = [y.name.lower() for y in member.roles]
                    if (group.lower() in memberRoles):
                        groupmembers[group].append(member.name)
                        continue
    return dict(groupmembers.items())

async def getGroupsOfServer(servername):
    groups = []
    for group in botCur.execute("""SELECT name from allowedroles 
                            WHERE server = '""" + servername + """'
                            """):
        groups.append(group[0])
    return groups


@bot.command(pass_context=True, aliases=["allowedroles"])
async def allowedgroups(ctx):
    member = ctx.message.author
    msg = "Folgende Gruppen sind erlaubt: \n"
    #for group in botCur.execute("""SELECT name from allowedroles 
    #                        WHERE server = '""" + member.server.name + """'
    #                        """):
    #    msg += group[0]
    #    msg += ", "
    #msg = msg[:-2] # remove last comma
    groups = await getGroupsOfServer(member.server.name)
    for group in groups:
        msg += group
        msg += ", "
    msg = msg[:-2] # remove last comma
    await bot.say(msg)

@bot.command(pass_context=True, aliases=["addallowedgroup"])
@commands.has_any_role("Moderator", "Handlanger 👷")
async def addallowedrole(ctx, group):
    member = ctx.message.author
    role = discord.utils.get(member.server.roles, name=group)
    if(role != None):
        await addRole(member.server.name, group)
        await bot.reply("Rolle " + group + " zu den erlaubten Rollen hinzugefügt")
    else:
        await bot.reply("Rolle " + group + " existiert nicht")

@bot.command(pass_context=True, aliases=["createallowedgroup"])
@commands.has_any_role("Moderator", "Handlanger 👷")
async def createallowedrole(ctx, group):
    member = ctx.message.author
    await bot.create_role(member.server, name=group, mentionable=True)
    await addRole(member.server.name, group)
    await bot.reply("Rolle " + group + " erstellt und zu den erlaubten Rollen hinzugefügt")

async def addRole(server, role):
    botCur.execute("""Insert Into allowedroles(server, name)
                            values('""" + server + """', '""" + role + """') """)
    botConn.commit()

@bot.command(pass_context=True, aliases=["deleteallowedgroup"])
@commands.has_any_role("Moderator", "Handlanger 👷")
async def deleteallowedrole(ctx, group):
    member = ctx.message.author
    role = discord.utils.get(member.server.roles, name=group)
    await deleteRole(member.server.name, group)
    await bot.delete_role(member.server, role)
    await bot.reply("Rolle " + group + " aus db und discord entfernt")

@bot.command(pass_context=True, aliases=["removeallowedgroup"])
@commands.has_any_role("Moderator", "Handlanger 👷")
async def removeallowedrole(ctx, group):
    member = ctx.message.author
    await deleteRole(member.server.name, group)
    await bot.reply("Rolle " + group + " ist nicht mehr erlaubt (Die Rolle existiert weiterhin in Discord)")

async def deleteRole(server, role):
    botCur.execute("""Delete from allowedroles
                        where server = '""" + server + """'
                        AND name = '""" + role + """'""")
    botConn.commit()

### END ROLES ###

#@bot.command()
async def getUserList():
    user = await bot.get_user_info(117416669810393097)
    logger.debug(user)
    #for server in bot.servers:
    #    #logger.debug(server)
    #    logger.debug('-' + server.name)
    #    for member in server.members:
    #        logger.debug('---' + member.name + ', ' + member.id)

#@bot.command()
async def testMsgReaction():
    msg = await bot.say("this is a test")
    logger.debug("original msg: ")
    logger.debug(msg)
    await bot.add_reaction(msg, '\U0001F44D')
    #emojis = bot.get_all_emojis()
    #logger.debug(emojis)
    await asyncio.sleep(10)
    cache_msg = discord.utils.get(bot.messages, id=msg.id)
    logger.debug("new msg: ")
    logger.debug(cache_msg)
    logger.debug(cache_msg.reactions)
    logger.debug(cache_msg.id)
    for reaction in cache_msg.reactions:
        logger.debug(reaction.emoji)
        logger.debug(reaction.count)
        
    logger.debug("test")
    emojis=bot.get_all_emojis()
    logger.debug(emojis)
    for emoji in emojis:
        logger.debug(emoji)
        
#@bot.command(pass_context=True)
async def msgStat(ctx):
    #cache_msg = discord.utils.get(bot.messages, id=510217606599409704)
    cache_msg = await bot.get_message(ctx.message.channel, 510222196459831296)
    logger.debug(ctx.message.channel)
    logger.debug(ctx.message.channel.id)
    logger.debug("new msg: ")
    logger.debug(cache_msg)
    logger.debug(cache_msg.reactions)
    logger.debug(cache_msg.id)
    for reaction in cache_msg.reactions:
        logger.debug(reaction.emoji)
        logger.debug(reaction.count)
        
#@bot.command()
async def testGetResult():
    api = strawpoll.API()
    resultPoll = await api.get_poll("https://www.strawpoll.me/16760672")
    logger.debug(resultPoll.result_at(0))
    logger.debug(resultPoll.options)
    logger.debug(resultPoll.votes)
    logger.debug(resultPoll.results())
    orderedResults = resultPoll.results()
    i = 0
    votes = orderedResults[0][1]
    winners = []
    while(len(orderedResults) > i and votes == orderedResults[i][1]):
        logger.debug(orderedResults[i][1])
        winners.append(orderedResults[i][0])
        i = i + 1
    
    logger.debug("Die Rammerdestages sind: %s" % winners)

#@bot.command(pass_context=True)
async def testVoice(ctx):
	channel = ctx.message.author.voice.voice_channel
	vc = await bot.join_voice_channel(channel)
	player = vc.create_ffmpeg_player('/home/pi/rammer_des_tages.mp3', after=lambda: print('done'))
	player.start()
	while not player.is_done():
		await asyncio.sleep(1)
	# disconnect after the player has finished
	player.stop()
	await vc.disconnect()

@bot.event
async def on_voice_state_update(before, after):
    # pointe: 368113080741265408
    # luke: 117416669810393097
    searchid = '368113080741265408'
    # pointezeit 
    logger.debug("checking for pointetime")
    if after.id == searchid and after.voice.voice_channel is not None and "GTA" in after.voice.voice_channel.name:
        logger.debug("correct user and channel")
        now = datetime.datetime.today()
        logger.debug(now)
        if(now.weekday() == 3 and now.hour >= 19 and now.hour <= 23):
            showtime = True
            with open("pointezeit.txt", "r") as pointefile:
                lines = pointefile.read().splitlines()
                for line in lines:
                    logger.debug("line: '"+ line + "'")
                    logger.debug("date: " + str(now.date()))
                    logger.debug(datetime.datetime.strptime(str(line),"%Y-%m-%dT%H:%M:%S.%f").date())
                    try:
                        if(datetime.datetime.strptime(str(line),"%Y-%m-%dT%H:%M:%S.%f").date() == now.date()):
                            showtime = False
                            logger.info("already posted pointetime")
                        else:
                            showtime = True
                    except:
                        logger.error("parse error in pointezeit")
            if showtime:
                logger.info("showing pointetime")
                with open("pointezeit.txt", "a+") as pointefile:
                    pointefile.write(datetime.datetime.today().isoformat())
                    pointefile.write("\n")

                try:
                    for c in bot.get_all_channels():
                        if(c.server.name == "Unterwasserpyromanen" and "GTA 5" in c.name):
                            vc = await bot.join_voice_channel(c)
                            player = vc.create_ffmpeg_player('/home/pi/workspace/AllstarBot/media/pointeblanc_1.mp3', after=lambda: print('done'))
                            player.start()
                            while not player.is_done():
                                await asyncio.sleep(1)
                            # disconnect after the player has finished
                            player.stop()
                            await vc.disconnect()
                except:
                    logger.error("fehler bei pointezeit")

                for channel in after.server.channels:
                    if "gta5" in channel.name:
                        logger.debug("posting in channel " + str(channel.name))
                        user = discord.utils.get(bot.get_all_members(), id='368113080741265408')
                        msg = "Endlich ist "
                        if user == None:
                            msg += "Pointeblanc"
                        else:
                            msg += user.mention
                        msg += " da! Jetzt gehts erst so richtig los! :boom: "
                        await bot.send_message(channel, msg)

@bot.command()
async def pointespass():
    logger.info("pointespass")
    for channel in bot.get_all_channels():
        if(channel.server.name == "Unterwasserpyromanen" and "GTA 5" in channel.name):
            logger.info("found channel")
            try:
                vc = await bot.join_voice_channel(channel)
                player = vc.create_ffmpeg_player('/home/pi/workspace/AllstarBot/media/gehtslos.mp3', after=lambda: print('done'))
                player.start()
                while not player.is_done():
                    await asyncio.sleep(1)
                # disconnect after the player has finished
                player.stop()
                await vc.disconnect()
            except:
                print("oh nein")

async def eventScheduler():
    """This scheduler runs every hour"""
    await bot.wait_until_ready()
    while not bot.is_closed:
        now = datetime.datetime.today()
        if(now.day == 3): # gif of the month - 3rd day of the month
            if(now.hour == 15): # at 12:00
                postGotm = True
                with open("gifsOfTheMonth.txt", "r") as gotmfile:
                    lines = gotmfile.readlines()
                    for line in lines:
                        lineDate=line.split(":")[0]
                        try:
                            if(datetime.datetime.strptime(str(lineDate),'%Y-%m-%d').date() == now.date()):
                                # skip because it has already been posted
                                postGotm = False
                        except:
                            logger.warn("ignore parse error in gotm")
                if(postGotm):
                    await gifs.gifOfTheMonth()
                else:
                    logger.info("Already postet GOTM")
                #await asyncio.sleep(3600) # sleep for an hour
            #else:
                #await asyncio.sleep(3600) # sleep for an hour
        
        elif(now.weekday() == 3): # gta thursday
            if(now.hour == 20): # at 20:00
                await bot.change_presence(game=discord.Game(name="GTA Donnerstag"))
            if(now.hour == 23): # turn off at 23:00
                await bot.change_presence(game=discord.Game(name=""))
        else:
            logger.info("[" + str(now) + "] nothing scheduled")
            
        await asyncio.sleep(3600) # always sleep for an hour
    logger.error("something went wrong in gif of the month")

##### WEBSERVER #####
class Webapi():

        def __init__(self, bot, gtaCog):
           self.bot = bot
           self.gtaCog = gtaCog

        async def webserver(self):
            async def handler(request):
                #await self.bot.change_presence(game=discord.Game(name="TEST"))
                for channel in self.bot.get_all_channels():
                    if(channel.server.name == "Lukes Playground" and "test" == channel.name):
                        await self.bot.send_message(channel, "This is awesome")
                return web.Response(text="it worked")
				
            async def rammer(request):
                await self.gtaCog.rammertest()
                return web.Response(text="it worked")

            async def getusername(request):
                id = request.rel_url.query['id']
                logger.debug(id)
                user = await self.bot.get_user_info(id)
                return web.Response(text=user.name)

            async def groupmembersapi(request):
                groupmem = await getGroupMembers("Unterwasserpyromanen")
                return web.json_response(groupmem)

            app = web.Application()

            # ROUTES
            app.router.add_get('/sendmsg', handler)
            app.router.add_get('/rammerdestages', rammer)
            app.router.add_get('/getusername', getusername)
            app.router.add_get('/groupmembers', groupmembersapi)
            runner = web.AppRunner(app)
            await runner.setup()
            # IP/PORT
            self.site = web.TCPSite(runner, '0.0.0.0', 5004)
            await self.bot.wait_until_ready()
            await self.site.start()
            logger.info("startet webserver on 0.0.0.0:5004")

        def __unload(self):
           asyncio.ensure_future(self.site.stop())
       
gtaCog = Gta(bot)       
webapi = Webapi(bot, gtaCog)
##### WEBSERVER END #####

##### SETUP #####
# EVENTS (Gif of the Month, Gta Donnerstag)
bot.loop.create_task(eventScheduler())

# GTA
bot.add_cog(gtaCog)

# TABLETOP - Commands werden aktuell nicht mehr unterstützt
#bot.add_cog(Tabletop(bot))

# GIFS
bot.add_cog(gifs)

# WEBSERVER
bot.add_cog(webapi)
bot.loop.create_task(webapi.webserver())

# START the Bot
bot.run(token())
