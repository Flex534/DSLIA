import discord
from discord.ext import commands

class Otros(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="prueba")
    async def prueba(self, ctx, *args):
        respuesta = ' '.join(args)
        await ctx.send(respuesta)

    @commands.command(name="saludo")
    async def saludo(self, ctx):
        apodo = ctx.author.nick if ctx.author.nick else ctx.author.name
        await ctx.send(f"Hola {apodo}, soy {self.bot.user.name} estoy aqui para ayudarte")

    @commands.command(name="help")
    async def help_command(self, ctx):
        embed = discord.Embed(title="Ayuda de comandos del bot", color=discord.Color.green())
        embed.add_field(name="!prueba <texto>", value="Repite el texto que escribas.", inline=False)
        embed.add_field(name="!saludo", value="El bot te saluda.", inline=False)
        embed.add_field(name="!subir", value="(Docente) Sube un archivo de teoría, TP o bibliografía.", inline=False)
        embed.add_field(name="!ver_archivos [filtro]", value="Muestra los archivos subidos. Puedes filtrar por 'teoria', 'tp', 'bibliografia'.", inline=False)
        embed.add_field(name="!descargar <categoria>", value="Muestra los archivos de la categoría elegida y permite descargarlos con botones interactivos.", inline=False)
        embed.add_field(name="!buscar [filtros]", value="Busca materiales por tipo, fecha o autor. Ejemplo: !buscar tipo=teoria fecha=2025-06-01 autor=Juan", inline=False)
        embed.add_field(name="!eliminar_archivo <nombre>", value="(Docente) Elimina un archivo por nombre.", inline=False)
        embed.add_field(name="!enviar_archivo <criterio>", value="Envía archivos por privado según nombre, tipo o 'todo'.", inline=False)
        embed.add_field(name="!agregar_entrega <nombre> <fecha> <hora> <#canal>", value="(Docente) Agrega una entrega y programa recordatorios automáticos. Fecha: YYYY-MM-DD, Hora: HH:MM.", inline=False)
        embed.add_field(name="!listar_entregas", value="Muestra la lista de entregas próximas.", inline=False)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"El bot {self.bot.user} está listo y los cogs están cargados.")

async def setup(bot):
    await bot.add_cog(Otros(bot))
