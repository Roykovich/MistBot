import discord
import datetime
import wavelink
import asyncio
from typing import cast

from discord.ext import commands, tasks

from settings import GUILD_ID

BIGBEN = "https://www.youtube.com/watch?v=vMA4_6yX3IM"

# zolok_time = datetime.time(hour=2, minute=0, tzinfo=datetime.timezone.utc)
zolok_time = datetime.time(hour=5, minute=18, tzinfo=datetime.timezone.utc)

zolok_time_dt = datetime.datetime(2024, 12, 25, hour=4, minute=40, tzinfo=datetime.timezone.utc)

new_test_real = datetime.time(hour=15, minute=0, tzinfo=datetime.timezone.utc)
new_test_real_dt = datetime.datetime(2024, 12, 25, hour=15, minute=10, tzinfo=datetime.timezone.utc)

class Timers(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.testing.start()

    def zolok_unload(self):
        self.testing.cancel()

    @tasks.loop(time=zolok_time)
    async def testing(self) -> None:
        try:
            guild = self.bot.get_guild(GUILD_ID.id)
            bot = self.bot
            # agregar esto a settings por el .env
            zolok = await guild.fetch_member() # Colocar id de zolok aca

            music = bot.get_cog("Music")
            vc = await music.export_players(str(GUILD_ID.id))
            bigben: wavelink.Search = await wavelink.Playable.search(BIGBEN)
            track: wavelink.Playable = bigben[0]

            if not vc:
                vc = await zolok.voice.channel.connect(cls=wavelink.Player, self_deaf=True, self_mute=True)
                vc = cast(wavelink.Player, guild.voice_client)
                await vc.play(track)
                return
            
            vc = vc['vc']

            print(vc)
            vc_status = vc.paused
            current_track_position = vc.position
            playable = vc.current

            if not vc_status:
                if not bigben:
                    print("Mano no hay bigben")
                    return
                


                vc.queue.put_at(0, track)
                vc.queue.put_at(1, playable)

                await vc.play(vc.queue.get())
                await asyncio.sleep(track.length / 1000)
                await vc.play(vc.queue.get(), start=current_track_position)

            else:
                print("ta pausao")

            # if zolok and zolok.voice:
            #     print(f"ta conectao a {zolok.voice.channel}")
            # else:
            #     print("no ta conectao")
                

        except discord.errors.NotFound:
            print("Este usuario no existe")





async def setup(bot) -> None:
    await bot.add_cog(Timers(bot))