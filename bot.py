import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Load cogs in the 'cogs' directory
async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'Loaded cog: {filename[:-3]}')
            except Exception as e:
                print(f'Failed to load cog {filename[:-3]}: {e}')

async def confirmation_delete(confirmation: discord.Message, time: int):
    await asyncio.sleep(time)  # Time in seconds   
    try:
        await confirmation.delete()
    except discord.HTTPException:
        pass  # Ignore if the message is not found

@bot.event
async def on_ready():
    #channel_id = 
    #channel = bot.get_channel(channel_id)
    #msg = "snipey has woken up!"
    #await channel.send(msg)
    #await confirmation_delete(msg, 10)
    print(f'Logged in as {bot.user.name}')

async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())