import discord
from discord.ext import commands
import re


class Moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.configs = {}
        self.log_channels = {}
        self.insults = [
            "con", "connard", "connasse", "conne", "c*n", "c0n", "fdp",
            "fils de pute", "filsdepute", "fils2pute", "ntm", "nique ta mère",
            "niquetamere", "n*t*m", "tg", "ta gueule", "tagueule", "enculé",
            "encule", "enculer", "enculė", "encul*", "encul3", "pute",
            "putain", "put1", "puteuh", "salope", "salop", "salopard",
            "batard", "bâtard", "batrd", "merde", "m*rde", "abruti", "abrutis",
            "abrutie", "bouffon", "boufon", "bouffonne", "pd", "tapette",
            "fiotte", "chiant", "chiotte", "chié", "chier", "culé", "cul",
            "gros con", "grosse conne", "trou du cul", "troudcul",
            "connard de merde"
        ]
        self.insult_patterns = [
            re.compile(rf"\b{re.escape(i)}\b", re.IGNORECASE)
            for i in self.insults
        ]
        self.link_pattern = re.compile(r"https?://|www\.")

    async def send_warning(self, user, reason):
        try:
            await user.send(f"⚠️ Tu as reçu un avertissement pour : {reason}")
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        config = self.configs.get(message.guild.id, {}).get(message.channel.id)
        if not config:
            return

        deleted = False

        if config.get("links") and self.link_pattern.search(message.content):
            await message.delete()
            await self.send_warning(message.author, "envoi de lien interdit")
            deleted = True

        elif config.get("insults"):
            for pattern in self.insult_patterns:
                if pattern.search(message.content):
                    await message.delete()
                    await self.send_warning(message.author,
                                            "insultes interdites")
                    deleted = True
                    break

        if deleted:
            log_channel_id = self.log_channels.get(message.guild.id)
            if log_channel_id:
                log_channel = message.guild.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(title="🚨 Message supprimé",
                                          description=message.content,
                                          color=discord.Color.red())
                    embed.set_author(
                        name=str(message.author),
                        icon_url=message.author.display_avatar.url)
                    embed.add_field(name="Salon",
                                    value=message.channel.mention)
                    await log_channel.send(embed=embed)

    def is_owner(self, ctx):
        return ctx.author == ctx.guild.owner

    @commands.command(name="config")
    async def config(self, ctx, salon: discord.TextChannel, lien: str,
                     insultes: str):
        if not self.is_owner(ctx):
            return await ctx.send(
                "❌ Seul le **créateur du serveur** peut utiliser cette commande."
            )
        guild_id = ctx.guild.id
        if guild_id not in self.configs:
            self.configs[guild_id] = {}
        self.configs[guild_id][salon.id] = {
            "links": lien.lower() == "on",
            "insults": insultes.lower() == "on"
        }
        await ctx.send(
            f"✅ Configuration mise à jour pour {salon.mention} : liens = {lien.upper()}, insultes = {insultes.upper()}"
        )

    @commands.command(name="voir_configs")
    async def voir_configs(self, ctx):
        if not self.is_owner(ctx):
            return await ctx.send(
                "❌ Seul le **créateur du serveur** peut utiliser cette commande."
            )
        configs = self.configs.get(ctx.guild.id, {})
        if not configs:
            return await ctx.send("❌ Aucune configuration définie.")
        embed = discord.Embed(title="🔧 Configurations des salons",
                              color=discord.Color.blue())
        for channel_id, settings in configs.items():
            channel = ctx.guild.get_channel(channel_id)
            if channel:
                embed.add_field(
                    name=channel.name,
                    value=f"Liens : {'✅' if settings['links'] else '❌'} | "
                    f"Insultes : {'✅' if settings['insults'] else '❌'}",
                    inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="config_log")
    async def config_log(self, ctx, salon: discord.TextChannel):
        if not self.is_owner(ctx):
            return await ctx.send(
                "❌ Seul le **créateur du serveur** peut utiliser cette commande."
            )
        self.log_channels[ctx.guild.id] = salon.id
        await ctx.send(f"📘 Les logs seront envoyés dans {salon.mention}.")


async def setup(bot):
    await bot.add_cog(Moderation(bot))
