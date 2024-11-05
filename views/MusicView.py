import discord
from utils.EmbedGenerator import music_embed_generator
from views.PlaylistView import PlaylistView
from utils.FormatTime import format_time
from utils.NowPlaying import now_playing


class MusicView(discord.ui.View):
    paused:bool = False
    skipper:bool = False

    # Para atras
    @discord.ui.button(label='', emoji='<:mb_rewind:1303148087807578173>')
    async def rewind(self, interaction: discord.Interaction, button: discord.ui.Button):
        new_position = self.vc.position - (5 * 1000)
        await self.vc.seek(new_position)
        await interaction.response.edit_message(view=self)


    @discord.ui.button(label='', emoji='<:mb_back:1244545665086914660>', disabled=True)
    async def backward(self, interaction: discord.Interaction, button: discord.ui.Button):
        ...


    # pausa y resumir
    @discord.ui.button(label='', emoji='<:mb_pause:1244545668563861625>', style=discord.ButtonStyle.green)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        # pauses the player if it's playing and changes the button label
        await self.vc.pause(True if not self.paused else False)
        self.children[2].emoji = '<:mb_pause:1244545668563861625>' if self.paused else '<:mb_resume:1244545666982744119>'
        self.paused = not self.paused
        await interaction.response.edit_message(view=self)


    @discord.ui.button(label='', emoji='<:mb_next:1244545663669243954>')
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc.queue.is_empty:
            self.clear_items()
            await interaction.response.edit_message(view=self)
            await self.vc.stop()
            return


    # Para adelante
    @discord.ui.button(label='', emoji='<:mb_forward:1303148126193848352>')
    async def forward(self, interaction: discord.Interaction, button: discord.ui.Button):
        new_position = self.vc.position + (5 * 1000)
        await self.vc.seek(new_position)
        await interaction.response.edit_message(view=self)


    @discord.ui.button(label='', emoji='<:mb_loop:1244545660041297930>', row=1, disabled=True)
    async def loop(self, interaction: discord.Interaction, button: discord.ui.Button):
        ...


    @discord.ui.button(label='', emoji='<:mb_lyrics:1303142190154907658>', row=1, disabled=True)
    async def lyrics(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=music_embed_generator(self.lyrics if self.lyrics else 'No se encontraron letras para esta canción'))


    @discord.ui.button(label='', emoji='<:mb_stop:1244545666211119104>', style=discord.ButtonStyle.red, row=1)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.vc.queue.clear() # clears the queue
        await self.vc.stop() # stops the player
        self.clear_items() # clears the buttons
        await interaction.response.edit_message(view=self)


    @discord.ui.button(label='', emoji='<:mb_playlist:1303137502894362634>', row=1)
    async def playlist(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = PlaylistView(timeout=None)
        view.vc = self.vc
        view.music_channel = self.music_channel
        await view.send()
        await interaction.response.defer()

    
    @discord.ui.button(label='', emoji='<:mb_shuffle:1244545660770979853>', row=1, disabled=True)
    async def shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):
        ...

    # @discord.ui.button(label='Preview', emoji='👀', row=1)
    # async def preview(self, interaction: discord.Interaction, button: discord.ui.Button):
    #     if self.vc.queue.is_empty:
    #         await interaction.response.send_message(embed=music_embed_generator('No hay ninguna canción'), ephemeral=True)
    #         return
        
    #     track = self.vc.queue.peek()
    #     current_position = format_time(int(self.vc.position))
    #     embed = now_playing(track, user=self.user_list[0] if self.user_list else None, current=True, position=current_position, peek=True)

    #     await interaction.response.send_message(embed=embed, ephemeral=True)


        await self.vc.play(self.vc.queue.get())
        self.clear_items()
        await interaction.response.edit_message(view=self)
