import discord
from discord.ext import commands
import asyncio

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()  # Make sure this is a listener inside a Cog
    async def on_message(self, message):
        # Ignore messages from the bot itself to prevent loops
        if message.author == self.bot.user:  # Corrected this line
            return
        
        # Check if the message starts with the command prefix
        if message.content.startswith(self.bot.command_prefix):
            return  # Skip the listener if it's a command

        # Check if "hello snipey" is in the message content
        if "hello snipey" in message.content.lower():
            await message.channel.send(f"Hi {message.author.mention}!")

        if "mvponaloss" in message.content.lower():
            await message.channel.send("FeelsAbzeerMan")
        
        # Allow the bot to process other commands
        await self.bot.process_commands(message)  

    @commands.command()
    async def helpme(self, ctx):
        help_txt = (
            "**Here are the commands you can use:**\n\n"
            "**Chat Commands"
            "```"
            "!clear  <#>: Clears the specified number of messages in the current channel.\n"
            "```"
            "**Snipe Calculator Commands"
            "```"
            "!avg       : Calculates the average rank of ranks entered.\n"
            "!delete <#>: Deletes a previously entered rank. Use the list number to delete.\n"
            "!rank      : Adds ranks for calculation. Accepts up to 5 ranks in a single line.\n"
            "!ranklist  : Lists ranks entered.\n"
            "!reset     : Clears ranks list.\n\n"
            "```"
            "**User Management**\n"
            "```"
            "!myaccs    : Displays all existing accounts from invoking user.\n"
            "!newacc    : Adds a new account.  Use format '!newacc <accname> <rank&points>'.\n"
            "!rmacc     : Deletes existing account.  Use format '!removeacc <accname>.\n"
            "!snipe     : Get the best combination of accounts for a snipe.  Use format '!snipe <targetrank> <number of players>'.\n"
            "!update    : Updates existing account points.  Use format '!update <accname> <rank&points>'.\n\n"
            "For every command that requires rank input, the format is: s1 500.\n"
            "```"
        )
        await ctx.send(help_txt)

    async def confirmation_delete(self, confirmation: discord.Message, time: int):
        await asyncio.sleep(time)  # Time in seconds   
        try:
            await confirmation.delete()
        except discord.HTTPException:
            pass  # Ignore if the message is not found

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(General(bot))