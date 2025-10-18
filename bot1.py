# bot1.py
import json
import discord
import requests
import asyncio
import aiohttp
from collections import deque

# Data structure to store player IDs and total flight times
#flight_data = {}
bazaar_data = {}
api_keys = []

# File path for saving and loading flight data
#flight_data_path = "flight_data.json"
bazaar_data_path = "bazaar_data.json"
api_keys_path = "api_keys.json"

# Function to load saved flight data from a text file
#def load_flight_data():
    #try:
        #with open(flight_data_path, "r") as file:
            #return json.load(file)
    #except #FileNotFoundError:
        #return {}

def load_bazaar_data():
    try:
        with open(bazaar_data_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def load_api_keys():
    try:
        with open(api_keys_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

# Function to save flight data to a text file
#def save_flight_data():
    #with open(flight_data_path, "w") as file:
        #json.dump(flight_data, file)
# Function to save bazaar data to a text file        
def save_bazaar_data():
    with open(bazaar_data_path, "w") as file:
        json.dump(bazaar_data, file)
# Function to save api keys to a text file 
def save_api_keys():
    with open(api_keys_path, "w") as file:
        json.dump(api_keys, file)
        

        
#flight_data = load_flight_data()
bazaar_data = load_bazaar_data()
api_keys = load_api_keys()
     
#Api key cycling function        
keys_queue = deque(api_keys)
def get_next_key():		
	key = keys_queue.popleft()
	keys_queue.append(key)
	#save_api_keys()
	return key



async def fetch_url(session, url):
    max_retries = len(api_keys)
    retry_delay = 3  # seconds
    for attempt in range(max_retries):
        current_key = get_next_key()  # Get a key from your rotating queue
        modified_url = f"{url}{current_key}"  # Modify this line if your API uses headers or other methods for key authentication

        try:
            async with session.get(modified_url) as response:
                if response.status == 200:
                    json_response = await response.json()
                    if 'error' not in json_response:
                        return json_response  # Success
                    else:
                        print(f"API Error: {json_response['error']} on attempt {attempt + 1} for {modified_url}.")  # Debug: Print API error
                else:
                    print(f"HTTP Error: {response.status} on attempt {attempt + 1} for {modified_url}.")  # Debug: Print HTTP error
        except Exception as e:
            print(f"Exception during request: {e} on attempt {attempt + 1} for {modified_url}.")  # Debug: Print exceptions

        await asyncio.sleep(retry_delay)  # Wait before retrying

    print(f"Failed to fetch data after {max_retries} retries for {url}.")  # Debug: Print after all retries fail
    return None  # Failed to fetch data after retries