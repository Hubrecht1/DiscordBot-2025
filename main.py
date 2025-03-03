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

#init:
greets = ["Hey", "Hello", "Hi", "Yo", "Howdy", "What's up", "Hiya", "Hey there", "Sup", "Greetings", "hoi", "moi", "fakka", "hallo", "goede", "!", "greet", "greetbot"]
farewells = ["farewell", "bye", "doei", "fuck off", "go away", "ga weg", "later", "tot ziens", "farewell", "goodbye", "fuck off", "shut up"]

AIModel = 'llama3.2'
prefix = '!'

class Client(discord.Client):
  lastUser = ''
  async def on_ready(self):
    formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f'{formatted_time} SUCCESS: Logged on as {self.user}.')
    await changStatus()
    channel = client.get_channel(895354381921304576)
    await channel.send("Greet bot is online!")

  async def on_message(self,message):
    if message.author == self.user:
      return
    if message.content.startswith(prefix):
      await checkCustomCommands(message, prefix)
      return

    userMessage = message.content.lower().split()
    if findWordsInMessage(greets, userMessage) == False and self.lastUser != message.author.name:
      return
    try:
      loop = asyncio.get_running_loop()
    except RuntimeError:
     loop = None
    if loop and loop.is_running():
      asyncio.create_task(AIChat(message))
    else:
      asyncio.run(AIChat(message)) # Safe to run normally

def findWordsInMessage(words, message):
  return (any (normalWord.lower() == word for word in message for normalWord in words))

async def changStatus():
  newActivity = greets[random.randrange(len(greets)-1)]
  await client.change_presence(activity = discord.CustomActivity(name = newActivity))

async def checkCustomCommands(message, prefix):
  content = message.content.removeprefix(prefix)
  content = content.lower()
  if content == 'restart':
    await message.channel.send('Shutting down...')
    subprocess.run('python3 main.py', shell=True)
    await client.close()

  if content == 'shutdown':
    await message.channel.send('Shutting down...')
    await client.close()

  if content == 'change status':
    await changStatus()
    await message.channel.send(f'Setting new status')
  if content == 'clear':
    await message.channel.purge(limit = 1)
  if content == 'reset':
    client.lastUser = ' '  
      

async def AIChat(messageInfo):
  userPrompt = await getUserContext(messageInfo)
  userPrompt += messageInfo.content

  fullResponse = ''
  stream = chat(
    model=AIModel,
    messages=[{'role': 'user', 'content': userPrompt}],
    stream=True,)
  i = 0
  async with messageInfo.channel.typing():
    for chunk in stream:
     i += len(chunk.message.content)
     if i >= 1700:
        break
     fullResponse += chunk.message.content

  print(f"DeepSeek: {fullResponse}")
  if(i >= 2000):
    fullResponse += '...'
    await messageInfo.channel.send(fullResponse)
    await messageInfo.channel.send('(greetbots reactie was iets te lang)')
  else:
    await messageInfo.channel.send(fullResponse)

async def getUserContext(message):
  userPrompt = message.content.lower().split()
  if(findWordsInMessage(farewells, userPrompt)):
   context = f'{message.author.name} says bye: '
   client.lastUser = ''
  else :
    context = f'{message.author.name}: '
    client.lastUser = message.author.name
  return context

#agreement or somthing
_intents = discord.Intents.default()
_intents.message_content = True
client = Client(intents= _intents)

secrets = dotenv_values(".env")
client.run(secrets['discordBotToken'])
