import discord
from discord.ext import commands
from discord import app_commands
import re


class Moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.configs = {}  # guild_id: {channel_id: {links, insults}}
        self.logs = {}  # guild_id: log_channel_id

        self.insults = [
            "con", "connard", "connasse", "conne", "c*n", "c0n", "fdp",
            "fils de pute", "filsdepute", "fils2pute", "ntm", "nique ta mère",
            "niquetamere", "n*t*m", "tg", "ta gueule", "tagueule", "enculé",
            "encule", "enculer", "enculė", "encul*", "encul3", "pute",
            "putain", "put1", "puteuh", "salope", "salop", "salopard",
            "batard", "bâtard", "batrd", "merde", "merd*", "m*rde", "abruti",
            "abrutis", "abrutie", "bouffon", "boufon", "bouffonne", "pd",
            "tapette", "fiotte", "chiant", "chiotte", "chié", "chier", "culé",
            "cul", "gros con", "grosse conne", "trou du cul", "troudcul",
            "connard de merde"
        ]
        self.insult_patterns = [
            re.compile(rf"\b{re.escape(insult)}\b", re.IGNORECASE)
            for insult in self.insults
        ]
        self.link_pattern = re.compile(r"https?://|www\.")

        self.bot.tree.add_command(self.config)
        self.bot.tree.add_command(self.voir_configs)
        self.bot.tree.add_command(self.config_logs)

    async def send_warning(self, user, reason):
        try:
            await user.send(f"⚠️ Tu as reçu un avertissement pour : {reason}")
        except discord.Forbidden:
            pass

    async def log_deletion(self, guild: discord.Guild, author: discord.Member,
                           content: str):
        log_channel_id = self.logs.get(guild.id)
        if not log_channel_id:
            return

        log_channel = guild.get_channel(log_channel_id)
        if not log_channel:
            return

        embed = discord.Embed(title="🔨 Message supprimé",
                              color=discord.Color.orange())
        embed.add_field(name="Auteur", value=author.mention, inline=True)
        embed.add_field(name="Message",
                        value=content[:1024] or "Vide",
                        inline=False)
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        config = self.configs.get(message.guild.id, {}).get(message.channel.id)
        if not config:
            return

        if config.get("links") and self.link_pattern.search(message.content):
            await message.delete()
            await self.send_warning(message.author, "envoi de lien interdit")
            await self.log_deletion(message.guild, message.author,
                                    message.content)
            return

        if config.get("insults"):
            for pattern in self.insult_patterns:
                if pattern.search(message.content):
                    await message.delete()
                    await self.send_warning(message.author,
                                            "insultes interdites")
                    await self.log_deletion(message.guild, message.author,
                                            message.content)
                    return

    @app_commands.command(name="config",
                          description="Configurer les vérifs dans un salon")
    @app_commands.describe(
        salon="Salon à configurer",
        lien="Activer/désactiver la détection de liens (on/off)",
        insultes="Activer/désactiver la détection d'insultes (on/off)")
    async def config(self, interaction: discord.Interaction,
                     salon: discord.TextChannel, lien: str, insultes: str):
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message(
                "❌ Seul le créateur du serveur peut faire ça.", ephemeral=True)
            return

        guild_id = interaction.guild_id
        if guild_id not in self.configs:
            self.configs[guild_id] = {}

        self.configs[guild_id][salon.id] = {
            "links": lien.lower() == "on",
            "insults": insultes.lower() == "on"
        }

        await interaction.response.send_message(
            f"✅ Config appliquée à {salon.mention} : Liens = {lien.upper()}, Insultes = {insultes.upper()}",
            ephemeral=True)

    @app_commands.command(name="voir_configs",
                          description="Voir les configs de modération")
    async def voir_configs(self, interaction: discord.Interaction):
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message(
                "❌ Seul le créateur du serveur peut voir ça.", ephemeral=True)
            return

        guild_id = interaction.guild_id
        configs = self.configs.get(guild_id, {})

        if not configs:
            await interaction.response.send_message(
                "Aucune configuration définie.", ephemeral=True)
            return

        embed = discord.Embed(title="🛠️ Configs des salons",
                              color=discord.Color.blue())

        for channel_id, settings in configs.items():
            channel = interaction.guild.get_channel(channel_id)
            if channel:
                embed.add_field(
                    name=channel.name,
                    value=
                    f"Liens : {'✅' if settings['links'] else '❌'} | Insultes : {'✅' if settings['insults'] else '❌'}",
                    inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="config_logs",
        description="Définit un salon de logs pour les suppressions")
    @app_commands.describe(salon="Salon où le bot enverra les logs")
    async def config_logs(self, interaction: discord.Interaction,
                          salon: discord.TextChannel):
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message(
                "❌ Seul le créateur du serveur peut faire ça.", ephemeral=True)
            return

        self.logs[interaction.guild.id] = salon.id
        await interaction.response.send_message(
            f"✅ Les messages supprimés seront loggés dans {salon.mention}.",
            ephemeral=True)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
