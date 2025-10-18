import discord
from discord.ext import commands
from discord import Embed
import bot1
import asyncio
import aiohttp
import requests
import time
import calendar
import logging

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)
#bot1.flight_data = bot1.load_flight_data()
bot1.bazaar_data = bot1.load_bazaar_data()
bot1.api_keys = bot1.load_api_keys()

#async def restart_bot():
    #await bot.close()
    #await asyncio.sleep(5)  # Optional delay to ensure the bot is fully closed
    #await bot.start(TOKEN)

@bot.event
async def on_ready():
	global flight_channel
	global bazaar_channel
	global se_channel
	flight_channel = bot.get_channel() #Put whatever channels the bot is to print in here.
	bazaar_channel = bot.get_channel()
	se_channel = bot.get_channel()
	print(f'We have logged in as {bot.user}')
	#bot.loop.create_task(check_api_flights())	
	#bot.loop.create_task(check_api_bazaar())
	#bot.loop.create_task(check_se_market())
	#while True:
		#await asyncio.sleep(21600)# 6 hours in seconds
		#print("Restarting bot")
		#await restart_bot()
        
def escape_discord_formatting(username):
	escape_map = {'_': '\\_', '*': '\\*', '~': '\\~', '`': '\\`', '|': '\\|'}
    
	for char, escaped_char in escape_map.items():
		username = username.replace(char, escaped_char)
    
	return username

@bot.command(name="addkey")
async def api_add(ctx, APIkey):
	test_request = requests.get("https://api.torn.com/user/1?selections=bazaar&key=%s&comment=TryItPage" % (APIkey))
	test_info = test_request.json()
	if "error" in test_info:
		await ctx.send("Invalid API key.")
	elif APIkey in bot1.api_keys:
		await ctx.send("That API key is already in the list.")
	else:
		bot1.api_keys.append(APIkey)
		bot1.save_api_keys()
		await ctx.send("API Key added.")
	
@bot.command(name="removekey")
async def api_remove(ctx, APIkey):
	if APIkey in bot1.api_keys:
		bot1.api_keys.remove(APIkey)
		bot1.save_api_keys()
		await ctx.send("Key removed.")
	elif APIkey not in bot1.api_keys:
		await ctx.send("That API key is not in the list.")
		
@bot.command(name="listkeys")
async def list_keys(ctx):
	if bot1.api_keys == []:
		await ctx.send("There are currently no API keys in the list.")
		return
	else:
		apikey_embed = Embed(title="API Keys", description = "")
		for APIkey in bot1.api_keys:
			username_request = requests.get("https://api.torn.com/user/?selections=profile&key=%s&comment=TryItPage" % (APIkey))
			username_info = username_request.json()
		
			apikey_embed.add_field(name = "", value = (username_info["name"] + "'s API Key - " + str(APIkey)), inline=False)
		await bazaar_channel.send(embed=apikey_embed)
		
	
#FORMAT {USERID: USERNAME, TOTAL BAZAAR VALUE, LAST ACTION TIMESTAMP, }
@bot.command(name="add")
async def bazaar_add(ctx, userID):
	bazaar_add_request = requests.get("https://api.torn.com/user/%s?selections=profile,bazaar&key=%s&comment=TryItPage" % (userID, bot1.get_next_key()))
	bazaar_add_info = bazaar_add_request.json()

	if userID in bot1.bazaar_data:
		await bazaar_channel.send("User already tracked.")
	elif "error" in bazaar_add_info:
		await bazaar_channel.send("Incorrect userID")
	elif(userID != "")  and ("error" not in bazaar_add_info) and (userID not in bot1.bazaar_data):
					
		total_bazaar_value = await get_bazaar_total(userID)
		bot1.bazaar_data[userID] = [escape_discord_formatting(bazaar_add_info["name"]), total_bazaar_value, (bazaar_add_info["last_action"]["timestamp"]), 0]
		await bazaar_channel.send(bot1.bazaar_data[userID][0] + " added to tracking.")
		bot1.save_bazaar_data()
		
		
@bot.command(name="remove")
async def bazaar_remove(ctx, userID):
	if userID in bot1.bazaar_data:
		removed_user = bot1.bazaar_data.pop(userID)
		bot1.save_bazaar_data()
		await bazaar_channel.send(removed_user[0] + " removed from tracking.")
	else:
		await bazaar_channel.send("This bazaar is not being tracked.")
		
		
@bot.command(name="btracking")
async def bazaar_list(ctx):
	if bot1.bazaar_data != {}:
		bazaar_embed = Embed(title=f"{len(bot1.bazaar_data)} Currently Tracked Users", description = "")
		for userID in bot1.bazaar_data:
			bazaar_embed.add_field(name = "", value=("[" + bot1.bazaar_data[userID][0] + "](https://www.torn.com/profiles.php?XID=%s)" % userID + "[" + str(userID) + "]"), inline=False)
		await bazaar_channel.send(embed=bazaar_embed)		
	else:
		await bazaar_channel.send("No bazaars currently tracked.")
		
@bot.command(name="check")
async def check(ctx, userID):
	if userID == userID in bot1.bazaar_data:
		await bazaar_channel.send(bot1.bazaar_data[userID])
			
			
async def get_bazaar_total(userID):
	async with aiohttp.ClientSession() as session:
		#bazaar_request = requests.get("https://api.torn.com/user/%s?selections=bazaar&key=%s" % (userID, get_next_key()))
		#bazaar_info = bazaar_request.json()
		
		bazaar_data_url = f"https://api.torn.com/user/{userID}?selections=bazaar&key={bot1.get_next_key()}&comment=TryItPage"
		target_bazaar_data = await bot1.fetch_url(session, bazaar_data_url)
		
		if target_bazaar_data is None:
			return 0
		
		bazaar_items = target_bazaar_data["bazaar"]
		if bazaar_items != []:
			total_bazaar_value = sum(item["price"] * item["quantity"] for item in bazaar_items)
			return int(total_bazaar_value)
		else:
			return 0
			
#FORMAT {USERID: USERNAME, TOTAL BAZAAR VALUE, LAST ACTION TIMESTAMP, RUNNING SOLD TOTAL}

#Keep running total of amount sold until user comes back online (last action > 2 mins). Reset running total if last action < 2 mins.

#PING REQUIREMENT - Last action > 2 mins, amount sold > 50m, out of hospital, landing soon, coming out of hospital soon. 

def format_sold(num):
    if num >= 1e12:
        return f"{num / 1e12:.2f}t"
    elif num >= 1e9:
        return f"{num / 1e9:.2f}b"
    elif num >= 1e6:
        return f"{num / 1e6:.2f}m"
    elif num >= 1e3:
        return f"{num / 1e3:.2f}k"
    else:
        return str(num)
        
def format_duration(seconds):
 
    minute = 60
    hour = 3600
    day = 86400

    if seconds < minute:
        return f"{seconds} second{'s' if seconds != 1 else ''}"
    elif seconds < hour:
        minutes = seconds // minute
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    elif seconds < day:
        hours = seconds // hour
        return f"{hours} hour{'s' if hours != 1 else ''}"
    else:
        days = seconds // day
        return f"{days} day{'s' if days != 1 else ''}"
        
def colour_choice(status):
	if status == "Offline":
		grey = 0xA9A9A9
		return grey
	elif status == "Online":
		green = 0x7BA400
		return green
	elif status == "Idle":
		orange = 0xDC9000
		return orange
		
def escape_discord_formatting_for_embeds(username):
    # Insert a zero-width space after each underscore for embeds
    return username.replace('\\_', '_\u200B')
	
@bot.command(name="commands")
async def bazaar_list(ctx):
	embed = discord.Embed(title="Full Command List",
                      colour=0xFFA500)

	embed.set_author(name = "", url="https://example.com")

	embed.add_field(name="__Flight Bot Commands__",
					value="",
					inline=False)
	embed.add_field(name="> !track \"id\"",
					value="Tracks a flying or abroad user.",
					inline=False)
	embed.add_field(name="> !untrack \"id\"",
					value="Untracks a tracked user.",
					inline=False)
	embed.add_field(name="> !tracking",
					value="Shows list of tracked targets.",
					inline=False)
	embed.add_field(name="__Bazaar Bot Commands__",
					value="",
					inline=True)
	embed.add_field(name="> !add \"id\"",
					value="Adds a bazaar to be tracked.",
					inline=False)
	embed.add_field(name="> !remove \"id\"",
					value="Removes a tracked bazaar.",
					inline=False)
	embed.add_field(name="> !btracking",
					value="Lists all bazaars being tracked.",
					inline=False)
	embed.add_field(name="__Other Commands__",
					value="",
					inline=False)
	embed.add_field(name="> !addkey \"key\"",
					value="Adds an API key",
					inline=False)
	embed.add_field(name="> !removekey \"key\"",
					value="Removes an API key",
					inline=False)
	embed.add_field(name="> !listkeys",
					value="Lists all API keys",
					inline=False)
	embed.add_field(name="> !commands",
					value="Lists all commands",
					inline=False)

	await ctx.send(embed=embed)
	
bot.run("") #Put discord bot key in quotes