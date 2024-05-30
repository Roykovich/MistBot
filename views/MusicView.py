import discord
from utils.embedGenerator import music_embed_generator
from views.PlaylistView import PlaylistView
from utils.formatTime import format_time
from utils.nowPlaying import now_playing


class MusicView(discord.ui.View):
    paused:bool = False
    skipper:bool = False

    @discord.ui.button(label='Atr.', emoji='<:mb_rewind:1244545665086914660>', style=discord.ButtonStyle.blurple)
    async def backward(self, interaction: discord.Interaction, button: discord.ui.Button):
        new_position = self.vc.position - (15 * 1000)
        await self.vc.seek(new_position)
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label='Parar', emoji='<:mb_stop:1244545666211119104>', style=discord.ButtonStyle.red)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.vc.queue.clear() # clears the queue
        await self.vc.stop() # stops the player
        self.clear_items() # clears the buttons
        await interaction.response.edit_message(view=self) # updates the message

    @discord.ui.button(label='Pausar', emoji='<:mb_pause:1244545668563861625>', style=discord.ButtonStyle.green)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        # pauses the player if it's playing and changes the button label
        await self.vc.pause(True if not self.paused else False)
        self.children[2].label = 'Resumir' if not self.paused else 'Pausar'
        self.children[2].emoji = '<:mb_pause:1244545668563861625>' if not self.paused else '<:mb_resume:1244545666982744119>'
        self.paused = not self.paused
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label='Adel.', emoji='<:mb_forward:1244545663669243954>', style=discord.ButtonStyle.blurple)
    async def forward(self, interaction: discord.Interaction, button: discord.ui.Button):
        new_position = self.vc.position + (15 * 1000)
        await self.vc.seek(new_position)
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label='Lista', emoji='📜', row=1)
    async def playlist(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = PlaylistView(timeout=None)
        view.vc = self.vc
        view.music_channel = self.music_channel
        await view.send()
        await interaction.response.defer()

    @discord.ui.button(label='Siguiente en lista', emoji='👀', row=1)
    async def cual(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc.queue.is_empty:
            await interaction.response.send_message(embed=music_embed_generator('No hay ninguna canción'), ephemeral=True)
            return
        
        track = self.vc.queue.peek()
        current_position = format_time(int(self.vc.position))
        embed = now_playing(track, user=self.user_list[0] if self.user_list else None, current=True, position=current_position, peek=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label='Siguiente', emoji='<:mb_next:1244545662482255872>', row=1)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc.queue.is_empty:
            channel = self.vc.channel.mention
            self.clear_items()
            await interaction.response.edit_message(view=self)
            self.vc.queue.clear()
            await self.vc.stop()
            await interaction.channel.send(embed=music_embed_generator(f'🎼 La playlist termino. Bot desconectado de {channel} 👋'))
            return
        
        await self.vc.play(self.vc.queue.get())
        self.clear_items()
        await interaction.response.edit_message(view=self)
