import asyncio
import calendar
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
            {"name": "Verdant Plain", "difficulty": "Normal", "maxturns": 2, "maxplayers": 5, "possible_rewards": ["Res Crystal", "Hit Crystal", "Avo Crystal", "Ddg Crystal"]},
            {"name": "Floral Field", "difficulty": "Normal", "maxturns": 2, "maxplayers": 5, "possible_rewards": ["Def Crystal", "Hit Crystal", "Avo Crystal", "Ddg Crystal"]},
            {"name": "Mountain Peak", "difficulty": "Normal", "maxturns": 2, "maxplayers": 5, "possible_rewards": ["Dex Crystal", "Hit Crystal", "Avo Crystal", "Ddg Crystal"]},
            {"name": "Winter Forest", "difficulty": "Hard", "maxturns": 2, "maxplayers": 5, "possible_rewards": ["Spd Crystal", "Hit Crystal", "Avo Crystal", "Ddg Crystal"]},
            {"name": "Desert Dunes", "difficulty": "Hard", "maxturns": 3, "maxplayers": 5, "possible_rewards": ["Crit Crystal", "Hit Crystal", "Avo Crystal", "Ddg Crystal"]},
        ]
        self.emoji = {
            "avo" : "<:avo:1068643333716586637>", 
            "crit" : "<:crit:1068643336178630796>",
            "ddg" : "<:ddg:1068643337550180403>",
            "dex" : "<:dex:1068643339227897977>",
            "hit" : "<:hit:1068643341757055006>",
            "res" : "<:res:1068643357322117121>",
            "spd" : "<:spd:1068643359448637552>",
            "map1" : "<:map1:1068643343418015905>",
            "map2" : "<:map2:1068643345334800467>",
            "map3" : "<:map3:1068643347486486618>",
            "map4" : "<:map4:1068643350376353792>",
            "map5" : "<:map5:1068643351697559693>",
        }

        # Active games from database
        self.db = TinyDB('db.json')

        # Test data
        new_item = {    "code": "666NB4R", 
                        "map": 3, 
                        "server_only" : False,
                        "group_pass" : "", 
                        "status" : "fail",
                        "turns" : [
                                {
                                    "user" : "330955309763788800", # str(ctx.user.id),
                                    "server" : "490564578128822293", #str(ctx.guild_id),
                                    "timestamp" : datetime.datetime.utcnow().isoformat(),
                                },
                            ],
                    }
        self.db.insert(new_item) 
        new_item = {    "code": "638P526", 
                        "map": 4, 
                        "server_only" : True,
                        "group_pass" : "", 
                        "status" : "open",
                        "turns" : [
                                {
                                    "user" : str(523211690213376005),
                                    "server" : str(870019135646613524),
                                    "timestamp" : datetime.datetime.utcnow().isoformat(),
                                },
                                {
                                    "user" : str(330955309763788800),
                                    "server" : str(490564578128822293),
                                    "timestamp" : datetime.datetime.utcnow().isoformat(),
                                },
                            ],
                    }
        self.db.insert(new_item) 
        new_item = {    "code": "8CL6W96", 
                        "map": 5, 
                        "server_only" : False,
                        "group_pass" : "11118888", 
                        "status" : "success",
                        "turns" : [
                                {
                                    "user" : str(234861064532131842),
                                    "server" : str(870019135646613524),
                                    "timestamp" : datetime.datetime.utcnow().isoformat(),
                                },
                                {
                                    "user" : str(330955309763788800),
                                    "server" : str(870019135646613524),
                                    "timestamp" : datetime.datetime.utcnow().isoformat(),
                                },
                                {
                                    "user" : str(523211690213376005),
                                    "server" : str(490564578128822293),
                                    "timestamp" : datetime.datetime.utcnow().isoformat(),
                                },
                                {
                                    "user" : str(363144319739232257),
                                    "server" : str(870019135646613524),
                                    "timestamp" : datetime.datetime.utcnow().isoformat(),
                                },
                                {
                                    "user" : str(307624030704238592),
                                    "server" : str(490564578128822293),
                                    "timestamp" : datetime.datetime.utcnow().isoformat(),
                                },
                            ],
                    }
        self.db.insert(new_item) 
        # Now search an entry
        # Games = Query()
        # results = self.db.search(Games.code == "666NB4R")
        # logging.info(str(results[0]["turns"][0]["user"]))
        # user = await interactions.get(self.bot, interactions.User, object_id=results[0]["turns"][0]["user"])
        # guild = await interactions.get(self.bot, interactions.Guild, object_id=results[0]["turns"][0]["server"])
        


        logging.info("FeeCoop loaded!")

    # Makes one embed for each given game ID
    async def build_embed_for_game(self, ctx, doc_id):
        entry = self.db.get(doc_id=doc_id)
        code = entry["code"]
        map = entry.get("map")
        server_only = entry.get("server_only")
        group_pass = entry.get("group_pass")
        status = entry.get("status")
        turns = entry.get("turns", [])
        if len(turns) > 0:
            created_on = turns[0]["timestamp"]
            started_userid = turns[0]["user"]
            started_serverid = turns[0]["server"]
            started_userobj = await interactions.get(self.bot, interactions.User, object_id=started_userid)
            started_serverobj = await interactions.get(self.bot, interactions.Guild, object_id=started_serverid)
            color = assign_color_to_user(started_userobj.username)
        else:
            color = interactions.Color.red()

        title = code
        if status:
            title += " (" + status + ")"

        embed = interactions.Embed(title=code, color=color, provider=interactions.EmbedProvider(name="Fee coop"))

        # Check the map data
        try:
            map = int(map)
        except ValueError:
            map = False
        if map:
            difficulty = self.mapdata[map]["difficulty"]
            maxturns = self.mapdata[map]["maxturns"]
            maxplayers = self.mapdata[map]["maxplayers"]
            possible_rewards = self.mapdata[map]["possible_rewards"]
            mapname = self.mapdata[map]["name"]
            # First line: Map
            try: 
                mapemoji = self.emoji["map" + str(map)]
            except:
                mapemoji = ""
            embed.description = "Map:" + mapname + " " + mapemoji + " (" + difficulty + ")"
            # Second line: Turns
            embed.description += "\nTurns: " + str(maxturns) + " (" + str(maxplayers) + " players)"
            # Remaining lines: Rewards
            embed.description += "\nReward:"
            for reward in possible_rewards:
                try: 
                    rewardemoji = self.emoji[reward.lower().split()[0]]
                except:
                    rewardemoji = ""
                embed.description += "\n" + rewardemoji + " " + reward

        if server_only or group_pass:
            # Group pass beats server ID
            if group_pass:
                embed.set_footer(text="Group pass: " + group_pass)
            elif server_only and started_serverid:
                embed.set_footer(text="Only for server: " + started_serverobj.name, icon_url=started_serverobj.icon_url)

        if created_on:
            embed.timestamp=datetime.datetime.fromisoformat(created_on)

        if started_userid:
            username = started_userobj.username + "#" + started_userobj.discriminator
            if started_serverid != str(ctx.guild_id):
                username += " (server " + started_serverobj.name + ")"
            embed.set_author(name=started_userobj.username + "#" + started_userobj.discriminator, icon_url=started_userobj.avatar_url)

        if len(turns) > 1:
            for turn in turns[1:]:
                userid = turn["user"]
                userobj = await interactions.get(self.bot, interactions.User, object_id=userid)
                username = userobj.username + "#" + userobj.discriminator
                serverid = turn["server"]
                # Show if its from a different server
                if serverid != str(ctx.guild_id):
                    serverobj = await interactions.get(self.bot, interactions.Guild, object_id=serverid)
                    username += " (server " + serverobj.name + ")"
                timestamp = datetime.datetime.fromisoformat(turn["timestamp"])
                utc_time = calendar.timegm(timestamp.utctimetuple())
                timestamp_discordstring = "<t:" + str(utc_time) + ":R>"
                embed.add_field(name=username, value=timestamp_discordstring, inline=True)

        return embed
        
    # Rightclick to check the message for game IDs
    @interactions.extension_command(
        type=interactions.ApplicationCommandType.MESSAGE,
        name="Show Game"
    )
    async def fee_coop_rightclick_show_game(self, ctx):
        game_ids = ctx.target.content.split()
        Games = Query()
        results = self.db.search(Games.code.one_of(game_ids))
        if len(results) > 0:
            found_games = []
            for result in results:
                embed = await self.build_embed_for_game(doc_id=result.doc_id, ctx=ctx)
                found_games.append(embed)
            return await ctx.send(embeds=found_games, ephemeral=True)
        else:
            return await ctx.send("No valid codes found in this message.", ephemeral=True)

def setup(client):
    FeeCoop(client)