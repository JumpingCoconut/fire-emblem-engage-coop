import asyncio
import datetime
import logging
import json
import chardet
import aiohttp
import interactions
from interactions import Button, SelectMenu, SelectOption, spread_to_rows, autodefer
import os
from dotenv import dotenv_values
from helpers import *
from tinydb import TinyDB, Query

# Set up logging
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO, handlers=[logging.FileHandler('logs/fee_coop.log'),logging.StreamHandler()])

app_base_dir = os.path.dirname(os.path.realpath(__file__))
logging.info("Initializing script from " + app_base_dir)

# load env variables
config = dotenv_values(app_base_dir + '/.env')
debug_mode=bool(config['DEBUG_MODE'] == "True")

# Discord interactions extension class
class FeeCoop(interactions.Extension):
    def __init__(self, client):
        self.bot: interactions.Client = client
        # All information about our games
        self.db = TinyDB('db.json')
        logging.info("FeeCoop loaded!")

    # Rightclick to check the message for game IDs
    @interactions.extension_command(
        type=interactions.ApplicationCommandType.MESSAGE,
        name="Show Game"
    )
    async def fee_coop_rightclick_show_game(self, ctx):
        # Insert one test game
        new_item = {    "code": "666NB4R", 
                        "map": "Mountains", 
                        "server_only" : False,
                        "group_pass" : "", 
                        "turns" : [
                                {
                                    "user" : str(ctx.user.id),
                                    "server" : str(ctx.guild_id),
                                    "timestamp" : datetime.datetime.utcnow().isoformat(),
                                },
                            ],
                    }
        self.db.insert(new_item) 
        # Now search an entry
        Games = Query()
        results = self.db.search(Games.code == "666NB4R")
        user = await interactions.get(self.bot, interactions.User, results["turns"][0]["user"])
        guild = await interactions.get(self.bot, interactions.Guild, results["turns"][0]["server"])


        messagetext = ctx.target.content
        return await ctx.send("Messagetext is: " + messagetext + " , Database is : " + str(results) + " User is "+ user + " and server is " + guild, ephemeral=True)
        

def setup(client):
    FeeCoop(client)