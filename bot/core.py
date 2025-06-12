import discord
from discord.ext import commands
import dst
import os
from bot.database import inicializar_db

def get_bot():
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
    inicializar_db()
    return bot
