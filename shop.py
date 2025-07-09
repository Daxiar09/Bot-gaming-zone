import discord
from discord.ext import commands

class ShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎬 Edits Shorts", style=discord.ButtonStyle.blurple)
    async def shorts(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("• 1 clip : 80 gemmes 💎\n• 2 clips : 110 gemmes 💎", ephemeral=True)

    @discord.ui.button(label="🎮 Cache-Cache", style=discord.ButtonStyle.green)
    async def cache(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("• 4 manches : 150 gemmes 💎\n• 6 manches : 200 gemmes 💎", ephemeral=True)

    @discord.ui.button(label="🏆 Word Record", style=discord.ButtonStyle.red)
    async def wordrecord(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("• 1 essai : 100 gemmes 💎\n• 2 essais : 170 gemmes 💎", ephemeral=True)

    @discord.ui.button(label="✨ Rôle esthétique", style=discord.ButtonStyle.gray)
    async def role(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("• Rôle @@Ww : 20 à 100 gemmes 💎\n• Rôle perso : 200 gemmes 💎", ephemeral=True)

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def shop(self, ctx):
        await ctx.send("Voici les offres disponibles :", view=ShopView())

def setup(bot):
    bot.add_cog(Shop(bot))
