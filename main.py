import asyncio
import time
from ollama import chat
from ollama import AsyncClient
from ollama import ChatResponse
import discord
from discord.ext import commands
import random
import subprocess
import os
from dotenv import dotenv_values
import string
import nest_asyncio
nest_asyncio.apply()

#init:
greets = ["Hey", "Hello", "Hi", "Yo", "Howdy", "What's up", "Hiya", "Hey there", "Sup", "Greetings", "hoi", "moi", "fakka", "hallo", "goede", "!", "greet", "greetbot", "hoi,"]
farewells = ["farewell", "bye", "doei", "fuckoff", "go away", "ga weg", "later", "totziens", "farewell", "goodbye", "shutup", "ga", "go"]

ChatModel = 'llama3.2'
prefix = '!'
secrets = dotenv_values(".env")

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

#agreement or somthing
_intents = discord.Intents.default()
_intents.message_content = True
client = Client(intents= _intents)

client.run(secrets['discordBotToken'])
