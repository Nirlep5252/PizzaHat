import datetime
import traceback
import typing
import uuid

import discord
import humanfriendly
from core.bot import PizzaHat
from core.cog import Cog
from discord.ext import commands
from discord.ext.commands import Context
from utils.ui import Paginator


class Mod(Cog, emoji=847248846526087239):
    """Keep your server safe!"""

    def __init__(self, bot: PizzaHat):
        self.bot: PizzaHat = bot

    async def warn_log(self, guild_id, user_id):
        data = await self.bot.db.fetchrow("SELECT * FROM warnlogs WHERE guild_id=$1 AND user_id=$2", guild_id, user_id)  # type: ignore

        if not data:
            print("No data")

        else:
            return data

    async def warn_entry(self, guild_id, user_id, reason, time):
        data = await self.warn_log(guild_id, user_id)

        if data == []:
            await self.bot.db.execute("INSERT INTO warnlogs (guild_id, user_id, warns, time) VALUES ($1, $2, $3, $4)", guild_id, user_id, [reason], [time])  # type: ignore
            return

        if data is not None:
            warns = data[2]
            times = data[3]

            if not warns:
                warns = [reason]
                times = [time]

            else:
                warns.append(reason)
                times.append(time)

            await self.bot.db.execute("UPDATE warnlogs SET time = $1, warns = $2 WHERE guild_id = $3 AND user_id = $4", times, warns, guild_id, user_id)  # type: ignore

    async def delete_warn(self, guild_id, user_id, index):
        data = await self.warn_log(guild_id, user_id)

        if data is not None:
            if len(data[2]) >= 1:
                data[2].remove(data[2][index])
                data[3].remove(data[3][index])
                return await self.bot.db.execute("UPDATE warnlogs SET warns = $1, time = $2 WHERE guild_id = $3 AND user_id = $4", data[2], data[3], guild_id, user_id)  # type: ignore

            else:
                await self.bot.db.execute("DELETE FROM warnlogs WHERE guild_id = $1 AND user_id = $2", guild_id, user_id)  # type: ignore

    @commands.command(aliases=["mn"])
    @commands.guild_only()
    @commands.has_permissions(manage_nicknames=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def modnick(self, ctx: Context, member: discord.Member):
        """
        Sets a random moderated nickname.

        In order for this to work, the bot must have Manage Nicknames permissions.

        To use this command, you must have Manage Nicknames permission.
        """
        try:
            nick = f"Moderated Nickname {uuid.uuid4()}"[:24]
            await member.edit(nick=nick)
            await ctx.send(f"{self.bot.yes} Nickname changed to `{nick}`")

        except discord.HTTPException:
            await ctx.send("Something went wrong.")

    @commands.command(aliases=["sn"])
    @commands.guild_only()
    @commands.has_permissions(manage_nicknames=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def setnick(self, ctx: Context, member: discord.Member, *, nick):
        """
        Sets a custom nickname.

        In order for this to work, the bot must have Manage Nicknames permissions.

        To use this command, you must have Manage Nicknames permission.
        """

        try:
            await member.edit(nick=nick)
            await ctx.send(
                f"{self.bot.yes} Nickname for {member.name} was changed to {member.mention}"
            )

        except discord.HTTPException:
            await ctx.send("Something went wrong.")

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_nicknames=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def decancer(self, ctx: Context, member: discord.Member):
        """
        Removes special characters and renames the member as "Moderated Nickname"

        In order for this to work, the bot must have Manage Nicknames permissions.

        To use this command, you must have Manage Nicknames permission.
        """

        characters = "!@#$%^&*()_+-=.,/?;:[]{}`~\"'\\|<>"

        try:
            if member.display_name[
                0
            ] in characters and not member.display_name.startswith("[AFK] "):
                await member.edit(
                    nick="Moderated Nickname",
                    reason=f"Decancered member (req. by: {ctx.author}).",
                )
                await ctx.send(f"{self.bot.yes} Successfully decancered {member}")

            if characters not in member.display_name[0]:
                await ctx.send("No special characters found.")

        except discord.HTTPException:
            await ctx.send("Something went wrong.")

    @commands.command(aliases=["sm"])
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def slowmode(self, ctx: Context, seconds: int = None):  # type: ignore
        """
        Change the slow-mode in the current channel.
        If no values are given, the bot returns slowmode of the current channel.

        In order for this to work, the bot must have Manage Messages permissions.

        To use this command, you must have Manage Messages permission.
        """

        if ctx.channel is discord.DMChannel:
            return await ctx.send("Slow-mode cannot be checked/added.")

        if seconds is None:
            seconds = ctx.channel.slowmode_delay  # type: ignore
            await ctx.send(f"The slowmode in this channel is `{seconds}` seconds")

        elif seconds == 0:
            await ctx.channel.edit(slowmode_delay=0)  # type: ignore
            await ctx.send(
                f"{self.bot.yes} Slow-mode set to none in this channel. Chat goes brrrr...."
            )

        else:
            await ctx.channel.edit(slowmode_delay=seconds)  # type: ignore
            await ctx.send(
                f"{self.bot.yes} Slow-mode in this channel changed to `{seconds}` seconds!"
            )

    @commands.group(aliases=["lockdown"])
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx: Context):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)

    @lock.command(name="channel")
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def lock_channel(self, ctx: Context, role: discord.Role = None, channel: discord.TextChannel = None):  # type: ignore
        """
        Locks a channel with role requirement.
        If role is not given, the bot takes the default role of the guild which is @everyone.

        Example: `p!lock channel [@role] [#channel]`

        In order for this to work, the bot must have Manage Channels permissions.

        To use this command, you must have Manage Channels permission.
        """

        if ctx.guild is not None:
            role = role or ctx.guild.default_role
            channel = channel or ctx.channel

            overwrite = channel.overwrites_for(role)
            overwrite.send_messages = False
            overwrite.add_reactions = False

            await channel.set_permissions(role, overwrite=overwrite)
            await ctx.message.add_reaction("🔒")

            em = discord.Embed(color=self.bot.color)
            em.add_field(
                name="🔒 Locked",
                value=f"{channel.mention} has been locked for {role.mention}",
                inline=False,
            )

            await ctx.send(embed=em)

    @lock.command(name="server")
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def lock_server(self, ctx: Context, role: discord.Role = None):  # type: ignore
        """
        Locks the whole server with role requirement.
        If role is not given, the bot takes the default role of the guild which is @everyone.

        In order for this to work, the bot must have Manage Channels permissions.

        To use this command, you must have Manage Channels permission.
        """

        if ctx.guild is not None:
            role = ctx.guild.default_role or role

            for tc in ctx.guild.text_channels:
                await tc.set_permissions(role, send_messages=False, add_reactions=False)

            for vc in ctx.guild.voice_channels:
                await vc.set_permissions(role, connect=False, speak=False)

            em = discord.Embed(
                title=f"{self.bot.yes} Server Locked",
                description=f"The server has been locked by a staff member. You are **not muted**.",
                color=self.bot.success,
            )

            await ctx.send(embed=em)

    @commands.group()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx: Context):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)

    @unlock.command(name="channel")
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def unlock_channel(self, ctx: Context, role: discord.Role = None, channel: discord.TextChannel = None):  # type: ignore
        """
        Unlocks a channel with role requirement.
        If role is not given, the bot takes the default role of the guild which is @everyone.

        Example: `p!unlock channel [@role] [#channel]`

        In order for this to work, the bot must have Manage Channels permissions.

        To use this command, you must have Manage Channels permission.
        """

        if ctx.guild is not None:
            role = role or ctx.guild.default_role
            channel = channel or ctx.channel

            overwrite = channel.overwrites_for(role)
            overwrite.send_messages = True
            overwrite.add_reactions = True

            await channel.set_permissions(role, overwrite=overwrite)
            await ctx.message.add_reaction("🔓")

            em = discord.Embed(color=self.bot.color)
            em.add_field(
                name="🔓 Unlocked",
                value=f"{channel.mention} has been unlocked for {role.mention}",
                inline=False,
            )

            await ctx.send(embed=em)

    @unlock.command(name="server")
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def unlock_server(self, ctx: Context, role: discord.Role = None):  # type: ignore
        """
        Unlocks the whole server with role requirement.
        If role is not given, the bot takes the default role of the guild which is @everyone.

        In order for this to work, the bot must have Manage Channels permissions.

        To use this command, you must have Manage Channels permission.
        """

        if ctx.guild is not None:
            role = ctx.guild.default_role or role

            for tc in ctx.guild.text_channels:
                await tc.set_permissions(
                    role,
                    send_messages=True,
                    add_reactions=True,
                    read_message_history=True,
                )

            for vc in ctx.guild.voice_channels:
                await vc.set_permissions(role, connect=True, speak=True)

            em = discord.Embed(
                title=f"{self.bot.yes} Server Unlocked",
                description=f"The server has been unlocked.",
                color=self.bot.success,
            )

            await ctx.send(embed=em)

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def hide(self, ctx: Context, role: discord.Role = None, channel: discord.TextChannel = None):  # type: ignore
        """
        Hides a channel from a given role or @everyone.

        In order for this to work, the bot must have Manage Channels permissions.

        To use this command, you must have Manage Channels permission.
        """

        if ctx.guild is not None:
            role = role or ctx.guild.default_role
            channel = channel or ctx.channel

            overwrite = channel.overwrites_for(role)
            overwrite.view_channel = False

            await channel.set_permissions(role, overwrite=overwrite)
            await ctx.send(f"{channel.mention} has been hidden from `{role}`")

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def expose(self, ctx: Context, role: discord.Role = None, channel: discord.TextChannel = None):  # type: ignore
        """
        Exposes a channel from a given role or @everyone.

        In order for this to work, the bot must have Manage Channels permissions.

        To use this command, you must have Manage Channels permission.
        """

        if ctx.guild is not None:
            role = role or ctx.guild.default_role
            channel = channel or ctx.channel

            overwrite = channel.overwrites_for(role)
            overwrite.view_channel = True

            await channel.set_permissions(role, overwrite=overwrite)
            await ctx.send(f"{channel.mention} has been exposed to `{role}`")

    @commands.command(aliases=["purge"])
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def clear(self, ctx: Context, amount: int = 100):
        """
        Deletes certain amount of messages in the current channel.
        If no amount is given, it deletes upto 100 messages.

        In order for this to work, the bot must have Manage Messages permissions.

        To use this command, you must have Manage Messages permission.
        """

        if ctx.channel is discord.DMChannel:
            return await ctx.send("Messages cannot be cleared.")

        if amount > 100:
            return await ctx.send(
                f"{self.bot.no} I can only purge 100 messages at a time."
            )

        else:
            await ctx.message.delete()
            await ctx.channel.purge(limit=amount)  # type: ignore
            await ctx.send(
                f"{self.bot.yes} {amount} messages cleared by {ctx.author}",
                delete_after=2.5,
            )

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def cleanup(self, ctx: Context, amount: int = 100):
        """
        Cleans up bot's messages in the current channel.
        If no amount is given, it deletes upto 100 messages.

        In order for this to work, the bot must have Manage Messages permissions.

        To use this command, you must have Manage Messages permission.
        """

        def is_bot(m):
            return m.author == self.bot.user

        if ctx.channel is discord.DMChannel:
            return await ctx.send("Cannot clear messages.")

        if amount > 100:
            return await ctx.send(
                f"{self.bot.no} I can only clear upto 100 messages at a time."
            )

        else:
            await ctx.channel.purge(limit=amount, check=is_bot)  # type: ignore
            await ctx.send(
                f"{self.bot.yes} {amount} messages cleared", delete_after=2.5
            )

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def kick(self, ctx: Context, member: discord.Member, *, reason=None):
        """
        Kicks a member from the server.

        In order for this to work, the bot must have Kick Members permissions.

        To use this command, you must have Kick Members permission.
        """

        try:
            if reason is None:
                reason = f"No reason provided.\nKicked by {ctx.author}"

            await member.kick(reason=reason)
            await ctx.send(f"{self.bot.yes} Kicked `{member}`")

        except Exception as e:
            print("".join(traceback.format_exception(e, e, e.__traceback__)))  # type: ignore

    @commands.command(aliases=["b"])
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def ban(
        self, ctx: Context, member: typing.Union[discord.Member, int], *, reason=None
    ):
        """
        Bans a member whether or not the member is in the server.
        You can ban the member using their ID or my mentioning them.

        In order for this to work, the bot must have Ban Members permissions.

        To use this command, you must have Ban Members permission.
        """

        try:
            if reason is None:
                reason = f"No reason provided\nBanned by {ctx.author}"

            if ctx.guild is not None:
                if isinstance(member, int):
                    await ctx.guild.ban(discord.Object(id=member), reason=f"{reason}")
                    user = await self.bot.fetch_user(member)
                    await ctx.send(f"{self.bot.yes} Banned `{user}`")

                else:
                    await member.ban(reason=f"{reason}", delete_message_days=0)
                    await ctx.send(f"{self.bot.yes} Banned `{member}`")

        except Exception as e:
            print("".join(traceback.format_exception(e, e, e.__traceback__)))  # type: ignore

    @commands.command(aliases=["mb"])
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def massban(
        self, ctx: Context, members: commands.Greedy[discord.Member], *, reason=None
    ):
        """
        Mass bans multiple members from the server.
        You can only ban users, who are in the server.

        In order for this to work, the bot must have Ban Members permissions.

        To use this command, you must have Ban Members permission.
        """

        try:
            if reason is None:
                reason = f"No reason provided\nBanned by {ctx.author}"

            if not len(members):
                await ctx.send("One or more required arguments are missing.")

            else:
                for target in members:
                    await target.ban(reason=reason, delete_message_days=0)
                    await ctx.send(f"{self.bot.yes} Banned `{target}`")

        except Exception as e:
            print("".join(traceback.format_exception(e, e, e.__traceback__)))  # type: ignore

    @commands.command(aliases=["sb"])
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def softban(self, ctx: Context, member: discord.Member, *, reason=None):
        """Soft bans a member from the server.

        A softban is basically banning the member from the server but
        then unbanning the member as well. This allows you to essentially
        kick the member while removing their messages.

        In order for this to work, the bot must have Ban Members permissions.

        To use this command, you must have Ban Members permission.
        """

        try:
            if reason is None:
                reason = f"No reason given.\nBanned by {ctx.author}"

            await ctx.guild.ban(member, reason)  # type: ignore
            await ctx.guild.unban(member, reason)  # type: ignore
            await ctx.send(f"{self.bot.yes} Sucessfully soft-banned {member}.")

        except Exception as e:
            print("".join(traceback.format_exception(e, e, e.__traceback__)))  # type: ignore

    @commands.command(aliases=["ub"])
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def unban(self, ctx: Context, id: int):
        """
        Unbans a member from the server using their ID.

        In order for this to work, the bot must have Ban Members permissions.

        To use this command, you must have Ban Members permission.
        """

        try:
            if ctx.guild is not None:
                user = self.bot.get_user(id)
                await ctx.guild.unban(
                    discord.Object(id=id), reason=f"Unbanned by {ctx.author}"
                )
                await ctx.send(f"{self.bot.yes} Unbanned `{user}`")

        except discord.NotFound:
            await ctx.send(
                "Not a valid previously banned member or the member could not be found."
            )

    @commands.command(aliases=["mute"])
    @commands.guild_only()
    @commands.has_permissions(moderate_members=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def timeout(
        self, ctx: Context, member: discord.Member, duration, *, reason=None
    ):
        """
        Mutes or timeouts a member for specific time.
        Maximum duration of timeout: 28 days (API limitation)
        Use 5m for 5 mins, 1h for 1 hour etc...

        In order for this to work, the bot must have Moderate Members permissions.

        To use this command, you must have Moderate Members permission.
        """

        try:
            if reason is None:
                reason = f"Action done by {ctx.author}"

            humanly_duration = humanfriendly.parse_timespan(duration)

            await member.timeout(
                discord.utils.utcnow() + datetime.timedelta(seconds=humanly_duration),
                reason=reason,
            )
            await ctx.send(
                f"{self.bot.yes} {member} has been timed out for {duration}.\nReason: {reason}"
            )

        except Exception as e:
            print("".join(traceback.format_exception(e, e, e.__traceback__)))  # type: ignore

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(moderate_members=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def unmute(self, ctx: Context, member: discord.Member, *, reason=None):
        """
        Unmutes or removes a member from timeout.

        In order for this to work, the bot must have Moderate Members permissions.

        To use this command, you must have Moderate Members permission.
        """

        try:
            if reason is None:
                reason = f"Action done by {ctx.author}"

            await member.timeout(None, reason=reason)
            await ctx.send(f"{self.bot.yes} {member} has been unmuted!")

        except Exception as e:
            print("".join(traceback.format_exception(e, e, e.__traceback__)))  # type: ignore

    @commands.group()
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx: Context):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)

    @role.command(name="add")
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def role_add(self, ctx: Context, user: discord.Member, *, role: discord.Role):
        """
        Assign role to a user.

        In order for this to work, the bot must have Manage Roles permissions.

        To use this command, you must have Manage Roles permission.
        """

        try:
            if role not in user.roles:
                await user.add_roles(role)
                await ctx.send(
                    f"{self.bot.yes} Successfully added `{role.name}` to {user}"
                )

            else:
                await ctx.send(f"{self.bot.no} {user} already has `{role.name}` role.")

        except Exception as e:
            print("".join(traceback.format_exception(e, e, e.__traceback__)))  # type: ignore

    @role.command(name="remove")
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def role_remove(
        self, ctx: Context, user: discord.Member, *, role: discord.Role
    ):
        """
        Remove role from a user.

        In order for this to work, the bot must have Manage Roles permissions.

        To use this command, you must have Manage Roles permission.
        """

        try:
            if role in user.roles:
                await user.remove_roles(role)
                await ctx.send(
                    f"{self.bot.yes} Successfully removed `{role.name}` from {user}"
                )

            else:
                await ctx.send(
                    f"{self.bot.no} {user} does not have `{role.name}` role."
                )

        except Exception as e:
            print("".join(traceback.format_exception(e, e, e.__traceback__)))  # type: ignore

    @role.command(name="create")
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def role_create(
        self,
        ctx: Context,
        *,
        role: discord.Role,
        color: discord.Color = discord.Color.default(),
        hoist: bool = False,
    ):
        """
        Create a new role in the server with given color and hoist options.

        In order for this to work, the bot must have Manage Roles permissions.

        To use this command, you must have Manage Roles permission.
        """

        try:
            if ctx.guild is not None:
                if role not in ctx.guild.roles:
                    await ctx.guild.create_role(
                        reason=f"Role created by {ctx.author}",
                        name=role.name,
                        color=color,
                        hoist=hoist,
                    )
                    await ctx.send(f"{self.bot.yes} Role created successfully!")

        except Exception as e:
            print("".join(traceback.format_exception(e, e, e.__traceback__)))  # type: ignore

    @role.command(name="delete")
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def role_delete(self, ctx: Context, *, role: discord.Role):
        """
        Delete an already existing role in the server.

        In order for this to work, the bot must have Manage Roles permissions.

        To use this command, you must have Manage Roles permission.
        """

        try:
            if ctx.guild is not None:
                if role in ctx.guild.roles:
                    await role.delete()
                    await ctx.send(f"{self.bot.yes} Role deleted successfully!")

        except Exception as e:
            print("".join(traceback.format_exception(e, e, e.__traceback__)))  # type: ignore

    @role.command(aliases=["list", "all"])
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def role_list(self, ctx: Context):
        """
        List all the server roles.
        """

        try:
            if ctx.guild is not None:
                roles = sorted(ctx.guild.roles, key=lambda x: x.position, reverse=True)
                embeds = []

                chunk_size = 10
                role_chunks = [
                    roles[i : i + chunk_size] for i in range(0, len(roles), chunk_size)
                ]

                for i, chunk in enumerate(role_chunks, 1):
                    description = "\n\n".join(
                        [
                            f"{role.mention} `({role.id})` • {role.name}"
                            for role in chunk
                        ]
                    )
                    embeds.append(
                        discord.Embed(
                            title=f"{ctx.guild.name} Roles ({len(roles)})",
                            description=description,
                            color=self.bot.color,
                            timestamp=ctx.message.created_at,
                        )
                        .set_thumbnail(url=ctx.guild.icon.url)  # type: ignore
                        .set_footer(text=f"Page {i}/{len(role_chunks)}")
                    )

                if not embeds:
                    return await ctx.send("No roles to display.")

                if len(embeds) == 1:
                    return await ctx.send(embed=embeds[0])

                view = Paginator(ctx, embeds)
                return await ctx.send(embed=embeds[0], view=view)

        except Exception as e:
            print("".join(traceback.format_exception(e, e, e.__traceback__)))  # type: ignore

    @commands.group()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def channel(self, ctx: Context):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)

    @channel.command(name="create")
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def channel_create(self, ctx: Context, name):
        """
        Create a new channel in the server.
        """

        try:
            if ctx.guild is not None:
                await ctx.guild.create_text_channel(name)
                await ctx.send(f"{self.bot.yes} Channel created successfully!")

        except Exception as e:
            print("".join(traceback.format_exception(e, e, e.__traceback__)))  # type: ignore

    @channel.command(name="delete")
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def channel_delete(self, ctx: Context, channel: discord.TextChannel):
        """Delete a channel in the server."""

        try:
            if ctx.guild is not None:
                await channel.delete()
                await ctx.send(f"{self.bot.yes} Channel deleted successfully!")

        except Exception as e:
            print("".join(traceback.format_exception(e, e, e.__traceback__)))  # type: ignore

    @channel.command(name="list", aliases=["all"])
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def channel_list(self, ctx: Context):
        """
        List all the server channels.
        """

        try:
            if ctx.guild is not None:
                channels = [
                    channel
                    for channel in ctx.guild.channels
                    if not isinstance(channel, discord.CategoryChannel)
                ]
                embeds = []

                # Group channels by category
                channels_by_category = {}
                channels_without_category = []

                for channel in channels:
                    if isinstance(channel, discord.TextChannel) and channel.category:
                        category_id = str(channel.category.id)
                        if category_id not in channels_by_category:
                            channels_by_category[category_id] = {
                                "category": channel.category,
                                "channels": [],
                            }
                        channels_by_category[category_id]["channels"].append(channel)
                    else:
                        channels_without_category.append(channel)

                # Create embed for channels without categories
                if channels_without_category:
                    description = "".join(
                        [
                            f"```asciidoc\nNo category\n\t{channel.name} :: {channel.type} :: {channel.id}\n```"
                            for channel in channels_without_category
                        ]
                    )

                    embeds.append(
                        discord.Embed(
                            title=f"{ctx.guild.name} Channels ({len(channels)})",
                            description=description,
                            color=self.bot.color,
                            timestamp=ctx.message.created_at,
                        )
                        .set_thumbnail(url=ctx.guild.icon.url)  # type: ignore
                        .set_footer(text=f"Page 1/{len(channels_by_category) + 1}")
                    )

                # Create embeds for channels with categories
                total_category_pages = len(channels_by_category)
                category_page_count = 1 if channels_without_category else 0

                for i, category_info in enumerate(
                    channels_by_category.values(), category_page_count + 1
                ):
                    category = category_info["category"]
                    category_name = category.name if category else "No category"
                    category_id = category.id if category else "No category"

                    description = "".join(
                        [
                            f"```asciidoc\n{category_name} :: '{category_id}'\n\t{channel.name} :: {channel.type} :: {channel.id}\n```"
                            for channel in category_info["channels"]
                        ]
                    )

                    embeds.append(
                        discord.Embed(
                            title=f"{ctx.guild.name} Channels ({len(channels)})",
                            description=description,
                            color=self.bot.color,
                            timestamp=ctx.message.created_at,
                        )
                        .set_thumbnail(url=ctx.guild.icon.url)  # type: ignore
                        .set_footer(text=f"Page {i}/{total_category_pages + 1}")
                    )

                if not embeds:
                    return await ctx.send("No channels to display.")

                if len(embeds) == 1:
                    return await ctx.send(embed=embeds[0])

                view = Paginator(ctx, embeds)
                return await ctx.send(embed=embeds[0], view=view)

        except Exception as e:
            print("".join(traceback.format_exception(e, e, e.__traceback__)))  # type: ignore

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def warn(self, ctx: Context, member: discord.Member, *, reason=None):
        """
        Warns a user.

        To use this command, you must have Manage Messages permission.
        """

        if reason is None:
            reason = f"No reason given.\nWarned done by {ctx.author}"

        try:
            if ctx.guild is not None:
                if member == ctx.author or member == self.bot.user:
                    return await ctx.send("You cant warn yourself or the bot.")

                if not ctx.author.top_role.position == member.top_role.position:  # type: ignore
                    if not ctx.author.top_role.position > member.top_role.position:  # type: ignore
                        return await ctx.send(
                            "You cant warn someone that has higher or same role heirarchy."
                        )

                await self.warn_entry(
                    ctx.guild.id,
                    member.id,
                    reason,
                    float(ctx.message.created_at.timestamp()),
                )

                em = discord.Embed(
                    title=f"{self.bot.yes} Warned User",
                    description=f"Moderator: {ctx.author.mention}\nMember: {member.mention}\nReason: {reason}",
                    color=self.bot.success,
                    timestamp=datetime.datetime.utcnow(),
                )

                await ctx.send(embed=em)

        except Exception as e:
            print("".join(traceback.format_exception(e, e, e.__traceback__)))  # type: ignore

    @commands.command(aliases=["warns"])
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def warnings(self, ctx: Context, member: discord.Member = None):  # type: ignore
        """
        Displays the warnings of the user.
        If no user is given, the bot sends your warnings.
        """

        if member is None:
            member = ctx.author  # type: ignore

        if ctx.guild and member.avatar is not None:
            data = await self.warn_log(ctx.guild.id, member.id)
            em = discord.Embed(
                title=f"Warnings of {member.name}",
                description=f"{self.bot.yes} This user has no warns!",
                color=self.bot.success,
                timestamp=datetime.datetime.utcnow(),
            )
            em.set_thumbnail(url=member.avatar.url)

            if not data:
                return await ctx.send(embed=em)

            if not len(data[2]):
                return await ctx.send(embed=em)

            for i in range(len(data[2])):
                reason = data[2][i]

                em = discord.Embed(
                    title=f"Warnings of {member.name} | {len(data[2])} warns",
                    description=f"Reason: {reason}\nWarn ID: `{data[3][i]}`",
                    color=self.bot.color,
                    timestamp=datetime.datetime.utcnow(),
                )

            await ctx.send(embed=em)

    @commands.command(aliases=["delwarn"])
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def deletewarn(self, ctx: Context, member: discord.Member, warn_id: float):
        """
        Deletes a warn of the user with warn ID.

        To use this command, you must have Manage Messages permission.
        """

        try:
            if ctx.guild is not None:
                data = await self.warn_log(ctx.guild.id, member.id)
                if data == []:
                    return await ctx.send(f"{self.bot.no} This user has no warns!")

                if data[2] and warn_id in data[3]:  # type: ignore
                    index = data[3].index(warn_id)  # type: ignore
                    await self.delete_warn(ctx.guild.id, member.id, index)
                    return await ctx.send(f"{self.bot.yes} Warn entry deleted!")

                else:
                    return await ctx.send(
                        f"{self.bot.no} No warn entry found for this user."
                    )

        except Exception as e:
            print("".join(traceback.format_exception(e, e, e.__traceback__)))  # type: ignore


async def setup(bot):
    await bot.add_cog(Mod(bot))
