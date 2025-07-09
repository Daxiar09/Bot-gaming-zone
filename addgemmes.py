import discord
from discord.ext import commands

class AddGemmes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def addgemmes(self, ctx, membre: discord.Member, montant: int):
        if ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("❌ Seul le créateur du serveur peut utiliser cette commande.")

        user_id = str(membre.id)
        if "user_gemmes" not in self.bot.__dict__:
            self.bot.user_gemmes = {}

        self.bot.user_gemmes[user_id] = self.bot.user_gemmes.get(user_id, 0) + montant
        await ctx.send(
            f"✅ {montant} gemmes ajoutées à {membre.mention}. Total : {self.bot.user_gemmes[user_id]} 💎")

def setup(bot):
    bot.add_cog(AddGemmes(bot))
