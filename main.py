import asyncio
import discord
import json
import overwatch
import league
import strings as s
import telegram

loop = asyncio.get_event_loop()
d_client = discord.Client()
discord_is_ready = False


# When Discord is ready, set discord_is_ready to True
@d_client.event
async def on_ready():
    global discord_is_ready
    discord_is_ready = True

# Get player database from the db.json file
file = open("db.json")
db = json.load(file)
file.close()

# Get the discord bot token from "discordtoken.txt"
file = open("discordtoken.txt", "r")
token = file.read()
file.close()

# Every timeout seconds, update player status and check for levelups
async def overwatch_level_up(timeout):
    while True:
        if discord_is_ready:
            print("[Overwatch] Starting check...")
            # Update data for every player in list
            for player in db:
                if "overwatch" in db[player]:
                    r = await overwatch.get_player_data(**db[player]["overwatch"])
                    if r["data"]["level"] > db[player]["overwatch"]["level"]:
                        # Send the message
                        loop.create_task(send_event(eventmsg=s.overwatch_level_up,
                                                    player=player,
                                                    level=r["data"]["level"]))
                        # Update database
                        db[player]["overwatch"]["level"] = r["data"]["level"]
                        f = open("db.json", "w")
                        json.dump(db, f)
                        f.close()
            print("[Overwatch] Check completed successfully.")
            # Wait for the timeout
            await asyncio.sleep(timeout)
        else:
            await asyncio.sleep(1)

# Every timeout seconds, update player league and check for rank changes
async def league_rank_change(timeout):
    while True:
        if discord_is_ready:
            print("[League] Starting check...")
            # Update data for every player in list
            for player in db:
                if "league" in db[player]:
                    try:
                        r = await league.get_player_rank(**db[player]["league"])
                    except league.NoRankedGamesCompletedException:
                        # If the player has no ranked games completed, skip him
                        continue
                    except league.RateLimitException:
                        # If you've been ratelimited, skip the player and notify the console.
                        print("[League] Request rejected for rate limit.")
                    else:
                        # Convert tier into a number
                        tier_number = league.ranklist.index(r["tier"])
                        roman_number = league.roman.index(r["entries"][0]["division"])
                        # Check for tier changes
                        if tier_number != db[player]["league"]["tier"] or roman_number != db[player]["league"]["division"]:
                            # Send the message
                            loop.create_task(send_event(eventmsg=s.league_rank_up,
                                                        player=player,
                                                        tier=s.league_tier_list[tier_number],
                                                        division=r["entries"][0]["division"]))
                            # Update database
                            db[player]["league"]["tier"] = tier_number
                            db[player]["league"]["division"] = roman_number
                            f = open("db.json", "w")
                            json.dump(db, f)
                            f.close()
                    finally:
                        # Prevent getting ratelimited by Riot
                        await asyncio.sleep(1)
            print("[League] Check completed.")
            # Wait for the timeout
            await asyncio.sleep(timeout)
        else:
            await asyncio.sleep(1)

# Send a new event to both Discord and Telegram
async def send_event(eventmsg: str, player: str, **kwargs):
    # Create arguments dict
    mapping = kwargs.copy()
    mapping["eventmsg"] = None
    # Discord
    # The user id is the player argument; convert that into a mention
    mapping["player"] = "<@" + player + ">"
    # Format the event message
    msg = eventmsg.format(**mapping)
    # Send the message
    loop.create_task(d_client.send_message(d_client.get_channel("213655027842154508"), msg))
    # Telegram
    # Find the matching Telegram username inside the db
    mapping["player"] = "@" + db[player]["telegram"]["username"]
    # Convert the Discord Markdown to Telegram Markdown
    msg = eventmsg.replace("**", "*")
    # Format the event message
    msg = msg.format(**mapping)
    # Send the message
    loop.create_task(telegram.send_message(msg, -2141322))


loop.create_task(overwatch_level_up(900))
print("[Overwatch] Added level up check to the queue.")

loop.create_task(league_rank_change(900))
print("[League] Added rank change check to the queue.")

try:
    loop.run_until_complete(d_client.start(token))
except KeyboardInterrupt:
    loop.run_until_complete(d_client.logout())
    # cancel all tasks lingering
finally:
    loop.close()
