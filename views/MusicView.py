import discord
from utils.embedGenerator import music_embed_generator
from views.PlaylistView import PlaylistView
from utils.formatTime import format_time


class MusicView(discord.ui.View):
    paused:bool = False
    skipper:bool = False

    @discord.ui.button(label='Atr.', emoji='⏪')
    async def backward(self, interaction: discord.Interaction, button: discord.ui.Button):
        new_position = self.vc.position - (15 * 1000)
        await self.vc.seek(new_position)
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label='Parar', emoji='⏹️')
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.vc.queue.clear() # clears the queue
        await self.vc.stop() # stops the player
        self.clear_items() # clears the buttons
        await interaction.response.edit_message(view=self) # updates the message

    @discord.ui.button(label='Pausar', emoji='⏸')
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        # pauses the player if it's playing and changes the button label
        await self.vc.pause(True if not self.paused else False)
        self.children[2].label = 'Resumir' if not self.paused else 'Pausar'
        self.children[2].emoji = '▶️' if not self.paused else '⏸️'
        self.paused = not self.paused
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label='Adel.', emoji='⏩')
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

    @discord.ui.button(label='¿Cuál viene?', emoji='👀', row=1)
    async def cual(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc.queue.is_empty:
            await interaction.response.send_message(embed=music_embed_generator('No hay ninguna canción'), ephemeral=True)
            return
        
        track = self.vc.queue.peek()
        current_position = format_time(int(self.vc.position))
        duration = format_time(track.length) if not track.is_stream else '🎙 live'
        thumbnail = track.artwork

        embed = discord.Embed(
            colour = discord.Colour.dark_purple(),
            description = f'[{track.title}]({track.uri})'
        )
        embed.set_author(name='🎵 | Suena')
        embed.add_field(name='Duración', value=f'`{current_position}/{duration}`', inline=True)
        embed.add_field(name='autor', value=f'`{track.author}`', inline=True)
        embed.set_thumbnail(url=thumbnail)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label='Siguiente', emoji='⏭️', row=1)
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
