import discord
from discord.ext import commands, tasks
import sqlite3
import datetime
from bot.database import DB_PATH

class Entregas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.recordatorio_entregas.start()

    @commands.command(name="agregar_entrega")
    @commands.has_role("Docente")
    async def agregar_entrega(self, ctx):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        await ctx.send("Por favor, indica el nombre de la entrega:")
        try:
            nombre_msg = await self.bot.wait_for('message', check=check, timeout=60)
            nombre = nombre_msg.content.strip()
        except Exception:
            return await ctx.send("❌ Tiempo agotado o entrada inválida. Abortando.")
        await ctx.send("Indica la fecha de entrega (YYYY-MM-DD):")
        try:
            fecha_msg = await self.bot.wait_for('message', check=check, timeout=60)
            fecha = fecha_msg.content.strip()
            datetime.datetime.strptime(fecha, "%Y-%m-%d")
        except Exception:
            return await ctx.send("❌ Formato de fecha incorrecto o tiempo agotado. Abortando.")
        await ctx.send("Indica la hora de entrega (HH:MM, 24hs):")
        try:
            hora_msg = await self.bot.wait_for('message', check=check, timeout=60)
            hora = hora_msg.content.strip()
            datetime.datetime.strptime(hora, "%H:%M")
        except Exception:
            return await ctx.send("❌ Formato de hora incorrecto o tiempo agotado. Abortando.")
        await ctx.send("Menciona el canal donde enviar el recordatorio (ejemplo: #general):")
        def check_channel(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.raw_channel_mentions
        try:
            canal_msg = await self.bot.wait_for('message', check=check_channel, timeout=60)
            canal_id = canal_msg.raw_channel_mentions[0]
        except Exception:
            return await ctx.send("❌ No se mencionó un canal válido o tiempo agotado. Abortando.")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO entregas (nombre, fecha, hora, canal_id) VALUES (?, ?, ?, ?)''',
                       (nombre, fecha, hora, canal_id))
        conn.commit()
        conn.close()
        await ctx.send(f"✅ Entrega '{nombre}' agregada para el {fecha} a las {hora}.")

    @commands.command(name="listar_entregas")
    async def listar_entregas(self, ctx):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''SELECT nombre, fecha, hora FROM entregas ORDER BY fecha, hora''')
        entregas = cursor.fetchall()
        conn.close()
        if not entregas:
            await ctx.send("📭 No hay entregas registradas.")
            return
        mensaje = "\n".join([f"📌 {n} - {f} {h}" for n, f, h in entregas])
        await ctx.send(f"**Entregas próximas:**\n{mensaje}")

    @tasks.loop(minutes=30)
    async def recordatorio_entregas(self):
        ahora = datetime.datetime.now()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''SELECT id, nombre, fecha, hora, canal_id, recordado_24h, recordado_1h FROM entregas''')
        entregas = cursor.fetchall()
        for id_, nombre, fecha, hora, canal_id, rec24, rec1 in entregas:
            dt_entrega = datetime.datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
            delta = dt_entrega - ahora
            canal = self.bot.get_channel(canal_id)
            alumnos_rol = None
            if canal and canal.guild:
                alumnos_rol = discord.utils.get(canal.guild.roles, name="Alumno")
            mention = alumnos_rol.mention if alumnos_rol else "@everyone"
            if 0 < delta.total_seconds() <= 86400 and not rec24:
                if canal:
                    await canal.send(f"{mention} ⏰ Recordatorio: La entrega '{nombre}' es en 24 horas ({fecha} {hora})!")
                cursor.execute('UPDATE entregas SET recordado_24h = 1 WHERE id = ?', (id_,))
            if 0 < delta.total_seconds() <= 3600 and not rec1:
                if canal:
                    await canal.send(f"{mention} ⏰ Recordatorio: La entrega '{nombre}' es en 1 hora ({fecha} {hora})!")
                cursor.execute('UPDATE entregas SET recordado_1h = 1 WHERE id = ?', (id_,))
            if delta.total_seconds() < -3600:
                cursor.execute('DELETE FROM entregas WHERE id = ?', (id_,))
        conn.commit()
        conn.close()

async def setup(bot):
    await bot.add_cog(Entregas(bot))
