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
