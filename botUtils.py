import asyncio
import discord
from discord.ext import commands
import logging
import os

class BotUtils(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('bot')

    async def playSound(self, channel, soundfile):
        """ Plays a sound file in the given channel. If there are other open voiceclients then we
        wait a maximum of 1 minute until the other voiceclient is finished."""
        try:
            soundfile = os.path.abspath(soundfile)
            self.logger.debug("playSound. channel: %s, soundfile: %s", str(channel), str(soundfile))
            if(os.path.isfile(soundfile)):
                i = 0
                while(len(self.bot.voice_clients) > 0):
                    self.logger.info("there are open voice clients: " + str(self.bot.voice_clients))
                    # already in a voice chat -> wait for that to finish first
                    await asyncio.sleep(1)
                    i += 1
                    if(i > 60):
                        raise Exception('Waited too long for other voice clients to finish')
                vc = await channel.connect()
                try :
                    self.logger.info("started soundfile")
                    await asyncio.sleep(0.5)
                    vc.play(discord.FFmpegPCMAudio(soundfile), after=lambda e: print('done', e))
                    while vc.is_playing():
                        self.logger.debug('not finished playing sound')
                        await asyncio.sleep(1)
                    self.logger.info("finished playing sound " + str(soundfile))
                except:
                    pass
                finally:
                    self.logger.info("disconnecting from voicechannel")
                    await vc.disconnect()
            else:
                self.logger.error("File %s doesn't exist.", soundfile)
        except:
            pass

    async def startvote(self, channel, options):
        messages = await self.createVoteMessages(channel, options)
        msgText = self.createVoteMessageText(messages)
        if msgText != None and msgText != '':
            discordMsg = await channel.send(msgText)
            await self.addVoteMessageReactions(messages, discordMsg)

    async def timedvote(self, channel, waittime, options):
        """
        Starts a timed vote
        Returns an array of the winners

        Parameters
        ----------
        channel
            The target TextChannel
        waittime
            How long in minutes before the result is announced
        options
            An array of possible options for the vote
        """
        self.logger.debug('timedvote start')
        self.logger.debug(options)
        try:
            timer = int(waittime)
        except:
            await channel.send('Bitte eine gültige Zeit (in Minuten eingeben)\n`!timedvote 30 option1 option2 option3`')
            return
        if(timer < 1 or timer > 240):
            await channel.send('Die Abstimmungszeit darf nur zwischen 1 und 240 Minuten (4 Stunden) sein')
        else:
            messages = await self.createVoteMessages(channel, options)
            msgText = self.createVoteMessageText(messages)
            if msgText != None and msgText != '':
                # post message
                msg = await channel.send(msgText)

                # add reactions
                await self.addVoteMessageReactions(messages, msg)

                await channel.send('Die Abstimmung läuft. Zeitlimit: ' + str(timer) + ' Minuten')
                self.logger.debug('Waiting for ' + str(timer) + ' minutes for the vote to end')
                await asyncio.sleep(timer * 60) # minutes to seconds
                self.logger.debug('Vote is over. Now counting reactions')
                
                # Count Reactions to get the winner(s)
                updatedMsg = await msg.channel.fetch_message(msg.id)
                msgReactions = updatedMsg.reactions
                self.logger.debug(msgReactions)
                winners = []
                mostVotes = 0
                counter = 0
                for reaction in msgReactions:
                    self.logger.debug('reaction ' + str(reaction.emoji) + ' - count: ' + str(reaction.count))
                    if reaction.emoji in messages:
                        if reaction.count > mostVotes:
                            winners = []
                            mostVotes = reaction.count
                        if reaction.count == mostVotes:
                            winners.append(options[counter])
                    else:
                        self.logger.warning('Not counting unsupported reaction for vote: ' + str(reaction.emoji))
                    counter += 1
                winnerMsg = ''
                if len(winners) > 1:
                    winnerMsg = 'Die Gewinner sind '
                else:
                    winnerMsg = 'Der Gewinner ist '
                first = True
                for winner in winners:
                    if first:
                        first = False
                    else:
                        winnerMsg += ", "
                    winnerMsg += str(winner)
                await channel.send(winnerMsg)
                return winners

        self.logger.debug('timedvote end')

    async def createVoteMessages(self, channel, options):
        """
        returns a dictionary where the key is an emoji which represents the voting option
        the value is the text of the option

        Parameters
        ----------
        channel
            The target TextChannel
        options : array
            The options in string form
        """
        messages = {}
        if len(options) > 20:
            await channel.send('Es sind maximal 20 Optionen erlaubt')
        elif len(options) <= 1:
            await channel.send('Bitte mindestens 2 Optionen angeben')
        else:
            counter = 1
            for option in options:
                messages[self.getNumberEmoji(counter)] = str(option)
                counter += 1
        return messages

    def createVoteMessageText(self, messages):
        """
        Returns the formatted message for the vote

        Parameters
        ----------
        messages : dict
            A Dictionary where the key represents the emoji which is used for the voting and
            the value is the text of the voting option
        """
        outmsg = ''
        counter = 1
        for k, v in messages.items():
            outmsg += '\n'
            outmsg += str(k) + ': '
            outmsg += str(v)
            counter += 1
        return outmsg

    async def addVoteMessageReactions(self, messages, discordMessage):
        for key in messages.keys():
            await discordMessage.add_reaction(key)

    def getNumberEmoji(self, number):
        """
        Returns an Emoji representing the voting option
        """
        numberEmojis = {
            1: '1️⃣',
            2: '2️⃣',
            3: '3️⃣',
            4: '4️⃣',
            5: '5️⃣',
            6: '6️⃣',
            7: '7️⃣',
            8: '8️⃣',
            9: '9️⃣',
            10: '🐲',
            11: '🐼',
            12: '🐸',
            13: '🐷',
            14: '🦊',
            15: '🐱',
            16: '👻',
            17: '👹',
            18: '🦉',
            19: '🦄',
            20: '🐞'
        }
        return numberEmojis[int(number)]