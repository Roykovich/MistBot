import discord
from utils.FormatTime import format_time
from modals.RemoveTrackModal import RemoveTrackModal

class PlaylistView(discord.ui.View):
    current_page: int = 1 # current page
    separator: int = 10 # number of items per page

    async def send(self):
        embed = await self.create_embed(list(self.vc.queue)[:self.separator])
        self.message = await self.music_channel.send(embed=embed, view=self)
        await self.update_message(list(self.vc.queue)[:self.separator])

    # Creates the embed of the playlist
    async def create_embed(self, tracks):
        current_track = self.vc.current
        current_position = format_time(int(self.vc.position))
        duration = format_time(current_track.length) if not current_track.is_stream else '🎙 live'
        thumbnail = current_track.artwork

        # if the queue is empty it returns the current track
        if not self.vc.queue or self.vc.queue.is_empty:
            embed = discord.Embed(
                colour = discord.Colour.dark_purple(),
                description = f'[{current_track.title}]({current_track.uri})'
            )
            embed.set_author(name='🎵 | Suena')
            embed.add_field(name='Duración', value=f'`{current_position}/{duration}`', inline=True)
            embed.add_field(name='autor', value=f'`{current_track.author}`', inline=True)
            embed.set_thumbnail(url=thumbnail)

            return embed

        description = f'**Ahora suena:**\n[{current_track} - {current_track.author}]({current_track.uri})\n**Duración:**\n`{current_position}/{duration}`\n\n**Playlist:**\n'
        
        for i, track in enumerate(tracks):
            description += f'`[{i}]`丨**{track.title} -** `{track.author}`\n'

        embed = discord.Embed(
            title=f"Página {self.current_page} / {int(len(self.vc.queue) / self.separator) + 1}",
            color=discord.Colour.dark_purple(), 
            description=description
        )
        embed.set_thumbnail(url=thumbnail)

        return embed

    # Updates the message of the playlist
    async def update_message(self, data):
        self.update_buttons()
        embed = await self.create_embed(data)
        await self.message.edit(embed=embed, view=self)

    # Updates the buttons of the playlist
    def update_buttons(self):
        if self.current_page == 1:
            self.previous.disabled = True
            self.previous.style = discord.ButtonStyle.grey
        else:
            self.previous.disabled = False
            self.previous.style = discord.ButtonStyle.primary
        
        if self.current_page == int(len(self.vc.queue) / self.separator) + 1:
            self.next.disabled = True
            self.next.style = discord.ButtonStyle.grey
        else:
            self.next.disabled = False
            self.next.style = discord.ButtonStyle.primary

    # Gets the current page of the playlist
    def get_current_page(self):
        until_page = self.current_page * self.separator
        from_page = until_page - self.separator

        if self.current_page == 1:
            from_page = 0
            until_page = self.separator
        
        if self.current_page == int(len(self.vc.queue) / self.separator) + 1:
            from_page = self.current_page - 1 * self.separator - self.separator
            until_page = len(self.vc.queue)

        return list(self.vc.queue)[from_page:until_page]
    
    @discord.ui.button(label='Anterior', emoji='⬅️', style=discord.ButtonStyle.gray, disabled=True)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page -= 1
        await self.update_message(self.get_current_page())

    @discord.ui.button(label='Eliminar', emoji='🗑️', style=discord.ButtonStyle.gray)
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        # añadimos el modal para eliminar una canción
        # el custom_id es necesario para que el modal funcione
        remove_modal = RemoveTrackModal(vc=self.vc, custom_id='remove_modal')
        await interaction.response.send_modal(remove_modal)

    @discord.ui.button(label='Siguiente', emoji='➡️', style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page += 1
        await self.update_message(self.get_current_page())
