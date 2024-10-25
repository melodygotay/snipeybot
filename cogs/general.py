import discord
from discord.ext import commands
#import asyncio

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore messages from the bot itself to prevent loops
        if message.author == self.bot.user:
            return

        if message.content.startswith(self.bot.command_prefix):
            return  # Skip the listener if it's a command

        # Check if "hello snipey" is in the message content
        if "hello snipey" in message.content.lower():
            await message.channel.send(f"Hi {message.author.mention}!")

        if "mvponaloss" in message.content.lower():
            await message.channel.send("FeelsAbzeerMan")

        if "thank you snipey" in message.content.lower():
            await message.channel.send(f"You're welcome {message.author.mention}!")
        
        # Allow the bot to process other commands
        await self.bot.process_commands(message)  

    @commands.command()
    async def helpme(self, ctx):
        embed = discord.Embed(
            title="Snipey Commands",
            description="Here are the available commands and their usage:",
            color=discord.Color.purple()
        )
        embed.add_field(name="**General Commands**", value="", inline=False)
        embed.add_field(name="", value="`!clear <#> `: Clears the specified number of messages in the current channel.", inline=False)
        embed.add_field(name="", value="`!devlog    `: Displays the latest changes made to snipey.", inline=False)
        embed.add_field(name="", value="`!info      `: Shows more information about these commands.", inline=False)
        embed.add_field(name="**Snipe Calculator Commands**", value="", inline=False)
        embed.add_field(name="", value="`!avg       `: Calculates the average rank of the ranks already entered.", inline=False)
        embed.add_field(name="", value="`!delete <#>`: Deletes a previously entered rank. Use the !ranklist number to delete.", inline=False)
        embed.add_field(name="", value="`!rank      `: Adds ranks for calculation. Accepts up to 5 ranks in a single line. Space separated.", inline=False)
        embed.add_field(name="", value="`!ranklist  `: Lists ranks entered.", inline=False)
        embed.add_field(name="", value="`!reset     `: Clears ranks list.", inline=False)
        embed.add_field(name="**User Management**", value="", inline=False)
        embed.add_field(name="", value="`!myaccs    `: Displays all existing accounts from invoking user.  Use `!myaccs @<another user>` to see their accounts.", inline=False)
        embed.add_field(name="", value="`!newacc    `: Adds a new account.  Use format `!newacc <accname> <rank&points>`.", inline=False)
        embed.add_field(name="", value="`!played    `: Adds today's date as the last date account was played on. `!info played` for more uses.", inline=False)
        embed.add_field(name="", value="`!rmacc     `: Deletes existing account.  Use format '!removeacc <accname>.", inline=False)
        embed.add_field(name="", value="`!snipe     `: Get the best combination of accounts for a snipe.  Use format `!snipe <target rank>`.", inline=False)
        embed.add_field(name="", value="`!update    `: Updates existing account points.  Use format `!update <accname> <rank&points>`.\n", inline=False)
        embed.set_footer(text="For every command that requires rank input, the format is: s1 500.")
        await ctx.send(embed=embed)

    @commands.command(name="info")
    async def info(self, ctx, cmd_name: str):
        if cmd_name == "snipe":
            await ctx.send("Use format '!snipe <targetrank> <number of players>'. To filter accounts by user, add their names with @ after the command.\n`!snipe g1 500 2 @user1 @user2`")
        elif cmd_name == "update":
            await ctx.send("Use format '!update <acc_name> <rank&points>.\n`!update <accname> g1 500.`")
        elif cmd_name == "played":
            await ctx.send("Use format `!played <acc_name>` to use today's date.  Otherwise, use `!played <acc_name> <Aug 2>`.")
        else:
            await ctx.send("Please add an existing command name to your info command to see more details.")

    @commands.command(name="devlog")
    async def devlog(self, ctx, version: float = None):
        if version is None:
            embed = discord.Embed(
                title="Snipey 0.1.1 October 23rd, 2024\n\n",
                color=discord.Color.purple()
            )
            embed.add_field(
                name="Account Management\n",
                value="- Fixed case sensitivity causing issues when using the `!update` command.  Users are now able to use mismatched casing when referencing their account names.\n"
                    "- Fixed an issue that prevented two different users to have two accounts with the same name.\n"
                    "-# - One user will still not be able to have two accounts with the same name to avoid creating duplicates.",
                inline=False
            )        
            embed.add_field(
                name="Comp Tracker!\n",
                value="- Added a tool to track compositions for draft play.\n"
                    "- Added a !flip command for coin flips.\n"
                    "- Added an interactive !ban @<other user> command for map ban phase.\n"
                    "- Added functionality for self closing matches.\n"
                    "- Added team name parsing from abbreviations.",
                inline=False
            )
            embed.add_field(
                name="Visual Updates\n",
                value="- Updated overall look of `!myaccs` command.\n"
                    "- Updated overall look of `!helpme command`.\n\n"
                "-# For previous log, use `!devlog 1.0`",
                inline=False
            )
            embed.set_footer(text=f"- - - Requested by {ctx.author.display_name} - - -")

            await ctx.send(embed=embed)
            return
        
        if version == 1.0:
            embed = discord.Embed(
                title ="Snipey 0.1.0 October 20th, 2024\n\n",
                color=discord.Color.purple()
            )
            embed.add_field(
                name="Account Management\n",
                value="- Added a 'Last Played' feature that allows users to track how many days since an account was played.\n"
                "-# - This feature will (in the future) remind players after 14 and 21 days of account inactivity.  Additionally, users can check how many days it has been since the last time they played by using the !lastplayed command.\n\n",
                inline=False
            )
            embed.add_field(
                name="General\n",
                value="- Added more responses to user messages.\n"
                "- Added more commands to 'helpme' and 'info'\n\n",
                inline=False         
            )
            embed.add_field(
                name="Visual Updates\n",
                value="- Added a Last Played column to the !myaccs table.\n",
                inline=False
            )
            embed.set_footer(text=f"- - - Requested by {ctx.author.display_name} - - -")
            await ctx.send(embed=embed)
            return

# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(General(bot))