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

        make_testdata = False
        if make_testdata:
            # Test data
            new_item = {    "code": "666NB4R", 
                            "map": 3, 
                            "server_only" : False,
                            "group_pass" : "", 
                            "status" : "failed",
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

    # Lists all games with given criteria
    async def show_game_list(self, ctx, server_only=None, group_pass=None, status="open", for_user=None, ephemeral=False):
        await ctx.defer(ephemeral=ephemeral)

        color = assign_color_to_user(ctx.user.username)
        title = "Fire Emblem Engage: Relay trials"
        embed = interactions.Embed(title=title, color=color, provider=interactions.EmbedProvider(name="Fee coop"))

        if server_only:
            server_id = ctx.guild_id
            serverobj = await interactions.get(self.bot, interactions.Guild, object_id=server_id)
            embed.set_author(name="Only listing server: " + serverobj.name, icon_url=serverobj.icon_url)
        elif group_pass:
            embed.set_author(name="All games from all servers with group pass: " + group_pass)

        # Prepare a simple search for these criteria
        game_search_fragment = {}
        if group_pass:
            game_search_fragment["group_pass"] = group_pass
        if status:
            game_search_fragment["status"] = status

        # Do we have any subcriteria where we need to check the individual turns?
        Games = Query()
        if server_only:
            # EVERY Turn object must have the same server ID as the current server
            Turns = Query()
            games = self.db.search(Games.fragment(game_search_fragment) & Games.turns.all(Turns.server == str(ctx.guild_id)))
        elif for_user:
            # The current user must be present in ANY turn, not neccessarily in all turns
            Turns = Query()
            games = self.db.search(Games.fragment(game_search_fragment) & Games.turns.any(Turns.user == str(ctx.user.id)))
        else:
            # Just match the broad search from above
            games = self.db.search(Games.fragment(game_search_fragment))

        # Sort the dict by timestamp and go
        def sort_by_timestamp(game):
            turns = game['turns']
            if turns:
                timestamp_str = turns[0]['timestamp']
                timestamp = datetime.datetime.fromisoformat(timestamp_str)
                return timestamp
            else:
                return datetime.datetime.max

        sorted_games = sorted(games, key=sort_by_timestamp,reverse=True)
        description = ""
        options = []
        for entry in sorted_games:
            turns = entry.get("turns", [])
            # Some games don't want to be seen unless they are on a specific server.
            game_wants_server_only = entry.get("server_only")
            if game_wants_server_only:
                game_server_id = turns[0]["server"]
                if str(ctx.guild_id) != game_server_id:
                    continue

            # First line: Code and map
            code = entry["code"]
            if not status:
                # If no status was selected, show the current games status
                code += " (" + entry.get("status") + ")"

            map = entry.get("map")
            difficulty = self.mapdata[map]["difficulty"]
            mapname = self.mapdata[map]["name"]
            maxplayers = self.mapdata[map]["maxplayers"]
            try: 
                mapemoji = self.emoji["map" + str(map)]
            except:
                mapemoji = ""
            description += "**" + code + "** - " + mapemoji + " " + mapname + "(" + difficulty + ")\n"

            # Second line: User, timestamp and turn count
            created_on = turns[0]["timestamp"]
            started_userid = turns[0]["user"]
            started_serverid = turns[0]["server"]
            started_userobj = await interactions.get(self.bot, interactions.User, object_id=started_userid)
            started_serverobj = await interactions.get(self.bot, interactions.Guild, object_id=started_serverid)
            timestamp = datetime.datetime.fromisoformat(created_on)
            utc_time = calendar.timegm(timestamp.utctimetuple())
            timestamp_discordstring = "<t:" + str(utc_time) + ":R>"
            username = started_userobj.username + "#" + started_userobj.discriminator
            if started_serverid != str(ctx.guild_id):
                username += " (server " + started_serverobj.name + ")"
            description += "*by user " + username + ", " + timestamp_discordstring + ", " + str(len(turns)) +  "/" + str(maxplayers) + " players*\n\n"

            # Now prepare the select menu. For this we need the emoji as emoji object, not as string
            if len(options < 25):
                start = mapemoji.find(":", mapemoji.find(":") + 1) + 1
                end = mapemoji.find(">")
                emoji_id = mapemoji[start:end]
                emoji = interactions.Emoji(id=emoji_id)
                options.append(SelectOption(label=code, 
                                                value=entry.doc_id, 
                                                description=str(mapname + "by " + username)[:100],
                                                emoji=emoji
                                                )
                                            )

        embed.description = description
        
        # Select menu to show one game in detail

        s1 = SelectMenu(
                custom_id="show_game_docid",
                placeholder="Select game",
                options=options,
            )


        return ctx.send(embeds=[embed], components=[[s1]], ephemeral=ephemeral)

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
            color = assign_color_to_user(ctx.user.username)

        title = code
        if status:
            title += " (" + status + ")"

        embed = interactions.Embed(title=title, color=color, provider=interactions.EmbedProvider(name="Fee coop"))

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
            embed.description = mapemoji + " " + mapname + "(" + difficulty + ")"
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
            embed.set_author(name=username, icon_url=started_userobj.avatar_url)

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

    # The fee main command. Its empty because the real stuff happens in the subcommands.
    @interactions.extension_command()
    async def fee(self, ctx: interactions.CommandContext):
        """The Fee base command. This description isn't shown in discord."""
        pass

    # Fee opengames subcommand. Shows games to join
    @fee.subcommand(
        name="opengames",
        description="Show open relay trials from Fire Emblem Engage",
        options=[
            interactions.Option(
                    name="server_only",
                    description="Only games from people of this discord server?",
                    value=False,
                    type=interactions.OptionType.BOOLEAN,
                    required=False,
            ),
            interactions.Option(
                    name="group_pass",
                    description="List only games with this group pass, server independent",
                    type=interactions.OptionType.STRING,
                    min_length=0,
                    max_length=100,
                    required=False,
            ),
            interactions.Option(
                    name="show_public",
                    description="Post the list public for everyone in this channel",
                    type=interactions.OptionType.BOOLEAN,
                    value=True,
                    required=False,
            ),
        ]
    )
    async def fee_opengames(self, ctx: interactions.CommandContext, server_only : bool = False, group_pass : str = None, show_public : bool = True):
        logging.info("Request fee_opengames by " + ctx.user.username + "#" + ctx.user.discriminator)
        return await self.show_game_list(ctx=ctx, server_only=server_only, group_pass=group_pass, status="open", for_user=None, ephemeral=show_public)


    # Fee mygames subcommand. Shows all games where the user participated
    @fee.subcommand(
        name="mygames",
        description="Show open relay trials from Fire Emblem Engage",
        options=[
            interactions.Option(
                    name="only_open_games",
                    description="Only games that are not finished yet",
                    value=False,
                    type=interactions.OptionType.BOOLEAN,
                    required=False,
            ),
        ]
    )
    async def fee_mygames(self, ctx: interactions.CommandContext, only_open_games : bool = False):
        logging.info("Request fee_mygames by " + ctx.user.username + "#" + ctx.user.discriminator)
        if only_open_games:
            status = "open"
        else:
            status = None
        return await self.show_game_list(ctx=ctx, server_only=False, group_pass=None, status=status, for_user=True, ephemeral=True)

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
            embed_counter = 0
            for result in results:
                embed = await self.build_embed_for_game(doc_id=result.doc_id, ctx=ctx)
                found_games.append(embed)
                embed_counter += 1
                # Max amount of discord embeds
                if embed_counter >= 10:
                    break
            return await ctx.send(embeds=found_games, ephemeral=True)
        else:
            return await ctx.send("No valid codes found in this message.", ephemeral=True)

def setup(client):
    FeeCoop(client)