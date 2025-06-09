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
@bot.command(name="ayuda")
async def ayuda(ctx):
    mensaje = """
📚 **Comandos disponibles**:

🔹 `!ayuda` - Muestra este mensaje.
🔹 `!promover @usuario` - Asigna el rol 'Docente' a un usuario (solo para docentes).
🔹 Otros comandos personalizados que tengas aquí...

Si tenés dudas, consultá con un Docente o administrador del servidor.
    """
    try:
        await ctx.author.send(mensaje)
        await ctx.send("📬 Te envié los comandos por privado.")
    except discord.Forbidden:
        await ctx.send("❌ No pude enviarte un mensaje privado. Asegurate de tener los DMs activados.")


@bot.command()
@commands.has_role("Docente")
async def canal_privado(ctx):
    await ctx.send("Este comando solo lo pueden usar docentes.")

@bot.command()
@commands.has_role("Docente")  # Solo docentes pueden usar este comando
async def promover(ctx, miembro: discord.Member):
    rol_docente = discord.utils.get(ctx.guild.roles, name="Docente")

    if not rol_docente:
        await ctx.send("⚠️ El rol 'Docente' no existe en este servidor.")
        return

    try:
        await miembro.add_roles(rol_docente)
        await ctx.send(f"✅ {miembro.mention} ahora es Docente.")
    except discord.Forbidden:
        await ctx.send("❌ No tengo permisos para asignar el rol 'Docente'.")
    except Exception as e:
        await ctx.send(f"⚠️ Ocurrió un error: {e}") 

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