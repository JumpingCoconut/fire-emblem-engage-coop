from dotenv import dotenv_values
import interactions
import os

# load env variables
config = dotenv_values('.env')

bot = interactions.Client(
    token=config['DISCORD_TOKEN'],
)
debug_mode=bool(config['DEBUG_MODE'] == "True")

# To use files in CommandContext send, you need to load it as an extension.
bot.load("interactions.ext.files")
bot.load("fee_coop")
feecoop = bot.get_extension("FeeCoop")

@bot.event
async def on_start():
    print("Discord bot is running!")
    #await feecoop.read_soundfiles()

bot.start()