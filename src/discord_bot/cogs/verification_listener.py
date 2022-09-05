import discord
from discord.ext import commands
from discord.ext import tasks

from ..environment import ROLES, START_CHANNEL, GUILD, NOT_BEFORE, CHECK_PERIOD, ONBOARDING_CHANNEL, ONBOARDING_ROLE
from ..log_setup import logger

from .buttons import OnboardingButtons, EntryPointView


class VerificationListener(commands.Cog):
    """
    Give member target roles if member accepts rules screen, check for members that were missed
    """

    def __init__(self, bot: commands.Bot):
        # bot is single server based - for now...
        self.bot = bot
        self.guild: discord.Guild = bot.get_guild(GUILD)
        print(self.guild)
        self.roles = [self.guild.get_role(role) for role in ROLES]
        self.walk_members.start()  # start backup task
        self.onboarding_channel = self.guild.get_channel(ONBOARDING_CHANNEL)
        self.onboarding_role = self.guild.get_role(ONBOARDING_ROLE)

    async def cog_load(self):
        """
        Sends a new start button every time, to ensure that the current button is functional
        """
        await self.onboarding_channel.purge()
        await self.onboarding_channel.send("Klick auf den Button und wähle die Optionen, die auf dich zutreffen.\n"
                                           "Bei Problemen wende dich bitte an die Serverleitung :)",
                                           view=EntryPointView(self.bot, "Freischalten"))

    @commands.Cog.listener()
    async def on_member_update(self, before_member: discord.Member, after_member: discord.Member):
        """ Give member target roles if member accepts rules screen """

        if after_member.guild.id != GUILD:
            return

        if before_member.pending and not after_member.pending:

            await after_member.send(self.get_welcome_text(after_member))

            # send message containing the selection buttons - this is a new message on purpose
            # we can edit this message without losing the greeting text
            await after_member.send("Bitte wähle hier aus, was auf dich zutrifft.\n"
                                    "Ignorier diese Nachricht, wenn du dies bereits auf dem Server gemacht hast :)",
                                    view=OnboardingButtons(self.bot))

            # set member in onboarding mode
            # allow only to see the onboarding channel where users are confronted with buttons
            await after_member.add_roles(self.onboarding_role)

    @tasks.loop(minutes=CHECK_PERIOD)
    async def walk_members(self):
        """ Walk all members every five minutes to fix errors that may occur due to downtimes or other errors """
        logger.info("Executing member check")
        i = 0
        j = 0
        async for member in self.guild.fetch_members():
            # check amount of roles,
            # if member is not pending
            # if he joined after a specific date to not verify old members
            if len(member.roles) == 1 and not member.pending and member.joined_at.replace(tzinfo=None) > NOT_BEFORE:
                # set user in onboarding mode
                await member.add_roles(self.onboarding_role)
                # also send welcome and
                await member.send(self.get_welcome_text(member))
                # also sending the buttons
                await member.send("Bitte wähle hier aus, was auf dich zutrifft.\n"
                                  "Ignorier diese Nachricht, wenn du dies bereits auf dem Server gemacht hast :)",
                                  view=OnboardingButtons(self.bot))
                i += 1

            # member has onboarding and interaction is timed out
            if self.onboarding_role in member.roles:
                private_chat = member.dm_channel

                async for message in private_chat.history(limit=20):
                    interaction = message.interaction
                    if interaction and interaction.is_expired():
                        logger.info(f"Sent new interaction message to {member.id}")
                        await member.send(
                            "Bitte wähle hier aus, was auf dich zutrifft.\n"
                            "Ignorier diese Nachricht, wenn du dies bereits auf dem Server gemacht hast :)",
                            view=OnboardingButtons(self.bot)
                        )
                        j +=1
                        break

        if i > 0:
            logger.info(f"Verified {i} member that accepted the rules but didn't get the roles")

        if j > 0:
            logger.info(f"Sent {j} members new interaction message")

    def get_welcome_text(self, member: discord.Member):
        return (f"Hey {member.display_name}, willkommen auf dem _{self.guild.name}_ Discord!\n"
                f"Schau für eine kurze Übersicht über den Server gerne mal in "
                f"{self.guild.get_channel(START_CHANNEL).mention} vorbei.\n"
                "Bei Fragen kannst du dich jederzeit an uns wenden,\n"
                "~Die Serverleitung")


async def setup(bot: commands.Bot):
    await bot.add_cog(VerificationListener(bot))
