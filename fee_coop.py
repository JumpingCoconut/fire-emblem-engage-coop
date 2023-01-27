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
        # All information about our maps just in code
        self.mapdata = [ 
            None, 
            {"name": "Grass field", "difficulty": "normal", "maxturns": 2, "maxplayers": 5, "possible_rewards": []},
            {"name": "Flower field", "difficulty": "normal", "maxturns": 2, "maxplayers": 5, "possible_rewards": []},
            {"name": "Mountains", "difficulty": "normal", "maxturns": 2, "maxplayers": 5, "possible_rewards": []},
            {"name": "Winter forest", "difficulty": "hard", "maxturns": 2, "maxplayers": 5, "possible_rewards": []},
            {"name": "Desert sand", "difficulty": "hard", "maxturns": 3, "maxplayers": 5, "possible_rewards": []},
        ]
        # Active games from database
        self.db = TinyDB('db.json')
        logging.info("FeeCoop loaded!")

    # Makes one embed for each given game ID
    async def build_embed_for_game(self, doc_id):
        entry = self.db.get(doc_id=doc_id)
        code = entry["code"]
        map = entry.get("map")
        server_only = entry.get("server_only")
        group_pass = entry.get("group_pass")
        status = entry.get("status")
        turns = entry.get("turns", [])
        if len(turns) > 0:
            created_on = turns[0]["timestamp"]
            started_by = turns[0]["user"]
            started_on_server = turns[0]["server"]
            user = await interactions.get(self.bot, interactions.User, object_id=started_by)
            color = assign_color_to_user(user.username)
        else:
            color = interactions.Color.red()

        if status:
            title += " (" + status + ")"

        embed = interactions.Embed(title=code, color=color, provider=interactions.EmbedProvider(name="Fee coop"))
        if map:
            difficulty = self.mapdata[map]
            maxturns = self.mapdata[map]
            maxplayers = self.mapdata[map]
            possible_rewards = self.mapdata[map]
            mapname = self.mapdata[map]
            embed.description = mapname + " (" + difficulty + ")"

        if server_only or group_pass:
            # Group pass beats server ID
            if group_pass:
                embed.set_footer(interactions.EmbedFooter(text="Group pass: " + group_pass))
            elif server_only and started_on_server:
                guild = await interactions.get(self.bot, interactions.Guild, object_id=started_on_server)
                embed.set_footer(interactions.EmbedFooter(text="Only for server: " + guild.name))

        if created_on:
            embed.timestamp=datetime.fromisoformat(created_on)

        if started_by:
            embed.set_author(name=user.username + "#" + user.discriminator, icon_url=user.avatar_url)

        if len(turns) > 1:
            for turn in turns[1:]:
                username = turn["user"]
                server = turn["server"]
                if server != started_on_server:
                    guild = await interactions.get(self.bot, interactions.Guild, object_id=server)
                    username += " (from discord server " + server.name + ")"
                timestamp = turn["timestamp"]
                embed.add_field(name=username, value=timestamp, inline=True)
        
    # Rightclick to check the message for game IDs
    @interactions.extension_command(
        type=interactions.ApplicationCommandType.MESSAGE,
        name="Show Game"
    )
    async def fee_coop_rightclick_show_game(self, ctx):
        # Insert one test game
        new_item = {    "code": "666NB4R", 
                        "map": "1", 
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
        logging.info(str(results[0]["turns"][0]["user"]))
        user = await interactions.get(self.bot, interactions.User, object_id=results[0]["turns"][0]["user"])
        guild = await interactions.get(self.bot, interactions.Guild, object_id=results[0]["turns"][0]["server"])

        game_ids = ctx.target.content.split()
        results = self.db.search(Games.code.one_of(game_ids))
        if len(results) > 0:
            found_games = []
            for result in results:
                found_games = await self.build_embed_for_game(result.doc_id)
                #found_games.append("Code: " + result["code"] + " Map: " + result["map"])
            return await ctx.send(embeds=found_games, ephemeral=True)
        else:
            return await ctx.send("No valid codes found in this message.", ephemeral=True)
        

def setup(client):
    FeeCoop(client)