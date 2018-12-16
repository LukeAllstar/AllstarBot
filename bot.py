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
    
#@bot.command()
async def gifOfTheMonth():
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
    for gif in gifsCur.execute("""Select game, comment, addedBy, date(addedOn), messageId, channelId, ROWID, url """ +
                    """from gifs """+
                    """where date(addedOn) >  date(date('now', '-2 day'), '-1 month')"""):
        if(gif[4] != None and gif[5] != None):
            gifChannel = discord.utils.get(bot.get_all_channels(), id=gif[5])
            cache_msg = await bot.get_message(gifChannel, gif[4])
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
    for channel in bot.get_all_channels():
        if(channel.server.name in postTo):
            # find the correct channel
            if(postTo[channel.server.name] == channel.name):
                await bot.send_message(channel, "**GIF DES MONATS**")
                if(msg != ""):
                    await bot.send_message(channel, msg)

                # Gif of the Month (most upvotes)
                await bot.send_message(channel, "Das Gif des Monats mit "+ str(mostVotes) +" 👍 ist Gif #"+str(gifOfTheWeek[6]))
                gifMsg = Gif.formatGif(gifOfTheWeek[7], gifOfTheWeek[0], gifOfTheWeek[1], gifOfTheWeek[2], gifOfTheWeek[6])
                gotmMsg = await bot.send_message(channel, gifMsg)
                await Gif.addReactions(gotmMsg, gifOfTheWeek[4], gifOfTheWeek[5])
                mostReactionsWinner=mostReactionsOTM[0]
                # Most Reactions
                await bot.send_message(channel, "Das Gif mit den meisten Reaktionen des Monats ist Gif #"+str(mostReactionsWinner[6]) + " mit " + str(mostReactions) + " Reaktionen!")
                gifMsg = Gif.formatGif(mostReactionsWinner[7], mostReactionsWinner[0], mostReactionsWinner[1], mostReactionsWinner[2], mostReactionsWinner[6])
                mostReactionsMsg = await bot.send_message(channel, gifMsg)
                await Gif.addReactions(mostReactionsMsg, mostReactionsWinner[4], mostReactionsWinner[5])
                        
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
                    await gifOfTheMonth()
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

bot.loop.create_task(eventScheduler())
bot.add_cog(Gta(bot))
# Tabletop Commands werden aktuell nicht mehr unterstützt
#bot.add_cog(Tabletop(bot))
bot.add_cog(Gif(bot))
bot.run(token())
