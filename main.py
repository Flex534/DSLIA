from ntpath import join
import discord
from discord.ext import commands
import requests
import dst

intents= discord.Intents.default()
intents.message_content= True
intents.members = True
@bot.event
async def on_member_join(member):
    # Nombre del rol a asignar automáticamente
    role_name = "Alumno"

    # Buscar el rol por nombre en el servidor
    role = discord.utils.get(member.guild.roles, name=role_name)

    if role:
        await member.add_roles(role)
        print(f"Se asignó el rol '{role_name}' a {member.name}")
    else:
        print(f"Rol '{role_name}' no encontrado en el servidor.")

bot= commands.Bot(command_prefix ="!", intents=intents)

@bot.command()
@commands.has_role("Docente")
async def canal_privado(ctx):
    await ctx.send("Este comando solo lo pueden usar docentes.")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("❌ No tenés permisos para usar este comando.")
    else:
        raise error  # para que otros errores se muestren normalmente

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