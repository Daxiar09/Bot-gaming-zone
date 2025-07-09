import discord
from discord.ext import commands

class SetSalon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def set(self, ctx, param: str, salon: discord.TextChannel):
        if ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("❌ Seul le créateur du serveur peut utiliser cette commande.")

        if param.lower() == "salon":
            self.bot.shop_channel_id = salon.id
            await ctx.send(f"✅ Salon défini : {salon.mention}")
        else:
            await ctx.send("❌ Paramètre invalide. Utilise `set salon #salon`.")

def setup(bot):
    bot.add_cog(SetSalon(bot))
