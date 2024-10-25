import discord
from discord.ext import commands
import asyncio

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def confirmation_delete(self, confirmation: discord.Message, time: int):
        await asyncio.sleep(time)  # Time in seconds   
        try:
            await confirmation.delete()
        except discord.HTTPException:
            pass  # Ignore if the message is not found

    @commands.command()
    async def clear(self, ctx, index: int = None, channel: discord.TextChannel = None):
        if index is None:
            await ctx.send("Please provide a valid number of messages to clear. Example: `!clear 10`")
            return
        
        if channel is None:
            channel = ctx.channel  # Use the current channel if no channel is specified

        try:
            deleted = await channel.purge(limit=index)    # Purge the specified number of messages
            delete_msg = await ctx.send(f"Deleted {len(deleted)} messages in {channel.mention}.")
            await self.confirmation_delete(delete_msg, 10)

        except discord.Forbidden:
            await ctx.send("I do not have permission to delete messages in that channel.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to clear messages: {e}")

    @commands.command(name="play")
    async def play(self, ctx: commands.Context, time: int, unit: str):
        if unit == "s" or unit == "seconds":
            seconds = time
        elif unit == "m" or unit == "minutes":
            seconds = time * 60
        elif unit == "h" or unit == "hours":
            seconds = time * 3600
        else:
            await ctx.send("Invalid time unit. Use 'seconds', 'minutes', or 'hours'.")
            return

        await asyncio.sleep(seconds)

        await ctx.send(f"Reminder: don't forget to update your account {ctx.author.mention}")

# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(Admin(bot))