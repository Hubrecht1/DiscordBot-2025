import asyncio
import time
from ollama import chat
from datetime import datetime, timedelta
import discord
from discord.ext import commands
import random
import subprocess
import os
from dotenv import dotenv_values
import string
import nest_asyncio
nest_asyncio.apply()
import rooster
import requests
import pytz

#init:
greets = ["Hey", "Hello", "Hi", "Yo", "Howdy", "What's up", "Hiya", "Hey there", "Sup", "Greetings", "hoi", "moi", "fakka", "hallo", "goede", "!", "greet", "greetbot", "hoi,"]
farewells = ["farewell", "bye", "doei", "fuckoff", "go away", "ga weg", "later", "totziens", "farewell", "goodbye", "shutup", "ga", "go"]

ChatModel = 'llama3.2'
prefix = '!'
secrets = dotenv_values(".env")
currentRooster = rooster.rooster.openRooster(secrets["roosterFilePath"])
local_tz = pytz.timezone("Europe/Amsterdam")


class Client(discord.Client):
  lastUser = ''
  prevResponse = ''

  async def on_ready(self):
    channel = client.get_channel(895354381921304576)
    await init(self = self)
    await channel.send("Greet bot is online!")
    await asyncio.sleep(8)
    await changStatus()

  async def on_message(self,message):
    if message.author == self.user:
      return
    if message.content.startswith(prefix):
      await checkCustomCommands(message, prefix)
      return
    # checks wurm
    #await checkSpecialCase(message)

    userMessage = message.content.lower().split()
    if findWordsInMessage(greets, userMessage) == False and self.lastUser != message.author.name:
      client.lastUser = ''
      return
    try:
      loop = asyncio.get_running_loop()
    except RuntimeError:
     loop = None
    if loop == True and loop.is_running():
      task = asyncio.create_task(AIChat(message))
    else:
      asyncio.run(AIChat(message)) # Safe to run normally

async def init(self):
  formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
  os.system('open /Applications/Ollama.app')

  print(f'{formatted_time} SUCCESS: Logged on as {self.user}.')

def findWordsInMessage(words, message):
  return (any (normalWord.lower() == word for word in message for normalWord in words))

async def checkSpecialCase(message):
  words = ["breaking", "saul", "walter", "finger"]
  if message.author.id == 504740278855401482 and any(word in message.content for word in words):
      print(message.content)
      await message.channel.purge(limit = 1)
      await message.author.send(message.content + "please stop spamming wurmwillem, the gifs arent funny and they are very offensive")

async def changStatus():
  randInt = random.randint(1,5)
  response = asyncio.run(getAIResponse(f"Make up a discord status, max {randInt} words!"))
  await client.change_presence(activity = discord.CustomActivity(name = response))

async def checkCustomCommands(message, prefix):
  content = message.content.removeprefix(prefix)
  content = content.lower()
  content = content.split()
  if content[0] == 'restart':
    await message.channel.send('Shutting down...')
    await client.close()
    os.system('killall Ollama')
    subprocess.run('python3 main.py', shell=True)
  elif content[0]  == 'shutdown':
    await message.channel.send('Shutting down...')
    os.system('killall Ollama')
    await client.close()
  elif content[0] == 'change' and content[1] == 'status':
    if len(content) >= 3:
      customStatus = ' '
      for x in range(2,len(content)):
        customStatus += content[x]
      await client.change_presence(activity = discord.CustomActivity(name = asyncio.run(getAIResponse(customStatus))))
    else:
      await changStatus()
    await message.channel.send(f'Setting new status')
  elif content[0]  == 'clear':
    await message.channel.purge(limit = 1 + 1)
  elif content[0] == 'reset':
    client.lastUser = ''
    client.prevResponse = ''
  elif content[0] == 'github':
    await message.channel.send('https://github.com/Hubrecht1/DiscordBot-2025')
  elif content[0] == 'code':
    _file = discord.File(fp=secrets["codefilePath"])
    await message.channel.send(file=_file)
  elif content[0] == 'push':
    exit_code = os.system(f'cd {secrets["repPath"]} && git commit -a -m "Commited by {message.author.name} via discord" && git push')
    await message.channel.send(f"Exit code {exit_code}")
  elif content[0] == 'ping':
    await message.channel.send("pong")
  elif content[0] == 'friend':
    await message.author.send(asyncio.run(getAIResponse(f"{message.author.name} wants to be your friend")))
  elif content[0] == 'weather':
    if(len(content) == 1):
      await message.channel.send("Input city")
    else:
      city = ''
      for x in range(1,len(content)):
        city += ' ' + content[x]
      async with message.channel.typing():
        await message.channel.send(getWeather(city))
  elif content[0] == 'rooster':
    date = datetime.today().date() + timedelta(days=0)
    #sets date if optional parameter is used
    if len(content) >= 2:
      date = datetime.today().date() + timedelta(days=int(content[1]))
    events = [event for event in currentRooster.events if event.begin.date() == date]
    #create discord event:
    if len(content) >= 3 and content[2] == 'event':
      existingEvents = await getEventsInServer(message.guild)
      await createEvents(message, events, existingEvents)
    #send discord embeds:
    else:
      await sendEvents(message, events, date)
  elif content[0] == 'roosterweek':

    date = datetime.today().date() + timedelta(days=0)
    #sets date if optional parameter is used
    if len(content) >= 2:
      date = datetime.today().date() + timedelta(days=int(content[1]))
    #creates events if 'event' is typed
    if len(content) >= 3 and content[2]== 'event':
      week_later = date + timedelta(days=7)
      unique_days = sorted(set(event.begin.date() for event in currentRooster.events if date <= event.begin.date() < week_later))
      existingEvents = await getEventsInServer(message.guild)
      # Loop through events in the next week
      for day in unique_days:
       events = sorted([event for event in currentRooster.events if event.begin.date() == day],key=lambda e: e.begin)
       await createEvents(message ,events, existingEvents)
    else:
     await sendWeekEvents(message, currentRooster, date)

async def AIChat(messageInfo):
  userPrompt = ''
  userPrompt += (await getUserContext(messageInfo))

  userPrompt += messageInfo.content
  print(userPrompt)

  fullResponse = ''
  stream = chat(
    model=ChatModel,
    messages=[{'role': 'user', 'content': userPrompt}],
    stream=True,)
  i = 0
  async with messageInfo.channel.typing():
    print(f"...\n{ChatModel}:")
    for chunk in stream:
      i += len(chunk.message.content)
      if i >= 1700:
         break
      fullResponse += chunk.message.content
      print(chunk['message']['content'], end='', flush=True)
  print("\nDONE")
  if(i >= 1700):
    fullResponse += '...'
    await messageInfo.channel.send(fullResponse)
    await messageInfo.channel.send('(greetbots reactie was iets te lang)')
    print("\nexceeded word limit")
  else:
    await messageInfo.channel.send(fullResponse)

  client.prevResponse = fullResponse #update prev response

async def getAIResponse(message):
  fullResponse = ''
  stream = chat(
    model=ChatModel,
    messages=[{'role': 'user', 'content': message}],
    stream=True,)
  for chunk in stream:
    print(chunk['message']['content'], end='', flush=True)
    fullResponse += chunk.message.content
  print("\nDONE")
  return fullResponse

async def getUserContext(message):
  context = ''
  userPrompt = message.content.lower().split()
  if(findWordsInMessage(farewells, userPrompt)):
   context = f'\n{message.author.name} says bye: '
   client.lastUser = ''
   client.prevResponse = ''
  else :
    if(client.prevResponse != ''):
      context += "You: '" + client.prevResponse + "'" #adds previous response
    context += f'\n{message.author.name} says: '
    client.lastUser = message.author.name
  return context

async def sendEvents(message, events, date):
  for icsEvent in events:
    embed = discord.Embed(title= icsEvent.name, description=f"{icsEvent.begin.strftime('%H:%M')} - {icsEvent.end.strftime('%H:%M')},  {date.strftime('%A %-d %B')}", color=discord.Color.green())
    embed.set_footer(text= icsEvent.location)
    poll_message = await message.channel.send(embed=embed)
    await poll_message.add_reaction("✅")
    await poll_message.add_reaction("❌")

async def createEvents(message, events: list, existingEvents):
  for icsEvent in events:
     await createEvent(message, icsEvent, existingEvents)
     await asyncio.sleep(3)

async def sendWeekEvents(message, icsCalendar, startDate):
  week_later = startDate + timedelta(days=7)
  unique_days = sorted(set(event.begin.date() for event in icsCalendar.events if startDate <= event.begin.date() < week_later))
  # Loop through events in the next week
  for day in unique_days:
    events = sorted([event for event in icsCalendar.events if event.begin.date() == day],key=lambda e: e.begin)
    await sendEventsCompact(message, events, day)

async def sendEventsCompact(message, events, date):
  embed = discord.Embed(title= date.strftime('%A %-d %B') , color=discord.Color.green())
  for icsEvent in events:
    embed.add_field(name= f"{icsEvent.name} {icsEvent.begin.strftime('%H:%M')} - {icsEvent.end.strftime('%H:%M')}", value=icsEvent.location, inline=False)
  await message.channel.send(embed=embed)

async def createEvent(message, event, existingEvents):

  # Convert to UTC
  utc_time = event.begin.datetime.astimezone(pytz.UTC).isoformat()
  utc_time_end = event.end.datetime.astimezone(pytz.UTC).isoformat()

  url = f"https://discord.com/api/v10/guilds/{message.guild.id}/scheduled-events"
  headers = {
    "Authorization": f"Bot {secrets['discordBotToken']}",
    "Content-Type": "application/json"
  }
  payload = {
    "name": event.name,
    "description": f"{event.name}\n {event.begin.strftime('%H:%M')} - {event.end.strftime('%H:%M')}",
    "scheduled_start_time": utc_time,  # UTC format
    "scheduled_end_time": utc_time_end,
    "privacy_level": 2,  # 2 = GUILD_ONLY
    "entity_type": 3,  # 3 = External Event
    "entity_metadata": {
        "location": event.location
    }
  }

  if existingEvents != None:
        # Check if the event with the same name and time already exists
        for existing_event in existingEvents:
            # Compare the event start time and name (you can add more checks like location if needed)
            if existing_event['name'] == event.name and existing_event['scheduled_start_time'] == utc_time:
                print(f"Event {existing_event['name']} already exists")
                return
  else:
    return

  response = requests.post(url, json=payload, headers=headers)
  if(response.status_code != 200):
    await message.channel.send(f"Event '{event.name}' couldn't be created: {response}")
    print(f"ERROR {response} ({event.name} couldn't be posted))") #debug

 # fetch all events, returns json
async def getEventsInServer(guild):
  url = f"https://discord.com/api/v10/guilds/{guild.id}/scheduled-events"
  headers = {
    "Authorization": f"Bot {secrets["discordBotToken"]}",
    "Content-Type": "application/json"
  }
  #checks for existing events
  eventsResponse = requests.get(url, headers=headers)  # GET to fetch all events
  if eventsResponse.status_code == 200:
    return eventsResponse.json()
  else:
    print(f"ERROR {eventsResponse} (Existing events couldn't be fetched.)") #debug
    return None

def getWeather(city):
  url = f"https://wttr.in/{city}?format=j1"
  response = requests.get(url)

  if response.status_code != 200:
    print(response.status_code)
    return asyncio.run(getAIResponse(f"explain that the city:{city} doesn't exist"))
    #return f"{city} doesn't exist"

  data = response.json()
  current = data['current_condition'][0]
  nearest_area = data['nearest_area'][0]
  weather_info = {
        "City": nearest_area['areaName'][0]['value'],
        "Country":  nearest_area['country'][0]['value'],
        "Temperature (°C)": current['temp_C'],
        "Feels Like (°C)": current['FeelsLikeC'],
        "Weather": current['weatherDesc'][0]['value'],
        "Humidity (%)": current['humidity'],
        "Wind (km/h)": f"{current['windspeedKmph']} {current['winddir16Point']}",
        "Visibility (km)": current['visibility'],
        "Pressure (mb)": current['pressure'],
  }
  weather = ''
  for key, value in weather_info.items():
    weather += f"{key}: {value}\n"
  print(weather)
  return (asyncio.run(getAIResponse("You are the weather forecaster (dont introduce yourself)this is the data tell the weather (be very concise)" + weather)))

#agreement or somthing
_intents = discord.Intents.default()
_intents.message_content = True
client = Client(intents= _intents)

client.run(secrets['discordBotToken'])
