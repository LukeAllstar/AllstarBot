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
from gtaCommands import Gta
from tabletopCommands import Tabletop
from gifCommands import Gif

with open('config.json') as json_data_file:
    data = json.load(json_data_file)

if not os.path.exists('db/tabletop.db') or not os.path.exists('db/gta.db') or not os.path.exists('db/quotes.db') or not os.path.exists('db/gifs.db'):
    print("Databases do not exist. Running setup!")
    setup.setup()

def token():
    '''Returns your token wherever it is'''
    if data.get('token') == "<token>":
        if not os.environ.get('TOKEN'):
            print("Error retrieving token.")
            exit()
    else:
        token = data.get('token').strip('\"')
    return os.environ.get('TOKEN') or token
        
bot = commands.Bot(command_prefix=data["command_prefix"], description=data["description"])
# maybe usefull later:
#bot.remove_command("help")

quotesConn = sqlite3.connect('db/quotes.db')
gifsConn = sqlite3.connect('db/gifs.db')

quotesCur = quotesConn.cursor()
gifsCur = gifsConn.cursor()
gifs = Gif(bot)

try:
    locale.setlocale(locale.LC_ALL, 'German_Germany')
except:
    print("Couldn't set locale")
  
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

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
    


#@bot.command()
#async def phil():
#    await bot.say('Der schoenste Oesterreicher :flag_at:')

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
        await bot.say('```\"%s\" - %s```' % (row[0], row[1]))
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
        await bot.say("Zitat hinzugefuegt")

#@bot.command(pass_context=True)
#async def test(ctx):
#    """ Testing some permission stuff """
#    await bot.say("author: " + str(ctx.message.author))
#    #for role in ctx.message.author.roles:
#    #    await bot.say("rolle: " + str(role.name))
#    await bot.say("ist admin: " + str(ctx.message.author.server_permissions.administrator))
         
@bot.command(pass_context=True)
async def friends(ctx):
    """Freunde!"""
    user = discord.utils.get(ctx.message.server.members, name = 'Lefty')
    await bot.say(":robot: My only friend is " + user.mention)
        

   
"""   
@bot.command(pass_context=True)
async def testupload(ctx, text):
    print(text)
    print(ctx.message)
    print(ctx.message.attachments)
    print(ctx.message.attachments[0]['url'])
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

#@bot.command()
async def testMsgReaction():
    msg = await bot.say("this is a test")
    print("original msg: ")
    print(msg)
    await bot.add_reaction(msg, '\U0001F44D')
    #emojis = bot.get_all_emojis()
    #print(emojis)
    await asyncio.sleep(10)
    cache_msg = discord.utils.get(bot.messages, id=msg.id)
    print("new msg: ")
    print(cache_msg)
    print(cache_msg.reactions)
    print(cache_msg.id)
    for reaction in cache_msg.reactions:
        print(reaction.emoji)
        print(reaction.count)
        
    print("test")
    emojis=bot.get_all_emojis()
    print(emojis)
    for emoji in emojis:
        print(emoji)
        
#@bot.command(pass_context=True)
async def msgStat(ctx):
    #cache_msg = discord.utils.get(bot.messages, id=510217606599409704)
    cache_msg = await bot.get_message(ctx.message.channel, 510222196459831296)
    print(ctx.message.channel)
    print(ctx.message.channel.id)
    print("new msg: ")
    print(cache_msg)
    print(cache_msg.reactions)
    print(cache_msg.id)
    for reaction in cache_msg.reactions:
        print(reaction.emoji)
        print(reaction.count)
        
#@bot.command()
async def testGetResult():
    api = strawpoll.API()
    resultPoll = await api.get_poll("https://www.strawpoll.me/16760672")
    print(resultPoll.result_at(0))
    print(resultPoll.options)
    print(resultPoll.votes)
    print(resultPoll.results())
    orderedResults = resultPoll.results()
    i = 0
    votes = orderedResults[0][1]
    winners = []
    while(len(orderedResults) > i and votes == orderedResults[i][1]):
        print(orderedResults[i][1])
        winners.append(orderedResults[i][0])
        i = i + 1
    
    print("Die Rammerdestages sind: %s" % winners)
                       
async def eventScheduler():
    """This scheduler runs every hour"""
    await bot.wait_until_ready()
    while not bot.is_closed:
        now = datetime.datetime.today()
        if(now.day == 3): # gif of the month - 3rd day of the month
            if(now.hour == 12): # at 12:00
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
                            print("ignore parse error")
                if(postGotm):
                    await gifs.gifOfTheMonth()
                else:
                    print("Already postet GOTM")
                #await asyncio.sleep(3600) # sleep for an hour
            #else:
                #await asyncio.sleep(3600) # sleep for an hour
        
        elif(now.weekday == 3): # gta thursday
            if(now.hour == 20): # at 20:00
                await bot.change_presence(game=discord.Game(name="GTA Donnerstag"))
            if(now.hour == 23): # turn off at 23:00
                await bot.change_presence(game=discord.Game(name=""))
        else:
            print("[" + str(now) + "] nothing scheduled")
            
        await asyncio.sleep(3600) # always sleep for an hour
    print("something went wrong in gif of the month")

@bot.command()
async def pointezeit(time = ""):
    userPointe = discord.utils.get(bot.get_all_members(), id='368113080741265408')
    msg = "Juhu, "
    if userPointe == None:
        msg += "Pointeblanc"
    else:
        msg += userPointe.mention
    msg += " ist hier! Jetzt geht die Party ab!"
    await bot.say(msg) 

bot.loop.create_task(eventScheduler())
bot.add_cog(Gta(bot))
# Tabletop Commands werden aktuell nicht mehr unterstützt
#bot.add_cog(Tabletop(bot))
bot.add_cog(gifs)
bot.run(token())
