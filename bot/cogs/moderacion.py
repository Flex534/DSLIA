import discord
from discord.ext import commands
import json
import os

BANEADOS_FILE = os.path.join(os.path.dirname(__file__), '../../baneados.json')

def cargar_baneados():
    if not os.path.exists(BANEADOS_FILE):
        return {}
    with open(BANEADOS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def guardar_baneados(baneados):
    with open(BANEADOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(baneados, f, ensure_ascii=False, indent=4)

def es_docente():
    async def predicate(ctx):
        return any(r.name.lower() == "docente" for r in ctx.author.roles)
    return commands.check(predicate)

class Moderacion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.baneados = cargar_baneados()

    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    @es_docente()
    async def ban(self, ctx, miembro: discord.Member, *, motivo: str = "Sin motivo"):
        try:
            # Solicitar comentario adicional al docente
            await ctx.send("¿Deseas agregar un comentario adicional para el usuario baneado? Responde este mensaje o escribe 'no' para omitir.")
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel
            try:
                comentario_msg = await self.bot.wait_for('message', check=check, timeout=30)
                comentario = comentario_msg.content if comentario_msg.content.lower() != 'no' else None
            except Exception:
                comentario = None
            await miembro.ban(reason=motivo)
            datos_ban = {"motivo": motivo, "comentario": comentario, "docente": str(ctx.author), "fecha": str(ctx.message.created_at)}
            self.baneados[str(miembro.id)] = datos_ban
            guardar_baneados(self.baneados)
            await ctx.send(f"{miembro} ha sido baneado. Motivo: {motivo}" + (f" | Comentario: {comentario}" if comentario else ""))
            try:
                mensaje_md = f"Has sido baneado del servidor '{ctx.guild.name}'. Motivo: {motivo}."
                if comentario:
                    mensaje_md += f"\nComentario del docente: {comentario}"
                await miembro.send(mensaje_md)
            except Exception:
                await ctx.send(f"No se pudo enviar mensaje privado a {miembro}.")
        except Exception as e:
            await ctx.send(f"Error al banear: {e}")

    @commands.command(name='unban')
    @commands.has_permissions(ban_members=True)
    @es_docente()
    async def unban(self, ctx, user_id: int):
        user = await self.bot.fetch_user(user_id)
        try:
            await ctx.guild.unban(user)
            if str(user_id) in self.baneados:
                del self.baneados[str(user_id)]
                guardar_baneados(self.baneados)
            await ctx.send(f"{user} ha sido desbaneado.")
        except Exception as e:
            await ctx.send(f"Error al desbanear: {e}")

    @commands.command(name='baneados')
    @commands.has_permissions(ban_members=True)
    @es_docente()
    async def listar_baneados(self, ctx):
        if not self.baneados:
            await ctx.send("No hay usuarios baneados.")
            return
        mensaje = "Usuarios baneados:\n"
        for uid, datos in self.baneados.items():
            motivo = datos["motivo"] if isinstance(datos, dict) else datos
            comentario = datos.get("comentario") if isinstance(datos, dict) else None
            docente = datos.get("docente") if isinstance(datos, dict) else None
            fecha = datos.get("fecha") if isinstance(datos, dict) else None
            mensaje += f"ID: {uid} | Motivo: {motivo}"
            if comentario:
                mensaje += f" | Comentario: {comentario}"
            if docente:
                mensaje += f" | Docente: {docente}"
            if fecha:
                mensaje += f" | Fecha: {fecha}"
            mensaje += "\n"
        await ctx.send(mensaje)

async def setup(bot):
    await bot.add_cog(Moderacion(bot))
