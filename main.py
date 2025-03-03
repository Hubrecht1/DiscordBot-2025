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
OllamaModel = 'llama3.2'
prefix = '!'

class Client(discord.Client):
  async def on_ready(self):
    formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f'{formatted_time} SUCCESS: Logged on as {self.user}.')
    await changStatus()
    channel = client.get_channel(895354381921304576)
    await channel.send("Greet bot is online!")

  async def on_message(self,message):
    if message.author == self.user:
      return
    userMessage = message.content.lower().split()
    if message.content.startswith(prefix):
      await checkCustomCommands(message, prefix)
      return

    if any(greet.lower() == word for word in userMessage for greet in greets) == False:
      return
    try:
      loop = asyncio.get_running_loop()
    except RuntimeError:
     loop = None
    if loop and loop.is_running():
      task = asyncio.create_task(deepSeekChat(message.content, message))
    else:
      asyncio.run(deepSeekChat(message.content, message)) # Safe to run normally

async def changStatus():
  newActivity = greets[random.randrange(len(greets)-1)]
  await client.change_presence(activity = discord.CustomActivity(name = newActivity))

async def checkCustomCommands(message, prefix):
  content = message.content.removeprefix(prefix)

  if content == 'Restart':
    await message.channel.send('Shutting down...')
    subprocess.run('python3 main.py', shell=True)
    await client.close()

  if content == 'Shutdown':
    await message.channel.send('Shutting down...')
    await client.close()

  if content == 'Change status':
    await changStatus()
    await message.channel.send(f'Setting new status')

async def deepSeekChat(content, messageInfo):
  fullResponse = ''
  stream = chat(
    model=OllamaModel,
    messages=[{'role': 'user', 'content': content}],
    stream=True,)
  i = 0
  async with messageInfo.channel.typing():

    for chunk in stream:
     i += len(chunk.message.content)
     if i >= 2000:
        break
     fullResponse += chunk.message.content

  print(f"DeepSeek: {fullResponse}")
  if(i >= 2000):
    fullResponse += '...'
    await messageInfo.channel.send(fullResponse)
    await messageInfo.channel.send('(greetbots reactie was iets te lang)')
  else:
    await messageInfo.channel.send(fullResponse)


#agreement or somthing
_intents = discord.Intents.default()
_intents.message_content = True
client = Client(intents= _intents)

secrets = dotenv_values(".env")
client.run(secrets['discordBotToken'])
