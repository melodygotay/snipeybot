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
            # Purge the specified number of messages
            deleted = await channel.purge(limit=index)
            delete_msg = await ctx.send(f"Deleted {len(deleted)} messages in {channel.mention}.")
            await self.confirmation_delete(delete_msg, 10)

        except discord.Forbidden:
            await ctx.send("I do not have permission to delete messages in that channel.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to clear messages: {e}")

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(Admin(bot))