from ntpath import join
import discord
from discord.ext import commands
import requests
import dst

intents= discord.Intents.default()
intents.message_content= True

bot= commands.Bot(command_prefix ="!", intents=intents)


@bot.command()
async def prueba(ctx,*args):
    respuesta= ' '.join(args)
    await ctx.send(respuesta)

@bot.command()
async def saludo(ctx):
    apodo= ctx.author.nick if ctx.author.nick else ctx.author.name
    await ctx.send(f"Hola {apodo}, soy {bot.user.name} estoy aqui para ayudarte")


@bot.event
async def on_ready():
    
    print(f"El bot {bot.user} esta listo")

bot.run(dst.TOKEN)