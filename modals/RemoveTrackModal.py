import discord

class RemoveTrackModal(discord.ui.Modal, title='Eliminar canción'):
    def __init__(self, vc, custom_id):
        self.vc = vc # the player, in order to access the queue in this view
        super().__init__()

    # the input field to get the index of the track to remove
    track_index = discord.ui.TextInput(label='Eliminar de la playlist', placeholder='El número a la izquierda en []', min_length=1, max_length=3, required=True)

    # what happen when you click submit
    async def on_submit(self, interaction: discord.Interaction):
        if not self.track_index.value.isdigit(): # if the value is not a number
            await interaction.response.send_message('El valor debe ser un número', ephemeral=True)
            return
        
        index = int(self.track_index.value)
        if index > len(self.vc.queue) - 1 or index < 0: # if the value is greater than the size of the queue or less than 0
            await interaction.response.send_message('El valor es mayor que el tamaño de la playlist', ephemeral=True)
            return
        
        # we create a string before the tracks gets deleted
        message = f'La canción **{self.vc.queue.peek(index)}** ha sido eliminada.'

        self.vc.queue.delete(index) # deletes the track
        await interaction.response.send_message(f'indice: {message}', ephemeral=True)


    async def on_error(self, interaction: discord.Interaction):
        # TODO: add error handling
        ...