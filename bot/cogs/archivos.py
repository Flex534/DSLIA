import discord
from discord.ext import commands
import os
import datetime
import aiofiles
import sqlite3
from bot.database import DB_PATH
from discord.ui import View, Button

class Archivos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="subir")
    @commands.has_role("Docente")
    async def subir(self, ctx):
        await ctx.send("Por favor, indica el tipo de archivo:\n`teoria` (Teo), `tp` (Trabajo práctico), `bibliografia` (Bib)")
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            tipo_msg = await self.bot.wait_for('message', check=check, timeout=60)
            tipo_input = tipo_msg.content.lower().strip()
        except Exception:
            return await ctx.send("❌ Tiempo agotado o entrada inválida. Abortando.")
        tipos_validos = {"teoria": "Teo", "tp": "TP", "bibliografia": "BIB"}
        if tipo_input not in tipos_validos:
            return await ctx.send("❌ Tipo inválido. Debe ser `teoria`, `tp` o `bibliografia`.")
        tipo = tipos_validos[tipo_input]
        await ctx.send("Ahora envíame el archivo que querés subir.")
        def check_file(m):
            return m.author == ctx.author and m.channel == ctx.channel and len(m.attachments) > 0
        try:
            archivo_msg = await self.bot.wait_for('message', check=check_file, timeout=120)
        except Exception:
            return await ctx.send("❌ Tiempo agotado o no enviaste un archivo. Abortando.")
        archivo = archivo_msg.attachments[0]
        nombre_archivo = archivo.filename
        carpeta = tipo_input
        ruta_carpeta = os.path.join("archivos", carpeta)
        os.makedirs(ruta_carpeta, exist_ok=True)
        ruta_guardado = os.path.join(ruta_carpeta, nombre_archivo)
        async with aiofiles.open(ruta_guardado, 'wb') as f:
            contenido = await archivo.read()
            await f.write(contenido)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO archivos (nombre_archivo, ruta_archivo, tipo, fecha_subida, autor_id, autor_nombre)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            nombre_archivo,
            ruta_guardado,
            tipo,
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ctx.author.id,
            str(ctx.author)
        ))
        conn.commit()
        conn.close()
        await ctx.send(f"✅ Archivo `{nombre_archivo}` guardado correctamente en `{carpeta}`.")

    @commands.command(name="ver_archivos")
    async def ver_archivos(self, ctx, *, tipos_filtro: str = ""):
        filtros = [t.strip().lower() for t in tipos_filtro.split(",") if t.strip()] if tipos_filtro else []
        tipo_mapeo = {
            "teo": "Teo",
            "tp": "TP",
            "bib": "BIB",
            "bibliografia": "BIB",
            "teoria": "Teo",
            "trabajo practico": "TP",
            "trabajopractico": "TP"
        }
        tipos_solicitados = set()
        for f in filtros:
            tipo_db = tipo_mapeo.get(f)
            if tipo_db:
                tipos_solicitados.add(tipo_db)
        mostrar_todos = not tipos_solicitados
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT nombre_archivo, tipo, fecha_subida FROM archivos ORDER BY tipo, fecha_subida DESC")
        archivos = cursor.fetchall()
        conn.close()
        if not archivos:
            return await ctx.send("📭 No hay archivos subidos todavía.")
        tipos = {"Teo": [], "TP": [], "BIB": []}
        for nombre, tipo, fecha in archivos:
            if mostrar_todos or tipo in tipos_solicitados:
                tipos[tipo].append(f"📄 `{nombre}` (subido: {fecha})")
        embed = discord.Embed(title="📚 Archivos disponibles", color=discord.Color.blue())
        if tipos["Teo"]:
            embed.add_field(name="📘 Teoría", value="\n".join(tipos["Teo"]), inline=False)
        if tipos["TP"]:
            embed.add_field(name="🧪 Trabajos Prácticos", value="\n".join(tipos["TP"]), inline=False)
        if tipos["BIB"]:
            embed.add_field(name="📖 Bibliografía", value="\n".join(tipos["BIB"]), inline=False)
        if not embed.fields:
            return await ctx.send("❌ No se encontraron archivos con los filtros indicados.")
        await ctx.send(embed=embed)

    @commands.command(name="eliminar_archivo")
    @commands.has_role("Docente")
    async def eliminar_archivo(self, ctx, *, nombre_archivo: str):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT ruta_archivo FROM archivos WHERE nombre_archivo = ?", (nombre_archivo,))
        resultado = cursor.fetchone()
        if not resultado:
            await ctx.send(f"❌ No se encontró un archivo con el nombre `{nombre_archivo}`.")
            conn.close()
            return
        ruta_archivo = resultado[0]
        try:
            os.remove(ruta_archivo)
        except FileNotFoundError:
            await ctx.send(f"⚠️ El archivo `{nombre_archivo}` no se encontró en el sistema de archivos. Se eliminará solo de la base de datos.")
        cursor.execute("DELETE FROM archivos WHERE nombre_archivo = ?", (nombre_archivo,))
        conn.commit()
        conn.close()
        await ctx.send(f"✅ Archivo `{nombre_archivo}` eliminado correctamente.")

    @commands.command(name="enviar_archivo")
    async def enviar_archivo(self, ctx, *, criterio: str):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        criterio = criterio.strip().lower()
        if criterio == "todo":
            cursor.execute("SELECT nombre_archivo, ruta_archivo FROM archivos")
        elif criterio in ["tp", "teo", "bib"]:
            tipo_mapeo = {"tp": "TP", "teo": "Teo", "bib": "BIB"}
            cursor.execute("SELECT nombre_archivo, ruta_archivo FROM archivos WHERE tipo = ?", (tipo_mapeo[criterio],))
        else:
            cursor.execute("SELECT nombre_archivo, ruta_archivo FROM archivos WHERE nombre_archivo = ?", (criterio,))
        resultados = cursor.fetchall()
        conn.close()
        if not resultados:
            await ctx.send("❌ No se encontraron archivos con ese criterio.")
            return
        try:
            for nombre, ruta in resultados:
                if os.path.exists(ruta):
                    await ctx.author.send(file=discord.File(ruta))
                else:
                    await ctx.author.send(f"⚠️ El archivo `{nombre}` no se encontró en el sistema.")
            await ctx.send("📩 Archivos enviados por privado.")
        except discord.Forbidden:
            await ctx.send("❌ No puedo enviarte mensajes privados. Verificá que tenés los DMs activados.")

    @commands.command(name="descargar")
    async def descargar(self, ctx, categoria: str = None):
        categorias = {"teoria": "Teo", "tp": "TP", "bibliografia": "BIB"}
        if categoria is None or categoria.lower() not in categorias:
            await ctx.send("Indica la categoría: `teoria`, `tp` o `bibliografia` (ejemplo: !descargar teoria)")
            return
        tipo = categorias[categoria.lower()]
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT nombre_archivo, ruta_archivo FROM archivos WHERE tipo = ? ORDER BY fecha_subida DESC", (tipo,))
        archivos = cursor.fetchall()
        conn.close()
        if not archivos:
            await ctx.send("No hay archivos en esa categoría.")
            return
        class ArchivoView(View):
            def __init__(self, archivos):
                super().__init__(timeout=60)
                for nombre, ruta in archivos[:10]:
                    self.add_item(Button(label=nombre, style=discord.ButtonStyle.primary, custom_id=nombre))
                self.rutas = {nombre: ruta for nombre, ruta in archivos}
            async def interaction_check(self, interaction):
                return interaction.user == ctx.author
            @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger, row=1)
            async def cancelar(self, interaction: discord.Interaction, button: Button):
                await interaction.response.edit_message(content="Operación cancelada.", view=None)
                self.stop()
            async def on_timeout(self):
                for item in self.children:
                    item.disabled = True
        view = ArchivoView(archivos)
        async def button_callback(interaction: discord.Interaction):
            nombre = interaction.data['custom_id']
            ruta = view.rutas.get(nombre)
            if ruta and os.path.exists(ruta):
                await interaction.response.send_message(f"Enviando `{nombre}`...", ephemeral=True)
                await ctx.send(file=discord.File(ruta))
            else:
                await interaction.response.send_message(f"No se encontró el archivo `{nombre}`.", ephemeral=True)
            view.stop()
        for item in view.children:
            if isinstance(item, Button) and item.label != "Cancelar":
                item.callback = button_callback
        await ctx.send(f"Selecciona un archivo de {categoria.title()}:", view=view)

    @commands.command(name="buscar")
    async def buscar(self, ctx):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT tipo FROM archivos")
        tipos = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT date(fecha_subida) FROM archivos")
        fechas = [row[0] for row in cursor.fetchall() if row[0]]
        cursor.execute("SELECT DISTINCT autor_nombre FROM archivos")
        autores = [row[0] for row in cursor.fetchall() if row[0]]
        conn.close()
        class FiltrosView(View):
            def __init__(self):
                super().__init__(timeout=120)
                self.tipo = None
                self.fecha = None
                self.autor = None
                self.resultados = None
                if tipos:
                    self.add_item(discord.ui.Select(placeholder="Filtrar por tipo (opcional)", options=[discord.SelectOption(label=t, value=t) for t in tipos], custom_id="tipo", min_values=0, max_values=1))
                if fechas:
                    self.add_item(discord.ui.Select(placeholder="Filtrar por fecha (opcional)", options=[discord.SelectOption(label=f, value=f) for f in fechas], custom_id="fecha", min_values=0, max_values=1))
                if autores:
                    self.add_item(discord.ui.Select(placeholder="Filtrar por autor (opcional)", options=[discord.SelectOption(label=a, value=a) for a in autores], custom_id="autor", min_values=0, max_values=1))
                self.add_item(Button(label="Buscar", style=discord.ButtonStyle.success, custom_id="buscar"))
                self.add_item(Button(label="Cancelar", style=discord.ButtonStyle.danger, custom_id="cancelar"))
            async def interaction_check(self, interaction):
                return interaction.user == ctx.author
            async def on_timeout(self):
                for item in self.children:
                    item.disabled = True
        view = FiltrosView()
        async def select_callback(interaction: discord.Interaction):
            cid = interaction.data['custom_id']
            value = interaction.data['values'][0] if interaction.data.get('values') else None
            if cid == "tipo":
                view.tipo = value
            elif cid == "fecha":
                view.fecha = value
            elif cid == "autor":
                view.autor = value
            await interaction.response.defer()
        async def buscar_callback(interaction: discord.Interaction):
            query = "SELECT nombre_archivo, tipo, fecha_subida, autor_nombre, ruta_archivo FROM archivos WHERE 1=1"
            params = []
            if view.tipo:
                query += " AND tipo = ?"
                params.append(view.tipo)
            if view.fecha:
                query += " AND date(fecha_subida) = ?"
                params.append(view.fecha)
            if view.autor:
                query += " AND autor_nombre = ?"
                params.append(view.autor)
            query += " ORDER BY fecha_subida DESC LIMIT 15"
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(query, params)
            resultados = cursor.fetchall()
            conn.close()
            if not resultados:
                await interaction.response.edit_message(content="No se encontraron archivos con esos filtros.", view=None)
                return
            class ResultadosView(View):
                def __init__(self, archivos):
                    super().__init__(timeout=60)
                    for nombre, _, _, _, _ in archivos[:10]:
                        self.add_item(Button(label=nombre, style=discord.ButtonStyle.primary, custom_id=nombre))
                    self.rutas = {nombre: ruta for nombre, _, _, _, ruta in archivos}
                async def interaction_check(self, interaction):
                    return interaction.user == ctx.author
                @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger, row=1)
                async def cancelar(self, interaction: discord.Interaction, button: Button):
                    await interaction.response.edit_message(content="Operación cancelada.", view=None)
                    self.stop()
                async def on_timeout(self):
                    for item in self.children:
                        item.disabled = True
            resultados_view = ResultadosView(resultados)
            async def button_callback(interaction: discord.Interaction):
                nombre = interaction.data['custom_id']
                ruta = resultados_view.rutas.get(nombre)
                if ruta and os.path.exists(ruta):
                    await interaction.response.send_message(f"Enviando `{nombre}`...", ephemeral=True)
                    await ctx.send(file=discord.File(ruta))
                else:
                    await interaction.response.send_message(f"No se encontró el archivo `{nombre}`.", ephemeral=True)
                resultados_view.stop()
            for item in resultados_view.children:
                if isinstance(item, Button) and item.label != "Cancelar":
                    item.callback = button_callback
            embed = discord.Embed(title="Resultados de búsqueda", color=discord.Color.purple())
            for nombre, tipo, fecha, autor, _ in resultados:
                embed.add_field(name=nombre, value=f"Tipo: {tipo}\nFecha: {fecha}\nAutor: {autor}", inline=False)
            await interaction.response.edit_message(content=None, embed=embed, view=resultados_view)
        async def cancelar_callback(interaction: discord.Interaction):
            await interaction.response.edit_message(content="Operación cancelada.", view=None)
            view.stop()
        for item in view.children:
            if isinstance(item, discord.ui.Select):
                item.callback = select_callback
            elif isinstance(item, Button):
                if item.custom_id == "buscar":
                    item.callback = buscar_callback
                elif item.custom_id == "cancelar":
                    item.callback = cancelar_callback
        await ctx.send("Selecciona los filtros para buscar materiales:", view=view)

async def setup(bot):
    await bot.add_cog(Archivos(bot))
