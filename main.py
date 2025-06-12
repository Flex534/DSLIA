from ntpath import join
import discord
from discord.ext import commands
import requests
import dst  #necesario para activar el token del bot
import os 
import datetime
import aiofiles
import sqlite3

intents= discord.Intents.default()
intents.message_content= True

bot= commands.Bot(command_prefix ="!", intents=intents)

from DSLIA.db import inicializar_db,DB_PATH
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


@bot.event
async def on_ready():
    print(f"El bot {bot.user} esta listo")

bot.run(dst.TOKEN)