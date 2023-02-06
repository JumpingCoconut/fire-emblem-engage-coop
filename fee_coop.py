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
                logging.info("Purge_old_entries: Game is " + str(days_since_last_activity) + " days old.")
                
                # Update game status
                self.db.update({"status" : "abandoned"}, doc_ids=[entry.doc_id])

                # Build an embed for the host to reinstate the game if needed
                embed = await self.build_embed_for_game(doc_id=entry.doc_id, show_private_information=True, for_server=None)
                embed.description = "This game has been **abandoned** automatically because it has been inactive for a while now so it likely has already been finished. If you want to list the game as open game again, just click the button below to **reinstate** it.\n\n\n" + embed.description
                embed.description = embed.description[0:4096]

                # Get the host object to send a private message
                started_userid = turns[0]["user"]
                started_userobj = await interactions.get(self.bot, interactions.User, object_id=started_userid)
                started_userobj._client = self.client._http

                # Host gets the "create new game" button
                components = await self.build_components_for_game(doc_id=entry.doc_id, for_user=started_userobj)
                logging.info("Purge_old_entries: Sending private message to " +  started_userobj.username + "#" + started_userobj.discriminator)
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
                last_activity = turns[-1]['timestamp']
                timestamp = datetime.datetime.fromisoformat(last_activity)
                return timestamp
            else:
                return datetime.datetime.max

        reverse_sort = False
        if for_user:
            reverse_sort = True
        sorted_games = sorted(games, key=sort_by_timestamp,reverse=reverse_sort)
        description = ""
        options = []
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
            
            # First line: Code and map
            code = entry["code"]
            if not status:
                # If no status was selected, show the current games status
                code += " (" + entry.get("status") + ")"
            if for_user and entry.get("group_pass"):
                code += " (group pass locked)"
            # If its the open game list, but ephemeral so only one user can see it anyways, might as well mark joined games 
            # TODO In future, this should be always checked and these games shouldnt appear in first place. Only makes sense after we have /fee pinboard though.
            #      Once /fee pinboard exists, we make this open list function to ephemeral only.
            if (not for_user) and ephemeral:
                user_is_participant, user_is_host = await self.is_user_in_game(doc_id=entry.doc_id, user=ctx.user)
                if user_is_participant:
                    code += " (already joined)"

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
            if started_serverid and (started_serverid != this_server_id):
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
        return await ctx.send(embeds=[embed], components=components, ephemeral=ephemeral)

    # Is the user part of this game? Expects a doc_id and a ctx.user object
    async def is_user_in_game(self, doc_id, user):
        entry = self.db.get(doc_id=doc_id)
        turns = entry.get("turns", [])
        user_is_participant = False
        user_is_host = False
        if str(user.id) in [turn['user'] for turn in turns]:
            user_is_participant = True
            if (str(user.id) == turns[0]['user']):
                user_is_host = True
        return user_is_participant, user_is_host

    # Can the user delete this game? Excpets a doc_id and a ctx.user object
    async def can_user_delete_game(self, doc_id, user):
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
        user_is_participant, user_is_host = await self.is_user_in_game(doc_id=doc_id, user=user)

        # Allow to abandon the game? Host can abandon always, participants after one day
        if user_is_host or (user_is_participant and days_since_last_activity > 1):
            return True
        elif days_since_last_activity > 2:
            # Everyone can abandon the game if its very old
            return True
        
        return False


    # Determines which buttons the user can see and returns them. Parameter for_user expects a ctx.user object or nothing.
    async def build_components_for_game(self, doc_id, for_user=None):
        components = None
        # Join - If the game is open and user didnt join already. Opens new modal with finished, lost and couldnt join
        # Abandon - If user is part of the group and game is old
        # Reinstate - Hosts can revive abandoned games

        entry = self.db.get(doc_id=doc_id)
        status = entry.get("status")
        turns = entry.get("turns", [])

        # Abandoned games can be reinstated by the host
        if status == "abandoned":
            if for_user and (str(for_user.id) == turns[0]["user"]):
                # Is the game ID still free?
                code = entry.get("code")
                game_search_fragment = {"code" : code, "status" : "open"}
                GamesQ = Query()
                games = self.db.search(GamesQ.fragment(game_search_fragment))
                if (not games) or len(games) == 0:
                    # No open game with this code exists, host can make one
                    button_reinstate = Button(style=3, custom_id="reinstate_game", label="Reinstate Game", emoji=interactions.Emoji(name="👼"))
                    components = [[button_reinstate]]

        elif status == "open":
            # Join game - show it always, we only check later if the user is already in the game.
            #if not user_is_participant:
            button_join = Button(style=3, custom_id="join_game", label="Join", emoji=interactions.Emoji(name="⚔️"))
            button_abandon = None

            if for_user:
                # Old games can be deleted
                delete_game_allowed = await self.can_user_delete_game(doc_id=doc_id, user=for_user)

                # Joining is only allowed if user is not in the game already
                user_is_participant, user_is_host = await self.is_user_in_game(doc_id=doc_id, user=for_user)
        
                # Allow to abandon the game? Host can abandon always, participants after one day
                if delete_game_allowed:
                    if user_is_participant:
                        button_abandon = Button(style=4, custom_id="abandon_game", label="Remove from open game list", emoji=interactions.Emoji(name="🇽"))
                    else:
                        button_abandon = Button(style=4, custom_id="abandon_game", label="Abandoned? Remove for EVERYONE", emoji=interactions.Emoji(name="⚠️"))

            # Arrange buttons for discord neatly
            if button_abandon:
                components = spread_to_rows(button_join, button_abandon)
            else:
                components = [[button_join]]
        
        return components

    # Makes one embed for each given game ID
    async def build_embed_for_game(self, doc_id, show_private_information=False, for_server=None):
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
            color = interactions.Color.white()

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
                if show_private_information:
                    embed.set_footer(text="Group pass: " + group_pass)
                else:
                    embed.set_footer(text="Group pass locked by " + started_userobj.username + "#" + started_userobj.discriminator)
            elif server_only and started_serverid:
                embed.set_footer(text="Only for server: " + started_serverobj.name, icon_url=started_serverobj.icon_url)

        if created_on:
            embed.timestamp=datetime.datetime.fromisoformat(created_on)

        if started_userid:
            username = started_userobj.username + "#" + started_userobj.discriminator
            # Only show the host servername if we are not on the host server anyways
            if started_serverid and ((not for_server) or (started_serverid != str(for_server))):
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
                    autocomplete=True,
            ),
            interactions.Option(
                    name="show_public",
                    description="Post the list public for everyone in this channel",
                    type=interactions.OptionType.BOOLEAN,
                    value=False,
                    required=False,
            ),
        ]
    )
    async def fee_opengames(self, ctx: interactions.CommandContext, server_only : bool = False, group_pass : str = None, show_public : bool = False):
        logging.info("Request fee_opengames by " + ctx.user.username + "#" + ctx.user.discriminator)
        ephemeral = not show_public
        return await self.show_game_list(ctx=ctx, server_only=server_only, group_pass=group_pass, status="open", for_user=None, ephemeral=ephemeral)


    # Fee mygames subcommand. Shows all games where the user participated
    @fee.subcommand(
        name="mygames",
        description="Show relay trials you participated in",
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
    # ATTENTION: To avoid spam, server_only is now true by default. Nobody getting notifs about EVERYTHING now.
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
                # interactions.Option(
                #         name="server_only",
                #         description="For ALL new games or just from this server?",
                #         type=interactions.OptionType.BOOLEAN,
                #         required=True,
                # ),
                interactions.Option(
                        name="group_pass",
                        description="Only watch a certain group pass (ignores server restrictions)",
                        type=interactions.OptionType.STRING,
                        min_length=0,
                        max_length=100,
                        required=False,
                        autocomplete=True,
                ),
            ]
        )
    # async def fee_notifications(self, ctx: interactions.CommandContext, active=True, server_only=True, group_pass=""):
    async def fee_notifications(self, ctx: interactions.CommandContext, active=True, group_pass=""):
        logging.info("Fee notifications by " + ctx.user.username + "#" + ctx.user.discriminator)

        # For now, act as if server_only is always on
        server_only = True

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

        # Server ID if the user wants only infos from one server
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
                messagetext += ". You set server_only to " + str(server_only)
                if server_only:
                    messagetext += ", meaning you will **only** get notifications about games created on this server and no notifications about games from all other servers"
                else:
                    messagetext += ", meaning you will get notifiations from all servers who chose to share them with everyone"
            if server_id != old_server_id and (not group_pass):
                if ctx.guild_id:
                    server_obj = await ctx.get_guild()
                    messagetext += ". Home server set to " + server_obj.name + ", so games which are only intended for this server will show up for you, too"
                elif old_server_id:
                    server_obj = await interactions.get(self.bot, interactions.Guild, object_id=old_server_id)
                    messagetext += ". Removed your old home server " + server_obj.name + " so you won't get updates for server-internal games from there anymore"
            if group_pass != old_group_pass:
                if group_pass:
                    messagetext += ". Watching only for group_pass " + group_pass + " now"
                else:
                    messagetext += ". Ignoring previous group pass \"" + old_group_pass + "\" now"
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
            # This game is only availible on this server so only look for users on this server
            # This is a workaround. Normally we would get a list of all members on this server and only send the message to them. 
            # But the code is restricted by discord. It would be: members = await server_obj.get_list_of_members()
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
            embed = await self.build_embed_for_game(doc_id=doc_id, show_private_information=False, for_server=None)
            description_server_name = ""
            if ctx.guild_id:
                server_obj = await ctx.get_guild()
                description_server_name = " on server " + server_obj.name
            embed.description = "A new game has been created" + description_server_name + "! You get this message because you turned **notifications on**. To deactivate notifications, reply with using this command:\n\n``/fee notifications``\n\n\n" + embed.description
            embed.description = embed.description[0:4096]
            components = await self.build_components_for_game(doc_id=doc_id, for_user=user_obj)
            logging.info("Notify_users: Sending private message to " + user_obj.username + "#" + user_obj.discriminator)
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
                        autocomplete=True,
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
                        min_length=0,
                        max_length=100,
                        required=False,
                        autocomplete=True,
                ),
            ]
        )
    async def fee_coop(self, ctx: interactions.CommandContext, code : str = "", server_only=False, group_pass=""):
        code = code.upper()
        game_search_fragment = {"code" : code, "status" : "open"}
        GamesQ = Query()
        games = self.db.search(GamesQ.fragment(game_search_fragment))
        if (games) and len(games) > 0:
            embed = await self.build_embed_for_game(doc_id=games[0].doc_id, show_private_information=False, for_server=ctx.guild_id)
            components = await self.build_components_for_game(doc_id=games[0].doc_id, for_user=None)
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
            ephemeral = False
            if group_pass:
                ephemeral = True
            return await ctx.send(embeds=[embed], components=components, ephemeral=ephemeral)
        
    # Autocompletion for the parameter "group_pass". Searches for previous group passes of that user and shows them
    @interactions.extension_autocomplete(command="fee", name="group_pass")
    async def autocomplete_group_pass(self, ctx, user_input: str = ""):
        logging.info("Autocomplete group pass by " + ctx.user.username + "#" + ctx.user.discriminator + " for " + str(user_input))
        options = []
        added_group_passes = []  

        # If the user has set a group pass to be notified about, that is probably the users favorite group pass, show it first
        user_config = self.db.table("user_config")
        UserQ = Query()
        entry = user_config.get(UserQ.user == str(ctx.user.id))
        if entry:
            notifications_group_pass = entry.get("notifications_group_pass", "")
            if notifications_group_pass:
                added_group_passes.append(notifications_group_pass)
                options.append(interactions.Choice(name=notifications_group_pass, value=notifications_group_pass))
          
        # Get a list of all games which have a group pass, and where the user participated in
        GamesQ = Query()
        TurnsQ = Query()
        games = self.db.search((GamesQ.group_pass != "") & (GamesQ.status != "abandoned") & (GamesQ.turns.any(TurnsQ.user == str(ctx.user.id))))

        # Now just check all these games for the group passes
        for entry in games:
            # Maximum of 25 results are allowed in discord. 
            if len(options) >= 25:
                break
            group_pass = entry.get("group_pass")
            if group_pass not in added_group_passes:
                if user_input in group_pass:
                    added_group_passes.append(group_pass)
                    options.append(interactions.Choice(name=group_pass, value=group_pass))

        await ctx.populate(options)

    # Autocompletion for the parameter "code". Searches open game IDs and tries to autocomplete them
    @interactions.extension_autocomplete(command="fee", name="code")
    async def autocomplete_code(self, ctx, user_input: str = ""):
        logging.info("Autocomplete code by " + ctx.user.username + "#" + ctx.user.discriminator + " for " + str(user_input))
        options = []

        # Before we read all open codes, check if the user belongs to a certain group pass
        user_config = self.db.table("user_config")
        UserQ = Query()
        entry = user_config.get(UserQ.user == str(ctx.user.id))
        notifications_group_pass = ""
        if entry:
            notifications_group_pass = entry.get("notifications_group_pass", "")

        # Get a list of all open games which either have no group pass, or the default group pass
        GamesQ = Query()
        games = self.db.search(((GamesQ.group_pass == "") | (GamesQ.group_pass == notifications_group_pass)) & (GamesQ.status == "open"))

        # Now just check all these games for the group passes
        for entry in games:
            # Maximum of 25 results are allowed in discord. 
            if len(options) >= 25:
                break
            code = entry.get("code")
            if user_input.upper() in code.upper():
                options.append(interactions.Choice(name=code, value=code))

        await ctx.populate(options)

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

        embed = await self.build_embed_for_game(doc_id=doc_id, show_private_information=False, for_server=ctx.guild_id)
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
        b4 = Button(style=4, custom_id="join_game_failed", label="Dead game? Click here to delete this game", emoji=interactions.Emoji(id=1068863333526151230))
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
            embed = await self.build_embed_for_game(doc_id=doc_id, show_private_information=True, for_server=ctx.guild_id)
            return await ctx.send(embeds=[embed], ephemeral=True)
        elif code:
            # Group pass locked games dont show public
            ephemeral = False
            if group_pass:
                ephemeral = True 
                
            await ctx.defer(ephemeral)
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
            embed = await self.build_embed_for_game(doc_id=doc_id, show_private_information=ephemeral, for_server=ctx.guild_id)
            components = await self.build_components_for_game(doc_id=doc_id, for_user=None)

            return await ctx.send(embeds=[embed], components=components, ephemeral=ephemeral)
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
        delete_game_allowed = await self.can_user_delete_game(doc_id=doc_id, user=ctx.user)
        if not delete_game_allowed:
            return await ctx.send("Not allowed to remove the game! The players have a few days to finish this. If no activity is found after a few days, you can try deleting it again.", ephemeral=True)

        # Prepare a deletion vote
        deletion_vote = {}
        deletion_vote['user'] = str(ctx.user.id)
        if ctx.guild_id:
            deletion_vote['server'] = str(ctx.guild_id)
        else:
            deletion_vote['server'] = ""
        deletion_votes = [deletion_vote]

        # Delete the game and send the host a info message
        return await self.delete_game_and_message_host(ctx, doc_id, deletion_votes)     

    # Reinstate the game
    @interactions.extension_component("reinstate_game")
    async def fee_reinstate_game(self, ctx):
        doc_id = await self.get_doc_id_from_message(ctx, status="abandoned")
        user_is_participant, user_is_host = await self.is_user_in_game(doc_id=doc_id, user=ctx.user)
        if not user_is_host:
            return await ctx.send("Only the host can reinstate this old game.", ephemeral=True)
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
        embed = await self.build_embed_for_game(doc_id=doc_id, show_private_information=False, for_server=None)

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
                logging.info("Update_game: Sending private message to " + userobj.username + "#" + userobj.discriminator)
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
        user_is_participant, user_is_host = await self.is_user_in_game(doc_id=doc_id, user=ctx.user)
        if user_is_participant:
            return await ctx.send("You have arleady participated in the game.", ephemeral=True)
        return await self.update_game(ctx=ctx, doc_id=doc_id, new_status="open")

    # Game successfully finished!
    @interactions.extension_component("game_success")
    async def game_success(self, ctx):
        doc_id = await self.get_doc_id_from_message(ctx, status="open")
        # User already in the game?
        user_is_participant, user_is_host = await self.is_user_in_game(doc_id=doc_id, user=ctx.user)
        if user_is_participant:
            return await ctx.send("You have arleady participated in the game.", ephemeral=True)
        return await self.update_game(ctx=ctx, doc_id=doc_id, new_status="success")

    # Game successfully finished!
    @interactions.extension_component("game_over")
    async def game_over(self, ctx):
        doc_id = await self.get_doc_id_from_message(ctx, status="open")
        # User already in the game?
        user_is_participant, user_is_host = await self.is_user_in_game(doc_id=doc_id, user=ctx.user)
        if user_is_participant:
            return await ctx.send("You have arleady participated in the game.", ephemeral=True)
        return await self.update_game(ctx=ctx, doc_id=doc_id, new_status="finished")

    # Join game failed
    @interactions.extension_component("join_game_failed")
    async def join_game_failed(self, ctx):
        doc_id = await self.get_doc_id_from_message(ctx, status="open")

        user_id = str(ctx.user.id)
        this_server_id = ""
        if ctx.guild_id:
            this_server_id = str(ctx.guild_id)

        # Check how many votes we have to delete this game
        entry = self.db.get(doc_id=doc_id)
        deletion_votes = entry.get("deletion_votes", [])
        if user_id in [deletion_vote['user'] for deletion_vote in deletion_votes]:
            return await ctx.send("You already voted to delete this game. Right now " + str(len(deletion_votes)) + " users voted to delete this game.", ephemeral=True)
        
        # Add vote to database#
        deletion_vote = {}
        deletion_vote['user'] = user_id
        deletion_vote['server'] = this_server_id
        deletion_votes.append(deletion_vote)
        self.db.update({"deletion_votes" : deletion_votes}, doc_ids=[entry.doc_id])

        # Do we have enough votes to delete the game?
        game_voted_for_deletion = False

        # Host can always delete
        turns = entry.get("turns", [])
        if len(turns) > 0:
            if user_id == turns[0]['user']:
                game_voted_for_deletion = True
        
        # 3 unique users can delete
        if len(deletion_votes) > 2:
            game_voted_for_deletion = True

        # If one user from another server agrees, also allow deletion
        if this_server_id not in [deletion_vote['server'] for deletion_vote in deletion_votes]:
            game_voted_for_deletion = True

        if not game_voted_for_deletion:
            return await ctx.send("Your vote to delete this game from the bot list has been accepted. Right now " + str(len(deletion_votes)) + " users voted to delete this game.", ephemeral=True)
        
        # Now delete the game and message the host
        return await self.delete_game_and_message_host(ctx, doc_id, deletion_votes) 

    # Delete a game and send the host a note that it was deleted by user vote
    async def delete_game_and_message_host(self, ctx, doc_id, deletion_votes):
        entry = self.db.get(doc_id=doc_id)
        self.db.update({"status" : "abandoned"}, doc_ids=[doc_id])
        
        deletion_voters_list = ""
        for deletion_vote in deletion_votes:
            userid = deletion_vote['user']
            serverid = deletion_vote['server']
            userobj = await interactions.get(self.bot, interactions.User, object_id=userid)
            deletion_voters_list += "\n" + userobj.username + "#" + userobj.discriminator
            if serverid:
                serverobj = await interactions.get(self.bot, interactions.Guild, object_id=serverid)
                deletion_voters_list += " from server " + serverobj.name
            
        # Build an embed for the host to reinstate the game if needed
        embed = await self.build_embed_for_game(doc_id=doc_id, show_private_information=True, for_server=None)
        embed.description = "This game has been **abandoned** on the request of: " + deletion_voters_list + "\n. It is likely that your game has been already finished but was still listed in the bot as open. If you want to list the game as open game again, just click the button below to **reinstate** it.\n\n\n" + embed.description
        embed.description = embed.description[0:4096]
        # Host gets the "create new game" button
        components = await self.build_components_for_game(doc_id=doc_id, for_user=ctx.user)

        # If this is the host, simple update message. If it is not the host, send the host a private message.
        entry = self.db.get(doc_id=doc_id)
        turns = entry.get("turns", [])
        started_userid = turns[0]["user"]
        try:
            await ctx.message.delete()
        except:
            logging.info("Tried deleting old message in delete_game_and_message_host. Failed. Not a problem.")
        if str(ctx.user.id) == started_userid:
            return await ctx.send(embeds=[embed], components=components, ephemeral=True)
        else:
            started_userobj = await interactions.get(self.bot, interactions.User, object_id=started_userid)
            started_userobj._client = self.client._http
            logging.info("delete_game_and_message_host: Sending private message to " + started_userobj.username + "#" + started_userobj.discriminator)
            await started_userobj.send(embeds=[embed], components=components)
            return await ctx.send("Game abandoned with " + str(len(deletion_votes)) + " votes. The host can reinstate the game anytime if desired.", ephemeral=True)      

    # Select menu processing of game select
    @interactions.extension_component("show_game_docid")
    async def show_game_docid(self, ctx, value):
        doc_id = value[0]
        # Discord sets the flag 64 on ephemeral messages
        if ctx.message.flags == 64:
            ephemeral = True
        else:
            ephemeral = False

        # For now: Always ephemeral
        ephemeral = True
        embed = await self.build_embed_for_game(doc_id=doc_id, show_private_information=ephemeral, for_server=ctx.guild_id)
        components = await self.build_components_for_game(doc_id=doc_id, for_user=ctx.user)
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
                embed = await self.build_embed_for_game(doc_id=result.doc_id, show_private_information=False, for_server=ctx.guild_id)
                found_games.append(embed)
                if len(results) == 1:
                    # Just one game? Allow to join immediatly
                    components = await self.build_components_for_game(doc_id=result.doc_id, for_user=ctx.user)
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