import asyncio
import random 
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
        # All information about our maps. Index = Map number
        self.mapdata = []
        with open("ressources/mapdata.json", "r") as json_file:
            self.mapdata = json.load(json_file)
        # Maps are also represented as emoji
        self.emoji = {}
        with open("ressources/emoji.json", "r") as json_file:
            self.emoji = json.load(json_file)

        # Active games from database
        self.db = TinyDB('db.json')

        add_testdata = False
        if add_testdata:
            # Test data
            new_item = {    "code": "7999996", 
                            "map": 2, 
                            "server_only" : True,
                            "group_pass" : "", 
                            "status" : "open",
                            "turns" : [
                                    {
                                        "user" : str(363144319739232257),
                                        "server" : str(490564578128822293),
                                        "timestamp" : "2022-12-24T16:59:00", #datetime.datetime.utcnow().isoformat(),
                                    },
                                    {
                                        "user" : str(523211690213376005),
                                        "server" : str(490564578128822293),
                                        "timestamp" : datetime.datetime.utcnow().isoformat(),
                                    },
                                ],
                        }
            self.db.insert(new_item)
            new_item = {    "code": "663NB4R", 
                            "map": 1, 
                            "server_only" : False,
                            "group_pass" : "", 
                            "status" : "open",
                            "turns" : [
                                    {
                                        "user" : "330955309763788800", # str(ctx.user.id),
                                        "server" : "490564578128822293", #str(ctx.guild_id),
                                        "timestamp" : datetime.datetime.utcnow().isoformat(),
                                    },
                                ],
                        }
            self.db.insert(new_item) 
            new_item = {    "code": "748P526", 
                            "map": 2, 
                            "server_only" : True,
                            "group_pass" : "", 
                            "status" : "open",
                            "turns" : [
                                    {
                                        "user" : str(523211690213376005),
                                        "server" : str(490564578128822293),
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
            new_item = {    "code": "9996W96", 
                            "map": 3, 
                            "server_only" : False,
                            "group_pass" : "", 
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
            new_item = {    "code": "8896W96", 
                            "map": 4, 
                            "server_only" : False,
                            "group_pass" : "", 
                            "status" : "finished",
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
                                ],
                        }
            self.db.insert(new_item) 
            new_item = {    "code": "9999526", 
                            "map": 5, 
                            "server_only" : False,
                            "group_pass" : "11118888", 
                            "status" : "open",
                            "turns" : [
                                    {
                                        "user" : str(330955309763788800),
                                        "server" : str(870019135646613524),
                                        "timestamp" : datetime.datetime.utcnow().isoformat(),
                                    },
                                    {
                                        "user" : str(234861064532131842),
                                        "server" : str(490564578128822293),
                                        "timestamp" : datetime.datetime.utcnow().isoformat(),
                                    },
                                    {
                                        "user" : str(363144319739232257),
                                        "server" : str(870019135646613524),
                                        "timestamp" : datetime.datetime.utcnow().isoformat(),
                                    },
                                ],
                        }
            self.db.insert(new_item) 
            new_item = {    "code": "123526", 
                            "map": 5, 
                            "server_only" : True,
                            "group_pass" : "", 
                            "status" : "open",
                            "turns" : [
                                    {
                                        "user" : str(234861064532131842),
                                        "server" : str(870019135646613524),
                                        "timestamp" : datetime.datetime.utcnow().isoformat(),
                                    },
                                    {
                                        "user" : str(307624030704238592),
                                        "server" : str(870019135646613524),
                                        "timestamp" : datetime.datetime.utcnow().isoformat(),
                                    },
                                ],
                        }
            self.db.insert(new_item) 
        
        logging.info("FeeCoop loaded!")

    # Checks an embed for a game id
    async def get_doc_id_from_message(self, ctx, status="open"):
        if not ctx.message.embeds:
            return None
        code = ctx.message.embeds[0].title.split()[0]
        game_search_fragment = {"code" : code, "status" : status}
        GamesQ = Query()
        games = self.db.search(GamesQ.fragment(game_search_fragment))
        if (not games) or len(games) == 0:
            return None
        else:
            # We *should* have only one open game with the same game code
            return games[0].doc_id

    # Gets a random image from the directory and returns it
    async def get_finished_picture(self, status="success"):
        img_directory = "ressources/" + status 
        files = os.listdir(img_directory)
        random_file = random.choice(files)
        absolute_path = os.path.abspath(os.path.join(img_directory, random_file))
        return absolute_path, random_file

    # Check for old games and delete them
    async def purge_old_entries(self, ctx):
        # Search for open games only
        game_search_fragment = {"status" : "open"}
        GamesQ = Query()
        games = self.db.search(GamesQ.fragment(game_search_fragment))

        # Instead of a fancy TinyDB search we manually select now the entries which are too old
        for entry in games:
            turns = entry.get("turns", [])
            last_activity = turns[-1]["timestamp"]
            timestamp = datetime.datetime.fromisoformat(last_activity)
            days_since_last_activity = (datetime.datetime.now() - timestamp).days

            # Older than 1 day? Remove and tell the owner that he can add it again anytime
            if days_since_last_activity > 1:
                # Update game status
                self.db.update({"status" : "abandoned"}, doc_ids=[entry.doc_id])

                # Build an embed for the host to reinstate the game if needed
                embed = await self.build_embed_for_game(ctx=ctx, doc_id=entry.doc_id)
                embed.description = "This game has been **abandoned** automatically because it has been inactive for a while now so it likely has already been finished. If you want to list the game as open game again, just click the button below to **reinstate** it.\n\n\n" + embed.description
                embed.description = embed.description[0:4096]
                # Host gets the "create new game" button
                button_reinstate = Button(style=3, custom_id="reinstate_game", label="Reinstate Game", emoji=interactions.Emoji(name="👼"))
                components = [[button_reinstate]]

                # If this is the host, simple update message. If it is not the host, send the host a private message.
                started_userid = turns[0]["user"]
                started_userobj = await interactions.get(self.bot, interactions.User, object_id=started_userid)
                started_userobj._client = self.client._http
                await started_userobj.send(embeds=[embed], components=components)
                    

    # Lists all games with given criteria
    async def show_game_list(self, ctx, server_only=None, group_pass="", status="open", for_user=None, ephemeral=False):
        # Before we attempt to create any kind of list, we should purge the list from old entries.
        await self.purge_old_entries(ctx)
        
        # Group pass should stay secret if possible
        if group_pass:
            ephemeral = True

        await ctx.defer(ephemeral=ephemeral)

        # Server only makes only sense if we have a server (not in private messages)
        if not ctx.guild_id:
            server_only = False

        color = assign_color_to_user(ctx.user.username)
        title = "Fire Emblem Engage: Relay Trials"
        embed = interactions.Embed( title=title, 
                                    color=color, 
                                    provider=interactions.EmbedProvider(name="Fee coop"),
                                    timestamp=datetime.datetime.utcnow())

        if server_only:
            server_id = ctx.guild_id
            serverobj = await interactions.get(self.bot, interactions.Guild, object_id=server_id)
            embed.set_author(name="Only listing server: " + serverobj.name, icon_url=serverobj.icon_url)
        elif group_pass:
            embed.set_author(name="Open games from all servers with group pass: " + group_pass)
        elif for_user:
            embed.set_author(name="Games of " + ctx.user.username + "#" + ctx.user.discriminator, icon_url=ctx.user.avatar_url)

        # Prepare a simple search for these criteria
        game_search_fragment = {}
        if status:
            game_search_fragment["status"] = status
        if group_pass:
            game_search_fragment["group_pass"] = group_pass
        else:
            # These games explicitly do not want to be listed
            if not for_user:
                game_search_fragment["group_pass"] = ""

        # Do we have any subcriteria where we need to check the individual turns?
        GamesQ = Query()
        if server_only:
            # EVERY Turn object must have the same server ID as the current server
            logging.info("Searching for current server and " + str(game_search_fragment))
            TurnsQ = Query()
            games = self.db.search((GamesQ.fragment(game_search_fragment)) & (GamesQ.turns.all(TurnsQ.server == str(ctx.guild_id))))
        elif for_user:
            # The current user must be present in ANY turn, not neccessarily in all turns
            logging.info("Searching for current user and " + str(game_search_fragment))
            TurnsQ = Query()
            games = self.db.search((GamesQ.fragment(game_search_fragment)) & (GamesQ.turns.any(TurnsQ.user == str(ctx.user.id))))
        else:
            # Just match the broad search from above
            logging.info("Searching for " + str(game_search_fragment))
            games = self.db.search(GamesQ.fragment(game_search_fragment))

        # Sort the dict by timestamp and go
        def sort_by_timestamp(game):
            turns = game['turns']
            if turns:
                timestamp_str = turns[0]['timestamp']
                timestamp = datetime.datetime.fromisoformat(timestamp_str)
                return timestamp
            else:
                return datetime.datetime.max

        reverse_sort = False
        if for_user:
            reverse_sort = True
        sorted_games = sorted(games, key=sort_by_timestamp,reverse=reverse_sort)
        description = ""
        options = []
        logging.info("Len is " + str(len(sorted_games)))
        for entry in sorted_games:
            turns = entry.get("turns", [])
            # Some games don't want to be seen unless they are on a specific server.
            game_wants_server_only = entry.get("server_only")
            this_server_id = ""
            if ctx.guild_id:
                this_server_id = str(ctx.guild_id)
            if game_wants_server_only:
                game_server_id = turns[0]["server"]
                if this_server_id != game_server_id:
                    continue
            
            logging.info("Adding game")
            # First line: Code and map
            code = entry["code"]
            if not status:
                # If no status was selected, show the current games status
                code += " (" + entry.get("status") + ")"
            if for_user and entry.get("group_pass"):
                code += " (group pass locked)"

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
            last_activity = turns[len(turns) - 1]["timestamp"]
            started_userid = turns[0]["user"]
            started_serverid = turns[0]["server"]
            started_userobj = await interactions.get(self.bot, interactions.User, object_id=started_userid)
            if started_serverid:
                started_serverobj = await interactions.get(self.bot, interactions.Guild, object_id=started_serverid)
            timestamp = datetime.datetime.fromisoformat(last_activity)
            utc_time = calendar.timegm(timestamp.utctimetuple())
            last_activity_discordstring = "<t:" + str(utc_time) + ":R>"
            username = started_userobj.username + "#" + started_userobj.discriminator
            if started_serverid != this_server_id:
                username += " (server " + started_serverobj.name + ")"
            description += "*by user " + username + ", " + str(len(turns)) +  "/" + str(maxplayers) + " players, " + last_activity_discordstring + "*\n\n"

            # Now prepare the select menu. For this we need the emoji as emoji object, not as string
            if len(options) < 25:
                start = mapemoji.find(":", mapemoji.find(":") + 1) + 1
                end = mapemoji.find(">")
                emoji_id = mapemoji[start:end]
                emoji = interactions.Emoji(id=emoji_id)
                options.append(SelectOption(label=code, 
                                                value=entry.doc_id, 
                                                description=str(mapname + " by " + username)[:100],
                                                emoji=emoji
                                                )
                                            )
            logging.info("Game added " + code)

            # Max length
            if len(description) >= 4096:
                description = description[0:4096]
                break
        if not description:
            description = "No games found!"

        embed.description = description
        
        # Select menu to show one game in detail
        components = None
        if len(options) > 0:
            s1 = SelectMenu(
                    custom_id="show_game_docid",
                    placeholder="Select game",
                    options=options,
                )
            components = [[s1]]
        logging.info("Sending reply")
        return await ctx.send(embeds=[embed], components=components, ephemeral=ephemeral)

    # Can the user delete this game?
    async def can_user_delete_game(self, ctx, doc_id):
        entry = self.db.get(doc_id=doc_id)
        status = entry.get("status")
        if status != "open":
            return False
        
        # When was the game touched the last time?
        turns = entry.get("turns", [])
        last_activity = turns[-1]["timestamp"]
        timestamp = datetime.datetime.fromisoformat(last_activity)
        days_since_last_activity = (datetime.datetime.now() - timestamp).days

        # User owner or participant?
        user_is_participant = False
        user_is_host = False
        if str(ctx.user.id) in [turn['user'] for turn in turns]:
            user_is_participant = True
            if (str(ctx.user.id) == turns[0]['user']):
                user_is_host = True

        # Allow to abandon the game? Host can abandon always, participants after one day
        if user_is_host or (user_is_participant and days_since_last_activity > 1):
            return True
        elif days_since_last_activity > 2:
            # Everyone can abandon the game if its very old
            return True
        
        return False


    # Determines which buttons the user can see and returns them
    async def build_components_for_game(self, ctx, doc_id):
        components = None
        # Join - If the game is open and user didnt join already. Opens new modal with finished, lost and couldnt join
        # Abandon - If user is part of the group and game is old

        entry = self.db.get(doc_id=doc_id)
        status = entry.get("status")
        turns = entry.get("turns", [])

        # Abandoned games can be reinstated by the host
        if status == "abandoned" and str(ctx.user.id) == turns[0]["user"]:
            # Is the game ID still free?
            code = entry.get("code")
            game_search_fragment = {"code" : code, "status" : "open"}
            GamesQ = Query()
            games = self.db.search(GamesQ.fragment(game_search_fragment))
            if (not games) or len(games) == 0:
                # No open game with this code exists, host can make one
                button_reinstate = Button(style=3, custom_id="reinstate_game", label="Reinstate Game", emoji=interactions.Emoji(name="👼"))
                return [[button_reinstate]]

        if status != "open":
            return components
        
        # Old games can be deleted
        delete_game_allowed = await self.can_user_delete_game(ctx=ctx, doc_id=doc_id)

        # Joining is only allowed if user is not in the game already
        user_is_participant = False
        if str(ctx.user.id) in [turn['user'] for turn in turns]:
            user_is_participant = True
        
        button_join = None
        button_abandon = None
        
        # Join game - show it always, we only check later if the user is already in the game.
        #if not user_is_participant:
        button_join = Button(style=3, custom_id="join_game", label="Join", emoji=interactions.Emoji(name="⚔️"))

        # Allow to abandon the game? Host can abandon always, participants after one day
        if delete_game_allowed:
            if user_is_participant:
                button_abandon = Button(style=4, custom_id="abandon_game", label="Remove from open game list", emoji=interactions.Emoji(name="🇽"))
            else:
                button_abandon = Button(style=4, custom_id="abandon_game", label="Abandoned? Remove for EVERYONE", emoji=interactions.Emoji(name="⚠️"))

        # Arrange buttons for discord neatly
        if button_join and button_abandon:
            components = spread_to_rows(button_join, button_abandon)
        elif button_join:
            components = [[button_join]]
        elif button_abandon:
            components = [[button_abandon]]
        
        return components

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
            if started_serverid:
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
                # Show only to the host
                if started_userid and (started_userid == ctx.user.id):
                    embed.set_footer(text="Group pass: " + group_pass)
                else:
                    embed.set_footer(text="Group pass locked by " + started_userobj.username + "#" + started_userobj.discriminator)
            elif server_only and started_serverid:
                embed.set_footer(text="Only for server: " + started_serverobj.name, icon_url=started_serverobj.icon_url)

        if created_on:
            embed.timestamp=datetime.datetime.fromisoformat(created_on)

        if started_userid:
            username = started_userobj.username + "#" + started_userobj.discriminator
            if started_serverid and ((not ctx.guild_id) or started_serverid != ctx.guild_id):
                username += " (server " + started_serverobj.name + ")"
            # Note: Adding URLS to the users private DM channel like this would be nice but it isn't allowed by discord. url="https://discord.com/channels/@me/" + str(started_userobj.id)
            embed.set_author(name=username, icon_url=started_userobj.avatar_url)

        if len(turns) > 1:
            for turn in turns[1:]:
                userid = turn["user"]
                userobj = await interactions.get(self.bot, interactions.User, object_id=userid)
                username = userobj.username + "#" + userobj.discriminator
                serverid = turn["server"]
                # Show if user is on a server, and if that server is a different server than the starting server or if there is no starting server (start via private message)
                if serverid and ((not started_serverid) or serverid != started_serverid):
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
        ephemeral = not show_public
        return await self.show_game_list(ctx=ctx, server_only=server_only, group_pass=group_pass, status="open", for_user=None, ephemeral=ephemeral)


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

    # Fee notifications turns on private messages for the user when a new game is created
    @fee.subcommand(
        name="notifications",
        description="Turn on or off notifications for new games",
        options=[
                interactions.Option(
                        name="active",
                        description="False to turn off notifications. True to receive notifications.",
                        type=interactions.OptionType.BOOLEAN,
                        required=True,
                ),
                interactions.Option(
                        name="server_only",
                        description="For ALL new games or just from this server?",
                        type=interactions.OptionType.BOOLEAN,
                        required=True,
                ),
                interactions.Option(
                        name="group_pass",
                        description="Only watch a certain group pass (ignores server restrictions)",
                        type=interactions.OptionType.STRING,
                        required=False,
                ),
            ]
        )
    async def fee_notifications(self, ctx: interactions.CommandContext, active=True, server_only=True, group_pass=""):
        logging.info("Fee notifications by " + ctx.user.username + "#" + ctx.user.discriminator)

        # Does a setting exist already?
        user_config = self.db.table("user_config")
        UserQ = Query()
        entry = user_config.get(UserQ.user == str(ctx.user.id))
        doc_id = None
        old_active = False
        old_server_only = False
        old_group_pass = ""
        old_server_id = ""
        if entry:
            doc_id = entry.doc_id
            old_active = entry.get("notifications_active", False)
            old_server_only = entry.get("notifications_server_only", False)
            old_server_id = entry.get("notifications_server_id", "")
            old_group_pass = entry.get("notifications_group_pass", "")

        # If group pass, then ignore server_only
        if group_pass:
            server_only = False

        # Server ID so we know if the user can be informed by games which only want a certain server
        server_id = ""
        if ctx.guild_id:
            server_id = str(ctx.guild_id)
        else:
            # If we have no server, the user can not listen to only games from this server
            server_only = False

        # Deactivate notification
        if not active:
            if old_active:
                user_config.update({"notifications_active" : False}, doc_ids=[doc_id])
                return await ctx.send("All notifictations deactivated!", ephemeral=True)
            else:
                return await ctx.send("No changes made, notifications were already deactivated for you.", ephemeral=True)
        else:
            # Activate notification
            if old_active and server_only == old_server_only and group_pass == old_group_pass and server_id == old_server_id:
                return await ctx.send("No changes made, your given notification settings were already active.", ephemeral=True)

            new_entry = {   
                            "user" : str(ctx.user.id),
                            "notifications_active" : True, 
                            "notifications_server_only" : server_only, 
                            "notifications_server_id" : server_id,
                            "notifications_group_pass" : group_pass
                        }
            user_config.upsert(new_entry, UserQ.user == str(ctx.user.id))
            messagetext = "Notifications"
            if not old_active:
                messagetext += " activated"
            else:
                messagetext += " changed"
            if server_only != old_server_only:
                messagetext += ", server_only: " + str(server_only)
            if server_id != old_server_id:
                if ctx.guild_id:
                    server_obj = await ctx.get_guild()
                    messagetext += ", getting now updates for all games on " + server_obj.name
                else:
                    messagetext += ", no server specific updates anymore"
            if group_pass != old_group_pass:
                if group_pass:
                    messagetext += ", watching only for group_pass " + group_pass + " now"
                else:
                    messagetext += ", ignoring previous group pass \"" + old_group_pass + "\" now"
            messagetext += "."
            return await ctx.send(messagetext, ephemeral=True)

    # Check all users that want to be notified and notify them about the new game
    async def notify_users(self, ctx, doc_id, server_only, group_pass):
        
        # Get the game data
        game_entry = self.db.get(doc_id=doc_id)
        if not game_entry:
            logging.info("notify_users was called with an invalid doc_id " + str(doc_id))
        
        # If group pass, then ignore server_only
        if group_pass:
            server_only = False

        # Current server
        server_id = ""
        if ctx.guild_id:
            server_id = str(ctx.guild_id)
        else:
            server_only = False

        # Find users who want to get informed
        user_config = self.db.table("user_config")
        UserQ = Query()
        entry = user_config.get(UserQ.user == str(ctx.user.id))
        user_search_fragment = {}
        if server_only:
            # This game is only availible on this server so only look for users with this server
            user_search_fragment = {"notifications_active" : True, "notifications_group_pass" : group_pass, "notifications_server_id" : server_id}
        else:
            user_search_fragment = {"notifications_active" : True, "notifications_group_pass" : group_pass}
        
        # Also, the users we search for should either ignore server restrictions, or have the exact same server as us
        configs = user_config.search(   (UserQ.fragment(user_search_fragment)) 
                                    & (   
                                          (UserQ.fragment({"notifications_server_only" : False}))
                                        | (UserQ.fragment({"notifications_server_id" : server_id}))
                                    ))
        for config in configs:
            # Send every user a private message
            user_id = config["user"]
            # Except the current user
            if user_id == str(ctx.user.id):
                continue
            user_obj = await interactions.get(self.bot, interactions.User, object_id=user_id)
            user_obj._client = self.client._http
            logging.info("Informing user " + user_obj.username + "#" + user_obj.discriminator + " about new game " + str(game_entry.get("code")))
            # Build embed and send it
            embed = await self.build_embed_for_game(ctx=ctx, doc_id=doc_id)
            embed.description = "A new game has been created! You get this message because you turned **notifications on**. To deactivate notifications, reply with using this command:\n\n``/fee notifications``\n\n\n" + embed.description
            embed.description = embed.description[0:4096]
            components = await self.build_components_for_game(ctx=ctx, doc_id=doc_id)
            return await user_obj.send(embeds=[embed], components=components)

    # Fee coop to show or create a game
    @fee.subcommand(
            name="coop",
            description="Join a Fire Emblem Engage game or create one!",
            options=[
                interactions.Option(
                        name="code",
                        description="Relay Trial ID. You get it in the Tower of Trials after opening a game.",
                        min_length=3,
                        type=interactions.OptionType.STRING,
                        required=True,
                ),
                interactions.Option(
                        name="server_only",
                        description="Create a new game just for this server",
                        type=interactions.OptionType.BOOLEAN,
                        required=False,
                ),
                interactions.Option(
                        name="group_pass",
                        description="Create a new game just for everyone who enters this passphrase later",
                        type=interactions.OptionType.STRING,
                        required=False,
                ),
            ]
        )
    async def fee_coop(self, ctx: interactions.CommandContext, code : str = "", server_only=False, group_pass=""):
        game_search_fragment = {"code" : code, "status" : "open"}
        GamesQ = Query()
        games = self.db.search(GamesQ.fragment(game_search_fragment))
        if (games) and len(games) > 0:
            embed = await self.build_embed_for_game(ctx=ctx, doc_id=games[0].doc_id)
            components = await self.build_components_for_game(ctx=ctx, doc_id=games[0].doc_id)
            return await ctx.send(embeds=[embed], components=components, ephemeral=False)
        else:
            # Send the user a message so a new game can be created
            options = []
            for mapid, mapinfo in enumerate(self.mapdata):
                if mapid == 0:
                    continue
                # List all maps that we have
                difficulty = mapinfo["difficulty"]
                mapname = mapinfo["name"]
                maxturns = mapinfo["maxturns"]
                maxplayers = mapinfo["maxplayers"]
                try: 
                    mapemoji = self.emoji["map" + str(mapid)]
                    start = mapemoji.find(":", mapemoji.find(":") + 1) + 1
                    end = mapemoji.find(">")
                    emoji_id = mapemoji[start:end]
                    emoji = interactions.Emoji(id=emoji_id)
                except:
                    emoji = None
                possible_rewards = mapinfo["possible_rewards"]
                options.append(SelectOption(label=mapname + "(" + difficulty + ")", 
                                            value=mapid,
                                            description=str("Turns: " + str(maxturns) + " Players: " + str(maxplayers) + " Rewards: "  + ",".join(possible_rewards))[:100],
                                            emoji=emoji
                                            )
                                        )
                if len(options) == 25:
                    break
            s1 = SelectMenu(
                            custom_id="select_map",
                            placeholder="Select map for new game",
                            options=options,
                        )
            components = [[s1]]
            color = assign_color_to_user(ctx.user.username)
            title = code.replace(" ", "") + " - Adding new game"
            embed = interactions.Embed( title=title, 
                                        color=color, 
                                        description="Please select the map below!",
                                        provider=interactions.EmbedProvider(name="Fee coop"),
                                        timestamp=datetime.datetime.utcnow()
                                        )
            embed.set_author(name=ctx.user.username + "#" + ctx.user.discriminator, icon_url=ctx.user.avatar_url)
            # Server only makes only sense if we are on a server
            if ctx.guild_id:
                server_obj = await ctx.get_guild()
            else:
                server_only = False
            # Group pass beats server ID
            if group_pass:
                embed.set_footer(text="Group pass: " + group_pass)
            elif server_only:
                embed.set_footer(text="Only for server: " + server_obj.name, icon_url=server_obj.icon_url)
            return await ctx.send(embeds=[embed], components=components, ephemeral=False)
        
   # Join the game
    @interactions.extension_component("join_game")
    async def fee_join_game(self, ctx):
        # Get the open game from the last message
        doc_id = await self.get_doc_id_from_message(ctx, status="open")

        # Last messgae hidden or not?
        # if ctx.message.flags == 64:
        #     ephemeral = True
        # else:
        #     ephemeral = False
        ephemeral = True

        # Game found?
        if not doc_id:
            return await ctx.send("Could not join game, maybe it was finished already?", ephemeral=True)

        entry = self.db.get(doc_id=doc_id)

        # User already in the game?
        turns = entry.get("turns", [])
        if str(ctx.user.id) in [turn['user'] for turn in turns]:
            return await ctx.send("You already participated in the game, you can't join it again.", ephemeral=True)

        # Tell the user how to join the game
        server_only = entry.get("server_only")
        group_pass = entry.get("group_pass")
        turns = entry.get("turns", [])
        if len(turns) > 0:
            started_serverid = turns[0]["server"]
            if started_serverid:
                started_serverobj = await interactions.get(self.bot, interactions.Guild, object_id=started_serverid)

        added_description = "Join the game using the above code in Fire Emblem Engage: Relay Trials now!"
        if server_only and started_serverid:
            added_description += "\nPlease note that the game opener only wants users from the server " + started_serverobj.name + " to join."
        if group_pass:
            added_description += "\nPlease note that the game opener only wants users with a group pass to join."
        added_description += "\n\nOnce you finished your turns, please use the buttons below to update the game status."

        embed = await self.build_embed_for_game(ctx=ctx, doc_id=doc_id)
        embed.description = added_description + "\n\n\n" + embed.description
        embed.description = embed.description[0:4096]

        last_turn = False
        map = entry["map"]
        maxplayers = self.mapdata[map]["maxplayers"]
        if len(turns) >= (maxplayers - 1):
            last_turn = True

        # Make the buttons to ask the user if it worked or not
        b1 = Button(style=3, custom_id="game_ongoing", label="Still ongoing", emoji=interactions.Emoji(id=1068863754713968700), disabled=last_turn)
        b2 = Button(style=1, custom_id="game_success", label="Success!", emoji=interactions.Emoji(id=1068852878661398548))
        b3 = Button(style=2, custom_id="game_over", label="Game Over", emoji=interactions.Emoji(id=1068852433129832558))
        b4 = Button(style=4, custom_id="join_game_failed", label="Could not join game", emoji=interactions.Emoji(id=1068863333526151230))
        components = spread_to_rows(b1, b2, b3, b4)

        return await ctx.send(embeds=[embed], components=components, ephemeral=ephemeral)

    # Create a new game or reopen an existing one
    async def create_new_game(self, ctx, doc_id=None, code=None, server_only=False, group_pass="", map=None):
        # Update an existing game?
        if doc_id:
            # Is the game ID still free?
            entry = self.db.get(doc_id=doc_id)
            code = entry.get("code")
            game_search_fragment = {"code" : code, "status" : "open"}
            GamesQ = Query()
            games = self.db.search(GamesQ.fragment(game_search_fragment))
            if (games) and len(games) > 0:
                # Game already exists
                return await ctx.send("Can not reinstate old game, because a new game with the code " + code + " already exists.", ephemeral=True)

            # Just update status and timestamp
            turns = entry.get("turns")
            turns[-1]["timestamp"] = datetime.datetime.utcnow().isoformat()
            self.db.update({"status" : "open", "turns": turns}, doc_ids=[doc_id])
            embed = await self.build_embed_for_game(ctx=ctx, doc_id=doc_id)
            return await ctx.send(embeds=[embed], ephemeral=True)
        elif code:
            await ctx.defer()
            game_search_fragment = {"code" : code, "status" : "open"}
            GamesQ = Query()
            games = self.db.search(GamesQ.fragment(game_search_fragment))
            if (games) and len(games) > 0:
                return await ctx.send("An open game with the code " + code + " already exists!", ephemeral=True)
            
            # Server only makes only sense if we are on a server
            this_server_id = ""
            if ctx.guild_id:
                this_server_id = str(ctx.guild_id)
            else:
                server_only = False

            # Mapdata contains always one more map than actually exist because the first mapdata entry is always blank
            if map < 1 or (map > (len(self.mapdata) - 1)):
                return await ctx.send("Map number " + str(map) + " unknown!", ephemeral=True)
            
            group_pass = group_pass[0:20]
            new_item = {    "code": code, 
                            "map": map, 
                            "server_only" : server_only,
                            "group_pass" : group_pass, 
                            "status" : "open",
                            "turns" : [
                                    {
                                        "user" : str(ctx.user.id),
                                        "server" : this_server_id,
                                        "timestamp" : datetime.datetime.utcnow().isoformat(),
                                    }
                                ],
                        }

            # Update database and inform users 
            doc_id = self.db.insert(new_item) 
            await self.notify_users(ctx=ctx, doc_id=doc_id, server_only=server_only, group_pass=group_pass)

            # Now show that a new game was added
            embed = await self.build_embed_for_game(ctx=ctx, doc_id=doc_id)
            components = await self.build_components_for_game(ctx=ctx, doc_id=doc_id)
            return await ctx.send(embeds=[embed], components=components, ephemeral=False)
        else:
            return await ctx.send("Creating new game failed.", ephemeral=True)

    # Abandon the game
    @interactions.extension_component("abandon_game")
    async def fee_abandon_game(self, ctx):
        await ctx.defer(ephemeral=True)
        # Get the open game from the last message
        doc_id = await self.get_doc_id_from_message(ctx, status="open")

        # Game found?
        if not doc_id:
            return await ctx.send("Could not find open game, maybe it was finished meanwhile?", ephemeral=True)

        # Game deletion allowed?
        delete_game_allowed = await self.can_user_delete_game(ctx=ctx, doc_id=doc_id)
        if not delete_game_allowed:
            return await ctx.send("Not allowed to remove the game! The players have a few days to finish this. If no activity is found after a few days, you can try deleting it again.", ephemeral=True)

        # Update game status
        self.db.update({"status" : "abandoned"}, doc_ids=[doc_id])

        # Build an embed for the host to reinstate the game if needed
        embed = await self.build_embed_for_game(ctx=ctx, doc_id=doc_id)
        embed.description = "This game has been **abandoned** on the request of **" + ctx.user.username + "#" + ctx.user.discriminator + "**. This can happen if the game has been inactive for a while.\n\n\n" + embed.description
        embed.description = embed.description[0:4096]
        # Host gets the "create new game" button
        button_reinstate = Button(style=3, custom_id="reinstate_game", label="Reinstate Game", emoji=interactions.Emoji(name="👼"))
        components = [[button_reinstate]]

        # If this is the host, simple update message. If it is not the host, send the host a private message.
        entry = self.db.get(doc_id=doc_id)
        turns = entry.get("turns", [])
        started_userid = turns[0]["user"]
        try:
            await ctx.message.delete()
        except:
            pass
        if str(ctx.user.id) == started_userid:
            return await ctx.send(embeds=[embed], components=components)
        else:
            started_userobj = await interactions.get(self.bot, interactions.User, object_id=started_userid)
            started_userobj._client = self.client._http
            await started_userobj.send(embeds=[embed], components=components)
            return await ctx.send("Game abandoned. The host can reinstate the game anytime if desired.", ephemeral=True)        

    # Reinstate the game
    @interactions.extension_component("reinstate_game")
    async def fee_reinstate_game(self, ctx):
        doc_id = await self.get_doc_id_from_message(ctx, status="abandoned")
        return await self.create_new_game(ctx=ctx, doc_id=doc_id)

    # Update the games status
    async def update_game(self, ctx, doc_id = None, new_status = "open"):
        if ctx.message and ctx.message.flags and ctx.message.flags == 64:
            ephemeral = True
        else:
            ephemeral = False

        if new_status == "success":
            ephemeral = False

        # Game found?
        if not doc_id:
            return await ctx.send("Game not found", ephemeral=True)
        entry = self.db.get(doc_id=doc_id)
        old_status = entry.get("status")
        if old_status != "open": 
            return await ctx.send("Game has been finished or abandoned by now! No update possible.", ephemeral=True)

        await ctx.defer(ephemeral=ephemeral)

        # Update game status
        self.db.update({"status" : new_status}, doc_ids=[doc_id])
        # Add the new user
        turns = entry.get("turns", [])
        this_server_id = ""
        if ctx.guild_id:
            this_server_id = str(ctx.guild_id)
        new_turn = {
                    "user" : str(ctx.user.id),
                    "server" : this_server_id,
                    "timestamp" : datetime.datetime.utcnow().isoformat(),
                }
        turns.append(new_turn)
        self.db.update({"turns" : turns}, doc_ids=[doc_id])

        # Build an embed with the new game data
        embed = await self.build_embed_for_game(ctx=ctx, doc_id=doc_id)

        # Add a picture if the game is fininshed, either way
        files = None
        if new_status == "success" or new_status == "finished":
            final_picture_path, final_picture_name = await self.get_finished_picture(status=new_status)
            embed.set_image(url="attachment://" + final_picture_name)
        
            # If the game is finished, send a message to everyone involved except for the last user    
            turns.pop()
            for turn in turns:
                userid = turn["user"]
                userobj = await interactions.get(self.bot, interactions.User, object_id=userid)
                userobj._client = self.client._http
                f = open(final_picture_path, mode='rb')
                fxy = interactions.File(
                    filename=final_picture_name,
                    fp=f,
                    description=str("Fee coop file")
                    )
                files = [fxy]
                await userobj.send(embeds=[embed], files=files)

            # We have to provide the file again and again for every single send
            f = open(final_picture_path, mode='rb')
            fxy = interactions.File(
                filename=final_picture_name,
                fp=f,
                description=str("Fee coop file")
                )
            files = [fxy]

        # Update message in the current channel for the updating user
        return await ctx.send(embeds=[embed], files=files, ephemeral=ephemeral)

    # Continue game
    @interactions.extension_component("game_ongoing")
    async def game_ongoing(self, ctx):
        doc_id = await self.get_doc_id_from_message(ctx, status="open")
        # User already in the game?
        entry = self.db.get(doc_id=doc_id)
        turns = entry.get("turns", [])
        if str(ctx.user.id) in [turn['user'] for turn in turns]:
            return await ctx.send("You have arleady participated in the game.", ephemeral=True)
        return await self.update_game(ctx=ctx, doc_id=doc_id, new_status="open")

    # Game successfully finished!
    @interactions.extension_component("game_success")
    async def game_success(self, ctx):
        doc_id = await self.get_doc_id_from_message(ctx, status="open")
        # User already in the game?
        entry = self.db.get(doc_id=doc_id)
        turns = entry.get("turns", [])
        if str(ctx.user.id) in [turn['user'] for turn in turns]:
            return await ctx.send("You have arleady participated in the game.", ephemeral=True)
        return await self.update_game(ctx=ctx, doc_id=doc_id, new_status="success")

    # Game successfully finished!
    @interactions.extension_component("game_over")
    async def game_over(self, ctx):
        doc_id = await self.get_doc_id_from_message(ctx, status="open")
        # User already in the game?
        entry = self.db.get(doc_id=doc_id)
        turns = entry.get("turns", [])
        if str(ctx.user.id) in [turn['user'] for turn in turns]:
            return await ctx.send("You have arleady participated in the game.", ephemeral=True)
        return await self.update_game(ctx=ctx, doc_id=doc_id, new_status="finished")

    # Join game failed
    @interactions.extension_component("join_game_failed")
    async def join_game_failed(self, ctx):
        return await ctx.send("This is unfortunate. You can ask the author if the game ID is wrong or if the game is already finished. The author can fix or remove this entry. If this doesn't help, then after a certain time without updates, the entry will be removed automatically.", ephemeral=True)

    # Select menu processing of game select
    @interactions.extension_component("show_game_docid")
    async def show_game_docid(self, ctx, value):
        doc_id = value[0]
        embed = await self.build_embed_for_game(ctx=ctx, doc_id=doc_id)
        components = await self.build_components_for_game(ctx=ctx, doc_id=doc_id)
        # Discord sets the flag 64 on ephemeral messages
        if ctx.message.flags == 64:
            ephemeral = True
        else:
            ephemeral = False
        return await ctx.send(embeds=[embed], components=components, ephemeral=ephemeral)

    # Select menu creating new game from mapid
    @interactions.extension_component("select_map")
    async def select_map(self, ctx, value):
        # Map was selected
        map = int(value[0])
        # And game ID is the first item in the title
        if not ctx.message.embeds:
            return await ctx.send("Failed to create game", ephemeral=True)
        code = ctx.message.embeds[0].title.split()[0]
        # Server only or group pass is in the footer
        footer = ""
        if ctx.message.embeds[0].footer:
            footer = ctx.message.embeds[0].footer.text
        group_pass = ""
        server_only = False
        if "Group pass" in footer:
            group_pass = footer.split()[2]
        elif "Only for server" in footer:
            server_only = True
        try:
            await ctx.message.delete()
        except:
            pass
        return await self.create_new_game(ctx=ctx, code=code, group_pass=group_pass, map=map, server_only=server_only)

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
            options = []
            components = None
            for result in results:
                embed = await self.build_embed_for_game(doc_id=result.doc_id, ctx=ctx)
                found_games.append(embed)
                if len(results) == 1:
                    # Just one game? Allow to join immediatly
                    components = await self.build_components_for_game(ctx=ctx, doc_id=result.doc_id)
                else:
                    # Multiple games? Then build a select menu for joining one
                    map = result.get("map")
                    mapname = self.mapdata[map]["name"]
                    mapemoji = self.emoji["map" + str(map)]
                    start = mapemoji.find(":", mapemoji.find(":") + 1) + 1
                    end = mapemoji.find(">")
                    emoji_id = mapemoji[start:end]
                    emoji = interactions.Emoji(id=emoji_id)
                    turns = result["turns"]
                    started_userid = turns[0]["user"]
                    started_serverid = turns[0]["server"]
                    started_userobj = await interactions.get(self.bot, interactions.User, object_id=started_userid)
                    if started_serverid:
                        started_serverobj = await interactions.get(self.bot, interactions.Guild, object_id=started_serverid)
                    username = started_userobj.username + "#" + started_userobj.discriminator
                    this_server_id = ""
                    if ctx.guild_id:
                        this_server_id = str(ctx.guild_id)
                    if started_serverid and started_serverid != this_server_id:
                        username += " (server " + started_serverobj.name + ")"
                    if len(options) < 25:
                        options.append(SelectOption(label=result.get("code"), 
                                                        value=result.doc_id, 
                                                        description=str(mapname + " by " + username)[:100],
                                                        emoji=emoji
                                                        )
                                                    )
                # Max amount of discord embeds
                embed_counter += 1
                if embed_counter >= 10:
                    break
            # Dont forget the select menu
            if len(results) > 1:
                s1 = SelectMenu(
                                    custom_id="show_game_docid",
                                    placeholder="Select game",
                                    options=options,
                                )
                components = [[s1]]
            return await ctx.send(embeds=found_games, components=components, ephemeral=True)
        else:
            return await ctx.send("No valid codes found in this message.", ephemeral=True)

def setup(client):
    FeeCoop(client)