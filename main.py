from ntpath import join
import discord
from discord.ext import commands, tasks
import requests
import dst  #necesario para activar el token del bot
import os 
import datetime
import aiofiles
import sqlite3
from discord.ui import View, Button

intents= discord.Intents.default()
intents.message_content= True

bot= commands.Bot(command_prefix ="!", intents=intents, help_command=None)

from db import inicializar_db, DB_PATH
inicializar_db()

@bot.command(name="prueba")
async def prueba(ctx,*args):
    respuesta= ' '.join(args)
    await ctx.send(respuesta)

@bot.command(name="saludo")
async def saludo(ctx):
    apodo= ctx.author.nick if ctx.author.nick else ctx.author.name
    await ctx.send(f"Hola {apodo}, soy {bot.user.name} estoy aqui para ayudarte")



#subir 1 dependiendo de si es teoria, practico o bibliografia
@bot.command(name="subir")
@commands.has_role("Docente")
async def subir(ctx):
    # Paso 1: Pedir el tipo de archivo
    await ctx.send("Por favor, indica el tipo de archivo:\n`teoria` (Teo), `tp` (Trabajo práctico), `bibliografia` (Bib)")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        tipo_msg = await bot.wait_for('message', check=check, timeout=60)
        tipo_input = tipo_msg.content.lower().strip()
    except:
        return await ctx.send("❌ Tiempo agotado o entrada inválida. Abortando.")

    tipos_validos = {"teoria": "Teo", "tp": "TP", "bibliografia": "BIB"}
    if tipo_input not in tipos_validos:
        return await ctx.send("❌ Tipo inválido. Debe ser `teoria`, `tp` o `bibliografia`.")

    tipo = tipos_validos[tipo_input]

    # Paso 2: Pedir que envíe un archivo
    await ctx.send("Ahora envíame el archivo que querés subir.")

    def check_file(m):
        return m.author == ctx.author and m.channel == ctx.channel and len(m.attachments) > 0

    try:
        archivo_msg = await bot.wait_for('message', check=check_file, timeout=120)
    except:
        return await ctx.send("❌ Tiempo agotado o no enviaste un archivo. Abortando.")

    archivo = archivo_msg.attachments[0]
    nombre_archivo = archivo.filename

    # ✅ Crear carpeta y ruta de guardado
    carpeta = tipo_input  # "teoria", "tp" o "bibliografia"
    ruta_carpeta = os.path.join("archivos", carpeta)
    os.makedirs(ruta_carpeta, exist_ok=True)
    ruta_guardado = os.path.join(ruta_carpeta, nombre_archivo)

    # Guardar el archivo de forma async
    async with aiofiles.open(ruta_guardado, 'wb') as f:
        contenido = await archivo.read()
        await f.write(contenido)

    # Guardar en base de datos
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

#ver los archivos subidos por categoria
@bot.command(name="ver_archivos")
async def ver_archivos(ctx, *, tipos_filtro: str = ""):
    # Procesar filtros si existen
    filtros = [t.strip().lower() for t in tipos_filtro.split(",") if t.strip()] if tipos_filtro else []

    # Mapeo entre entrada del usuario y tipos válidos en la DB
    tipo_mapeo = {
        "teo": "Teo",
        "tp": "TP",
        "bib": "BIB",
        "bibliografia": "BIB",
        "teoria": "Teo",
        "trabajo practico": "TP",
        "trabajopractico": "TP"
    }

    # Convertir filtros a valores válidos de la DB
    tipos_solicitados = set()
    for f in filtros:
        tipo_db = tipo_mapeo.get(f)
        if tipo_db:
            tipos_solicitados.add(tipo_db)

    # Si no se pasa nada o los filtros son inválidos, se muestran todos
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

#eliminar los archivo
@bot.command(name="eliminar_archivo")
@commands.has_role("Docente")
async def eliminar_archivo(ctx, *, nombre_archivo: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Buscar archivo en la base de datos
    cursor.execute("SELECT ruta_archivo FROM archivos WHERE nombre_archivo = ?", (nombre_archivo,))
    resultado = cursor.fetchone()

    if not resultado:
        await ctx.send(f"❌ No se encontró un archivo con el nombre `{nombre_archivo}`.")
        conn.close()
        return

    ruta_archivo = resultado[0]

    # Intentar borrar el archivo físico
    try:
        os.remove(ruta_archivo)
    except FileNotFoundError:
        await ctx.send(f"⚠️ El archivo `{nombre_archivo}` no se encontró en el sistema de archivos. Se eliminará solo de la base de datos.")

    # Borrar registro de la base de datos
    cursor.execute("DELETE FROM archivos WHERE nombre_archivo = ?", (nombre_archivo,))
    conn.commit()
    conn.close()

    await ctx.send(f"✅ Archivo `{nombre_archivo}` eliminado correctamente.")

@bot.command(name="enviar_archivo")
async def enviar_archivo(ctx, *, criterio: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    criterio = criterio.strip().lower()

    if criterio == "todo":
        cursor.execute("SELECT nombre_archivo, ruta_archivo FROM archivos")
    elif criterio in ["tp", "teo", "bib"]:
        tipo_mapeo = {"tp": "TP", "teo": "Teo", "bib": "BIB"}
        cursor.execute("SELECT nombre_archivo, ruta_archivo FROM archivos WHERE tipo = ?", (tipo_mapeo[criterio],))
    else:
        # Buscar por nombre exacto
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

# Comando para agregar una entrega
@bot.command(name="agregar_entrega")
@commands.has_role("Docente")
async def agregar_entrega(ctx):
    """
    Agrega una entrega de forma interactiva.
    """
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    # Paso 1: Nombre
    await ctx.send("Por favor, indica el nombre de la entrega:")
    try:
        nombre_msg = await bot.wait_for('message', check=check, timeout=60)
        nombre = nombre_msg.content.strip()
    except:
        return await ctx.send("❌ Tiempo agotado o entrada inválida. Abortando.")

    # Paso 2: Fecha
    await ctx.send("Indica la fecha de entrega (YYYY-MM-DD):")
    try:
        fecha_msg = await bot.wait_for('message', check=check, timeout=60)
        fecha = fecha_msg.content.strip()
        datetime.datetime.strptime(fecha, "%Y-%m-%d")
    except:
        return await ctx.send("❌ Formato de fecha incorrecto o tiempo agotado. Abortando.")

    # Paso 3: Hora
    await ctx.send("Indica la hora de entrega (HH:MM, 24hs):")
    try:
        hora_msg = await bot.wait_for('message', check=check, timeout=60)
        hora = hora_msg.content.strip()
        datetime.datetime.strptime(hora, "%H:%M")
    except:
        return await ctx.send("❌ Formato de hora incorrecto o tiempo agotado. Abortando.")

    # Paso 4: Canal
    await ctx.send("Menciona el canal donde enviar el recordatorio (ejemplo: #general):")
    def check_channel(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.raw_channel_mentions
    try:
        canal_msg = await bot.wait_for('message', check=check_channel, timeout=60)
        canal_id = canal_msg.raw_channel_mentions[0]
    except:
        return await ctx.send("❌ No se mencionó un canal válido o tiempo agotado. Abortando.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO entregas (nombre, fecha, hora, canal_id) VALUES (?, ?, ?, ?)''',
                   (nombre, fecha, hora, canal_id))
    conn.commit()
    conn.close()
    await ctx.send(f"✅ Entrega '{nombre}' agregada para el {fecha} a las {hora}.")

# Comando para listar entregas
@bot.command(name="listar_entregas")
async def listar_entregas(ctx):
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

# Tarea background para enviar recordatorios
@tasks.loop(minutes=30)
async def recordatorio_entregas():
    ahora = datetime.datetime.now()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''SELECT id, nombre, fecha, hora, canal_id, recordado_24h, recordado_1h FROM entregas''')
    entregas = cursor.fetchall()
    for id_, nombre, fecha, hora, canal_id, rec24, rec1 in entregas:
        dt_entrega = datetime.datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
        delta = dt_entrega - ahora
        canal = bot.get_channel(canal_id)
        alumnos_rol = None
        if canal and canal.guild:
            alumnos_rol = discord.utils.get(canal.guild.roles, name="Alumno")
        mention = alumnos_rol.mention if alumnos_rol else "@everyone"
        # Recordatorio 24h antes
        if 0 < delta.total_seconds() <= 86400 and not rec24:
            if canal:
                await canal.send(f"{mention} ⏰ Recordatorio: La entrega '{nombre}' es en 24 horas ({fecha} {hora})!")
            cursor.execute('UPDATE entregas SET recordado_24h = 1 WHERE id = ?', (id_,))
        # Recordatorio 1h antes
        if 0 < delta.total_seconds() <= 3600 and not rec1:
            if canal:
                await canal.send(f"{mention} ⏰ Recordatorio: La entrega '{nombre}' es en 1 hora ({fecha} {hora})!")
            cursor.execute('UPDATE entregas SET recordado_1h = 1 WHERE id = ?', (id_,))
        # Si ya pasó la entrega, se puede eliminar (opcional)
        if delta.total_seconds() < -3600:
            cursor.execute('DELETE FROM entregas WHERE id = ?', (id_,))
    conn.commit()
    conn.close()

@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(title="Ayuda de comandos del bot", color=discord.Color.green())
    embed.add_field(name="!prueba <texto>", value="Repite el texto que escribas.", inline=False)
    embed.add_field(name="!saludo", value="El bot te saluda.", inline=False)
    embed.add_field(name="!subir", value="(Docente) Sube un archivo de teoría, TP o bibliografía.", inline=False)
    embed.add_field(name="!ver_archivos [filtro]", value="Muestra los archivos subidos. Puedes filtrar por 'teoria', 'tp', 'bibliografia'.", inline=False)
    embed.add_field(name="!descargar <categoria>", value="Muestra los archivos de la categoría elegida y permite descargarlos con botones interactivos.", inline=False)
    embed.add_field(name="!eliminar_archivo <nombre>", value="(Docente) Elimina un archivo por nombre.", inline=False)
    embed.add_field(name="!enviar_archivo <criterio>", value="Envía archivos por privado según nombre, tipo o 'todo'.", inline=False)
    embed.add_field(name="!agregar_entrega <nombre> <fecha> <hora> <#canal>", value="(Docente) Agrega una entrega y programa recordatorios automáticos. Fecha: YYYY-MM-DD, Hora: HH:MM.", inline=False)
    embed.add_field(name="!listar_entregas", value="Muestra la lista de entregas próximas.", inline=False)
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f"El bot {bot.user} esta listo")
    recordatorio_entregas.start()

@bot.command(name="descargar")
async def descargar(ctx, categoria: str = None):
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
            for nombre, ruta in archivos[:10]:  # Máximo 10 botones por mensaje
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

bot.run(dst.TOKEN)