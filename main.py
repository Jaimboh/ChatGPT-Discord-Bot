import os
import discord

from src.discordBot import DiscordClient, Sender
from src.logger import logger
from src.chatgpt import ChatGPT
from src.models import OpenAIModel
from src.memory import Memory


DISCORD_TOKEN = os.environ['DISCORD_TOKEN']
OPENAI_API = os.environ['OPENAI_API']
OPENAI_MODEL_ENGINE = os.environ['OPENAI_MODEL_ENGINE']
SYSTEM_MESSAGE = os.environ['SYSTEM_MESSAGE']


models = OpenAIModel(api_key=OPENAI_API, model_engine=OPENAI_MODEL_ENGINE)
memory = Memory(system_message=SYSTEM_MESSAGE)
chatgpt = ChatGPT(models, memory)


intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)


sender = Sender()


@client.event
async def on_ready():
    logger.info(f'Logged in as {client.user.name} - {client.user.id}')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!chat'):
        user_id = message.author.id
        receive = chatgpt.get_response(user_id, message.content[5:])
        await sender.send_message(message, message.content, receive)


@client.event
async def on_interaction(interaction):
    if interaction.author == client.user:
        return

    if interaction.data['name'] == 'chat':
        user_id = interaction.user.id
        receive = chatgpt.get_response(user_id, interaction.data['options'][0]['value'])
        await sender.send_message(interaction, interaction.data['options'][0]['value'], receive)

    if interaction.data['name'] == 'reset':
        user_id = interaction.user.id
        logger.info(f"resetting memory from {user_id}")
        try:
            chatgpt.clean_history(user_id)
            await interaction.response.send_message(f'> Reset chatGPT conversation history < - <@{user_id}>', ephemeral=True)
        except Exception as e:
            logger.error(f"Error resetting memory: {e}")
            await interaction.response.send_message('> Oops! Something went wrong. <', ephemeral=True)


def lambda_handler(event, context):
    client.run(DISCORD_TOKEN)


