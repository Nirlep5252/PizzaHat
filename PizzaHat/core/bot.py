import datetime
import sys
import traceback
from logging.config import dictConfig

import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import CommandError, Context
from discord.ext.commands.errors import ExtensionAlreadyLoaded

import core.database as db

INITIAL_EXTENSIONS = [
    # 'cogs.activities',
    "cogs.admin",
    "cogs.dev",
    "cogs.emojis",
    "cogs.games",
    "cogs.images",
    "cogs.meta",
    "cogs.mod",
    # 'cogs.music',
    "cogs.polls",
    "cogs.tags",
    "cogs.tickets",
    "cogs.utility",
]

SUB_EXTENSIONS = [
    "utils.automod",
    "utils.events",
    "utils.help",
]

LOGGING_CONFIG = {
    "version": 1,
    "disabled_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)-10s - %(asctime)s - %(module)-15s : %(message)s",
        },
        "standard": {
            "format": "%(levelname)-10s - %(name)-15s : %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "console2": {
            "level": "WARNING",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "formatter": "verbose",
            "filename": "bot.log",
            "mode": "w",
        },
    },
    "loggers": {
        "bot": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "discord": {
            "handlers": ["console2", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

dictConfig(LOGGING_CONFIG)

description = """
I'm PizzaHat, a bot made by DTS#5976 to provide some epic server utilities.
I have features such as moderation, utiltity, games and more!

I'm also open source. You can see my code on [GitHub](https://github.com/DTS-11/PizzaHat)
"""


class PizzaHat(commands.Bot):
    bot_app_info: discord.AppInfo

    def __init__(self):
        allowed_mentions = discord.AllowedMentions(
            roles=False, everyone=False, users=True
        )
        intents = discord.Intents(
            guilds=True,
            members=True,
            bans=True,
            emojis=True,
            voice_states=True,
            messages=True,
            reactions=True,
            message_content=True,
        )

        super().__init__(
            command_prefix=commands.when_mentioned_or("p!", "P!"),
            description=description,
            intents=intents,
            allowed_mentions=allowed_mentions,
            case_insensitive=True,
            strip_after_prefix=True,
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.watching, name="p!help"
            ),
        )

        self._BotBase__cogs = commands.core._CaseInsensitiveDict()
        self.yes = "<:yes:813819712953647206>"
        self.no = "<:no:829841023445631017>"
        self.color = 0x456DD4
        self.success = discord.Color.green()
        self.failed = discord.Color.red()
        self.session = aiohttp.ClientSession()

    async def on_ready(self):
        if not hasattr(self, "uptime"):
            self.uptime = datetime.datetime.utcnow()

        print(f"Logged in as {self.user}")
        # self.togetherControl = await DiscordTogether(os.getenv("TOKEN"), debug=True)  # type: ignore

    async def setup_hook(self) -> None:
        self.bot_app_info = await self.application_info()
        self.owner_id = self.bot_app_info.owner.id

        # Create DB connection
        self.db = await db.create_db_pool()

        # Loading cogs...
        success = fail = 0
        total = len(INITIAL_EXTENSIONS + SUB_EXTENSIONS)

        for ext in INITIAL_EXTENSIONS:
            try:
                await self.load_extension(ext)
                success += 1

            except Exception as e:
                print(f"Failed to load extension {ext}")
                print("".join(traceback.format_exception(e, e, e.__traceback__)))  # type: ignore
                fail += 1

        for sub_ext in SUB_EXTENSIONS:
            try:
                await self.load_extension(sub_ext)
                success += 1

            except Exception as e:
                print(f"Failed to load extension: {sub_ext}")
                print("".join(traceback.format_exception(e, e, e.__traceback__)))  # type: ignore
                fail += 1

        try:
            await self.load_extension("jishaku")
            print("Jishaku has been loaded.")

        except ExtensionAlreadyLoaded:
            pass

        print(
            f"Loaded all cogs.\nSuccess: {success}, Fail: {fail}\nDone! ({success+fail}/{total})"
        )
        print("=========================")

    # async def on_wavelink_node_ready(self, node: wavelink.Node):
    #     print(f"Node: {node.identifier} is ready.")

    # async def on_wavelink_track_end(
    #     self, player: wavelink.Player, track: wavelink.Track, reason: str
    # ):
    #     ctx = player.ctx  # type: ignore
    #     vc: player = ctx.voice_client  # type: ignore

    #     track.info["requester"] = ctx.author
    #     wavelink_track = wavelink.Track(track.id, track.info)

    #     if vc.loop:
    #         return await vc.play(track)

    #     try:
    #         next_song = vc.queue.get()
    #         await vc.play(next_song)

    #         em = discord.Embed(color=self.color)
    #         em.add_field(
    #             name="▶ Now playing",
    #             value=f"[{next_song.title}]({next_song.uri})",
    #             inline=False,
    #         )
    #         em.add_field(
    #             name="⌛ Song Duration",
    #             value=str(datetime.timedelta(seconds=next_song.duration)),
    #             inline=False,
    #         )
    #         em.add_field(name="👥 Requested by", value=wavelink_track, inline=False)
    #         em.add_field(name="🎵 Song by", value=next_song.author, inline=False)
    #         em.set_thumbnail(url=vc.source.thumbnail)

    #         await ctx.send(embed=em)

    #     except wavelink.errors.QueueEmpty:
    #         pass

    async def on_command_error(self, ctx: Context, error: CommandError) -> None:
        if isinstance(error, commands.CommandNotFound):
            pass

        elif isinstance(error, commands.NotOwner):
            pass

        if isinstance(error, commands.NoPrivateMessage):
            await ctx.author.send("This command cannot be used in private messages.")

        elif isinstance(error, commands.DisabledCommand):
            await ctx.author.send("Sorry. This command is disabled and cannot be used.")

        elif isinstance(error, commands.BotMissingPermissions):
            if error.missing_permissions[0] == "send_messages":
                return

            await ctx.send(
                "I am missing **{}** permissions.".format(
                    " ".join(error.missing_permissions[0].split("_")).title()
                )
            )

        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(
                "You need **{}** perms to run this command.".format(
                    " ".join(error.missing_permissions[0].split("_")).title()
                )
            )

        elif isinstance(error, commands.MaxConcurrencyReached):
            await ctx.send(
                "An instance of this command is already running...\n"
                f"You can only run `{error.number}` instances at the same time."
            )

        elif isinstance(error, commands.ArgumentParsingError):
            await ctx.send(str(error))

        elif isinstance(error, commands.CommandInvokeError):
            original = error.original
            if not isinstance(original, discord.HTTPException):
                if ctx.command is not None:
                    print(f"In {ctx.command.qualified_name}:", file=sys.stderr)
                    traceback.print_tb(original.__traceback__)
                    print(f"{original.__class__.__name__}: {original}", file=sys.stderr)
                    print()
                    print()

        elif isinstance(error, commands.MissingRequiredArgument):
            if ctx.command is not None:
                em = discord.Embed(
                    title=f"{ctx.command.name} {ctx.command.signature}",
                    description=ctx.command.help,
                    color=discord.Color.og_blurple(),
                )

                await ctx.send(embed=em)

    @property
    def owner(self) -> discord.User:
        return self.bot_app_info.owner
