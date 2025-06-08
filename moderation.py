    import discord
    from discord.ext import commands
    from discord import app_commands
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
                "batard", "bâtard", "batrd", "merde", "m*rde", "abruti",
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
                        await self.send_warning(message.author, "insultes interdites")
                        deleted = True
                        break

            if deleted:
                log_channel_id = self.log_channels.get(message.guild.id)
                if log_channel_id:
                    log_channel = message.guild.get_channel(log_channel_id)
                    if log_channel:
                        embed = discord.Embed(
                            title="🚨 Message supprimé",
                            description=message.content,
                            color=discord.Color.red()
                        )
                        embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
                        embed.add_field(name="Salon", value=message.channel.mention)
                        await log_channel.send(embed=embed)

        # Check: uniquement le créateur du serveur
        @staticmethod
        def is_owner(interaction: discord.Interaction) -> bool:
            return interaction.user.id == interaction.guild.owner_id

        @app_commands.command(name="config", description="Configurer les vérifs dans un salon")
        @app_commands.check(is_owner)
        @app_commands.describe(
            salon="Salon à configurer",
            lien="Activer/désactiver la détection de liens (on/off)",
            insultes="Activer/désactiver la détection d'insultes (on/off)"
        )
        async def config(self, interaction: discord.Interaction, salon: discord.TextChannel, lien: str, insultes: str):
            guild_id = interaction.guild_id
            if guild_id not in self.configs:
                self.configs[guild_id] = {}

            self.configs[guild_id][salon.id] = {
                "links": lien.lower() == "on",
                "insults": insultes.lower() == "on"
            }

            await interaction.response.send_message(
                f"✅ Config mise à jour pour {salon.mention} : liens = {lien.upper()}, insultes = {insultes.upper()}",
                ephemeral=True
            )

        @app_commands.command(name="voir_configs", description="Voir les configurations")
        @app_commands.check(is_owner)
        async def voir_configs(self, interaction: discord.Interaction):
            guild_id = interaction.guild_id
            configs = self.configs.get(guild_id, {})

            if not configs:
                await interaction.response.send_message("❌ Aucune configuration définie.", ephemeral=True)
                return

            embed = discord.Embed(title="🛠️ Configurations actuelles", color=discord.Color.blue())
            for channel_id, settings in configs.items():
                channel = interaction.guild.get_channel(channel_id)
                if channel:
                    embed.add_field(
                        name=channel.name,
                        value=f"Liens : {'✅' if settings['links'] else '❌'} | "
                              f"Insultes : {'✅' if settings['insults'] else '❌'}",
                        inline=False
                    )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        @app_commands.command(name="config_log", description="Définir un salon de log pour les messages supprimés")
        @app_commands.check(is_owner)
        async def config_log(self, interaction: discord.Interaction, salon: discord.TextChannel):
            self.log_channels[interaction.guild.id] = salon.id
            await interaction.response.send_message(f"📘 Les logs seront envoyés dans {salon.mention}.", ephemeral=True)

        @config.error
        @voir_configs.error
        @config_log.error
        async def permission_error(self, interaction: discord.Interaction, error):
            if isinstance(error, app_commands.errors.CheckFailure):
                await interaction.response.send_message("❌ Seul le **créateur du serveur** peut utiliser cette commande.", ephemeral=True)


    async def setup(bot):
        await bot.add_cog(Moderation(bot))
