import discord
import datetime
import wavelink
import asyncio
from typing import cast

from discord.ext import commands, tasks

from settings import GUILD_ID, ZOLOK_ID

BIGBEN = "https://www.youtube.com/watch?v=vMA4_6yX3IM"
ACE = "https://www.youtube.com/watch?v=80XAJKqRU9k"

zolok_time = datetime.time(hour=1, minute=0, tzinfo=datetime.timezone.utc)

class Timers(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.testing.start()

    def zolok_unload(self):
        self.testing.cancel()

    @tasks.loop(time=zolok_time)
    async def testing(self) -> None:
        try:
            # We look for the guild
            guild = self.bot.get_guild(GUILD_ID.id)
            bot = self.bot
            # And we look for the given member we want to check if it's in the guild
            # and if it's connected to a voice channel
            zolok = await guild.fetch_member(ZOLOK_ID)

            if zolok and not zolok.voice:
                print(f"[+] Z0lok no estaba conetado para el evento de bigben")
                return

            # we import the information of the Music cog
            music = bot.get_cog("Music")
            vc = await music.export_players(str(GUILD_ID.id))

            # we search for the sound we want to play at the given time
            bigben: wavelink.Search = await wavelink.Playable.search(ACE)
            clock_track: wavelink.Playable = bigben[0]

            if not bigben:
                print("[!] No se pudo encontrar el track del bigben")
                return

            # if they are not using the bot to play music, we connect it to the vc
            if not vc:
                await music.bigben_toggle()
                vc = await zolok.voice.channel.connect(
                    cls=wavelink.Player,
                    self_deaf=True,
                    self_mute=True
                )
                vc = cast(wavelink.Player, guild.voice_client)
                # Zolok es marico y ahora quiere que suena una cancion ahi de un momento a otro.
                await vc.play(clock_track, start=171000, end=193000)
                await asyncio.sleep((clock_track.length / 1000) + 1)
                print((clock_track.length / 1000) + 1)
                await music.bigben_toggle()
                return
            
            # If the vc exists we use the properties to see
            # the current track and its position
            vc = vc['vc']
            current_track = vc.current
            current_track_position = vc.position
            current_tract_status = vc.paused

            # we put the bigben track as the next song to be played
            # and after that the current song that was being played
            vc.queue.put_at(0, clock_track)
            vc.queue.put_at(1, current_track)

            # because we use play() it will skip the current track to
            # the next one by default, after that we wait the length of
            # the bigben track and the skip/play the current song that will
            # start were it was left
            await music.bigben_toggle()
            await vc.play(vc.queue.get(), paused=False)
            await asyncio.sleep(clock_track.length / 1000)
            await music.bigben_toggle()

            if current_tract_status:
                await vc.play(vc.queue.get(), start=current_track_position, paused=True)

            await vc.play(vc.queue.get(), start=current_track_position)

        except discord.errors.NotFound:
            print("[!] El usuario para el evento bigben no existe")


async def setup(bot) -> None:
    await bot.add_cog(Timers(bot))